"""ARC-AGI-3 Python SDK for building agents.

This package provides everything you need to build AI agents for ARC-AGI-3 games.

Quick start:
    from arc_agi_3 import Agent, Swarm, AVAILABLE_AGENTS
    from arc_agi_3.templates import Random

Basic usage:
    # Run a random agent on a game
    arc-agi-3 --agent=random --game=ls20

Install with extras for more agent types:
    pip install arc-agi-3[openai]      # For LLM-based agents
    pip install arc-agi-3[langgraph]   # For LangGraph-based agents
    pip install arc-agi-3[smolagents]  # For SmolAgents-based agents
    pip install arc-agi-3[all]         # For all extras
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from dotenv import load_dotenv

from ._agent import Agent, Playback
from ._recorder import Recorder
from ._structs import (
    ActionInput,
    Card,
    ComplexAction,
    FrameData,
    GameAction,
    GameState,
    Scorecard,
    SimpleAction,
)
from ._swarm import Swarm

# Load environment variables
load_dotenv()

if TYPE_CHECKING:
    from .templates import (
        FastLLM,
        GuidedLLM,
        LangGraphFunc,
        LangGraphRandom,
        LangGraphTextOnly,
        LangGraphThinking,
        LLM,
        Random,
        ReasoningAgent,
        ReasoningLLM,
        SmolCodingAgent,
        SmolVisionAgent,
    )


def _build_available_agents() -> dict[str, type[Agent]]:
    """Build the dictionary of available agents."""
    agents: dict[str, type[Agent]] = {}

    # Always import Random as it has no extra deps
    from .templates import Random

    agents["random"] = Random

    # Try to import optional agents
    try:
        from .templates._llm import LLM, FastLLM, GuidedLLM, ReasoningLLM

        agents["llm"] = LLM
        agents["fastllm"] = FastLLM
        agents["guidedllm"] = GuidedLLM
        agents["reasoningllm"] = ReasoningLLM
    except ImportError:
        pass

    try:
        from .templates._reasoning import ReasoningAgent

        agents["reasoningagent"] = ReasoningAgent
    except ImportError:
        pass

    try:
        from .templates._langgraph import (
            LangGraphFunc,
            LangGraphRandom,
            LangGraphTextOnly,
            LangGraphThinking,
        )

        agents["langgraphrandom"] = LangGraphRandom
        agents["langgraphfunc"] = LangGraphFunc
        agents["langgraphtextonly"] = LangGraphTextOnly
        agents["langgraphthinking"] = LangGraphThinking
    except ImportError:
        pass

    try:
        from .templates._smolagents import SmolCodingAgent, SmolVisionAgent

        agents["smolcodingagent"] = SmolCodingAgent
        agents["smolvisionagent"] = SmolVisionAgent
    except ImportError:
        pass

    # Add all recording files as valid agent names (for playback)
    for rec in Recorder.list():
        agents[rec] = Playback

    return agents


# Build available agents dictionary
AVAILABLE_AGENTS: dict[str, type[Agent]] = _build_available_agents()

__version__ = "0.1.0"

__all__ = [
    # Version
    "__version__",
    # Core classes
    "Agent",
    "Playback",
    "Swarm",
    "Recorder",
    # Data structures
    "GameState",
    "GameAction",
    "FrameData",
    "ActionInput",
    "Scorecard",
    "Card",
    "SimpleAction",
    "ComplexAction",
    # Registry
    "AVAILABLE_AGENTS",
]
