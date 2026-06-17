"""심사 상태 — 배치 멱등성(이미 심사한 아이디어 재심사 방지)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict


class State:
    def __init__(self, path: Path):
        self.path = path
        self.data: Dict[str, dict] = {}
        if path.exists():
            try:
                loaded = json.loads(path.read_text(encoding="utf-8"))
                self.data = loaded.get("judged", {})
            except (json.JSONDecodeError, OSError):
                self.data = {}

    def is_judged(self, idea_id: str) -> bool:
        return idea_id in self.data

    def mark(self, idea_id: str, meta: dict) -> None:
        self.data[idea_id] = meta

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps({"judged": self.data}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
