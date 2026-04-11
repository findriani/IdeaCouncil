"""Persist lightweight Streamlit session snapshots for later restore."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import uuid4


class SessionSnapshotStore:
    """Save and load restorable app state using a stable session id."""

    def __init__(self, output_dir: Path):
        self.base_dir = Path(output_dir) / "sessions"
        self.base_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def new_session_id() -> str:
        return uuid4().hex[:12]

    def path_for(self, session_id: str) -> Path:
        return self.base_dir / f"{session_id}.json"

    def save(self, session_id: str, payload: Dict[str, Any]) -> Path:
        path = self.path_for(session_id)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=True)
        return path

    def load(self, session_id: str) -> Optional[Dict[str, Any]]:
        path = self.path_for(session_id)
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
