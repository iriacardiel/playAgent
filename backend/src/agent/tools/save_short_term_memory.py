from datetime import datetime
from typing import Annotated, List

from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId, tool
from langgraph.prebuilt import InjectedState
from langgraph.types import Command
from termcolor import cprint



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