import operator
from typing import Annotated
from typing_extensions import TypedDict
from langchain.messages import AnyMessage

class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]