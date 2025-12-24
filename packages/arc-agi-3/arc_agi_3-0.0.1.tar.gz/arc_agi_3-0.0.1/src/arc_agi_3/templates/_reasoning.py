"""Reasoning agent that tracks screen history and builds hypotheses.

Requires the 'openai' extra: pip install arc-agi-3[openai]
"""

from __future__ import annotations

import base64
import io
import json
import logging
import textwrap
from typing import Any, Literal

from pydantic import BaseModel, Field

from .._structs import FrameData, GameAction
from ._llm import ReasoningLLM

logger = logging.getLogger(__name__)


class ReasoningActionResponse(BaseModel):
    """Action response structure for reasoning agent."""

    name: Literal["ACTION1", "ACTION2", "ACTION3", "ACTION4", "RESET"] = Field(
        description="The action to take."
    )
    reason: str = Field(
        description="Detailed reasoning for choosing this action",
        min_length=10,
        max_length=2000,
    )
    short_description: str = Field(
        description="Brief description of the action",
        min_length=5,
        max_length=500,
    )
    hypothesis: str = Field(
        description="Current hypothesis about game mechanics",
        min_length=10,
        max_length=2000,
    )
    aggregated_findings: str = Field(
        description="Summary of discoveries and learnings so far",
        min_length=10,
        max_length=2000,
    )


class ReasoningAgent(ReasoningLLM):
    """A reasoning agent that tracks screen history and builds hypotheses."""

    MAX_ACTIONS = 400
    DO_OBSERVATION = True
    MODEL = "o4-mini"
    MESSAGE_LIMIT = 5
    REASONING_EFFORT = "high"
    ZONE_SIZE = 16

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.history: list[ReasoningActionResponse] = []
        self.screen_history: list[bytes] = []
        self.max_screen_history = 10

        try:
            from openai import OpenAI

            self.client = OpenAI()
        except ImportError as e:
            raise ImportError(
                "OpenAI is required for ReasoningAgent. "
                "Install with: pip install arc-agi-3[openai]"
            ) from e

    def clear_history(self) -> None:
        """Clear all history when transitioning between levels."""
        self.history = []
        self.screen_history = []

    def generate_grid_image_with_zone(
        self, grid: list[list[int]], cell_size: int = 40
    ) -> bytes:
        """Generate PIL image of the grid with colored cells and zone coordinates."""
        try:
            from PIL import Image, ImageDraw, ImageFont
        except ImportError:
            return b""

        if not grid or not grid[0]:
            img = Image.new("RGB", (200, 200), color="black")
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            return buffer.getvalue()

        height = len(grid)
        width = len(grid[0])

        img = Image.new("RGB", (width * cell_size, height * cell_size), color="white")
        draw = ImageDraw.Draw(img)

        key_colors = {
            0: "#FFFFFF",
            1: "#CCCCCC",
            2: "#999999",
            3: "#666666",
            4: "#333333",
            5: "#000000",
            6: "#E53AA3",
            7: "#FF7BCC",
            8: "#F93C31",
            9: "#1E93FF",
            10: "#88D8F1",
            11: "#FFDC00",
            12: "#FF851B",
            13: "#921231",
            14: "#4FCC30",
            15: "#A356D6",
        }

        for y in range(height):
            for x in range(width):
                color = key_colors.get(grid[y][x], "#888888")
                draw.rectangle(
                    [
                        x * cell_size,
                        y * cell_size,
                        (x + 1) * cell_size,
                        (y + 1) * cell_size,
                    ],
                    fill=color,
                    outline="#000000",
                    width=1,
                )

        # Draw zone coordinates and borders
        for y in range(0, height, self.ZONE_SIZE):
            for x in range(0, width, self.ZONE_SIZE):
                try:
                    font = ImageFont.load_default()
                    zone_text = f"({x},{y})"
                    draw.text(
                        (x * cell_size + 2, y * cell_size + 2),
                        zone_text,
                        fill="#FFFFFF",
                        font=font,
                    )
                except Exception:
                    pass

                zone_width = min(self.ZONE_SIZE, width - x) * cell_size
                zone_height = min(self.ZONE_SIZE, height - y) * cell_size
                draw.rectangle(
                    [
                        x * cell_size,
                        y * cell_size,
                        x * cell_size + zone_width,
                        y * cell_size + zone_height,
                    ],
                    fill=None,
                    outline="#FFD700",
                    width=2,
                )

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()

    def build_functions(self) -> list[dict[str, Any]]:
        """Build JSON function description for reasoning agent."""
        schema = ReasoningActionResponse.model_json_schema()
        schema["properties"].pop("name", None)
        if "required" in schema:
            schema["required"].remove("name")

        functions: list[dict[str, Any]] = [
            {
                "name": action.name,
                "description": f"Take action {action.name}",
                "parameters": schema,
            }
            for action in [
                GameAction.ACTION1,
                GameAction.ACTION2,
                GameAction.ACTION3,
                GameAction.ACTION4,
                GameAction.RESET,
            ]
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
                    },
                }
            )
        return tools

    def build_user_prompt(self, latest_frame: FrameData) -> str:
        """Build the user prompt for hypothesis-driven exploration."""
        return textwrap.dedent("""
You are playing a video game.

Your ultimate goal is to understand the rules of the game.

You can do 5 actions:
- RESET (used to start a new game or level)
- ACTION1 (MOVE_UP)
- ACTION2 (MOVE_DOWN)
- ACTION3 (MOVE_LEFT)
- ACTION4 (MOVE_RIGHT)

You can do one action at once.

How to proceed:
1. Define an hypothesis and an action to validate it.
2. Once confirmed, store the findings.
3. Make sure to understand clearly the game rules.

Hint:
- The game is a 2D platformer.
- The player can move up, down, left and right.
- There are walls in black.
        """)

    def call_llm_with_structured_output(
        self, messages: list[dict[str, Any]]
    ) -> ReasoningActionResponse:
        """Call LLM with structured output parsing."""
        try:
            tools = self.build_tools()

            response = self.client.chat.completions.create(
                model=self.MODEL,
                messages=messages,
                tools=tools,
                tool_choice="required",
            )

            self.track_tokens(
                response.usage.total_tokens if response.usage else 0,
                response.choices[0].message.content or "",
            )
            self.capture_reasoning_from_response(response)

            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls
            if tool_calls:
                tool_call = tool_calls[0]
                function_args = json.loads(tool_call.function.arguments)
                function_args["name"] = tool_call.function.name
                return ReasoningActionResponse(**function_args)

            raise ValueError("LLM did not return a tool call.")

        except Exception as e:
            logger.error(f"LLM structured call failed: {e}")
            raise

    def define_next_action(self, latest_frame: FrameData) -> ReasoningActionResponse:
        """Define next action for the reasoning agent."""
        current_grid = latest_frame.frame[-1] if latest_frame.frame else []
        map_image = self.generate_grid_image_with_zone(current_grid)

        system_prompt = self.build_user_prompt(latest_frame)
        latest_action = self.history[-1] if self.history else None

        user_message_content: list[dict[str, Any]] = []

        previous_screen = self.screen_history[-1] if self.screen_history else None
        if previous_screen:
            user_message_content.extend(
                [
                    {"type": "text", "text": "Previous screen:"},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64.b64encode(previous_screen).decode()}",
                            "detail": "high",
                        },
                    },
                ]
            )

        raw_grid_text = self.pretty_print_3d(latest_frame.frame)
        user_message_text = (
            f"Your previous action was: "
            f"{json.dumps(latest_action.model_dump() if latest_action else None, indent=2)}\n\n"
            f"Raw Grid:\n{raw_grid_text}\n\nWhat should you do next?"
        )

        current_image_b64 = base64.b64encode(map_image).decode()
        user_message_content.extend(
            [
                {"type": "text", "text": user_message_text},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{current_image_b64}",
                        "detail": "high",
                    },
                },
            ]
        )

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message_content},
        ]

        result = self.call_llm_with_structured_output(messages)

        self.screen_history.append(map_image)
        if len(self.screen_history) > self.max_screen_history:
            self.screen_history.pop(0)

        return result

    def choose_action(
        self,
        frames: list[FrameData],
        latest_frame: FrameData,
    ) -> GameAction:
        """Choose action using parent class tool calling with reasoning enhancement."""
        if latest_frame.full_reset:
            self.clear_history()
            return GameAction.RESET

        if not self.history:
            action = GameAction.RESET
            initial_response = ReasoningActionResponse(
                name="RESET",
                reason="Initial action to start the game and observe the environment.",
                short_description="Start game",
                hypothesis="The game requires a RESET to begin.",
                aggregated_findings="No findings yet.",
            )
            self.history.append(initial_response)
            return action

        action_response = self.define_next_action(latest_frame)
        self.history.append(action_response)

        action = GameAction.from_name(action_response.name)

        reasoning_meta = {
            "model": self.MODEL,
            "reasoning_effort": self.REASONING_EFFORT,
            "reasoning_tokens": self._last_reasoning_tokens,
            "total_reasoning_tokens": self._total_reasoning_tokens,
            "agent_type": "reasoning_agent",
            "hypothesis": action_response.hypothesis,
            "aggregated_findings": action_response.aggregated_findings,
            "response_preview": (
                action_response.reason[:200] + "..."
                if len(action_response.reason) > 200
                else action_response.reason
            ),
            "action_chosen": action.name,
            "game_context": {
                "score": latest_frame.score,
                "state": latest_frame.state.name,
                "action_counter": self.action_counter,
                "frame_count": len(frames),
            },
        }
        action.reasoning = reasoning_meta

        return action


__all__ = ["ReasoningAgent", "ReasoningActionResponse"]
