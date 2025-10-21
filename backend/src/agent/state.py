from typing import Annotated, List, Sequence, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from langgraph.graph.ui import AnyUIMessage, ui_message_reducer


def add(left, right):
    """Can also import `add` from the `operator` built-in."""
    if left != right:
        return left + right
    else:
        return left + [None]

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
    tasks: Annotated[list[str], add]
    tools_used : Annotated[list[str], add]
    short_term_memories: list[dict]
