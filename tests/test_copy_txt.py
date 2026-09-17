from __future__ import annotations

import json
import unittest

from tests.fixture import make_site
import copy_txt


class CopyTxtTest(unittest.TestCase):
    def setUp(self):
        self.root = make_site()

    def read(self, rel):
        return json.loads((self.root / rel).read_text(encoding="utf-8"))

    def test_export_lists_text_fields_with_keys(self):
        text = copy_txt.export(self.root, "ko")
        self.assertIn("[demo.subtitle] sub", text)
        self.assertIn("[demo.pro.title] first\\nsecond", text)
        self.assertIn("[demo.privacy.sections.9.pairs.0.value] kvndh36@naver.com", text)
        self.assertIn("[ui.navAbout] ko navAbout", text)
        self.assertNotIn(".layout]", text)
        self.assertNotIn(".glyph]", text)
        self.assertNotIn("privacy.effectiveDate]", text)
        self.assertIn("[ui.effectiveDate] ko effectiveDate", text)

    def test_round_trip_changes_nothing(self):
        before = self.read("content/apps/demo/ko.json")
        changed = copy_txt.apply(self.root, "ko", copy_txt.export(self.root, "ko"))
        self.assertEqual(changed, [])
        self.assertEqual(before, self.read("content/apps/demo/ko.json"))

    def test_edited_lines_are_written_back(self):
        text = copy_txt.export(self.root, "ko")
        text = text.replace("[demo.subtitle] sub", "[demo.subtitle] 새 부제")
        text = text.replace("[demo.pro.title] first\\nsecond", "[demo.pro.title] 한 줄\\n두 줄")
        text = text.replace("[ui.navAbout] ko navAbout", "[ui.navAbout] 소개")
        changed = copy_txt.apply(self.root, "ko", text)
        self.assertEqual(len(changed), 3)
        copy = self.read("content/apps/demo/ko.json")
        self.assertEqual(copy["subtitle"], "새 부제")
        self.assertEqual(copy["pro"]["title"], "한 줄\n두 줄")
        self.assertEqual(self.read("content/i18n/ko.json")["navAbout"], "소개")
        self.assertEqual(self.read("content/apps/demo/en.json")["subtitle"], "sub")

    def test_unknown_key_is_rejected(self):
        with self.assertRaises(KeyError):
            copy_txt.apply(self.root, "ko", "[demo.nothing] x\n")

    def test_missing_lines_leave_fields_alone(self):
        changed = copy_txt.apply(self.root, "ko", "[demo.summary] 요약만 바꿈\n")
        self.assertEqual(len(changed), 1)
        self.assertEqual(self.read("content/apps/demo/ko.json")["subtitle"], "sub")


if __name__ == "__main__":
    unittest.main()
