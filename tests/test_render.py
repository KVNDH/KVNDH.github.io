from __future__ import annotations

import json
import re
import unittest

from tests.fixture import REPO, look, make_site, store, write
import render
from sitelib import Site


class HubTest(unittest.TestCase):
    def setUp(self):
        self.site = Site(make_site())

    def test_hub_piece_links_page_and_store(self):
        html = render.render_hub(self.site, "ko")
        self.assertIn('<html lang="ko">', html)
        self.assertIn('<article class="piece" id="demo">', html)
        self.assertIn('<h2>Demo</h2>', html)   # 10-25 N: 이름은 글자, 소개 쪽 링크는 '자세히 보기' 하나
        self.assertEqual(html.count('href="/ko/demo/"'), 1)
        self.assertIn('<a class="lnk" href="/ko/demo/">ko learnMore</a>', html)
        self.assertIn('aria-label="Demo store"', html)
        self.assertIn("https://apps.apple.com/app/id123", html)
        self.assertIn('<span class="lab">No. 01 / 01</span>', html)

    def test_hub_is_the_album_page(self):
        html = render.render_hub(self.site, "ko")
        self.assertIn('<body class="hub">', html)
        self.assertIn('<main class="sheet" id="main">', html)
        self.assertNotIn('class="lede"', html)     # C안(10-25): 화면 동작을 풀어 쓴 안내 문장은 두지 않는다
        self.assertNotIn('class="cue', html)

    def test_piece_slot_is_a_button_with_the_icon(self):
        html = render.render_hub(self.site, "ko")
        self.assertIn('<button class="slot" type="button" data-open="0" aria-label="Demo larger">'
                      '<img src="/assets/demo/icon-360.webp"', html)
        (self.site.root / "assets" / "demo" / "icon-640.webp").write_bytes(b"x")
        self.assertIn('<img src="/assets/demo/icon-640.webp"', render.render_hub(Site(self.site.root), "ko"))

    def test_viewer_actions_stay_in_view_on_landscape_phones(self):
        # 10-25: 가로 폰(844x390)에서 크게 보기의 상점, 자세히 보기, 지원 줄이 시트 스크롤 아래에 숨지 않게 바닥에 붙인다
        html = render.render_hub(self.site, "ko")
        self.assertIn("@media (max-height:500px) and (min-width:721px){", html)
        self.assertIn(".vtext .acts{position:sticky;bottom:-28px", html)

    def test_hub_has_no_summary_sentence(self):
        html = render.render_hub(self.site, "ko")
        self.assertIn('<h1 class="sr-only">ko hubMetaTitle</h1>', html)
        self.assertIn('<meta name="description" content="Demo">', html)

    def test_hub_footer_lists_privacy_in_one_flow(self):
        html = render.render_hub(self.site, "ko")
        self.assertIn('<footer class="foot">', html)
        self.assertIn('href="/ko/demo/privacy/"', html)
        # 10-25: 처리방침은 맨 아래 한 줄 전체(.fpv)에 옆으로 흐르는 목록(.flow)
        self.assertIn('<div class="fpv"><h2>ko navPrivacy</h2><ul class="flow">', html)
        self.assertIn(".foot .fpv{grid-column:1/-1}", html)

    def test_hub_without_pages_has_no_detail_link(self):
        html = render.render_hub(Site(make_site(with_pages=False)), "ko")
        self.assertNotIn('href="/ko/demo/"', html)
        self.assertIn("<h2>Demo</h2>", html)
        self.assertIn("https://apps.apple.com/app/id123", html)

    def test_unreleased_app_shows_only_its_icon(self):
        site = Site(make_site(unreleased=True))
        html = render.render_hub(site, "ko")
        self.assertIn('<section class="quiet" aria-hidden="true"><span class="qslot">', html)
        self.assertIn('src="/assets/soon/icon-180.webp"', html)
        self.assertIn('<img src="/assets/soon/icon-180.webp" alt="" width="72" height="72" class="soon">', html)
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


class AppPageTest(unittest.TestCase):
    def setUp(self):
        self.site = Site(make_site())

    def test_alternates_cover_active_languages_and_default(self):
        html = render.render_app(self.site, "ko", "demo")
        self.assertIn('hreflang="ko" href="https://kvndh.com/ko/demo/"', html)
        self.assertIn('hreflang="en" href="https://kvndh.com/en/demo/"', html)
        self.assertIn('hreflang="x-default" href="https://kvndh.com/en/demo/"', html)
        self.assertNotIn('hreflang="ja"', html)

    def test_app_bar_and_banner(self):
        html = render.render_app(self.site, "ko", "demo")
        self.assertIn('content="app-id=123"', html)
        self.assertIn('<nav class="ab"', html)
        self.assertIn('<a href="/ko/demo/" aria-current="page">ko navAbout</a>', html)
        self.assertIn('href="/ko/demo/support/"', html)

    def test_hero_and_sections(self):
        html = render.render_app(self.site, "ko", "demo")
        self.assertIn('<h1 class="hero-n">Demo</h1>', html)
        self.assertIn('<div class="frame still">', html)
        self.assertIn('<div class="plate plate-l"><img class="ic-l" src="/assets/demo/icon-360.webp" alt=""', html)
        self.assertIn('<span class="lab">No. 01 / 01</span>', html)
        self.assertIn('<section class="pano"><figure class="print"><img src="/assets/demo/shots/en/01.webp" alt="Demo ko screenshot"', html)
        self.assertNotIn('class="meta"', html)
        self.assertIn('<section class="feat"><figure class="feat-vis crop">', html)
        self.assertIn('<section class="feat feat-rev"><div class="feat-vis kit"', html)
        self.assertIn('<li class="on"><span class="g g-gl"></span><b>n</b><small>d</small></li>', html)
        self.assertIn('<i style="--i:2" class="on"></i>', html)
        self.assertIn('<section class="duo"><div class="card"><p class="kick">03</p>', html)
        self.assertIn('<div class="play" aria-hidden="true">', html)
        self.assertIn('<ul class="chips"><li>c</li></ul>', html)

    def test_page_is_the_album_paper(self):
        html = render.render_app(self.site, "ko", "demo")
        self.assertIn('<body class="app">', html)
        self.assertIn('<meta name="theme-color" content="#000000" media="(prefers-color-scheme: dark)">', html)
        # 10-25 Y: 앱 쪽 번호 점은 번호만. 이름은 바로 아래 머리띠에 한 번
        self.assertIn('<p class="now" data-on="1" aria-hidden="true"><i></i><b>01 / 01</b></p>', html)
        for kind in (render.render_support, render.render_privacy):
            self.assertIn('<b>01 / 01</b></p>', kind(self.site, "ko", "demo"))

    def test_unreleased_app_page_shows_no_number_dot(self):
        html = render.render_app(Site(make_site(unreleased=True)), "ko", "soon")
        self.assertIn('<p class="now" data-on="0" aria-hidden="true"><i></i><b></b></p>', html)

    def test_store_button_reads_like_the_hub(self):
        # 10-25 W: 허브와 앱 쪽이 같은 'App Store ↗' 한 문구, 앱 이름은 접근 이름에
        html = render.render_app(self.site, "ko", "demo")
        self.assertIn('<a class="btn" href="https://apps.apple.com/app/id123" aria-label="Demo store">App Store ↗</a>', html)
        self.assertIn('<a class="btn btn-s" href="https://apps.apple.com/app/id123" aria-label="Demo store">App Store ↗</a>', html)
        self.assertNotIn("getOnAppStore", html)
        self.assertIn('aria-label="Demo store">App Store ↗</a>', render.render_hub(self.site, "ko"))

    def test_panorama_shows_the_store_screenshots_in_the_page_language(self):
        for i in (1, 2, 3):
            store(self.site.root, "en", i)
        look(self.site.root, ink="dark", color="#EEE8DD", alts={"en": ["one", "two", "three"]})
        html = render.render_app(Site(self.site.root), "ko", "demo")
        self.assertIn('<figure class="print"><img src="/assets/demo/store/en/01.webp" alt="one">', html)
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
        self.assertIn('<div class="pv">', html)
        self.assertIn('<body class="page-doc">', html)
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

    # 화첩(2026-10-16): 판이 읽을 언어별 데이터를 JSON 으로 넣는다
    def canvas(self, html):
        m = re.search(r'<script type="application/json" id="canvas-data">(.*?)</script>', html, re.S)
        self.assertIsNotNone(m)
        return json.loads(m.group(1))

    def test_no_page_carries_three(self):
        # C안(2026-10-25): 허브도 3D 를 싣지 않는다. 로더, 캔버스, 묶음 주소가 어느 페이지에도 없다
        for html in (render.render_hub(self.site, "ko"), render.render_app(self.site, "ko", "demo"),
                     render.render_support(self.site, "ko", "demo"), render.render_privacy(self.site, "ko", "demo")):
            markup = re.sub(r"<style>.*?</style>", "", html, flags=re.S)
            for needle in ("kvndh-canvas.js", "webgl", 'id="gl"', "gl-wait", "data-plate", "gl-only", "readout"):
                self.assertNotIn(needle, markup)

    def test_canvas_data_is_per_language(self):
        ko = self.canvas(render.render_hub(self.site, "ko"))
        en = self.canvas(render.render_hub(self.site, "en"))
        self.assertEqual(ko["page"], "hub")
        self.assertEqual(ko["ui"], {"total": "01", "more": "ko learnMore", "support": "ko navSupport"})
        app = ko["plates"][0]
        self.assertEqual((app["name"], app["no"], app["href"], app["support"]), ("Demo", "01", "/ko/demo/", "/ko/demo/support/"))
        self.assertEqual(en["plates"][0]["href"], "/en/demo/")
        self.assertEqual(app["icon"], "/assets/demo/icon-360.webp")
        self.assertEqual(app["bullets"], ["x", "y"])
        self.assertEqual(app["storeLabel"], "Demo store")

    def test_sub_pages_carry_no_three(self):
        # B안(2026-10-16): 소개, 지원, 개인정보는 판 묶음도 로더도 판 데이터도 싣지 않고 CSS 정지 판 하나만 건다
        for html in (render.render_app(self.site, "ko", "demo"), render.render_support(self.site, "ko", "demo"),
                     render.render_privacy(self.site, "ko", "demo")):
            markup = re.sub(r"<style>.*?</style>", "", html, flags=re.S)
            for needle in ("kvndh-canvas.js", "webgl", 'id="gl"', "canvas-data", "data-plate", "gl-only", "readout"):
                self.assertNotIn(needle, markup)
            self.assertEqual(html.count('class="plate plate-'), 1)

    def test_still_plate_tilt_stops_for_reduced_motion(self):
        css = render.css(Site(make_site()))
        self.assertIn("@media (hover:hover) and (prefers-reduced-motion:no-preference){\n.still:hover .plate{", css)
        self.assertEqual(css.count("{\n.still:hover"), 1)
        self.assertNotRegex(css.split("@media (hover:hover) and (prefers-reduced-motion:no-preference)")[0], r":hover \.plate")

    def test_canvas_without_pages_has_no_link(self):
        data = self.canvas(render.render_hub(Site(make_site(with_pages=False)), "ko"))
        self.assertIsNone(data["plates"][0]["href"])

    def test_unreleased_app_is_a_nameless_blurred_plate(self):
        html = render.render_hub(Site(make_site(unreleased=True)), "ko")
        data = self.canvas(html)
        self.assertEqual(len(data["plates"]), 2)
        self.assertEqual(data["plates"][1], {"icon": "/assets/soon/icon-360.webp", "soon": True})
        self.assertNotIn("Soon", html)
        self.assertNotIn("/ko/soon/", html)

    def test_first_released_app_tops_the_pile(self):
        # 첫 화면 더미는 위에서부터 1, 2, ... 줄이고 맨 위가 출시된 첫 앱(출시 전 앱은 뒤로)
        html = render.render_hub(Site(make_site(unreleased=True)), "ko")
        fan = re.search(r'<div class="fan" style="--rows:2">(.*?)</div>', html).group(1)
        self.assertTrue(fan.startswith('<span class="row"><a href="#demo"><img src="/assets/demo/icon-180.webp"'))
        self.assertEqual(fan.count('<span class="row">'), 2)

    def test_canvas_json_cannot_close_its_script(self):
        site = Site(make_site())
        site.copy[("demo", "ko")]["subtitle"] = "a</script><b>"
        html = render.render_hub(site, "ko")
        self.assertEqual(self.canvas(html)["plates"][0]["sub"], "a</script><b>")
        self.assertNotIn("a</script>", html)

    def test_root_redirect_and_language_list(self):
        html = render.render_root(self.site)
        self.assertIn('["ko", "en"]', html)
        self.assertIn('href="/en/"', html)
        self.assertIn("location.replace", html)

    def test_404_uses_absolute_links(self):
        html = render.render_404(self.site)
        self.assertIn('href="/ko/"', html)

    def test_scripts_stay_inline_and_off_404(self):
        site = Site(make_site())
        for html in (render.render_app(site, "ko", "demo"), render.render_support(site, "ko", "demo"),
                     render.render_privacy(site, "ko", "demo")):
            self.assertNotIn("__open", html)   # 크게 보기는 허브에만
        self.assertIn("__open", render.render_hub(site, "ko"))
        self.assertNotIn("<script", render.render_404(site))
        self.assertEqual(render.render_root(site).count("<script"), 1)

    def test_sub_pages_use_album_marks(self):
        site = Site(make_site())
        about = render.render_app(site, "ko", "demo")
        self.assertIn('<a class="ab-id" href="/ko/demo/"><img class="ic"', about)
        self.assertIn('<span>Demo</span></a>', about)
        for html in (render.render_privacy(site, "ko", "demo"), render.render_support(site, "ko", "demo")):
            self.assertIn('<div class="doc-head"><span class="plate plate-s"><img src="/assets/demo/icon-180.webp"', html)
            self.assertIn('<p class="doc-k"><span>Demo</span><span class="mono">No. 01 / 01</span></p>', html)

    def test_hub_only_css_stays_on_the_hub(self):
        site = Site(make_site())
        sub, hub = render.css(site), render.css(site, hub=True)
        self.assertNotIn("/*h*/", sub + hub)
        self.assertNotIn("/*s*/", sub + hub)
        self.assertNotIn(".plate{", hub)
        self.assertNotIn(".viewer{", sub)
        self.assertNotIn("#gl{", sub)
        self.assertIn(".viewer{", hub)
        self.assertIn(".plate{", sub)
        self.assertLess(len(sub), len(hub))
        self.assertIn(".viewer{", render.render_hub(site, "ko"))
        self.assertNotIn(".viewer{", render.render_app(site, "ko", "demo"))

    def test_vermilion_sits_only_on_the_number_dot(self):
        for css in (render.css(Site(make_site())), render.css(Site(make_site()), hub=True)):
            self.assertEqual(css.upper().count("#E63946"), 1)
            self.assertEqual(css.count("var(--dot)"), 1)
            self.assertIn(".now i{", css.split("var(--dot)")[0].rsplit("}", 1)[1])

    def test_dark_mode_is_pure_black(self):
        css = render.css(Site(make_site()))
        dark = css.split("@media (prefers-color-scheme:dark){:root{", 1)[1].split("}}", 1)[0]
        self.assertIn("--paper:#000000", dark)
        self.assertIn("--desk:#000000", dark)

    def test_sitemap_lists_only_directory_pages(self):
        xml = render.render_sitemap(self.site, ["/", "/404.html", "/ko/"])
        self.assertIn("<loc>https://kvndh.com/ko/</loc>", xml)
        self.assertNotIn("404", xml)


def rule(css: str, selector: str, media: str | None = None) -> str:
    """css 에서 selector 규칙 본문. media 를 주면 그 미디어 블록 안에서만 찾는다."""
    if media:
        css = css.split("@media " + media + "{", 1)[1]
        depth, end = 1, 0
        for end, ch in enumerate(css):
            depth += {"{": 1, "}": -1}.get(ch, 0)
            if depth == 0:
                break
        css = css[:end]
    m = re.search(r"(?:^|[}\n])" + re.escape(selector) + r"\{([^}]*)\}", css)
    return m.group(1) if m else ""


class OverlapAndWidthTest(unittest.TestCase):
    """10-25 사용성 제안 1단계(원인 ②): 고정 띠 겹침과 폭 경계."""

    def setUp(self):
        site = Site(make_site())
        self.hub, self.sub = render.css(site, hub=True), render.css(site)
        self.js = render.text(site, "hub.js")

    def z(self, css: str, selector: str) -> int:
        return int(re.search(r"z-index:(\d+)", rule(css, selector)).group(1))

    def test_viewer_sits_above_the_top_bar(self):
        # A: 머리띠(40)가 크게 보기(20)를 덮어 닫기 단추를 누르면 언어 메뉴가 열렸다
        self.assertGreater(self.z(self.hub, ".viewer"), self.z(self.hub, ".top"))
        self.assertLess(self.z(self.hub, ".viewer"), self.z(self.hub, ".skip"))

    def test_open_viewer_locks_the_album_scroll(self):
        # C: 열린 채 휠을 굴리면 뒤 화첩이 600px 내려갔다
        self.assertIn("overflow:hidden", rule(self.hub, "html.lock"))
        self.assertIn("scrollbar-gutter:stable", self.hub)
        self.assertIn("root.classList.add('lock')", self.js)
        self.assertIn("root.classList.remove('lock')", self.js)
        self.assertIn("scrollTop=0", self.js)   # 열 때마다 시트 맨 위(닫기 단추)부터
        self.assertNotIn("html.lock", self.sub)

    def test_viewer_actions_stay_in_reach_on_short_phones(self):
        # D: 375x667 에서 App Store, 자세히 보기, 지원 줄이 시트 안 스크롤 아래에 있었다
        acts = rule(self.hub, ".vtext .acts", "(max-width:720px)")
        self.assertIn("position:sticky", acts)
        bottom = int(re.search(r"padding:\d+px \d+px (\d+)px", rule(self.hub, ".vsheet", "(max-width:720px)")).group(1))
        self.assertIn(f"bottom:-{bottom}px", acts)   # 시트 아래 여백까지 덮는다
        self.assertIn("24vh", rule(self.hub, ".vslot", "(max-width:720px)"))

    def test_bar_store_button_hides_below_940(self):
        # AF: 721~853px 에서 상점 단추가 머리띠 밖으로 나가 페이지가 가로로 흔들렸다
        self.assertIn("display:none", rule(self.sub, ".ab .btn", "(max-width:940px)"))
        self.assertEqual(rule(self.sub, ".ab .btn"), "")

    def test_long_tab_names_wrap_up_to_374(self):
        # H: es 360폭 탭 줄이 6px 넘쳤다. .now 를 숨기는 경계(359)는 그대로
        self.assertIn("white-space:normal", rule(self.sub, ".tabs a", "(max-width:374px)"))
        self.assertIn("display:none", rule(self.sub, ".now", "(max-width:359px)"))

    def test_level_icons_shrink_at_every_width(self):
        # AG: Tapey 아이콘 줄이 720 이하에서만 줄어 721~1054px 에서 칸을 넘었다
        self.assertIn("flex:0 1 26px", rule(self.sub, ".lv i"))
        self.assertIn("min-width:0", rule(self.sub, ".lv i"))
        self.assertNotIn("width:26px;height:26px", self.sub)
        self.assertIn("max-width:100%", rule(self.sub, ".lv"))
        self.assertIn("flex-wrap:wrap", rule(self.sub, ".kit-r:has(.lv)"))   # 이름 옆 자리가 모자라면 아이콘 줄이 다음 줄로

    def test_ticks_wrap_below_the_label(self):
        # 3단계 후속: TailorColor 눈금 줄이 721~1120px 에서 칸 테두리를 넘고(es 최대 152px) es 721 은 문서가 10px 넘쳤다
        self.assertIn("flex-wrap:wrap", rule(self.sub, ".kit-r:has(.ticks)"))
        self.assertIn("flex:1 1 8em", rule(self.sub, ".kit-r:has(.ticks) p"))   # 자리가 되면(1280) 이름 옆 그대로
        self.assertIn("gap:6px", rule(self.sub, ".ticks", "(max-width:760px)"))
        self.assertEqual(rule(self.sub, ".ticks", "(max-width:720px)"), "")   # 720 안에만 있던 줄이기는 760 으로 옮김

    def test_contact_buttons_keep_their_width(self):
        # I: 1280폭 es 지원 '연락' 칸(124px)이 메일 단추(167px)보다 좁았다
        self.assertIn("min-width:auto", rule(self.sub, ".help div:last-child"))
        self.assertIn("min-width:0", rule(self.sub, ".help>div"))   # 왼쪽 안내문은 그대로 줄어든다


def contrast(a: str, b: str) -> float:
    def lum(h: str) -> float:
        c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        c = [v / 12.92 if v <= .03928 else ((v + .055) / 1.055) ** 2.4 for v in c]
        return .2126 * c[0] + .7152 * c[1] + .0722 * c[2]
    x, y = sorted((lum(a), lum(b)), reverse=True)
    return (x + .05) / (y + .05)


class AlternateConditionTest(unittest.TestCase):
    """10-25 사용성 제안 2단계(원인 ④): 다크, 인쇄, JS 클래스, 누르는 자리 같은 대체 조건 값."""

    def setUp(self):
        self.site = Site(make_site())
        self.hub, self.sub = render.css(self.site, hub=True), render.css(self.site)

    def colors(self, dark: bool) -> dict:
        body = self.sub.split("@media (prefers-color-scheme:dark){:root{", 1)[1].split("}}", 1)[0] if dark \
            else rule(self.sub, ":root")
        return dict(re.findall(r"--(\w+):(#[0-9A-Fa-f]{6})", body))

    def test_dark_secondary_text_keeps_the_light_hierarchy(self):
        # K: 다크 본문 대 보조 글자가 1.34:1 로 거의 같은 밝기였다(라이트 3.55:1)
        light, dark = self.colors(False), self.colors(True)
        self.assertGreaterEqual(contrast(dark["tx"], dark["t2"]), contrast(light["tx"], light["t2"]))
        self.assertGreaterEqual(contrast(dark["t2"], dark["paper"]), 4.5)
        self.assertGreaterEqual(contrast(dark["t2"], dark["pl"]), 4.5)

    def test_ghost_button_ring_is_visible_in_both_modes(self):
        # AA: 고스트 단추 테두리(--ln)가 라이트 1.43:1, 다크 1.55:1 이었다
        self.assertIn("inset 0 0 0 1px var(--t2)", rule(self.sub, ".btn-g"))
        for dark in (False, True):
            c = self.colors(dark)
            self.assertGreaterEqual(contrast(c["t2"], c["paper"]), 3)

    def test_print_drops_fixed_bars_and_opens_answers(self):
        # AB: 인쇄 규칙이 없어 머리띠가 쪽마다 본문을 덮고 지원 답은 하나도 인쇄되지 않았다
        for css in (self.hub, self.sub):
            self.assertIn("display:none", rule(css, ".top,.ab,.foot,.toc", "print"))
        self.assertIn("minmax(0,1fr)", rule(self.sub, ".pv", "print"))   # 목차가 빠진 자리로 본문이 넓어진다
        js = render.text(self.site, "page.js")
        self.assertIn("'beforeprint'", js)
        self.assertIn("'afterprint'", js)
        self.assertIn('<script>', render.render_support(self.site, "en", "demo"))
        self.assertIn("beforeprint", render.render_support(self.site, "en", "demo"))

    def test_small_links_are_44_wide(self):
        # J: '지원' 25px, 바닥 'Tapey' 38px, 목차 줄 40px 높이
        self.assertIn("min-width:44px", rule(self.hub, ".lnk"))
        self.assertIn("min-width:44px", rule(self.sub, ".foot a"))
        self.assertIn("min-height:44px", rule(self.sub, ".toc a"))

    def test_no_dead_view_button(self):
        # B: html 에 js 클래스를 붙이는 코드가 없어 '크게 보기' 단추 8개가 늘 숨어 있었다. 입구는 아이콘 판 하나
        html = render.render_hub(self.site, "ko")
        self.assertEqual(html.count("data-open="), 1)
        self.assertNotIn('class="lnk big"', html)
        self.assertNotIn(".big{", self.hub)
        self.assertNotIn("html:not(.js)", self.hub)
        self.assertIn('aria-label="ko viewLarge"', html)   # 크게 보기 대화상자 이름으로는 그대로 쓴다

def grow(site: Site, times: int) -> Site:
    """출시된 demo 앱을 times 벌로 늘린 사이트(같은 문구, 다른 slug)."""
    base = site.apps[0]
    for k in range(2, times + 1):
        slug = f"demo{k}"
        site.apps.append(base | {"slug": slug, "appStoreId": str(1000 + k)})
        for code in site.lang_codes():
            site.copy[(slug, code)] = site.copy[(base["slug"], code)] | {"name": f"Demo{k}"}
    return site


def footer(html: str) -> str:
    return html[html.index('<footer'):html.index('</footer>')]


class ListCapTest(unittest.TestCase):
    """10-25 사용성 제안 3단계(원인 ①): 앱 수, 언어 수만큼 쌓이거나 줄어드는 목록에 상한과 흐름."""

    def setUp(self):
        self.site = Site(make_site())
        self.hub = render.css(self.site, hub=True)

    def test_same_yardstick_with_twice_the_apps(self):
        # 1: 앱이 두 배가 돼도 바닥 블록, 404 문단, 판 안 링크 수는 늘지 않는다(늘어나는 것은 흐르는 목록의 항목뿐)
        one = render.render_hub(grow(Site(make_site()), 4), "ko")
        two = render.render_hub(grow(Site(make_site()), 8), "ko")
        for html in (one, two):
            self.assertEqual(footer(html).count("<h2>"), 2)          # 문의, 처리방침
            self.assertEqual(footer(html).count('<ul class="flow">'), 1)
        self.assertEqual(footer(two).count("<li>") - footer(one).count("<li>"), 4)   # 앱 하나에 항목 하나
        pieces = re.findall(r'<article class="piece".*?</article>', two, re.S)
        self.assertEqual(len(pieces), 8)
        self.assertEqual({len(re.findall(r"<a |<button ", p)) for p in pieces}, {3})   # 판 단추, App Store, 자세히 보기
        self.assertIn('style="--rows:3"', one)   # 4개 = 1 + 2 + 1
        self.assertIn('style="--rows:4"', two)   # 8개 = 1 + 2 + 3 + 2
        two_langs = render.render_404(Site(make_site(langs=("ko", "en"))))
        three_langs = render.render_404(Site(make_site(langs=("ko", "en", "ja"))))
        self.assertEqual(len(re.findall(r"<p[ >]", two_langs)), len(re.findall(r"<p[ >]", three_langs)))

    def test_hub_footer_has_no_language_block(self):
        # M: 머리띠 메뉴와 같은 언어 목록이 바닥에 한 번 더 있었다(390폭 바닥 553 → 425px)
        html = render.render_hub(self.site, "ko")
        self.assertNotIn('class="langs"', html)
        self.assertNotIn("ko language</h2>", footer(html))
        self.assertIn('<details class="lang">', html)   # 언어는 머리띠 메뉴 하나로
        self.assertNotIn(".foot .langs", self.hub)

    def test_404_is_the_number_and_languages(self):
        # F, G: 언어마다 안내문을 쌓아 360폭 첫 언어 링크가 794px(가시 740px), ja 셋째 줄에 '。' 한 글자
        html = render.render_404(Site(make_site(langs=("ko", "en", "ja"))))
        self.assertNotIn("<p lang=", html)
        self.assertEqual(len(re.findall(r"<p[ >]", html)), 1)   # No. 404 하나
        self.assertEqual(html.count('<li><a href="/'), 3)
        for path in sorted((REPO / "content" / "i18n").glob("*.json")):   # 실제 여덟 언어 파일에 다시 들어오지 않게
            self.assertNotIn("notFound", json.loads(path.read_text(encoding="utf-8")), path.name)

    def test_fan_icons_divide_the_cluster_height(self):
        # L: 844x390 에서 칸 195px 에 더미 318px, 위 아이콘이 제목을 41px 덮었다
        self.assertIn("container-type:size", rule(self.hub, ".cluster"))
        img = rule(self.hub, ".fan img")
        self.assertIn("calc((100cqh - (var(--rows) - 1) * 10px) / var(--rows))", img)
        self.assertIn("calc((100cqw - (var(--rows) - 1) * 10px) / var(--rows))", img)
        self.assertIn("min(var(--ic),", img)
        self.assertIn("--ic:72px", rule(self.hub, ".fan"))
        self.assertIn("--ic:54px", rule(self.hub, ".fan", "(max-width:720px)"))
        self.assertNotIn("width:72px;height:72px", self.hub)

    def test_quiet_row_wraps_instead_of_squeezing(self):
        # Q: 출시 전 아이콘이 6개부터 37x48px 로 찌그러졌다
        self.assertIn("flex-wrap:wrap", rule(self.hub, ".quiet"))
        self.assertIn("flex:none", rule(self.hub, ".qslot"))

    def test_language_menu_scrolls_inside_the_screen(self):
        # AE: 667x375 에서 언어 8개 중 2개가 화면 밖이라 닿을 수 없었다
        for css in (self.hub, render.css(self.site)):
            menu = rule(css, ".lang ul")
            self.assertIn("max-height:calc(100dvh - 76px)", menu)
            self.assertIn("overflow-y:auto", menu)

    def test_piece_name_is_text(self):
        # N: 판마다 이름 링크와 '자세히 보기'가 같은 주소라 Tab 이 앱당 4회였다
        html = render.render_hub(grow(Site(make_site()), 3), "ko")
        self.assertNotIn("<h2><a", html)
        for slug in ("demo", "demo2", "demo3"):
            self.assertEqual(html.count(f'href="/ko/{slug}/"'), 1)
        self.assertNotIn(".cap h2 a", self.hub)


class ShortcutTest(unittest.TestCase):
    """10-25 사용성 제안 4단계(원인 ③): 앱 사이, 문서 안 지름길."""

    def setUp(self):
        self.site = Site(make_site())
        self.sub = render.css(self.site)
        self.js = render.text(self.site, "page.js")

    def test_fan_icons_link_to_their_plates(self):
        # O: 첫 화면 더미 아이콘이 다 보이지만 누를 수 없어 8번째 판까지 390x844 스크롤 5388px, Tab 25회
        html = render.render_hub(grow(Site(make_site(unreleased=True)), 3), "ko")
        fan = re.search(r'<div class="fan" style="--rows:\d+">(.*?)</div>', html).group(1)
        self.assertNotIn('<div class="cluster" aria-hidden', html)
        links = re.findall(r'<a href="#([^"]+)"><img [^>]*alt="([^"]+)"', fan)
        self.assertEqual(links, [("demo", "Demo"), ("demo2", "Demo2"), ("demo3", "Demo3")])
        for slug, _ in links:
            self.assertIn(f'<article class="piece" id="{slug}">', html)
        self.assertNotIn('href="#soon"', html)                           # 출시 전 앱은 흐린 그림 그대로
        self.assertIn('alt="" width="72" height="72" class="soon">', fan)
        self.assertIn(".fan a{display:block", render.css(self.site, hub=True))

    def test_other_app_is_reached_through_the_wordmark_and_fan(self):
        # T: 앱 쪽에서 다른 앱으로 가는 새 목록은 두지 않고 낱말표(허브) 다음 더미 링크로 간다
        site = grow(Site(make_site()), 2)
        support = render.render_support(site, "ko", "demo")
        self.assertIn('<a class="wm" href="/ko/">', support)
        self.assertEqual(support.count('href="/ko/demo2/'), 0)
        self.assertIn('<a href="#demo2">', render.render_hub(site, "ko"))

    def test_privacy_toc_folds_on_narrow_screens(self):
        # E: 900px 이하에서 목차를 통째로 숨겨 de 390폭 12절 7291px 에 목차 0개였다
        html = render.render_privacy(self.site, "en", "demo")
        self.assertIn('<nav class="toc" aria-label="en toc"><details open><summary>en toc</summary><ol><li><a href="#p1">', html)   # JS 가 없어도 펼친 채
        narrow = rule(self.sub, ".toc", "(max-width:900px)")
        self.assertNotIn("display:none", narrow)
        self.assertIn("position:static", narrow)
        self.assertIn("min-height:44px", rule(self.sub, ".toc summary", "(max-width:900px)"))
        self.assertIn("matchMedia('(min-width:901px)')", self.js)      # 넓은 화면에서는 늘 펼친다
        self.assertIn("if(wide.matches)e.preventDefault()", self.js)   # 넓은 화면에서는 제목을 눌러도 접히지 않는다
        self.assertIn("head.tabIndex=-1", self.js)                     # 넓은 화면에서는 Tab 이 제목을 건너뛴다
        self.assertIn("cursor:default", rule(self.sub, ".toc summary"))
        self.assertIn("cursor:pointer", rule(self.sub, ".toc summary", "(max-width:900px)"))
        self.assertIn(".toc", self.sub.split("@media print{")[1].split("{")[0])   # 인쇄에서는 그대로 뺀다

    def test_faq_answers_have_addresses(self):
        # AD: 지원 답에 주소가 없어 #q7 같은 링크로 답을 가리킬 수 없었다
        site = Site(make_site())
        site.copy[("demo", "en")] = site.copy[("demo", "en")] | {"faq": [{"q": f"q{i}", "a": ["a"]} for i in range(1, 8)]}
        html = render.render_support(site, "en", "demo")
        self.assertEqual(re.findall(r'<details id="(q\d+)">', html), [f"q{i}" for i in range(1, 8)])
        self.assertIn("addEventListener('hashchange',reveal)", self.js)
        self.assertIn("d.tagName==='DETAILS')d.open=true", self.js)
        self.assertNotIn("decodeURIComponent", self.js)   # '#100%' 같은 주소가 URIError 로 아래 처리기를 막지 않게


if __name__ == "__main__":
    unittest.main()
