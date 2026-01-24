"""
HashIndex - A document indexing and querying system using hash-based indexing.

This library provides a simple way to index PDF documents using LLM-powered
content analysis and query them using natural language.
"""

from hashindex.core import HashIndex, HashObject, index_pdf, query_index
from hashindex.model import Model, Message
from hashindex.tools import GenerateHashKey, ListKeys, GetSummary, GetContent

__version__ = "0.1.0"

__all__ = [
    # Core classes
    "HashIndex",
    "HashObject",
    # Convenience functions
    "index_pdf",
    "query_index",
    # Model
    "Model",
    "Message",
    # Tools
    "GenerateHashKey",
    "ListKeys",
    "GetSummary",
    "GetContent",
]
