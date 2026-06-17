import tempfile
import unittest
from pathlib import Path

from ideathon_judge.state import State


class TestState(unittest.TestCase):
    def test_roundtrip_and_idempotency(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "state.json"
            s = State(p)
            self.assertFalse(s.is_judged("abc"))
            s.mark("abc", {"final_score": 50})
            s.save()
            s2 = State(p)
            self.assertTrue(s2.is_judged("abc"))
            self.assertEqual(s2.data["abc"]["final_score"], 50)

    def test_corrupt_file_is_tolerated(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "state.json"
            p.write_text("{not valid json", encoding="utf-8")
            s = State(p)  # 예외 없이 빈 상태로 시작
            self.assertEqual(s.data, {})


if __name__ == "__main__":
    unittest.main()
