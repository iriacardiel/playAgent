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
    save_short_term_memory,
    retrieve_long_term_memory,
)
from config.settings import Settings
from utils.logger import log_token_usage, log_llm_input
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
)  # LANGGRAPH HTTP RUNNER DOES NOT SUPPORT CUSTOM MEMORY CHECKPOINTING, USE BUILT-IN MEMORY


# --------------------------
#  AGENT (SELF MANAGED LLM)
# --------------------------
class Agent:
    def __init__(
        self, llm: BaseChatModel, tools: list, memory_tools: list, checkpointer: SqliteSaver | None
    ):
        """Initialize the agent with an LLM and tools."""
        # Store the LLM instance with do-not-render tag
        self.llm = llm.with_config(
            config={"tags": ["langsmith:do-not-render"]}
        )
        self.tools = tools + memory_tools

        self.checkpointer = checkpointer

        # Bind the LLM with tools and add do-not-render tag
        self.llm_with_tools = llm.bind_tools(self.tools).with_config(
            config={"tags": ["langsmith:do-not-render"]}
        )

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
        builder.add_edge("tools", "LLM_assistant")
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
                return "blocked"
        return "safe"

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

        log_llm_input(llm_input)
            
        ai_message = self.llm_with_tools.batch([llm_input])[0]

        # Token count (through LangChain AIMessage)
        log_token_usage(ai_message, messages_list)
        
        # Store the response in a temporary buffer instead of immediately adding to messages
        # Prefix the ID to prevent frontend rendering until judge approval
        ai_message.id = f"do-not-render-{ai_message.id}"
        logger.debug("LLM response generated, storing in buffer for safety verification")
        return {"pending_response": ai_message}
    
    def _evaluate_content_safety(self, message) -> bool:
        """Evaluate if a message's content is safe using the judge LLM."""
        logger.debug(f"Evaluating safety of message type: {type(message)}")
        logger.debug(f"Message content: {getattr(message, 'content', 'No content')[:150]}...")
        
        # Extract content text
        if hasattr(message, 'content'):
            if isinstance(message.content, list):
                content_text = ""
                for item in message.content:
                    if isinstance(item, dict) and 'text' in item:
                        content_text += item['text']
                    else:
                        content_text += str(item)
            else:
                content_text = str(message.content)
        else:
            content_text = str(message)
        
        # If content is empty or only whitespace, consider it safe (e.g., tool-only messages)
        if not content_text or not content_text.strip():
            logger.debug("Empty content detected, defaulting to SAFE")
            return True
        
        # Create evaluation message
        evaluation_message = HumanMessage(content=content_text)
        judge_prompt = get_judge_prompt(cdu="main")
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
            return True
        else:
            is_safe = response_content.strip().upper() == "SAFE"
            logger.debug(f"Is safe: {is_safe}")
            return is_safe

    # Judge Node
    def judge_node(self, state: AgentState):
        """Judge Node - Evaluates message content for safety."""
       
        blocked_message = "⚠️ Content blocked due to safety concerns."

        # Check if we have a pending response to evaluate
        if "pending_response" in state and state["pending_response"]:
            logger.debug("Judge node called with pending response for safety verification")
            pending_message = state["pending_response"]
            
            # Tool messages should be passed through without safety evaluation
            if isinstance(pending_message, ToolMessage):
                logger.debug("Tool message detected, passing through without safety evaluation")
                # Remove the do-not-render prefix to allow frontend rendering
                pending_message.id = pending_message.id.replace("do-not-render-", "")
                return {"messages": [pending_message], "pending_response": None}
            
            is_safe = self._evaluate_content_safety(pending_message)

            if is_safe:
                logger.debug("Content is safe, releasing pending response to messages")
                # Remove the do-not-render prefix to allow frontend rendering
                pending_message.id = pending_message.id.replace("do-not-render-", "")
                # Release the pending response to messages
                return {"messages": [pending_message], "pending_response": None}
            else:
                # If not safe, replace with a safety warning
                output = blocked_message
                logger.debug("Content is unsafe, replacing with safety warning")
                blocked_message = AIMessage(content=output)
                return {"messages": [blocked_message], "pending_response": None}
        
        # Fallback to original logic for other cases (like initial user input check)
        last_messages = self.filtermessages(1, state["messages"])
        if not last_messages:
            logger.debug("No messages to judge")
            return {}
        
        logger.debug(f"Judge node called with {len(state['messages'])} messages in state")
        
        # Get the last message to evaluate
        last_message = last_messages[-1]
        
        if isinstance(last_message, ToolMessage):
            logger.debug("Skipping tool message")
            return {}  

        is_safe = self._evaluate_content_safety(last_message)

        if is_safe:
            logger.debug("Content is safe, returning empty state")
            return {}
        else:
            # If not safe, replace the last message with a safety warning
            output = blocked_message
            logger.debug("Content is unsafe, replacing with safety warning")
            logger.debug(f"Original message count: {len(state['messages'])}")
            # Replace the last message instead of adding a new one
            new_messages = state["messages"][:-1] + [AIMessage(content=output)]
            logger.debug(f"New message count: {len(new_messages)}")
            logger.debug(f"Replaced message with: {output}")
            return {"messages": new_messages}

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
        streaming=False,
        stream=False,
    )

if Settings.MODEL_SERVER == "OPENAI":
    # Use OpenAI's Chat model
    llm = ChatOpenAI(
        model=Settings.MODEL_NAME,
        api_key=Settings.OPENAI_API_KEY,
        temperature=0,
        streaming=False,
        stream=False
    )

if Settings.MODEL_SERVER == "CLAUDE":
    # Use Google's Chat model
    llm = ChatVertexAI(
        model=Settings.MODEL_NAME,
        temperature=0,
        max_tokens=None,
        max_retries=6,
        stop=None,
        disable_streaming=True,
        streaming=False,
        stream=False
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