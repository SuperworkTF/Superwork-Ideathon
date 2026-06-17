import unittest

from ideathon_judge.models import Idea


def mk(**kw) -> Idea:
    base = dict(
        row_index=1,
        timestamp="2026-06-17 10:00",
        affiliation="팀A",
        name="홍길동",
        service_name="테스트앱",
        problem="사용자가 X를 못해서 매일 시간을 낭비한다",
        target_user="20대 직장인",
        feature_1="자동화 기능",
        feature_2="",
        expected_effect="시간 절약",
    )
    base.update(kw)
    return Idea(**base)


class TestIdea(unittest.TestCase):
    def test_id_stable_and_len(self):
        self.assertEqual(mk().idea_id, mk().idea_id)
        self.assertEqual(len(mk().idea_id), 12)

    def test_id_stable_across_content_edits(self):
        # 내용(문제/서비스명) 수정해도 ID 불변 → 재심사/중복 리포트 방지
        self.assertEqual(
            mk().idea_id,
            mk(problem="완전히 다른 문제 정의 텍스트입니다", service_name="새이름").idea_id,
        )

    def test_id_changes_with_submitter_identity(self):
        # 제출 정체성(시각/소속/성명) 변경 시 ID 변경
        self.assertNotEqual(mk().idea_id, mk(name="다른사람").idea_id)
        self.assertNotEqual(mk().idea_id, mk(timestamp="2026-06-18 09:00").idea_id)

    def test_substantive_true(self):
        self.assertTrue(mk().is_substantive)

    def test_not_substantive_when_empty(self):
        self.assertFalse(
            mk(service_name="", problem="", target_user="", feature_1="").is_substantive
        )

    def test_not_substantive_when_problem_is_filler_token(self):
        # 길이는 충분하지만 problem 이 무의미 토큰이면 탈락
        idea = mk(
            problem="없음",
            service_name="긴서비스이름입니다요",
            target_user="타겟유저군집단입니다",
            feature_1="핵심기능설명입니다",
        )
        self.assertFalse(idea.is_substantive)

    def test_brief_contains_fields(self):
        b = mk().to_brief()
        self.assertIn("테스트앱", b)
        self.assertIn("20대 직장인", b)

    def test_to_dict_has_id_and_no_raw(self):
        d = mk().to_dict()
        self.assertIn("idea_id", d)
        self.assertNotIn("raw", d)


if __name__ == "__main__":
    unittest.main()
