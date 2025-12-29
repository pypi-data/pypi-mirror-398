"""A2A (Agent-to-Agent) channel for exposing agents through A2A protocol."""

from __future__ import annotations

import logging
import uuid
from collections.abc import AsyncIterable
from typing import TYPE_CHECKING, Any, Literal

import httpx
from a2a.server.agent_execution import (
    AgentExecutor as A2AAgentExecutor,
)
from a2a.server.agent_execution import (
    RequestContext,
)
from a2a.server.apps import A2AStarletteApplication
from a2a.server.events import EventQueue
from a2a.server.request_handlers import (
    DefaultRequestHandler,
)
from a2a.server.tasks import (
    BasePushNotificationSender,
    InMemoryPushNotificationConfigStore,
    InMemoryTaskStore,
    TaskUpdater,
)
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    InternalError,
    InvalidParamsError,
    Part,
    Task,
    TextPart,
    UnsupportedOperationError,
)
from a2a.utils import new_task
from a2a.utils.errors import ServerError
from langchain_core.messages import AnyMessage, HumanMessage
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from starlette.applications import Starlette
from typing_extensions import override

from orcakit_sdk.runner.agent_executor import AgentExecutor

from .base import BaseChannel

if TYPE_CHECKING:
    from fastapi import FastAPI

logger = logging.getLogger(__name__)


class ResponseFormat(BaseModel):
    """Response format for A2A agent."""

    status: Literal["input_required", "completed", "error"] = "input_required"
    message: str


class A2AAgentWrapper:
    """Wrapper for AgentExecutor to provide A2A-compatible interface."""

    SUPPORTED_CONTENT_TYPES: list[str] = ["text", "text/plain"]

    def __init__(self, agent_executor: AgentExecutor) -> None:
        """Initialize the A2A agent wrapper.

        Args:
            agent_executor: The underlying AgentExecutor instance.
        """
        self.agent_executor: AgentExecutor = agent_executor
        logger.info("A2AAgentWrapper initialized")

    async def stream(
        self,
        query: str,
        session_id: str,
    ) -> AsyncIterable[dict[str, str | bool]]:
        """Stream responses from the agent.

        Args:
            query: The user query.
            session_id: Session ID for conversation continuity.

        Yields:
            Dictionaries containing response content and status.
        """
        messages: list[AnyMessage] = [HumanMessage(content=query)]

        try:
            full_response: str = ""
            # Pass thread_id directly to ensure proper Langfuse tracing
            async for event in self.agent_executor.stream(
                messages, thread_id=session_id, tags=["a2a"]
            ):
                # Extract content from LangGraph streaming events
                # Event format: (namespace, event_type, (message, metadata))
                if isinstance(event, tuple) and len(event) == 3:
                    namespace, event_type, data = event

                    # Handle messages event - contains AIMessageChunk
                    if (
                        event_type == "messages"
                        and isinstance(data, tuple)
                        and len(data) >= 1
                    ):
                        message = data[0]
                        content = ""

                        # Extract content from message
                        if hasattr(message, "content"):
                            content = str(message.content) if message.content else ""
                        elif isinstance(message, dict) and "content" in message:
                            content = (
                                str(message["content"]) if message["content"] else ""
                            )

                        if content:
                            full_response += content
                            yield {
                                "is_task_complete": False,
                                "require_user_input": False,
                                "content": content,
                                "finished": False,
                            }

            yield {
                "is_task_complete": True,
                "require_user_input": False,
                "content": full_response,
                "finished": True,
            }
        except Exception as e:
            logger.error(f"Error in agent stream: {e}", exc_info=True)
            raise


class A2AExecutorAdapter(A2AAgentExecutor):
    """Adapter to make AgentExecutor compatible with A2A protocol."""

    def __init__(self, agent_wrapper: A2AAgentWrapper) -> None:
        """Initialize the A2A executor adapter.

        Args:
            agent_wrapper: The A2A agent wrapper instance.
        """
        super().__init__()
        self.agent_wrapper: A2AAgentWrapper = agent_wrapper

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Execute the agent request.

        Args:
            context: The request context.
            event_queue: The event queue for sending responses.
        """
        error = self._validate_request(context)
        if error:
            raise ServerError(error=InvalidParamsError())

        query = context.get_user_input()
        task = context.current_task
        if not task:
            task = new_task(context.message)
            await event_queue.enqueue_event(task)
        updater = TaskUpdater(event_queue, task.id, task.context_id)

        try:
            artifact_id = str(uuid.uuid4())
            await updater.add_artifact(
                [Part(root=TextPart(text=""))],
                name="conversion_result",
                append=False,
                last_chunk=False,
                artifact_id=artifact_id,
            )

            async for item in self.agent_wrapper.stream(query, task.context_id):
                is_task_complete = item.get("is_task_complete", False)
                require_user_input = item.get("require_user_input", False)
                content = item.get("content", "")

                if not is_task_complete and not require_user_input:
                    await updater.add_artifact(
                        [Part(root=TextPart(text=content))],
                        name="conversion_result",
                        append=True,
                        last_chunk=False,
                        artifact_id=artifact_id,
                    )
                elif require_user_input:
                    await updater.add_artifact(
                        [Part(root=TextPart(text=content))],
                        name="conversion_result",
                        append=False,
                        last_chunk=True,
                        artifact_id=artifact_id,
                    )
                    break
                else:
                    await updater.add_artifact(
                        [Part(root=TextPart(text=content))],
                        name="conversion_result",
                        append=True,
                        last_chunk=True,
                        artifact_id=artifact_id,
                    )
                    await updater.complete()
                    break

        except Exception as e:
            logger.error(f"An error occurred while streaming the response: {e}")
            raise ServerError(error=InternalError()) from e

    def _validate_request(self, context: RequestContext) -> bool:
        """Validate the request context.

        Args:
            context: The request context to validate.

        Returns:
            True if validation fails, False otherwise.
        """
        user_input = context.get_user_input()
        if not user_input or not user_input.strip():
            return True
        return False

    async def cancel(
        self,
        request: RequestContext,
        event_queue: EventQueue,
    ) -> Task | None:
        """Cancel the current task.

        Args:
            request: The request context.
            event_queue: The event queue.

        Raises:
            ServerError: Always raises UnsupportedOperationError.
        """
        _ = request, event_queue  # Unused
        raise ServerError(error=UnsupportedOperationError())


class A2AChannelConfig(BaseSettings):
    """Configuration for A2A channel with environment variable support.

    Environment variables are prefixed with A2A_ (e.g., A2A_NAME, A2A_STREAMING).
    """

    model_config = SettingsConfigDict(
        env_prefix="A2A_",
        env_ignore_empty=True,
        extra="ignore",
    )

    name: str = Field(default="Agent", description="Agent name")
    description: str = Field(default="AI Assistant", description="Agent description")
    version: str = Field(default="1.0.0", description="Agent version")
    streaming: bool = Field(default=True, description="Enable streaming support")
    push_notifications: bool = Field(
        default=True, description="Enable push notifications"
    )
    skills: list[Any] = Field(default_factory=list, description="Agent skills")


class A2AChannel(BaseChannel):
    """Channel for exposing agents through A2A (Agent-to-Agent) protocol.

    This channel creates an A2A-compatible application for agent-to-agent
    communication following the A2A protocol specification.

    Example:
        >>> from fastapi import FastAPI
        >>> from orcakit_sdk.agent import Agent
        >>> from orcakit_sdk.channels.a2a_channel import A2AChannel, A2AChannelConfig
        >>>
        >>> fastapi_app = FastAPI()
        >>> agent = Agent(graph)
        >>> config = A2AChannelConfig(
        ...     name="My Agent",
        ...     description="An intelligent assistant",
        ...     skills=[AgentSkill(id="chat", name="Chat", description="General chat")]
        ... )
        >>> channel = A2AChannel(config)
        >>> channel.create_router(fastapi_app, agent.agent_executor, prefix="/a2a")
    """

    def __init__(
        self,
        config: A2AChannelConfig | None = None,
        agent_card: AgentCard | None = None,
    ) -> None:
        """Initialize the A2A channel.

        Args:
            config: Configuration for the A2A channel. Used to create AgentCard if agent_card is not provided.
            agent_card: Pre-configured AgentCard. If provided, config is ignored.
        """
        if agent_card:
            self._agent_card = agent_card
        else:
            cfg = config or A2AChannelConfig()
            capabilities = AgentCapabilities(
                streaming=cfg.streaming,
                pushNotifications=cfg.push_notifications,
            )
            self._agent_card = AgentCard(
                name=cfg.name,
                description=cfg.description,
                url="",  # Will be set in _build_a2a_starlette_app
                version=cfg.version,
                defaultInputModes=A2AAgentWrapper.SUPPORTED_CONTENT_TYPES,
                defaultOutputModes=A2AAgentWrapper.SUPPORTED_CONTENT_TYPES,
                capabilities=capabilities,
                skills=cfg.skills,
            )
        self.agent_executor: AgentExecutor | None = None
        self.agent_wrapper: A2AAgentWrapper | None = None

    @override
    def create_router(
        self,
        fastapi_app: FastAPI,
        agent_executor: AgentExecutor,
        url_prefix: str = "/a2a-protocol",
        **kwargs: str,
    ) -> None:
        """Create and register full A2A protocol endpoints on FastAPI.

        This method mounts a complete A2A Starlette application to the FastAPI app,
        providing full A2A protocol support including streaming and task management.

        Args:
            fastapi_app: The FastAPI application to register routes on.
            agent_executor: The AgentExecutor instance to create a router for.
            url_prefix: Path prefix for the A2A endpoints (e.g., "/a2a").
            **kwargs: Additional arguments. Supports:
                - base_url: Base URL for agent card (e.g., "http://localhost:8000").
        """
        self.agent_executor = agent_executor
        self.agent_wrapper = A2AAgentWrapper(agent_executor)

        mount_path = self.normalize_prefix(url_prefix)

        # Build agent card URL - must be a complete HTTP/HTTPS URL with trailing slash
        base_url = kwargs.get("base_url", "http://localhost:8888")
        agent_url = f"{base_url.rstrip('/')}{mount_path}/"

        a2a_app = self._build_a2a_starlette_app(agent_url)
        fastapi_app.mount(mount_path, a2a_app)

    def _build_a2a_starlette_app(self, agent_url: str) -> Starlette:
        """Build A2A Starlette app with specified URL for agent card.

        Args:
            agent_url: Full URL for the agent card.

        Returns:
            A Starlette application configured for A2A protocol.
        """
        if self.agent_wrapper is None:
            raise RuntimeError(
                "agent_wrapper not initialized. Call create_a2a_app first."
            )

        # Update agent card URL
        self._agent_card.url = agent_url

        httpx_client = httpx.AsyncClient()
        notification_config_store = InMemoryPushNotificationConfigStore()
        a2a_executor = A2AExecutorAdapter(self.agent_wrapper)

        request_handler = DefaultRequestHandler(
            agent_executor=a2a_executor,
            task_store=InMemoryTaskStore(),
            push_sender=BasePushNotificationSender(
                httpx_client, notification_config_store
            ),
        )

        server = A2AStarletteApplication(
            agent_card=self._agent_card,
            http_handler=request_handler,
        )

        return server.build()
