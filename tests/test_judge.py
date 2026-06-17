import unittest

from ideathon_judge import judge as J
from ideathon_judge.config import Config
from ideathon_judge.llm import MockLLM
from ideathon_judge.models import Idea, PersonaScore


def _idea() -> Idea:
    return Idea(
        row_index=1,
        timestamp="t",
        affiliation="팀",
        name="이름",
        service_name="서비스",
        problem="충분히 긴 문제 정의 텍스트입니다 정말로",
        target_user="20대 직장인",
        feature_1="자동화 기능",
        feature_2="요약",
        expected_effect="시간 절약",
    )


class TestAggregate(unittest.TestCase):
    def setUp(self):
        self.rubric = Config.load().rubric
        self.dims = [d["key"] for d in self.rubric["dimensions"]]

    def test_dimension_weights_sum_to_one(self):
        total = sum(d["weight"] for d in self.rubric["dimensions"])
        self.assertAlmostEqual(total, 1.0, places=6)

    def test_panel_weights_sum_to_one(self):
        total = sum(self.rubric["panel_weights"].values())
        self.assertAlmostEqual(total, 1.0, places=6)

    def test_all_tens_gives_100(self):
        pss = [
            PersonaScore(p["key"], p["name"], {k: 10.0 for k in self.dims}, {}, [], [], "")
            for p in self.rubric["panel"]
        ]
        dim_agg, panel100 = J.aggregate(self.rubric, pss)
        self.assertAlmostEqual(panel100, 100.0, places=4)
        for k in self.dims:
            self.assertAlmostEqual(dim_agg[k], 10.0, places=4)

    def test_all_zeros_gives_0(self):
        pss = [
            PersonaScore(p["key"], p["name"], {k: 0.0 for k in self.dims}, {}, [], [], "")
            for p in self.rubric["panel"]
        ]
        _, panel100 = J.aggregate(self.rubric, pss)
        self.assertAlmostEqual(panel100, 0.0, places=4)

    def test_verdict_bands(self):
        self.assertTrue(J.verdict_for(self.rubric, 95).startswith("STRONG PASS"))
        self.assertTrue(J.verdict_for(self.rubric, 70).startswith("PASS"))
        self.assertTrue(J.verdict_for(self.rubric, 55).startswith("REVISE"))
        self.assertTrue(J.verdict_for(self.rubric, 10).startswith("REJECT"))

    def test_verdict_for_empty_bands_does_not_crash(self):
        # 설정 오류(빈 밴드)에도 예외 없이 폴백
        self.assertTrue(J.verdict_for({"verdict_bands": []}, 90))
        self.assertTrue(J.verdict_for({}, 90))

    def test_verdict_for_unsorted_bands(self):
        # 밴드가 오름차순으로 잘못 정렬돼도 올바른 판정
        rubric = {
            "verdict_bands": [
                {"min": 0, "label": "LOW"},
                {"min": 80, "label": "HIGH"},
                {"min": 50, "label": "MID"},
            ]
        }
        self.assertEqual(J.verdict_for(rubric, 90), "HIGH")
        self.assertEqual(J.verdict_for(rubric, 60), "MID")
        self.assertEqual(J.verdict_for(rubric, 10), "LOW")


class TestJudgeEndToEndMock(unittest.TestCase):
    def test_mock_judge_idea(self):
        conf = Config.load()
        j = J.judge_idea(MockLLM(), conf.rubric, _idea(), market=None)
        self.assertTrue(0.0 <= j.final_score <= 100.0)
        self.assertEqual(len(j.persona_scores), len(conf.rubric["panel"]))
        self.assertTrue(j.verdict)
        self.assertTrue(j.recommendation)
        # 모든 차원이 채점되었는지
        for d in conf.rubric["dimensions"]:
            self.assertIn(d["key"], j.dimension_scores)


if __name__ == "__main__":
    unittest.main()
