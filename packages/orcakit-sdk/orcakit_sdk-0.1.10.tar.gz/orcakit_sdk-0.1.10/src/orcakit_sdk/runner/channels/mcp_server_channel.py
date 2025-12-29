"""MCP Server channel implementing Streamable HTTP transport protocol.

This module implements the Model Context Protocol (MCP) Streamable HTTP transport
as specified in the 2025-03-26 specification.

Reference: https://modelcontextprotocol.io/specification/2025-03-26/basic/transports
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Header, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage
from langchain_core.runnables.config import RunnableConfig
from pydantic import BaseModel, Field
from typing_extensions import override

from orcakit_sdk.runner.agent_executor import AgentExecutor

from .base import BaseChannel

if TYPE_CHECKING:
    from fastapi import FastAPI

logger = logging.getLogger(__name__)

# MCP Protocol version
MCP_PROTOCOL_VERSION = "2025-03-26"

# JSON-RPC error codes
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603


class MCPMessage(BaseModel):
    """MCP message with role and content."""

    role: str = Field(
        ...,
        description="Message role: 'user', 'assistant', or 'system'",
    )
    content: str = Field(..., description="Message content")


class MCPToolArguments(BaseModel):
    """Arguments for MCP tool call."""

    messages: list[MCPMessage] = Field(
        ...,
        description="List of messages with role and content",
    )
    thread_id: str | None = Field(
        default=None,
        description="Thread ID for conversation continuity",
    )
    user: str | None = Field(
        default=None,
        description="User identifier",
    )
    tags: list[str] | None = Field(
        default=None,
        description="Tags for tracing",
    )
    config: dict[str, Any] | None = Field(
        default=None,
        description="Additional configuration",
    )
    include_tool_result: bool = Field(
        default=True,
        description="Whether to include tool execution results",
    )

    def to_runnable_config(self) -> RunnableConfig:
        """Convert to RunnableConfig format."""
        thread_id = self.thread_id if self.thread_id else str(uuid.uuid4())
        configurable: dict[str, Any] = {"thread_id": thread_id}

        if self.user:
            configurable["user"] = self.user

        base_config: RunnableConfig = {"configurable": configurable}

        if self.config:
            if "configurable" in self.config:
                base_config["configurable"].update(self.config["configurable"])
            if "metadata" in self.config:
                base_config["metadata"] = self.config["metadata"]

        return base_config

    def to_langchain_messages(self) -> list[AnyMessage]:
        """Convert MCP messages to LangChain message objects."""
        result: list[AnyMessage] = []
        for msg in self.messages:
            role = msg.role.lower()
            if role == "system":
                result.append(SystemMessage(content=msg.content))
            elif role in ("assistant", "ai"):
                result.append(AIMessage(content=msg.content))
            else:
                result.append(HumanMessage(content=msg.content))
        return result


def _create_jsonrpc_response(id: int | str | None, result: Any) -> dict[str, Any]:
    """Create a JSON-RPC 2.0 success response."""
    return {"jsonrpc": "2.0", "id": id, "result": result}


def _create_jsonrpc_error(
    id: int | str | None, code: int, message: str, data: Any = None
) -> dict[str, Any]:
    """Create a JSON-RPC 2.0 error response."""
    error: dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return {"jsonrpc": "2.0", "id": id, "error": error}


class MCPServerChannel(BaseChannel):
    """Channel implementing MCP Streamable HTTP transport protocol.

    This channel creates a FastAPI router with MCP-compatible endpoints
    following the 2025-03-26 specification for Streamable HTTP transport.

    The MCP endpoint supports:
    - POST: Send JSON-RPC requests/notifications, receive responses via JSON or SSE
    - GET: Open SSE stream for server-initiated messages

    Example:
        >>> from fastapi import FastAPI
        >>> from orcakit_sdk.agent import Agent
        >>> from orcakit_sdk.runner.channels.mcp_server_channel import MCPServerChannel
        >>>
        >>> fastapi_app = FastAPI()
        >>> agent = Agent(graph)
        >>> channel = MCPServerChannel(tool_name="chat_agent")
        >>> channel.create_router(fastapi_app, agent.agent_executor, url_prefix="/mcp")
    """

    def __init__(
        self,
        tool_name: str = "agent_executor",
        tool_description: str | None = None,
        server_name: str = "orcakit-mcp-server",
        server_version: str = "1.0.0",
    ) -> None:
        """Initialize the MCP Server channel.

        Args:
            tool_name: Name of the tool to expose in MCP protocol.
            tool_description: Description of the tool. Defaults to a generic description.
            server_name: Server name for MCP initialization.
            server_version: Server version for MCP initialization.
        """
        self.tool_name = tool_name
        self.tool_description = tool_description or (
            "Execute agent with streaming responses. "
            "Provides AI assistant capabilities with tool execution support."
        )
        self.server_name = server_name
        self.server_version = server_version
        self.agent_executor: AgentExecutor | None = None
        self._sessions: dict[str, dict[str, Any]] = {}

    @override
    def create_router(
        self,
        fastapi_app: FastAPI,
        agent_executor: AgentExecutor,
        url_prefix: str = "/mcp-server",
        **kwargs: str,
    ) -> None:
        """Create and register FastAPI router with MCP Streamable HTTP endpoints.

        Args:
            fastapi_app: The FastAPI application to register routes on.
            agent_executor: The AgentExecutor instance to create a router for.
            url_prefix: Path prefix for the router endpoints.
            **kwargs: Additional arguments (e.g., tool_name).
        """
        self.agent_executor = agent_executor

        if kwargs.get("tool_name"):
            self.tool_name = kwargs["tool_name"]

        if kwargs.get("tool_description"):
            self.tool_description = kwargs["tool_description"]

        router = self._create_router(url_prefix)
        fastapi_app.include_router(router)

    def _get_tool_input_schema(self) -> dict[str, Any]:
        """Get the JSON Schema for tool input."""
        return {
            "type": "object",
            "properties": {
                "messages": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "role": {
                                "type": "string",
                                "enum": ["user", "assistant", "system"],
                                "description": "Message role",
                            },
                            "content": {
                                "type": "string",
                                "description": "Message content",
                            },
                        },
                        "required": ["role", "content"],
                    },
                    "description": "List of messages with role and content",
                },
                "thread_id": {
                    "type": "string",
                    "description": "Thread ID for conversation continuity",
                },
                "user": {
                    "type": "string",
                    "description": "User identifier",
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Tags for tracing",
                },
                "config": {
                    "type": "object",
                    "description": "Additional configuration",
                },
                "include_tool_result": {
                    "type": "boolean",
                    "default": True,
                    "description": "Whether to include tool execution results",
                },
            },
            "required": ["messages"],
        }

    def _create_router(self, prefix: str = "") -> APIRouter:
        """Create a FastAPI router with MCP Streamable HTTP endpoints.

        Args:
            prefix: Path prefix for the router endpoints.

        Returns:
            A FastAPI router with MCP-compatible endpoints.

        Raises:
            RuntimeError: If no agent executor has been set.
        """
        if self.agent_executor is None:
            raise RuntimeError(
                "No agent executor available. Call create_router() first."
            )

        prefix = self.normalize_prefix(prefix)
        router = APIRouter(
            prefix=prefix, tags=["MCP Server Protocol"], redirect_slashes=False
        )
        executor = self.agent_executor

        @router.get("/health")
        async def health_check() -> dict[str, str]:
            """Health check endpoint."""
            return {
                "status": "healthy",
                "protocol": "mcp",
                "transport": "streamable-http",
            }

        @router.post("")
        async def mcp_post_endpoint(
            request: Request,
            accept: str = Header(default="application/json"),
            mcp_session_id: str | None = Header(default=None, alias="Mcp-Session-Id"),
        ) -> Response:
            """MCP Streamable HTTP POST endpoint.

            Handles JSON-RPC requests, notifications, and responses.
            Can return either JSON or SSE stream based on request type.
            """
            try:
                body = await request.json()
            except json.JSONDecodeError:
                return JSONResponse(
                    content=_create_jsonrpc_error(None, PARSE_ERROR, "Parse error"),
                    status_code=400,
                )

            # Handle batch requests
            if isinstance(body, list):
                return await self._handle_batch_request(
                    body, accept, mcp_session_id, executor
                )

            # Handle single request
            return await self._handle_single_request(
                body, accept, mcp_session_id, executor
            )

        @router.get("")
        async def mcp_get_endpoint(
            accept: str = Header(default="text/event-stream"),
            mcp_session_id: str | None = Header(default=None, alias="Mcp-Session-Id"),
        ) -> Response:
            """MCP Streamable HTTP GET endpoint for SSE streams.

            Opens an SSE stream for server-initiated messages.
            """
            if "text/event-stream" not in accept:
                return Response(status_code=405, content="Method Not Allowed")

            async def sse_stream():
                # Keep-alive stream for server-initiated messages
                # In this implementation, we just keep the connection open
                yield "event: ping\ndata: {}\n\n"

            return StreamingResponse(
                sse_stream(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                },
            )

        return router

    async def _handle_batch_request(
        self,
        requests: list[dict[str, Any]],
        accept: str,
        session_id: str | None,
        executor: AgentExecutor,
    ) -> Response:
        """Handle batch JSON-RPC requests."""
        responses = []
        has_requests = False

        for req in requests:
            if "method" in req and "id" in req:
                has_requests = True
                result = await self._process_request(req, session_id, executor)
                responses.append(result)
            elif "method" in req:
                # Notification - no response needed
                await self._process_notification(req, session_id)
            elif "result" in req or "error" in req:
                # Response from client - process but no response needed
                pass

        if not has_requests:
            return Response(status_code=202)

        return JSONResponse(content=responses)

    async def _handle_single_request(
        self,
        body: dict[str, Any],
        accept: str,
        session_id: str | None,
        executor: AgentExecutor,
    ) -> Response:
        """Handle single JSON-RPC request."""
        # Validate JSON-RPC format
        if body.get("jsonrpc") != "2.0":
            return JSONResponse(
                content=_create_jsonrpc_error(
                    body.get("id"), INVALID_REQUEST, "Invalid JSON-RPC version"
                ),
                status_code=400,
            )

        # Check if it's a notification (no id)
        if "method" in body and "id" not in body:
            await self._process_notification(body, session_id)
            return Response(status_code=202)

        # Check if it's a response (has result or error but no method)
        if "method" not in body and ("result" in body or "error" in body):
            return Response(status_code=202)

        # It's a request - process and return response
        method = body.get("method")

        # Check if SSE streaming is requested and appropriate
        use_sse = "text/event-stream" in accept and method == "tools/call"

        if use_sse:
            return await self._handle_streaming_request(body, session_id, executor)

        # Return JSON response
        result = await self._process_request(body, session_id, executor)
        headers = {}
        if session_id:
            headers["Mcp-Session-Id"] = session_id
        elif method == "initialize":
            # Generate new session ID on initialize
            new_session_id = str(uuid.uuid4())
            headers["Mcp-Session-Id"] = new_session_id
            self._sessions[new_session_id] = {"initialized": True}

        return JSONResponse(content=result, headers=headers)

    async def _process_request(
        self,
        request: dict[str, Any],
        session_id: str | None,
        executor: AgentExecutor,
    ) -> dict[str, Any]:
        """Process a JSON-RPC request and return response."""
        request_id = request.get("id")
        method = request.get("method")
        params = request.get("params", {})

        try:
            if method == "initialize":
                return self._handle_initialize(request_id, params)
            elif method == "tools/list":
                return self._handle_tools_list(request_id, params)
            elif method == "tools/call":
                return await self._handle_tools_call(request_id, params, executor)
            elif method == "ping":
                return _create_jsonrpc_response(request_id, {})
            else:
                return _create_jsonrpc_error(
                    request_id, METHOD_NOT_FOUND, f"Method not found: {method}"
                )
        except Exception as e:
            logger.exception(f"Error processing request: {method}")
            return _create_jsonrpc_error(request_id, INTERNAL_ERROR, str(e))

    async def _process_notification(
        self, notification: dict[str, Any], session_id: str | None
    ) -> None:
        """Process a JSON-RPC notification."""
        method = notification.get("method")
        logger.debug(f"Received notification: {method}")

        if method == "notifications/initialized":
            logger.info("Client initialized")
        elif method == "notifications/cancelled":
            logger.info(f"Request cancelled: {notification.get('params', {})}")

    def _handle_initialize(
        self, request_id: int | str | None, params: dict[str, Any]
    ) -> dict[str, Any]:
        """Handle initialize request."""
        client_version = params.get("protocolVersion", "")
        client_info = params.get("clientInfo", {})

        logger.info(
            f"MCP initialize: client={client_info.get('name')}, "
            f"version={client_info.get('version')}, protocol={client_version}"
        )

        return _create_jsonrpc_response(
            request_id,
            {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {
                    "tools": {"listChanged": False},
                },
                "serverInfo": {
                    "name": self.server_name,
                    "version": self.server_version,
                },
            },
        )

    def _handle_tools_list(
        self, request_id: int | str | None, params: dict[str, Any]
    ) -> dict[str, Any]:
        """Handle tools/list request."""
        tools = [
            {
                "name": self.tool_name,
                "description": self.tool_description,
                "inputSchema": self._get_tool_input_schema(),
            }
        ]

        return _create_jsonrpc_response(request_id, {"tools": tools})

    async def _handle_tools_call(
        self,
        request_id: int | str | None,
        params: dict[str, Any],
        executor: AgentExecutor,
    ) -> dict[str, Any]:
        """Handle tools/call request."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if tool_name != self.tool_name:
            return _create_jsonrpc_error(
                request_id,
                INVALID_PARAMS,
                f"Unknown tool: {tool_name}. Available: [{self.tool_name}]",
            )

        try:
            tool_args = MCPToolArguments(**arguments)
            config = tool_args.to_runnable_config()
            messages = tool_args.to_langchain_messages()

            # Collect streaming content
            accumulated_content = ""
            async for content_chunk in executor.stream_content(
                messages,
                thread_id=tool_args.thread_id,
                user=tool_args.user,
                tags=tool_args.tags,
                config=config,
                include_tool_result=tool_args.include_tool_result,
            ):
                accumulated_content += content_chunk

            content = []
            if accumulated_content.strip():
                content.append({"type": "text", "text": accumulated_content})

            return _create_jsonrpc_response(
                request_id, {"content": content, "isError": False}
            )

        except Exception as e:
            logger.exception("Error in tools/call")
            return _create_jsonrpc_response(
                request_id,
                {"content": [{"type": "text", "text": str(e)}], "isError": True},
            )

    async def _handle_streaming_request(
        self,
        request: dict[str, Any],
        session_id: str | None,
        executor: AgentExecutor,
    ) -> StreamingResponse:
        """Handle request with SSE streaming response."""
        request_id = request.get("id")
        params = request.get("params", {})
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        async def sse_generator():
            event_id = 0

            if tool_name != self.tool_name:
                error_response = _create_jsonrpc_error(
                    request_id,
                    INVALID_PARAMS,
                    f"Unknown tool: {tool_name}. Available: [{self.tool_name}]",
                )
                yield f"id: {event_id}\nevent: message\ndata: {json.dumps(error_response)}\n\n"
                return

            try:
                tool_args = MCPToolArguments(**arguments)
                config = tool_args.to_runnable_config()
                messages = tool_args.to_langchain_messages()

                accumulated_content = ""

                async for content_chunk in executor.stream_content(
                    messages,
                    thread_id=tool_args.thread_id,
                    user=tool_args.user,
                    tags=tool_args.tags,
                    config=config,
                    include_tool_result=tool_args.include_tool_result,
                ):
                    if content_chunk:
                        accumulated_content += content_chunk
                        # Send progress notification
                        progress = {
                            "jsonrpc": "2.0",
                            "method": "notifications/progress",
                            "params": {
                                "progressToken": request_id,
                                "progress": len(accumulated_content),
                                "data": {"chunk": content_chunk},
                            },
                        }
                        yield f"id: {event_id}\nevent: message\ndata: {json.dumps(progress, ensure_ascii=False)}\n\n"
                        event_id += 1

                # Send final response
                content = []
                if accumulated_content.strip():
                    content.append({"type": "text", "text": accumulated_content})

                final_response = _create_jsonrpc_response(
                    request_id, {"content": content, "isError": False}
                )
                yield f"id: {event_id}\nevent: message\ndata: {json.dumps(final_response, ensure_ascii=False)}\n\n"

            except Exception as e:
                logger.exception("Error in streaming tools/call")
                error_response = _create_jsonrpc_response(
                    request_id,
                    {"content": [{"type": "text", "text": str(e)}], "isError": True},
                )
                yield f"id: {event_id}\nevent: message\ndata: {json.dumps(error_response, ensure_ascii=False)}\n\n"

        headers = {
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Content-Type": "text/event-stream; charset=utf-8",
        }
        if session_id:
            headers["Mcp-Session-Id"] = session_id

        return StreamingResponse(
            sse_generator(),
            media_type="text/event-stream",
            headers=headers,
        )
