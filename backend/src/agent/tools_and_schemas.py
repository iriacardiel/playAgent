from datetime import datetime
import json
import traceback
from dataclasses import dataclass
from typing import Annotated, List, Literal

from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId, tool
from langgraph.graph.ui import push_ui_message
from langgraph.prebuilt import InjectedState
from langgraph.types import Command, interrupt
import numpy as np
from termcolor import colored, cprint

from config import Settings
from services.memory.chromadb_store import ChromaVectorMemoryStore
from agent.state import AgentState

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

    return Command(update=update)

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

    return Command(update=update)

@tool
def save_short_term_memory(
    new_short_term_memory: str, 
    keep_boolean: str, 
    tag: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
    short_term_memories: Annotated[List, InjectedState("short_term_memories")]
) -> Command:
    """
    Save new short term memory or insight inferred from the user messages into the Short Term Memories section. Also known as Core Memories.
    Args:
        new_short_term_memory (str): The new memory to be saved. Keep it short and concise.
        keep_boolean (str): "True" or "False" whether or not to keep the memory in the Short Term Memories section for forever. Only the user name should be kept forever.
        tag: (str): The tag for the memory, e.g., "user_info", "DORI_info", "user_preferences" or "animals". You can combine them like: "user_info,user_preferences".

    Call this tool autonomously, when you want to save new memory into the Short Term or Core Memories section. The user will not explicitly ask you to do this.
    Extract any relevant information from each user message and save it as a short term memory.
    You should use this tool frequently, everytime the user says something relevant.
    Almost all interactions with the user will provide you with new information that can be stored as short term memory.
    You might need to call this tool often, so do not hesitate to use it when you think it is necessary.
    This helps you to build a more personalized experience.

    ### When to Call `save_short_term_memory`
    You must call `save_short_term_memory` when the user shares information such as:
    - Their name, age, location, or personal details
    - Interests, preferences, or background
    - Current activities, goals, or lifestyle choices
    - User information: name, age, occupation, etc.
    - User interests: hobbies, what they like to do, like interests, hobbies, etc.
    - User preferences: what they like or dislike, favorite things, etc.
    - User future plans: what they want to do in the future, goals, etc.
    - Any other information that helps you to provide a better experience to the user in the future.

    Examples:
    - If the user says "My name is Martha", call:
    new_short_term_memory="The user's name is Martha."
    - If the user says "I'm a physics student", call this tool.:
    new_short_term_memory="Martha is a physics student."
    - If the user says "My boyfriend plays chess", call this tool.:
    new_short_term_memory="Martha has a boyfriend."

    """
    # Control how many short-term memories to keep
    MAX_TEMP_MEMORIES = 10
    
    memory_entry = {
        "content": new_short_term_memory,
        "metadata": {
            "tags": tag,
            "importance": "5",
            "keep": keep_boolean,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    }
    
    # Get current short term memories from injected state
    current_memories = short_term_memories if short_term_memories else []
    updated_memories = current_memories + [memory_entry]
    
    # Separate fixed (keep="True") and temporary (keep="False") memories
    fixed_memories = [m for m in updated_memories if m.get("metadata", {}).get("keep") == "True"]
    temp_memories = [m for m in updated_memories if m.get("metadata", {}).get("keep") != "True"]
    
    if len(temp_memories) > MAX_TEMP_MEMORIES:
        # Keep only the most recent MAX_TEMP_MEMORIES temporary memories
        num_discarded = len(temp_memories) - MAX_TEMP_MEMORIES
        temp_memories = temp_memories[-MAX_TEMP_MEMORIES:]
        cprint(f"Discarded {num_discarded} old temporary memories (over limit of {MAX_TEMP_MEMORIES})", "yellow")
    
    # Merge fixed and trimmed temp memories to form final short-term memory list
    final_short_term_memories = fixed_memories + temp_memories
    
    content = f"Short term memory saved: {new_short_term_memory}"
    
    tool_message = ToolMessage(content, tool_call_id=tool_call_id)
    
    # Return Command to update state
    return Command(update={
        "messages": [tool_message],
        "short_term_memories": final_short_term_memories,
        "tools_used": ["save_short_term_memory"]
    })

@tool
def retrieve_long_term_memory(
    query: str,
    tool_call_id: Annotated[str, InjectedToolCallId]
) -> Command:
    """
    Retrieve memories from Long Term Memory Vector Database based on a query
    Args:
        query (str): The query to retrieve memories.

    Call this when the user asks you about remembering something about the past.

    ### When to Call `retrieve_long_term_memory`
    You must call `retrieve_long_term_memory` when the user asks for information such as:
    - Past experiences, events, or stories
    - Historical facts or details about their life
    
    Consider the user name to make the query more personalized, use third person to make the query more natural.

    """
    try:
        # Perform actual vector store retrieval
        vector_store = ChromaVectorMemoryStore(collection_name="DORI_memories", reset_on_init=False)
        
        results = vector_store.retrieve(
            query=query,
            alpha_importance=0.0,
            alpha_recency=0.0,
            alpha_similarity=1.0,
            num_results=5
        )
        
        formatted_results = []
        if results:
            content = f"Retrieved {len(results)} memories for query: {query}\n\n"
            for i, memory_content in enumerate(results, 1):
                # memory_content is a string, not a dict
                content += f"{i}. {memory_content}\n"
                # Format as dict for state storage
                formatted_results.append({
                    "content": memory_content,
                    "metadata": {}
                })
        else:
            content = f"No memories found for query: {query}"
        
        tool_message = ToolMessage(content, tool_call_id=tool_call_id)
        
        return Command(update={
            "messages": [tool_message],
            "long_term_memories": formatted_results,
            "tools_used": ["retrieve_long_term_memory"]
        })
        
    except Exception as e:
        content = f"Error retrieving memories: {str(e)}"
        tool_message = ToolMessage(content, tool_call_id=tool_call_id)
        
        return Command(update={
            "messages": [tool_message],
            "long_term_memories": [],
            "tools_used": ["retrieve_long_term_memory"]
        })


@tool
def save_long_term_memory(
    content: str,
    tag: str,
    importance: str,
    tool_call_id: Annotated[str, InjectedToolCallId]
) -> Command:
    """
    Save an important memory or insight about the user to Long Term Memory.
    Use this tool ONLY for truly important, meaningful information about the user that should be remembered permanently.
    This is different from short-term memory - only save things here that are significant and worth remembering long-term.
    Use this tool ONLY for essential information that affects how you interact with and assist the user.
    
    Args:
        content (str): The important memory to save. Should be functional, work-related, or essential personal info.
        tag (str): The tag/category, e.g., "user_info", "user_preferences", "work_context". You can combine: "user_info,user_preferences".
        importance (str): Importance level from "1" to "10", where "10" is most important. Use "5" for typical important memories.

    ### When to Call `save_long_term_memory`
    
    You should call `save_long_term_memory` ONLY when the user shares information that is:
    - Significant and meaningful (not trivial details)
    - Worth remembering permanently
    - Important for building a deep understanding of the user
    - Relevant for future interactions
    - User's name (always important)
    - Preferences for LLM responses (tone, style, format, length)
    - Important personal info (profession, key roles, context)
    - Work-related preferences and requirements
    - Functional preferences that affect interactions
    
    Do NOT save casual preferences, temporary plans, or day-to-day details - use short-term memory instead.
    
    This memory will be stored in a vector database and can be retrieved later using `retrieve_long_term_memory`.

    """
    try:
        vector_store = ChromaVectorMemoryStore(collection_name="DORI_memories", reset_on_init=False)
        
        metadata = {
            "tags": tag,
            "importance": importance,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "stored_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        vector_store.save(
            content=content,
            metadata=metadata
        )
        
        content_msg = f"Important memory saved to long-term storage: {content}"
        tool_message = ToolMessage(content_msg, tool_call_id=tool_call_id)
        
        return Command(update={
            "messages": [tool_message],
            "tools_used": ["save_long_term_memory"]
        })
        
    except Exception as e:
        content_msg = f"Error saving memory to long-term storage: {str(e)}"
        tool_message = ToolMessage(content_msg, tool_call_id=tool_call_id)
        
        return Command(update={
            "messages": [tool_message],
            "tools_used": ["save_long_term_memory"]
        })


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
    
    return Command(update={
        "messages": [tool_message],
        "tools_used": ["check_current_time"]
    })

