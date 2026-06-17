"""LLM 래퍼 — Anthropic 강제 tool-use 기반 구조화 JSON 출력 + 재시도.

MockLLM: API 키 없이 파이프라인 전체를 검증(dry-run)하기 위한 결정적 가짜 출력기.
스키마를 introspect 해 어떤 요청 스키마든 형태에 맞는 값을 채운다.
"""
from __future__ import annotations

import hashlib
import json
import random
import shutil
import subprocess
import time
from typing import Any


class LLMError(RuntimeError):
    pass


class LLM:
    """Anthropic 클라이언트 — tool_choice 강제로 구조화 JSON을 안정적으로 받음."""

    def __init__(self, api_key: str, model: str, max_retries: int = 3):
        try:
            import anthropic  # 지연 임포트 (미설치 환경에서도 mock 사용 가능)
        except ImportError as e:  # pragma: no cover
            raise LLMError(
                "anthropic 패키지 미설치. `pip install -r requirements.txt` 후 재시도."
            ) from e
        if not api_key:
            raise LLMError("ANTHROPIC_API_KEY 미설정. .env 에 키를 넣거나 --dry-run 사용.")
        self._client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.max_retries = max_retries

    def structured(
        self,
        system: str,
        user: str,
        schema: dict,
        tool_name: str = "emit",
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> dict:
        tools = [
            {
                "name": tool_name,
                "description": "분석 결과를 구조화된 JSON으로 반환한다.",
                "input_schema": schema,
            }
        ]
        last_err: Any = None
        for attempt in range(self.max_retries):
            try:
                resp = self._client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system,
                    tools=tools,
                    tool_choice={"type": "tool", "name": tool_name},
                    messages=[{"role": "user", "content": user}],
                )
                for block in resp.content:
                    if getattr(block, "type", None) == "tool_use":
                        return dict(block.input)
                raise LLMError("응답에 tool_use 블록이 없음")
            except Exception as e:  # noqa: BLE001 — 전송/모델 오류 재시도
                last_err = e
                status = getattr(e, "status_code", None)
                # 4xx(잘못된 요청/인증/모델 없음)는 재시도 무의미 — 429(rate limit)만 예외
                if isinstance(status, int) and 400 <= status < 500 and status != 429:
                    break
                if attempt < self.max_retries - 1:
                    time.sleep(min(8.0, 2**attempt) + random.uniform(0, 0.5))
        raise LLMError(f"LLM 호출 실패 ({self.max_retries}회 시도): {last_err}")


class MockLLM:
    """API 키 없이 파이프라인을 검증하는 결정적 가짜 LLM.

    user 텍스트 해시로 점수를 변주해 아이디어별로 다른(그러나 재현가능한) 결과 생성.
    """

    def __init__(self, model: str = "mock", **_: Any):
        self.model = model

    def structured(
        self,
        system: str,
        user: str,
        schema: dict,
        tool_name: str = "emit",
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> dict:
        seed = int(hashlib.sha1(user.encode("utf-8")).hexdigest(), 16)
        return self._fill(schema, seed, depth=0)

    # 스키마 기반 결정적 채움
    def _fill(self, schema: dict, seed: int, depth: int) -> Any:
        t = schema.get("type")
        if t == "object":
            props = schema.get("properties", {})
            out = {}
            for i, (key, sub) in enumerate(props.items()):
                out[key] = self._fill(sub, seed * 31 + i * 7 + depth, depth + 1)
            return out
        if t == "array":
            items = schema.get("items", {"type": "string"})
            n = schema.get("minItems", 3)
            return [self._fill(items, seed * 17 + j * 13, depth + 1) for j in range(n)]
        if t in ("integer", "number"):
            lo = schema.get("minimum", 0)
            hi = schema.get("maximum", 10)
            span = max(hi - lo, 1)
            val = lo + (seed % (int(span * 100) + 1)) / 100.0
            if t == "integer":
                return int(round(val))
            return round(val, 2)
        if t == "string":
            enum = schema.get("enum")
            if enum:
                return enum[seed % len(enum)]
            desc = schema.get("description", "항목")
            return f"[mock] {desc[:40]}"
        if t == "boolean":
            return bool(seed % 2)
        return None


def _extract_json(text: str) -> dict:
    """모델 텍스트에서 JSON 객체 추출 (마크다운 펜스/잡텍스트 허용)."""
    s = (text or "").strip()
    start, end = s.find("{"), s.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise LLMError(f"응답에서 JSON 객체를 찾지 못함: {s[:120]!r}")
    blob = s[start : end + 1]
    try:
        out = json.loads(blob)
    except json.JSONDecodeError as e:
        raise LLMError(f"JSON 파싱 실패: {e}: {blob[:120]!r}") from e
    if not isinstance(out, dict):
        raise LLMError(f"JSON 최상위가 객체가 아님: {type(out).__name__}")
    return out


class ClaudeCLI:
    """claude CLI 헤드리스(-p) 백엔드 — ANTHROPIC_API_KEY 없이 Claude 구독을 공유 사용.

    `claude -p --output-format json` 의 result(모델 텍스트)에서 JSON 을 추출.
    structured() 시그니처는 LLM 과 동일(교체 가능). temperature/max_tokens 는 CLI 가
    노출하지 않아 무시됨(스키마+프롬프트로 제어).
    """

    def __init__(
        self,
        model: str,
        bin: str = "claude",
        max_retries: int = 3,
        timeout: int = 180,
    ):
        resolved = shutil.which(bin)
        if not resolved:
            raise LLMError(
                f"claude CLI 미발견('{bin}'). Claude Code 설치 및 로그인 상태를 확인하거나 "
                "ANTHROPIC_API_KEY 를 설정하세요."
            )
        self._bin = resolved
        self.model = model
        self.max_retries = max_retries
        self.timeout = timeout

    @staticmethod
    def _cli_model(model: str) -> str:
        """API 스타일 모델 id → CLI 별칭 정규화 (full id 는 통과)."""
        m = (model or "").lower()
        if m.startswith("claude-opus") or m == "opus":
            return "opus"
        if m.startswith("claude-sonnet") or m == "sonnet":
            return "sonnet"
        if m.startswith("claude-haiku") or m == "haiku":
            return "haiku"
        return model

    def structured(
        self,
        system: str,
        user: str,
        schema: dict,
        tool_name: str = "emit",
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> dict:
        prompt = (
            f"{system}\n\n{user}\n\n"
            "아래 JSON 스키마에 정확히 맞는 JSON 객체만 출력하라. "
            "마크다운 코드펜스/설명/서론 없이 순수 JSON 만 출력:\n"
            f"{json.dumps(schema, ensure_ascii=False)}"
        )
        cmd = [
            self._bin,
            "-p",
            "--output-format",
            "json",
            "--model",
            self._cli_model(self.model),
            "--max-turns",
            "1",
        ]
        last_err: Any = None
        for attempt in range(self.max_retries):
            try:
                proc = subprocess.run(
                    cmd,
                    input=prompt,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                )
                if proc.returncode != 0:
                    raise LLMError(
                        f"claude CLI 종료코드 {proc.returncode}: {(proc.stderr or '')[:200]}"
                    )
                env = json.loads(proc.stdout)
                if env.get("is_error") or env.get("subtype") != "success":
                    raise LLMError(
                        f"claude CLI 응답 오류: subtype={env.get('subtype')} "
                        f"{str(env.get('result', ''))[:200]}"
                    )
                return _extract_json(env.get("result", ""))
            except Exception as e:  # noqa: BLE001 — 호출/파싱 오류 재시도
                last_err = e
                if attempt < self.max_retries - 1:
                    time.sleep(min(8.0, 2**attempt) + random.uniform(0, 0.5))
        raise LLMError(f"claude CLI 호출 실패 ({self.max_retries}회 시도): {last_err}")
