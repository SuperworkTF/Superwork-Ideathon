"""배치 오케스트레이션: 수집 → 신규 diff → 심사(+시장반응) → 기록 → 종합."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import List, Optional

from . import config as cfg
from .judge import judge_idea
from .llm import LLM, ClaudeCLI, LLMError, MockLLM
from .market_sim import simulate_market
from .models import Idea, Judgment
from .report import judgment_to_dict, write_idea_report, write_summary
from .sheet import load_ideas
from .state import State


@dataclass
class RunResult:
    total_rows: int
    new_judged: int
    skipped_existing: int
    skipped_empty: int
    failed: int
    judgments: List[Judgment]


def resolve_backend(conf: cfg.Config, dry_run: bool) -> str:
    """실제 사용할 백엔드 결정. auto = 키 있으면 api, 없으면 cli(구독)."""
    backend = "mock" if dry_run else conf.backend
    if backend == "auto":
        backend = "api" if conf.api_key else "cli"
    return backend


def _build_llm(conf: cfg.Config, dry_run: bool, model: str):
    backend = resolve_backend(conf, dry_run)
    if backend == "mock":
        return MockLLM(model="mock-dry-run")
    if backend == "api":
        if not conf.api_key:
            raise LLMError("backend=api 인데 ANTHROPIC_API_KEY 미설정")
        return LLM(api_key=conf.api_key, model=model)
    if backend == "cli":
        return ClaudeCLI(model=model, bin=conf.claude_bin)
    raise LLMError(f"알 수 없는 JUDGE_BACKEND: {backend!r} (auto|cli|api|mock)")


def run(
    dry_run: bool = False,
    limit: Optional[int] = None,
    force: bool = False,
    skip_market: bool = False,
    verbose: bool = True,
) -> RunResult:
    conf = cfg.Config.load()
    llm_judge = _build_llm(conf, dry_run, conf.judge_model)
    llm_sim = _build_llm(conf, dry_run, conf.sim_model)

    ideas: List[Idea] = load_ideas(conf.sheet_csv_url)
    state = State(cfg.STATE_PATH)

    new_judgments: List[Judgment] = []
    skipped_existing = skipped_empty = failed = 0

    def log(msg: str) -> None:
        if verbose:
            print(msg, flush=True)

    log(f"시트에서 {len(ideas)}건 로드. 신규 심사 시작...")
    for idea in ideas:
        if not force and state.is_judged(idea.idea_id):
            skipped_existing += 1
            continue
        if not idea.is_substantive:
            skipped_empty += 1
            log(f"  · 스킵(공란/무의미): row{idea.row_index} {idea.service_name!r}")
            continue

        log(f"  ▸ 심사: row{idea.row_index} [{idea.idea_id}] {idea.service_name!r}")
        # 한 건 실패가 배치 전체를 중단시키지 않도록 격리 + 증분 저장(크론 내구성)
        try:
            market = None
            if not skip_market:
                market = simulate_market(llm_sim, conf.personas, idea)
            judgment = judge_idea(llm_judge, conf.rubric, idea, market=market)
            path = write_idea_report(cfg.REPORTS_DIR, conf.rubric, judgment)
        except Exception as e:  # noqa: BLE001 — 개별 아이디어 실패 격리
            failed += 1
            log(f"      ✗ 심사 실패(스킵, 미기록): {type(e).__name__}: {e}")
            continue

        state.mark(
            idea.idea_id,
            {
                "service": idea.service_name,
                "final_score": round(judgment.final_score, 1),
                "verdict": judgment.verdict,
                "judged_at": judgment.judged_at,
                "report": path.name,
            },
        )
        state.save()  # 매 건 저장 → 중단되어도 완료분 보존
        new_judgments.append(judgment)
        log(f"      → {judgment.final_score:.1f}/100  {judgment.verdict}  ({path.name})")

        if limit and len(new_judgments) >= limit:
            log(f"  (limit={limit} 도달, 중단)")
            break

    state.save()

    # 종합 산출물 — 기존 scores.json 과 병합(누적). 재심사분은 idea_id 로 덮어씀.
    if new_judgments:
        merged: dict = {}
        if cfg.SCORES_JSON.exists():
            try:
                prior = json.loads(cfg.SCORES_JSON.read_text(encoding="utf-8"))
                for d in prior:
                    merged[d.get("idea", {}).get("idea_id")] = d
            except (json.JSONDecodeError, OSError):
                pass  # 손상 시 신규분만으로 재구성
        for j in new_judgments:
            merged[j.idea.idea_id] = judgment_to_dict(j)
        merged.pop(None, None)
        write_summary(
            cfg.SCORES_CSV, cfg.SCORES_JSON, cfg.LEADERBOARD, list(merged.values())
        )

    return RunResult(
        total_rows=len(ideas),
        new_judged=len(new_judgments),
        skipped_existing=skipped_existing,
        skipped_empty=skipped_empty,
        failed=failed,
        judgments=new_judgments,
    )
