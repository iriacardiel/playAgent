
import logging
from typing import Annotated, List

from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId, tool
from langgraph.prebuilt import InjectedState
from langgraph.types import Command

logger = logging.getLogger(__name__)

@tool
def get_list_of_tasks(
    tool_call_id: Annotated[str, InjectedToolCallId],
    tasks: Annotated[List, InjectedState("tasks")],

) -> Command:
    """
    Get the list of tasks from the state and present them to the user.
    If list is, empty, inform the user that there are no tasks yet.
    """
    if tasks is None or len(tasks) == 0:
        content = "There are no tasks yet."
    else:
        content = (
            "Tasks:\n"
            "\n".join(f"- {task}" for task in tasks if task is not None)
        )
    
    tool_message = ToolMessage(content, tool_call_id=tool_call_id)

    update = {
        "messages": [tool_message],
        "tools_used": ["get_list_of_tasks"],
    }
    logger.info("Tool: get_list_of_tasks.")

    return Command(update=update, goto="LLM_assistant")