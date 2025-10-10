from typing import Annotated, List, Sequence, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from langgraph.graph.ui import AnyUIMessage, ui_message_reducer


def add_str(left, right):
    """Can also import `add` from the `operator` built-in."""
    if left != right:
        return left + right
    else:
        return left + ["None"]
    
def add_dict(left, right):
    """Can also import `add` from the `operator` built-in."""
    if left != right:
        return left + right
    else:
        return left + [{}]



# --------------------------
# STATE
# --------------------------
class TokenUsage(TypedDict):
    input_tokens: int
    output_tokens: int


# State:
class AgentState(TypedDict, total=False):
    messages: Annotated[List[AnyMessage], add_messages]
    ui: Annotated[Sequence[AnyUIMessage], ui_message_reducer]
    tasks: Annotated[list[str], add_str]
    tools_used : Annotated[list[str], add_str]
    short_term_memories: list[dict]
    pending_response: AnyMessage  # Buffer for LLM response before safety verification
