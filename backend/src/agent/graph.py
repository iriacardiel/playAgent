import sqlite3

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AnyMessage, SystemMessage, AIMessage, HumanMessage
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_google_vertexai import ChatVertexAI
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from agent.prompts import get_system_prompt
from agent.prompts import get_judge_prompt
from agent.state import AgentState
from agent.tools_and_schemas import (
    get_list_of_tasks,
    add_task,
    check_current_time,
    save_short_term_memory,
    retrieve_long_term_memory,
)
from config.settings import Settings
from logs.log_utils import log_token_usage
from termcolor import colored

VERBOSE = bool(int(Settings.VERBOSE))



# --------------------------
# MEMORY
# --------------------------
def create_memory_checkpointer(memory_db_path: str | None = None) -> SqliteSaver | None:
    """Create memory checkpointer."""
    if memory_db_path is None:
        return
    conn = sqlite3.connect(database=memory_db_path, check_same_thread=False)
    return SqliteSaver(conn)


checkpointer = create_memory_checkpointer(
    memory_db_path=None
)  # LANGGRAPH HTTP RUNNER DOES NOT SUPPORT CUSTOM MEMORY CHECKPOINTING, USE BUILT-IN MEMORY


# --------------------------
#  AGENT (SELF MANAGED LLM)
# --------------------------
class Agent:
    def __init__(
        self, llm: BaseChatModel, tools: list, memory_tools: list, checkpointer: SqliteSaver | None
    ):
        """Initialize the agent with an LLM and tools."""
        # Store the LLM instance
        self.llm = llm
        self.tools = tools + memory_tools

        self.checkpointer = checkpointer

        # Bind the LLM with tools
        self.llm_with_tools = llm.bind_tools(self.tools)

    def build_graph(self):
        """Create the agent graph."""
        # --------------------------
        # BUILD GRAPH
        # --------------------------
        builder = StateGraph(AgentState)
        builder.add_node("LLM_assistant", self.LLM_node)
        builder.add_node("judge", judge_node)
        builder.add_node("tools", ToolNode(self.tools, handle_tool_errors=False))

        builder.add_edge(START, "LLM_assistant")
        builder.add_edge("LLM_assistant", "judge")
        builder.add_conditional_edges(
            "LLM_assistant", tools_condition, path_map=["tools", "__end__"]) # TODO This should be judge not llm_assistant

        # --------------------------
        # COMPILE GRAPH
        # --------------------------
        return builder.compile(checkpointer=self.checkpointer, debug=False)

    # --------------------------
    # NODES
    # --------------------------
    
    # LLM Assistant Node
    def LLM_node(self, state: AgentState):
        """LLM Assistant Node - Handles LLM interactions."""
        messages_list = self.filtermessages( 20, state["messages"])

        # Apply custom filtering
        llm_input = [
            SystemMessage(content=get_system_prompt(state.get("short_term_memories", []), cdu = "main")),
        ] + messages_list

        with open("./src/logs/llm_input.txt", "w") as f:
            f.write("Empty" if not llm_input else "\n" + "\n".join(
                f"{'DORI' if isinstance(m, AIMessage) else 'User' if isinstance(m, HumanMessage) else 'System' if isinstance(m, SystemMessage) else 'Tool'} - {m.content}"
                for m in llm_input
            ))
                
        # Call LLM
        ai_message = self.llm_with_tools.invoke(llm_input)

        # Token count (through LangChain AIMessage)
        log_token_usage(ai_message, messages_list)
        
        return {"messages": [ai_message]}

    # --------------------------
    # AGENT UTILS
    # --------------------------
    def filtermessages(self, last :int, allmessages: list):
        """Filter messages to keep only relevant ones."""

        # TODO: Pending to implement
        def is_relevant_message(msg: AnyMessage, index: int, totalmessages: int):
            # Always keep last `last` messages
            if index >= totalmessages - last:
                return True

            # Keep all other messages
            return False

        # Apply custom filtering
        filteredmessages = [
            msg
            for idx, msg in enumerate(allmessages)
            if is_relevant_message(msg, idx, len(allmessages))
        ]

        return filteredmessages
    

# --------------------------
# LLM
# --------------------------
if Settings.MODEL_SERVER == "OLLAMA":

    llm = ChatOllama(
        model=Settings.MODEL_NAME,
        temperature=0,
        num_ctx=16000,
        n_seq_max=1,
        extract_reasoning=False,
    )

if Settings.MODEL_SERVER == "OPENAI":
    # Use OpenAI's Chat model
    llm = ChatOpenAI(
        model=Settings.MODEL_NAME,
        api_key=Settings.OPENAI_API_KEY,
        temperature=0,
    )

if Settings.MODEL_SERVER == "CLAUDE":
    # Use Google's Chat model
    llm = ChatVertexAI(
        model=Settings.MODEL_NAME,
        temperature=0,
        max_tokens=None,
        max_retries=6,
        stop=None,
    )


# --------------------------
# Judge
# --------------------------
def judge_content(input_text: str) -> bool:
    """Returns True if content is safe, False if it violates rules."""
    prompt = llm_input = [
            SystemMessage(content=get_judge_prompt(state.get("short_term_memories", []), cdu = "main")),
        ] + messages_list
    response = llm.invoke(prompt)
    return response.strip().upper() == "SAFE"


def judge_node(state):
    output = state["output"]
    if judge_content(output):
        return {"output": output}
    else:
        return {"output": "⚠️ Content blocked due to safety concerns."}

# --------------------------
# TOOLS
# --------------------------
tools = [
    get_list_of_tasks,
    add_task,
    check_current_time
]

memory_tools = [
    save_short_term_memory,
    retrieve_long_term_memory,
]


# --------------------------
# AGENT
graph = Agent(llm, tools, memory_tools, checkpointer).build_graph()