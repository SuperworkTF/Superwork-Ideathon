"""시장반응 시뮬레이션 — 합성 타겟 페르소나 생성 + 반응 정량화.

MiroFish-Offline 검토 결론(과중한 Neo4j/Ollama 스택·점수 미산출·AGPL)에 따라
직접 구현한 경량 버전. 1회 LLM 호출로 N명 페르소나와 반응을 동시 생성 → 결정적 집계.
"""
from __future__ import annotations

from collections import Counter
from statistics import mean, median

from .models import Idea, MarketReaction


def build_sim_schema(n: int, scale: int) -> dict:
    persona_props = {
        "profile": {
            "type": "string",
            "description": "한 줄 페르소나 소개 (연령/성향/현재 쓰는 대안 포함)",
        },
        "adopt_probability": {
            "type": "number",
            "minimum": 0,
            "maximum": 1,
            "description": "무료라면 시도해볼 확률",
        },
        "pay_probability": {
            "type": "number",
            "minimum": 0,
            "maximum": 1,
            "description": "유료로 전환할 확률",
        },
        "willingness_to_pay": {
            "type": "integer",
            "minimum": 0,
            "maximum": 10000000,
            "description": "월 지불의향 (KRW, 0 가능)",
        },
        "excitement": {"type": "integer", "minimum": 0, "maximum": scale},
        "top_objection": {"type": "string", "description": "가장 큰 거부/이탈 이유 (구체적)"},
        "switching_barrier": {"type": "string", "enum": ["low", "med", "high"]},
    }
    return {
        "type": "object",
        "properties": {
            "personas": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": persona_props,
                    "required": list(persona_props),
                },
                "minItems": n,
                "maxItems": n,
            },
            "summary": {
                "type": "string",
                "description": "시장 반응 종합 2-3문장 (낙관·비관 균형)",
            },
        },
        "required": ["personas", "summary"],
    }


def simulate_market(llm, personas_cfg: dict, idea: Idea) -> MarketReaction:
    sim = personas_cfg["simulation"]
    n = int(sim["num_personas"])
    scale = int(sim["reaction_scale"])
    axes = "\n".join(f"  - {a}" for a in personas_cfg["diversity_axes"])
    schema = build_sim_schema(n, scale)

    system = (
        f"너는 시장조사 시뮬레이터다. 주어진 신규 앱 아이디어의 '타겟 유저'를 대표하는 "
        f"서로 다른 합성 소비자 {n}명을 생성하고, 각자가 이 앱에 보일 현실적 반응을 시뮬레이션한다.\n\n"
        "다양성 축 (반드시 분산 — 낙관 일색 금지, 회의적/비채택 후보 포함):\n"
        f"{axes}\n\n"
        "각 페르소나는 솔직하게 반응한다. 현재 쓰는 대안 대비 전환 이유가 약하면 "
        "낮은 채택확률·지불의향을 매긴다. 한국 시장의 가격 감각을 반영하라."
    )
    user = (
        "아이디어:\n\n"
        f"{idea.to_brief()}\n\n"
        f"이 아이디어에 대한 타겟 유저 {n}명의 반응을 시뮬레이션해 제출하라."
    )
    out = llm.structured(
        system,
        user,
        schema,
        tool_name="market_sim",
        temperature=float(sim["temperature"]),
        max_tokens=4096,
    )
    # 배열 원소가 dict 가 아닐 수 있는 비정상 응답 방어 (한 건이 통째로 죽지 않도록)
    ps = [p for p in out.get("personas", []) if isinstance(p, dict)]

    def _num(p, key, default=0.0):
        try:
            return float(p.get(key, default))
        except (TypeError, ValueError):
            return default

    adopt = [min(1.0, max(0.0, _num(p, "adopt_probability"))) for p in ps]
    pay = [min(1.0, max(0.0, _num(p, "pay_probability"))) for p in ps]
    exc = [min(float(scale), max(0.0, _num(p, "excitement"))) for p in ps]
    wtp = [min(10_000_000, max(0, int(_num(p, "willingness_to_pay")))) for p in ps]

    w = personas_cfg["demand_score_weights"]
    adopt_rate = mean(adopt) if adopt else 0.0
    pay_rate = mean(pay) if pay else 0.0
    exc_rate = (mean(exc) / scale) if exc else 0.0
    demand = 100.0 * (
        w["adopt_rate"] * adopt_rate
        + w["pay_rate"] * pay_rate
        + w["excitement"] * exc_rate
    )

    objections = Counter(
        p.get("top_objection", "").strip() for p in ps if p.get("top_objection")
    )
    return MarketReaction(
        num_personas=len(ps),
        adopt_rate=adopt_rate,
        pay_rate=pay_rate,
        avg_excitement=mean(exc) if exc else 0.0,
        median_wtp=int(median(wtp)) if wtp else 0,
        demand_score=demand,
        top_objections=[list(x) for x in objections.most_common(5)],
        persona_samples=ps,
        summary=out.get("summary", ""),
    )
