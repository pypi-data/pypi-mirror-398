"""App class for wrapping LangGraph StateGraph."""

from __future__ import annotations

import json
import logging
import os
import uuid
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Protocol

from langchain_core.messages import AnyMessage
from langchain_core.runnables.config import RunnableConfig
from langfuse import Langfuse
from langfuse.langchain import CallbackHandler
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
from typing_extensions import override

logger = logging.getLogger(__name__)

# Blocked instrumentation scopes to filter out A2A SDK traces
_BLOCKED_SCOPES = ["a2a-python-sdk"]

# Global Langfuse client instance (initialized once with blocked scopes)
_langfuse_client: Langfuse | None = None


class AsyncCloseable(Protocol):
    """Protocol for objects that can be closed asynchronously."""

    async def close(self) -> None:
        """Close the resource."""
        ...


def _get_langfuse_client() -> Langfuse:
    """Get or initialize the global Langfuse client with blocked scopes.

    Returns:
        Langfuse client instance with A2A SDK traces filtered out.
    """
    global _langfuse_client
    if _langfuse_client is None:
        _langfuse_client = Langfuse(blocked_instrumentation_scopes=_BLOCKED_SCOPES)
    return _langfuse_client


class AgentExecutor(ABC):
    """Abstract interface for agent implementations.

    This interface defines the contract that all agent implementations
    should follow, providing a consistent API for different agent types.
    """

    @abstractmethod
    async def call(
        self,
        messages: list[AnyMessage],
        thread_id: str | None = None,
        user: str | None = None,
        tags: list[str] | None = None,
        config: RunnableConfig | None = None,
        **kwargs: object,
    ) -> dict[str, object]:
        """Invoke the agent with a list of messages.

        Args:
            messages: List of messages to send to the agent.
            thread_id: Optional thread ID for conversation continuity.
            user: Optional user ID for tracking user interactions.
            tags: Optional tags for tracking user interactions.
            config: Optional configuration for the agent execution.
            **kwargs: Additional keyword arguments for implementation-specific options.

        Returns:
            Dictionary containing the agent's response.
        """
        ...

    @abstractmethod
    async def stream(
        self,
        messages: list[AnyMessage],
        thread_id: str | None = None,
        user: str | None = None,
        tags: list[str] | None = None,
        config: RunnableConfig | None = None,
        **kwargs: object,
    ) -> AsyncGenerator[dict[str, object], None]:
        """Stream responses from the agent with a list of messages.

        Args:
            messages: List of messages to send to the agent.
            thread_id: Optional thread ID for conversation continuity.
            user: Optional user ID for tracking user interactions.
            tags: Optional tags for tracking user interactions.
            config: Optional configuration for the agent execution.
            **kwargs: Additional keyword arguments for implementation-specific options.

        Yields:
            Dictionaries containing partial response content and metadata.
        """
        ...

    @abstractmethod
    async def stream_content(
        self,
        messages: list[AnyMessage],
        thread_id: str | None = None,
        user: str | None = None,
        tags: list[str] | None = None,
        config: RunnableConfig | None = None,
        include_tool_result: bool = True,
        **kwargs: object,
    ) -> AsyncGenerator[str, None]:
        """Stream content strings extracted from the agent's responses.

        This method wraps the stream() method and extracts human-readable content
        including text responses, tool calls, and tool execution results.

        Args:
            messages: List of messages to send to the agent.
            thread_id: Optional thread ID for conversation continuity.
            user: Optional user ID for tracking user interactions.
            tags: Optional tags for tracking user interactions.
            config: Optional configuration for the agent execution.
            include_tool_result: Whether to include tool calls and results in output. Defaults to True.
            **kwargs: Additional keyword arguments for implementation-specific options.
                - ignore_nodes: List of node names to ignore in stream output.
                    Useful for hiding supervisor routing decisions in multi-agent systems.

        Yields:
            String content extracted from stream events.
        """
        ...


class LangGraphAgentExecutor(AgentExecutor):
    """Wrapper for LangGraph StateGraph providing deployment capabilities.

    This class encapsulates a LangGraph StateGraph and provides convenient
    methods for running and deploying the graph with different runners.

    This class implements the AgentInterface to provide a consistent API
    for interacting with different agent types.

    Example:
        >>> from langgraph.graph import StateGraph
        >>> from react_agent import App, SimpleRunner
        >>>
        >>> # Create your StateGraph
        >>> graph = StateGraph(...)
        >>> # ... configure graph ...
        >>>
        >>> # Wrap it with App
        >>> app = App(graph)
        >>>
        >>> # Run with built-in simple runner
        >>> app.run(host="0.0.0.0", port=8090)
        >>>
        >>> # Or deploy with custom runner
        >>> await app.deploy(SimpleRunner(host="0.0.0.0", port=8091))
    """

    def __init__(
        self, graph: StateGraph | CompiledStateGraph, name: str = "agent"
    ) -> None:
        """Initialize the App with a StateGraph or CompiledStateGraph.

        Args:
            graph: LangGraph StateGraph instance or compiled graph to wrap.
            name: Name for the compiled graph.
        """
        # Check if graph is already compiled
        if hasattr(graph, "invoke") and hasattr(graph, "ainvoke"):
            # Already compiled
            self._graph: StateGraph | None = None
            self._compiled_graph: CompiledStateGraph = graph
        else:
            # Not compiled yet
            self._graph = graph
            self._compiled_graph: CompiledStateGraph = graph.compile(name=name)

        self._compiled_graph.name = name
        self._name = name

        # Checkpointer state - will be initialized lazily for async postgres
        self._checkpointer_initialized = False
        self._postgres_uri = os.getenv("POSTGRES_URI")
        self._async_checkpointer_context: AsyncCloseable | None = None

        # Set sync checkpointer initially (MemorySaver as fallback)
        if not self._postgres_uri:
            self._compiled_graph.checkpointer = self._get_sync_checkpointer()

        # Initialize Langfuse client with blocked scopes to filter A2A traces
        self._langfuse = _get_langfuse_client()

        # Initialize Langfuse CallbackHandler for Langchain (tracing)
        self._langfuse_handler = CallbackHandler()

    @property
    def graph(self) -> StateGraph | None:
        """Get the underlying StateGraph.

        Returns:
            The wrapped StateGraph instance, or None if initialized with compiled graph.
        """
        return self._graph

    @property
    def compiled_graph(self) -> CompiledStateGraph:
        """Get the compiled graph.

        Returns:
            The compiled graph instance ready for execution.
        """
        return self._compiled_graph

    def _get_sync_checkpointer(self):
        """Get synchronous checkpointer (MemorySaver).

        Returns:
            MemorySaver instance or None.
        """
        try:
            from langgraph.checkpoint.memory import MemorySaver

            logger.info("Using in-memory checkpointer")
            return MemorySaver()
        except ImportError:
            logger.error("No checkpointer available, running without persistence")
            return None

    async def _ensure_async_checkpointer(self) -> None:
        """Ensure async PostgreSQL checkpointer is initialized.

        This method lazily initializes the AsyncPostgresSaver when POSTGRES_URI
        is configured. It uses AsyncConnectionPool for connection management.
        """
        if self._checkpointer_initialized:
            return

        if not self._postgres_uri:
            # No postgres URI, use sync checkpointer (already set in __init__)
            self._checkpointer_initialized = True
            return

        try:
            from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
            from psycopg_pool import AsyncConnectionPool

            logger.info(f"Initializing AsyncPostgresSaver at {self._postgres_uri}")

            # Create async connection pool with keepalive and reconnect settings
            # - min_size: minimum connections to keep open
            # - max_size: maximum connections allowed
            # - max_idle: max time (seconds) a connection can be idle before being closed
            # - reconnect_timeout: time to wait for reconnection
            # - check: enable connection health check before use
            pool = AsyncConnectionPool(
                conninfo=self._postgres_uri,
                open=False,
                min_size=1,
                max_size=10,
                max_idle=300,  # 5 minutes idle timeout
                reconnect_timeout=60,
                check=AsyncConnectionPool.check_connection,
                kwargs={
                    "keepalives": 1,
                    "keepalives_idle": 30,
                    "keepalives_interval": 10,
                    "keepalives_count": 5,
                },
            )
            await pool.open()

            # Store pool reference for cleanup
            self._async_checkpointer_context = pool

            # Create checkpointer with the pool
            checkpointer = AsyncPostgresSaver(pool)

            # Setup tables
            await checkpointer.setup()

            # Set the checkpointer on the compiled graph
            self._compiled_graph.checkpointer = checkpointer

            logger.info("AsyncPostgresSaver initialized successfully")
            self._checkpointer_initialized = True

        except ImportError as e:
            logger.warning(
                f"POSTGRES_URI is configured but required packages are not installed: {e}. "
                "Please install with: pip install langgraph-checkpoint-postgres psycopg[pool]"
            )
            # Fall back to memory saver
            self._compiled_graph.checkpointer = self._get_sync_checkpointer()
            self._checkpointer_initialized = True

        except Exception as e:
            logger.error(f"Failed to initialize AsyncPostgresSaver: {str(e)}")
            # Fall back to memory saver
            self._compiled_graph.checkpointer = self._get_sync_checkpointer()
            self._checkpointer_initialized = True

    async def close(self) -> None:
        """Close the async checkpointer connection if initialized.

        Call this method when shutting down to properly close database connections.
        """
        if self._async_checkpointer_context is not None:
            try:
                await self._async_checkpointer_context.close()
                logger.info("AsyncPostgresSaver connection pool closed")
            except Exception as e:
                logger.error(f"Error closing AsyncPostgresSaver: {str(e)}")
            finally:
                self._async_checkpointer_context = None

    def _ensure_config_with_langfuse(
        self,
        config: RunnableConfig | None = None,
        thread_id: str | None = None,
        user: str | None = None,
        tags: list[str] | None = None,
    ) -> RunnableConfig:
        """Ensure config has langfuse callbacks and metadata for tracing.

        Args:
            config: Optional RunnableConfig configuration.
            thread_id: Optional thread/session ID for conversation continuity.
            user: Optional user ID for tracking user interactions.
            tags: Optional list of tags for tracing.

        Returns:
            RunnableConfig with langfuse callbacks and metadata configured.
        """
        if config is None:
            config = {}

        # Ensure callbacks list exists and includes a langfuse handler
        if "callbacks" not in config:
            config["callbacks"] = [self._langfuse_handler]
        elif self._langfuse_handler not in config["callbacks"]:
            config["callbacks"].append(self._langfuse_handler)

        # Ensure configurable section exists
        if "configurable" not in config:
            config["configurable"] = {}

        # Set thread_id (generate one if not provided)
        if thread_id:
            config["configurable"]["thread_id"] = thread_id
        elif "thread_id" not in config["configurable"]:
            config["configurable"]["thread_id"] = str(uuid.uuid4())

        # Set user_name if provided
        if user:
            config["configurable"]["user_name"] = user

        # Ensure metadata section exists for langfuse
        if "metadata" not in config:
            config["metadata"] = {}

        # Set langfuse metadata
        if user:
            config["metadata"]["langfuse_user_id"] = user
        if tags:
            existing_tags: list[str] = config["metadata"].get("langfuse_tags", [])
            config["metadata"]["langfuse_tags"] = existing_tags + tags
        if thread_id:
            config["metadata"]["langfuse_session_id"] = thread_id
        elif config["configurable"].get("thread_id"):
            config["metadata"]["langfuse_session_id"] = config["configurable"][
                "thread_id"
            ]

        return config

    @override
    async def call(
        self,
        messages: list[AnyMessage],
        thread_id: str | None = None,
        user: str | None = None,
        tags: list[str] | None = None,
        config: RunnableConfig | None = None,
        **kwargs: object,
    ) -> dict[str, object]:
        """Invoke the compiled graph with a chat request.

        Args:
            messages: List of messages to send to the graph.
            thread_id: Optional thread ID for conversation continuity.
            user: Optional user ID for tracking user interactions.
            tags: Optional tags for tracing.
            config: Optional configuration for the graph execution.
            **kwargs: Additional keyword arguments (reserved for future use).

        Returns:
            Dictionary containing the assistant's response.
        """
        # Ensure async checkpointer is initialized
        await self._ensure_async_checkpointer()

        config = self._ensure_config_with_langfuse(
            config, thread_id=thread_id, user=user, tags=tags
        )
        logger.debug(f"call() - config: {config}")
        logger.debug(f"call() - messages: {messages}")
        return await self._compiled_graph.ainvoke({"messages": messages}, config=config)

    @override
    async def stream(
        self,
        messages: list[AnyMessage],
        thread_id: str | None = None,
        user: str | None = None,
        tags: list[str] | None = None,
        config: RunnableConfig | None = None,
        **kwargs: object,
    ) -> AsyncGenerator[dict[str, object], None]:
        """Stream messages from the compiled graph with a chat request.

        Args:
            messages: List of messages to send to the graph.
            thread_id: Optional thread ID for conversation continuity.
            user: Optional user ID for tracking user interactions.
            tags: Optional tags for tracing.
            config: Optional configuration for the graph execution.
            **kwargs: Additional keyword arguments (reserved for future use).

        Yields:
            Dictionaries containing message content and metadata.
        """
        # Ensure async checkpointer is initialized
        await self._ensure_async_checkpointer()

        config = self._ensure_config_with_langfuse(
            config, thread_id=thread_id, user=user, tags=tags
        )
        logger.debug(f"stream() - config: {config}")
        logger.debug(f"stream() - messages: {messages}")

        # Stream events from the compiled graph
        # astream with stream_mode returns tuples of (event_type, data)
        async for event in self._compiled_graph.astream(
            {"messages": messages},
            config=config,
            stream_mode=["updates", "custom", "messages"],
            subgraphs=True,
        ):
            yield event

    @override
    async def stream_content(
        self,
        messages: list[AnyMessage],
        thread_id: str | None = None,
        user: str | None = None,
        tags: list[str] | None = None,
        config: RunnableConfig | None = None,
        include_tool_result: bool = False,
        **kwargs: object,
    ) -> AsyncGenerator[str, None]:
        """Stream content strings extracted from the agent's responses.

        This method wraps the stream() method and extracts human-readable content
        including text responses, tool calls, and tool execution results.

        Args:
            messages: List of messages to send to the graph.
            thread_id: Optional thread ID for conversation continuity.
            user: Optional user ID for tracking user interactions.
            tags: Optional tags for tracing.
            config: Optional configuration for the graph execution.
            include_tool_result: Whether to include tool calls and results in output. Defaults to False.
            **kwargs: Additional keyword arguments.
                - ignore_nodes: List of node names to ignore in stream output.
                    Useful for hiding supervisor routing decisions in multi-agent systems.
                    Example: ignore_nodes=["supervisor"] to hide supervisor node output.

        Yields:
            String content extracted from stream events.
        """
        # Get ignore_nodes from kwargs
        ignore_nodes_value = kwargs.get("ignore_nodes")
        ignore_nodes: list[str] = (
            ignore_nodes_value if isinstance(ignore_nodes_value, list) else []
        )

        # Cache for accumulating tool calls across chunks
        # Structure: {cache_key: {"name": str, "args": dict}}
        accumulated_tool_calls: dict[str, dict[str, str | dict[str, object]]] = {}

        async for event in self.stream(
            messages, thread_id=thread_id, user=user, tags=tags, config=config
        ):
            # Validate event format
            if not isinstance(event, tuple) or len(event) != 3:
                continue

            __, event_type, data = event

            # Check if current node should be ignored based on langgraph_node in metadata
            # data is a tuple like (message, metadata_dict)
            # metadata_dict contains 'langgraph_node' field
            if ignore_nodes and isinstance(data, tuple) and len(data) >= 2:
                metadata = data[1]
                if isinstance(metadata, dict):
                    current_node = metadata.get("langgraph_node")
                    if current_node and current_node in ignore_nodes:
                        logger.debug(f"Ignoring output from node: {current_node}")
                        continue

            # Only handle "messages" events
            if event_type != "messages" or not isinstance(data, tuple) or len(data) < 1:
                continue

            message = data[0]
            message_type = (
                message.__class__.__name__ if hasattr(message, "__class__") else None
            )

            # Case 1: ToolMessage - Tool execution results
            if message_type and "ToolMessage" in message_type:
                # Skip tool results if include_tool_result is False
                if not include_tool_result:
                    continue

                tool_name = getattr(message, "name", "未知工具")
                tool_content = getattr(message, "content", "")

                # Format tool result nicely
                content = f"\n\n🔧 工具执行结果：{tool_name}\n{tool_content}\n"
                if content.strip():
                    yield content
                continue

            # Case 2: AIMessage/AIMessageChunk - AI response and tool calls
            content_parts = []

            # Extract text content
            text_content = ""
            if hasattr(message, "content"):
                text_content = str(message.content) if message.content else ""
            elif isinstance(message, dict) and "content" in message:
                content_val = message.get("content", "")
                if isinstance(content_val, list):
                    # Handle list content (multimodal format)
                    text_content = "".join(
                        item.get("text", "") if isinstance(item, dict) else str(item)
                        for item in content_val
                    )
                else:
                    text_content = str(content_val) if content_val else ""

            # Add text content if present
            if text_content:
                content_parts.append(text_content)

            # Extract and accumulate tool calls (only if include_tool_result is True)
            if include_tool_result:
                tool_calls = None
                if hasattr(message, "tool_calls") and message.tool_calls:
                    tool_calls = message.tool_calls
                elif isinstance(message, dict) and message.get("tool_calls"):
                    tool_calls = message["tool_calls"]

                # Process tool calls - accumulate chunks
                if tool_calls:
                    for tc in tool_calls:
                        # Get tool call ID (use index or id field)
                        tc_id = None
                        tc_index = None

                        if isinstance(tc, dict):
                            tc_id = tc.get("id")
                            tc_index = tc.get("index", 0)
                        else:
                            tc_id = getattr(tc, "id", None)
                            tc_index = getattr(tc, "index", 0)

                        # Use ID as key, fallback to index
                        cache_key = tc_id if tc_id else f"index_{tc_index}"

                        # Get tool name and args
                        tool_name = (
                            tc.get("name")
                            if isinstance(tc, dict)
                            else getattr(tc, "name", None)
                        )
                        tool_args = (
                            tc.get("args", {})
                            if isinstance(tc, dict)
                            else getattr(tc, "args", {})
                        )

                        # Initialize or update cache entry
                        if cache_key not in accumulated_tool_calls:
                            accumulated_tool_calls[cache_key] = {
                                "name": tool_name or "",
                                "args": dict(tool_args) if tool_args else {},
                            }
                        else:
                            # Update name if we get it (might be empty in first chunk)
                            if tool_name:
                                accumulated_tool_calls[cache_key]["name"] = tool_name
                            # Merge args (in case they come in chunks)
                            if tool_args:
                                existing_args = accumulated_tool_calls[cache_key][
                                    "args"
                                ]
                                if isinstance(existing_args, dict) and isinstance(
                                    tool_args, dict
                                ):
                                    existing_args.update(tool_args)

                        # Check if this tool call is complete (has both name and non-empty args)
                        cached_call = accumulated_tool_calls[cache_key]
                        if cached_call["name"] and cached_call["args"]:
                            # Output complete tool call
                            args_str = json.dumps(
                                cached_call["args"], ensure_ascii=False, indent=2
                            )
                            tool_desc = f"\n\n🔧 正在调用工具：{cached_call['name']}\n参数：\n{args_str}\n"
                            content_parts.append(tool_desc)

                            # Remove from cache after outputting
                            del accumulated_tool_calls[cache_key]

            # Yield combined content if any
            if content_parts:
                content = "".join(content_parts)
                if content.strip():
                    yield content

    async def _stream_events(
        self,
        messages: list[AnyMessage],
        config: RunnableConfig | None = None,
    ) -> AsyncGenerator[dict[str, object], None]:
        """Stream events from the compiled graph with a chat request.

        Args:
            messages: List of messages to send to the graph.
            config: Optional configuration for the graph execution.

        Yields:
            Dictionaries containing event content and metadata.
        """
        try:
            async for event in self._compiled_graph.astream_events(
                {"messages": messages}, config=config
            ):
                kind = event["event"]

                # Stream tokens from LLM
                if kind == "on_chat_model_stream":
                    content = event["data"]["chunk"].content
                    if content:
                        # Convert content to string if it's a list
                        if isinstance(content, str):
                            content_str = content
                        elif isinstance(content, list):
                            content_str = "".join(str(item) for item in content)
                        else:
                            content_str = str(content)

                        yield {
                            "content": content_str,
                            "role": "assistant",
                            "finished": False,
                        }

                # Tool call events
                elif kind == "on_tool_start":
                    logger.info(
                        f"\n--- Calling Tool: {event['name']} with args {event['data'].get('input')} ---"
                    )

                elif kind == "on_tool_end":
                    logger.info(
                        f"\n--- Tool {event['name']} Finished, Output: {event['data'].get('output')} ---"
                    )

                # Chain events (node start/end)
                elif kind == "on_chain_end":
                    logger.debug(f"\n--- Node '{event['name']}' Ended ---")
                    logger.debug(f"Output: {event['data'].get('output')}")

            yield {
                "content": "",
                "role": "assistant",
                "finished": True,
            }
        except Exception as e:
            logger.error(f"Error in streaming: {str(e)}", exc_info=True)
            yield {
                "content": f"Error: {str(e)}",
                "role": "error",
                "finished": True,
            }
            raise
        finally:
            logger.info("Stream completed")
