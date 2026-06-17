import unittest

from ideathon_judge.sheet import parse_ideas

CSV = (
    "타임스탬프,소속,성명,서비스명,해결할 문제,타겟 유저,핵심기능1,핵심기능2,기대효과\n"
    "2026-06-17 10:00,팀A,홍길동,앱이름,문제 정의입니다,20대,기능1,기능2,효과\n"
)


class TestSheet(unittest.TestCase):
    def test_parse_single_row(self):
        ideas = parse_ideas(CSV)
        self.assertEqual(len(ideas), 1)
        i = ideas[0]
        self.assertEqual(i.service_name, "앱이름")
        self.assertEqual(i.affiliation, "팀A")
        self.assertEqual(i.feature_1, "기능1")
        self.assertEqual(i.row_index, 1)

    def test_skip_fully_blank_row(self):
        ideas = parse_ideas(CSV + ",,,,,,,,\n")
        self.assertEqual(len(ideas), 1)

    def test_short_row_padded(self):
        # 누락 컬럼이 있어도 패딩되어 파싱
        ideas = parse_ideas("h1,h2,h3\n2026,팀,이름\n")
        self.assertEqual(len(ideas), 1)
        self.assertEqual(ideas[0].name, "이름")
        self.assertEqual(ideas[0].service_name, "")

    def test_empty_input(self):
        self.assertEqual(parse_ideas(""), [])


if __name__ == "__main__":
    unittest.main()
