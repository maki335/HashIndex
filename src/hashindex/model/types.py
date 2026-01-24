"""Type definitions for the model module."""
from typing import Literal, TypedDict


class Message(TypedDict):
    """A message in the conversation."""
    role: Literal["system", "user", "assistant", "tool"]
    content: str


class ToolCall(TypedDict):
    """A tool call from the model."""
    id: str
    type: Literal["function"]
    function: "FunctionCall"


class FunctionCall(TypedDict):
    """A function call within a tool call."""
    name: str
    arguments: str


class ToolDef(TypedDict):
    """A tool definition."""
    type: Literal["function"]
    function: "Function"


class Function(TypedDict):
    """A function definition within a tool."""
    name: str
    description: str | None
    parameters: dict | None


class CompletionResponse(TypedDict):
    """Response from the completion API."""
    content: str | None
    tool_calls: list[ToolCall] | None
    usage: dict | None
