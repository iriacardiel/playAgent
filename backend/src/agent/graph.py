import logging
import re
import sqlite3
import json

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_google_vertexai import ChatVertexAI
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from agent.prompts import JUDGE_PROMPT, SYSTEM_PROMPT
from agent.state import AgentState
from agent.tools import (
    get_list_of_tasks,
    add_task,
    check_current_time,
    add_symptom,
    get_list_of_symptoms,
    get_social_data,
    get_diagnosis,
    get_treatment,
    save_short_term_memory,
    retrieve_long_term_memory,
    save_long_term_memory,
)
from config.settings import Settings
from services.neo4j import Neo4jService


# Set up logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# --------------------------
# LLM
# --------------------------
ENABLE_JUDGE = bool(int(Settings.ENABLE_JUDGE))


if Settings.MODEL_SERVER == "OLLAMA":

    llm = ChatOllama(
        model=Settings.MODEL_NAME,
        temperature=0,
        num_ctx=16000,
        n_seq_max=1,
        extract_reasoning=False,
        reasoning=False,
        verbose=False,
        callbacks=[],
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

if Settings.MODEL_SERVER == "VERTEXAI":
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
# Neo4J LLM Configuration
# --------------------------
Neo4jService.set_llm(
    llm=llm.with_config({"tags": ["nostream"], "metadata": {"run_name": "cypher"}})
)

# --------------------------
# TOOLS
# --------------------------
tools = [
    get_list_of_tasks,
    add_task,
    check_current_time,
    add_symptom,
    get_list_of_symptoms,
    get_diagnosis,
    get_treatment,
]

memory_tools = [
    save_short_term_memory,
    retrieve_long_term_memory,
    save_long_term_memory,
]

tools = tools + memory_tools

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
        builder = StateGraph(AgentState)

        if ENABLE_JUDGE:
            builder.add_node("LLM_assistant", self.LLM_node)
            builder.add_node("judge", self.judge_node)
            builder.add_node("judge_final", self.judge_node)
            builder.add_node("tools", ToolNode(tools, handle_tool_errors=False))

            builder.add_edge(START, "judge")
            # First judge: Check if the user request is safe to be processed by the LLM
            builder.add_conditional_edges(
                "judge",
                self.judge_condition,
                path_map={"blocked": "__end__", "safe": "LLM_assistant"},
            )
            # Conditional edge to decide if the LLM needs tools or the response can be sent directly to the final judge
            builder.add_conditional_edges(
                "LLM_assistant",
                self.llm_condition,
                path_map={"tools": "tools", "judge": "judge_final"},
            )
            # Final judge: Check if the LLM response is safe to be sent to the user
            builder.add_conditional_edges(
                "judge_final",
                self.judge_condition,
                path_map={"blocked": "__end__", "safe": "__end__", "tools": "tools"},
            )
            # After a tool call, the LLM needs to be invoked again to process the response.
            builder.add_edge("tools", "LLM_assistant")

        else:
            builder.add_node("LLM_assistant", self.LLM_node)
            builder.add_node("tools", ToolNode(tools, handle_tool_errors=False))

            builder.add_edge(START, "LLM_assistant")
            builder.add_conditional_edges(
                "LLM_assistant", tools_condition, path_map=["tools", "__end__"]
            )

        return builder.compile(checkpointer=self.checkpointer, debug=False)

    # --------------------------
    # CONDITIONS
    # --------------------------
    def judge_condition(self, state: AgentState):
        """Determine next step based on judge result."""
        # Check if the last message is a safety warning
        if state["messages"]:
            last_message = state["messages"][-1]
            # If the last message is a safety warning, return blocked
            if (
                hasattr(last_message, "content")
                and "⚠️ Content blocked" in last_message.content
            ):
                return "blocked"
            # If the last message is an AIMessage with tool calls, route to tools
            elif hasattr(last_message, "tool_calls") and last_message.tool_calls:
                return "tools"

        # No safety warning and no tool calls. Safe content, end the conversation
        return "safe"

    def llm_condition(self, state: AgentState):
        """Determine next step based on the type of the last message."""
        # Check if we have a pending response to be analyzed by the final judge
        if "pending_response" in state and state["pending_response"]:
            return "judge"

        # Check if the last message has tool calls
        elif "messages" in state and state["messages"]:
            last_message = state["messages"][-1]

            if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                return "tools"

        # Default to judge for safety evaluation
        return "judge"

    # --------------------------
    # NODES
    # --------------------------

    # LLM Assistant Node
    def LLM_node(self, state: AgentState):
        """LLM Assistant Node that handles the LLM interactions."""
        # TODO: wait for long-term memory implementation to filter messages
        # messages_list = self.filtermessages(None, state["messages"])
        messages_list = state["messages"]

        # Build LLM input with the system prompt and the last messages
        short_term_memories = state.get("short_term_memories", []) # short_term_memories is a list of dicts
        llm_input = [
            SystemMessage(content=SYSTEM_PROMPT.format(short_term_memories_str=str("Empty" if not short_term_memories else "\n" + "\n".join(f"- {json.dumps(mem)}" for mem in short_term_memories)))),
        ] + messages_list

        if ENABLE_JUDGE:
            # Invoke the LLM with tools in background thread so that the response is not printed until the judge approves it
            ai_message = self.llm_with_tools.invoke(
                llm_input,
                config={"tags": ["nostream"], "metadata": {"run_name": "main"}},
            )

            # Check if the response has text content (to be checked by judge)
            has_content = False
            if hasattr(ai_message, "content"):
                content = ai_message.content
                # Depending on the model and response format, the content may be a list of dicts or a string
                if content:
                    if isinstance(content, list):
                        # Look for at least one non-empty text chunk within the structured response
                        has_content = any(
                            item
                            for item in content
                            if (isinstance(item, dict) and item.get("type") == "text")
                            or (isinstance(item, str) and item.strip())
                        )
                    elif isinstance(content, str) and content.strip():
                        # Simple string response that contains text must be judged
                        has_content = True

            # Check if the response contains tool calls
            has_tool_calls = hasattr(ai_message, "tool_calls") and ai_message.tool_calls

            if has_content:
                # If message has text content, it MUST be checked by judge_final first
                return {"pending_response": ai_message}
            elif has_tool_calls:
                # Only tool calls, no text content. This is safe to execute.
                return {"messages": [ai_message]}
            else:
                # No content and no tool calls. Store in pending_response for safety check anyway
                return {"pending_response": ai_message}

        else:
            ai_message = self.llm_with_tools.invoke(
                llm_input, config={"metadata": {"run_name": "main"}}
            )
            return {"messages": [ai_message]}

    def _evaluate_content_safety(self, message) -> bool:
        """Evaluate if a message's content is safe using the judge LLM.

        Args:
            message: Message object or string to evaluate

        Returns:
            bool: True if content is safe, False otherwise
        """
        try:
            # Extract content text. Depending on the model and response format,
            # the content may be a list of dicts or a string.
            # If it's a list of dicts, extract the text content from the response
            if hasattr(message, "content"):
                if isinstance(message.content, list):
                    evaluation_text = ""
                    for item in message.content:
                        if isinstance(item, dict) and "text" in item:
                            evaluation_text += item["text"]
                        else:
                            evaluation_text += str(item)
                else:
                    evaluation_text = str(message.content)
            else:
                evaluation_text = str(message)

            # If content is empty or only whitespace, consider it safe
            if not evaluation_text or not evaluation_text.strip():
                return True

            # Create evaluation message. The message is the judge prompt with the content of the message to be evaluated.
            # The message type is either "user" or "assistant".

            prompt = [
                SystemMessage(content=JUDGE_PROMPT.format(content=str(evaluation_text)))
            ]

            # Invoke the judge in the background thread to evaluate the content safety wihtout printing the response.
            response = self.llm.invoke(
                prompt, config={"tags": ["nostream"], "metadata": {"run_name": "judge"}}
            )

            # Extract content from response if it's a message object
            if hasattr(response, "content"):
                evaluation_response = response.content
            else:
                evaluation_response = str(response)
            
            logger.info(f"LLM JUDGE: {evaluation_response}. Message: {evaluation_text}")

            # If the response is empty, default to SAFE
            if not evaluation_response or not evaluation_response.strip():
                return True

            # Use regex to find SAFE or UNSAFE in the response (case-insensitive)
            # This handles cases where the LLM adds extra text or formatting
            safe_match = re.search(r"\bSAFE\b", evaluation_response, re.IGNORECASE)
            unsafe_match = re.search(r"\bUNSAFE\b", evaluation_response, re.IGNORECASE)

            # If UNSAFE is found, return False
            if unsafe_match:
                return False
            # If SAFE is found, return True
            elif safe_match:
                return True
            # If neither is found clearly, default to SAFE (allow content through)
            else:
                logger.warning(f"[WARNING] Could not parse safety evaluation. Defaulting to SAFE. Response: {evaluation_response}")
                return True

        except Exception as e:
            # Log error and fail safe (allow content through)
            logger.error(f"[ERROR] Content safety evaluation failed: {e}")
            return True

    # Judge Node
    def judge_node(self, state: AgentState):
        """Judge Node - Evaluates message content for safety."""
        blocked_message = "⚠️ Content blocked due to safety concerns."

        # CASE 1: Check if we have a pending response to evaluate.
        # A message in pending_response is a response from the LLM that needs to be evaluated by the judge.
        if "pending_response" in state and state["pending_response"]:
            pending_message = state["pending_response"]

            # Tool messages should be passed through without safety evaluation
            if isinstance(pending_message, ToolMessage):
                return {"messages": [pending_message], "pending_response": None}

            is_safe = self._evaluate_content_safety(pending_message)

            if is_safe:
                # Release the pending response to messages
                return {"messages": [pending_message], "pending_response": None}
            else:
                # If not safe, replace with a safety warning
                output = blocked_message
                blocked_message = AIMessage(content=output)
                return {"messages": [blocked_message], "pending_response": None}

        # CASE 2: Check any message in the state for judge verification.
        # Messages in "messages" can be either the user input
        # or a response from the LLM containing a ToolMessage.
        if state["messages"]:
            last_message = state["messages"][-1]

            # If the last message is a tool message, skip evaluation
            if isinstance(last_message, ToolMessage):
                return {}

            # Evaluate the content safety of the last message
            is_safe = self._evaluate_content_safety(last_message)
            if is_safe:
                # Content is safe, return empty state
                return {}
            else:
                # If not safe, replace the last message with a safety warning
                output = blocked_message
                new_messages = state["messages"][:-1] + [AIMessage(content=output)]
                return {"messages": new_messages}

    # --------------------------
    # AGENT UTILS
    # --------------------------
    def filtermessages(self, last: int = None, allmessages: list = []):
        """Return only the last messages (or all if last is None)."""
        if last is None:
            return allmessages  # Return all messages
        if last < 0:
            raise ValueError(f"'last' must be non-negative, got {last}")
        if last == 0:
            return []
        return allmessages[-last:] if len(allmessages) > last else allmessages
    

# --------------------------
# AGENT INSTANCE
# --------------------------
graph = Agent(llm, tools, checkpointer).build_graph()