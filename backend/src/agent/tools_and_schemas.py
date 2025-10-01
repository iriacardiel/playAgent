from datetime import datetime
import json
import traceback
from dataclasses import dataclass
from typing import Annotated, List, Literal

from agent import state
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
def save_short_term_memory(new_short_term_memory:str, keep_boolean:str, tag:str,
    tool_call_id: Annotated[str, InjectedToolCallId],
    state: Annotated[AgentState, InjectedState()],
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
    tool_name = "save_short_term_memory"
    max_temp_memories = 5  # Maximum number of temporary memories to keep in Short Term Memory
    
    try:
        # Save Short Term Memory
        # =====================2
        
        
        short_term_memories = state.get("short_term_memories", [])
        
        d = {
            "content": new_short_term_memory,
            "metadata": {
                "tags": tag,
                "importance": "5",
                "keep": keep_boolean,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        }


        short_term_memories += [d]
        
    except Exception as e:
        content = f"Error saving short term memory: {e}"
        
    try:
        # Save Long Term Memory (if needed)
        # ======================
                
        # Separate fixed (keep=True) and temporary (keep=False) memories
        fixed_memories = [m for m in short_term_memories if m["metadata"].get("keep") == "True"]
        temp_memories = [m for m in short_term_memories if m["metadata"].get("keep") != "True"]
        # Only move oldest temp memories to long term if over the limit (e.g., more than max_temp_memories)
        long_term_memories_to_save = []
        vector_store = ChromaVectorMemoryStore(collection_name="DORI_memories", reset_on_init=False)
        if len(temp_memories) > max_temp_memories:

            # Move oldest temp memories to long term
            long_term_memories_to_save = temp_memories[:-max_temp_memories]
            temp_memories = temp_memories[-max_temp_memories:]

            # Save to vector store
            for d in long_term_memories_to_save:
                vector_store.save(
                    content=d["content"],
                    metadata={**d["metadata"], "stored_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
                )

        # Merge fixed and trimmed temp memories to form updated short term
        short_term_memories_updated = fixed_memories + temp_memories
        
        vector_store.show_all()
        content = (
            f"New Short Term memory added successfully: {new_short_term_memory}"
            f"{len(long_term_memories_to_save)} memories moved to Long Term Memory."
        )

    except Exception as e:
        content = f"Error saving long term memories: {e}"

    print(colored(f"{content}", "green"))

    tool_message = ToolMessage(content, tool_call_id=tool_call_id)
    
    update = {
        "messages": [tool_message],
        "short_term_memories": short_term_memories_updated,
        "tools_used": [tool_name],
    }

    return Command(update=update, goto="LLM_assistant")

@tool
def retrieve_long_term_memory(query:str,
    tool_call_id: Annotated[str, InjectedToolCallId],
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
    num_results = 3  # Number of top memories to retrieve
    
    vector_store = ChromaVectorMemoryStore(collection_name="DORI_memories", reset_on_init=False)

    results = vector_store.retrieve(
            query=query,
            alpha_importance=0.0,
            alpha_recency=0.0,
            alpha_similarity=1.0,
            num_results=num_results
        )
    
    
    content = (
        f"Based on query: {query}, the top {num_results} retrieved memories are: {results}"
    )

    print(colored(f"{content}", "green"))

    tool_message = ToolMessage(content, tool_call_id=tool_call_id)

    update = {
        "messages": [tool_message],
        "tools_used": ["retrieve_long_term_memory"],
    }

    return Command(update=update, goto="LLM_assistant")


@tool
def check_current_time(
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    """
    Check the current time. Convert the current time to a human-readable format:
    
    Example:
    Current time is: 2023-10-01 12:00:00 --> it is 12:00 PM on October 1st, 2023.

    """
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    content = f"Current time is: {current_time}"

    print(colored(f"{content}", "green"))

    tool_message = ToolMessage(content, tool_call_id=tool_call_id)

    update = {
        "messages": [tool_message],
        "tools_used": ["check_current_time"],
    }

    return Command(update=update, goto="LLM_assistant")


@tool
def get_social_data(
    question: str, tool_call_id: Annotated[str, InjectedToolCallId]
) -> Command:
    """Obtain current social data by querying a knowledge graph database.

    input: question
    output: Answer to the question based on the data in the graph database.
    """
    try:
        print(colored("Executing cypher query synchronously...", "blue"))

        # Use direct execution to completely bypass any streaming mechanisms
        out =Neo4jService.get_cypher_chain().invoke(question)
        print(out)
        print(type(out))
        response = out.get("result","")
        steps = out.get("intermediate_steps") or []
        if steps:
            cypher = steps[0].get("query") 
            context = steps[1].get("context")
            cprint(response, "cyan")
            print("#"*60)
            print()

        print(colored(f"CypherChain response completed: {response[:100]}...", "green"))

    except Exception as e:
        out = {}
        print(colored(f"Error in cypher execution: {e}", "red"))
        response = f"There was an error in get_battlefield_data tool: {e}"

    # Return the COMPLETE result as a tool message
    tool_message = ToolMessage(json.dumps(out), tool_call_id=tool_call_id)

    update = {"messages": [tool_message], "tools_used": ["get_battlefield_data"]}

    return Command(update=update, goto="LLM_assistant")

