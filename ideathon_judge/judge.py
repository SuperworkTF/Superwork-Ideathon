"""다관점 비판적 심사 — 패널 페르소나가 각 차원을 독립 채점 후 가중 집계."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional, Tuple

from .models import Idea, Judgment, MarketReaction, PersonaScore


def build_persona_schema(rubric: dict) -> dict:
    """루브릭 차원으로부터 페르소나 채점 스키마를 동적 생성."""
    dims = rubric["dimensions"]
    score_props = {
        d["key"]: {
            "type": "integer",
            "minimum": 0,
            "maximum": 10,
            "description": f'{d["name"]}: {d["question"]}',
        }
        for d in dims
    }
    rationale_props = {
        d["key"]: {"type": "string", "description": f'{d["name"]} 채점 근거 (1-2문장, 구체적)'}
        for d in dims
    }
    return {
        "type": "object",
        "properties": {
            "scores": {
                "type": "object",
                "properties": score_props,
                "required": list(score_props),
            },
            "rationales": {
                "type": "object",
                "properties": rationale_props,
                "required": list(rationale_props),
            },
            "strengths": {
                "type": "array",
                "items": {"type": "string"},
                "description": "핵심 강점 1-3개",
                "minItems": 1,
            },
            "flaws": {
                "type": "array",
                "items": {"type": "string"},
                "description": "치명적/주요 결함 (없으면 빈 배열). 구체적으로.",
            },
            "overall_comment": {
                "type": "string",
                "description": "이 관점에서의 총평 2-3문장",
            },
        },
        "required": ["scores", "rationales", "strengths", "flaws", "overall_comment"],
    }


def persona_system(rubric: dict, persona: dict) -> str:
    anchors = "\n".join(
        f"  {k}점대: {v}" for k, v in rubric["scale"]["anchors"].items()
    )
    dims = "\n".join(
        f'  - {d["name"]} ({d["key"]}): {d["question"]}' for d in rubric["dimensions"]
    )
    return f"""당신은 사내 아이디어톤의 심사위원이며, 맡은 역할은 **{persona['name']}** 입니다.
관점: {persona['lens']}

심사 원칙:
- 엄격하고 비판적으로 평가한다. 근거 없는 후한 점수는 금지.
- 각 차원을 0~10 정수로 채점한다. 아래 점수 앵커를 반드시 준수:
{anchors}
- 신규 앱 아이디어임을 전제로 현실적으로 판단한다.
- 모호하거나 공란인 항목은 낮게 채점한다.
- 7점 이상은 명확한 근거가 있을 때만, 9~10은 드물게 부여한다.
- 당신의 페르소나({persona['name']}) 관점을 일관되게 유지한다.

평가 차원:
{dims}"""


def evaluate_persona(llm, rubric: dict, idea: Idea, persona: dict) -> PersonaScore:
    schema = build_persona_schema(rubric)
    system = persona_system(rubric, persona)
    user = (
        "다음 신규 앱 아이디어를 평가하라:\n\n"
        f"{idea.to_brief()}\n\n"
        "위 차원별로 채점하고 근거, 강점, 결함, 총평을 구조화해 제출하라."
    )
    out = llm.structured(
        system, user, schema, tool_name="persona_eval", temperature=0.2
    )
    raw_scores = out.get("scores", {})
    scores = {}
    for d in rubric["dimensions"]:
        k = d["key"]
        try:
            scores[k] = max(0.0, min(10.0, float(raw_scores.get(k, 0))))
        except (TypeError, ValueError):
            scores[k] = 0.0
    return PersonaScore(
        persona_key=persona["key"],
        persona_name=persona["name"],
        scores=scores,
        rationales=out.get("rationales", {}),
        strengths=list(out.get("strengths", [])),
        flaws=list(out.get("flaws", [])),
        overall_comment=out.get("overall_comment", ""),
    )


def aggregate(rubric: dict, persona_scores: List[PersonaScore]) -> Tuple[dict, float]:
    """페르소나 가중 → 차원별 집계(0..10), 차원 가중 → 패널 점수(0..100)."""
    dims = rubric["dimensions"]
    pweights = rubric["panel_weights"]
    dim_agg = {}
    for d in dims:
        k = d["key"]
        num = sum(
            ps.scores.get(k, 0.0) * pweights.get(ps.persona_key, 0.0)
            for ps in persona_scores
        )
        den = sum(pweights.get(ps.persona_key, 0.0) for ps in persona_scores) or 1.0
        dim_agg[k] = num / den
    panel100 = sum(dim_agg[d["key"]] * d["weight"] for d in dims) * 10.0
    return dim_agg, panel100


_FALLBACK_BAND = {"min": 0, "label": "REJECT — 탈락"}


def verdict_for(rubric: dict, score100: float) -> str:
    # 설정 오류(빈 밴드/오름차순 정렬)에도 안전하도록 방어: 항상 내림차순으로 첫 충족 밴드 사용
    bands = rubric.get("verdict_bands") or [_FALLBACK_BAND]
    for band in sorted(bands, key=lambda b: b["min"], reverse=True):
        if score100 >= band["min"]:
            return band["label"]
    return _FALLBACK_BAND["label"]


def _recommendation(verdict: str, fatal_flaws: List[str]) -> str:
    if verdict.startswith("STRONG PASS"):
        return "본선 진출 강력 추천. 데모/프로토타입 우선 투자 검토."
    if verdict.startswith("PASS"):
        return "본선 진출. 식별된 결함 보완 시 경쟁력 상승."
    if verdict.startswith("REVISE"):
        top = fatal_flaws[0] if fatal_flaws else "핵심 가정 검증 필요"
        return f"보완 후 재검토 권장. 최우선 보완: {top}"
    return "현 상태 탈락. 문제 정의·차별성·수요 근거의 근본적 재고 필요."


def judge_idea(
    llm,
    rubric: dict,
    idea: Idea,
    market: Optional[MarketReaction] = None,
    panel_keys: Optional[List[str]] = None,
) -> Judgment:
    panel = rubric["panel"]
    if panel_keys:
        panel = [p for p in panel if p["key"] in panel_keys]
    persona_scores = [evaluate_persona(llm, rubric, idea, p) for p in panel]
    dim_agg, panel100 = aggregate(rubric, persona_scores)

    blend = rubric.get("market_blend", 0.0)
    if market is not None and blend > 0:
        final = blend * market.demand_score + (1 - blend) * panel100
    else:
        final = panel100

    fatal = [f"[{ps.persona_name}] {f}" for ps in persona_scores for f in ps.flaws]
    strengths = [
        f"[{ps.persona_name}] {s}" for ps in persona_scores for s in ps.strengths
    ]
    verdict = verdict_for(rubric, final)
    return Judgment(
        idea=idea,
        persona_scores=persona_scores,
        dimension_scores=dim_agg,
        panel_score_100=panel100,
        market=market,
        final_score=final,
        verdict=verdict,
        fatal_flaws=fatal,
        key_strengths=strengths,
        recommendation=_recommendation(verdict, fatal),
        judged_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        model=getattr(llm, "model", "?"),
    )
