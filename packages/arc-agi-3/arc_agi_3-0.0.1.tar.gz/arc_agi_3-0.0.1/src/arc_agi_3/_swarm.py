"""Swarm orchestration for running multiple agents across multiple games."""

from __future__ import annotations

import json
import logging
import os
from threading import Thread
from typing import TYPE_CHECKING

import requests

from ._structs import Scorecard

if TYPE_CHECKING:
    from ._agent import Agent

logger = logging.getLogger(__name__)


class Swarm:
    """Orchestration for many agents playing many ARC-AGI-3 games."""

    GAMES: list[str]
    ROOT_URL: str
    COUNT: int
    agent_name: str
    agent_class: type[Agent]
    threads: list[Thread]
    agents: list[Agent]
    record_games: list[str]
    cleanup_threads: list[Thread]
    headers: dict[str, str]
    card_id: str | None
    _session: requests.Session

    def __init__(
        self,
        agent: str,
        ROOT_URL: str,
        games: list[str],
        tags: list[str] | None = None,
    ) -> None:
        """Initialize a Swarm.

        Args:
            agent: Name of the agent to run (must be in AVAILABLE_AGENTS)
            ROOT_URL: Base URL for the API
            games: List of game IDs to play
            tags: Optional tags for the scorecard
        """
        from . import AVAILABLE_AGENTS

        self.GAMES = games
        self.ROOT_URL = ROOT_URL
        self.agent_name = agent
        self.agent_class = AVAILABLE_AGENTS[agent]
        self.threads = []
        self.agents = []
        self.cleanup_threads = []
        self.headers = {
            "X-API-Key": os.getenv("ARC_API_KEY", ""),
            "Accept": "application/json",
        }
        self._session = requests.Session()
        self._session.headers.update(self.headers)
        self.tags = tags.copy() if tags else []

        # Set up base tags for tracing
        if self.agent_name.endswith(".recording.jsonl"):
            # Extract GUID from playback filename
            parts = self.agent_name.split(".")
            guid = parts[-3] if len(parts) >= 4 else "unknown"
            self.tags.extend(["playback", guid])
        else:
            self.tags.extend(["agent", self.agent_name])

    def main(self) -> Scorecard | None:
        """The main orchestration loop. Continues until all agents are done."""
        # Submit start of scorecard
        self.card_id = self.open_scorecard()

        # Create all the agents
        for i in range(len(self.GAMES)):
            g = self.GAMES[i % len(self.GAMES)]
            a = self.agent_class(
                card_id=self.card_id,
                game_id=g,
                agent_name=self.agent_name,
                ROOT_URL=self.ROOT_URL,
                record=True,
                cookies=self._session.cookies,
                tags=self.tags,
            )
            self.agents.append(a)

        # Create all the threads
        for a in self.agents:
            self.threads.append(Thread(target=a.main, daemon=True))

        # Start all the threads
        for t in self.threads:
            t.start()

        # Wait for all agents to finish
        for t in self.threads:
            t.join()

        # All agents are now done
        card_id = self.card_id
        scorecard = self.close_scorecard(card_id)
        if scorecard:
            logger.info("--- FINAL SCORECARD REPORT ---")
            logger.info(json.dumps(scorecard.model_dump(), indent=2))

        # Provide web link to scorecard
        if card_id:
            scorecard_url = f"{self.ROOT_URL}/scorecards/{card_id}"
            logger.info(f"View your scorecard online: {scorecard_url}")

        self.cleanup(scorecard)

        return scorecard

    def open_scorecard(self) -> str:
        """Open a new scorecard via the API.

        Returns:
            The card_id for the new scorecard

        Raises:
            Exception: If the API request fails
        """
        json_str = json.dumps({"tags": self.tags})

        r = self._session.post(
            f"{self.ROOT_URL}/api/scorecard/open",
            json=json.loads(json_str),
            headers=self.headers,
        )

        try:
            response_data = r.json()
        except ValueError as e:
            raise Exception(f"Failed to open scorecard: {r.status_code} - {r.text}") from e

        if not r.ok:
            raise Exception(
                f"API error during open scorecard: {r.status_code} - {response_data}"
            )

        return str(response_data["card_id"])

    def close_scorecard(self, card_id: str) -> Scorecard | None:
        """Close a scorecard via the API.

        Args:
            card_id: The card_id to close

        Returns:
            The final Scorecard, or None if the request failed
        """
        self.card_id = None
        json_str = json.dumps({"card_id": card_id})
        r = self._session.post(
            f"{self.ROOT_URL}/api/scorecard/close",
            json=json.loads(json_str),
            headers=self.headers,
        )

        try:
            response_data = r.json()
        except ValueError:
            logger.warning(f"Failed to close scorecard: {r.status_code} - {r.text}")
            return None

        if not r.ok:
            logger.warning(
                f"API error during close scorecard: {r.status_code} - {response_data}"
            )
            return None

        return Scorecard.model_validate(response_data)

    def cleanup(self, scorecard: Scorecard | None = None) -> None:
        """Cleanup all agents."""
        for a in self.agents:
            a.cleanup(scorecard)
        if hasattr(self, "_session"):
            self._session.close()


__all__ = ["Swarm"]
