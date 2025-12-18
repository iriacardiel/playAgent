
import logging
from typing import Annotated

from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId, tool
from langgraph.types import Command

from services.memory.chromadb_store import ChromaVectorMemoryStore

logger = logging.getLogger(__name__)

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
        logger.info("Tool: retrieve_long_term_memory.")
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
