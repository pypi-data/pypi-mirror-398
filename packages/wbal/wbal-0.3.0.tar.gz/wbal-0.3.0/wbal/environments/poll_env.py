from __future__ import annotations

from datetime import datetime
from typing import Any

from wbal.environments.data_env import DataEnv
from wbal.helper import weaveTool

DEFAULT_POLL_INSTRUCTIONS = "You are a polling agent. Log observations and notes for future chat sessions."


class PollEnv(DataEnv):
    """Environment for unattended polling agents (write capabilities)."""

    poll_instructions: str = DEFAULT_POLL_INSTRUCTIONS

    def observe(self) -> str:
        base = self.poll_instructions.strip()
        rest = super().observe()
        return f"{base}\n\n{rest}" if base else rest

    @weaveTool
    def store_note(self, key: str, content: str, category: str = "general") -> dict[str, Any]:
        """Store or update a note (persists if working_directory is set)."""
        now = datetime.now().isoformat()
        is_update = key in self._state["notes"]
        self._state["notes"][key] = {
            "content": content,
            "category": category,
            "created_at": self._state["notes"].get(key, {}).get("created_at", now),
            "updated_at": now,
        }
        self.save_state()
        return {"success": True, "action": "updated" if is_update else "created", "key": key, "category": category}

    @weaveTool
    def delete_note(self, key: str) -> dict[str, Any]:
        """Delete a stored note."""
        if key in self._state["notes"]:
            del self._state["notes"][key]
            self.save_state()
            return {"success": True, "deleted": key}
        return {"success": False, "error": f"Note '{key}' not found"}

    @weaveTool
    def add_observation(self, observation: str, category: str = "general", severity: str = "INFO") -> dict[str, Any]:
        """Append an observation to the log (persisted if working_directory set)."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "observation": observation,
            "category": category,
            "severity": severity,
        }
        self._state.setdefault("observations", []).append(entry)
        if len(self._state["observations"]) > 1000:
            self._state["observations"] = self._state["observations"][-1000:]
        self.save_state()
        return {"success": True, "observation": entry}
