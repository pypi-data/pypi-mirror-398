"""Base channel class for exposing LangGraph apps through different protocols."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from fastapi import FastAPI

from orcakit_sdk.runner.agent_executor import AgentExecutor


class BaseChannel(ABC):
    """Abstract base class for channels.

    A Channel provides a way to expose an App through different protocols
    such as HTTP, WebSocket, gRPC, etc.
    """

    @abstractmethod
    def create_router(
        self,
        fastapi_app: FastAPI,
        agent_executor: AgentExecutor,
        url_prefix: str = "",
        **kwargs: str,
    ) -> None:
        """Create and register protocol-specific routes on the FastAPI app.

        Args:
            fastapi_app: The FastAPI application to register routes on.
            agent_executor: AgentExecutor instance to create routes for.
            prefix: Path prefix for the router endpoints.
            **kwargs: Additional arguments for future extension.
        """
        ...

    @staticmethod
    def normalize_prefix(prefix: str) -> str:
        """Normalize URL prefix to ensure consistent format.

        Args:
            prefix: The URL prefix to normalize.

        Returns:
            Normalized prefix starting with "/" and not ending with "/".
        """
        if not prefix:
            return ""
        if not prefix.startswith("/"):
            prefix = f"/{prefix}"
        return prefix.rstrip("/")

    @staticmethod
    def extract_content(result: dict[str, Any]) -> str:
        """Extract content from agent result.

        Args:
            result: The result dictionary from agent execution.

        Returns:
            The extracted content as a string.
        """
        response_messages = result.get("messages")
        if isinstance(response_messages, list) and response_messages:
            last_message = response_messages[-1]
            if hasattr(last_message, "content"):
                msg_content = getattr(last_message, "content", "")
                return str(msg_content) if msg_content else ""
            return str(last_message)
        return ""
