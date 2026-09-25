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
    "skip", "language", "hubMetaTitle", "learnMore", "getOnAppStore", "screenshot",
    "navAbout", "navSupport", "navPrivacy", "helpBody", "supportPage", "faqTitle", "contactTitle", "contactBody", "effectiveDate", "summaryLabel",
    "toc", "notFound",
]


def write(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


def ui(lang: str) -> dict:
    values = {k: f"{lang} {k}" for k in UI_KEYS}
    values["storeLabel"] = "{name} store"
    values["effectiveFrom"] = "from {date}"
    return values


def privacy(lang: str) -> dict:
    sections = [{"title": f"s{i}", "paragraphs": ["p"], "bullets": []} for i in range(1, 13)]
    sections[9]["pairs"] = [{"label": "mail", "value": "kvndh36@naver.com"}]
    return {"title": f"{lang} privacy", "effectiveDate": "2026-09-17", "summary": "sum", "intro": ["intro"],
            "sections": sections}


def app_copy(lang: str) -> dict:
    return {
        "name": "Demo",
        "subtitle": "sub",
        "summary": "summary",
        "hero": {"hook": "hook"},
        "sections": [
            {"layout": "feat", "title": "title", "body": ["b"], "bullets": ["x"],
             "visual": {"type": "crop", "shot": 1, "alt": "alt", "caption": "cap"}},
            {"layout": "feat", "title": "kit", "body": ["b"], "bullets": [],
             "visual": {"type": "kit", "label": "kit", "items": [{"glyph": "gl", "name": "n", "desc": "d", "on": True}],
                        "rows": [{"label": "l", "value": "v", "meter": "ticks", "count": 3, "on": 2}]}},
            {"layout": "card", "title": "card", "body": ["b"], "bullets": ["y"], "visual": {"type": "play", "label": "play"}},
            {"layout": "card", "title": "chips", "body": ["b"], "bullets": [], "visual": {"type": "chips", "items": ["c"]}},
        ],
        "pro": {"kick": "Pro", "title": "first\nsecond", "items": ["p"]},
        "faq": [{"q": "q", "a": ["a"]}],
        "privacy": privacy(lang),
    }


def store(root: Path, lang: str, index: int) -> None:
    """스토어 합성본 한 장(assets/demo/store/<lang>/0N.webp)."""
    p = root / "assets" / "demo" / "store" / lang / f"{index:02d}.webp"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b"x")


def look(root: Path, ink: str, color: str, alts: dict | None = None) -> None:
    """import_assets.py 가 만드는 content/looks.json 과 번짐 그림."""
    write(root / "content" / "looks.json", {"demo": {"mode": "blur", "ink": ink, "color": color, "alts": alts or {}}})
    (root / "assets" / "demo" / "field.webp").write_bytes(b"x")


def make_site(langs=("ko", "en"), with_pages: bool = True, unreleased: bool = False) -> Path:
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
        "apps": [{"slug": "demo", "appStoreId": "123", "accent": "#A05B42", "accentText": "#E39C80",
                  "glow": "rgba(160,91,66,.5)", "paperAccent": "#8A4A34", "button": "#A05B42",
                  "buttonText": "#FFFFFF", "shotCrop": "--sw:196px"}]
                 + ([{"slug": "soon", "appStoreId": "456", "accent": "#FFB347", "accentText": "#FFB347",
                      "glow": "rgba(255,179,71,.28)", "paperAccent": "#8A5A14", "unreleased": True}]
                    if unreleased else []),
    })
    for lang in langs:
        write(content / "i18n" / f"{lang}.json", ui(lang))
        copy = app_copy(lang) if with_pages else {"name": "Demo", "subtitle": "sub", "summary": "summary"}
        write(content / "apps" / "demo" / f"{lang}.json", copy)
    write(content / "apps" / "demo" / "facts.json", {"describesVersion": "1.0.0", "numbers": [], "ads": False})
    if unreleased:
        for lang in langs:
            write(content / "apps" / "soon" / f"{lang}.json", app_copy(lang) | {"name": "Soon"})
        write(content / "apps" / "soon" / "facts.json", {"describesVersion": "1.0.0", "numbers": [], "ads": False})
        for rel in ("assets/soon/icon-180.webp", "assets/soon/icon-360.webp", "assets/soon/og.jpg",
                    "assets/soon/shots/en/01.webp"):
            q = root / rel
            q.parent.mkdir(parents=True, exist_ok=True)
            q.write_bytes(b"x")
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
