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
        # 앱마다 스토어 스크린샷에서 가져온 모양(번짐 색, 글자색, 합성본 문구). import_assets.py 가 만든다
        looks = content / "looks.json"
        self.looks: dict[str, dict] = load_json(looks) if looks.exists() else {}
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
