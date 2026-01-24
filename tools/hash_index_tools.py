"""Tools for hash indexing operations."""
from typing import Any
from model.tool import Tool as ToolClass


class GenerateHashKey(ToolClass):
    """Tool to generate a unique hash key and summary for a page content."""

    def __init__(self, existing_keys: set[str]):
        """
        Initialize the tool with a set of existing keys.

        Args:
            existing_keys: Set of already used hash keys.
        """
        self.existing_keys = existing_keys

    @property
    def name(self) -> str:
        return "generate_hash_key_and_summary"

    @property
    def description(self) -> str:
        return "Generate a unique, descriptive hash key AND a concise summary. The hash key will be used to RETRIEVE this section later, so it must clearly describe what content is in this section. Use lowercase_with_underscores, 3-8 words that describe the topic (e.g., 'neural_network_backpropagation', 'python_list_operations'). The summary should be 2-4 sentences."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "hash_key": {
                    "type": "string",
                    "description": "A descriptive hash key that will be used to RETRIEVE this section. It must clearly describe what content is in this section so users can find it again. Format: lowercase_with_underscores, 3-8 words describing the specific topic (e.g., 'neural_network_backpropagation', 'python_list_methods', 'react_hooks_useeffect')."
                },
                "summary": {
                    "type": "string",
                    "description": "A concise summary of the page content in 2-4 sentences that covers the main points and key information."
                }
            },
            "required": ["hash_key", "summary"],
        }

    def __call__(self, hash_key: str, summary: str) -> dict[str, Any]:
        """
        Validate and register the hash key and summary.

        Args:
            hash_key: The generated hash key.
            summary: The generated summary.

        Returns:
            Dict with success status and data.

        Raises:
            ValueError: If the hash key already exists.
        """
        if hash_key in self.existing_keys:
            raise ValueError(
                f"Hash key '{hash_key}' already exists. Please generate a unique key."
            )

        self.existing_keys.add(hash_key)
        return {
            "success": True,
            "hash_key": hash_key,
            "summary": summary,
        }

    def to_dict(self) -> dict:
        """Convert to API format, including existing keys in description."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": f"{self.description} NOTE: Already used keys: {', '.join(sorted(self.existing_keys)) if self.existing_keys else 'none'}. Please ensure your hash_key is unique.",
                "parameters": self.parameters,
            },
        }
