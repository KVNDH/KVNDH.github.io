# kvndh.com 사이트 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 출시 앱 5개의 소개, 지원, 개인정보 처리방침을 8개 언어로 담은 정적 사이트를 `kvndh.com` 에 배포한다.

**Architecture:**
- `content/` 의 JSON 과 `templates/` 의 `string.Template` 을 `scripts/build.py` 가 `docs/` 로 렌더링하고, GitHub Pages 가 `main /docs` 를 공개한다
- `scripts/check.py` 가 문구 규칙, 구조, 사실, 출력물(링크, 필수 파일, 최신 여부)을 검사한다
- 0단계 뼈대는 HQ 가 만들고, 문구와 번역, 검토는 에이전트가 나눠 맡는다

**Tech Stack:** Python 3.9 표준 라이브러리(unittest, string.Template, html.parser), ImageMagick(`magick`, 자산 가져오기에만), Google Chrome headless(화면 확인), gh CLI

**Spec:** `_design/specs/2026-09-17-kvndh-site-design.md`

## Global Constraints

- **Python 3.9**
  - 모든 모듈 첫 줄 아래에 `from __future__ import annotations` 를 둔다
  - `match` 문과 3.10 이상 문법은 쓰지 않는다
  - 외부 패키지는 쓰지 않는다
- **테스트:** `python3 -m unittest discover -s tests -v` (저장소 루트에서)
- **작업 브랜치:** `site-v1`. `main` 은 배포 태스크 전까지 건드리지 않는다
- **커밋 메시지:** 한국어이고, 끝에 `Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>`
- **언어 코드:** `ko en ja zh-hans zh-hant de es pt-br`
- **앱 슬러그:** `brushworks life-tyde snapline tapey dice-master`
- **페이지 주소:** `/<lang>/`, `/<lang>/<app>/`, `/<lang>/<app>/support/`, `/<lang>/<app>/privacy/`. 최상위 `docs/support/` 는 만들지 않는다
- **리소스:**
  - 외부 CDN, 웹폰트, 원격 이미지, 외부 스타일시트는 쓰지 않는다
  - CSS 는 페이지마다 인라인으로 넣는다
  - 스크립트는 `/` 의 언어 이동 하나만 쓴다
- **출력 필수:** `docs/` 에 `CNAME`(`kvndh.com`), `app-ads.txt`, `.nojekyll`, `404.html`, `robots.txt`, `sitemap.xml` 이 있어야 한다
- **문구:** 스펙 3절과 3-1절(문장 계약)을 따른다
  - 개발자 자기소개 금지
  - "기기 밖" 계열 표현 금지
  - AI 상투어 금지
  - `·`, 전각대시(U+2014), `【】`, 느낌표 금지
  - ko 는 문단 합니다체, 불릿은 명사형으로 끝낸다
- **개인정보 처리방침:** 12개 절, 한국 표준 목차 순서(스펙 5절)
- **색:** 바탕 `#0A0A0B`, 개인정보 처리방침 종이 면 `#F5F3EE`
  - 앱 강조색: brushworks `#A05B42`/`#E39C80`, life-tyde `#E33C48`/`#F46A74`, snapline `#F9F9F9`/`#F9F9F9`, tapey `#CBD3B6`/`#CBD3B6`, dice-master `#EE9D1C`/`#EE9D1C`
- **문의 메일:** `kvndh36@naver.com`

---

## 파일 구조

| 파일 | 책임 |
|---|---|
| `scripts/sitelib.py` | 콘텐츠 읽기(`Site`), 주소(`page_path`), 이스케이프 |
| `scripts/render.py` | 페이지 한 장씩 HTML 만들기 |
| `scripts/build.py` | 전체를 `docs/` 로 쓰기, 정적 파일과 자산 복사, sitemap |
| `scripts/check.py` | 문구, 구조, 사실, 출력물 검사. 종료 코드 |
| `scripts/import_assets.py` | 앱 저장소의 아이콘과 스크린샷을 WebP 로 가져오기 (ImageMagick) |
| `templates/*.html`, `templates/style.css` | 틀과 스타일 |
| `content/site.json`, `content/i18n/<lang>.json`, `content/apps/<app>/{facts,<lang>}.json`, `content/asset-sources.json` | 콘텐츠 |
| `static/` | `docs/` 로 그대로 복사하는 파일 |
| `tests/fixture.py`, `tests/test_*.py` | 임시 사이트를 만드는 도우미와 테스트 |

---

### Task 1: 콘텐츠 읽기와 주소 (`sitelib.py`)

**Files:**
- Create: `scripts/sitelib.py`
- Create: `tests/__init__.py` (빈 파일)
- Create: `tests/fixture.py`
- Test: `tests/test_sitelib.py`
- Create: `templates/.gitkeep` (Task 2 전까지 fixture 의 `copytree` 가 실패하지 않게)

**Interfaces:**
- Produces:
  - `Site(root: Path)` 의 속성: `.root`, `.config`, `.langs`, `.ui: dict[str, dict]`, `.apps: list[dict]`, `.copy: dict[tuple[str, str], dict]`, `.facts: dict[str, dict | None]`, `.base_url`
  - `Site` 의 메서드: `.lang_codes() -> list[str]`, `.lang(code) -> dict`, `.app(slug) -> dict`, `.app_copy(slug, lang) -> dict | None`, `.has_pages(slug, lang) -> bool`, `.page_langs(slug | None) -> list[str]`
  - `page_path(lang, slug=None, kind="about") -> str`
  - `esc(text) -> str`, `load_json(path) -> dict`, `app_store_url(app_id) -> str`
  - 상수 `ROOT`, `PAGE_KINDS`, `PRIVACY_SECTION_COUNT = 12`
  - `tests/fixture.py`: `make_site(langs=("ko","en"), with_pages=True) -> Path`, `write(path, data)`, `REPO`

- [ ] **Step 1: fixture 와 실패하는 테스트를 쓴다**

`tests/__init__.py` 는 빈 파일로 만든다.

`tests/fixture.py`:

```python
"""테스트용 임시 사이트를 만든다."""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

UI_KEYS = [
    "skip", "language", "hubMetaTitle", "hubTitle", "hubLead", "learnMore", "getOnAppStore",
    "screenshot", "navAbout", "navSupport", "navPrivacy", "free", "pro", "faqTitle",
    "contactTitle", "contactBody", "effectiveDate", "toc", "notFound",
]


def write(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


def ui(lang: str) -> dict:
    return {k: f"{lang} {k}" for k in UI_KEYS}


def privacy(lang: str) -> dict:
    return {
        "title": f"{lang} privacy",
        "effectiveDate": "2026-09-17",
        "intro": ["intro"],
        "sections": [{"title": f"s{i}", "paragraphs": ["p"], "bullets": []} for i in range(1, 13)],
    }


def app_copy(lang: str) -> dict:
    return {
        "name": "Demo",
        "subtitle": "sub",
        "summary": "summary",
        "hero": {"hook": "hook", "points": ["point"]},
        "sections": [{"title": "title", "body": ["b"], "bullets": ["x"]}],
        "pro": {"title": "Pro", "body": ["pb"], "free": ["f"], "pro": ["p"], "note": "n"},
        "faq": [{"q": "q", "a": ["a"]}],
        "privacy": privacy(lang),
    }


def make_site(langs=("ko", "en"), with_pages: bool = True) -> Path:
    root = Path(tempfile.mkdtemp(prefix="kvndh-site-"))
    shutil.copytree(REPO / "templates", root / "templates")
    content = root / "content"
    write(content / "site.json", {
        "baseUrl": "https://kvndh.com",
        "contact": "kvndh36@naver.com",
        "languages": [
            {"code": "ko", "htmlLang": "ko", "hreflang": "ko", "label": "한국어", "ogLocale": "ko_KR"},
            {"code": "en", "htmlLang": "en", "hreflang": "en", "label": "English", "ogLocale": "en_US"},
            {"code": "ja", "htmlLang": "ja", "hreflang": "ja", "label": "日本語", "ogLocale": "ja_JP"},
        ],
        "apps": [{"slug": "demo", "appStoreId": "123", "accent": "#A05B42",
                  "accentText": "#E39C80", "featured": True}],
    })
    for lang in langs:
        write(content / "i18n" / f"{lang}.json", ui(lang))
        copy = app_copy(lang) if with_pages else {"name": "Demo", "subtitle": "sub", "summary": "summary"}
        write(content / "apps" / "demo" / f"{lang}.json", copy)
    write(content / "apps" / "demo" / "facts.json", {"describesVersion": "1.0.0", "numbers": [], "ads": False})
    for rel in ("assets/demo/icon-180.webp", "assets/demo/icon-360.webp", "assets/demo/og.jpg",
                "assets/demo/shots/en/01.webp", "assets/og.jpg"):
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"x")
    static = root / "static"
    static.mkdir()
    (static / "CNAME").write_text("kvndh.com\n")
    (static / "app-ads.txt").write_text("google.com, pub-0, DIRECT, f08c47fec0942fa0\n")
    (static / ".nojekyll").write_text("")
    (static / "robots.txt").write_text("User-agent: *\nAllow: /\n")
    return root
```

`tests/test_sitelib.py`:

```python
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
```

- [ ] **Step 2: 실패를 확인한다**

Run: `mkdir -p templates && touch templates/.gitkeep && python3 -m unittest discover -s tests -v`
Expected: `ModuleNotFoundError: No module named 'sitelib'`

- [ ] **Step 3: `scripts/sitelib.py` 를 쓴다**

```python
"""kvndh.com 콘텐츠를 읽고 주소를 만든다. 표준 라이브러리만 쓴다."""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGE_KINDS = ("about", "support", "privacy")
PRIVACY_SECTION_COUNT = 12


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def app_store_url(app_id: str) -> str:
    return f"https://apps.apple.com/app/id{app_id}"


def page_path(lang: str, slug: str | None = None, kind: str = "about") -> str:
    """사이트 안 경로. 항상 / 로 시작하고 / 로 끝난다."""
    if kind not in PAGE_KINDS:
        raise ValueError(f"unknown page kind: {kind}")
    if slug is None:
        return f"/{lang}/"
    if kind == "about":
        return f"/{lang}/{slug}/"
    return f"/{lang}/{slug}/{kind}/"


class Site:
    """content/ 를 읽은 결과. i18n 파일이 있는 언어만 활성이다."""

    def __init__(self, root: Path = ROOT):
        self.root = root
        content = root / "content"
        self.config = load_json(content / "site.json")
        self.langs = [
            lang for lang in self.config["languages"]
            if (content / "i18n" / f"{lang['code']}.json").exists()
        ]
        self.ui = {lang["code"]: load_json(content / "i18n" / f"{lang['code']}.json") for lang in self.langs}
        self.apps = self.config["apps"]
        self.copy: dict[tuple[str, str], dict] = {}
        self.facts: dict[str, dict | None] = {}
        for app in self.apps:
            folder = content / "apps" / app["slug"]
            facts = folder / "facts.json"
            self.facts[app["slug"]] = load_json(facts) if facts.exists() else None
            for lang in self.langs:
                path = folder / f"{lang['code']}.json"
                if path.exists():
                    self.copy[(app["slug"], lang["code"])] = load_json(path)

    @property
    def base_url(self) -> str:
        return self.config["baseUrl"]

    def lang_codes(self) -> list[str]:
        return [lang["code"] for lang in self.langs]

    def lang(self, code: str) -> dict:
        return next(lang for lang in self.langs if lang["code"] == code)

    def app(self, slug: str) -> dict:
        return next(app for app in self.apps if app["slug"] == slug)

    def app_copy(self, slug: str, lang: str) -> dict | None:
        return self.copy.get((slug, lang))

    def has_pages(self, slug: str, lang: str) -> bool:
        copy = self.app_copy(slug, lang)
        return bool(copy) and "sections" in copy

    def page_langs(self, slug: str | None) -> list[str]:
        """이 페이지가 있는 언어들. hreflang 에 쓴다."""
        if slug is None:
            return self.lang_codes()
        return [code for code in self.lang_codes() if self.has_pages(slug, code)]
```

- [ ] **Step 4: 통과를 확인한다**

Run: `python3 -m unittest discover -s tests -v`
Expected: 6 tests OK

- [ ] **Step 5: 커밋한다**

```bash
git add scripts/sitelib.py tests/ templates/.gitkeep
git commit -m "사이트 콘텐츠를 읽고 주소를 만드는 sitelib 을 둔다"
```

---

### Task 2: 템플릿과 페이지 렌더링 (`render.py`)

**Files:**
- Create: `templates/base.html`, `templates/hub.html`, `templates/tile.html`, `templates/app.html`, `templates/pro.html`, `templates/support.html`, `templates/privacy.html`, `templates/root.html`, `templates/404.html`, `templates/style.css`
- Delete: `templates/.gitkeep`
- Create: `scripts/render.py`
- Test: `tests/test_render.py`

**Interfaces:**
- Consumes: Task 1 의 `Site`, `page_path`, `esc`, `app_store_url`
- Produces:
  - 렌더 함수(모두 `-> str`): `render_hub(site, lang)`, `render_app(site, lang, slug)`, `render_support(site, lang, slug)`, `render_privacy(site, lang, slug)`, `render_root(site)`, `render_404(site)`, `render_sitemap(site, paths: list[str])`
  - `shot_path(site, slug, lang, index=1) -> str`: 없으면 `FileNotFoundError`
- 콘텐츠 스키마: `content/apps/<app>/<lang>.json`

  ```json
  {"name": "", "subtitle": "", "summary": "",
   "hero": {"hook": "", "points": [""]},
   "sections": [{"title": "", "body": [""], "bullets": [""]}],
   "pro": {"title": "", "body": [""], "free": [""], "pro": [""], "note": ""},
   "faq": [{"q": "", "a": [""]}],
   "privacy": {"title": "", "effectiveDate": "YYYY-MM-DD", "intro": [""],
               "sections": [{"title": "", "paragraphs": [""], "bullets": []}]}}
  ```

  - `pro` 는 `null` 이 될 수 있다
  - 카드만 있는 파일은 `name`, `subtitle`, `summary` 만 가진다
- UI 키: `tests/fixture.py` 의 `UI_KEYS` 와 같다

- [ ] **Step 1: 실패하는 테스트를 쓴다**

`tests/test_render.py`:

```python
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
```

- [ ] **Step 2: 실패를 확인한다**

Run: `python3 -m unittest tests.test_render -v`
Expected: `ModuleNotFoundError: No module named 'render'`

- [ ] **Step 3: 템플릿을 쓴다** (`rm templates/.gitkeep`)

`templates/base.html`:

```html
<!DOCTYPE html>
<html lang="$html_lang">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>$title</title>
<meta name="description" content="$description">
<link rel="canonical" href="$canonical">
$alternates
<meta property="og:type" content="website">
<meta property="og:title" content="$title">
<meta property="og:description" content="$description">
<meta property="og:url" content="$canonical">
<meta property="og:image" content="$og_image">
<meta property="og:locale" content="$og_locale">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#0A0A0B">
$extra_head
<style>$css</style>
</head>
<body style="$body_style">
<a class="skip" href="#main">$skip_label</a>
<header class="site-head">
  <a class="wordmark" href="$hub_path">kvndh</a>
  $lang_menu
</header>
<main id="main">
$content
</main>
<footer class="site-foot">
$footer
</footer>
</body>
</html>
```

`templates/hub.html`:

```html
<div class="wrap">
  <section class="hub-intro">
    <h1>$title</h1>
    <p>$lead</p>
  </section>
  <div class="bento">
$tiles
  </div>
</div>
```

`templates/tile.html`:

```html
<article class="tile$featured" style="$style">
  <div class="tile__head">
    <img class="tile__icon" src="$icon" alt="" width="56" height="56">
    <div>
      <h2>$name</h2>
      <p class="tile__sub">$subtitle</p>
    </div>
  </div>
  <p class="tile__summary">$summary</p>
  <div class="tile__links">$more<a class="btn btn--primary" href="$store">$get</a></div>
  <img class="tile__shot" src="$shot" alt="$shot_alt" width="330" height="717" loading="lazy">
</article>
```

`templates/app.html`:

```html
<div class="wrap">
  $tabs
  <section class="app-hero">
    <div>
      <img class="app-hero__icon" src="$icon" alt="" width="88" height="88">
      <h1>$name</h1>
      <p class="app-hero__sub">$subtitle</p>
      <p class="app-hero__hook">$hook</p>
      <ul class="app-hero__points">$points</ul>
      <a class="btn btn--primary" href="$store">$get</a>
    </div>
    <div class="device"><img src="$shot" alt="$shot_alt" width="330" height="717"></div>
  </section>
  $sections
  $pro
</div>
```

`templates/pro.html`:

```html
<section class="pro">
  <h2>$title</h2>
  $body
  <div class="pro__grid">
    <div class="pro__col"><h3>$free_label</h3><ul class="list">$free</ul></div>
    <div class="pro__col pro__col--pro"><h3>$pro_label</h3><ul class="list">$pro</ul></div>
  </div>
  <p class="pro__note">$note</p>
</section>
```

`templates/support.html`:

```html
<div class="wrap">
  $tabs
  <h1 class="page-title">$title</h1>
  <section class="faq" aria-labelledby="faq-title">
    <h2 id="faq-title">$faq_title</h2>
    $faq
  </section>
  <section class="contact">
    <h2>$contact_title</h2>
    <p>$contact_body</p>
    <p><a class="btn" href="mailto:$email">$email</a></p>
  </section>
</div>
```

`templates/privacy.html`:

```html
<div class="wrap">
  $tabs
  <div class="paper">
    <div class="paper__inner">
      <nav class="toc" aria-label="$toc_label"><strong>$toc_label</strong><ol>$toc</ol></nav>
      <article>
        <h1>$title</h1>
        <p class="meta">$meta</p>
        $intro
        $body
      </article>
    </div>
  </div>
</div>
```

`templates/root.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>kvndh</title>
<link rel="canonical" href="$base/">
<script>
(function () {
  var have = $langs_json;
  var wanted = navigator.languages || [navigator.language || "en"];
  for (var i = 0; i < wanted.length; i++) {
    var tag = String(wanted[i]).toLowerCase();
    var code = tag.split("-")[0];
    if (code === "zh") { code = /hant|tw|hk|mo/.test(tag) ? "zh-hant" : "zh-hans"; }
    if (code === "pt") { code = "pt-br"; }
    if (have.indexOf(code) !== -1) { location.replace("/" + code + "/"); return; }
  }
  location.replace("/" + (have.indexOf("en") !== -1 ? "en" : have[0]) + "/");
})();
</script>
<style>$css</style>
</head>
<body>
<main class="wrap center">
  <p class="wordmark">kvndh</p>
  <ul class="lang-list">$items</ul>
</main>
</body>
</html>
```

`templates/404.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>404 | kvndh</title>
<style>$css</style>
</head>
<body>
<main class="wrap center">
  <a class="wordmark" href="/">kvndh</a>
  <h1 class="page-title">404</h1>
  $messages
  <ul class="lang-list">$items</ul>
</main>
</body>
</html>
```

`templates/style.css`:

```css
:root{--bg:#0A0A0B;--surface:#141416;--line:#26262A;--text:#F2F2F3;--muted:#A3A3AA;--accent:#F2F2F3;--accent-text:#F2F2F3;--paper:#F5F3EE;--ink:#1C1B19;--ink-muted:#5E5A52;--radius:22px;--max:1200px}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--text);font:16px/1.7 -apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Hiragino Sans","PingFang SC","PingFang TC","Segoe UI",Roboto,"Noto Sans",sans-serif;word-break:keep-all;overflow-wrap:anywhere}
a{color:inherit}
a:focus-visible,summary:focus-visible{outline:2px solid var(--accent-text);outline-offset:3px;border-radius:6px}
img{max-width:100%;height:auto;display:block}
h1,h2,h3{text-wrap:balance}
.skip{position:absolute;left:-999px;top:0}
.skip:focus{left:16px;top:12px;background:var(--text);color:var(--bg);padding:8px 12px;border-radius:8px;z-index:10}
.wrap{max-width:var(--max);margin:0 auto;padding:0 24px}
.site-head{max-width:var(--max);margin:0 auto;padding:20px 24px;display:flex;align-items:center;justify-content:space-between;gap:16px}
.wordmark{font-weight:700;font-size:20px;letter-spacing:-.02em;text-decoration:none;margin:0}
.lang-menu{position:relative;font-size:14px}
.lang-menu summary{cursor:pointer;list-style:none;padding:6px 14px;border:1px solid var(--line);border-radius:999px;color:var(--muted)}
.lang-menu summary::-webkit-details-marker{display:none}
.lang-menu ul{position:absolute;right:0;top:calc(100% + 8px);margin:0;padding:8px;list-style:none;background:var(--surface);border:1px solid var(--line);border-radius:14px;min-width:190px;z-index:5}
.lang-menu li a{display:block;padding:8px 12px;border-radius:8px;text-decoration:none}
.lang-menu li a:hover{background:var(--line)}
.lang-menu li a[aria-current]{color:var(--accent-text);font-weight:600}
.hub-intro{padding:56px 0 40px}
.hub-intro h1{font-size:clamp(34px,6vw,64px);line-height:1.15;letter-spacing:-.03em;margin:0 0 16px}
.hub-intro p{color:var(--muted);margin:0;max-width:40em}
.bento{display:grid;gap:16px;grid-template-columns:repeat(4,1fr);padding-bottom:72px}
.tile{position:relative;overflow:hidden;background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);padding:24px;min-height:320px;display:flex;flex-direction:column;isolation:isolate}
.tile::after{content:"";position:absolute;right:-30%;bottom:-40%;width:90%;height:90%;background:radial-gradient(closest-side,var(--accent),transparent);opacity:.28;z-index:-1;pointer-events:none}
.tile--featured{grid-column:span 2;grid-row:span 2;min-height:660px}
.tile__head{display:flex;gap:14px;align-items:center}
.tile__icon{width:56px;height:56px;border-radius:13px}
.tile h2{font-size:22px;margin:0;letter-spacing:-.01em}
.tile__sub{color:var(--accent-text);font-size:14px;margin:2px 0 0}
.tile__summary{color:var(--muted);margin:16px 0 0;font-size:15px}
.tile__links{display:flex;gap:10px;margin-top:18px;flex-wrap:wrap;position:relative;z-index:1}
.tile__shot{margin-top:auto;align-self:center;width:62%;max-width:240px;border-radius:24px;transform:translateY(30%);box-shadow:0 20px 60px rgba(0,0,0,.5)}
.tile--featured .tile__shot{width:62%;max-width:380px;transform:translateY(6%)}
.btn{display:inline-flex;align-items:center;gap:6px;padding:10px 16px;border-radius:999px;border:1px solid var(--line);text-decoration:none;font-size:14px;font-weight:600;background:rgba(10,10,11,.6)}
.btn--primary{background:var(--accent-text);color:#0A0A0B;border-color:transparent}
.tabs{display:flex;gap:4px;border-bottom:1px solid var(--line);margin:8px 0 0;overflow-x:auto}
.tabs a{padding:12px 14px;text-decoration:none;color:var(--muted);border-bottom:2px solid transparent;white-space:nowrap}
.tabs a[aria-current]{color:var(--text);border-color:var(--accent-text)}
.app-hero{display:grid;grid-template-columns:1.1fr .9fr;gap:48px;align-items:center;padding:48px 0 64px}
.app-hero__icon{width:88px;height:88px;border-radius:20px}
.app-hero h1{font-size:clamp(44px,8vw,96px);line-height:1;letter-spacing:-.04em;margin:20px 0 12px}
.app-hero__sub{color:var(--accent-text);font-size:20px;margin:0 0 20px}
.app-hero__hook{font-size:18px;margin:0 0 24px;max-width:32em}
.app-hero__points{list-style:none;padding:0;margin:0 0 28px;color:var(--muted);display:flex;flex-wrap:wrap;gap:8px 20px;font-size:14px}
.device{justify-self:center;width:min(340px,80vw);padding:10px;border-radius:48px;background:#1B1B1E;border:1px solid var(--line);box-shadow:0 0 140px -30px var(--accent)}
.device img{border-radius:38px}
.feature{display:grid;grid-template-columns:1fr 1.4fr;gap:40px;padding:48px 0;border-top:1px solid var(--line)}
.feature h2{font-size:28px;letter-spacing:-.02em;margin:0}
.feature p{margin:0 0 14px}
.list{margin:0;padding:0;list-style:none}
.list li{padding:10px 0;border-bottom:1px solid var(--line)}
.pro{margin:24px 0 80px;padding:32px;border-radius:var(--radius);background:var(--surface);border:1px solid var(--line)}
.pro h2{margin:0 0 8px;font-size:28px}
.pro p{margin:0}
.pro__grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:20px}
.pro__col{padding:20px;border-radius:16px;border:1px solid var(--line)}
.pro__col--pro{border-color:var(--accent-text)}
.pro__col h3{margin:0 0 8px;font-size:16px}
.pro .pro__note{color:var(--muted);margin:16px 0 0;font-size:14px}
.page-title{font-size:clamp(32px,5vw,48px);letter-spacing:-.03em;margin:40px 0 24px}
.faq{margin:0 0 48px}
.faq h2{font-size:20px}
.faq details{border-top:1px solid var(--line)}
.faq summary{cursor:pointer;padding:16px 0;font-weight:600;list-style:none}
.faq summary::-webkit-details-marker{display:none}
.faq details p{margin:0 0 16px;color:var(--muted)}
.contact{padding:28px;border-radius:var(--radius);background:var(--surface);border:1px solid var(--line);margin-bottom:80px}
.contact h2{margin:0 0 8px;font-size:20px}
.paper{background:var(--paper);color:var(--ink);border-radius:var(--radius);margin:24px 0 80px;padding:56px 24px}
.paper__inner{max-width:65ch;margin:0 auto}
.paper h1{font-size:clamp(28px,4vw,40px);letter-spacing:-.02em;margin:0 0 8px}
.paper .meta{color:var(--ink-muted);margin:0 0 32px;font-size:14px}
.paper h2{font-size:19px;margin:40px 0 10px}
.paper p,.paper li{font-size:17px;line-height:1.85}
.paper a{color:var(--ink)}
.paper a:focus-visible{outline-color:var(--ink)}
.toc{border:1px solid #D9D5CC;border-radius:14px;padding:16px 20px;margin:0 0 32px;font-size:15px}
.toc ol{margin:8px 0 0;padding-left:22px}
.toc a{text-decoration:none}
.site-foot{border-top:1px solid var(--line);color:var(--muted);font-size:14px}
.site-foot .wrap{padding-top:32px;padding-bottom:40px;display:flex;flex-wrap:wrap;gap:12px 32px;justify-content:space-between}
.site-foot p{margin:0}
.site-foot ul{list-style:none;margin:0;padding:0;display:flex;flex-wrap:wrap;gap:8px 16px}
.site-foot a{color:var(--muted)}
.center{min-height:70vh;display:flex;flex-direction:column;justify-content:center;padding:48px 24px}
.lang-list{list-style:none;padding:0;margin:24px 0 0;display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:10px}
.lang-list a{display:block;padding:14px 18px;border:1px solid var(--line);border-radius:14px;text-decoration:none}
@media (max-width:900px){.bento{grid-template-columns:1fr 1fr}.tile--featured{grid-row:auto;min-height:560px}.app-hero,.feature{grid-template-columns:1fr}.app-hero{gap:32px}.feature{gap:16px}}
@media (max-width:560px){.bento{grid-template-columns:1fr}.tile--featured{grid-column:auto}.pro__grid{grid-template-columns:1fr}.paper{padding:36px 18px;border-radius:16px}.pro{padding:22px}}
@media (min-width:1100px){.paper__inner{max-width:none;display:grid;grid-template-columns:240px minmax(0,65ch);gap:48px;justify-content:center}.paper .toc{position:sticky;top:24px;align-self:start}}
@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important;scroll-behavior:auto!important}}
```

- [ ] **Step 4: `scripts/render.py` 를 쓴다**

```python
"""페이지 HTML 을 만든다. 틀은 templates/*.html (string.Template)."""
from __future__ import annotations

import json
from string import Template

from sitelib import Site, app_store_url, esc, page_path

KIND_UI_KEY = {"about": "navAbout", "support": "navSupport", "privacy": "navPrivacy"}


def tpl(site: Site, name: str) -> Template:
    return Template((site.root / "templates" / name).read_text(encoding="utf-8"))


def css(site: Site) -> str:
    return (site.root / "templates" / "style.css").read_text(encoding="utf-8")


def accent_style(app: dict) -> str:
    return f"--accent:{app['accent']};--accent-text:{app['accentText']}"


def asset(slug: str, name: str) -> str:
    return f"/assets/{slug}/{name}"


def shot_path(site: Site, slug: str, lang: str, index: int = 1) -> str:
    name = f"{index:02d}.webp"
    for code in (lang, "en", "ko"):
        if (site.root / "assets" / slug / "shots" / code / name).exists():
            return asset(slug, f"shots/{code}/{name}")
    raise FileNotFoundError(f"no screenshot {name} for {slug}")


def items(values: list[str]) -> str:
    return "".join(f"<li>{esc(v)}</li>" for v in values)


def paragraphs(values: list[str]) -> str:
    return "".join(f"<p>{esc(v)}</p>" for v in values)


def alternates(site: Site, slug: str | None, kind: str) -> str:
    langs = site.page_langs(slug)
    tags = [
        f'<link rel="alternate" hreflang="{esc(site.lang(code)["hreflang"])}" '
        f'href="{site.base_url}{page_path(code, slug, kind)}">'
        for code in langs
    ]
    default = "en" if "en" in langs else langs[0]
    tags.append(f'<link rel="alternate" hreflang="x-default" href="{site.base_url}{page_path(default, slug, kind)}">')
    return "\n".join(tags)


def lang_menu(site: Site, lang: str, slug: str | None, kind: str) -> str:
    available = site.page_langs(slug)
    entries = []
    for option in site.langs:
        code = option["code"]
        target = page_path(code, slug, kind) if code in available else page_path(code)
        current = ' aria-current="true"' if code == lang else ""
        entries.append(
            f'<li><a href="{target}" lang="{esc(option["htmlLang"])}" '
            f'hreflang="{esc(option["hreflang"])}"{current}>{esc(option["label"])}</a></li>'
        )
    return (
        f'<details class="lang-menu"><summary aria-label="{esc(site.ui[lang]["language"])}">'
        f'{esc(site.lang(lang)["label"])}</summary><ul>{"".join(entries)}</ul></details>'
    )


def footer(site: Site, lang: str) -> str:
    ui = site.ui[lang]
    email = site.config["contact"]
    links = "".join(
        f'<li><a href="{page_path(lang, app["slug"], "privacy")}">'
        f'{esc(site.app_copy(app["slug"], lang)["name"])} {esc(ui["navPrivacy"])}</a></li>'
        for app in site.apps if site.has_pages(app["slug"], lang)
    )
    return (
        f'<div class="wrap"><p>{esc(ui["contactTitle"])} <a href="mailto:{email}">{email}</a></p>'
        f"<ul>{links}</ul><p>© kvndh</p></div>"
    )


def tabs(site: Site, lang: str, slug: str, current: str) -> str:
    ui = site.ui[lang]
    links = []
    for kind in ("about", "support", "privacy"):
        mark = ' aria-current="page"' if kind == current else ""
        links.append(f'<a href="{page_path(lang, slug, kind)}"{mark}>{esc(ui[KIND_UI_KEY[kind]])}</a>')
    return f'<nav class="tabs" aria-label="{esc(site.app_copy(slug, lang)["name"])}">{"".join(links)}</nav>'


def page(site: Site, *, lang: str, slug: str | None, kind: str, title: str, description: str,
         content: str, body_style: str = "", extra_head: str = "", og_image: str = "/assets/og.jpg") -> str:
    option = site.lang(lang)
    return tpl(site, "base.html").substitute(
        html_lang=esc(option["htmlLang"]),
        title=esc(title),
        description=esc(description),
        canonical=site.base_url + page_path(lang, slug, kind),
        alternates=alternates(site, slug, kind),
        og_image=site.base_url + og_image,
        og_locale=esc(option["ogLocale"]),
        extra_head=extra_head,
        css=css(site),
        body_style=esc(body_style),
        skip_label=esc(site.ui[lang]["skip"]),
        hub_path=page_path(lang),
        lang_menu=lang_menu(site, lang, slug, kind),
        content=content,
        footer=footer(site, lang),
    )


def render_hub(site: Site, lang: str) -> str:
    ui = site.ui[lang]
    tiles = []
    for app in site.apps:
        slug = app["slug"]
        copy = site.app_copy(slug, lang)
        if not copy:
            continue
        more = (
            f'<a class="btn" href="{page_path(lang, slug)}">{esc(ui["learnMore"])}</a>'
            if site.has_pages(slug, lang) else ""
        )
        tiles.append(tpl(site, "tile.html").substitute(
            featured=" tile--featured" if app.get("featured") else "",
            style=esc(accent_style(app)),
            icon=asset(slug, "icon-180.webp"),
            name=esc(copy["name"]),
            subtitle=esc(copy["subtitle"]),
            summary=esc(copy["summary"]),
            more=more,
            store=app_store_url(app["appStoreId"]),
            get=esc(ui["getOnAppStore"]),
            shot=shot_path(site, slug, lang),
            shot_alt=esc(f'{copy["name"]} {ui["screenshot"]}'),
        ))
    content = tpl(site, "hub.html").substitute(
        title=esc(ui["hubTitle"]), lead=esc(ui["hubLead"]), tiles="\n".join(tiles),
    )
    return page(site, lang=lang, slug=None, kind="about", title=ui["hubMetaTitle"],
                description=ui["hubLead"], content=content)


def render_app(site: Site, lang: str, slug: str) -> str:
    ui, app, copy = site.ui[lang], site.app(slug), site.app_copy(slug, lang)
    sections = "".join(
        f'<section class="feature"><h2>{esc(s["title"])}</h2><div>{paragraphs(s["body"])}'
        + (f'<ul class="list">{items(s["bullets"])}</ul>' if s.get("bullets") else "")
        + "</div></section>"
        for s in copy["sections"]
    )
    pro = ""
    if copy.get("pro"):
        p = copy["pro"]
        pro = tpl(site, "pro.html").substitute(
            title=esc(p["title"]), body=paragraphs(p["body"]),
            free_label=esc(ui["free"]), free=items(p["free"]),
            pro_label=esc(ui["pro"]), pro=items(p["pro"]), note=esc(p["note"]),
        )
    content = tpl(site, "app.html").substitute(
        tabs=tabs(site, lang, slug, "about"),
        icon=asset(slug, "icon-360.webp"),
        name=esc(copy["name"]),
        subtitle=esc(copy["subtitle"]),
        hook=esc(copy["hero"]["hook"]),
        points=items(copy["hero"]["points"]),
        store=app_store_url(app["appStoreId"]),
        get=esc(ui["getOnAppStore"]),
        shot=shot_path(site, slug, lang),
        shot_alt=esc(f'{copy["name"]} {ui["screenshot"]}'),
        sections=sections,
        pro=pro,
    )
    return page(site, lang=lang, slug=slug, kind="about",
                title=f'{copy["name"]}: {copy["subtitle"]}', description=copy["summary"],
                content=content, body_style=accent_style(app),
                extra_head=f'<meta name="apple-itunes-app" content="app-id={app["appStoreId"]}">',
                og_image=asset(slug, "og.jpg"))


def render_support(site: Site, lang: str, slug: str) -> str:
    ui, app, copy = site.ui[lang], site.app(slug), site.app_copy(slug, lang)
    faq = "".join(
        f'<details><summary>{esc(f["q"])}</summary>{paragraphs(f["a"])}</details>' for f in copy["faq"]
    )
    title = f'{copy["name"]} {ui["navSupport"]}'
    content = tpl(site, "support.html").substitute(
        tabs=tabs(site, lang, slug, "support"),
        title=esc(title),
        faq_title=esc(ui["faqTitle"]),
        faq=faq,
        contact_title=esc(ui["contactTitle"]),
        contact_body=esc(ui["contactBody"]),
        email=site.config["contact"],
    )
    return page(site, lang=lang, slug=slug, kind="support", title=title, description=copy["summary"],
                content=content, body_style=accent_style(app), og_image=asset(slug, "og.jpg"))


def render_privacy(site: Site, lang: str, slug: str) -> str:
    ui, app, copy = site.ui[lang], site.app(slug), site.app_copy(slug, lang)
    policy = copy["privacy"]
    toc = "".join(
        f'<li><a href="#p{i}">{esc(s["title"])}</a></li>' for i, s in enumerate(policy["sections"], 1)
    )
    body = "".join(
        f'<section id="p{i}"><h2>{i}. {esc(s["title"])}</h2>{paragraphs(s["paragraphs"])}'
        + (f'<ul>{items(s["bullets"])}</ul>' if s.get("bullets") else "")
        + "</section>"
        for i, s in enumerate(policy["sections"], 1)
    )
    content = tpl(site, "privacy.html").substitute(
        tabs=tabs(site, lang, slug, "privacy"),
        toc_label=esc(ui["toc"]),
        toc=toc,
        title=esc(policy["title"]),
        meta=esc(f'{ui["effectiveDate"]} {policy["effectiveDate"]}'),
        intro=paragraphs(policy["intro"]),
        body=body,
    )
    return page(site, lang=lang, slug=slug, kind="privacy", title=policy["title"],
                description=policy["title"], content=content, body_style=accent_style(app),
                og_image=asset(slug, "og.jpg"))


def language_items(site: Site) -> str:
    return "".join(
        f'<li><a href="{page_path(option["code"])}" lang="{esc(option["htmlLang"])}">'
        f'{esc(option["label"])}</a></li>'
        for option in site.langs
    )


def render_root(site: Site) -> str:
    return tpl(site, "root.html").substitute(
        base=site.base_url, langs_json=json.dumps(site.lang_codes()), css=css(site), items=language_items(site),
    )


def render_404(site: Site) -> str:
    messages = "".join(
        f'<p lang="{esc(option["htmlLang"])}">{esc(site.ui[option["code"]]["notFound"])}</p>'
        for option in site.langs
    )
    return tpl(site, "404.html").substitute(css=css(site), messages=messages, items=language_items(site))


def render_sitemap(site: Site, paths: list[str]) -> str:
    urls = "".join(f"<url><loc>{site.base_url}{p}</loc></url>" for p in paths if p.endswith("/"))
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n'
    )
```

- [ ] **Step 5: 통과를 확인한다**

Run: `python3 -m unittest discover -s tests -v`
Expected: 19 tests OK

- [ ] **Step 6: 커밋한다**

```bash
git add templates scripts/render.py tests/test_render.py
git commit -m "C안 템플릿과 페이지 렌더러를 둔다"
```

---

### Task 3: 전체 빌드 (`build.py`)

**Files:**
- Create: `scripts/build.py`
- Test: `tests/test_build.py`

**Interfaces:**
- Consumes: Task 2 의 렌더 함수 전부
- Produces:
  - `build(site: Site, out: Path) -> list[str]`: 쓴 페이지 경로 목록을 돌려준다. `out` 을 비우고 새로 만든다
  - `snapshot(out: Path) -> dict[str, bytes]`

- [ ] **Step 1: 실패하는 테스트를 쓴다**

`tests/test_build.py`:

```python
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
```

- [ ] **Step 2: 실패를 확인한다**

Run: `python3 -m unittest tests.test_build -v`
Expected: `ModuleNotFoundError: No module named 'build'`

- [ ] **Step 3: `scripts/build.py` 를 쓴다**

```python
"""content/ + templates/ 를 docs/ 로 렌더링한다.

사용: python3 scripts/build.py
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import render  # noqa: E402
from sitelib import ROOT, Site, page_path  # noqa: E402


def _write(out: Path, path: str, html: str) -> None:
    target = out / path.lstrip("/")
    if path.endswith("/"):
        target = target / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html, encoding="utf-8")


def build(site: Site, out: Path) -> list[str]:
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    written: list[str] = []

    def emit(path: str, html: str) -> None:
        _write(out, path, html)
        written.append(path)

    emit("/", render.render_root(site))
    emit("/404.html", render.render_404(site))
    for lang in site.lang_codes():
        emit(page_path(lang), render.render_hub(site, lang))
        for app in site.apps:
            slug = app["slug"]
            if not site.has_pages(slug, lang):
                continue
            emit(page_path(lang, slug), render.render_app(site, lang, slug))
            emit(page_path(lang, slug, "support"), render.render_support(site, lang, slug))
            emit(page_path(lang, slug, "privacy"), render.render_privacy(site, lang, slug))
    for src in sorted((site.root / "static").iterdir()):
        shutil.copyfile(src, out / src.name)
    if (site.root / "assets").exists():
        shutil.copytree(site.root / "assets", out / "assets")
    (out / "sitemap.xml").write_text(render.render_sitemap(site, written), encoding="utf-8")
    return written


def snapshot(out: Path) -> dict[str, bytes]:
    return {str(p.relative_to(out)): p.read_bytes() for p in sorted(out.rglob("*")) if p.is_file()}


def main() -> int:
    written = build(Site(ROOT), ROOT / "docs")
    print(f"페이지 {len(written)}개 -> docs/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: 통과를 확인한다**

Run: `python3 -m unittest discover -s tests -v`
Expected: 22 tests OK

- [ ] **Step 5: 커밋한다**

```bash
git add scripts/build.py tests/test_build.py
git commit -m "docs/ 로 전체를 빌드하는 build.py 를 둔다"
```

---

### Task 4: 검사기 (`check.py`)

**Files:**
- Create: `scripts/check.py`
- Test: `tests/test_check.py`

**Interfaces:**
- Consumes: `Site`, `build.build`, `build.snapshot`
- Produces: 아래 함수는 모두 문제 문자열 목록을 돌려준다. 비어 있으면 통과다
  - `check_copy(site) -> list[str]`
  - `check_structure(site, release: bool) -> list[str]`
  - `check_facts(site) -> list[str]`
  - `check_output(site, out) -> list[str]`
  - `check_fresh(site, out) -> list[str]`
  - `main(argv) -> int`
- `facts.json` 스키마:

  ```json
  {"describesVersion": "", "purchase": "one-time|none", "ads": false, "account": false,
   "network": [""], "permissions": [""], "storage": [""], "numbers": [""], "sources": [""]}
  ```

- [ ] **Step 1: 실패하는 테스트를 쓴다**

`tests/test_check.py`:

```python
from __future__ import annotations

import unittest

from tests.fixture import make_site
import build
import check
from sitelib import Site


def site_with(lang: str, field: str, text: str) -> Site:
    site = Site(make_site())
    site.copy[("demo", lang)][field] = text
    return site


class CopyRulesTest(unittest.TestCase):
    def test_clean_copy_passes(self):
        self.assertEqual(check.check_copy(Site(make_site())), [])

    def test_banned_ko_phrases(self):
        for text in ["혁신적인 그림 앱", "지금 바로 받아 보세요", "사진은 기기 밖으로 나가지 않습니다",
                     "iOS 앱을 혼자 만듭니다", "단순한 필터가 아닙니다", "여러분의 사진"]:
            self.assertTrue(check.check_copy(site_with("ko", "summary", text)), text)

    def test_banned_en_phrases(self):
        for text in ["A seamless way to paint", "Not just a filter, but a canvas",
                     "Your photos never leave your device"]:
            self.assertTrue(check.check_copy(site_with("en", "summary", text)), text)

    def test_banned_characters(self):
        for text in ["위치·크기", "붓 — 나이프", "【안내】", "좋습니다!"]:
            self.assertTrue(check.check_copy(site_with("ko", "summary", text)), text)

    def test_ko_haeyo(self):
        self.assertTrue(check.check_copy(site_with("ko", "summary", "사진을 골라요.")))
        self.assertTrue(check.check_copy(site_with("ko", "summary", "바로 써요")))
        self.assertEqual(check.check_copy(site_with("ko", "summary", "필요한 것만 남깁니다.")), [])
        self.assertEqual(check.check_copy(site_with("ko", "summary", "메일로 보내 주세요.")), [])

    def test_ko_bullets_must_be_noun_endings(self):
        site = Site(make_site())
        site.copy[("demo", "ko")]["sections"][0]["bullets"] = ["붓이 세 자루입니다"]
        self.assertTrue(check.check_copy(site))
        site.copy[("demo", "ko")]["sections"][0]["bullets"] = ["붓 세 자루"]
        self.assertEqual(check.check_copy(site), [])

    def test_ui_strings_are_checked(self):
        site = Site(make_site())
        site.ui["ko"]["hubLead"] = "놀라운 앱"
        self.assertTrue(check.check_copy(site))


class StructureTest(unittest.TestCase):
    def test_matching_structure_passes(self):
        self.assertEqual(check.check_structure(Site(make_site()), release=False), [])

    def test_section_count_mismatch_fails(self):
        site = Site(make_site())
        site.copy[("demo", "en")]["sections"].append({"title": "x", "body": [], "bullets": []})
        self.assertTrue(check.check_structure(site, release=False))

    def test_privacy_needs_twelve_sections(self):
        site = Site(make_site())
        site.copy[("demo", "en")]["privacy"]["sections"].pop()
        self.assertTrue(check.check_structure(site, release=False))

    def test_missing_ui_key_fails(self):
        site = Site(make_site())
        del site.ui["en"]["toc"]
        self.assertTrue(check.check_structure(site, release=False))

    def test_release_requires_all_languages(self):
        self.assertTrue(check.check_structure(Site(make_site()), release=True))


class FactsTest(unittest.TestCase):
    def test_unknown_number_in_marketing_copy_fails(self):
        self.assertTrue(check.check_facts(site_with("ko", "summary", "붓 7자루")))

    def test_known_numbers_pass_with_separators(self):
        site = site_with("ko", "summary", "붓 7자루, 긴 변 3,072px, 1.5배")
        site.facts["demo"]["numbers"] = ["7", "3072", "1.5"]
        self.assertEqual(check.check_facts(site), [])

    def test_ads_app_privacy_must_name_admob(self):
        site = Site(make_site())
        site.facts["demo"]["ads"] = True
        self.assertTrue(check.check_facts(site))
        for lang in ("ko", "en"):
            site.copy[("demo", lang)]["privacy"]["sections"][8]["paragraphs"] = ["Google AdMob"]
        self.assertEqual(check.check_facts(site), [])

    def test_missing_facts_file_fails_when_pages_exist(self):
        site = Site(make_site())
        site.facts["demo"] = None
        self.assertTrue(check.check_facts(site))


class OutputTest(unittest.TestCase):
    def built(self):
        root = make_site()
        site = Site(root)
        build.build(site, root / "docs")
        return site, root / "docs"

    def edit(self, path, old, new):
        path.write_text(path.read_text(encoding="utf-8").replace(old, new), encoding="utf-8")

    def test_built_site_passes(self):
        site, out = self.built()
        self.assertEqual(check.check_output(site, out), [])
        self.assertEqual(check.check_fresh(site, out), [])

    def test_missing_app_ads_fails(self):
        site, out = self.built()
        (out / "app-ads.txt").unlink()
        self.assertTrue(check.check_output(site, out))

    def test_wrong_cname_fails(self):
        site, out = self.built()
        (out / "CNAME").write_text("example.com\n")
        self.assertTrue(check.check_output(site, out))

    def test_top_level_support_folder_fails(self):
        site, out = self.built()
        (out / "support").mkdir()
        (out / "support" / "x.html").write_text("<p>x</p>")
        self.assertTrue(check.check_output(site, out))

    def test_broken_internal_link_fails(self):
        site, out = self.built()
        self.edit(out / "ko" / "index.html", "</main>", '<a href="/ko/nope/">x</a></main>')
        self.assertTrue(check.check_output(site, out))

    def test_broken_anchor_fails(self):
        site, out = self.built()
        self.edit(out / "en" / "demo" / "privacy" / "index.html", 'id="p3"', 'id="px"')
        self.assertTrue(check.check_output(site, out))

    def test_external_image_fails(self):
        site, out = self.built()
        self.edit(out / "ko" / "index.html", "</main>", '<img src="https://cdn.example.com/a.png"></main>')
        self.assertTrue(check.check_output(site, out))

    def test_unknown_app_store_id_fails(self):
        site, out = self.built()
        self.edit(out / "ko" / "index.html", "/app/id123", "/app/id999")
        self.assertTrue(check.check_output(site, out))

    def test_stale_output_fails_freshness(self):
        site, out = self.built()
        self.edit(out / "ko" / "index.html", "</main>", "<p>edited</p></main>")
        self.assertTrue(check.check_fresh(site, out))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 실패를 확인한다**

Run: `python3 -m unittest tests.test_check -v`
Expected: `ModuleNotFoundError: No module named 'check'`

- [ ] **Step 3: `scripts/check.py` 를 쓴다**

```python
"""content/ 와 docs/ 를 검사한다.

사용:
  python3 scripts/check.py            # 지금 있는 언어와 앱만 검사
  python3 scripts/check.py --release  # 8개 언어 x 5개 앱이 모두 있어야 통과
문제가 하나라도 있으면 종료 코드 1.
"""
from __future__ import annotations

import re
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build  # noqa: E402
from sitelib import PRIVACY_SECTION_COUNT, ROOT, Site  # noqa: E402

BANNED_CHARS = {"·": "가운뎃점", "—": "전각대시", "【": "전각 괄호", "】": "전각 괄호",
                "!": "느낌표", "！": "느낌표"}

# 스펙 3절, 3-1절. 대소문자 무시, 부분 문자열.
BANNED_WORDS = {
    "ko": [
        "1인 개발", "직접 만든", "앱을 만듭니다",
        "기기 밖", "밖으로 나가지", "어디에도 올라가지", "전송되지 않", "기기 안에만", "기기 안에 있습니다",
        "혁신적", "놀라운", "완벽한", "특별한", "스마트한", "강력한", "직관적", "손쉽게", "간편하게",
        "쉽고 빠르게", "차원이 다른", "새로운 차원", "한 단계 업그레이드", "똑똑하게",
        "지금 바로", "경험하세요", "만나 보세요", "만나보세요", "여정", "소중한 추억", "의 모든 것",
        "어플", "당신", "여러분",
    ],
    "en": [
        "seamless", "effortless", "elevate", "unlock", "unleash", "dive into", "journey", "cherished",
        "game-changer", "game changer", "stunning", "powerful", "intuitive", "next level",
        "at your fingertips", "like never before", "say goodbye", "all-in-one", "not just",
        "whether you're", "never leave", "never leaves", "stays on your device", "stay on your device",
        "indie developer", "solo developer",
    ],
    "ja": ["革新的", "シームレス", "の全て", "のすべて", "新たな体験", "端末の外"],
    "zh-hans": ["无缝", "全新体验", "之旅", "离开设备", "离开您的设备"],
    "zh-hant": ["無縫", "全新體驗", "之旅", "離開裝置", "離開您的裝置"],
    "de": ["nahtlos", "mühelos", "neues level", "verlassen nie", "verlassen niemals"],
    "es": ["sin esfuerzo", "siguiente nivel", "nunca salen", "nunca sale"],
    "pt-br": ["sem esforço", "próximo nível", "nunca saem", "nunca sai"],
}

# 반전과 권유 구문. 소개 문구(MARKETING_KEYS)에만 적용한다.
BANNED_REGEX = {
    "ko": [r"혼자서?\s?만[들듭드]", r"단순한 \S+(?:이|가) 아닙니다", r"(?:이|가) 아니라 .{1,30}입니다",
           r"뿐만 아니라", r"더 이상 .{0,12}필요", r"(?:앱|것)을 만듭니다"],
    "en": [r"\bit'?s not\b.{1,40}\bit'?s\b", r"\bnot\b[^.]{1,40}\bbut\b"],
}

MARKETING_KEYS = ("summary", "subtitle", "hero", "sections", "pro")
HAEYO_OK = ("필요", "중요", "주요", "수요", "세요", "개요", "강요")
NUMBER = re.compile(r"\d+(?:[.,]\d+)*")
REQUIRED_KEYS = ("name", "subtitle", "summary", "hero", "sections", "faq", "privacy")
REQUIRED_FILES = ("CNAME", "app-ads.txt", ".nojekyll", "404.html", "index.html", "robots.txt", "sitemap.xml")


def strings(obj, path: str = ""):
    if isinstance(obj, str):
        yield path, obj
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            yield from strings(value, f"{path}[{i}]")
    elif isinstance(obj, dict):
        for key, value in obj.items():
            yield from strings(value, f"{path}.{key}" if path else key)


def is_haeyo(text: str) -> bool:
    for sentence in re.split(r"(?<=[.?])\s+|\n", text):
        s = sentence.strip().rstrip(".?")
        if len(s) >= 2 and s.endswith("요") and re.match(r"[가-힣]", s[-2]) and s[-2:] not in HAEYO_OK:
            return True
    return False


def rule_problems(lang: str, text: str, marketing: bool) -> list[str]:
    found = [f"{label} '{ch}'" for ch, label in BANNED_CHARS.items() if ch in text]
    low = text.lower()
    found += [f"금지 표현 '{w}'" for w in BANNED_WORDS.get(lang, []) if w.lower() in low]
    if marketing:
        found += [f"금지 구문 /{rx}/" for rx in BANNED_REGEX.get(lang, []) if re.search(rx, text, re.I)]
    if lang == "ko" and is_haeyo(text):
        found.append("해요체")
    return found


def bullet_items(copy: dict):
    for i, section in enumerate(copy.get("sections", [])):
        for j, item in enumerate(section.get("bullets", [])):
            yield f"sections[{i}].bullets[{j}]", item
    for j, item in enumerate((copy.get("hero") or {}).get("points", [])):
        yield f"hero.points[{j}]", item
    pro = copy.get("pro") or {}
    for key in ("free", "pro"):
        for j, item in enumerate(pro.get(key, [])):
            yield f"pro.{key}[{j}]", item


def check_copy(site: Site) -> list[str]:
    problems = []
    for (slug, lang), copy in sorted(site.copy.items()):
        for path, text in strings(copy):
            if path.endswith("effectiveDate"):
                continue
            marketing = re.split(r"[.\[]", path)[0] in MARKETING_KEYS
            problems += [f"{slug}/{lang} {path}: {p}" for p in rule_problems(lang, text, marketing)]
        if lang == "ko":
            for path, item in bullet_items(copy):
                if re.search(r"(?:다|요|\.)$", item.strip()):
                    problems.append(f"{slug}/ko {path}: 불릿은 명사형으로 끝낸다 ({item})")
    for lang, ui in sorted(site.ui.items()):
        for path, text in strings(ui):
            problems += [f"i18n/{lang} {path}: {p}" for p in rule_problems(lang, text, False)]
    return problems


def shape(copy: dict) -> dict:
    pro = copy.get("pro") or {}
    return {
        "sections": len(copy["sections"]),
        "section bullets": [len(s.get("bullets", [])) for s in copy["sections"]],
        "hero points": len(copy["hero"].get("points", [])),
        "faq": len(copy["faq"]),
        "pro": bool(copy.get("pro")),
        "pro free": len(pro.get("free", [])),
        "pro items": len(pro.get("pro", [])),
        "privacy bullets": [len(s.get("bullets", [])) for s in copy["privacy"]["sections"]],
    }


def check_structure(site: Site, release: bool) -> list[str]:
    problems = []
    if release:
        for option in site.config["languages"]:
            code = option["code"]
            if code not in site.lang_codes():
                problems.append(f"i18n/{code}: 파일 없음")
                continue
            for app in site.apps:
                if not site.has_pages(app["slug"], code):
                    problems.append(f"{app['slug']}/{code}: 페이지 문구 없음")
    for app in site.apps:
        slug = app["slug"]
        reference = shape(site.app_copy(slug, "ko")) if site.has_pages(slug, "ko") else None
        for code in site.lang_codes():
            if not site.has_pages(slug, code):
                continue
            copy = site.app_copy(slug, code)
            missing = [k for k in REQUIRED_KEYS if k not in copy]
            if missing:
                problems.append(f"{slug}/{code}: 빠진 키 {missing}")
                continue
            count = len(copy["privacy"]["sections"])
            if count != PRIVACY_SECTION_COUNT:
                problems.append(f"{slug}/{code}: 개인정보 처리방침 {count}개 절 (12개여야 함)")
                continue
            if reference is not None and code != "ko":
                mine = shape(copy)
                problems += [
                    f"{slug}/{code}: {key} {mine[key]} (ko 는 {reference[key]})"
                    for key in reference if mine[key] != reference[key]
                ]
    reference_keys = set(site.ui.get("ko", {}))
    for code, ui in sorted(site.ui.items()):
        missing = sorted(reference_keys - set(ui))
        if missing:
            problems.append(f"i18n/{code}: 빠진 키 {missing}")
    return problems


def normalize_number(raw: str) -> str:
    if re.fullmatch(r"\d{1,3}(?:[.,]\d{3})+", raw):
        return re.sub(r"[.,]", "", raw)
    return raw.replace(",", ".")


def check_facts(site: Site) -> list[str]:
    problems = []
    for app in site.apps:
        slug = app["slug"]
        facts = site.facts.get(slug)
        langs = [code for code in site.lang_codes() if site.app_copy(slug, code)]
        if facts is None:
            if any(site.has_pages(slug, code) for code in langs):
                problems.append(f"{slug}: facts.json 없음")
            continue
        allowed = {normalize_number(n) for n in facts.get("numbers", [])}
        for code in langs:
            copy = site.app_copy(slug, code)
            marketing = {k: copy[k] for k in MARKETING_KEYS if k in copy}
            for path, text in strings(marketing):
                for raw in NUMBER.findall(text):
                    if normalize_number(raw) not in allowed:
                        problems.append(f"{slug}/{code} {path}: facts.json 에 없는 숫자 {raw}")
            if facts.get("ads") and site.has_pages(slug, code):
                policy = " ".join(text for _, text in strings(copy["privacy"]))
                if "AdMob" not in policy:
                    problems.append(f"{slug}/{code}: 광고 SDK(AdMob)가 개인정보 처리방침에 없음")
    return problems


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links: list[str] = []
        self.srcs: list[str] = []
        self.ids: set[str] = set()
        self.alternates: dict[str, str] = {}
        self.stylesheets: list[str] = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.ids.add(a["id"])
        if tag == "a" and a.get("href"):
            self.links.append(a["href"])
        if a.get("src"):
            self.srcs.append(a["src"])
        if tag == "link" and a.get("rel") == "alternate" and a.get("hreflang"):
            self.alternates[a["hreflang"]] = a.get("href", "")
        if tag == "link" and a.get("rel") == "stylesheet":
            self.stylesheets.append(a.get("href", ""))


def resolve(out: Path, url_path: str) -> Path:
    path = url_path.split("#")[0].split("?")[0]
    target = out / path.lstrip("/")
    return target / "index.html" if path.endswith("/") else target


def check_output(site: Site, out: Path) -> list[str]:
    problems = [f"docs/{name} 없음" for name in REQUIRED_FILES if not (out / name).exists()]
    if (out / "CNAME").exists() and (out / "CNAME").read_text().strip() != "kvndh.com":
        problems.append("docs/CNAME 내용이 kvndh.com 이 아님")
    if (out / "app-ads.txt").exists() and not (out / "app-ads.txt").read_text().strip():
        problems.append("docs/app-ads.txt 가 비어 있음")
    if (out / "support").exists():
        problems.append("docs/support/ 가 있음 (KVNDH/support 프로젝트 사이트와 겹침)")
    app_ids = {app["appStoreId"] for app in site.apps}
    pages: dict[Path, PageParser] = {}
    for html_file in sorted(out.rglob("*.html")):
        parser = PageParser()
        parser.feed(html_file.read_text(encoding="utf-8"))
        pages[html_file] = parser
    for html_file, p in pages.items():
        rel = html_file.relative_to(out)
        if p.stylesheets:
            problems.append(f"{rel}: 외부 스타일시트 {p.stylesheets}")
        for src in p.srcs:
            if re.match(r"(?:https?:)?//", src):
                problems.append(f"{rel}: 외부 리소스 {src}")
            elif not resolve(out, src).exists():
                problems.append(f"{rel}: 없는 파일 {src}")
        for href in p.links:
            if href.startswith("#"):
                if href[1:] not in p.ids:
                    problems.append(f"{rel}: 없는 앵커 {href}")
            elif href.startswith("/"):
                target = resolve(out, href)
                if not target.exists():
                    problems.append(f"{rel}: 깨진 링크 {href}")
                elif "#" in href and target in pages and href.split("#", 1)[1] not in pages[target].ids:
                    problems.append(f"{rel}: 없는 앵커 {href}")
            elif href.startswith("https://apps.apple.com/"):
                m = re.search(r"/id(\d+)", href)
                if not m or m.group(1) not in app_ids:
                    problems.append(f"{rel}: 모르는 App Store 링크 {href}")
        for lang, url in p.alternates.items():
            if not url.startswith(site.base_url + "/"):
                problems.append(f"{rel}: hreflang {lang} 주소가 사이트 밖 {url}")
                continue
            other = pages.get(resolve(out, url[len(site.base_url):]))
            if other is None:
                problems.append(f"{rel}: hreflang {lang} 대상 없음 {url}")
            elif other.alternates != p.alternates:
                problems.append(f"{rel}: hreflang 짝이 {url} 와 다름")
    return problems


def check_fresh(site: Site, out: Path) -> list[str]:
    with tempfile.TemporaryDirectory() as tmp:
        fresh = Path(tmp) / "docs"
        build.build(site, fresh)
        expected = build.snapshot(fresh)
    actual = build.snapshot(out)
    changed = sorted(set(expected) ^ set(actual)) + sorted(
        k for k in set(expected) & set(actual) if expected[k] != actual[k]
    )
    if changed:
        return [f"docs/ 가 content 와 다름 ({len(changed)}개 파일, 예: {changed[:3]}). build.py 를 다시 돌릴 것"]
    return []


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    site = Site(ROOT)
    out = ROOT / "docs"
    problems = check_copy(site) + check_structure(site, "--release" in argv) + check_facts(site)
    if out.exists():
        problems += check_output(site, out) + check_fresh(site, out)
    else:
        problems.append("docs/ 없음. 먼저 python3 scripts/build.py")
    for problem in problems:
        print("✗", problem)
    print("통과" if not problems else f"문제 {len(problems)}건")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: 통과를 확인한다**

Run: `python3 -m unittest discover -s tests -v`
Expected: 47 tests OK

- [ ] **Step 5: 커밋한다**

```bash
git add scripts/check.py tests/test_check.py
git commit -m "문구 규칙과 구조, 사실, 출력물을 보는 check.py 를 둔다"
```

---

### Task 5: 0단계 샘플 (한국어 허브와 BrushWorks) — 사용자 확인 관문

**Files:**
- Create: `content/site.json`, `content/i18n/ko.json`, `content/asset-sources.json`
- Create: `content/apps/brushworks/facts.json`, `content/apps/brushworks/ko.json`
- Create: 카드만 있는 `content/apps/{life-tyde,snapline,tapey,dice-master}/ko.json`
- Create: `static/CNAME`, `static/app-ads.txt`(저장소 루트 파일 복사), `static/.nojekyll`, `static/robots.txt`
- Create: `scripts/import_assets.py`
- Generated: `assets/**`, `docs/**`

**Interfaces:**
- Consumes: Task 1~4 전부
- Produces:
  - 실제 콘텐츠 파일. Task 6~9 의 에이전트가 이 형식을 그대로 따른다
  - `import_assets.py` 의 `import_app(slug)`, `import_site_og()`

- [ ] **Step 1: 설정과 정적 파일을 쓴다**

`content/site.json`:

```json
{
 "baseUrl": "https://kvndh.com",
 "contact": "kvndh36@naver.com",
 "languages": [
  {"code": "ko", "htmlLang": "ko", "hreflang": "ko", "label": "한국어", "ogLocale": "ko_KR"},
  {"code": "en", "htmlLang": "en", "hreflang": "en", "label": "English", "ogLocale": "en_US"},
  {"code": "ja", "htmlLang": "ja", "hreflang": "ja", "label": "日本語", "ogLocale": "ja_JP"},
  {"code": "zh-hans", "htmlLang": "zh-Hans", "hreflang": "zh-Hans", "label": "简体中文", "ogLocale": "zh_CN"},
  {"code": "zh-hant", "htmlLang": "zh-Hant", "hreflang": "zh-Hant", "label": "繁體中文", "ogLocale": "zh_TW"},
  {"code": "de", "htmlLang": "de", "hreflang": "de", "label": "Deutsch", "ogLocale": "de_DE"},
  {"code": "es", "htmlLang": "es", "hreflang": "es", "label": "Español", "ogLocale": "es_ES"},
  {"code": "pt-br", "htmlLang": "pt-BR", "hreflang": "pt-BR", "label": "Português (Brasil)", "ogLocale": "pt_BR"}
 ],
 "apps": [
  {"slug": "brushworks", "appStoreId": "6810951573", "accent": "#A05B42", "accentText": "#E39C80", "featured": true},
  {"slug": "life-tyde", "appStoreId": "6773198369", "accent": "#E33C48", "accentText": "#F46A74"},
  {"slug": "snapline", "appStoreId": "6809834907", "accent": "#F9F9F9", "accentText": "#F9F9F9"},
  {"slug": "tapey", "appStoreId": "6778635856", "accent": "#CBD3B6", "accentText": "#CBD3B6"},
  {"slug": "dice-master", "appStoreId": "6765857608", "accent": "#EE9D1C", "accentText": "#EE9D1C"}
 ]
}
```

`static/` 파일:

```bash
mkdir -p static && cp app-ads.txt static/app-ads.txt && printf 'kvndh.com\n' > static/CNAME && : > static/.nojekyll
printf 'User-agent: *\nAllow: /\nSitemap: https://kvndh.com/sitemap.xml\n' > static/robots.txt
```

`content/i18n/ko.json`:

```json
{
 "skip": "본문으로 건너뛰기",
 "language": "언어",
 "hubMetaTitle": "kvndh 앱",
 "hubTitle": "사진과 기록, 주사위를 다루는 iOS 앱",
 "hubLead": "다섯 앱 모두 회원가입 없이 바로 씁니다.",
 "learnMore": "자세히 보기",
 "getOnAppStore": "App Store에서 받기",
 "screenshot": "화면",
 "navAbout": "소개",
 "navSupport": "지원",
 "navPrivacy": "개인정보 처리방침",
 "free": "무료",
 "pro": "Pro",
 "faqTitle": "자주 묻는 질문",
 "contactTitle": "문의",
 "contactBody": "궁금한 점이나 오류는 메일로 보내 주세요. 기기 모델과 iOS 버전을 함께 적어 주시면 빨리 확인합니다.",
 "effectiveDate": "시행일",
 "toc": "목차",
 "notFound": "찾는 페이지가 없습니다. 아래에서 언어를 고르면 앱 목록으로 갑니다."
}
```

- [ ] **Step 2: BrushWorks 사실과 문구를 쓴다**

`content/apps/brushworks/facts.json`:

```json
{
 "describesVersion": "1.0.1",
 "purchase": "one-time",
 "ads": false,
 "account": false,
 "network": ["App Store 결제와 구매 복원(StoreKit 2)"],
 "permissions": ["사진 선택: PHPicker, 고른 한 장만 전달", "사진 추가 전용: 완성작 저장"],
 "storage": ["고른 사진의 사본: 앱 저장공간, 다른 사진을 고르거나 처음 상태로를 누르면 삭제", "붓질 기록과 설정: 앱 저장공간"],
 "numbers": ["0.25", "9", "16", "10", "90", "720", "1280", "1080", "1920", "1.5", "3072"],
 "sources": [
  "BrushWorks/README.md",
  "BrushWorks/docs/STATUS.md",
  "BrushWorks/docs/store/metadata.json",
  "support/brushworks.html"
 ]
}
```

`content/apps/brushworks/ko.json`:

```json
{
 "name": "BrushWorks",
 "subtitle": "문질러서 쌓아 올리는 물감 질감",
 "summary": "사진을 밑그림으로 깔고 손가락으로 문질러 그림으로 옮깁니다.",
 "hero": {
  "hook": "손가락이 지나간 자리에 그 아래 사진의 색이 물감으로 얹힙니다. 한 번에 바뀌는 필터는 없습니다.",
  "points": ["회원가입 없이 바로 사용", "붓 세 자루, 크기 아홉 단계", "한 번 구매로 여는 Pro"]
 },
 "sections": [
  {
   "title": "물감이 쌓입니다",
   "body": ["겹쳐 칠할수록 두께가 생기고, 그 두께가 빛을 받아 그림자를 만듭니다. 캔버스를 다 덮어야 그림이 끝납니다."],
   "bullets": ["겹칠수록 짙어지는 붓자국", "빛을 받는 물감 두께", "원본을 잠깐 비춰 보는 눈 버튼"]
  },
  {
   "title": "붓 세 자루",
   "body": ["밑그림 농도는 다섯 단계입니다. 가장 낮은 Blind 모드에서는 사진이 보이지 않습니다."],
   "bullets": ["색이 비쳐 섞이는 얇은 칠", "그린 방향으로 결이 남는 붓결", "두껍게 밀어 바르는 나이프"]
  },
  {
   "title": "그린 시간이 남습니다",
   "body": ["붓질은 하나하나 기록됩니다. 리플레이로 처음부터 다시 보고, 짧은 타임랩스로 내보냅니다."],
   "bullets": ["0.25배속까지 느려지는 리플레이", "세로 9:16 타임랩스", "끝에 남는 붓질 수와 그린 시간"]
  }
 ],
 "pro": {
  "title": "BrushWorks Pro",
  "body": ["무료로도 끝까지 그리고 저장합니다. Pro는 결과물을 더 크고 깨끗하게 남깁니다."],
  "free": ["붓 세 자루와 크기 아홉 단계", "모서리에 작은 워터마크가 들어가는 PNG 저장", "10초 720×1280 타임랩스"],
  "pro": ["워터마크 없는 저장", "1.5배 크기, 긴 변 최대 3072px", "PNG, HEIF, TIFF 선택", "10초에서 90초까지 1080×1920 타임랩스", "색 고정과 세밀 조절"],
  "note": "한 번 구매, 구독 없음"
 },
 "faq": [
  {"q": "고른 사진의 보관 위치", "a": [
   "고른 사진의 사본은 다음에 앱을 열 때 그림을 되살리려고 앱 저장공간에 둡니다. 다른 사진을 고르거나 설정에서 처음 상태로를 누르면 지워집니다.",
   "사진은 iOS 사진 선택기로 고른 한 장만 앱에 전달됩니다. 완성작을 저장할 때는 추가 전용 권한만 씁니다."]},
  {"q": "캔버스 전체를 문질러야 하는 이유", "a": [
   "손으로 그리는 앱이라 한 번에 바꿔 주는 기능이 없습니다. 타임랩스 끝에 붓질 수와 그린 시간이 남는 것도 그래서입니다."]},
  {"q": "사진을 바꾸면 그림이 사라지는 이유", "a": [
   "붓질의 색은 그림을 다시 그릴 때마다 사진에서 읽어 옵니다. 사진이 바뀌면 옛 붓질에 없던 색이 나오므로 캔버스를 비웁니다. 칠한 것이 있으면 먼저 묻습니다.",
   "되돌리기로는 복구되지 않습니다. 사진을 바꾸기 전에 그림을 저장해 두세요."]},
  {"q": "타임랩스 길이", "a": [
   "무료 타임랩스는 10초, 세로 9:16입니다. Pro에서는 10초에서 90초 사이로 길이를 고릅니다.",
   "전 과정을 천천히 보려면 앱 안의 리플레이를 씁니다. 0.25배속까지 느려지고, 캔버스를 좌우로 끌면 원하는 지점으로 갑니다."]},
  {"q": "Pro 구매 복원", "a": [
   "기기를 바꾸거나 앱을 다시 설치했다면 설정의 Pro 카드에서 구매 복원을 누릅니다. 같은 Apple 계정이면 다시 결제하지 않습니다."]},
  {"q": "인터넷 연결", "a": [
   "그리기와 저장, 타임랩스는 인터넷 연결 없이 됩니다. Pro 구매와 복원에만 App Store 연결이 필요합니다."]}
 ],
 "privacy": {
  "title": "BrushWorks 개인정보 처리방침",
  "effectiveDate": "2026-09-17",
  "intro": ["kvndh(이하 개발자)는 BrushWorks 앱(이하 앱)을 쓰는 분의 개인정보를 「개인정보 보호법」에 따라 다루며, 그 기준을 아래와 같이 알립니다."],
  "sections": [
   {"title": "개인정보의 처리 목적", "paragraphs": ["앱에는 회원가입과 로그인이 없고, 개발자는 이용자의 개인정보를 처리하지 않습니다. 그래서 따로 정한 처리 목적이 없습니다."], "bullets": []},
   {"title": "처리하는 개인정보의 항목", "paragraphs": ["개발자가 수집하는 개인정보 항목은 없습니다. 앱이 쓰는 자료는 아래와 같으며, 모두 이용자 기기의 앱 저장공간에 보관됩니다. 개발자는 이 자료를 받지 않습니다."], "bullets": ["고른 사진의 사본: 그림을 다시 열 때 사용", "붓질 기록과 설정: 그림을 다시 그릴 때 사용"]},
   {"title": "처리 및 보유 기간", "paragraphs": ["개발자가 보유하는 개인정보가 없습니다. 앱 저장공간의 자료는 앱을 삭제하면 함께 지워집니다. 사진 앱에 저장한 그림은 사진 앱에서 지웁니다."], "bullets": []},
   {"title": "제3자 제공", "paragraphs": ["개인정보를 제3자에게 제공하지 않습니다."], "bullets": []},
   {"title": "처리 위탁", "paragraphs": ["개인정보 처리를 위탁하지 않습니다. BrushWorks Pro 결제는 Apple이 App Store에서 처리하며, 결제 정보는 Apple의 개인정보 처리방침을 따릅니다. 개발자는 결제 수단이나 Apple 계정 정보를 받지 않습니다."], "bullets": []},
   {"title": "파기 절차와 방법", "paragraphs": ["개발자가 보유하는 개인정보가 없어 파기할 대상이 없습니다. 고른 사진의 사본은 설정에서 처음 상태로를 누르면 지워지고, 앱의 모든 자료는 앱을 삭제하면 지워집니다."], "bullets": []},
   {"title": "정보주체와 법정대리인의 권리와 의무, 행사 방법", "paragraphs": ["개발자가 보유한 개인정보가 없으므로 열람, 정정, 삭제를 요청할 대상이 없습니다. 궁금한 점은 아래 문의처로 연락하면 확인해 드립니다."], "bullets": []},
   {"title": "안전성 확보 조치", "paragraphs": ["사진은 iOS 사진 선택기로 고른 한 장만 앱에 전달됩니다. 완성작을 저장할 때는 사진을 추가하는 권한만 쓰며, 사진 보관함을 읽는 권한은 요청하지 않습니다."], "bullets": []},
   {"title": "자동 수집 장치의 설치와 운영, 거부 방법", "paragraphs": ["쿠키, 광고 식별자, 방문 분석 도구를 쓰지 않습니다."], "bullets": []},
   {"title": "개인정보 보호책임자", "paragraphs": ["개인정보와 관련한 문의는 아래로 연락하면 됩니다."], "bullets": ["책임자: kvndh", "이메일: kvndh36@naver.com"]},
   {"title": "권익침해 구제 방법", "paragraphs": ["개인정보 침해에 대한 상담이나 분쟁 해결이 필요하면 아래 기관에 문의할 수 있습니다."], "bullets": ["개인정보분쟁조정위원회: 1833-6972 (www.kopico.go.kr)", "개인정보침해신고센터: 국번 없이 118 (privacy.kisa.or.kr)", "대검찰청: 국번 없이 1301 (www.spo.go.kr)", "경찰청: 국번 없이 182 (ecrm.police.go.kr)"]},
   {"title": "처리방침의 변경", "paragraphs": ["이 방침은 시행일부터 적용합니다. 내용이 바뀌면 이 페이지에서 시행일과 함께 알립니다."], "bullets": []}
  ]
 }
}
```

- [ ] **Step 3: 나머지 네 앱의 카드 문구를 쓴다**

`content/apps/life-tyde/ko.json`:

```json
{"name": "Life Tyde", "subtitle": "조용히 쌓이는 나의 연대기", "summary": "해시태그 아래 굵직한 순간만 골라 한 줄 타임라인에 남깁니다."}
```

`content/apps/snapline/ko.json`:

```json
{"name": "SnapLine", "subtitle": "피사체 뒤로 지나가는 구도선", "summary": "사진 위 카메라 격자를 피사체 쪽으로 꺾고, 겹친 자리를 지워 선이 뒤로 지나가게 합니다."}
```

`content/apps/tapey/ko.json`:

```json
{"name": "Tapey", "subtitle": "벽에 붙인 듯한 사진 콜라주", "summary": "좋아하는 사진을 워시테이프로 벽에 붙인 듯 배치해 배경화면으로 내보냅니다."}
```

`content/apps/dice-master/ko.json`:

```json
{"name": "Dice Master", "subtitle": "수식 자동 계산과 색상별 부분합", "summary": "면체를 골라 굴리면 수식이 바로 계산되고, 색상별 부분합이 함께 나옵니다."}
```

- [ ] **Step 4: 자산 가져오기 스크립트를 쓰고 돌린다**

`content/asset-sources.json` (경로는 `~/Desktop/CODING` 기준):

```json
{
 "brushworks": {"icon": "BrushWorks/Sources/Resources/Assets.xcassets/AppIcon.appiconset/AppIcon.png",
  "shots": {"en": ["BrushWorks/docs/store/screenshots/01-finished.png"]}},
 "life-tyde": {"icon": "Life Tyde/Life Tyde/Assets.xcassets/AppIcon.appiconset/AppIcon.png",
  "shots": {"ko": ["Life Tyde/results/screenshots/01-timeline-ko.png"], "en": ["Life Tyde/results/screenshots/01-timeline-en.png"]}},
 "snapline": {"icon": "SnapLine/SnapLine/Resources/Assets.xcassets/AppIcon.appiconset/icon-1024.png",
  "shots": {"en": ["SnapLine/docs/appstore/screenshots/01-behind.png"]}},
 "tapey": {"icon": "Tapey/ios/App/App/Assets.xcassets/AppIcon.appiconset/AppIcon-512@2x.png",
  "shots": {"ko": ["Tapey/screenshots/ko/APP_IPHONE_67_01.png"]}},
 "dice-master": {"icon": "diceMaster/diceMaster/Assets.xcassets/AppIcon.appiconset/AppIcon-1024.png",
  "shots": {"ko": ["diceMaster/results/asc-shot1-final/ko/APP_IPHONE_67/00_01_formula3d.png"]}}
}
```

`scripts/import_assets.py`:

```python
"""앱 저장소의 아이콘과 스토어 스크린샷을 assets/ 로 가져온다. ImageMagick(magick)이 필요하다.

원본 경로는 content/asset-sources.json (~/Desktop/CODING 기준).
사용: python3 scripts/import_assets.py            # 전부
      python3 scripts/import_assets.py tapey      # 일부
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sitelib import ROOT, load_json  # noqa: E402

CODING = ROOT.parent
FONT = "/System/Library/Fonts/Helvetica.ttc"


def magick(*args) -> None:
    subprocess.run(["magick", *map(str, args)], check=True)


def import_app(slug: str) -> None:
    spec = load_json(ROOT / "content" / "asset-sources.json")[slug]
    app = next(a for a in load_json(ROOT / "content" / "site.json")["apps"] if a["slug"] == slug)
    dest = ROOT / "assets" / slug
    dest.mkdir(parents=True, exist_ok=True)
    icon = CODING / spec["icon"]
    for size in (180, 360):
        magick(icon, "-strip", "-resize", f"{size}x{size}", "-quality", "85", dest / f"icon-{size}.webp")
    for lang, shots in spec["shots"].items():
        for i, rel in enumerate(shots, 1):
            out = dest / "shots" / lang / f"{i:02d}.webp"
            out.parent.mkdir(parents=True, exist_ok=True)
            magick(CODING / rel, "-strip", "-resize", "660x", "-quality", "80", out)
    magick("-size", "1200x630", f"radial-gradient:{app['accent']}-#0A0A0B",
           "(", icon, "-resize", "300x300", ")", "-gravity", "center", "-composite", "-strip", "-quality", "85", dest / "og.jpg")


def import_site_og() -> None:
    (ROOT / "assets").mkdir(exist_ok=True)
    magick("-size", "1200x630", "xc:#0A0A0B", "-fill", "#F2F2F3", "-font", FONT, "-pointsize", "150",
           "-gravity", "center", "-annotate", "+0+0", "kvndh", "-strip", "-quality", "85", ROOT / "assets" / "og.jpg")


def main(argv: list[str]) -> int:
    slugs = argv or list(load_json(ROOT / "content" / "asset-sources.json"))
    for slug in slugs:
        import_app(slug)
        print("가져옴:", slug)
    if not argv:
        import_site_og()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

Run: `python3 scripts/import_assets.py && find assets -type f | sort`
Expected:
- 앱마다 `icon-180.webp`, `icon-360.webp`, `og.jpg`, `shots/<lang>/01.webp` 가 생긴다
- 사이트 전체용 `assets/og.jpg` 가 생긴다

- [ ] **Step 5: 빌드하고 검사한다**

Run: `python3 scripts/build.py && python3 scripts/check.py`
Expected: `페이지 6개 -> docs/` (루트, 404, ko 허브, BrushWorks 3종) 그리고 `통과`
실패하면 문구를 규칙에 맞게 고친다. 검사기를 느슨하게 만들지 않는다.

- [ ] **Step 6: 화면을 확인한다**

```bash
python3 -m http.server 8765 -d docs >/tmp/kvndh-http.log 2>&1 &
for p in ko ko/brushworks ko/brushworks/support ko/brushworks/privacy; do
  for w in 390 1280; do
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --hide-scrollbars \
      --window-size=$w,2400 --screenshot=/tmp/kvndh-$(echo $p | tr / -)-$w.png "http://localhost:8765/$p/"
  done
done
```

- 스크린샷 8장을 읽어 깨진 배치, 겹침, 대비를 확인하고 고친다
- Orca 브라우저 탭으로 `http://localhost:8765/ko/` 를 사용자에게 연다

- [ ] **Step 7: 커밋하고 사용자 확인을 받는다**

```bash
git add content static assets scripts/import_assets.py docs
git commit -m "0단계: 한국어 허브와 BrushWorks 샘플 페이지를 만든다"
```

사용자에게 확인받을 것은 세 가지다.
- 화면
- 문구 말투
- 개인정보 처리방침 구조

**승인 전에는 Task 6 으로 넘어가지 않는다.**

---

### Task 6: 1단계 앱별 사실과 문구 (에이전트 5개, 병렬)

**Files (앱마다):**
- `content/apps/<app>/facts.json`
- `content/apps/<app>/ko.json`
- `content/apps/<app>/en.json`
- `content/asset-sources.json` 의 해당 앱 항목
- 해당 앱의 `assets/<app>/**`
- 영어 UI 문자열 `content/i18n/en.json` 은 HQ 가 먼저 쓴다

**Interfaces:**
- Consumes: Task 5 의 형식. BrushWorks 는 ko 가 이미 있으므로 사실을 재확인하고 en 만 추가한다
- Produces: 5개 앱 × (ko, en) 전체 문구

- [ ] **Step 1: HQ 가 `content/i18n/en.json` 을 쓴다** (ko 와 같은 키, 문장 계약 준수)

```json
{
 "skip": "Skip to content",
 "language": "Language",
 "hubMetaTitle": "kvndh apps",
 "hubTitle": "iOS apps for photos, records and dice",
 "hubLead": "All five apps work without an account.",
 "learnMore": "Details",
 "getOnAppStore": "Download on the App Store",
 "screenshot": "screen",
 "navAbout": "About",
 "navSupport": "Support",
 "navPrivacy": "Privacy Policy",
 "free": "Free",
 "pro": "Pro",
 "faqTitle": "Questions",
 "contactTitle": "Contact",
 "contactBody": "Send questions and bug reports by email. Include your device model and iOS version so we can check faster.",
 "effectiveDate": "Effective",
 "toc": "Contents",
 "notFound": "This page does not exist. Pick a language below to see the apps."
}
```

- [ ] **Step 2: 워크플로로 에이전트 5개를 띄운다** (Workflow 도구, 앱 하나에 에이전트 하나)

각 에이전트에게 주는 지시문 틀(`{app}`, `{repo}`, `{support_page}` 만 바꾼다):

```
kvndh.com 사이트의 {app} 콘텐츠를 만든다. 저장소: ~/Desktop/CODING/KVNDH.github.io (브랜치 site-v1).
반드시 먼저 읽을 것: _design/specs/2026-09-17-kvndh-site-design.md (3절, 3-1절, 5절),
content/apps/brushworks/ko.json 과 facts.json (형식과 말투의 기준).

1. 사실 조사 (앱 저장소 ~/Desktop/CODING/{repo} 는 읽기만 한다. 절대 수정하지 않는다)
   - 가격 구조: .storekit, ProStore, Paywall, FreeLimits
   - 광고 SDK와 추적: Package.resolved, Podfile, package.json, Info.plist 의 NSUserTrackingUsageDescription
   - 권한: Info.plist 의 *UsageDescription
   - 저장 위치, 네트워크 사용, PrivacyInfo.xcprivacy
   - 지원 페이지 ~/Desktop/CODING/support/{support_page} 의 FAQ
   - 스토어 문안 docs/store/metadata.json 과 main 브랜치의 현재 버전
   → content/apps/{app}/facts.json 에 적는다. 모든 항목에 출처 파일을 sources 로 남긴다.
     numbers 에는 소개 문구에 쓸 숫자만 넣는다.
2. ko.json, en.json 작성 (BrushWorks ko.json 과 같은 키와 구조)
   - sections 3개, pro 는 유료 기능이 있을 때만(없으면 null)
   - FAQ 는 기존 지원 페이지에서 옮기되 코드와 대조해 틀린 것은 고친다
   - 개인정보 처리방침은 12개 절, 순서와 제목은 BrushWorks ko.json 과 같게.
     광고 SDK가 있으면 9절(자동 수집 장치)과 4절이나 5절(제3자 제공, 위탁)에 사실대로 적고 "AdMob" 을 이름으로 쓴다
   - en 은 ko 와 구조(섹션 수, 불릿 수, FAQ 수, 절별 불릿 수)가 같아야 한다.
     영어 개인정보 처리방침의 11절은 한국 기관 대신 "거주 국가의 개인정보 감독기관에 문의할 수 있다"로 쓴다
   - 문장 계약(3-1절)을 지킨다
     - 개발자 이야기 금지
     - "기기 밖으로 나가지 않는다" 계열 금지
     - AI 상투어 금지
     - 느낌표, 가운뎃점, 전각대시 금지
     - ko 불릿은 명사형
   - 기능 이름과 버튼 이름은 앱 번역 카탈로그(ko, en)의 글자 그대로 쓴다
3. 자산: content/asset-sources.json 의 {app} 항목에 ko 와 en 스토어 스크린샷 1장씩 경로를 적고
   `python3 scripts/import_assets.py {app}` 를 돌린다
4. 확인: `python3 scripts/build.py && python3 scripts/check.py` 에서 {app} 관련 문제가 0건이어야 한다.
   다른 앱 문제는 건드리지 않는다
5. 커밋하지 않는다. 끝나면 보고한다
   - 바꾼 파일
   - facts.json 요약
   - 코드와 스토어 문안이 달랐던 점
   - 확신이 없는 사실 (특히 개인정보 처리방침)
```

| app | repo | support_page |
|---|---|---|
| brushworks | BrushWorks | brushworks.html |
| life-tyde | Life Tyde | life-tyde.html |
| snapline | SnapLine | snapline.html |
| tapey | Tapey | tapey.html, tapey-privacy.html |
| dice-master | diceMaster | dicemaster.html |

- [ ] **Step 3: HQ 가 합친다**
  - Run: `python3 scripts/build.py && python3 scripts/check.py`
  - Expected: `통과`
  - 에이전트가 올린 "확신 없는 사실"을 목록으로 모은다

- [ ] **Step 4: 커밋한다**

```bash
git add content assets docs
git commit -m "1단계: 앱 다섯 개의 사실 정리와 한국어, 영어 문구를 채운다"
```

---

### Task 7: 2단계 번역 (에이전트 3개, 병렬)

**Files:**
- `content/i18n/{ja,zh-hans,zh-hant,de,es,pt-br}.json`
- `content/apps/*/{ja,zh-hans,zh-hant,de,es,pt-br}.json`
- 해당 언어 스크린샷

**Interfaces:**
- Consumes: Task 6 의 ko, en 문구와 facts.json
- Produces: 8개 언어 전체

- [ ] **Step 1: 워크플로로 에이전트 3개를 띄운다** (묶음: `ja` / `zh-hans`, `zh-hant` / `de`, `es`, `pt-br`)

지시문 틀:

```
kvndh.com 사이트를 {langs} 로 옮긴다. 저장소 ~/Desktop/CODING/KVNDH.github.io (site-v1).
먼저 읽을 것: 스펙 3절과 3-1절, content/i18n/en.json, content/apps/*/{ko,en}.json, facts.json.

- 기준은 en 의 구조와 ko 의 사실이다. 섹션 수, 불릿 수, FAQ 수, 개인정보 처리방침 12개 절과 절별 불릿 수를 똑같이 맞춘다
- 기계 번역 말투를 쓰지 않는다. 그 언어로 처음 쓴 것처럼 쓴다. 3-1절의 그 언어 금지 표현을 피한다.
  "기기 밖으로 나가지 않는다" 계열은 어느 언어에서도 쓰지 않는다
- 기능 이름과 버튼 이름은 각 앱 저장소 번역 카탈로그(*.xcstrings, Localizable.strings, 웹 앱은 locale 파일)에서
  그 언어 글자를 찾아 쓴다. 앱이 그 언어를 지원하지 않으면 영어 표기를 쓴다. 앱 저장소는 읽기만 한다
- 개인정보 처리방침 11절은 en 과 같이 "거주 국가의 감독기관" 문장으로 쓴다
- 숫자는 facts.json numbers 에 있는 값만 쓴다(천 단위 구분 기호는 허용)
- 스크린샷: 앱 저장소에 그 언어 스토어 스크린샷이 있으면 content/asset-sources.json 에 추가하고
  import_assets.py 를 돌린다. 없으면 두지 않는다(en 으로 대체된다)
- 확인: python3 scripts/build.py && python3 scripts/check.py 에서 {langs} 관련 문제 0건
- 커밋하지 않는다. 보고: 바꾼 파일, 카탈로그에서 못 찾은 용어, 번역에서 판단이 필요했던 곳
```

- [ ] **Step 2: HQ 가 합친다**
  - Run: `python3 scripts/build.py && python3 scripts/check.py --release`
  - Expected: `통과`

- [ ] **Step 3: 커밋한다**

```bash
git add content assets docs
git commit -m "2단계: 여섯 개 언어 번역을 더한다"
```

---

### Task 8: 3단계 검토 (에이전트 2개, 병렬, 읽기 전용)

- [ ] **Step 1: 워크플로로 검토 에이전트 2개를 띄운다**

검토 ① 문구와 사실:

```
kvndh.com 사이트 콘텐츠를 적대적으로 검토한다. 파일은 고치지 않는다.
대상: ~/Desktop/CODING/KVNDH.github.io/content/**. 기준: 스펙 3절, 3-1절, 5절.
- 모든 언어에서 문장 계약 위반을 찾는다(검사기가 못 잡는 것 위주)
  - 번역투, 반전 구문, 요약으로 끝맺는 문장, 감정 유도, 비슷한 길이 문장 연속, 장식용 3개 나열, 개발자 이야기, "기기 밖" 계열의 우회 표현
- facts.json 의 sources 를 직접 열어 문구의 사실(가격 구조, 한도, 권한, 저장, 네트워크, 광고)을 대조한다.
  개인정보 처리방침은 코드와 한 줄씩 맞춘다. Tapey 의 AdMob 서술은 따로 표시한다
- 보고 형식: 파일 경로, JSON 경로, 문제, 고칠 문장 제안, 심각도(틀린 사실 > 법적 표현 > 말투)
```

검토 ② 화면과 링크:

```
kvndh.com 빌드 결과를 검토한다. 파일은 고치지 않는다.
- `python3 -m http.server 8766 -d ~/Desktop/CODING/KVNDH.github.io/docs` 를 띄운다
- Chrome headless 로 모든 페이지를 390px 과 1280px 에서 찍는다
- 확인할 것
  - 넘치는 글자, 겹침, 잘린 이미지
  - 언어별 줄바꿈(ja, zh, de 의 긴 단어)
  - 대비(AA), 포커스 표시, 언어 메뉴, 탭, FAQ 펼침, 개인정보 처리방침 목차 이동
- `python3 scripts/check.py --release` 결과를 첨부한다
- 보고 형식: 페이지, 폭, 문제, 스크린샷 경로, 고칠 곳(CSS 선택자 또는 JSON 경로)
- 끝나면 서버를 끈다
```

- [ ] **Step 2: HQ 가 지적 목록을 받아 Task 9 로 넘긴다**

---

### Task 9: 4단계 수정과 사용자 검토

- [ ] **Step 1: 지적을 반영한다**
  - 순서: 틀린 사실 → 법적 표현 → 말투 → 화면
  - CSS 를 고치면 해당 폭을 다시 찍어 확인한다
- [ ] **Step 2: 검사한다**
  - Run: `python3 -m unittest discover -s tests -v && python3 scripts/build.py && python3 scripts/check.py --release`
  - Expected: 테스트 전부 OK, `통과`
- [ ] **Step 3: 사용자 검토**
  - Tapey 개인정보 처리방침(ko, en)과 "확신 없는 사실" 목록을 사용자에게 보여 주고 확인받는다
  - 로컬 서버 주소를 Orca 브라우저 탭으로 연다
- [ ] **Step 4: 커밋한다**

```bash
git add -A content assets docs templates scripts
git commit -m "4단계: 검토 지적을 반영한다"
```

---

### Task 10: 5단계 배포 — 사용자 확인 뒤에만

- [ ] **Step 1: 배포 전 사실 확인**
  - 각 앱 `facts.json` 의 `describesVersion` 과 ASC 라이브 버전을 대조한다
    (`~/.claude/skills/asc-upload/asc_client.py` 로 `appStoreVersions` 조회, 읽기만)
  - 라이브가 아직 그 버전이 아니면 사용자에게 알린다. 예: BrushWorks 1.0.1 Pro 가 아직 심사 전이면 Pro 블록이 실제 앱과 다르다
  - 사용자가 "그대로 배포", "그 앱 Pro 블록 잠시 숨김", "배포 연기" 중에서 고른다
- [ ] **Step 2: 시행일을 배포일로 맞추고 다시 빌드와 검사를 한다**

```bash
python3 - <<'EOF'
import json, glob, datetime
today = datetime.date.today().isoformat()
for p in glob.glob("content/apps/*/*.json"):
    if p.endswith("facts.json"):
        continue
    d = json.load(open(p, encoding="utf-8"))
    if "privacy" in d:
        d["privacy"]["effectiveDate"] = today
        open(p, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False, indent=1) + "\n")
EOF
python3 scripts/build.py && python3 scripts/check.py --release
```

Expected: `통과`

- [ ] **Step 3: 사용자 확인을 받고 합친다**

```bash
git add -A content docs && git commit -m "배포: 시행일을 배포일로 맞춘다"
git switch main && git pull --ff-only && git merge --no-ff site-v1 -m "kvndh.com 사이트 v1 을 합친다"
git push origin main
```

- [ ] **Step 4: 공개 폴더를 `/docs` 로 바꾼다**

```bash
gh api -X PUT repos/KVNDH/KVNDH.github.io/pages -f cname=kvndh.com -F https_enforced=true \
  -f 'source[branch]=main' -f 'source[path]=/docs'
```

- [ ] **Step 5: 확인한다** (Pages 빌드 `status` 가 `built` 가 될 때까지 기다린 뒤)

```bash
gh api repos/KVNDH/KVNDH.github.io/pages --jq '{status,cname,https_enforced,protected_domain_state,source}'
for u in / /ko/ /en/ /ja/ /zh-hans/ /zh-hant/ /de/ /es/ /pt-br/ /app-ads.txt /sitemap.xml /robots.txt \
         /support/snapline.html /support/privacy-none.html /support/tapey-privacy.html /nope/; do
  printf '%-34s %s\n' "$u" "$(curl -s -o /dev/null -w '%{http_code}' https://kvndh.com$u)"
done
for app in brushworks life-tyde snapline tapey dice-master; do for k in "" support/ privacy/; do
  printf '%-40s %s\n' "/ko/$app/$k" "$(curl -s -o /dev/null -w '%{http_code}' https://kvndh.com/ko/$app/$k)"
done; done
curl -s -o /dev/null -w '%{http_code} %{redirect_url}\n' https://kvndh.github.io/support/brushworks.html
curl -s -o /dev/null -w '%{http_code} %{redirect_url}\n' http://www.kvndh.com/
```

Expected:
- `/nope/` 만 404 이고 나머지는 200 이다
- 두 리다이렉트는 301 이고 대상이 `kvndh.com` 이다

- [ ] **Step 6: 되돌리기 기준**
  - 5단계에서 `app-ads.txt` 나 `/support/` 가 200 이 아니면 즉시 공개 폴더를 `/` 로 되돌린다
  - 되돌리기: 같은 `gh api` 명령에서 `source[path]=/`
  - 되돌린 뒤 원인을 찾는다
- [ ] **Step 7: HQ 가 결과를 짧게 보고한다**
  - `_design/specs` 에 배포일과 결과를 한 줄 적어 커밋하고 푸시한다
