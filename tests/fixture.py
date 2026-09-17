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
        "sections": [{"title": "t1", "body": ["b"], "bullets": ["x"]}],
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
    for rel in ("assets/demo/icon-180.webp", "assets/demo/icon-360.webp", "assets/demo/og.png",
                "assets/demo/shots/en/01.webp", "assets/og.png"):
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
