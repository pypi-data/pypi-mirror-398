# arc-agi-3

Python SDK for building ARC-AGI-3 agents.

ARC-AGI-3 is an Interactive Reasoning Benchmark designed to measure an AI Agent's ability to generalize in novel, unseen environments. By building agents that can play ARC-AGI-3, you're directly contributing to the frontier of AI research.

## Installation

```bash
# Core installation (Random agent only)
pip install arc-agi-3

# With OpenAI support (LLM-based agents)
pip install arc-agi-3[openai]

# With LangGraph support
pip install arc-agi-3[langgraph]

# With SmolAgents support
pip install arc-agi-3[smolagents]

# With AgentOps observability
pip install arc-agi-3[agentops]

# Everything
pip install arc-agi-3[all]
```

## Quick Start

### 1. Get an API Key

1. Go to [three.arcprize.org](https://three.arcprize.org/)
2. Create an account and get your API key
3. Set it as an environment variable:

```bash
export ARC_API_KEY="your-api-key-here"
```

Or create a `.env` file:

```
ARC_API_KEY=your-api-key-here
```

### 2. Run an Agent

Using the CLI:

```bash
# Run a random agent on the ls20 game
arc-agi-3 --agent=random --game=ls20

# Run with tags for tracking
arc-agi-3 --agent=random --game=ls20 --tags=experiment,v1.0

# List available agents
arc-agi-3 --list-agents
```

Or programmatically:

```python
from arc_agi_3 import Swarm, AVAILABLE_AGENTS

# Run a swarm of agents
swarm = Swarm(
    agent="random",
    ROOT_URL="https://three.arcprize.org",
    games=["ls20"],
    tags=["my-experiment"],
)
scorecard = swarm.main()
print(f"Final score: {scorecard.score}")
```

## Available Agents

| Agent | Extra Required | Description |
|-------|----------------|-------------|
| `random` | None | Random action selection |
| `llm` | `openai` | Basic LLM agent using GPT-4o-mini |
| `fastllm` | `openai` | LLM agent without observation step |
| `reasoningllm` | `openai` | LLM with o4-mini reasoning |
| `guidedllm` | `openai` | LLM with game-specific guidance |
| `reasoningagent` | `openai` | Hypothesis-driven reasoning agent |
| `langgraphrandom` | `langgraph` | Random agent using LangGraph workflow |
| `langgraphfunc` | `langgraph` | LangGraph functional API agent |
| `langgraphtextonly` | `langgraph` | LangGraph without image frames |
| `smolcodingagent` | `smolagents` | SmolAgents CodeAgent |
| `smolvisionagent` | `smolagents` | SmolAgents with vision |

## Building Your Own Agent

Subclass the `Agent` base class:

```python
from arc_agi_3 import Agent
from arc_agi_3._structs import FrameData, GameAction, GameState

class MyAgent(Agent):
    MAX_ACTIONS = 80

    def is_done(self, frames: list[FrameData], latest_frame: FrameData) -> bool:
        return latest_frame.state is GameState.WIN

    def choose_action(
        self,
        frames: list[FrameData],
        latest_frame: FrameData,
    ) -> GameAction:
        # Your logic here
        if latest_frame.state in [GameState.NOT_PLAYED, GameState.GAME_OVER]:
            return GameAction.RESET

        # Choose an action based on the frame data
        action = GameAction.ACTION1
        action.reasoning = "My reasoning for this action"
        return action
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ARC_API_KEY` | Your ARC-AGI-3 API key | Required |
| `SCHEME` | HTTP scheme | `https` |
| `HOST` | API host | `three.arcprize.org` |
| `PORT` | API port | (standard) |
| `RECORDINGS_DIR` | Directory for session recordings | `.` |
| `AGENTOPS_API_KEY` | AgentOps API key for observability | Optional |
| `OPENAI_API_KEY` | OpenAI API key for LLM agents | Required for LLM agents |
| `DEBUG` | Enable debug logging | `False` |

## Data Structures

### GameAction

Available actions:
- `RESET` - Start or restart a game
- `ACTION1` - Simple action (typically Up/W)
- `ACTION2` - Simple action (typically Down/S)
- `ACTION3` - Simple action (typically Left/A)
- `ACTION4` - Simple action (typically Right/D)
- `ACTION5` - Simple action (typically Enter/Space)
- `ACTION6` - Complex action with x,y coordinates (Click/Point)
- `ACTION7` - Simple action

### GameState

- `NOT_PLAYED` - Game hasn't started
- `NOT_FINISHED` - Game in progress
- `WIN` - Game won
- `GAME_OVER` - Game lost

### FrameData

Each frame contains:
- `game_id` - The game identifier
- `frame` - 3D list of grid data (list of 2D grids)
- `state` - Current GameState
- `score` - Current score (0-254)
- `available_actions` - List of valid actions for this state

## Links

- [ARC Prize](https://arcprize.org/)
- [ARC-AGI-3 Preview](https://three.arcprize.org/)
- [Documentation](https://docs.arcprize.org/)
- [GitHub Repository](https://github.com/arcprize/ARC-AGI-3-Agents)

## License

MIT License - see the original [ARC-AGI-3-Agents](https://github.com/arcprize/ARC-AGI-3-Agents) repository.
