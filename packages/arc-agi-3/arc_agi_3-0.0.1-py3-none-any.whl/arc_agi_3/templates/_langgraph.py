"""LangGraph-based agents.

Requires the 'langgraph' extra: pip install arc-agi-3[langgraph]
"""

from __future__ import annotations

import base64
import io
import json
import logging
import random
import time
import uuid
from typing import Any, TypedDict, TypeVar, cast

from .._agent import Agent
from .._structs import FrameData, GameAction, GameState

logger = logging.getLogger(__name__)


def _check_langgraph_available() -> None:
    """Check if LangGraph dependencies are available."""
    try:
        import langgraph  # noqa: F401
        import langchain  # noqa: F401
    except ImportError as e:
        raise ImportError(
            "LangGraph is required for these agents. "
            "Install with: pip install arc-agi-3[langgraph]"
        ) from e


class RandomAgentState(TypedDict):
    """State for the LangGraph Random workflow."""

    latest_frame: FrameData


class RandomAgentOutput(TypedDict):
    """Output from the LangGraph Random workflow."""

    action: GameAction


class LangGraphRandom(Agent):
    """An agent that selects actions at random using a LangGraph workflow."""

    MAX_ACTIONS = 80

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        _check_langgraph_available()
        super().__init__(*args, **kwargs)
        seed = int(time.time() * 1_000_000) + hash(self.game_id) % 1_000_000
        random.seed(seed)
        self.workflow = self._build_workflow()

    @property
    def name(self) -> str:
        return f"{super().name}.{self.MAX_ACTIONS}"

    def _build_workflow(self) -> Any:
        """Build the LangGraph workflow for decision making."""
        from langgraph.graph import END, START, StateGraph

        def choose_action(state: RandomAgentState) -> RandomAgentOutput:
            latest_frame = state["latest_frame"]

            if latest_frame.state in [GameState.NOT_PLAYED, GameState.GAME_OVER]:
                action = GameAction.RESET
                action.reasoning = "Game not started or over - need to reset"
            else:
                available_actions = [a for a in GameAction if a is not GameAction.RESET]
                action = random.choice(available_actions)

                if action.is_simple():
                    action.reasoning = f"RNG told me to pick {action.value}"
                elif action.is_complex():
                    action.set_data(
                        {
                            "x": random.randint(0, 63),
                            "y": random.randint(0, 63),
                        }
                    )
                    action.reasoning = {
                        "desired_action": f"{action.value}",
                        "my_reason": "RNG said so!",
                    }

            return {"action": action}

        workflow = StateGraph(
            RandomAgentState,
            input_schema=RandomAgentState,
            output_schema=RandomAgentOutput,
        )

        workflow.add_node("choose_action", choose_action)
        workflow.add_edge(START, "choose_action")
        workflow.add_edge("choose_action", END)

        return workflow.compile()

    def is_done(self, frames: list[FrameData], latest_frame: FrameData) -> bool:
        """Done when the game is won."""
        return latest_frame.state is GameState.WIN

    def choose_action(
        self,
        frames: list[FrameData],
        latest_frame: FrameData,
    ) -> GameAction:
        """Choose action using LangGraph workflow."""
        initial_state: RandomAgentState = {"latest_frame": latest_frame}
        output: RandomAgentOutput = self.workflow.invoke(initial_state)
        return output["action"]


# LangGraph Functional Agent

MESSAGES = TypeVar("MESSAGES", bound=list[dict[str, Any]])

SYS_PROMPT = """# CONTEXT:
You are an agent playing a dynamic game. Your objective is to
WIN and avoid GAME_OVER while minimizing actions.

One action produces one Frame. One Frame is made of one or more sequential
Grids. Each Grid is a matrix size INT<0,63> by INT<0,63> filled with
INT<0,15> values.

# TURN:
Call exactly one action.
"""


def g2im(g: list[list[list[int]]]) -> bytes:
    """Convert a grid to a PNG image."""
    try:
        import PIL.Image
    except ImportError:
        return b""

    C = [
        (0, 0, 0),
        (0, 0, 170),
        (0, 170, 0),
        (0, 170, 170),
        (170, 0, 0),
        (170, 0, 170),
        (170, 85, 0),
        (170, 170, 170),
        (85, 85, 85),
        (85, 85, 255),
        (85, 255, 85),
        (85, 255, 255),
        (255, 85, 85),
        (255, 85, 255),
        (255, 255, 85),
        (255, 255, 255),
    ]

    if not g or not g[0]:
        return b""

    h, w = len(g[0]), len(g[0][0])
    good = [block for block in g if len(block) == h and len(block[0]) == w]
    n = len(good)
    s = 5 * (n > 1)
    W = w * n + s * (n - 1)

    im = PIL.Image.new("RGB", (W, h), "white")
    px = im.load()
    for i, block in enumerate(good):
        ox = i * (w + s)
        for y, row in enumerate(block):
            for x, val in enumerate(row):
                px[ox + x, y] = C[val & 15]

    buf = io.BytesIO()
    im.save(buf, "PNG")
    return buf.getvalue()


def format_frame(latest_frame: FrameData, as_image: bool) -> list[dict[str, Any]]:
    """Format a frame for the LLM."""
    img = g2im(latest_frame.frame) if latest_frame.frame else None
    if as_image and img:
        frame_block: dict[str, Any] = {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{base64.b64encode(img).decode('ascii')}",
            },
        }
    else:
        lines = []
        for i, block in enumerate(latest_frame.frame):
            lines.append(f"Grid {i}:")
            for row in block:
                lines.append(f"  {row}")
            lines.append("")
        frame_block = {"type": "text", "text": "\n".join(lines)}

    return [
        {
            "type": "text",
            "text": f"""# State:
{latest_frame.state.name}

# Score:
{latest_frame.score}

# Frame:
""",
        },
        frame_block,
        {
            "type": "text",
            "text": """
# TURN:
Reply with a few sentences of plain-text strategy observation about the frame.""",
        },
    ]


class State(TypedDict, total=False):
    """State for the LangGraph functional agent."""

    frames: list[FrameData]
    latest_frame: FrameData


def build_agent(
    model: str = "o4-mini",
    tools: list[dict[str, Any]] | None = None,
    reasoning_effort: str | None = None,
    as_image: bool = True,
) -> Any:
    """Build a LangGraph functional agent."""
    _check_langgraph_available()

    from langgraph.checkpoint.memory import InMemorySaver
    from langgraph.func import entrypoint
    from openai import OpenAI

    if tools is None:
        tools = []

    openai_client = OpenAI()
    model_kwargs = {"reasoning_effort": reasoning_effort} if reasoning_effort else {}

    def prompt(latest_frame: FrameData, messages: list[Any]) -> list[Any]:
        """Build the user prompt for the LLM."""
        content = format_frame(latest_frame, as_image)
        if len(messages) == 0:
            inbound = {"role": "user", "content": content}
        else:
            inbound = {
                "role": "tool",
                "tool_call_id": messages[-1].tool_calls[0].id,
                "content": content,
            }

        return [
            {"role": "system", "content": SYS_PROMPT},
            *messages,
            inbound,
        ]

    def llm(
        model_name: str,
        messages: list[dict[str, Any]],
        tools_list: list[dict[str, Any]],
        tool_choice: str = "required",
        **kwargs: Any,
    ) -> Any:
        return openai_client.chat.completions.create(
            model=model_name,
            messages=messages,
            tools=tools_list,
            tool_choice=tool_choice,
            **kwargs,
        )

    @entrypoint(checkpointer=InMemorySaver())
    def agent(
        state: State, *, previous: list[dict[str, Any]] | None = None
    ) -> Any:
        sys_messages, *convo = prompt(state["latest_frame"], previous or [])
        response = llm(
            model_name=model,
            messages=[sys_messages, *convo],
            tools_list=tools,
            tool_choice="required",
            **model_kwargs,
        )
        ai_msg = response.choices[0].message
        ai_msg.tool_calls = ai_msg.tool_calls[:1]
        return entrypoint.final(value=ai_msg, save=[*convo, ai_msg])

    agent.name = "Agent"
    return agent


class LangGraphFunc(Agent):
    """An agent using LangGraph's functional API."""

    MAX_ACTIONS = 80
    MODEL: str = "o4-mini"
    USE_IMAGE: bool = True
    REASONING_EFFORT: str | None = None

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        _check_langgraph_available()

        # Import LLM for build_tools
        from ._llm import LLM

        super().__init__(*args, **kwargs)
        self._thread_id = uuid.uuid5(uuid.NAMESPACE_DNS, self.game_id)

        # Create a temporary LLM instance to get tools
        self._llm_helper = LLM.__new__(LLM)
        self._llm_helper.MODEL_REQUIRES_TOOLS = True

        self.agent = build_agent(
            self.MODEL,
            tools=self._llm_helper.build_tools(),
            reasoning_effort=self.REASONING_EFFORT,
            as_image=self.USE_IMAGE,
        )

    def is_done(self, frames: list[FrameData], latest_frame: FrameData) -> bool:
        """Done when the game is won."""
        return latest_frame.state is GameState.WIN

    def choose_action(
        self,
        frames: list[FrameData],
        latest_frame: FrameData,
    ) -> GameAction:
        """Choose action using the LangGraph agent."""
        msg = self.agent.invoke(
            {"frames": frames, "latest_frame": latest_frame},
            {"configurable": {"thread_id": self._thread_id}},
        )
        func = msg.tool_calls[0].function
        action = GameAction.from_name(func.name)
        try:
            args = json.loads(func.arguments) if func.arguments else {}
        except Exception as e:
            args = {}
            logger.warning(f"JSON parsing error on LLM function response: {e}")
        action.set_data(args)
        return action


class LangGraphTextOnly(LangGraphFunc):
    """LangGraphFunc but with text-only frames (no images)."""

    USE_IMAGE = False


class LangGraphThinking(Agent):
    """A LangGraph agent using various tools to make decisions."""

    MAX_ACTIONS = 20

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        _check_langgraph_available()
        super().__init__(*args, **kwargs)
        self.workflow = self._build_workflow()

    @property
    def name(self) -> str:
        return f"{super().name}.{self.MAX_ACTIONS}"

    def _build_workflow(self) -> Any:
        """Build the LangGraph workflow."""
        from langgraph.graph import END, START, StateGraph

        # Simplified workflow for the package
        workflow = StateGraph(RandomAgentState, output_schema=RandomAgentOutput)

        def simple_action(state: RandomAgentState) -> RandomAgentOutput:
            """Simple action selection."""
            latest_frame = state["latest_frame"]
            if latest_frame.state in [GameState.NOT_PLAYED, GameState.GAME_OVER]:
                return {"action": GameAction.RESET}
            # Default to random action for this simplified version
            action = random.choice([a for a in GameAction if a is not GameAction.RESET])
            if action.is_complex():
                action.set_data({"x": 32, "y": 32})
            return {"action": action}

        workflow.add_node("act", simple_action)
        workflow.add_edge(START, "act")
        workflow.add_edge("act", END)

        return workflow.compile()

    def is_done(self, frames: list[FrameData], latest_frame: FrameData) -> bool:
        """Done when the game is won."""
        return latest_frame.state is GameState.WIN

    def choose_action(
        self,
        frames: list[FrameData],
        latest_frame: FrameData,
    ) -> GameAction:
        """Choose action using LangGraph workflow."""
        initial_state: RandomAgentState = {"latest_frame": latest_frame}
        output = self.workflow.invoke(initial_state)
        return cast(GameAction, output["action"])


__all__ = [
    "LangGraphRandom",
    "LangGraphFunc",
    "LangGraphTextOnly",
    "LangGraphThinking",
]
