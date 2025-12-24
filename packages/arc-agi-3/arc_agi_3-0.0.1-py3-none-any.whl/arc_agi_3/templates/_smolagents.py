"""SmolAgents-based agents.

Requires the 'smolagents' extra: pip install arc-agi-3[smolagents]
"""

from __future__ import annotations

import logging
import textwrap
import time
from typing import Any

from .._agent import Agent
from .._structs import FrameData, GameAction, GameState

logger = logging.getLogger(__name__)


def _check_smolagents_available() -> None:
    """Check if SmolAgents dependencies are available."""
    try:
        import smolagents  # noqa: F401
    except ImportError as e:
        raise ImportError(
            "SmolAgents is required for these agents. "
            "Install with: pip install arc-agi-3[smolagents]"
        ) from e


class SmolCodingAgent(Agent):
    """An agent that uses CodeAgent from the smolagents library to play games."""

    MAX_ACTIONS: int = 100
    DO_OBSERVATION: bool = True
    MESSAGE_LIMIT: int = 10
    MODEL: str = "o4-mini"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        _check_smolagents_available()
        super().__init__(*args, **kwargs)

    def main(self) -> None:
        """The main function to initialize the agent and play the game."""
        from smolagents import CodeAgent, OpenAIServerModel

        self.timer = time.time()
        model = OpenAIServerModel(self.MODEL)

        agent = CodeAgent(
            model=model,
            planning_interval=10,
            tools=self.build_tools(),
        )

        # Reset the game at the start
        reset_frame = self.take_action(GameAction.RESET)
        if reset_frame:
            self.append_frame(reset_frame)

        # Start the agent
        prompt = self.build_initial_prompt(self.frames[-1])
        response = agent.run(prompt, max_steps=self.MAX_ACTIONS)
        print(response)

        self.cleanup()

    def is_done(self, frames: list[FrameData], latest_frame: FrameData) -> bool:
        """Done when the game is won."""
        return latest_frame.state is GameState.WIN

    def build_tools(self) -> list[Any]:
        """Create smolagents tools for all available game actions."""
        from smolagents import tool

        tools = []
        for action in GameAction:
            try:
                t = self._create_tool(action, tool)
                tools.append(t)
            except Exception as e:
                print(f"Failed to create tool for {action.name}: {e}")

        return tools

    def _create_tool(self, game_action: GameAction, tool_decorator: Any) -> Any:
        """Create a smolagents tool for a game action."""
        if game_action.is_simple():

            @tool_decorator
            def simple_action() -> str:
                """Execute a simple game action."""
                return self._execute_action(game_action)

            simple_action.name = game_action.name.lower()
            simple_action.description = f"Execute {game_action.name}"
            simple_action.inputs = {}
            simple_action.output_type = "string"
            return simple_action

        else:

            @tool_decorator
            def complex_action(x: int, y: int) -> str:
                """Execute a complex game action with coordinates."""
                if not (0 <= x <= 63):
                    return "Error: x coordinate must be between 0 and 63"
                if not (0 <= y <= 63):
                    return "Error: y coordinate must be between 0 and 63"

                action = game_action
                action.set_data({"x": x, "y": y})
                return self._execute_action(action, f" at coordinates ({x}, {y})")

            complex_action.name = game_action.name.lower()
            complex_action.description = f"Execute {game_action.name} with coordinates"
            complex_action.inputs = {
                "x": {"type": "integer", "description": "X coordinate (0-63)"},
                "y": {"type": "integer", "description": "Y coordinate (0-63)"},
            }
            complex_action.output_type = "string"
            return complex_action

    def _execute_action(self, action: GameAction, action_description: str = "") -> str:
        """Execute an action and handle common logic."""
        if frame := self.take_action(action):
            self.append_frame(frame)
            logger.info(
                f"{self.game_id} - {action.name}: count {self.action_counter}, "
                f"score {frame.score}, avg fps {self.fps})"
            )

            if self.is_done(self.frames, self.frames[-1]):
                return (
                    f"Action {action.name}{action_description} executed successfully! "
                    "GAME WON! Use the final_answer tool to end the run."
                )
            else:
                return self.build_func_resp_prompt(self.frames[-1])
        else:
            raise Exception(
                f"Action {action.name}{action_description} failed to execute properly."
            )

    def build_initial_prompt(self, latest_frame: FrameData) -> str:
        """Build initial prompt for the LLM."""
        return textwrap.dedent(f"""
# CONTEXT:
You are an agent playing an unknown dynamic game. Your objective is to
WIN and avoid GAME_OVER while minimizing actions.

# Initial Game State:
Current State: {latest_frame.state.name}
Current Score: {latest_frame.score}

# Initial Frame:
{self.pretty_print_3d(latest_frame.frame)}

# INSTRUCTIONS:
First explore the game by taking actions and then determine the best strategy to WIN.
        """)

    def build_func_resp_prompt(self, latest_frame: FrameData) -> str:
        """Build function response prompt."""
        return textwrap.dedent(f"""
# Game State:
{latest_frame.state.name}

# Score:
{latest_frame.score}

# Action Count:
{len(self.frames)}

# Current Frame:
{self.pretty_print_3d(latest_frame.frame)}
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


class SmolVisionAgent(Agent):
    """An agent that uses a multimodal model with smolagents to play by seeing."""

    MAX_ACTIONS: int = 100
    DO_OBSERVATION: bool = True
    MESSAGE_LIMIT: int = 10
    MODEL: str = "o4-mini"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        _check_smolagents_available()
        super().__init__(*args, **kwargs)

    def main(self) -> None:
        """The main agent loop."""
        from smolagents import AgentImage, OpenAIServerModel, ToolCallingAgent

        self.timer = time.time()
        model = OpenAIServerModel(self.MODEL)

        agent = ToolCallingAgent(
            model=model,
            tools=self.build_tools(),
            planning_interval=10,
        )

        # Reset the game at the start
        reset_frame = self.take_action(GameAction.RESET)
        if reset_frame:
            self.append_frame(reset_frame)

        # Start the agent
        prompt = self.build_initial_prompt(self.frames[-1])
        initial_image = self.grid_to_image(self.frames[-1].frame)
        agent.run(prompt, max_steps=self.MAX_ACTIONS, images=[initial_image])
        self.cleanup()

    def is_done(self, frames: list[FrameData], latest_frame: FrameData) -> bool:
        """Done when the game is won."""
        return latest_frame.state is GameState.WIN

    def build_tools(self) -> list[Any]:
        """Create smolagents tools for all available game actions."""
        from smolagents import tool

        tools = []
        for action in GameAction:
            try:
                t = self._create_tool(action, tool)
                tools.append(t)
            except Exception as e:
                print(f"Failed to create tool for {action.name}: {e}")
        return tools

    def _create_tool(self, game_action: GameAction, tool_decorator: Any) -> Any:
        """Create a smolagents tool for a game action."""
        from smolagents import AgentImage

        if game_action.is_simple():

            @tool_decorator
            def simple_action() -> AgentImage:
                """Execute a simple game action."""
                return self._execute_action(game_action)

            simple_action.name = game_action.name.lower()
            simple_action.description = f"Execute {game_action.name}"
            simple_action.inputs = {}
            simple_action.output_type = "image"
            return simple_action

        else:

            @tool_decorator
            def complex_action(x: int, y: int) -> AgentImage:
                """Execute a complex game action with coordinates."""
                if not (0 <= x <= 63):
                    return "Error: x coordinate must be between 0 and 63"
                if not (0 <= y <= 63):
                    return "Error: y coordinate must be between 0 and 63"

                action = game_action
                action.set_data({"x": x, "y": y})
                return self._execute_action(action, f" at ({x}, {y})")

            complex_action.name = game_action.name.lower()
            complex_action.description = f"Execute {game_action.name} with coordinates"
            complex_action.inputs = {
                "x": {"type": "integer", "description": "X coordinate (0-63)"},
                "y": {"type": "integer", "description": "Y coordinate (0-63)"},
            }
            complex_action.output_type = "image"
            return complex_action

    def _execute_action(self, action: GameAction, action_description: str = "") -> Any:
        """Execute an action and return the new frame as an image."""
        from smolagents import AgentImage

        if frame := self.take_action(action):
            self.append_frame(frame)
            logger.info(
                f"{self.game_id} - {action.name}: count {self.action_counter}, "
                f"score {frame.score}, avg fps {self.fps})"
            )

            image = self.grid_to_image(frame.frame)

            if self.is_done(self.frames, self.frames[-1]):
                return (
                    f"Action {action.name}{action_description} executed! "
                    "GAME WON! Use final_answer to end."
                )
            else:
                return AgentImage(image)
        else:
            raise Exception(
                f"Action {action.name}{action_description} failed to execute."
            )

    def grid_to_image(self, grid: list[list[list[int]]]) -> Any:
        """Convert a 3D grid to a PIL image."""
        from PIL import Image

        color_map = [
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

        if not grid or not grid[0]:
            return Image.new("RGB", (64, 64), "black")

        height = len(grid[0])
        width = len(grid[0][0])
        num_layers = len(grid)

        separator_width = 5 if num_layers > 1 else 0
        total_width = (width * num_layers) + (separator_width * (num_layers - 1))

        image = Image.new("RGB", (total_width, height), "white")
        pixels = image.load()

        for i, grid_layer in enumerate(grid):
            if len(grid_layer) != height or len(grid_layer[0]) != width:
                continue

            offset_x = i * (width + separator_width)
            for y in range(height):
                for x in range(width):
                    color_index = grid_layer[y][x] % 16
                    pixels[x + offset_x, y] = color_map[color_index]

        return image

    def build_initial_prompt(self, latest_frame: FrameData) -> str:
        """Build initial prompt for the LLM."""
        return textwrap.dedent(f"""
# CONTEXT:
You are an agent playing an unknown dynamic game by looking at images.
Your objective is to WIN and avoid GAME_OVER while never giving up.

# Initial Game State:
Current State: {latest_frame.state.name}
Current Score: {latest_frame.score}

# INSTRUCTIONS:
Analyze the image and decide on the best action to take.
The game is already reset, so you can start taking other actions.

# TURN:
Call exactly one action.
        """)


__all__ = ["SmolCodingAgent", "SmolVisionAgent"]
