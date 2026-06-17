"""데이터 모델 — 아이디어, 페르소나 점수, 시장반응, 최종 판정."""
from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass, field
from typing import Optional

# 공란/무의미 제출 감지용 토큰
_EMPTY_TOKENS = {"", "-", "n/a", "na", "없음", ".", "test", "테스트", "tbd", "미정"}


@dataclass
class Idea:
    """구글폼 1개 제출 행."""

    row_index: int  # 헤더 제외 1-based 데이터 행 번호
    timestamp: str
    affiliation: str
    name: str
    service_name: str
    problem: str
    target_user: str
    feature_1: str
    feature_2: str
    expected_effect: str
    raw: dict = field(default_factory=dict)

    @property
    def idea_id(self) -> str:
        """제출 식별자 기반 안정적 12자 해시 (배치 중복심사 방지 키).

        제출 정체성(제출시각+소속+성명)으로 해시 → 제안자가 내용(문제/기능)을 수정해도
        ID 가 바뀌지 않아 재심사·중복 리포트가 발생하지 않음.
        (수정분 재심사가 필요하면 `run --force`.)
        """
        basis = "|".join([self.timestamp, self.affiliation, self.name]).strip()
        if not basis.strip("|"):  # 식별 필드가 모두 비면 내용으로 폴백
            basis = (self.service_name + self.problem)[:120]
        return hashlib.sha1(basis.encode("utf-8")).hexdigest()[:12]

    @property
    def is_substantive(self) -> bool:
        """심사 가치가 있는 실질 제출인지 (공란/스팸 필터). 유료 LLM 낭비 방지."""
        # 필수 필드가 비었거나 무의미 토큰이면 탈락
        if self.problem.strip().lower() in _EMPTY_TOKENS:
            return False
        if self.service_name.strip().lower() in _EMPTY_TOKENS:
            return False
        if len(self.problem.strip()) < 10:  # 문제 정의가 너무 짧으면 탈락
            return False
        core = re.sub(
            r"\s+",
            " ",
            " ".join([self.service_name, self.problem, self.target_user, self.feature_1]),
        ).strip()
        if len(core) < 20:
            return False
        if len([t for t in core.split(" ") if len(t) >= 2]) < 4:  # 최소 의미 토큰 수
            return False
        return True

    def to_brief(self) -> str:
        """LLM 프롬프트용 정형 텍스트."""
        return (
            f"[서비스명] {self.service_name or '(미기재)'}\n"
            f"[해결할 문제] {self.problem or '(미기재)'}\n"
            f"[타겟 유저] {self.target_user or '(미기재)'}\n"
            f"[핵심기능1] {self.feature_1 or '(미기재)'}\n"
            f"[핵심기능2] {self.feature_2 or '(미기재)'}\n"
            f"[기대효과] {self.expected_effect or '(미기재)'}\n"
            f"[제안자] {self.name or '(익명)'} / {self.affiliation or '(소속미상)'}"
        )

    def to_dict(self) -> dict:
        d = asdict(self)
        d.pop("raw", None)
        d["idea_id"] = self.idea_id
        return d


@dataclass
class PersonaScore:
    """1명 심사 페르소나의 채점 결과."""

    persona_key: str
    persona_name: str
    scores: dict  # dim_key -> 0..10
    rationales: dict  # dim_key -> str
    strengths: list
    flaws: list
    overall_comment: str


@dataclass
class MarketReaction:
    """시장반응 시뮬레이션 집계."""

    num_personas: int
    adopt_rate: float  # 평균 시도확률 0..1
    pay_rate: float  # 평균 유료전환확률 0..1
    avg_excitement: float  # 0..10
    median_wtp: int  # 월 지불의향 중앙값 KRW
    demand_score: float  # 0..100
    top_objections: list  # [[objection, count], ...]
    persona_samples: list  # 원시 반응 리스트
    summary: str


@dataclass
class Judgment:
    """1개 아이디어 최종 심사 결과."""

    idea: Idea
    persona_scores: list  # list[PersonaScore]
    dimension_scores: dict  # dim_key -> 집계 0..10
    panel_score_100: float
    market: Optional[MarketReaction]
    final_score: float  # 0..100
    verdict: str
    fatal_flaws: list
    key_strengths: list
    recommendation: str
    judged_at: str
    model: str
