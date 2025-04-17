from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from typing import Annotated, Sequence
from langgraph.graph.message import add_messages
from langgraph.managed import IsLastStep, RemainingSteps

class State(TypedDict):
    question: str
    query: str
    result: str
    answer: str

class AgentState(TypedDict):
    input: str
    top_k: int
    dialect: str
    messages: Annotated[Sequence[BaseMessage], add_messages]
    is_last_step: IsLastStep
    remaining_steps:  RemainingSteps = 25
