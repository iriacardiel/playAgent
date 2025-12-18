
import logging
from typing import Annotated, List

from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId, tool
from langgraph.prebuilt import InjectedState
from langgraph.types import Command

logger = logging.getLogger(__name__)

@tool
def get_list_of_symptoms(
    tool_call_id: Annotated[str, InjectedToolCallId],
    symptoms: Annotated[List, InjectedState("symptoms")],

) -> Command:
    """
    Get the list of symptoms from the state and present them to the user.
    If list is, empty, inform the user that there are no symptoms yet.
    """
    if symptoms is None or len(symptoms) == 0:
        content = "There are no symptoms yet."
    else:
        content = (
            "symptoms:\n"
            "\n".join(f"- {symptom}" for symptom in symptoms if symptom is not None)
        )
    
    tool_message = ToolMessage(content, tool_call_id=tool_call_id)

    update = {
        "messages": [tool_message],
        "tools_used": ["get_list_of_symptoms"],
    }
    logger.info("Tool: get_list_of_symptoms.")

    return Command(update=update)