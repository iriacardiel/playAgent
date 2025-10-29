import sqlite3

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import message_to_dict, AnyMessage, ToolMessage, SystemMessage, AIMessage, HumanMessage
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_google_vertexai import ChatVertexAI
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.tools import BaseTool
from langgraph.types import Command

from agent_multi.prompts import get_system_prompt
from agent_multi.state import AgentState
from agent_multi.tools_and_schemas import (
    get_list_of_tasks,
    add_task,
    check_current_time,
    save_short_term_memory,
    retrieve_long_term_memory,
    tools_condition_main,
    tools_condition_mem
)
from config.settings import Settings
from utils.logger import log_token_usage, log_llm_input
from termcolor import colored, cprint
from typing import Annotated, TypedDict, List, Any, Dict

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
        self.tools = tools
        self.memory_tools = memory_tools

        self.checkpointer = checkpointer

        # Bind the LLM with tools
        self.llm_with_tools = llm.bind_tools(tools)
        self.llm_with_memory_tools = llm.bind_tools(memory_tools)

    def build_graph(self):
        """Create the agent graph."""
        # --------------------------
        # BUILD GRAPH
        # --------------------------
        builder = StateGraph(AgentState)
        
        builder.add_node("memory_manager", self.memory_manager)
        builder.add_node("LLM_assistant", self.LLM_node)

        # Tool nodes: standard ToolNode for assistant, custom for memory
        builder.add_node("assistant_tools", ToolNode(self.tools, handle_tool_errors=False, messages_key="messages"))
        builder.add_node("memory_tools", ToolNode(self.memory_tools, handle_tool_errors=False, messages_key="mem_messages"))

        # Flow
        builder.add_edge(START, "memory_manager")

        builder.add_conditional_edges(
            "memory_manager",
            tools_condition_mem,
            path_map={"mem_tools": "memory_tools", "__end__": "LLM_assistant"},
        )

        builder.add_conditional_edges(
            "LLM_assistant",
            tools_condition_main,
            path_map={"tools": "assistant_tools", "__end__": "__end__"},
        )

        # After tools, route back to the corresponding LLM
        builder.add_edge("assistant_tools", "LLM_assistant")
        builder.add_edge("memory_tools", "memory_manager")

        return builder.compile(checkpointer=self.checkpointer, debug=False)

    # --------------------------
    # NODES
    # --------------------------
        
    
    def memory_manager(self, state: AgentState):
        # Use ONLY user-facing convo as evidence for memory extraction
        messages_list = self.filtermessages(20, state.get("messages", []))

        llm_input = [
            SystemMessage(
                content=get_system_prompt(
                    state.get("short_term_memories", []),
                    state.get("long_term_memories", []),
                    messages_list,
                    cdu="memory",
                )
            ),
        ] + state.get("mem_messages", [])  # <-- include prior mem thread!
        
        with open("./src/logs/llm_memories_input.txt", "w") as f:
            f.write("Empty" if not llm_input else "\n" + "\n".join(
                f"{'DORI' if isinstance(m, AIMessage) else 'User' if isinstance(m, HumanMessage) else 'System' if isinstance(m, SystemMessage) else 'Tool'} - {m.content}"
                for m in llm_input
            ))

        ai_message = self.llm_with_memory_tools.invoke(llm_input)
        return {"mem_messages": [ai_message]}
    
    # LLM Assistant Node
    def LLM_node(self, state: AgentState):
        """LLM Assistant Node - Handles LLM interactions."""
        messages_list = self.filtermessages( 20, state["messages"])

        # Apply custom filtering
        llm_input = [
            SystemMessage(content=get_system_prompt(state.get("short_term_memories", []), cdu = "main")),
        ] + messages_list

        log_llm_input(llm_input)
            
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

if Settings.MODEL_SERVER == "VERTEXAI":
    # Use Google's Chat model
    llm = ChatVertexAI(
        model=Settings.MODEL_NAME,
        temperature=0,
        max_tokens=None,
        max_retries=6,
        stop=None,
    )

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