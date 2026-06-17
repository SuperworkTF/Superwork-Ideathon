"""CLI 엔트리포인트.

사용:
  python -m ideathon_judge run [--dry-run] [--limit N] [--force] [--no-market]
  python -m ideathon_judge list
  python -m ideathon_judge show <idea_id>
  python -m ideathon_judge leaderboard
  python -m ideathon_judge reset [--yes]
"""
from __future__ import annotations

import argparse
import sys

from . import config as cfg
from .pipeline import resolve_backend, run
from .sheet import load_ideas
from .state import State


def _cmd_run(args: argparse.Namespace) -> int:
    conf = cfg.Config.load()
    backend = resolve_backend(conf, args.dry_run)
    label = {
        "mock": "DRY-RUN · mock(가짜 점수)",
        "cli": f"LIVE · Claude 구독(claude CLI) · {conf.judge_model}/{conf.sim_model}",
        "api": f"LIVE · API 키 · {conf.judge_model}/{conf.sim_model}",
    }.get(backend, backend)
    print(f"=== 아이디어톤 심사 배치 [{label}] ===")
    if backend == "cli":
        print("  (ANTHROPIC_API_KEY 없음 → Claude 구독 공유 사용. 호출당 수초~수십초 소요.)\n")
    res = run(
        dry_run=args.dry_run,
        limit=args.limit,
        force=args.force,
        skip_market=args.no_market,
    )
    print("\n=== 완료 ===")
    print(f"시트 총 {res.total_rows}행 · 신규 심사 {res.new_judged} · "
          f"기존 스킵 {res.skipped_existing} · 공란 스킵 {res.skipped_empty} · "
          f"실패 {res.failed}")
    if res.judgments:
        print(f"\n리더보드: {cfg.LEADERBOARD}")
        print(f"상세 리포트: {cfg.REPORTS_DIR}/")
        ranked = sorted(res.judgments, key=lambda x: x.final_score, reverse=True)
        print("\nTop 결과:")
        for i, j in enumerate(ranked[:10], 1):
            print(f"  {i:>2}. {j.final_score:5.1f}  {j.verdict:<22} {j.idea.service_name}")
    return 0


def _cmd_list(args: argparse.Namespace) -> int:
    conf = cfg.Config.load()
    ideas = load_ideas(conf.sheet_csv_url)
    state = State(cfg.STATE_PATH)
    print(f"시트 {len(ideas)}건:")
    for idea in ideas:
        mark = "✓심사됨" if state.is_judged(idea.idea_id) else (
            "·신규" if idea.is_substantive else "✗공란")
        print(f"  [{idea.idea_id}] {mark}  row{idea.row_index}  {idea.service_name!r} "
              f"— {idea.name}/{idea.affiliation}")
    return 0


def _cmd_show(args: argparse.Namespace) -> int:
    state = State(cfg.STATE_PATH)
    meta = state.data.get(args.idea_id)
    if not meta:
        print(f"미심사 ID: {args.idea_id}")
        return 1
    report = cfg.REPORTS_DIR / meta.get("report", "")
    if report.exists():
        print(report.read_text(encoding="utf-8"))
        return 0
    print(meta)
    return 0


def _cmd_leaderboard(args: argparse.Namespace) -> int:
    if cfg.LEADERBOARD.exists():
        print(cfg.LEADERBOARD.read_text(encoding="utf-8"))
        return 0
    print("리더보드 없음. 먼저 `run` 실행.")
    return 1


def _cmd_reset(args: argparse.Namespace) -> int:
    if not args.yes:
        print("심사 상태(state.json)를 삭제하면 모든 아이디어가 재심사 대상이 됩니다.")
        print("확인하려면 --yes 플래그와 함께 실행하세요.")
        return 1
    if cfg.STATE_PATH.exists():
        cfg.STATE_PATH.unlink()
        print(f"삭제: {cfg.STATE_PATH}")
    else:
        print("상태 파일 없음.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ideathon_judge", description="사내 아이디어톤 심사 배치"
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="신규 아이디어 배치 심사")
    r.add_argument("--dry-run", action="store_true", help="mock LLM (API 키 불필요)")
    r.add_argument("--limit", type=int, default=None, help="이번 실행 최대 심사 건수")
    r.add_argument("--force", action="store_true", help="이미 심사한 것도 재심사")
    r.add_argument("--no-market", action="store_true", help="시장반응 시뮬레이션 생략")
    r.set_defaults(func=_cmd_run)

    li = sub.add_parser("list", help="시트 아이디어 + 심사 상태 목록")
    li.set_defaults(func=_cmd_list)

    sh = sub.add_parser("show", help="심사 리포트 출력")
    sh.add_argument("idea_id")
    sh.set_defaults(func=_cmd_show)

    lb = sub.add_parser("leaderboard", help="리더보드 출력")
    lb.set_defaults(func=_cmd_leaderboard)

    rs = sub.add_parser("reset", help="심사 상태 초기화")
    rs.add_argument("--yes", action="store_true", help="확인")
    rs.set_defaults(func=_cmd_reset)
    return p


def main(argv=None) -> int:
    import os

    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\n중단됨.")
        return 130
    except Exception as e:  # noqa: BLE001 — 크론 로그를 위한 깔끔한 종료
        if os.environ.get("DEBUG"):
            raise
        print(f"오류: {type(e).__name__}: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
