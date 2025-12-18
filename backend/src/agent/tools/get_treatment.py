
import logging
from typing import Annotated, List
import json

from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId, tool
from langgraph.prebuilt import InjectedState
from langgraph.types import Command

logger = logging.getLogger(__name__)

@tool
def get_treatment(
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    """
    Get the treatment for the user
    """
    fake_treatment = {
        "treatment_name": "Neurocognitive Regulation Program (NRP)",
        "components": [
            "45-minute cognitive activity blocks",
            "structured active breaks",
            "daily mental energy level logging",
            "evening digital disengagement routine"
        ],
        "nutrition_plan": {
            "plan_name": "Energy-Stable Nutrition Plan",
            "guidelines": [
                "Regular meal timing",
                "Balanced macronutrient intake",
                "Avoid long fasting periods during high cognitive demand"
            ],
            "example_meals": [
                "Whole grains with vegetables and protein",
                "Light evening meals",
                "Hydration-focused snacks"
            ],
            "intended_effect": "Support sustained energy and reduce fatigue fluctuations",
            "date": "2025-01-15"
        },
        "duration": "8 weeks",
        "expected_outcome": "Progressive improvement in mental clarity and reduced perceived fatigue.",
        "date": "2025-01-15"
        }
    
    
    content = json.dumps(fake_treatment)
    
    tool_message = ToolMessage(content, tool_call_id=tool_call_id)

    update = {
        "messages": [tool_message],
        "tools_used": ["get_treatment"],
    }
    logger.info("Tool: get_treatment.")

    return Command(update=update)