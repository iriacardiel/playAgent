import sqlite3

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AnyMessage, SystemMessage
from langchain_ollama import ChatOllama
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from agent.prompts import SYSTEM_PROMPT
from agent.state import AgentState
from agent.tools_and_schemas import (
    get_list_of_tasks,
    add_task
)
from config.settings import Settings

VERBOSE = bool(int(Settings.VERBOSE))


# --------------------------
# LLM
# --------------------------
llm = ChatOllama(
    model=Settings.MODEL_NAME,
    temperature=0,
    num_ctx=16000,
    n_seq_max=1,
    extract_reasoning=False,
)

# --------------------------
# TOOLS
# --------------------------
tools = [
    get_list_of_tasks,
    add_task,
]


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
)  # TODO: Pending to implement to an specific file


# --------------------------
#  AGENT
# --------------------------
class Agent:
    def __init__(
        self, llm: BaseChatModel, tools: list, checkpointer: SqliteSaver | None
    ):
        """Initialize the agent with an LLM and tools."""
        # Store the LLM instance
        self.llm = llm

        self.checkpointer = checkpointer

        # Bind the LLM with tools
        self.llm_with_tools = llm.bind_tools(tools)

    def build_graph(self):
        """Create the agent graph."""
        # --------------------------
        # BUILD GRAPH
        # --------------------------
        builder = StateGraph(AgentState)

        builder.add_node("LLM_assistant", self.LLM_node)
        builder.add_node("tools", ToolNode(tools, handle_tool_errors=False))

        builder.add_edge(START, "LLM_assistant")
        builder.add_conditional_edges(
            "LLM_assistant", tools_condition, path_map=["tools", "__end__"]
        )

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
        messages_list = self.filtermessages(state["messages"])

        # Apply custom filtering
        llm_input = [
            SystemMessage(content=SYSTEM_PROMPT),
        ] + messages_list

        # Call LLM
        ai_message = self.llm_with_tools.invoke(llm_input)

        return {"messages": [ai_message]}

    # --------------------------
    # AGENT UTILS
    # --------------------------
    def filtermessages(self, allmessages: list):
        """Filter messages to keep only relevant ones."""

        # TODO: Pending to implement
        def is_relevant_message(msg: AnyMessage, index: int, totalmessages: int):
            # Always keep last 3 messages
            if index >= totalmessages - 3:
                return True

            # Keep all other messages
            return True

        # Apply custom filtering
        filteredmessages = [
            msg
            for idx, msg in enumerate(allmessages)
            if is_relevant_message(msg, idx, len(allmessages))
        ]

        return filteredmessages


graph = Agent(llm, tools, checkpointer).build_graph()
