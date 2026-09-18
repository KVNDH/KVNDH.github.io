from __future__ import annotations

import unittest

from tests.fixture import make_site
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


if __name__ == "__main__":
    unittest.main()
