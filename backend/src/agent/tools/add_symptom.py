import logging

from typing import Annotated

from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId, tool
from langgraph.types import Command


logger = logging.getLogger(__name__)

@tool
def add_symptom(new_symptom:str,
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    """
    Add a symptom to the list of symptoms and present the updated list to the user.
    This function simulates adding a symptom to a list and returns the updated list of symptoms.
    Args:
        new_symptom (str): The symptom to be added.
    """
    
    content = (
        f"Symptom added successfully! '{new_symptom}'"
    )
    
    tool_message = ToolMessage(content, tool_call_id=tool_call_id)

    update = {
        "messages": [tool_message],
        "symptoms": [new_symptom],
        "tools_used": ["add_symptom"],
    }

    logger.info(f"Tool: add_symptom. {content}")
    return Command(update=update, goto="LLM_assistant")