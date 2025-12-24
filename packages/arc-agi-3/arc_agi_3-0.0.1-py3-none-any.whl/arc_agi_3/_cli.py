"""CLI entry point for arc-agi-3."""

from __future__ import annotations

import argparse
import json
import logging
import os
import signal
import sys
import threading
from functools import partial
from types import FrameType
from typing import NoReturn

from dotenv import load_dotenv

# Load environment files
load_dotenv(dotenv_path=".env.example")
load_dotenv(dotenv_path=".env", override=True)

import requests

from . import AVAILABLE_AGENTS
from ._recorder import Recorder
from ._swarm import Swarm
from ._tracing import initialize as init_agentops

logger = logging.getLogger(__name__)


def _get_root_url() -> str:
    """Build the root URL from environment variables."""
    scheme = os.environ.get("SCHEME", "https")
    host = os.environ.get("HOST", "three.arcprize.org")
    port = os.environ.get("PORT", "")

    # Hide standard ports in URL
    if (scheme == "http" and port == "80") or (scheme == "https" and port == "443"):
        port = ""

    if port:
        return f"{scheme}://{host}:{port}"
    return f"{scheme}://{host}"


def run_agent(swarm: Swarm) -> None:
    """Run the swarm and signal completion."""
    swarm.main()
    os.kill(os.getpid(), signal.SIGINT)


def cleanup(
    swarm: Swarm,
    root_url: str,
    signum: int | None,
    frame: FrameType | None,
) -> NoReturn:
    """Handle cleanup on exit."""
    logger.info("Received SIGINT, exiting...")
    card_id = swarm.card_id
    if card_id:
        scorecard = swarm.close_scorecard(card_id)
        if scorecard:
            logger.info("--- EXISTING SCORECARD REPORT ---")
            logger.info(json.dumps(scorecard.model_dump(), indent=2))
            swarm.cleanup(scorecard)

        # Provide web link to scorecard
        scorecard_url = f"{root_url}/scorecards/{card_id}"
        logger.info(f"View your scorecard online: {scorecard_url}")

    sys.exit(0)


def main() -> None:
    """Main CLI entry point."""
    root_url = _get_root_url()
    headers = {
        "X-API-Key": os.getenv("ARC_API_KEY", ""),
        "Accept": "application/json",
    }

    # Configure logging
    log_level = logging.INFO
    if os.environ.get("DEBUG", "False") == "True":
        log_level = logging.DEBUG

    logger.setLevel(log_level)
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(log_level)
    stdout_handler.setFormatter(formatter)

    file_handler = logging.FileHandler("logs.log", mode="w")
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stdout_handler)

    # Parse arguments
    parser = argparse.ArgumentParser(
        description="ARC-AGI-3 Agent Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  arc-agi-3 --agent=random --game=ls20
  arc-agi-3 -a llm -g locksmith -t experiment,v1.0

Available agents depend on installed extras:
  Core: random
  With 'openai' extra: llm, fastllm, reasoningllm, guidedllm, reasoningagent
  With 'langgraph' extra: langgraphrandom, langgraphfunc, langgraphtextonly
  With 'smolagents' extra: smolcodingagent, smolvisionagent
        """,
    )
    parser.add_argument(
        "-a",
        "--agent",
        choices=list(AVAILABLE_AGENTS.keys()),
        help="Choose which agent to run.",
    )
    parser.add_argument(
        "-g",
        "--game",
        help="Choose a specific game_id for the agent to play. "
        "If none specified, plays all available games.",
    )
    parser.add_argument(
        "-t",
        "--tags",
        type=str,
        help="Comma-separated list of tags for the scorecard (e.g., 'experiment,v1.0')",
        default=None,
    )
    parser.add_argument(
        "--list-agents",
        action="store_true",
        help="List all available agents and exit.",
    )

    args = parser.parse_args()

    if args.list_agents:
        print("Available agents:")
        for name in sorted(AVAILABLE_AGENTS.keys()):
            if not name.endswith(".recording.jsonl"):
                print(f"  - {name}")
        return

    if not args.agent:
        parser.error("the following arguments are required: -a/--agent")

    print(f"API endpoint: {root_url}/api/games")

    # Get the list of games from the API
    full_games: list[str] = []
    try:
        with requests.Session() as session:
            session.headers.update(headers)
            r = session.get(f"{root_url}/api/games", timeout=10)

        if r.status_code == 200:
            try:
                full_games = [g["game_id"] for g in r.json()]
            except (ValueError, KeyError) as e:
                logger.error(f"Failed to parse games response: {e}")
                logger.error(f"Response content: {r.text[:200]}")
        else:
            logger.error(
                f"API request failed with status {r.status_code}: {r.text[:200]}"
            )

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to connect to API server: {e}")

    # For playback agents, derive game from recording filename
    if not full_games and args.agent and args.agent.endswith(".recording.jsonl"):
        game_prefix = Recorder.get_prefix_one(args.agent)
        full_games = [game_prefix]
        logger.info(f"Using game '{game_prefix}' derived from playback recording filename")

    games = full_games[:]
    if args.game:
        filters = args.game.split(",")
        games = [
            gid for gid in full_games if any(gid.startswith(prefix) for prefix in filters)
        ]

    logger.info(f"Game list: {games}")

    if not games:
        if full_games:
            logger.error(
                f"The specified game '{args.game}' does not exist or is not available "
                "with your API key. Please try a different game."
            )
        else:
            logger.error(
                "No games available to play. Check API connection or recording file."
            )
        return

    # Build tags
    tags: list[str] = []
    if args.tags:
        user_tags = [tag.strip() for tag in args.tags.split(",")]
        tags.extend(user_tags)

    # Initialize AgentOps client
    init_agentops(api_key=os.getenv("AGENTOPS_API_KEY"), log_level=log_level)

    # Create and run swarm
    swarm = Swarm(
        args.agent,
        root_url,
        games,
        tags=tags,
    )

    agent_thread = threading.Thread(target=partial(run_agent, swarm))
    agent_thread.daemon = True
    agent_thread.start()

    signal.signal(signal.SIGINT, partial(cleanup, swarm, root_url))

    try:
        while agent_thread.is_alive():
            agent_thread.join(timeout=5)
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received in main thread")
        cleanup(swarm, root_url, signal.SIGINT, None)
    except Exception as e:
        logger.error(f"Unexpected error in main thread: {e}")
        cleanup(swarm, root_url, None, None)


if __name__ == "__main__":
    os.environ["TESTING"] = "False"
    main()
