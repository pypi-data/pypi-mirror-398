from __future__ import annotations

import json
import os
import textwrap
from datetime import datetime
from typing import Any, Callable

from wbal.environment import Environment
from wbal.helper import weaveTool

DEFAULT_STATE = {
    "notes": {},
    "observations": [],
    "metadata": {"created_at": None, "last_updated": None},
}


class DataEnv(Environment):
    """Base environment for WBAL agents.

    Holds shared state (notes/observations) and optional persistence.
    Provides read-only tools; PollEnv adds write capabilities.
    """

    task: str = ""
    working_directory: str | None = None
    include_working_directory_listing: bool = True

    output_handler: Callable[[str], None] = lambda x: print(x)

    def __init__(self, working_directory: str | None = None, **kwargs: Any):
        super().__init__(working_directory=working_directory, **kwargs)
        self.working_directory = working_directory
        self._state: dict[str, Any] = json.loads(json.dumps(DEFAULT_STATE))
        if self.working_directory:
            self._ensure_working_directory()
            self.load_state()

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------
    def _ensure_working_directory(self) -> None:
        if self.working_directory:
            os.makedirs(self.working_directory, exist_ok=True)

    def _state_file_path(self) -> str | None:
        if self.working_directory:
            return os.path.join(self.working_directory, "environment_state.json")
        return None

    def load_state(self) -> bool:
        state_file = self._state_file_path()
        if not state_file or not os.path.exists(state_file):
            return False
        try:
            with open(state_file, "r") as f:
                loaded = json.load(f)
            self._state.update(loaded)
            return True
        except (json.JSONDecodeError, OSError):
            return False

    def save_state(self) -> bool:
        state_file = self._state_file_path()
        if not state_file:
            return False
        try:
            now = datetime.now().isoformat()
            self._state["metadata"]["last_updated"] = now
            if self._state["metadata"]["created_at"] is None:
                self._state["metadata"]["created_at"] = now
            with open(state_file, "w") as f:
                json.dump(self._state, f, indent=2)
            return True
        except OSError:
            return False

    # ------------------------------------------------------------------
    # Observation helpers
    # ------------------------------------------------------------------
    def _get_state_summary(self) -> str:
        notes_count = len(self._state.get("notes", {}))
        obs_count = len(self._state.get("observations", []))
        last_updated = self._state.get("metadata", {}).get("last_updated", "never")
        categories = list({n.get("category", "general") for n in self._state.get("notes", {}).values()})
        return textwrap.dedent(
            f"""
            ## Environment State
            - Notes stored: {notes_count}
            - Observations logged: {obs_count}
            - Note categories: {', '.join(categories) if categories else 'none'}
            - Last updated: {last_updated}
            """
        ).strip()

    def _get_working_directory_contents(self) -> str:
        if not self.working_directory or not os.path.exists(self.working_directory):
            return ""
        try:
            files = os.listdir(self.working_directory)
        except OSError:
            return ""
        if not files:
            return ""
        file_list = "\n".join(f"  - {f}" for f in sorted(files))
        return f"## Working Directory\nPath: {self.working_directory}\n{file_list}"

    def observe(self) -> str:
        parts = []
        base = self.env
        if base:
            parts.append(base)
        parts.append(self._get_state_summary())
        if self.include_working_directory_listing:
            wd = self._get_working_directory_contents()
            if wd:
                parts.append(wd)
        tool_desc = self.get_tool_descriptions()
        if tool_desc:
            parts.append(tool_desc)
        return "\n\n".join([p for p in parts if p])

    # ------------------------------------------------------------------
    # Read-only tools
    # ------------------------------------------------------------------
    @weaveTool
    def get_notes(self, category: str | None = None, key: str | None = None) -> dict[str, Any]:
        """Retrieve stored notes (read-only here; PollEnv writes)."""
        if key:
            note = self._state["notes"].get(key)
            return {"success": note is not None, "notes": {key: note} if note else {}, "count": 1 if note else 0}
        notes = self._state["notes"]
        if category:
            notes = {k: v for k, v in notes.items() if v.get("category") == category}
        return {"success": True, "notes": notes, "count": len(notes)}

    @weaveTool
    def get_observations(self, category: str | None = None, limit: int | None = None) -> dict[str, Any]:
        """Retrieve stored observations (append-only log written by PollEnv)."""
        observations = list(self._state.get("observations", []))
        if category:
            observations = [o for o in observations if o.get("category") == category]
        if limit is not None and limit > 0:
            observations = observations[-limit:]
        return {"success": True, "observations": observations, "count": len(observations)}
