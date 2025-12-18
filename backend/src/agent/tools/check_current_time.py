import logging
from datetime import datetime

from typing import Annotated

from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId, tool
from langgraph.types import Command

logger = logging.getLogger(__name__)

@tool
def check_current_time(
    tool_call_id: Annotated[str, InjectedToolCallId]
) -> Command:
    """
    Check the current time. Convert the current time to a human-readable format:
    
    Example:
    Current time is: 2023-10-01 12:00:00 --> it is 12:00 PM on October 1st, 2023.

    """
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    content = f"Current time is: {current_time}"
    
    tool_message = ToolMessage(content, tool_call_id=tool_call_id)
    logger.info("Tool: check_current_time.")
    return Command(update={
        "messages": [tool_message],
        "tools_used": ["check_current_time"]
    })