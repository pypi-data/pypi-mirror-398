"""Recording and playback functionality for agent sessions."""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any

RECORDING_SUFFIX = ".recording.jsonl"


def get_recordings_dir() -> str:
    """Get the current recordings directory from environment variable."""
    return os.environ.get("RECORDINGS_DIR", "")


class Recorder:
    """Records and retrieves agent session data to/from JSONL files."""

    def __init__(
        self,
        prefix: str,
        filename: str | None = None,
        guid: str | None = None,
    ) -> None:
        """Initialize a recorder.

        Args:
            prefix: Prefix for the recording filename
            filename: Optional existing filename to use
            guid: Optional GUID to use (extracted from filename if provided)
        """
        self.guid = self.get_guid(filename) if filename else (guid or str(uuid.uuid4()))
        self.prefix = prefix
        recordings_dir = get_recordings_dir()
        self.filename = (
            os.path.join(recordings_dir, filename)
            if filename
            else os.path.join(
                recordings_dir,
                f"{self.prefix}.{self.guid}{RECORDING_SUFFIX}",
            )
        )
        # Create directory once during initialization
        if recordings_dir:
            os.makedirs(recordings_dir, exist_ok=True)

    def record(self, data: dict[str, Any]) -> None:
        """Record an event to the file.

        Args:
            data: Dictionary of data to record (must be JSON-serializable)
        """
        event: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data,
        }

        with open(self.filename, "a", encoding="utf-8") as f:
            json.dump(event, f)
            f.write("\n")

    def get(self) -> list[dict[str, Any]]:
        """Load all recorded events.

        Returns:
            List of recorded events as dictionaries
        """
        if not os.path.isfile(self.filename):
            return []

        events: list[dict[str, Any]] = []
        with open(self.filename, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    events.append(json.loads(line))
        return events

    def __repr__(self) -> str:
        return f"<Recorder guid={self.guid} file={self.filename}>"

    @classmethod
    def list(cls) -> list[str]:
        """List all recording filenames in the recordings directory.

        Returns:
            List of recording filenames
        """
        recordings_dir = get_recordings_dir()
        if recordings_dir:
            os.makedirs(recordings_dir, exist_ok=True)
            filenames = os.listdir(recordings_dir)
        else:
            filenames = []
        return [f for f in filenames if f.endswith(RECORDING_SUFFIX)]

    @classmethod
    def get_prefix(cls, filename: str) -> str:
        """Extract the prefix portion from a filename.

        Example:
            locksmith.random.50.81329339-1951-487c-8bed-e9d4780320f2.recording.jsonl
            Returns: locksmith.random.50
        """
        if "." in filename:
            parts = filename.split(".")
            return ".".join(parts[:-3])
        return filename

    @classmethod
    def get_prefix_one(cls, filename: str) -> str:
        """Extract only the first segment of a filename.

        Example:
            locksmith.random.50.81329339-1951-487c-8bed-e9d4780320f2.recording.jsonl
            Returns: locksmith
        """
        if "." in filename:
            parts = filename.split(".")
            return parts[0]
        return filename

    @classmethod
    def get_guid(cls, filename: str) -> str:
        """Extract the GUID portion from a filename.

        Example:
            locksmith.random.50.81329339-1951-487c-8bed-e9d4780320f2.recording.jsonl
            Returns: 81329339-1951-487c-8bed-e9d4780320f2
        """
        if "." in filename:
            parts = filename.split(".")
            return parts[-3]
        return filename


__all__ = ["RECORDING_SUFFIX", "get_recordings_dir", "Recorder"]
