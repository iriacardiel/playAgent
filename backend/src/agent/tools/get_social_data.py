import logging
import json
from typing import Annotated
from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId, tool
from langgraph.types import Command
from termcolor import colored
from services.neo4j import Neo4jService

logger = logging.getLogger(__name__)

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
        response = json.dumps(Neo4jService.get_cypher_chain().invoke(question))

        print(colored(f"CypherChain response completed: {response[:100]}...", "green"))

    except Exception as e:
        print(colored(f"Error in cypher execution: {e}", "red"))
        response = f"There was an error in get_battlefield_data tool: {e}"

    # Return the COMPLETE result as a tool message
    tool_message = ToolMessage(response, tool_call_id=tool_call_id)

    update = {
        "messages": [tool_message], 
        "tools_used": ["get_social_data"]
    }
    
    logger.info("Tool: get_social_data")
    return Command(update=update, goto="LLM_assistant")
