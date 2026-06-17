"""산출물 렌더링 — 아이디어별 Markdown 리포트 + 종합 CSV/JSON + 리더보드."""
from __future__ import annotations

import csv
import json
import re
from dataclasses import asdict
from pathlib import Path
from typing import List

from .models import Judgment


def _slug(text: str, maxlen: int = 30) -> str:
    s = re.sub(r"[^\w가-힣]+", "-", text.strip())
    return s.strip("-")[:maxlen] or "idea"


def _bar(score: float, width: int = 20, lo: float = 0, hi: float = 10) -> str:
    span = (hi - lo) or 1
    frac = max(0.0, min(1.0, (score - lo) / span))
    filled = round(frac * width)
    return "█" * filled + "░" * (width - filled)


def render_report(rubric: dict, j: Judgment) -> str:
    idea = j.idea
    lines: List[str] = []
    lines.append(f"# 심사 리포트 — {idea.service_name or '(무제)'}")
    lines.append("")
    lines.append(f"- **아이디어 ID**: `{idea.idea_id}`")
    lines.append(f"- **제안자**: {idea.name or '(익명)'} / {idea.affiliation or '(소속미상)'}")
    lines.append(f"- **제출시각**: {idea.timestamp or '-'}")
    lines.append(f"- **심사시각**: {j.judged_at}  ·  **모델**: `{j.model}`")
    lines.append("")
    lines.append(f"## 최종 점수: **{j.final_score:.1f} / 100**  →  {j.verdict}")
    lines.append("")
    lines.append(f"> {j.recommendation}")
    lines.append("")
    lines.append(
        f"- 패널 가중 점수: **{j.panel_score_100:.1f}**"
        + (
            f"  ·  시장반응 점수: **{j.market.demand_score:.1f}**"
            f" (blend {int(rubric.get('market_blend', 0)*100)}%)"
            if j.market
            else ""
        )
    )
    lines.append("")

    # 제출 내용
    lines.append("## 제출 내용")
    lines.append("")
    lines.append("```")
    lines.append(idea.to_brief())
    lines.append("```")
    lines.append("")

    # 차원별 집계
    lines.append("## 차원별 점수 (패널 집계)")
    lines.append("")
    lines.append("| 차원 | 점수 | |")
    lines.append("|---|---|---|")
    dim_name = {d["key"]: d["name"] for d in rubric["dimensions"]}
    for d in rubric["dimensions"]:
        k = d["key"]
        sc = j.dimension_scores.get(k, 0.0)
        lines.append(f"| {dim_name[k]} | {sc:.1f} | `{_bar(sc)}` |")
    lines.append("")

    # 시장반응
    if j.market:
        m = j.market
        lines.append("## 시장반응 시뮬레이션")
        lines.append("")
        lines.append(f"- 합성 페르소나 **{m.num_personas}명** 시뮬레이션")
        lines.append(f"- 평균 시도확률: **{m.adopt_rate*100:.0f}%**  ·  유료전환확률: **{m.pay_rate*100:.0f}%**")
        lines.append(f"- 평균 기대감: **{m.avg_excitement:.1f}/10**  ·  월 지불의향 중앙값: **{m.median_wtp:,} KRW**")
        lines.append(f"- 수요 점수: **{m.demand_score:.1f}/100**")
        lines.append("")
        if m.summary:
            lines.append(f"> {m.summary}")
            lines.append("")
        if m.top_objections:
            lines.append("**주요 거부 이유 (빈도순):**")
            for obj, cnt in m.top_objections:
                lines.append(f"- ({cnt}) {obj}")
            lines.append("")

    # 페르소나별 코멘트
    lines.append("## 심사위원 패널 코멘트")
    lines.append("")
    for ps in j.persona_scores:
        avg = sum(ps.scores.values()) / max(len(ps.scores), 1)
        lines.append(f"### {ps.persona_name}  (평균 {avg:.1f}/10)")
        if ps.overall_comment:
            lines.append(f"{ps.overall_comment}")
        if ps.strengths:
            lines.append("- 강점: " + "; ".join(ps.strengths))
        if ps.flaws:
            lines.append("- 결함: " + "; ".join(ps.flaws))
        lines.append("")

    # 종합 강점/결함
    if j.key_strengths:
        lines.append("## 핵심 강점")
        lines.extend(f"- {s}" for s in j.key_strengths)
        lines.append("")
    if j.fatal_flaws:
        lines.append("## 주요 결함 / 리스크")
        lines.extend(f"- {f}" for f in j.fatal_flaws)
        lines.append("")

    return "\n".join(lines)


def write_idea_report(reports_dir: Path, rubric: dict, j: Judgment) -> Path:
    reports_dir.mkdir(parents=True, exist_ok=True)
    # 파일명을 idea_id 로 고정 → --force 재심사 시 같은 파일을 덮어써 orphan 미발생
    fname = f"{j.idea.idea_id}_{_slug(j.idea.service_name)}.md"
    path = reports_dir / fname
    path.write_text(render_report(rubric, j), encoding="utf-8")
    return path


def judgment_to_dict(j: Judgment) -> dict:
    """Judgment → 영속 dict (scores.json 1건 형태)."""
    return {
        "idea": j.idea.to_dict(),
        "final_score": round(j.final_score, 2),
        "panel_score_100": round(j.panel_score_100, 2),
        "verdict": j.verdict,
        "recommendation": j.recommendation,
        "dimension_scores": {k: round(v, 2) for k, v in j.dimension_scores.items()},
        "market": asdict(j.market) if j.market else None,
        "persona_scores": [asdict(ps) for ps in j.persona_scores],
        "fatal_flaws": j.fatal_flaws,
        "key_strengths": j.key_strengths,
        "judged_at": j.judged_at,
        "model": j.model,
    }


def _csv_row(jd: dict) -> dict:
    """judgment dict → scores.csv 1행 (차원 점수 평탄화)."""
    idea = jd.get("idea", {})
    market = jd.get("market") or {}
    row = {
        "idea_id": idea.get("idea_id", ""),
        "service_name": idea.get("service_name", ""),
        "name": idea.get("name", ""),
        "affiliation": idea.get("affiliation", ""),
        "final_score": round(jd.get("final_score", 0), 1),
        "panel_score": round(jd.get("panel_score_100", 0), 1),
        "market_score": round(market.get("demand_score", ""), 1) if market else "",
        "verdict": jd.get("verdict", ""),
        "judged_at": jd.get("judged_at", ""),
    }
    for k, v in jd.get("dimension_scores", {}).items():
        row[f"dim_{k}"] = round(v, 2)
    return row


def write_summary(
    scores_csv: Path,
    scores_json: Path,
    leaderboard: Path,
    judgment_dicts: List[dict],
) -> None:
    """누적 심사 결과(dict 리스트) → CSV / JSON / leaderboard.md (점수 내림차순)."""
    ranked = sorted(judgment_dicts, key=lambda d: d.get("final_score", 0), reverse=True)
    scores_csv.parent.mkdir(parents=True, exist_ok=True)

    # CSV — 차원 컬럼이 행마다 다를 수 있으니 키 합집합으로 헤더 구성
    if ranked:
        rows = [_csv_row(d) for d in ranked]
        fields: List[str] = []
        for r in rows:
            for k in r:
                if k not in fields:
                    fields.append(k)
        with scores_csv.open("w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=fields, restval="")
            w.writeheader()
            w.writerows(rows)

    # JSON
    scores_json.write_text(
        json.dumps(ranked, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # leaderboard.md
    lines = ["# 아이디어톤 리더보드", "", f"총 {len(ranked)}건 심사.", ""]
    lines.append("| 순위 | 점수 | 판정 | 서비스명 | 제안자 | ID |")
    lines.append("|---:|---:|---|---|---|---|")
    for i, d in enumerate(ranked, start=1):
        idea = d.get("idea", {})
        lines.append(
            f"| {i} | {d.get('final_score', 0):.1f} | {d.get('verdict', '')} | "
            f"{idea.get('service_name') or '(무제)'} | {idea.get('name') or '익명'} | "
            f"`{idea.get('idea_id', '')}` |"
        )
    lines.append("")
    leaderboard.write_text("\n".join(lines), encoding="utf-8")
