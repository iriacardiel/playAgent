import json
import traceback
from dataclasses import dataclass
from typing import Annotated, List, Literal

from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId, tool
from langgraph.graph.ui import push_ui_message
from langgraph.prebuilt import InjectedState
from langgraph.types import Command, interrupt
from termcolor import colored

from config import Settings

VERBOSE = bool(int(Settings.VERBOSE))

# --------------------------
# TOOLS
# --------------------------


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

    return Command(update=update, goto="LLM_assistant")

@tool
def add_task(new_task:str,
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    """
    Add a task to the list of tasks and present the updated list to the user.
    This function simulates adding a task to a list and returns the updated list of tasks.
    Args:
        new_task (str): The task to be added.
    """
    
    content = (
        f"Task added successfully! '{new_task}'"
    )
    
    tool_message = ToolMessage(content, tool_call_id=tool_call_id)

    update = {
        "messages": [tool_message],
        "tasks": [new_task],
        "tools_used": ["add_task"],
    }

    return Command(update=update, goto="LLM_assistant")

@tool
def save_core_memory(new_core_memory:str,
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    """
    Save new memory or insight inferred from the user messages into the Core Memories section.
    Args:
        new_core_memory (str): The new memory to be saved.

    Call this tool autonomously, when you want to save new memory into the Core Memories section. The user will not explicitly ask you to do this.
    Extract any relevant information from each user message and save it as a core memory.
    You should use this tool frequently, everytime the user says something relevant.
    Almost all interactions with the user will provide you with new information that can be stored as core memory.
    You might need to call this tool often, so do not hesitate to use it when you think it is necessary.
    This helps you to build a more personalized experience.

    ### When to Call `save_core_memory`
    You must call `save_core_memory` when the user shares information such as:
    - Their name, age, location, or personal details
    - Interests, preferences, or background
    - Current activities, goals, or lifestyle choices
    - User information: name, age, occupation, etc.
    - User interests: hobbies, what they like to do, like interests, hobbies, etc.
    - User preferences: what they like or dislike, favorite things, etc.
    - User future plans: what they want to do in the future, goals, etc.
    - Any other information that helps you to provide a better experience to the user in the future.

    Examples:
    - If the user says "My name is Iria", call:
    new_core_memory="The user's name is Iria."
    - If the user says "I'm a physics student", call this tool.:
    new_core_memory="The user is a physics student."
    - If the user says "My boyfriend plays chess", call this tool.:
    new_core_memory="The user has a boyfriend."

    """
    
    content = (
        f"New core memory added successfully: {new_core_memory}"
    )
    
    print(colored(f"New Core Memory: {new_core_memory}", "green"))
    
    tool_message = ToolMessage(content, tool_call_id=tool_call_id)

    update = {
        "messages": [tool_message],
        "core_memories": [new_core_memory],
        "tools_used": ["save_core_memory"],
    }

    return Command(update=update, goto="LLM_assistant")


