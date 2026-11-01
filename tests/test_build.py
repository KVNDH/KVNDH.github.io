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

    def test_static_subfolders_survive_the_build(self):
        # 2026-11-01: docs/ 는 빌드마다 지워진다. 옛 주소 연결 쪽은 static/ 아래 경로 그대로 다시 놓인다
        root = make_site()
        moved = root / "static" / "ko" / "old" / "index.html"
        moved.parent.mkdir(parents=True)
        moved.write_text("moved")
        out = root / "docs"
        written = build.build(Site(root), out)
        self.assertEqual((out / "ko" / "old" / "index.html").read_text(), "moved")
        self.assertTrue((out / "ko" / "index.html").exists())
        self.assertNotIn("/ko/old/", written)
        self.assertNotIn("/ko/old/", (out / "sitemap.xml").read_text())

    def test_apps_without_pages_are_skipped(self):
        root = make_site(with_pages=False)
        out = root / "docs"
        build.build(Site(root), out)
        self.assertTrue((out / "ko" / "index.html").exists())
        self.assertFalse((out / "ko" / "demo").exists())


class SpecPairRetiredTest(unittest.TestCase):
    """2026-11-01: 옛 가칭 specpair 를 spectable 로 합쳤다. 쿠팡 파트너스 활동 매체에 옛 주소 등록이 남아 있어
    옛 주소 셋은 끊지 않고 새 주소로 보낸다(static/ko/specpair). 제휴 링크와 대가성 문구는 spectable ko 쪽으로 옮겼다."""

    MOVED = {
        "ko/specpair/": "/ko/spectable/",
        "ko/specpair/support/": "/ko/spectable/support/",
        "ko/specpair/privacy/": "/ko/spectable/privacy/",
    }
    PARTNER_LINKS = ("https://link.coupang.com/a/h8G9sJl5Qy", "https://link.coupang.com/a/h8G9J2MtNY",
                     "https://link.coupang.com/a/h8G934WY1c")

    @classmethod
    def setUpClass(cls):
        cls.out = Path(tempfile.mkdtemp(prefix="kvndh-specpair-")) / "docs"
        cls.written = build.build(Site(REPO), cls.out)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.out.parent, ignore_errors=True)

    def test_old_addresses_lead_to_the_same_page_of_spectable(self):
        for old, new in self.MOVED.items():
            html = (self.out / old / "index.html").read_text(encoding="utf-8")
            self.assertIn(f'<meta http-equiv="refresh" content="0; url={new}">', html)
            self.assertIn(f'<link rel="canonical" href="https://kvndh.com{new}">', html)
            self.assertIn(f'<a href="{new}">', html)
            self.assertIn('<meta name="robots" content="noindex">', html)
            self.assertIn("스펙페어는 스펙테이블이 되었습니다.", html)
            self.assertTrue((self.out / new.lstrip("/") / "index.html").exists(), new)
            self.assertIn(new, self.written)

    def test_old_addresses_leave_the_sitemap_and_page_list(self):
        sitemap = (self.out / "sitemap.xml").read_text()
        self.assertNotIn("specpair", sitemap)
        self.assertIn("<loc>https://kvndh.com/ko/spectable/</loc>", sitemap)
        self.assertFalse([path for path in self.written if "specpair" in path])

    def test_old_app_is_gone_from_content_and_assets(self):
        site = Site(REPO)
        self.assertNotIn("specpair", [app["slug"] for app in site.apps])
        self.assertNotIn("specpair", site.looks)
        self.assertFalse((self.out / "assets" / "specpair").exists())

    def test_old_address_was_only_ko(self):
        for code in Site(REPO).lang_codes():
            if code != "ko":
                self.assertFalse((self.out / code / "specpair").exists(), code)
                self.assertTrue((self.out / code / "index.html").exists(), code)

    def test_hub_has_spectable_and_no_specpair(self):
        for code in Site(REPO).lang_codes():
            hub = (self.out / code / "index.html").read_text(encoding="utf-8")
            self.assertNotIn("specpair", hub.lower())
            self.assertNotIn("스펙페어", hub)
            self.assertIn('src="/assets/spectable/icon-180.webp"', hub)

    def test_partner_links_moved_to_spectable_ko_with_notice_first(self):
        html = (self.out / "ko" / "spectable" / "index.html").read_text(encoding="utf-8")
        main = html[html.index('id="main"'):]
        notice = '<p class="pnotice">이 게시물은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.</p>'
        self.assertLess(main.index(notice), main.index('class="app-hero"'))
        for url in self.PARTNER_LINKS:
            self.assertIn(f'href="{url}" rel="sponsored noopener"', html)

    def test_partner_links_stay_ko_only(self):
        for code in Site(REPO).lang_codes():
            if code != "ko":
                html = (self.out / code / "spectable" / "index.html").read_text(encoding="utf-8")
                self.assertNotIn("pnotice", html.split("</style>", 1)[1], code)
                self.assertNotIn("link.coupang.com", html, code)


if __name__ == "__main__":
    unittest.main()
