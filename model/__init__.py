"""Model module for OpenRouter API integration."""
from .client import Model
from .tool import Tool as ToolClass
from .types import (
    CompletionResponse,
    Function,
    FunctionCall,
    Message,
    ToolCall,
    ToolDef,
)

__all__ = [
    "Model",
    "Message",
    "ToolCall",
    "ToolDef",
    "ToolClass",
    "Function",
    "FunctionCall",
    "CompletionResponse",
]
