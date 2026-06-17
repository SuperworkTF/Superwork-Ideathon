"""구글폼 연동 시트 CSV 수집·파싱.

헤더가 멀티라인·특수문자(▎)라 위치 기반 매핑이 가장 안정적.
구글폼 컬럼 순서는 고정이므로 0..8 위치로 매핑하고 원본 헤더는 raw에 보존.
"""
from __future__ import annotations

import csv
import io
import sys
import urllib.request
from typing import List
from urllib.parse import urlparse

from .models import Idea

# 구글폼 고정 컬럼 순서
COLS = [
    "timestamp",
    "affiliation",
    "name",
    "service_name",
    "problem",
    "target_user",
    "feature_1",
    "feature_2",
    "expected_effect",
]


def fetch_csv(url: str, timeout: int = 30) -> str:
    scheme = urlparse(url).scheme.lower()
    if scheme not in ("http", "https"):  # file:// 등 차단 (로컬파일/메타데이터 SSRF 방지)
        raise RuntimeError(f"허용되지 않은 URL 스킴: {scheme or '(없음)'!r}. http/https만 허용.")
    req = urllib.request.Request(url, headers={"User-Agent": "ideathon-judge/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (운영자 신뢰 URL)
        text = resp.read().decode("utf-8-sig")
    # 공유 설정이 바뀌면 구글이 CSV 대신 로그인/에러 HTML을 돌려줌 → 조기 차단
    head = text.lstrip()[:200].lower()
    if head.startswith("<!doctype") or head.startswith("<html"):
        raise RuntimeError(
            "시트가 CSV 대신 HTML을 반환했습니다. 시트 공유를 '링크가 있는 모든 사용자=뷰어'로 "
            "설정했는지, SHEET_CSV_URL(gid 포함 export 링크)이 올바른지 확인하세요."
        )
    return text


def parse_ideas(csv_text: str) -> List[Idea]:
    reader = csv.reader(io.StringIO(csv_text))
    rows = list(reader)
    if len(rows) < 1:
        return []
    header = rows[0]
    # 폼 구조 변경 조기 감지 — 위치 기반 매핑이 조용히 어긋나는 것 방지(경고만, 파싱은 계속)
    if len(header) < len(COLS):
        print(
            f"[경고] 시트 컬럼 {len(header)}개 < 예상 {len(COLS)}개 — 폼 구조 변경 가능성. 매핑 확인 필요.",
            file=sys.stderr,
        )
    elif header and "타임스탬프" not in header[0] and "timestamp" not in header[0].lower():
        print(
            "[경고] 첫 컬럼이 타임스탬프가 아님 — 컬럼 순서/매핑(COLS)을 확인하세요.",
            file=sys.stderr,
        )
    ideas: List[Idea] = []
    for i, row in enumerate(rows[1:], start=1):
        vals = (row + [""] * len(COLS))[: len(COLS)]
        rec = dict(zip(COLS, (v.strip() for v in vals)))
        if not any(rec.values()):  # 완전 공백 행 스킵
            continue
        ideas.append(Idea(row_index=i, raw=dict(zip(header, row)), **rec))
    return ideas


def load_ideas(url: str) -> List[Idea]:
    return parse_ideas(fetch_csv(url))
