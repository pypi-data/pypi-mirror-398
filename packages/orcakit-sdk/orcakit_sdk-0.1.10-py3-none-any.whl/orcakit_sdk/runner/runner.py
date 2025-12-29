"""Runner classes for deploying and serving LangGraph apps."""

from __future__ import annotations

import asyncio
import importlib
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from scalar_fastapi import get_scalar_api_reference

from orcakit_sdk.context import EnvAwareConfig
from orcakit_sdk.runner.agent_executor import AgentExecutor, LangGraphAgentExecutor
from orcakit_sdk.runner.channels.a2a_channel import A2AChannel
from orcakit_sdk.runner.channels.langgraph_channel import LangGraphChannel
from orcakit_sdk.runner.channels.mcp_server_channel import MCPServerChannel
from orcakit_sdk.runner.channels.openai_channel import OpenAIChannel
from orcakit_sdk.runner.channels.wework_channel import WeWorkChannel


class BaseRunner(ABC):
    """Abstract base class for app runners.

    A Runner is responsible for deploying and serving an App,
    providing API access to the underlying StateGraph.
    """

    @abstractmethod
    def run(self, agent_executor: AgentExecutor, **kwargs: str) -> None:
        """Run the given app.

        Args:
            agent_executor: The agent instance to run.
            **kwargs: Additional arguments for running the app.
        """
        ...

    @abstractmethod
    async def run_async(self, agent_executor: AgentExecutor, **kwargs: str) -> None:
        """Run the agent asynchronously.

        Args:
            agent_executor: The agent_executor instance to run.
            **kwargs: Additional arguments for running the app.
        """

    @abstractmethod
    async def stop(self) -> None:
        """Stop the runner."""
        ...

    @abstractmethod
    async def health_check(self) -> dict[str, str]:
        """Check the health status of the runner.

        Returns:
            Dictionary containing health status information.
        """
        ...


# Environment variable keys for dev mode configuration
_DEV_URL_PREFIX_ENV = "ORCAKIT_DEV_URL_PREFIX"
_DEV_GRAPH_MODULE_ENV = "ORCAKIT_DEV_GRAPH_MODULE"
_DEV_GRAPH_ATTR_ENV = "ORCAKIT_DEV_GRAPH_ATTR"


@dataclass(kw_only=True)
class SimpleRunnerConfig(EnvAwareConfig):
    """Configuration for SimpleRunner.

    Environment variables:
        - HOST: Server host address (default: 0.0.0.0)
        - PORT: Server port (default: 8090)
        - RELOAD: Enable auto-reload (default: false)
        - LOG_LEVEL: Logging level (default: info)
        - DEV: Enable dev mode with hot reload (default: false)
    """

    host: str = "0.0.0.0"
    port: int = 8888
    reload: bool = False
    log_level: str = "info"
    dev: bool = False
    extra: dict[str, str] | None = None

    def __post_init__(self) -> None:
        """Initialize default values for extra fields."""
        if self.extra is None:
            self.extra = {}


class SimpleRunner(BaseRunner):
    """Simple FastAPI-based runner for LangGraph apps.

    This runner creates a FastAPI web server that exposes the StateGraph
    through REST API endpoints, supporting ainvoke, astream, and astream_events.

    Example:
        >>> from orcakit_sdk.runner import SimpleRunner
        >>> from orcakit_sdk.runner.agent_executor import LangGraphAgentExecutor
        >>>
        >>> executor = LangGraphAgentExecutor(graph=graph)
        >>> runner = SimpleRunner(host="0.0.0.0", port=8091)
        >>> runner.run(executor)
    """

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8888,
        reload: bool = False,
        log_level: str = "info",
        dev: bool = False,
        fastapi_app: FastAPI | None = None,
        **kwargs: str,
    ) -> None:
        """Initialize the SimpleRunner.

        Args:
            host: Host address to bind the server.
            port: Port number to bind the server.
            reload: Whether to enable auto-reload during development.
            log_level: Logging level (debug, info, warning, error, critical).
            dev: Enable dev mode with hot reload support.
            fastapi_app: Optional pre-configured FastAPI app.
            **kwargs: Additional configuration parameters.
        """
        self.config: SimpleRunnerConfig = SimpleRunnerConfig(
            host=host,
            port=port,
            reload=reload,
            log_level=log_level,
            dev=dev,
            extra=kwargs if kwargs else None,
        )
        self.server: uvicorn.Server | None = None
        self.fastapi_app: FastAPI | None = fastapi_app
        self._app_initialized: bool = False

    def run(
        self,
        agent_executor: AgentExecutor,
        url_prefix: str = "",
        start: bool = True,
        **kwargs: str,
    ) -> None:
        """Run the app.

        This method can be called multiple times with different url_prefix values
        to register multiple agents. Set start=False for all calls except the last
        one to avoid starting the server prematurely.

        Args:
            agent_executor: The AgentExecutor instance to run.
            url_prefix: URL prefix for all routes. Must be unique for each agent.
            start: Whether to start the server after registering channels.
                Set to False when registering multiple agents, True for the last one.
            **kwargs: Additional arguments for running the app.
                - graph_module: Module path for dev mode (e.g., 'my_agent.graph').
                - graph_attr: Graph attribute name in module (default: 'graph').

        Example:
            >>> runner = SimpleRunner(port=8888)
            >>> runner.run(agent1, url_prefix="/agent1", start=False)
            >>> runner.run(agent2, url_prefix="/agent2", start=True)  # Starts server
        """
        if self.config.dev:
            graph_module = str(kwargs.get("graph_module", ""))
            graph_attr = str(kwargs.get("graph_attr", "graph"))
            self._run_dev_mode(url_prefix, graph_module, graph_attr)
        else:
            self._initialize_app(agent_executor, url_prefix=url_prefix)
            if start:
                self._start_server_sync()

    async def run_async(
        self,
        agent_executor: AgentExecutor,
        url_prefix: str = "",
        start: bool = True,
        **kwargs: str,
    ) -> None:
        """Run the app asynchronously.

        This method can be called multiple times with different url_prefix values
        to register multiple agents. Set start=False for all calls except the last
        one to avoid starting the server prematurely.

        Args:
            agent_executor: The AgentExecutor instance to run.
            url_prefix: URL prefix for all routes. Must be unique for each agent.
            start: Whether to start the server after registering channels.
                Set to False when registering multiple agents, True for the last one.
            **kwargs: Additional arguments (unused, for compatibility).
        """
        self._initialize_app(agent_executor, url_prefix=url_prefix)
        if start:
            await self.stop()
            await self._start_server_async()

    async def stop(self) -> None:
        """Stop the running server."""
        if self.server:
            self.server.should_exit = True
            await asyncio.sleep(0.1)

    async def health_check(self) -> dict[str, str]:
        """Check the health status.

        Returns:
            Dictionary with health status.
        """
        return {"status": "healthy", "runner": "SimpleRunner"}

    @staticmethod
    def _create_fastapi_app() -> FastAPI:
        """Create and configure the base FastAPI application.

        Returns:
            Configured FastAPI application instance with Scalar docs and CORS.
        """
        fastapi_app = FastAPI(
            title="OrcaKit Simple Runner",
            description="Simple runner for OrcaKit execution",
            version="0.1.0",
            openapi_url="/openapi.json",
            docs_url=None,
        )

        return fastapi_app

    @staticmethod
    def _setup_channels(
        app: FastAPI,
        agent_executor: AgentExecutor,
        url_prefix: str = "",
    ) -> None:
        """Set up API channels on the given FastAPI app.

        Args:
            app: FastAPI application instance.
            agent_executor: The AgentExecutor instance.
            url_prefix: URL prefix for all routes.
        """
        a2a_base_url = os.environ.get("A2A_BASE_URL", "")
        agent_name = os.environ.get("AGENT_NAME", "")
        agent_description = os.environ.get("AGENT_DESCRIPTION", "")

        LangGraphChannel().create_router(
            fastapi_app=app,
            agent_executor=agent_executor,
            url_prefix=f"{url_prefix}/langgraph",
        )

        OpenAIChannel().create_router(
            fastapi_app=app,
            agent_executor=agent_executor,
            url_prefix=f"{url_prefix}/openai",
        )

        WeWorkChannel().create_router(
            fastapi_app=app,
            agent_executor=agent_executor,
            url_prefix=f"{url_prefix}/wework",
        )

        MCPServerChannel().create_router(
            fastapi_app=app,
            agent_executor=agent_executor,
            url_prefix=f"{url_prefix}/mcp-server",
            tool_description=agent_description,
            tool_name=agent_name,
        )

        A2AChannel().create_router(
            fastapi_app=app,
            agent_executor=agent_executor,
            url_prefix=f"{url_prefix}/a2a-protocol",
            base_url=a2a_base_url,
        )

    def _initialize_app(
        self, agent_executor: AgentExecutor, url_prefix: str = ""
    ) -> None:
        """Initialize FastAPI app and register API channels.

        Args:
            agent_executor: The AgentExecutor instance.
            url_prefix: URL prefix for all routes.
        """
        if self.fastapi_app is None:
            self.fastapi_app = self._create_fastapi_app()

        # Only add docs and middleware once
        if not self._app_initialized:
            fastapi_app = self.fastapi_app

            # Disable default Swagger UI by setting docs_url to None
            fastapi_app.docs_url = None

            # Remove existing /docs and /docs/oauth2-redirect routes
            fastapi_app.router.routes = [
                route
                for route in fastapi_app.router.routes
                if getattr(route, "path", None)
                not in ("/docs", "/docs/oauth2-redirect")
            ]

            # Ensure openapi_url is set
            openapi_url = fastapi_app.openapi_url or "/openapi.json"
            app_title = fastapi_app.title or "OrcaKit API Reference"

            @fastapi_app.get("/docs", include_in_schema=False)
            async def scalar_docs():
                return get_scalar_api_reference(
                    openapi_url=openapi_url,
                    title=app_title,
                )

            fastapi_app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
            self._app_initialized = True

        self._setup_channels(self.fastapi_app, agent_executor, url_prefix)

    def _run_dev_mode(
        self,
        url_prefix: str = "",
        graph_module: str = "",
        graph_attr: str = "graph",
    ) -> None:
        """Run in dev mode with hot reload support.

        Args:
            url_prefix: URL prefix for all routes.
            graph_module: Module path containing the graph (e.g., 'my_agent.graph').
            graph_attr: Attribute name of the graph in the module.

        Raises:
            RuntimeError: If graph_module is not provided.
        """
        if not graph_module:
            raise RuntimeError(
                "graph_module is required for dev mode. "
                "Pass it via kwargs: runner.run(executor, graph_module='my_agent.graph')"
            )

        os.environ[_DEV_URL_PREFIX_ENV] = url_prefix
        os.environ[_DEV_GRAPH_MODULE_ENV] = graph_module
        os.environ[_DEV_GRAPH_ATTR_ENV] = graph_attr

        uvicorn.run(
            app="orcakit_sdk.runner.runner:create_dev_app",
            factory=True,
            host=self.config.host,
            port=self.config.port,
            log_level=self.config.log_level,
            reload=True,
            reload_dirs=["src"],
        )

    def _start_server_sync(self) -> None:
        """Start the server synchronously."""
        if self.fastapi_app is None:
            raise RuntimeError("FastAPI app not initialized")
        uvicorn.run(
            app=self.fastapi_app,
            host=self.config.host,
            port=self.config.port,
            log_level=self.config.log_level,
            reload=self.config.reload,
        )

    async def _start_server_async(self) -> None:
        """Start the server asynchronously."""
        if self.fastapi_app is None:
            raise RuntimeError("FastAPI app not initialized")
        config = uvicorn.Config(
            app=self.fastapi_app,
            host=self.config.host,
            port=self.config.port,
            log_level=self.config.log_level,
            reload=self.config.reload,
        )

        server = uvicorn.Server(config)
        self.server = server
        await server.serve()


def create_dev_app() -> FastAPI:
    """Create FastAPI app in dev mode.

    This function is called by uvicorn when reload=True.
    It creates a fresh app instance with reloaded modules.

    Note:
        This must be a module-level function (not a method) because
        uvicorn needs to import it by string path for hot reload.

    Environment variables:
        - ORCAKIT_DEV_GRAPH_MODULE: Module path containing the graph (required)
        - ORCAKIT_DEV_GRAPH_ATTR: Attribute name of the graph in the module (default: "graph")
        - ORCAKIT_DEV_URL_PREFIX: URL prefix for all routes (default: "")

    Returns:
        FastAPI: Configured FastAPI application instance.

    Raises:
        RuntimeError: If ORCAKIT_DEV_GRAPH_MODULE is not set.
    """
    graph_module = os.environ.get(_DEV_GRAPH_MODULE_ENV)
    if not graph_module:
        raise RuntimeError(
            f"Environment variable {_DEV_GRAPH_MODULE_ENV} is required for dev mode. "
            "Set it to the module path containing your graph (e.g., 'my_agent.graph')."
        )

    graph_attr = os.environ.get(_DEV_GRAPH_ATTR_ENV, "graph")
    url_prefix = os.environ.get(_DEV_URL_PREFIX_ENV, "")

    module = importlib.import_module(graph_module)
    importlib.reload(module)
    fresh_graph = getattr(module, graph_attr)

    fastapi_app = SimpleRunner._create_fastapi_app()

    # Add Scalar docs route
    openapi_url = fastapi_app.openapi_url or "/openapi.json"

    @fastapi_app.get("/docs", include_in_schema=False)
    async def scalar_docs():
        return get_scalar_api_reference(
            openapi_url=openapi_url,
            title=fastapi_app.title or "OrcaKit API Reference",
        )

    fastapi_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    fresh_executor = LangGraphAgentExecutor(graph=fresh_graph)
    SimpleRunner._setup_channels(fastapi_app, fresh_executor, url_prefix)

    return fastapi_app
