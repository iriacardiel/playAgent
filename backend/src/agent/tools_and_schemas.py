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
from long_term_memory.vector_store import VectorMemoryStore

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
    - If the user says "My name is Martha", call:
    new_core_memory="The user's name is Martha."
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



@tool
def save_external_memory(new_external_memory:str,
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    """
    Save new memory or insight inferred from the user messages into the External Memories Vector Database.
    Args:
        new_external_memory (str): The new memory to be saved.

    Call this when the user asks you to remember something about the past. 

    ### When to Call `save_external_memory`
    You must call `save_external_memory` when the user shares information such as:
    - Past experiences, events, or stories
    - Historical facts or details about their life
    - Memories that are not directly related to the current conversation but are important for future interactions

    """
    
    
    # Initialize Vector Memory Store
    vector_store = VectorMemoryStore(collection_name="DORI_Memories", reset_on_init=False)

    # Step 1: Save (store)
    # =====================

    d = {
        "content": new_external_memory,
        "metadata": {
            "tags": "NA",
            "importance": "5"
        }
    }


    vector_store.save(
        content=d["content"],
        metadata={**d["metadata"], "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    )
    
    vector_store.show_all()
    
    
    
    content = (
        f"New external memory added successfully: {new_external_memory}"
    )

    print(colored(f"New External Memory: {new_external_memory}", "green"))

    tool_message = ToolMessage(content, tool_call_id=tool_call_id)

    update = {
        "messages": [tool_message],
        "core_memories": [new_external_memory],
        "tools_used": ["save_external_memory"],
    }

    return Command(update=update, goto="LLM_assistant")

@tool
def retrieve_external_memory(query:str,
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    """
    Retrieve memories from External Memories Vector Database based on a query
    Args:
        query (str): The query to retrieve memories.

    Call this when the user asks you about remembering something about the past.

    ### When to Call `retrieve_external_memory`
    You must call `retrieve_external_memory` when the user asks for information such as:
    - Past experiences, events, or stories
    - Historical facts or details about their life

    """
    vector_store = VectorMemoryStore(collection_name="DORI_Memories", reset_on_init=False)

    # Vector search
    contents, distances, cosine_similarities, recencies, importances = vector_store.search(query, k=vector_store.count_all(), include_tags=[])

    # Calculate scores based on importance, recency, and similarity
    cprint("\Documents reordered by SCORE:\nalpha_importance*importance + alpha_recency*0.995**recency + alpha_similarity*cosine_similarity", "yellow")
    alpha_importance = 1
    alpha_recency = 1
    alpha_similarity = 1
    exp_recency = 0.995**recencies
    scores = alpha_importance*importances + alpha_recency*exp_recency + alpha_similarity*cosine_similarities

    # Sort documents by score
    sorted_indices = np.argsort(scores)[::-1]  # Sort in descending order
    print(f"Sorted indices: {sorted_indices}")
    sorted_contents = [contents[i] for i in sorted_indices]
    sorted_distances = [distances[i] for i in sorted_indices]
    sorted_cosine_similarities = [cosine_similarities[i] for i in sorted_indices]
    sorted_recencies = [recencies[i] for i in sorted_indices]
    sorted_exp_recency = [exp_recency[i] for i in sorted_indices]
    sorted_importances = [importances[i] for i in sorted_indices]

    cprint(f"alpha_importance = {alpha_importance} | alpha_recency = {alpha_recency} | alpha_similarity = {alpha_similarity}", "yellow")
    for i, content in enumerate(sorted_contents):
        print(f"\n[{i}] Content: {content}")
        print(f"     Distance: {sorted_distances[i]}")
        print(f"     Cosine Similarity: {sorted_cosine_similarities[i]}")
        print(f"     Recency: {sorted_recencies[i]}")
        print(f"     Exp Recency: {sorted_exp_recency[i]}")
        print(f"     Importance: {sorted_importances[i]}")
        print(f"     SCORE: {scores[sorted_indices[i]]}")
        print("-" * 40)
    
    top_k_score = 3  # Number of top memories to retrieve
    content = (
        f"Based on query: {query}, the top {top_k_score} retrieved memories are: {sorted_contents[:top_k_score]}"
    )

    print(colored(f"{content}", "green"))

    tool_message = ToolMessage(content, tool_call_id=tool_call_id)

    update = {
        "messages": [tool_message],
        "tools_used": ["retrieve_external_memory"],
    }

    return Command(update=update, goto="LLM_assistant")
