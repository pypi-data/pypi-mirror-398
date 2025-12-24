"""AgentOps integration module for tracing agent execution."""

from __future__ import annotations

import functools
import logging
from typing import TYPE_CHECKING, Any, Callable, TypeVar

if TYPE_CHECKING:
    from ._agent import Agent

logger = logging.getLogger(__name__)

# Module-level state
_is_initialized = False
_agentops_client: Any = None

F = TypeVar("F", bound=Callable[..., Any])


class _NoOpAgentOps:
    """No-op implementation when AgentOps is not available."""

    def init(self, *args: Any, **kwargs: Any) -> None:
        """No-op initialization."""

    class NoOpTrace:
        """No-op trace context manager."""

        def __enter__(self) -> _NoOpAgentOps.NoOpTrace:
            return self

        def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
            pass

        def set_status(self, *args: Any, **kwargs: Any) -> None:
            """No-op status setting."""

    def start_trace(self, *args: Any, **kwargs: Any) -> NoOpTrace:
        """Create a no-op trace context."""
        return self.NoOpTrace()


def _get_agentops() -> Any:
    """Get the AgentOps client, initializing if needed."""
    global _agentops_client
    if _agentops_client is None:
        try:
            import agentops

            _agentops_client = agentops
        except ImportError:
            _agentops_client = _NoOpAgentOps()
    return _agentops_client


def initialize(
    api_key: str | None = None,
    log_level: int | None = logging.INFO,
) -> None:
    """Initialize the AgentOps SDK with an optional API key.

    Args:
        api_key: Optional AgentOps API key
        log_level: Optional log level for AgentOps
    """
    global _is_initialized

    client = _get_agentops()

    # Check if library is available
    if isinstance(client, _NoOpAgentOps):
        return

    # Validate API key
    if not api_key or not api_key.strip() or api_key == "your_agentops_api_key_here":
        return

    try:
        client.init(
            api_key=api_key,
            auto_start_session=False,
            log_level=log_level,
        )
        _is_initialized = True
    except Exception:
        # AgentOps may handle status automatically
        pass


def is_available() -> bool:
    """Check if AgentOps is available and initialized."""
    client = _get_agentops()
    return not isinstance(client, _NoOpAgentOps) and _is_initialized


def _set_trace_status(trace: Any, agent_instance: Agent) -> None:
    """Set trace status based on agent execution outcome."""
    if not hasattr(trace, "set_status"):
        return

    try:
        if agent_instance.action_counter >= agent_instance.MAX_ACTIONS:
            trace.set_status("Indeterminate")
        else:
            trace.set_status("Success")
    except AttributeError:
        pass


def _handle_trace_error(trace: Any, agent_instance: Agent, error: Exception) -> None:
    """Handle trace error by setting error status."""
    if hasattr(trace, "set_status"):
        try:
            trace.set_status(f"Error: {error}")
        except AttributeError:
            pass


def trace_agent_session(func: F) -> F:
    """Decorator that wraps an agent's main execution loop to trace it."""

    @functools.wraps(func)
    def wrapper(agent_instance: Agent, *args: Any, **kwargs: Any) -> Any:
        if not is_available():
            return func(agent_instance, *args, **kwargs)

        tags = agent_instance.tags or []
        client = _get_agentops()

        if client is None:
            return func(agent_instance, *args, **kwargs)

        trace = None
        try:
            with client.start_trace(trace_name=agent_instance.name, tags=tags) as trace:
                agent_instance.trace = trace
                result = func(agent_instance, *args, **kwargs)
                _set_trace_status(trace, agent_instance)
                return result
        except Exception as e:
            if trace is not None:
                _handle_trace_error(trace, agent_instance, e)
            logger.error(
                f"Agent {agent_instance.name} failed with exception: {e}",
                exc_info=True,
            )
            raise

    return wrapper  # type: ignore[return-value]


__all__ = ["initialize", "is_available", "trace_agent_session"]
