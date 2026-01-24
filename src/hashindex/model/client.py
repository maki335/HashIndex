"""OpenRouter API client with tool calling support."""
import os
from typing import Literal

import httpx

from hashindex.model.types import (
    CompletionResponse,
    Function,
    Message,
    ToolCall,
    ToolDef,
)


class Model:
    """Client for OpenRouter API with tool calling support."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://openrouter.ai/api/v1",
        model: str = "anthropic/claude-3.5-sonnet",
    ):
        """
        Initialize the OpenRouter client.

        Args:
            api_key: OpenRouter API key. Defaults to OPENROUTER_API_KEY env var.
            base_url: Base URL for the API.
            model: Default model to use for completions.
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key must be provided or set in OPENROUTER_API_KEY environment variable"
            )

        self.base_url = base_url.rstrip("/")
        self.model = model
        self.client = httpx.Client(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=120.0,
        )

    def complete(
        self,
        messages: list[Message],
        tools: list[ToolDef] | None = None,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> CompletionResponse:
        """
        Get a completion from the model.

        Args:
            messages: List of messages in the conversation.
            tools: List of tools available for the model to call.
            model: Model to use. Defaults to the model set during initialization.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.

        Returns:
            CompletionResponse with content and optional tool calls.
        """
        model = model or self.model

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if tools:
            payload["tools"] = tools

        response = self.client.post("/chat/completions", json=payload)
        response.raise_for_status()
        data = response.json()

        choice = data["choices"][0]
        message = choice["message"]

        content = message.get("content")
        tool_calls = None

        if "tool_calls" in message and message["tool_calls"]:
            tool_calls = [
                {
                    "id": tc["id"],
                    "type": tc["type"],
                    "function": {
                        "name": tc["function"]["name"],
                        "arguments": tc["function"]["arguments"],
                    },
                }
                for tc in message["tool_calls"]
            ]

        return CompletionResponse(
            content=content,
            tool_calls=tool_calls,
            usage=data.get("usage"),
        )

    def complete_with_retry(
        self,
        messages: list[Message],
        tools: list[ToolDef] | None = None,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        max_retries: int = 3,
    ) -> CompletionResponse:
        """
        Get a completion from the model with retry logic.

        Retries up to max_retries times if:
        - The request fails (network error, API error, etc.)

        Args:
            messages: List of messages in the conversation.
            tools: List of tools available for the model to call.
            model: Model to use. Defaults to the model set during initialization.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.
            max_retries: Maximum number of retry attempts.

        Returns:
            CompletionResponse with content and optional tool calls.

        Raises:
            Exception: If all retry attempts fail.
        """
        last_exception = None

        for attempt in range(max_retries):
            try:
                return self.complete(
                    messages=messages,
                    tools=tools,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            except Exception as e:
                last_exception = e
                continue

        raise Exception(
            f"Failed after {max_retries} attempts. Last error: {last_exception}"
        ) from last_exception

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
