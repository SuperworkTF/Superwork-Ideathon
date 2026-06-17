import tempfile
import unittest
from pathlib import Path

from ideathon_judge import config as cfg
from ideathon_judge import pipeline
from ideathon_judge.config import Config
from ideathon_judge.llm import MockLLM
from ideathon_judge.market_sim import simulate_market
from ideathon_judge.models import Idea


def _idea(i=1, name="박", svc="서비스A") -> Idea:
    return Idea(
        row_index=i,
        timestamp="t",
        affiliation="팀",
        name=name,
        service_name=svc,
        problem="충분히 긴 문제 정의 텍스트입니다 정말로 길게",
        target_user="20대 직장인",
        feature_1="자동화 기능",
        feature_2="요약",
        expected_effect="시간 절약",
    )


class TestMarketSim(unittest.TestCase):
    def test_mock_sim_aggregates(self):
        conf = Config.load()
        m = simulate_market(MockLLM(), conf.personas, _idea())
        self.assertEqual(m.num_personas, conf.personas["simulation"]["num_personas"])
        self.assertTrue(0.0 <= m.demand_score <= 100.0)
        self.assertTrue(0.0 <= m.adopt_rate <= 1.0)
        self.assertTrue(0.0 <= m.pay_rate <= 1.0)


class TestPipelineDryRun(unittest.TestCase):
    def test_dry_run_and_idempotency(self):
        ideas = [_idea(1, "박", "서비스A"), _idea(2, "김", "서비스B")]
        saved = dict(
            STATE_PATH=cfg.STATE_PATH,
            REPORTS_DIR=cfg.REPORTS_DIR,
            SCORES_CSV=cfg.SCORES_CSV,
            SCORES_JSON=cfg.SCORES_JSON,
            LEADERBOARD=cfg.LEADERBOARD,
            load_ideas=pipeline.load_ideas,
        )
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            cfg.STATE_PATH = d / "state.json"
            cfg.REPORTS_DIR = d / "reports"
            cfg.SCORES_CSV = d / "scores.csv"
            cfg.SCORES_JSON = d / "scores.json"
            cfg.LEADERBOARD = d / "lb.md"
            pipeline.load_ideas = lambda url: ideas
            try:
                res = pipeline.run(dry_run=True, verbose=False)
                self.assertEqual(res.new_judged, 2)
                self.assertTrue((d / "scores.json").exists())
                self.assertTrue((d / "lb.md").exists())
                reports = list((d / "reports").glob("*.md"))
                self.assertEqual(len(reports), 2)

                # 2nd run → 모두 스킵 (멱등성)
                res2 = pipeline.run(dry_run=True, verbose=False)
                self.assertEqual(res2.new_judged, 0)
                self.assertEqual(res2.skipped_existing, 2)
            finally:
                cfg.STATE_PATH = saved["STATE_PATH"]
                cfg.REPORTS_DIR = saved["REPORTS_DIR"]
                cfg.SCORES_CSV = saved["SCORES_CSV"]
                cfg.SCORES_JSON = saved["SCORES_JSON"]
                cfg.LEADERBOARD = saved["LEADERBOARD"]
                pipeline.load_ideas = saved["load_ideas"]


class TestBackendResolution(unittest.TestCase):
    def _conf(self, api_key=None, backend="auto"):
        c = Config.load()
        c.api_key = api_key
        c.backend = backend
        return c

    def test_auto_with_key_uses_api(self):
        self.assertEqual(pipeline.resolve_backend(self._conf("sk-x", "auto"), False), "api")

    def test_auto_without_key_uses_cli_subscription(self):
        self.assertEqual(pipeline.resolve_backend(self._conf(None, "auto"), False), "cli")

    def test_dry_run_forces_mock(self):
        self.assertEqual(pipeline.resolve_backend(self._conf("sk-x", "auto"), True), "mock")

    def test_explicit_cli_override(self):
        self.assertEqual(pipeline.resolve_backend(self._conf("sk-x", "cli"), False), "cli")


class TestPipelineCumulative(unittest.TestCase):
    def test_outputs_accumulate_across_runs(self):
        import json

        batch1 = [_idea(1, "a", "S1"), _idea(2, "b", "S2")]
        batch2 = batch1 + [_idea(3, "c", "S3")]  # 2차에 새 1건 추가
        saved_load = pipeline.load_ideas
        saved_paths = (
            cfg.STATE_PATH,
            cfg.REPORTS_DIR,
            cfg.SCORES_CSV,
            cfg.SCORES_JSON,
            cfg.LEADERBOARD,
        )
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            cfg.STATE_PATH = d / "state.json"
            cfg.REPORTS_DIR = d / "r"
            cfg.SCORES_CSV = d / "s.csv"
            cfg.SCORES_JSON = d / "s.json"
            cfg.LEADERBOARD = d / "lb.md"
            try:
                pipeline.load_ideas = lambda url: batch1
                pipeline.run(dry_run=True, verbose=False)
                pipeline.load_ideas = lambda url: batch2
                res2 = pipeline.run(dry_run=True, verbose=False)
                self.assertEqual(res2.new_judged, 1)  # 새 1건만 심사
                data = json.loads(cfg.SCORES_JSON.read_text(encoding="utf-8"))
                self.assertEqual(len(data), 3)  # 누적 3건 (덮어쓰기 아님)
            finally:
                pipeline.load_ideas = saved_load
                (
                    cfg.STATE_PATH,
                    cfg.REPORTS_DIR,
                    cfg.SCORES_CSV,
                    cfg.SCORES_JSON,
                    cfg.LEADERBOARD,
                ) = saved_paths


class TestPipelineFailureIsolation(unittest.TestCase):
    def test_one_failing_idea_does_not_abort_batch(self):
        ideas = [_idea(1, "a", "S1"), _idea(2, "b", "S2"), _idea(3, "c", "S3")]
        saved_sim = pipeline.simulate_market
        saved_load = pipeline.load_ideas
        saved_paths = (
            cfg.STATE_PATH,
            cfg.REPORTS_DIR,
            cfg.SCORES_CSV,
            cfg.SCORES_JSON,
            cfg.LEADERBOARD,
        )

        def boom(llm, cfg_p, idea):
            if idea.row_index == 2:
                raise RuntimeError("의도적 실패")
            return saved_sim(llm, cfg_p, idea)

        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            cfg.STATE_PATH = d / "s.json"
            cfg.REPORTS_DIR = d / "r"
            cfg.SCORES_CSV = d / "s.csv"
            cfg.SCORES_JSON = d / "s2.json"
            cfg.LEADERBOARD = d / "lb.md"
            pipeline.simulate_market = boom
            pipeline.load_ideas = lambda url: ideas
            try:
                res = pipeline.run(dry_run=True, verbose=False)
                self.assertEqual(res.new_judged, 2)
                self.assertEqual(res.failed, 1)
            finally:
                pipeline.simulate_market = saved_sim
                pipeline.load_ideas = saved_load
                (
                    cfg.STATE_PATH,
                    cfg.REPORTS_DIR,
                    cfg.SCORES_CSV,
                    cfg.SCORES_JSON,
                    cfg.LEADERBOARD,
                ) = saved_paths


if __name__ == "__main__":
    unittest.main()
