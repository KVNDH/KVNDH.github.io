from __future__ import annotations

import json
import re
import unittest

from tests.fixture import look, make_site, store, write
import render
from sitelib import Site


class HubTest(unittest.TestCase):
    def setUp(self):
        self.site = Site(make_site())

    def test_hub_piece_links_page_and_store(self):
        html = render.render_hub(self.site, "ko")
        self.assertIn('<html lang="ko">', html)
        self.assertIn('<article class="piece" id="demo">', html)
        self.assertIn('<h2><a href="/ko/demo/">Demo</a></h2>', html)
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

    def test_hub_has_no_summary_sentence(self):
        html = render.render_hub(self.site, "ko")
        self.assertIn('<h1 class="sr-only">ko hubMetaTitle</h1>', html)
        self.assertIn('<meta name="description" content="Demo">', html)

    def test_hub_footer_lists_privacy_and_languages(self):
        html = render.render_hub(self.site, "ko")
        self.assertIn('<footer class="foot">', html)
        self.assertIn('href="/ko/demo/privacy/"', html)
        self.assertIn('<ul class="langs">', html)
        # 10-25: 처리방침은 언어 다음, 맨 아래 한 줄 전체(.fpv)에 옆으로 흐르는 목록(.flow)
        self.assertIn('<div class="fpv"><h2>ko navPrivacy</h2><ul class="flow">', html)
        self.assertLess(html.index('class="langs"'), html.index('class="fpv"'))
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
        fan = re.search(r'<div class="fan">(.*?)</div>', html).group(1)
        self.assertTrue(fan.startswith('<span class="row"><img src="/assets/demo/icon-180.webp"'))
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
        self.assertIn("ko notFound", html)

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

    def test_contact_buttons_keep_their_width(self):
        # I: 1280폭 es 지원 '연락' 칸(124px)이 메일 단추(167px)보다 좁았다
        self.assertIn("min-width:auto", rule(self.sub, ".help div:last-child"))
        self.assertIn("min-width:0", rule(self.sub, ".help>div"))   # 왼쪽 안내문은 그대로 줄어든다


if __name__ == "__main__":
    unittest.main()
