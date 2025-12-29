"""OpenAI-compatible channel for exposing agents through OpenAI API protocol."""

from __future__ import annotations

import json
import logging
import time
import uuid
from collections.abc import AsyncIterator

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage
from langchain_core.runnables.config import RunnableConfig
from pydantic import BaseModel, Field, model_serializer
from typing_extensions import override

from orcakit_sdk.runner.agent_executor import AgentExecutor

from .base import BaseChannel

logger = logging.getLogger(__name__)


class ChatMessage(BaseModel):
    """OpenAI-compatible chat message."""

    role: str
    content: str
    name: str | None = None


class ChatCompletionRequest(BaseModel):
    """OpenAI-compatible chat completion request."""

    model: str
    messages: list[ChatMessage]
    temperature: float | None = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float | None = Field(default=1.0, ge=0.0, le=1.0)
    n: int | None = Field(default=1, ge=1)
    stream: bool | None = False
    stop: list[str] | None = None
    max_tokens: int | None = Field(default=None, gt=0)
    presence_penalty: float | None = Field(default=0, ge=-2.0, le=2.0)
    frequency_penalty: float | None = Field(default=0, ge=-2.0, le=2.0)
    logit_bias: dict[str, float] | None = None
    user: str | None = None


class ChatCompletionResponseChoice(BaseModel):
    """OpenAI-compatible chat completion response choice."""

    index: int
    message: ChatMessage
    finish_reason: str


class UsageInfo(BaseModel):
    """Token usage information."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatCompletionResponse(BaseModel):
    """OpenAI-compatible chat completion response."""

    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[ChatCompletionResponseChoice]
    usage: UsageInfo


class ToolCallFunction(BaseModel):
    """Function call in a tool call."""

    model_config = {"exclude_none": True}

    name: str | None = None
    arguments: str | None = None


class ToolCall(BaseModel):
    """Tool call in OpenAI format."""

    model_config = {"exclude_none": True}

    index: int = 0
    id: str | None = None
    type: str = "function"
    function: ToolCallFunction | None = None


class DeltaContent(BaseModel):
    """Delta content for streaming response."""

    model_config = {"exclude_none": True}

    content: str | None = None
    role: str | None = None
    tool_calls: list[ToolCall] | None = None

    @model_serializer(mode="wrap")
    def _serialize_model(self, serializer, info):
        """Exclude empty strings and empty lists from serialization."""
        data = serializer(self)
        # Remove empty strings and empty lists
        return {k: v for k, v in data.items() if v not in ("", [], None)}


class StreamChoice(BaseModel):
    """Streaming response choice."""

    model_config = {"exclude_none": True}

    index: int
    delta: DeltaContent
    finish_reason: str | None = None


class ChatCompletionChunk(BaseModel):
    """OpenAI-compatible chat completion chunk for streaming."""

    model_config = {"exclude_none": True}

    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: list[StreamChoice]


def convert_messages(messages: list[ChatMessage]) -> list[AnyMessage]:
    """Convert OpenAI format messages to LangChain format.

    Args:
        messages: List of OpenAI-format chat messages.

    Returns:
        List of LangChain message objects.
    """
    converted: list[AnyMessage] = []
    for msg in messages:
        if msg.role == "system":
            converted.append(SystemMessage(content=msg.content))
        elif msg.role == "user":
            converted.append(HumanMessage(content=msg.content))
        elif msg.role == "assistant":
            converted.append(AIMessage(content=msg.content))
        else:
            logger.warning(
                f"Unknown message role: {msg.role}, treating as user message"
            )
            converted.append(HumanMessage(content=msg.content))
    return converted


class OpenAIChannel(BaseChannel):
    """Channel for exposing agents through OpenAI-compatible API.

    This channel creates a FastAPI router with OpenAI-compatible endpoints
    for chat completions and model listing.

    Example:
        >>> from fastapi import FastAPI
        >>> from orcakit_sdk.agent import Agent
        >>> from orcakit_sdk.channels.openai_channel import OpenAIChannel
        >>>
        >>> fastapi_app = FastAPI()
        >>> agent = Agent(graph)
        >>> channel = OpenAIChannel(model_name="my-agent")
        >>> channel.create_router(fastapi_app, agent.agent_executor, prefix="/v1")
    """

    def __init__(self, model_name: str = "agent") -> None:
        """Initialize the OpenAI channel.

        Args:
            model_name: Name of the model to expose in the API.
        """
        self.model_name = model_name
        self.agent_executor: AgentExecutor | None = None

    @override
    def create_router(
        self,
        fastapi_app: FastAPI,
        agent_executor: AgentExecutor,
        url_prefix: str = "/openai",
        **kwargs: str,
    ) -> None:
        """Create and register FastAPI router with OpenAI-compatible endpoints.

        Args:
            fastapi_app: The FastAPI application to register routes on.
            agent_executor: The AgentExecutor instance to create a router for.
            prefix: Path prefix for the router endpoints.
            **kwargs: Additional arguments (e.g., model_name).
        """
        self.agent_executor = agent_executor

        # Override model_name if provided in kwargs
        if "model_name" in kwargs:
            self.model_name = kwargs["model_name"]

        router = self._create_router(url_prefix)
        fastapi_app.include_router(router)

    def _create_router(self, prefix: str = "") -> APIRouter:
        """Create a FastAPI router with OpenAI-compatible endpoints.

        Args:
            prefix: Path prefix for the router endpoints.

        Returns:
            A FastAPI router with OpenAI-compatible endpoints.

        Raises:
            RuntimeError: If no agent executor has been set.
        """
        if self.agent_executor is None:
            raise RuntimeError(
                "No agent executor available. Call create_router() first."
            )

        # Normalize prefix
        prefix = self.normalize_prefix(prefix)
        router = APIRouter(prefix=prefix, tags=["OpenAI Protocol"])
        executor = self.agent_executor

        @router.post("/v1/chat/completions", response_model=None)
        async def create_chat_completion(
            request: ChatCompletionRequest,
        ) -> ChatCompletionResponse | StreamingResponse:
            """Create chat completion - OpenAI compatible API."""
            completion_id = f"chatcmpl-{uuid.uuid4().hex[:8]}"

            # Use user field as thread_id if provided
            config: RunnableConfig | None = None
            if request.user:
                config = {"configurable": {"thread_id": request.user}}

            try:
                if request.stream:
                    return StreamingResponse(
                        self._stream_response(request, completion_id, config),
                        media_type="text/event-stream",
                    )

                # Non-streaming response
                messages = convert_messages(request.messages)
                result = await executor.call(
                    messages, user=request.user, tags=["openai"], config=config
                )
                response_content = self._extract_response_content(result)

                return ChatCompletionResponse(
                    id=completion_id,
                    created=int(time.time()),
                    model=request.model,
                    choices=[
                        ChatCompletionResponseChoice(
                            index=0,
                            message=ChatMessage(
                                role="assistant", content=response_content
                            ),
                            finish_reason="stop",
                        )
                    ],
                    usage=UsageInfo(),
                )
            except Exception as e:
                logger.exception("Error in chat completion")
                raise HTTPException(status_code=500, detail=str(e)) from e

        @router.get("/v1/models")
        async def list_models() -> dict[str, object]:
            """List available models."""
            return {
                "object": "list",
                "data": [
                    {
                        "id": self.model_name,
                        "object": "model",
                        "created": int(time.time()),
                        "owned_by": "orcakit",
                        "permission": [],
                        "root": self.model_name,
                        "parent": None,
                    }
                ],
            }

        return router

    async def _stream_response(
        self,
        request: ChatCompletionRequest,
        completion_id: str,
        config: RunnableConfig | None = None,
    ) -> AsyncIterator[str]:
        """Generate streaming response.

        Args:
            request: The chat completion request.
            completion_id: Unique ID for this completion.
            config: Configuration dict with thread_id for checkpointer.

        Yields:
            Server-sent event formatted strings.
        """
        if self.agent_executor is None:
            yield self._format_error_chunk(
                completion_id, request.model, "No agent executor"
            )
            yield "data: [DONE]\n\n"
            return

        messages = convert_messages(request.messages)

        try:
            # Send initial chunk with role
            initial_chunk = ChatCompletionChunk(
                id=completion_id,
                created=int(time.time()),
                model=request.model,
                choices=[
                    StreamChoice(
                        index=0,
                        delta=DeltaContent(role="assistant"),
                        finish_reason=None,
                    )
                ],
            )
            yield f"data: {initial_chunk.model_dump_json(exclude_none=True)}\n\n"

            # Stream content using the stream_content method
            async for content in self.agent_executor.stream_content(
                messages, config=config
            ):
                delta = DeltaContent(content=content)
                chunk_data = ChatCompletionChunk(
                    id=completion_id,
                    created=int(time.time()),
                    model=request.model,
                    choices=[
                        StreamChoice(
                            index=0,
                            delta=delta,
                            finish_reason=None,
                        )
                    ],
                )
                yield f"data: {chunk_data.model_dump_json(exclude_none=True)}\n\n"

            # Send final chunk with finish_reason
            final_chunk = ChatCompletionChunk(
                id=completion_id,
                created=int(time.time()),
                model=request.model,
                choices=[
                    StreamChoice(
                        index=0,
                        delta=DeltaContent(),
                        finish_reason="stop",
                    )
                ],
            )
            yield f"data: {final_chunk.model_dump_json(exclude_none=True)}\n\n"
            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.exception("Error in streaming response")
            yield self._format_error_chunk(completion_id, request.model, str(e))
            yield "data: [DONE]\n\n"

    @staticmethod
    def _format_error_chunk(completion_id: str, model: str, error_msg: str) -> str:
        """Format an error chunk for streaming response.

        Args:
            completion_id: The completion ID.
            model: The model name.
            error_msg: The error message.

        Returns:
            Formatted SSE error chunk.
        """
        error_chunk = {
            "id": completion_id,
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "delta": {"content": f"Error: {error_msg}"},
                    "finish_reason": "error",
                }
            ],
        }
        return f"data: {json.dumps(error_chunk)}\n\n"

    @staticmethod
    def _extract_response_content(result: dict[str, object]) -> str:
        """Extract response content from agent result (non-streaming).

        Args:
            result: The result dictionary from agent execution.

        Returns:
            The extracted response content as a string.
        """
        # Try to extract content from messages
        messages = result.get("messages")
        if isinstance(messages, list) and messages:
            last_message = messages[-1]
            if hasattr(last_message, "content"):
                return str(getattr(last_message, "content", ""))
            if isinstance(last_message, dict) and "content" in last_message:
                return str(last_message["content"])

        # Try common result keys
        for key in ("response", "output", "content"):
            if key in result:
                return str(result[key])

        # Fallback: convert entire result to string
        return str(result)
