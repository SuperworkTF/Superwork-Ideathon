"""실제 LLM.structured 의 tool_use 파싱 + 재시도 경로 검증 (API 키 불필요).

Anthropic SDK 응답 구조(content=[tool_use block])를 모사한 가짜 클라이언트로
네트워크 없이 파싱·재시도 로직만 단위 검증한다.
"""
import json
import unittest
from unittest import mock

from ideathon_judge.llm import LLM, ClaudeCLI, LLMError, MockLLM, _extract_json


class _Block:
    def __init__(self, type_, input_=None):
        self.type = type_
        self.input = input_ or {}


class _Resp:
    def __init__(self, blocks):
        self.content = blocks


class _Messages:
    def __init__(self, behavior):
        self._behavior = behavior
        self.calls = 0

    def create(self, **kwargs):
        self.calls += 1
        return self._behavior(self.calls, kwargs)


class _Client:
    def __init__(self, behavior):
        self.messages = _Messages(behavior)


def _make_llm(behavior) -> LLM:
    # __init__ 우회(anthropic 실제 생성 회피) 후 가짜 클라이언트 주입
    llm = LLM.__new__(LLM)
    llm._client = _Client(behavior)
    llm.model = "fake"
    llm.max_retries = 3
    return llm


class TestLLMStructured(unittest.TestCase):
    def setUp(self):
        # 재시도 백오프 sleep 무력화 → 테스트 고속화
        self._sleep = mock.patch("ideathon_judge.llm.time.sleep", lambda *_: None)
        self._sleep.start()

    def tearDown(self):
        self._sleep.stop()

    def test_parses_tool_use_input(self):
        llm = _make_llm(lambda n, kw: _Resp([_Block("tool_use", {"score": 7})]))
        out = llm.structured("sys", "user", {"type": "object"}, tool_name="t")
        self.assertEqual(out, {"score": 7})

    def test_retries_then_succeeds(self):
        def behavior(n, kw):
            if n == 1:
                raise RuntimeError("일시적 오류")
            return _Resp([_Block("tool_use", {"ok": True})])

        llm = _make_llm(behavior)
        out = llm.structured("s", "u", {"type": "object"})
        self.assertEqual(out, {"ok": True})
        self.assertEqual(llm._client.messages.calls, 2)

    def test_raises_after_max_retries(self):
        llm = _make_llm(lambda n, kw: (_ for _ in ()).throw(RuntimeError("계속 실패")))
        with self.assertRaises(LLMError):
            llm.structured("s", "u", {"type": "object"})

    def test_missing_tool_use_block_raises(self):
        llm = _make_llm(lambda n, kw: _Resp([_Block("text", None)]))
        with self.assertRaises(LLMError):
            llm.structured("s", "u", {"type": "object"})

    def test_forces_tool_choice(self):
        captured = {}

        def behavior(n, kw):
            captured.update(kw)
            return _Resp([_Block("tool_use", {"x": 1})])

        llm = _make_llm(behavior)
        llm.structured("s", "u", {"type": "object"}, tool_name="persona_eval")
        self.assertEqual(captured["tool_choice"], {"type": "tool", "name": "persona_eval"})
        self.assertEqual(captured["tools"][0]["name"], "persona_eval")


class TestLLMNoKey(unittest.TestCase):
    def test_missing_key_raises(self):
        with self.assertRaises(LLMError):
            LLM(api_key="", model="x")


class _Proc:
    def __init__(self, stdout, returncode=0, stderr=""):
        self.stdout = stdout
        self.returncode = returncode
        self.stderr = stderr


def _env(result, is_error=False, subtype="success"):
    return json.dumps({"is_error": is_error, "subtype": subtype, "result": result})


class TestExtractJson(unittest.TestCase):
    def test_bare(self):
        self.assertEqual(_extract_json('{"a": 1}'), {"a": 1})

    def test_markdown_fenced(self):
        self.assertEqual(_extract_json('```json\n{"a": 1}\n```'), {"a": 1})

    def test_prose_wrapped(self):
        self.assertEqual(_extract_json('결과는 다음과 같다: {"a": 1} 끝.'), {"a": 1})

    def test_no_json_raises(self):
        with self.assertRaises(LLMError):
            _extract_json("여기에 JSON 없음")

    def test_top_level_array_raises(self):
        with self.assertRaises(LLMError):
            _extract_json("[1, 2, 3]")


class TestClaudeCLI(unittest.TestCase):
    def setUp(self):
        self._which = mock.patch(
            "ideathon_judge.llm.shutil.which", return_value="/usr/bin/claude"
        )
        self._which.start()
        self._sleep = mock.patch("ideathon_judge.llm.time.sleep", lambda *_: None)
        self._sleep.start()

    def tearDown(self):
        self._which.stop()
        self._sleep.stop()

    def _cli(self):
        return ClaudeCLI(model="claude-opus-4-8")

    def test_model_alias_normalization(self):
        self.assertEqual(ClaudeCLI._cli_model("claude-opus-4-8"), "opus")
        self.assertEqual(ClaudeCLI._cli_model("claude-sonnet-4-6"), "sonnet")
        self.assertEqual(ClaudeCLI._cli_model("claude-haiku-4-5"), "haiku")
        self.assertEqual(ClaudeCLI._cli_model("custom-model"), "custom-model")

    def test_success_parses_result(self):
        with mock.patch(
            "ideathon_judge.llm.subprocess.run", return_value=_Proc(_env('{"score": 7}'))
        ):
            out = self._cli().structured("s", "u", {"type": "object"})
        self.assertEqual(out, {"score": 7})

    def test_fenced_result_extracted(self):
        with mock.patch(
            "ideathon_judge.llm.subprocess.run",
            return_value=_Proc(_env('```json\n{"x": 1}\n```')),
        ):
            out = self._cli().structured("s", "u", {"type": "object"})
        self.assertEqual(out, {"x": 1})

    def test_is_error_envelope_raises(self):
        with mock.patch(
            "ideathon_judge.llm.subprocess.run",
            return_value=_Proc(_env("oops", is_error=True)),
        ):
            with self.assertRaises(LLMError):
                self._cli().structured("s", "u", {"type": "object"})

    def test_nonzero_returncode_raises(self):
        with mock.patch(
            "ideathon_judge.llm.subprocess.run",
            return_value=_Proc("", returncode=1, stderr="boom"),
        ):
            with self.assertRaises(LLMError):
                self._cli().structured("s", "u", {"type": "object"})

    def test_missing_binary_raises(self):
        with mock.patch("ideathon_judge.llm.shutil.which", return_value=None):
            with self.assertRaises(LLMError):
                ClaudeCLI(model="x")


class TestMockSchemaFill(unittest.TestCase):
    def test_respects_enum_and_bounds(self):
        schema = {
            "type": "object",
            "properties": {
                "barrier": {"type": "string", "enum": ["low", "med", "high"]},
                "score": {"type": "integer", "minimum": 0, "maximum": 10},
                "ratio": {"type": "number", "minimum": 0, "maximum": 1},
                "items": {"type": "array", "items": {"type": "string"}, "minItems": 2},
            },
        }
        out = MockLLM().structured("s", "u", schema)
        self.assertIn(out["barrier"], ["low", "med", "high"])
        self.assertTrue(0 <= out["score"] <= 10)
        self.assertTrue(0 <= out["ratio"] <= 1)
        self.assertEqual(len(out["items"]), 2)


if __name__ == "__main__":
    unittest.main()
