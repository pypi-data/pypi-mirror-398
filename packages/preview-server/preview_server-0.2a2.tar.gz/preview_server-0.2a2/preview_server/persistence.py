"""Persistence layer for repo configuration."""

import json
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class RepoState:
    """State for a single repository."""

    label: str
    path: str
    paused: bool = False


class RepoPersistence:
    """Manages persisting repo configuration to a JSON file.

    If no path is provided, repos are stored in memory only and
    will be lost when the server restarts.

    File format:
        {
            "repos": [
                {"label": "frontend", "path": "/path/to/repo", "paused": false},
                {"label": "backend", "path": "https://github.com/...", "paused": true}
            ]
        }
    """

    def __init__(self, path: Optional[str] = None):
        """Initialize persistence.

        Args:
            path: Path to JSON file for persistence. If None, repos are
                  stored in memory only.
        """
        self.path = Path(path) if path else None
        self._lock = threading.Lock()

    def load(self) -> dict[str, RepoState]:
        """Load repos from persistence file.

        Returns:
            Dict mapping label to RepoState. Empty dict if file doesn't exist.
        """
        if not self.path or not self.path.exists():
            return {}

        with self._lock:
            with open(self.path, "r") as f:
                data = json.load(f)

            repos = {}
            for item in data.get("repos", []):
                repos[item["label"]] = RepoState(
                    label=item["label"],
                    path=item["path"],
                    paused=item.get("paused", False),
                )
            return repos

    def save(self, repos: dict[str, RepoState]) -> None:
        """Save repos to persistence file (pretty-printed JSON).

        Args:
            repos: Dict mapping label to RepoState.
        """
        if not self.path:
            return

        with self._lock:
            data = {
                "repos": [
                    {
                        "label": rs.label,
                        "path": rs.path,
                        "paused": rs.paused,
                    }
                    for rs in repos.values()
                ]
            }

            # Write atomically using temp file + rename
            temp_path = self.path.with_suffix(".tmp")
            with open(temp_path, "w") as f:
                json.dump(data, f, indent=2)
                f.write("\n")
            temp_path.rename(self.path)

    def initialize_from(self, initial_repos: dict[str, str]) -> dict[str, RepoState]:
        """Initialize persistence from initial config.

        If persist file exists, use it as source of truth.
        Otherwise, create RepoState objects from initial_repos and save them.

        Args:
            initial_repos: Dict mapping label to path/URL.

        Returns:
            Dict mapping label to RepoState.
        """
        if self.path and self.path.exists():
            return self.load()

        # Create from initial config
        repos = {
            label: RepoState(label=label, path=path, paused=False)
            for label, path in initial_repos.items()
        }

        self.save(repos)
        return repos
