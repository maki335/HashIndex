"""Abstract base class for tools that can be called by the model."""
from abc import ABC, abstractmethod
from typing import Any


class Tool(ABC):
    """Abstract base class for tools."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of the tool."""
        ...

    @property
    def description(self) -> str | None:
        """Return the description of the tool."""
        return None

    @property
    def parameters(self) -> dict | None:
        """Return the JSON schema for the tool's parameters."""
        return None

    @abstractmethod
    def __call__(self, **kwargs: Any) -> Any:
        """
        Execute the tool with the given arguments.

        Args:
            **kwargs: Arguments to pass to the tool.

        Returns:
            The result of the tool execution.
        """
        ...

    def to_dict(self) -> dict:
        """
        Convert the tool to a dictionary format compatible with the API.

        Returns:
            A dictionary representation of the tool.
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }
