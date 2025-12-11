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
from services.neo4j import Neo4jService
from services.memory.chromadb_store import ChromaVectorMemoryStore
from agent.state import AgentState


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