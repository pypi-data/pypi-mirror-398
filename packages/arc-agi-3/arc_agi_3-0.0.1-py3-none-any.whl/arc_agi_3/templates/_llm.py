"""LLM-based agents using OpenAI API.

Requires the 'openai' extra: pip install arc-agi-3[openai]
"""

from __future__ import annotations

import json
import logging
import os
import textwrap
from typing import TYPE_CHECKING, Any

from .._agent import Agent
from .._structs import FrameData, GameAction, GameState

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


def _get_openai_client() -> Any:
    """Get OpenAI client, raising helpful error if not installed."""
    try:
        from openai import OpenAI

        return OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))
    except ImportError as e:
        raise ImportError(
            "OpenAI is required for LLM agents. Install with: pip install arc-agi-3[openai]"
        ) from e


class LLM(Agent):
    """An agent that uses a base LLM model to play games."""

    MAX_ACTIONS: int = 80
    DO_OBSERVATION: bool = True
    REASONING_EFFORT: str | None = None
    MODEL_REQUIRES_TOOLS: bool = False

    MESSAGE_LIMIT: int = 10
    MODEL: str = "gpt-4o-mini"
    messages: list[dict[str, Any]]
    token_counter: int

    _latest_tool_call_id: str = "call_12345"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.messages = []
        self.token_counter = 0

    @property
    def name(self) -> str:
        obs = "with-observe" if self.DO_OBSERVATION else "no-observe"
        sanitized_model_name = self.MODEL.replace("/", "-").replace(":", "-")
        name = f"{super().name}.{sanitized_model_name}.{obs}"
        if self.REASONING_EFFORT:
            name += f".{self.REASONING_EFFORT}"
        return name

    def is_done(self, frames: list[FrameData], latest_frame: FrameData) -> bool:
        """Done when the game is won."""
        return latest_frame.state is GameState.WIN

    def choose_action(
        self,
        frames: list[FrameData],
        latest_frame: FrameData,
    ) -> GameAction:
        """Choose an action using the LLM."""
        # Suppress noisy loggers
        logging.getLogger("openai").setLevel(logging.CRITICAL)
        logging.getLogger("httpx").setLevel(logging.CRITICAL)

        try:
            import openai
            from openai import OpenAI as OpenAIClient
        except ImportError as e:
            raise ImportError(
                "OpenAI is required for LLM agents. Install with: pip install arc-agi-3[openai]"
            ) from e

        client = OpenAIClient(api_key=os.environ.get("OPENAI_API_KEY", ""))

        functions = self.build_functions()
        tools = self.build_tools()

        # First message - trigger initial reset
        if len(self.messages) == 0:
            user_prompt = self.build_user_prompt(latest_frame)
            message0 = {"role": "user", "content": user_prompt}
            self.push_message(message0)
            if self.MODEL_REQUIRES_TOOLS:
                message1 = {
                    "role": "assistant",
                    "tool_calls": [
                        {
                            "id": self._latest_tool_call_id,
                            "type": "function",
                            "function": {
                                "name": GameAction.RESET.name,
                                "arguments": json.dumps({}),
                            },
                        }
                    ],
                }
            else:
                message1: dict[str, Any] = {
                    "role": "assistant",
                    "function_call": {"name": "RESET", "arguments": json.dumps({})},
                }
            self.push_message(message1)
            return GameAction.RESET

        # Add function response to conversation
        function_name = latest_frame.action_input.id.name
        function_response = self.build_func_resp_prompt(latest_frame)
        if self.MODEL_REQUIRES_TOOLS:
            message2: dict[str, Any] = {
                "role": "tool",
                "tool_call_id": self._latest_tool_call_id,
                "content": str(function_response),
            }
        else:
            message2 = {
                "role": "function",
                "name": function_name,
                "content": str(function_response),
            }
        self.push_message(message2)

        # Observation step
        if self.DO_OBSERVATION:
            logger.info("Sending to Assistant for observation...")
            try:
                create_kwargs: dict[str, Any] = {
                    "model": self.MODEL,
                    "messages": self.messages,
                }
                if self.REASONING_EFFORT is not None:
                    create_kwargs["reasoning_effort"] = self.REASONING_EFFORT
                response = client.chat.completions.create(**create_kwargs)
            except openai.BadRequestError as e:
                logger.info(f"Message dump: {self.messages}")
                raise e
            self.track_tokens(
                response.usage.total_tokens if response.usage else 0,
                response.choices[0].message.content or "",
            )
            message3 = {
                "role": "assistant",
                "content": response.choices[0].message.content,
            }
            logger.info(f"Assistant: {response.choices[0].message.content}")
            self.push_message(message3)

        # Ask for next action
        user_prompt = self.build_user_prompt(latest_frame)
        message4 = {"role": "user", "content": user_prompt}
        self.push_message(message4)

        name = GameAction.ACTION5.name  # Default action if LLM doesn't call one
        arguments = None
        message5 = None

        if self.MODEL_REQUIRES_TOOLS:
            logger.info("Sending to Assistant for action...")
            try:
                create_kwargs = {
                    "model": self.MODEL,
                    "messages": self.messages,
                    "tools": tools,
                    "tool_choice": "required",
                }
                if self.REASONING_EFFORT is not None:
                    create_kwargs["reasoning_effort"] = self.REASONING_EFFORT
                response = client.chat.completions.create(**create_kwargs)
            except openai.BadRequestError as e:
                logger.info(f"Message dump: {self.messages}")
                raise e
            self.track_tokens(response.usage.total_tokens if response.usage else 0)
            message5 = response.choices[0].message
            logger.debug(f"... got response {message5}")
            if message5.tool_calls:
                tool_call = message5.tool_calls[0]
                self._latest_tool_call_id = tool_call.id
                logger.debug(
                    f"Assistant: {tool_call.function.name} ({tool_call.id}) "
                    f"{tool_call.function.arguments}"
                )
                name = tool_call.function.name
                arguments = tool_call.function.arguments

                # Handle extra tool calls
                extra_tools = message5.tool_calls[1:]
                for tc in extra_tools:
                    logger.info(
                        "Error: assistant called more than one action, only using the first."
                    )
                    message_extra = {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": "Error: assistant can only call one action (tool) at a time.",
                    }
                    self.push_message(message_extra)
        else:
            logger.info("Sending to Assistant for action...")
            try:
                create_kwargs = {
                    "model": self.MODEL,
                    "messages": self.messages,
                    "functions": functions,
                    "function_call": "auto",
                }
                if self.REASONING_EFFORT is not None:
                    create_kwargs["reasoning_effort"] = self.REASONING_EFFORT
                response = client.chat.completions.create(**create_kwargs)
            except openai.BadRequestError as e:
                logger.info(f"Message dump: {self.messages}")
                raise e
            self.track_tokens(response.usage.total_tokens if response.usage else 0)
            message5 = response.choices[0].message
            function_call = message5.function_call
            if function_call:
                logger.debug(f"Assistant: {function_call.name} {function_call.arguments}")
                name = function_call.name
                arguments = function_call.arguments

        if message5:
            self.push_message(message5)

        action_id = name
        if arguments:
            try:
                data = json.loads(arguments) or {}
            except Exception as e:
                data = {}
                logger.warning(f"JSON parsing error on LLM function response: {e}")
        else:
            data = {}

        action = GameAction.from_name(action_id)
        action.set_data(data)
        return action

    def track_tokens(self, tokens: int, message: str = "") -> None:
        """Track token usage."""
        self.token_counter += tokens
        if hasattr(self, "recorder") and not self.is_playback:
            self.recorder.record(
                {
                    "tokens": tokens,
                    "total_tokens": self.token_counter,
                    "assistant": message,
                }
            )
        logger.info(f"Received {tokens} tokens, new total {self.token_counter}")

    def push_message(self, message: dict[str, Any] | Any) -> list[dict[str, Any]]:
        """Push a message onto stack, store up to MESSAGE_LIMIT with FIFO."""
        self.messages.append(message)
        if len(self.messages) > self.MESSAGE_LIMIT:
            self.messages = self.messages[-self.MESSAGE_LIMIT :]
        if self.MODEL_REQUIRES_TOOLS:
            # Can't clip between tool and tool_call
            while (
                self.messages[0].get("role")
                if isinstance(self.messages[0], dict)
                else getattr(self.messages[0], "role", None)
            ) == "tool":
                self.messages.pop(0)
        return self.messages

    def build_functions(self) -> list[dict[str, Any]]:
        """Build JSON function description of game actions for LLM."""
        empty_params: dict[str, Any] = {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        }
        functions: list[dict[str, Any]] = [
            {
                "name": GameAction.RESET.name,
                "description": "Start or restart a game. Must be called first when NOT_PLAYED or after GAME_OVER.",
                "parameters": empty_params,
            },
            {
                "name": GameAction.ACTION1.name,
                "description": "Send this simple input action (1, W, Up).",
                "parameters": empty_params,
            },
            {
                "name": GameAction.ACTION2.name,
                "description": "Send this simple input action (2, S, Down).",
                "parameters": empty_params,
            },
            {
                "name": GameAction.ACTION3.name,
                "description": "Send this simple input action (3, A, Left).",
                "parameters": empty_params,
            },
            {
                "name": GameAction.ACTION4.name,
                "description": "Send this simple input action (4, D, Right).",
                "parameters": empty_params,
            },
            {
                "name": GameAction.ACTION5.name,
                "description": "Send this simple input action (5, Enter, Spacebar, Delete).",
                "parameters": empty_params,
            },
            {
                "name": GameAction.ACTION6.name,
                "description": "Send this complex input action (6, Click, Point).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "x": {
                            "type": "string",
                            "description": "Coordinate X which must be Int<0,63>",
                        },
                        "y": {
                            "type": "string",
                            "description": "Coordinate Y which must be Int<0,63>",
                        },
                    },
                    "required": ["x", "y"],
                    "additionalProperties": False,
                },
            },
        ]
        return functions

    def build_tools(self) -> list[dict[str, Any]]:
        """Support models that expect tool_call format."""
        functions = self.build_functions()
        tools: list[dict[str, Any]] = []
        for f in functions:
            tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": f["name"],
                        "description": f["description"],
                        "parameters": f.get("parameters", {}),
                        "strict": True,
                    },
                }
            )
        return tools

    def build_func_resp_prompt(self, latest_frame: FrameData) -> str:
        """Build the function response prompt."""
        return textwrap.dedent(f"""
# State:
{latest_frame.state.name}

# Score:
{latest_frame.score}

# Frame:
{self.pretty_print_3d(latest_frame.frame)}

# TURN:
Reply with a few sentences of plain-text strategy observation about the frame to inform your next action.
        """)

    def build_user_prompt(self, latest_frame: FrameData) -> str:
        """Build the user prompt for the LLM."""
        return textwrap.dedent("""
# CONTEXT:
You are an agent playing a dynamic game. Your objective is to
WIN and avoid GAME_OVER while minimizing actions.

One action produces one Frame. One Frame is made of one or more sequential
Grids. Each Grid is a matrix size INT<0,63> by INT<0,63> filled with
INT<0,15> values.

# TURN:
Call exactly one action.
        """)

    def pretty_print_3d(self, array_3d: list[list[list[Any]]]) -> str:
        """Format a 3D array for display."""
        lines = []
        for i, block in enumerate(array_3d):
            lines.append(f"Grid {i}:")
            for row in block:
                lines.append(f"  {row}")
            lines.append("")
        return "\n".join(lines)

    def cleanup(self, *args: Any, **kwargs: Any) -> None:
        """Cleanup with LLM metadata recording."""
        if self._cleanup:
            if hasattr(self, "recorder") and not self.is_playback:
                meta = {
                    "llm_user_prompt": self.build_user_prompt(self.frames[-1]),
                    "llm_tools": (
                        self.build_tools()
                        if self.MODEL_REQUIRES_TOOLS
                        else self.build_functions()
                    ),
                    "llm_tool_resp_prompt": self.build_func_resp_prompt(self.frames[-1]),
                }
                self.recorder.record(meta)
        super().cleanup(*args, **kwargs)


class ReasoningLLM(LLM):
    """An LLM agent that uses o4-mini and captures reasoning metadata."""

    MAX_ACTIONS = 80
    DO_OBSERVATION = True
    MODEL_REQUIRES_TOOLS = True
    MODEL = "o4-mini"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._last_reasoning_tokens = 0
        self._last_response_content = ""
        self._total_reasoning_tokens = 0

    def choose_action(
        self,
        frames: list[FrameData],
        latest_frame: FrameData,
    ) -> GameAction:
        """Override to capture and store reasoning metadata."""
        action = super().choose_action(frames, latest_frame)

        action.reasoning = {
            "model": self.MODEL,
            "action_chosen": action.name,
            "reasoning_tokens": self._last_reasoning_tokens,
            "total_reasoning_tokens": self._total_reasoning_tokens,
            "game_context": {
                "score": latest_frame.score,
                "state": latest_frame.state.name,
                "action_counter": self.action_counter,
                "frame_count": len(frames),
            },
            "response_preview": (
                self._last_response_content[:200] + "..."
                if len(self._last_response_content) > 200
                else self._last_response_content
            ),
        }

        return action

    def track_tokens(self, tokens: int, message: str = "") -> None:
        """Override to capture reasoning token information."""
        super().track_tokens(tokens, message)
        if message and not message.startswith("{"):
            self._last_response_content = message
        self._last_reasoning_tokens = tokens
        self._total_reasoning_tokens += tokens

    def capture_reasoning_from_response(self, response: Any) -> None:
        """Capture reasoning tokens from OpenAI API response."""
        if hasattr(response, "usage") and hasattr(response.usage, "completion_tokens_details"):
            if hasattr(response.usage.completion_tokens_details, "reasoning_tokens"):
                self._last_reasoning_tokens = (
                    response.usage.completion_tokens_details.reasoning_tokens
                )
                self._total_reasoning_tokens += self._last_reasoning_tokens
                logger.debug(
                    f"Captured {self._last_reasoning_tokens} reasoning tokens from {self.MODEL}"
                )


class FastLLM(LLM):
    """Similar to LLM, but skips observations."""

    MAX_ACTIONS = 80
    DO_OBSERVATION = False
    MODEL = "gpt-4o-mini"

    def build_user_prompt(self, latest_frame: FrameData) -> str:
        return textwrap.dedent("""
# CONTEXT:
You are an agent playing a dynamic game. Your objective is to
WIN and avoid GAME_OVER while minimizing actions.

One action produces one Frame. One Frame is made of one or more sequential
Grids. Each Grid is a matrix size INT<0,63> by INT<0,63> filled with
INT<0,15> values.

# TURN:
Call exactly one action.
        """)


class GuidedLLM(LLM):
    """LLM with explicit human-provided rules in the prompt."""

    MAX_ACTIONS = 80
    DO_OBSERVATION = True
    MODEL = "o3"
    MODEL_REQUIRES_TOOLS = True
    MESSAGE_LIMIT = 10
    REASONING_EFFORT = "high"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._last_reasoning_tokens = 0
        self._last_response_content = ""
        self._total_reasoning_tokens = 0

    def choose_action(
        self,
        frames: list[FrameData],
        latest_frame: FrameData,
    ) -> GameAction:
        """Override to capture and store reasoning metadata."""
        action = super().choose_action(frames, latest_frame)

        action.reasoning = {
            "model": self.MODEL,
            "action_chosen": action.name,
            "reasoning_effort": self.REASONING_EFFORT,
            "reasoning_tokens": self._last_reasoning_tokens,
            "total_reasoning_tokens": self._total_reasoning_tokens,
            "game_context": {
                "score": latest_frame.score,
                "state": latest_frame.state.name,
                "action_counter": self.action_counter,
                "frame_count": len(frames),
            },
            "agent_type": "guided_llm",
            "game_rules": "locksmith",
            "response_preview": (
                self._last_response_content[:200] + "..."
                if len(self._last_response_content) > 200
                else self._last_response_content
            ),
        }

        return action

    def track_tokens(self, tokens: int, message: str = "") -> None:
        """Override to capture reasoning token information."""
        super().track_tokens(tokens, message)
        if message and not message.startswith("{"):
            self._last_response_content = message
        self._last_reasoning_tokens = tokens
        self._total_reasoning_tokens += tokens

    def capture_reasoning_from_response(self, response: Any) -> None:
        """Capture reasoning tokens from OpenAI API response."""
        if hasattr(response, "usage") and hasattr(response.usage, "completion_tokens_details"):
            if hasattr(response.usage.completion_tokens_details, "reasoning_tokens"):
                self._last_reasoning_tokens = (
                    response.usage.completion_tokens_details.reasoning_tokens
                )
                self._total_reasoning_tokens += self._last_reasoning_tokens
                logger.debug(
                    f"Captured {self._last_reasoning_tokens} reasoning tokens from o3"
                )

    def build_user_prompt(self, latest_frame: FrameData) -> str:
        return textwrap.dedent("""
# CONTEXT:
You are an agent playing a dynamic game. Your objective is to
WIN and avoid GAME_OVER while minimizing actions.

One action produces one Frame. One Frame is made of one or more sequential
Grids. Each Grid is a matrix size INT<0,63> by INT<0,63> filled with
INT<0,15> values.

You are playing a game called LockSmith. Rules and strategy:
* RESET: start over, ACTION1: move up, ACTION2: move down, ACTION3: move left, ACTION4: move right
* your goal is find and collect a matching key then touch the exit door
* 6 levels total, score shows which level, complete all levels to win
* start each level with limited energy. you GAME_OVER if you run out
* the player is a 4x4 square
* walls are made of INT<10>, you cannot move through a wall
* walkable floor area is INT<8>
* you can refill energy by touching energy pills (a 2x2 of INT<6>)
* current key is shown in bottom-left of entire grid
* the exit door is a 4x4 square with INT<11> border

# TURN:
Call exactly one action.
        """)


__all__ = ["LLM", "ReasoningLLM", "FastLLM", "GuidedLLM"]
