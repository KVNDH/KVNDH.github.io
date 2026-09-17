from __future__ import annotations

import unittest

from tests.fixture import make_site
import render
from sitelib import Site


class RenderTest(unittest.TestCase):
    def setUp(self):
        self.site = Site(make_site())

    def test_hub_lists_app_with_links(self):
        html = render.render_hub(self.site, "ko")
        self.assertIn('<html lang="ko">', html)
        self.assertIn('href="/ko/demo/"', html)
        self.assertIn("https://apps.apple.com/app/id123", html)
        self.assertIn("tile--featured", html)

    def test_hub_has_no_summary_sentence(self):
        html = render.render_hub(self.site, "ko")
        self.assertNotIn("hub-intro", html)
        self.assertIn('<h1 class="sr-only">ko hubMetaTitle</h1>', html)
        self.assertIn('<meta name="description" content="Demo">', html)

    def test_hub_without_pages_has_no_detail_link(self):
        html = render.render_hub(Site(make_site(with_pages=False)), "ko")
        self.assertNotIn('href="/ko/demo/"', html)
        self.assertIn("https://apps.apple.com/app/id123", html)

    def test_alternates_cover_active_languages_and_default(self):
        html = render.render_app(self.site, "ko", "demo")
        self.assertIn('hreflang="ko" href="https://kvndh.com/ko/demo/"', html)
        self.assertIn('hreflang="en" href="https://kvndh.com/en/demo/"', html)
        self.assertIn('hreflang="x-default" href="https://kvndh.com/en/demo/"', html)
        self.assertNotIn('hreflang="ja"', html)

    def test_app_page_has_banner_accent_tabs_and_pro(self):
        html = render.render_app(self.site, "ko", "demo")
        self.assertIn('content="app-id=123"', html)
        self.assertIn("--accent:#A05B42;--accent-text:#E39C80", html)
        self.assertIn('href="/ko/demo/support/"', html)
        self.assertIn('aria-current="page"', html)
        self.assertIn('class="pro"', html)

    def test_app_page_without_pro(self):
        self.site.copy[("demo", "ko")]["pro"] = None
        self.assertNotIn('class="pro"', render.render_app(self.site, "ko", "demo"))

    def test_support_page_has_faq_and_contact(self):
        html = render.render_support(self.site, "en", "demo")
        self.assertIn("<summary>q</summary>", html)
        self.assertIn('href="mailto:kvndh36@naver.com"', html)

    def test_privacy_has_twelve_numbered_sections_and_toc(self):
        html = render.render_privacy(self.site, "en", "demo")
        self.assertIn('id="p12"', html)
        self.assertIn('href="#p1"', html)
        self.assertIn("2026-09-17", html)
        self.assertIn('class="paper"', html)

    def test_text_is_escaped(self):
        self.site.copy[("demo", "ko")]["hero"]["hook"] = "<script>x</script>"
        html = render.render_app(self.site, "ko", "demo")
        self.assertNotIn("<script>x</script>", html)
        self.assertIn("&lt;script&gt;x&lt;/script&gt;", html)

    def test_screenshot_falls_back_to_en(self):
        self.assertEqual(render.shot_path(self.site, "demo", "ko"), "/assets/demo/shots/en/01.webp")
        with self.assertRaises(FileNotFoundError):
            render.shot_path(self.site, "demo", "ko", index=2)

    def test_no_external_resources(self):
        for html in (render.render_hub(self.site, "ko"), render.render_app(self.site, "ko", "demo"),
                     render.render_privacy(self.site, "ko", "demo")):
            self.assertNotRegex(html, r'src="(https?:)?//')
            self.assertNotIn('rel="stylesheet"', html)
            self.assertIn("<style>", html)

    def test_root_redirect_and_language_list(self):
        html = render.render_root(self.site)
        self.assertIn('["ko", "en"]', html)
        self.assertIn('href="/en/"', html)
        self.assertIn("location.replace", html)

    def test_404_uses_absolute_links(self):
        html = render.render_404(self.site)
        self.assertIn('href="/ko/"', html)
        self.assertIn("ko notFound", html)

    def test_sitemap_lists_only_directory_pages(self):
        xml = render.render_sitemap(self.site, ["/", "/404.html", "/ko/"])
        self.assertIn("<loc>https://kvndh.com/ko/</loc>", xml)
        self.assertNotIn("404", xml)


if __name__ == "__main__":
    unittest.main()
