"""Template agents for ARC-AGI-3.

This module provides various agent implementations:

- Random: Random action selection (no extra dependencies)
- LLM, ReasoningLLM, FastLLM, GuidedLLM: OpenAI-based agents (requires 'openai' extra)
- LangGraphRandom, LangGraphFunc, LangGraphTextOnly, LangGraphThinking: LangGraph-based agents (requires 'langgraph' extra)
- SmolCodingAgent, SmolVisionAgent: SmolAgents-based agents (requires 'smolagents' extra)
- ReasoningAgent: Hypothesis-driven reasoning agent (requires 'openai' extra)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

# Always available
from ._random import Random

# Type checking imports for IDE support
if TYPE_CHECKING:
    from ._langgraph import (
        LangGraphFunc,
        LangGraphRandom,
        LangGraphTextOnly,
        LangGraphThinking,
    )
    from ._llm import FastLLM, GuidedLLM, LLM, ReasoningLLM
    from ._reasoning import ReasoningAgent
    from ._smolagents import SmolCodingAgent, SmolVisionAgent


def __getattr__(name: str) -> type:
    """Lazy import for optional dependencies."""
    # OpenAI-based agents
    if name in ("LLM", "ReasoningLLM", "FastLLM", "GuidedLLM"):
        from . import _llm

        return getattr(_llm, name)

    # LangGraph-based agents
    if name in ("LangGraphRandom", "LangGraphFunc", "LangGraphTextOnly", "LangGraphThinking"):
        from . import _langgraph

        return getattr(_langgraph, name)

    # SmolAgents-based agents
    if name in ("SmolCodingAgent", "SmolVisionAgent"):
        from . import _smolagents

        return getattr(_smolagents, name)

    # Reasoning agent
    if name == "ReasoningAgent":
        from . import _reasoning

        return getattr(_reasoning, name)

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    # Core (no extra deps)
    "Random",
    # OpenAI-based (requires 'openai' extra)
    "LLM",
    "ReasoningLLM",
    "FastLLM",
    "GuidedLLM",
    # LangGraph-based (requires 'langgraph' extra)
    "LangGraphRandom",
    "LangGraphFunc",
    "LangGraphTextOnly",
    "LangGraphThinking",
    # SmolAgents-based (requires 'smolagents' extra)
    "SmolCodingAgent",
    "SmolVisionAgent",
    # Reasoning (requires 'openai' extra)
    "ReasoningAgent",
]
