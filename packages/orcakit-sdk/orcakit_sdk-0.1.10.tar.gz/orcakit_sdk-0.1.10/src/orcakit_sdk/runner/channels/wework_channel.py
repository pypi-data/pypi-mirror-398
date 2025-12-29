"""WeWork channel for exposing LangGraph apps through WeWork robot protocol."""

from __future__ import annotations

import json
import logging
import uuid
from typing import TYPE_CHECKING

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from langchain_core.messages import AnyMessage, HumanMessage
from langchain_core.runnables.config import RunnableConfig
from pydantic import BaseModel, Field
from typing_extensions import override

from orcakit_sdk.runner.agent_executor import AgentExecutor

from .base import BaseChannel

if TYPE_CHECKING:
    from fastapi import FastAPI

logger = logging.getLogger(__name__)


class WeWorkChatRequest(BaseModel):
    """WeWork chat request model."""

    content: str = Field(default="", description="The user message content")
    msg_id: str = Field(default="", description="Message ID")
    user: str = Field(default="", description="User identifier")
    msg_type: str = Field(default="text", description="Message type")
    raw_msg: str = Field(default="<xml></xml>", description="Raw XML message")
    session_id: str | None = Field(
        default=None,
        description="Session ID for conversation continuity",
    )
    business_keys: list[str] = Field(default_factory=list, description="Business keys")
    request_source: str = Field(default="robot", description="Request source")
    stream: bool = Field(default=True, description="Enable streaming response")

    def to_config(self) -> RunnableConfig:
        """Convert request parameters to RunnableConfig format."""
        thread_id = self.session_id if self.session_id else str(uuid.uuid4())
        configurable: dict[str, str | list[str]] = {
            "thread_id": thread_id,
            "user": self.user,
            "msg_id": self.msg_id,
            "msg_type": self.msg_type,
            "request_source": self.request_source,
            "business_keys": self.business_keys,
        }
        return {"configurable": configurable}

    def to_messages(self) -> list[AnyMessage]:
        """Convert content to message list."""
        return [HumanMessage(content=self.content)]


class WeWorkGlobalOutput(BaseModel):
    """WeWork global output model."""

    urls: str = Field(default="", description="Related URLs")
    context: str = Field(default="", description="Context information")
    answer_success: int = Field(default=0, description="Answer success flag")
    docs: list[str] = Field(default_factory=list, description="Related documents")


class WeWorkStreamResponse(BaseModel):
    """WeWork streaming response model."""

    response: str = Field(default="", description="Response content")
    finished: bool = Field(default=False, description="Whether response is finished")
    global_output: WeWorkGlobalOutput = Field(
        default_factory=WeWorkGlobalOutput,
        description="Global output information",
    )


class WeWorkChatResponse(BaseModel):
    """WeWork chat response model for non-streaming."""

    response: str = Field(default="", description="Response content")
    session_id: str = Field(default="", description="Session ID")
    global_output: WeWorkGlobalOutput = Field(
        default_factory=WeWorkGlobalOutput,
        description="Global output information",
    )


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""

    status: str = Field(default="healthy", description="Service health status")


class ErrorResponse(BaseModel):
    """Response model for error cases."""

    error: str = Field(..., description="Error message")
    detail: str | None = Field(default=None, description="Detailed error information")


class WeWorkChannel(BaseChannel):
    """Channel for exposing LangGraph apps through WeWork robot protocol.

    This channel creates a FastAPI router with endpoints compatible with
    WeWork robot message format.

    Example:
        >>> from fastapi import FastAPI
        >>> from orcakit_sdk.agent import Agent
        >>> from orcakit_sdk.channels.wework_channel import WeWorkChannel
        >>>
        >>> fastapi_app = FastAPI()
        >>> agent = Agent(graph)
        >>> channel = WeWorkChannel()
        >>> channel.create_router(fastapi_app, agent.agent_executor, prefix="/api")
    """

    def __init__(self) -> None:
        """Initialize the WeWork channel."""
        self.agent_executor: AgentExecutor | None = None

    @override
    def create_router(
        self,
        fastapi_app: FastAPI,
        agent_executor: AgentExecutor,
        url_prefix: str = "/wework",
        **_kwargs: object,
    ) -> None:
        """Create and register FastAPI router with WeWork-compatible endpoints.

        Args:
            fastapi_app: The FastAPI application to register routes on.
            agent_executor: The AgentExecutor instance to create a router for.
            prefix: Path prefix for the router endpoints.
            **_kwargs: Additional arguments for future extension.
        """
        self.agent_executor = agent_executor
        router = self._create_router(url_prefix)
        fastapi_app.include_router(router)

    def _create_router(self, prefix: str = "") -> APIRouter:
        """Create a FastAPI router with WeWork-compatible endpoints.

        Args:
            prefix: Path prefix for the router endpoints.

        Returns:
            A FastAPI router with /health, /call, and /stream endpoints.

        Raises:
            RuntimeError: If no agent instance has been set.
        """
        if self.agent_executor is None:
            raise RuntimeError(
                "No agent instance available. Call create_router() first."
            )

        prefix = self.normalize_prefix(prefix)
        router = APIRouter(prefix=prefix, tags=["WeWork Protocol"])
        executor = self.agent_executor

        @router.get("/health", response_model=HealthResponse)
        async def health_check() -> HealthResponse:
            """Health check endpoint."""
            return HealthResponse(status="healthy")

        @router.post("/call", response_model=None)
        async def call(
            request: WeWorkChatRequest,
        ) -> WeWorkChatResponse | ErrorResponse:
            """Chat endpoint for single-turn conversation."""
            logger.info(
                f"WeWork call request: user={request.user}, msg_id={request.msg_id}"
            )
            try:
                config = request.to_config()
                messages = request.to_messages()
                result = await executor.call(
                    messages,
                    user=request.user,
                    thread_id=request.session_id,
                    tags=["wework"],
                    config=config,
                )

                content = self.extract_content(result)
                session_id = str(config.get("configurable", {}).get("thread_id", ""))

                return WeWorkChatResponse(
                    response=content,
                    session_id=session_id,
                    global_output=WeWorkGlobalOutput(),
                )
            except Exception as e:
                logger.exception("Error in WeWork call endpoint")
                return ErrorResponse(error=str(e))

        @router.post("/stream", response_model=None)
        async def stream(request: WeWorkChatRequest) -> StreamingResponse:
            """Stream endpoint for streaming chat responses."""
            logger.info(
                f"WeWork stream request: user={request.user}, msg_id={request.msg_id}"
            )

            config = request.to_config()
            messages = request.to_messages()

            async def generate():
                try:
                    async for content in executor.stream_content(
                        messages,
                        user=request.user,
                        thread_id=request.session_id,
                        tags=["wework"],
                        config=config,
                    ):
                        if content:
                            output = WeWorkStreamResponse(
                                response=content,
                                finished=False,
                                global_output=WeWorkGlobalOutput(),
                            )
                            yield f"data: {json.dumps(output.model_dump(), ensure_ascii=False)}\n\n"
                except Exception as e:
                    logger.error(f"WeWork stream error: {e}", exc_info=True)
                    error_response = {"error": str(e)}
                    yield f"data: {json.dumps(error_response, ensure_ascii=False)}\n\n"
                finally:
                    logger.info("WeWork stream finished")
                    output = WeWorkStreamResponse(
                        response="",
                        finished=True,
                        global_output=WeWorkGlobalOutput(answer_success=1),
                    )
                    yield f"data: {json.dumps(output.model_dump(), ensure_ascii=False)}\n\n"

            return StreamingResponse(
                generate(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                    "Content-Type": "text/event-stream; charset=utf-8",
                    "Transfer-Encoding": "chunked",
                },
            )

        return router
