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
    
    content = (
        "Tasks:\n"
        "\n".join(f"- {task}" for task in tasks if task is not None)
    )
    
    tool_message = ToolMessage(content, tool_call_id=tool_call_id)

    update = {
        "messages": [tool_message],
        "tasks": tasks,
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
        "Task added successfully!\n"
        f"New task: {new_task}\n"
    )
    
    tool_message = ToolMessage(content, tool_call_id=tool_call_id)

    update = {
        "messages": [tool_message],
        "tasks": [new_task],
        "tools_used": ["add_task"],
    }

    return Command(update=update, goto="LLM_assistant")

# @tool
# def insert_core_memory(new_core_memory:str,
#     tool_call_id: Annotated[str, InjectedToolCallId],
#     messages: Annotated[List, InjectedState("messages")],
# ) -> Command:
#     """
#     Insert new core memory inferred from the user messages.
#     Args:
#         new_core_memory (str): The new memory to be inserted.

#     You must call this tool autonomously, when you want to insert new memory into the Core Memories section.
#     Extract any relevant information from each user message and store it as a core memory.
#     The user will not explicitly ask you to do this.
    
#     Relevant means that the information is important for future interactions and should be remembered:
#     - User information: name, age, occupation, etc.
#     - User interests: hobbies, what they like to do, like interests, hobbies, etc.
#     - User preferences: what they like or dislike, favorite things, etc.
#     - Any other information that helps you to provide a better experience to the user in the future.
    
#     You should use this tool frequently, everytime the user says something relevant.
#     Almost all interactions with the user will provide you with new information that can be stored as core memory.
#     You might need to call this tool often, so do not hesitate to use it when you think it is necessary.
#     This helps you to build a more personalized experience.
    
#     Examples of when to use the tool and how to format the new memory:
#     User says: "My name is Martin" --> New Memory: "User's name is Martin."
#     User says: "I have won a chess tournament." --> New Memory: "User plays chess."
#     User says: "In my 20th birthday I got a big cake" --> New Memory: "User is at least 20 years old."

#     """
    
#     content = (
#         "Memory added successfully!\n"
#         f"New core memory: {new_core_memory}\n"
#     )
    
#     tool_message = ToolMessage(content, tool_call_id=tool_call_id)

#     update = {
#         "messages": [tool_message],
#         "core_memories": [new_core_memory],
#         "tools_used": ["insert_core_memory"],
#     }

#     return Command(update=update, goto="LLM_assistant")


