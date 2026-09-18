from __future__ import annotations

import unittest

from tests.fixture import make_site
from sitelib import Site, esc, page_path


class SiteTest(unittest.TestCase):
    def test_only_languages_with_ui_files_are_active(self):
        site = Site(make_site())
        self.assertEqual(site.lang_codes(), ["ko", "en"])

    def test_has_pages_requires_sections(self):
        site = Site(make_site(with_pages=False))
        self.assertIsNotNone(site.app_copy("demo", "ko"))
        self.assertFalse(site.has_pages("demo", "ko"))
        self.assertEqual(site.page_langs("demo"), [])

    def test_page_langs_for_hub_is_all_active(self):
        self.assertEqual(Site(make_site()).page_langs(None), ["ko", "en"])

    def test_facts_are_loaded(self):
        self.assertEqual(Site(make_site()).facts["demo"]["describesVersion"], "1.0.0")


class HelpersTest(unittest.TestCase):
    def test_page_path(self):
        self.assertEqual(page_path("ko"), "/ko/")
        self.assertEqual(page_path("ko", "demo"), "/ko/demo/")
        self.assertEqual(page_path("en", "demo", "support"), "/en/demo/support/")
        self.assertEqual(page_path("en", "demo", "privacy"), "/en/demo/privacy/")
        with self.assertRaises(ValueError):
            page_path("en", "demo", "blog")

    def test_esc(self):
        self.assertEqual(esc('<a href="x">'), "&lt;a href=&quot;x&quot;&gt;")


if __name__ == "__main__":
    unittest.main()
