"""App class for wrapping LangGraph StateGraph."""

from __future__ import annotations

import logging
from typing import Any

from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph

from orcakit_sdk.runner.agent_executor import AgentExecutor, LangGraphAgentExecutor
from orcakit_sdk.runner.runner import BaseRunner


class Agent:
    """Wrapper for LangGraph StateGraph providing deployment capabilities.

    This class encapsulates a LangGraph StateGraph and provides convenient
    methods for running and deploying the graph with different runners.

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

    logger: logging.Logger = logging.getLogger(__name__)
    _agent_executor: AgentExecutor

    def __init__(
        self,
        agent_executor: AgentExecutor | None = None,
        graph: StateGraph | CompiledStateGraph | None = None,
        name: str = "agent",
    ) -> None:
        """Initialize the Agent with an AgentExecutor, StateGraph, or CompiledStateGraph.

        Args:
            agent_executor: AgentExecutor instance, LangGraph StateGraph instance, or compiled graph to wrap.
            name: Name for the compiled graph (used only when agent_executor is a StateGraph).
        """
        if agent_executor is not None:
            self._agent_executor = agent_executor
        elif graph is not None:
            self._agent_executor = LangGraphAgentExecutor(graph=graph, name=name)
        else:
            raise ValueError("Either agent_executor or graph must be provided")

    @property
    def agent_executor(self) -> AgentExecutor:
        """Get the underlying AgentExecutor.

        Returns:
            The AgentExecutor instance.
        """
        return self._agent_executor

    def run(
        self,
        host: str = "0.0.0.0",
        port: int = 8888,
        **kwargs: Any,
    ) -> None:
        """Run the app with a simple built-in runner.

        This is a convenience method that creates and runs a SimpleRunner
        with the specified configuration.

        Args:
            host: Host address to bind the server.
            port: Port number to bind the server.
            **kwargs: Additional arguments to pass to the SimpleRunner.
        """
        from orcakit_sdk.runner.runner import SimpleRunner

        runner = SimpleRunner(host=host, port=port, **kwargs)
        # Initialize the app in the runner and start the server synchronously
        runner.run(self._agent_executor)

    async def deploy(self, runner: BaseRunner, **kwargs: Any) -> None:
        """Deploy the app with a custom runner.

        Args:
            runner: Runner instance responsible for deploying the app.
            **kwargs: Additional arguments to pass to the runner.

        Example:
            >>> runner = SimpleRunner(host="0.0.0.0", port=8091)
            >>> await app.deploy(runner)
        """
        # Check if runner has async run method
        import inspect

        if inspect.iscoroutinefunction(runner.run):
            await runner.run(self._agent_executor, **kwargs)
        else:
            # For sync runners, call directly
            runner.run(self._agent_executor, **kwargs)
