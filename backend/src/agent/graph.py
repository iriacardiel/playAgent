import sqlite3
import logging

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AnyMessage, SystemMessage, AIMessage, HumanMessage, ToolMessage
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
    get_social_data,
    save_short_term_memory,
    retrieve_long_term_memory,
)
from config.settings import Settings
from logs.log_utils import log_token_usage
from termcolor import colored

VERBOSE = bool(int(Settings.VERBOSE))

# Set up logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


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

    # --------------------------
    # BUILD & COMPILE GRAPH
    # --------------------------
    def build_graph(self):
        """Create the agent graph."""
        # --------------------------
        # BUILD GRAPH
        # --------------------------

        builder = StateGraph(AgentState)
        
        builder.add_node("LLM_assistant", self.LLM_node)
        builder.add_node("judge", self.judge_node)
        builder.add_node("judge_final", self.judge_node)
        builder.add_node("tools", ToolNode(self.tools, handle_tool_errors=False))

        builder.add_edge(START, "judge")
        builder.add_conditional_edges(
            "judge", self.judge_condition, path_map={"blocked": "__end__", "safe": "LLM_assistant"}
        )
        builder.add_conditional_edges(
            "LLM_assistant", tools_condition, path_map={"tools": "tools", "__end__": "judge_final"}
        )
        builder.add_edge("tools", "judge_final")
        builder.add_edge("judge_final", "__end__")

        # --------------------------
        # COMPILE GRAPH
        # --------------------------
        return builder.compile(checkpointer=self.checkpointer, debug=False)

    # --------------------------
    # CONDITIONS
    # --------------------------
    def judge_condition(self, state: AgentState):
        """Determine next step based on judge result."""
        # Check if the last message is a safety warning
        if state["messages"]:
            last_message = state["messages"][-1]
            if hasattr(last_message, 'content') and "⚠️ Content blocked" in last_message.content:
                return "blocked"  # End the conversation
        return "safe"  # Continue to next step

    # --------------------------
    # NODES
    # --------------------------
    
    # LLM Assistant Node
    def LLM_node(self, state: AgentState):
        """LLM Assistant Node - Handles LLM interactions."""
        # Apply custom filtering
        messages_list = self.filtermessages( 20, state["messages"])
        
        # Build LLM input
        SYSTEM_PROMPT = get_system_prompt(state.get("short_term_memories", []), cdu = CDU)
        llm_input = [
            SystemMessage(content=SYSTEM_PROMPT),
        ] + messages_list

        log_llm_input(llm_input)
            
        # Call LLM
        ai_message = self.llm_with_tools.invoke(llm_input)

        # Token count (through LangChain AIMessage)
        log_token_usage(ai_message, messages_list)
        
        return {"messages": [ai_message]}
    
    # Judge Node
    def judge_node(self, state: AgentState):
        """Judge Node - Evaluates message content for safety."""
        # Get the last message content to evaluate
        last_messages = self.filtermessages(1, state["messages"])
        if not last_messages:
            logger.debug("No messages to judge")
            return {}
        
        # Get the last message to evaluate
        last_message = last_messages[-1]
        logger.debug(f"Judging message type: {type(last_message)}")
        logger.debug(f"Message content: {getattr(last_message, 'content', 'No content')[:100]}...")
        
        if isinstance(last_message, ToolMessage):
            logger.debug("Skipping tool message")
            return {}  

        judge_prompt = get_judge_prompt(cdu="main")
        
        # Create a clean evaluation message with just the content
        if hasattr(last_message, 'content'):
            if isinstance(last_message.content, list):
                content_text = ""
                for item in last_message.content:
                    if isinstance(item, dict) and 'text' in item:
                        content_text += item['text']
                    else:
                        content_text += str(item)
            else:
                content_text = str(last_message.content)
        else:
            content_text = str(last_message)
        
        # Create evaluation message
        evaluation_message = HumanMessage(content=content_text)
        
        prompt = [
            SystemMessage(content=judge_prompt),
            evaluation_message
        ]
        
        response = self.llm.invoke(prompt)
        logger.debug(f"Judge response: {response}")
        
        # Extract content from response if it's a message object
        if hasattr(response, 'content'):
            response_content = response.content
        else:
            response_content = str(response)
            
        logger.debug(f"Raw response content: '{response_content}'")
        
        # Handle empty or invalid responses
        if not response_content or not response_content.strip():
            logger.debug("Empty response from judge, defaulting to SAFE")
            is_safe = True
        else:
            is_safe = response_content.strip().upper() == "SAFE"
            
        logger.debug(f"Is safe: {is_safe}")

        if is_safe:
            logger.debug("Content is safe, returning empty state")
            return {}
        else:
            # If not safe, replace the last message with a safety warning
            output = "⚠️ Content blocked due to safety concerns."
            logger.debug("Content is unsafe, replacing with safety warning")
            # Replace the last message instead of adding a new one
            new_messages = state["messages"][:-1] + [AIMessage(content=output)]
            return {"messages": new_messages}

    # --------------------------
    # AGENT UTILS
    # --------------------------
    
    # Messages filter
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
# AGENT INSTANCE
# --------------------------
graph = Agent(llm, tools, checkpointer).build_graph()
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