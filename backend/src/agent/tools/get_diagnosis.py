
import logging
from typing import Annotated, List
import json

from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId, tool
from langgraph.prebuilt import InjectedState
from langgraph.types import Command

logger = logging.getLogger(__name__)

@tool
def get_diagnosis(
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    """
    Get a synthetic diagnosis summary for the user
    """
    fake_diagnosis = {
        "diagnosis_name": "Neuroadaptive Fatigue Syndrome (NFS)",
        "confidence_level": "moderate",
        "summary": (
            "The reported symptom pattern is consistent with a functional, "
            "non-structural dysregulation of cognitive energy management."
        ),
        "notes": [
            "No structural abnormalities detected",
            "Symptoms appear context-dependent and stress-related",
            "Recommended longitudinal observation"
        ],
        "date": "2025-01-15"
    }

    content = json.dumps(fake_diagnosis)

    tool_message = ToolMessage(content, tool_call_id=tool_call_id)

    update = {
        "messages": [tool_message],
        "tools_used": ["get_diagnosis_summary"],
    }
    logger.info("Tool: get_diagnosis_summary.")

    return Command(update=update)