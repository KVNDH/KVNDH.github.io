from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from tests.fixture import REPO, make_site
import build
from sitelib import Site


class BuildTest(unittest.TestCase):
    def test_build_writes_pages_static_assets_and_sitemap(self):
        root = make_site()
        out = root / "docs"
        written = build.build(Site(root), out)
        for rel in ("index.html", "404.html", "ko/index.html", "en/demo/index.html",
                    "en/demo/support/index.html", "ko/demo/privacy/index.html", "CNAME",
                    "app-ads.txt", ".nojekyll", "robots.txt", "sitemap.xml",
                    "assets/demo/icon-180.webp", "assets/og.jpg"):
            self.assertTrue((out / rel).exists(), rel)
        self.assertIn("/ko/demo/privacy/", written)
        sitemap = (out / "sitemap.xml").read_text()
        self.assertIn("<loc>https://kvndh.com/en/demo/</loc>", sitemap)
        self.assertNotIn("404", sitemap)

    def test_build_is_deterministic_and_clears_old_output(self):
        root = make_site()
        out = root / "docs"
        out.mkdir()
        (out / "stale.html").write_text("old")
        build.build(Site(root), out)
        first = build.snapshot(out)
        build.build(Site(root), out)
        self.assertEqual(first, build.snapshot(out))
        self.assertFalse((out / "stale.html").exists())

    def test_apps_without_pages_are_skipped(self):
        root = make_site(with_pages=False)
        out = root / "docs"
        build.build(Site(root), out)
        self.assertTrue((out / "ko" / "index.html").exists())
        self.assertFalse((out / "ko" / "demo").exists())


class SpecPairTest(unittest.TestCase):
    """2026-10-25: ASC 레코드가 없는 출시 전 앱 SpecPair 는 ko 소개, 지원, 처리방침만 연다(쿠팡 파트너스 활동 매체 주소).
    허브에는 이름 없는 흐린 아이콘으로만 남고, 어느 쪽에도 App Store 링크나 스마트 배너가 없다."""

    @classmethod
    def setUpClass(cls):
        cls.out = Path(tempfile.mkdtemp(prefix="kvndh-specpair-")) / "docs"
        cls.written = build.build(Site(REPO), cls.out)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.out.parent, ignore_errors=True)

    def test_ko_pages_exist_without_store_link(self):
        for path in ("/ko/specpair/", "/ko/specpair/support/", "/ko/specpair/privacy/"):
            self.assertIn(path, self.written)
            html = (self.out / path.lstrip("/") / "index.html").read_text(encoding="utf-8")
            self.assertIn("스펙페어", html)
            self.assertNotIn("apps.apple.com", html)
            self.assertNotIn("apple-itunes-app", html)
        sitemap = (self.out / "sitemap.xml").read_text()
        self.assertIn("<loc>https://kvndh.com/ko/specpair/</loc>", sitemap)

    def test_ko_only(self):
        for code in Site(REPO).lang_codes():
            if code != "ko":
                self.assertFalse((self.out / code / "specpair").exists(), code)
                self.assertTrue((self.out / code / "index.html").exists(), code)

    def test_hub_keeps_it_nameless(self):
        for code in Site(REPO).lang_codes():
            hub = (self.out / code / "index.html").read_text(encoding="utf-8")
            self.assertIn('src="/assets/specpair/icon-180.webp" alt="" width="72" height="72" class="soon"', hub)
            self.assertNotIn("/specpair/", hub.replace("/assets/specpair/", ""))
            self.assertNotIn("스펙페어", hub)


if __name__ == "__main__":
    unittest.main()
