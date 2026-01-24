"""Tools for querying a hash index."""
from typing import Any
from model.tool import Tool as ToolClass


class ListKeys(ToolClass):
    """Tool to list all available hash keys with their summaries."""

    def __init__(self, index: 'HashIndex'):
        """
        Initialize the tool with a hash index.

        Args:
            index: The HashIndex to query.
        """
        self.index = index

    @property
    def name(self) -> str:
        return "list_keys"

    @property
    def description(self) -> str:
        return "List all available hash keys in the index along with their summaries. Use this to get an overview of what content is available."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }

    def __call__(self) -> dict[str, Any]:
        """
        List all keys with their summaries.

        Returns:
            Dict with success status and list of keys with summaries.
        """
        keys_info = []
        for key, obj in self.index.PageTable.items():
            keys_info.append({
                "hash_key": key,
                "page_number": obj.page_number,
                "summary": obj.summary,
            })

        return {
            "success": True,
            "keys": keys_info,
            "total": len(keys_info),
        }


class GetSummary(ToolClass):
    """Tool to get the summary for a specific hash key."""

    def __init__(self, index: 'HashIndex'):
        """
        Initialize the tool with a hash index.

        Args:
            index: The HashIndex to query.
        """
        self.index = index

    @property
    def name(self) -> str:
        return "get_summary"

    @property
    def description(self) -> str:
        return "Get the summary for a specific hash key. Use this to quickly understand what a page contains before deciding to read the full content."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "hash_key": {
                    "type": "string",
                    "description": "The hash key to get the summary for."
                }
            },
            "required": ["hash_key"],
        }

    def __call__(self, hash_key: str) -> dict[str, Any]:
        """
        Get the summary for a hash key.

        Args:
            hash_key: The hash key to get the summary for.

        Returns:
            Dict with success status and summary.

        Raises:
            ValueError: If the hash key doesn't exist.
        """
        if hash_key not in self.index.PageTable:
            raise ValueError(f"Hash key '{hash_key}' not found in index.")

        obj = self.index.PageTable[hash_key]
        return {
            "success": True,
            "hash_key": hash_key,
            "page_number": obj.page_number,
            "summary": obj.summary,
        }


class GetContent(ToolClass):
    """Tool to get the full content for a specific hash key."""

    def __init__(self, index: 'HashIndex'):
        """
        Initialize the tool with a hash index.

        Args:
            index: The HashIndex to query.
        """
        self.index = index

    @property
    def name(self) -> str:
        return "get_content"

    @property
    def description(self) -> str:
        return "Get the full content for a specific hash key. Use this after reviewing the summary to get detailed information from a page."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "hash_key": {
                    "type": "string",
                    "description": "The hash key to get the full content for."
                }
            },
            "required": ["hash_key"],
        }

    def __call__(self, hash_key: str) -> dict[str, Any]:
        """
        Get the full content for a hash key.

        Args:
            hash_key: The hash key to get the content for.

        Returns:
            Dict with success status and content.

        Raises:
            ValueError: If the hash key doesn't exist.
        """
        if hash_key not in self.index.PageTable:
            raise ValueError(f"Hash key '{hash_key}' not found in index.")

        obj = self.index.PageTable[hash_key]
        return {
            "success": True,
            "hash_key": hash_key,
            "page_number": obj.page_number,
            "summary": obj.summary,
            "content": obj.content,
        }
