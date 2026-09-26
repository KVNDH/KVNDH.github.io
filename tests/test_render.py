from __future__ import annotations

import json
import unittest

from tests.fixture import look, make_site, store, write
import render
from sitelib import Site


class HubTest(unittest.TestCase):
    def setUp(self):
        self.site = Site(make_site())

    def test_hub_tile_links_whole_tile_and_store(self):
        html = render.render_hub(self.site, "ko")
        self.assertIn('<html lang="ko">', html)
        self.assertIn('<article class="tile t-feature th-light"', html)
        self.assertIn('<a class="tile-link" href="/ko/demo/">Demo</a>', html)
        self.assertIn('aria-label="Demo store"', html)
        self.assertIn("https://apps.apple.com/app/id123", html)
        self.assertIn('<div class="shot" style="--sw:196px">', html)

    def test_hub_is_the_light_page(self):
        self.assertIn('<body class="hub">', render.render_hub(self.site, "ko"))

    def test_tile_uses_the_store_screenshot_when_present(self):
        store(self.site.root, "en", 1)
        html = render.render_hub(Site(self.site.root), "ko")
        self.assertIn('<div class="shot shot-store"><img src="/assets/demo/store/en/01.webp"', html)
        self.assertNotIn('--sw:196px', html)

    def test_tile_takes_the_app_field_and_ink(self):
        look(self.site.root, ink="light", color="#101418")
        html = render.render_hub(Site(self.site.root), "ko")
        self.assertIn('<article class="tile t-feature th-dark"', html)
        self.assertIn("--fc:#101418;--fld:url(/assets/demo/field.webp)", html)

    def test_feature_tile_shows_summary(self):
        self.assertIn('<p class="hook">summary</p>', render.render_hub(self.site, "ko"))

    def test_hub_has_no_summary_sentence(self):
        html = render.render_hub(self.site, "ko")
        self.assertIn('<h1 class="sr-only">ko hubMetaTitle</h1>', html)
        self.assertIn('<meta name="description" content="Demo">', html)

    def test_hub_footer_lists_privacy_and_languages(self):
        html = render.render_hub(self.site, "ko")
        self.assertIn('<footer class="sf">', html)
        self.assertIn('href="/ko/demo/privacy/"', html)
        self.assertIn('<ul class="langs">', html)

    def test_hub_without_pages_has_no_detail_link(self):
        html = render.render_hub(Site(make_site(with_pages=False)), "ko")
        self.assertNotIn('href="/ko/demo/"', html)
        self.assertNotIn('class="tile-link"', html)
        self.assertIn("https://apps.apple.com/app/id123", html)

    def test_unreleased_app_shows_only_its_icon(self):
        site = Site(make_site(unreleased=True))
        html = render.render_hub(site, "ko")
        self.assertIn('<div class="quiet" aria-hidden="true">', html)
        self.assertIn('src="/assets/soon/icon-180.webp"', html)
        self.assertNotIn("Soon", html)
        self.assertNotIn("/ko/soon/", html)
        self.assertNotIn("https://apps.apple.com/app/id456", html)

    def test_unreleased_app_page_has_no_store_button(self):
        site = Site(make_site(unreleased=True))
        html = render.render_app(site, "ko", "soon")
        self.assertIn("Soon", html)
        self.assertNotIn("https://apps.apple.com/app/id456", html)
        self.assertNotIn('class="btn"', html)

    def test_app_without_store_record_has_pages_but_no_smart_banner(self):
        # 2026-09-26 Readride: ASC 레코드가 생기기 전에 지원, 개인정보 주소가 먼저 열려 있어야 한다
        root = make_site(unreleased=True)
        path = root / "content" / "site.json"
        config = json.loads(path.read_text(encoding="utf-8"))
        del next(a for a in config["apps"] if a["slug"] == "soon")["appStoreId"]
        write(path, config)
        site = Site(root)
        html = render.render_app(site, "ko", "soon")
        self.assertIn("Soon", html)
        self.assertNotIn("apple-itunes-app", html)
        self.assertNotIn("https://apps.apple.com/", html)
        self.assertIn("Soon", render.render_privacy(site, "ko", "soon"))


class TilePositionTest(unittest.TestCase):
    def test_five_or_fewer_keep_the_grid(self):
        self.assertEqual(render.tile_positions(5), render.TILE_POSITIONS)

    def test_six_apps_split_the_third_row(self):
        self.assertEqual(render.tile_positions(6)[3:], ["t-r1", "t-r2", "t-r3"])

    def test_seven_apps_make_two_rows_of_two(self):
        self.assertEqual(render.tile_positions(7)[3:], ["t-r1", "t-r2", "t-q1", "t-q2"])

    def test_more_apps_than_tiles_stops_the_build(self):
        with self.assertRaises(SystemExit):
            render.tile_positions(8)


class AppPageTest(unittest.TestCase):
    def setUp(self):
        self.site = Site(make_site())

    def test_alternates_cover_active_languages_and_default(self):
        html = render.render_app(self.site, "ko", "demo")
        self.assertIn('hreflang="ko" href="https://kvndh.com/ko/demo/"', html)
        self.assertIn('hreflang="en" href="https://kvndh.com/en/demo/"', html)
        self.assertIn('hreflang="x-default" href="https://kvndh.com/en/demo/"', html)
        self.assertNotIn('hreflang="ja"', html)

    def test_app_bar_accent_and_banner(self):
        html = render.render_app(self.site, "ko", "demo")
        self.assertIn('content="app-id=123"', html)
        self.assertIn("--acc:#A05B42;--ink:#E39C80;--glow:rgba(160,91,66,.5);--p-acc:#8A4A34;--btn:#A05B42", html)
        self.assertIn('<nav class="ab"', html)
        self.assertIn('<a href="/ko/demo/" aria-current="page">ko navAbout</a>', html)
        self.assertIn('href="/ko/demo/support/"', html)

    def test_hero_and_sections(self):
        html = render.render_app(self.site, "ko", "demo")
        self.assertIn('<h1 class="hero-n">Demo</h1>', html)
        self.assertIn('<div class="pano"><img src="/assets/demo/shots/en/01.webp" alt="Demo ko screenshot"', html)
        self.assertNotIn('class="meta"', html)
        self.assertIn('<section class="feat"><figure class="feat-vis crop">', html)
        self.assertIn('<section class="feat feat-rev"><div class="feat-vis kit"', html)
        self.assertIn('<li class="on"><span class="g g-gl"></span><b>n</b><small>d</small></li>', html)
        self.assertIn('<i style="--i:2" class="on"></i>', html)
        self.assertIn('<section class="duo"><div class="card"><p class="kick">03</p>', html)
        self.assertIn('<div class="play" aria-hidden="true">', html)
        self.assertIn('<ul class="chips"><li>c</li></ul>', html)

    def test_page_takes_the_app_field(self):
        html = render.render_app(self.site, "ko", "demo")
        self.assertIn('<body class="th-light" style="--fc:#F5F5F7">', html)
        look(self.site.root, ink="light", color="#101418")
        html = render.render_app(Site(self.site.root), "ko", "demo")
        self.assertIn('<body class="th-dark" style="--fc:#101418;--fld:url(/assets/demo/field.webp)">', html)
        self.assertIn('<meta name="theme-color" content="#101418">', html)

    def test_panorama_shows_the_store_screenshots_in_the_page_language(self):
        for i in (1, 2, 3):
            store(self.site.root, "en", i)
        look(self.site.root, ink="dark", color="#EEE8DD", alts={"en": ["one", "two", "three"]})
        html = render.render_app(Site(self.site.root), "ko", "demo")
        self.assertIn('<div class="pano"><img src="/assets/demo/store/en/01.webp" alt="one"', html)
        self.assertIn('<img src="/assets/demo/store/en/03.webp" alt="three"', html)
        store(self.site.root, "ko", 1)
        html = render.render_app(Site(self.site.root), "ko", "demo")
        self.assertIn('src="/assets/demo/store/ko/01.webp" alt="Demo ko screenshot"', html)
        self.assertNotIn("/store/en/", html)

    def test_crop_offsets_render_as_css_vars(self):
        crop = self.site.copy[("demo", "ko")]["sections"][0]["visual"]
        self.assertNotIn("style=", render.render_app(self.site, "ko", "demo").split("feat-vis crop")[1][:40])
        crop["focus"] = "-10px"
        self.assertIn('<figure class="feat-vis crop" style="--cy:-10px">', render.render_app(self.site, "ko", "demo"))
        crop["focusX"] = "26px"
        self.assertIn('style="--cy:-10px;--cx:26px"', render.render_app(self.site, "ko", "demo"))
        del crop["focus"]
        self.assertIn('style="--cx:26px"', render.render_app(self.site, "ko", "demo"))

    def test_glyph_svg_is_inlined_when_present(self):
        folder = self.site.root / "assets" / "demo" / "glyphs"
        folder.mkdir(parents=True)
        (folder / "gl.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 52 40" role="img" aria-label="Glaze"><path d="M0 0" fill="currentColor"/></svg>')
        html = render.render_app(self.site, "ko", "demo")
        self.assertIn('<span class="g-svg"><svg aria-hidden="true" focusable="false" xmlns=', html)
        self.assertNotIn('aria-label="Glaze"', html)
        self.assertNotIn('class="g g-gl"', html)

    def test_kit_without_glyphs_is_marked_plain(self):
        self.assertIn('<ul class="kit-b">', render.render_app(self.site, "ko", "demo"))
        del self.site.copy[("demo", "ko")]["sections"][1]["visual"]["items"][0]["glyph"]
        self.assertIn('<ul class="kit-b kit-b--plain">', render.render_app(self.site, "ko", "demo"))

    def test_pro_block_lists_pro_features_only(self):
        html = render.render_app(self.site, "ko", "demo")
        self.assertIn("<h2>first<br>second</h2>", html)
        self.assertIn('<ul class="chk chk-pro"><li>p</li></ul>', html)
        self.assertNotIn("plans", html.split("<main")[1])
        self.assertNotIn("badge", html.split("<main")[1])

    def test_hero_meta_is_optional(self):
        self.site.copy[("demo", "ko")]["hero"]["meta"] = "meta"
        self.assertIn('<span class="meta">meta</span>', render.render_app(self.site, "ko", "demo"))

    def test_app_page_without_pro(self):
        self.site.copy[("demo", "ko")]["pro"] = None
        self.assertNotIn('class="pro"', render.render_app(self.site, "ko", "demo"))

    def test_text_is_escaped(self):
        self.site.copy[("demo", "ko")]["hero"]["hook"] = "<script>x</script>"
        html = render.render_app(self.site, "ko", "demo")
        self.assertNotIn("<script>x</script>", html)
        self.assertIn("&lt;script&gt;x&lt;/script&gt;", html)

    def test_screenshot_falls_back_to_en(self):
        self.assertEqual(render.shot_path(self.site, "demo", "ko"), "/assets/demo/shots/en/01.webp")
        with self.assertRaises(FileNotFoundError):
            render.shot_path(self.site, "demo", "ko", index=2)

    def test_unknown_visual_fails(self):
        self.site.copy[("demo", "ko")]["sections"][0]["visual"]["type"] = "video"
        with self.assertRaises(ValueError):
            render.render_app(self.site, "ko", "demo")


class OtherPagesTest(unittest.TestCase):
    def setUp(self):
        self.site = Site(make_site())

    def test_support_page_has_faq_and_contact(self):
        html = render.render_support(self.site, "en", "demo")
        self.assertIn('<section class="sup">', html)
        self.assertIn("<summary>q</summary>", html)
        self.assertIn('href="mailto:kvndh36@naver.com"', html)
        self.assertIn('<a href="/en/demo/support/" aria-current="page">', html)

    def test_privacy_sheet(self):
        html = render.render_privacy(self.site, "en", "demo")
        self.assertIn('<div class="sheet">', html)
        self.assertIn('<section id="p12"><h2><span>12</span>s12</h2>', html)
        self.assertIn('href="#p1"', html)
        self.assertIn('<time datetime="2026-09-17">2026-09-17</time>', html)
        self.assertIn('<p class="doc-sum"><strong>en summaryLabel</strong>sum</p>', html)
        self.assertIn('<dd><a href="mailto:kvndh36@naver.com">kvndh36@naver.com</a></dd>', html)
        self.assertIn('<p class="doc-end">from 2026-09-17</p>', html)

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
