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
