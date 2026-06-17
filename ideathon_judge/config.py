"""설정 로딩 — 루브릭/페르소나 YAML, .env, 경로."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "config"
RESULTS_DIR = ROOT / "results"
REPORTS_DIR = RESULTS_DIR / "reports"
STATE_PATH = RESULTS_DIR / "state.json"
SCORES_CSV = RESULTS_DIR / "scores.csv"
SCORES_JSON = RESULTS_DIR / "scores.json"
LEADERBOARD = RESULTS_DIR / "leaderboard.md"

DEFAULT_SHEET_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1odEggEuF2E6znnAN4rHF5pIbcoR_dbt6MgD8JloSfzU/export?format=csv&gid=1041254954"
)


def _load_env_file() -> None:
    """의존성 없는 최소 .env 로더 (KEY=VALUE). 이미 설정된 환경변수는 유지."""
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export ") :]
        key, val = line.split("=", 1)
        key, val = key.strip(), val.strip()
        # 따옴표로 감싼 값의 따옴표 제거 (KEY="sk-..." → sk-...)
        if len(val) >= 2 and val[0] == val[-1] and val[0] in ("'", '"'):
            val = val[1:-1]
        os.environ.setdefault(key, val)


@dataclass
class Config:
    rubric: dict
    personas: dict
    sheet_csv_url: str
    judge_model: str
    sim_model: str
    api_key: Optional[str]
    backend: str  # auto | cli | api | mock
    claude_bin: str

    @classmethod
    def load(cls) -> "Config":
        _load_env_file()
        rubric = yaml.safe_load((CONFIG_DIR / "rubric.yaml").read_text(encoding="utf-8"))
        personas = yaml.safe_load((CONFIG_DIR / "personas.yaml").read_text(encoding="utf-8"))
        return cls(
            rubric=rubric,
            personas=personas,
            sheet_csv_url=os.environ.get("SHEET_CSV_URL", DEFAULT_SHEET_URL),
            judge_model=os.environ.get("JUDGE_MODEL", "claude-opus-4-8"),
            sim_model=os.environ.get("SIM_MODEL", "claude-sonnet-4-6"),
            api_key=os.environ.get("ANTHROPIC_API_KEY"),
            # auto: 키 있으면 API, 없으면 claude CLI(구독 공유). cli/api/mock 강제 가능.
            backend=os.environ.get("JUDGE_BACKEND", "auto").lower(),
            claude_bin=os.environ.get("CLAUDE_BIN", "claude"),
        )
