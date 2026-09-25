"""앱 저장소의 아이콘과 스토어 스크린샷을 assets/ 로 가져온다. ImageMagick(magick)이 필요하다.

원본 경로는 content/asset-sources.json (~/Desktop/CODING 기준).
사용: python3 scripts/import_assets.py            # 전부
      python3 scripts/import_assets.py tapey      # 일부
      python3 scripts/import_assets.py --looks    # 스토어 합성본과 번짐 바탕만(content/looks.json 도 고친다)

--looks 는 앱의 docs/store(shots.json 과 합성본)에서 첫 세 장을 언어마다 가져오고, 스토어 합성기
(~/Desktop/CODING/tools/storeshots)의 field() 로 같은 캡처에서 번짐 바탕을 다시 만든다(2026-09-26 B안).
store 가 없는 앱은 사이트 캡처 한 장으로 번짐을 만든다. 줄 모티프 앱은 번짐 없이 흰 바탕이다.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sitelib import ROOT, load_json  # noqa: E402

CODING = ROOT.parent
FONT = "/System/Library/Fonts/Helvetica.ttc"
STORE_LOCALE = {"ko": "ko", "en": "en-US", "ja": "ja", "zh-hans": "zh-Hans", "zh-hant": "zh-Hant",
                "de": "de-DE", "es": "es-ES", "pt-br": "pt-BR"}
PANO = 3                      # 첫 화면에 늘어놓는 장 수. App Store 검색 결과에 뜨는 장 수와 같다
FIELD_W, FIELD_H = 264, 574   # 번짐을 만드는 캔버스. 아이폰 1320x2868 의 1/5
PLAIN = {"mode": "blur", "base": "#F4F4F6", "mix": 0.4}   # store 가 없는 앱의 번짐


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


def storeshots():
    sys.path.insert(0, str(CODING / "tools" / "storeshots"))
    import storeshots as ss  # noqa: E402
    return ss


def field_look(ss, slug: str, screens: list, spec: dict) -> dict:
    """번짐 바탕을 assets/<slug>/field.webp 로 쓰고 평균색과 글자색을 돌려준다."""
    from PIL import ImageStat
    img = ss.field(screens, spec, FIELD_W, FIELD_H, round(FIELD_W * ss.GAP))
    img.save(ROOT / "assets" / slug / "field.webp", "WEBP", quality=72)
    r, g, b = (round(v) for v in ImageStat.Stat(img.convert("RGB")).mean)
    lum = (.2126 * r + .7152 * g + .0722 * b) / 255
    return {"mode": spec["mode"], "ink": "light" if lum < .5 else "dark", "color": f"#{r:02X}{g:02X}{b:02X}"}


def import_look(slug: str) -> dict | None:
    spec_src = load_json(ROOT / "content" / "asset-sources.json")[slug]
    ss = storeshots()
    dest = ROOT / "assets" / slug
    if not spec_src.get("store"):
        shots = spec_src.get("shots", {})
        first = (shots.get("en") or shots.get("ko") or [None])[0]
        if not first or not (CODING / first).exists():
            print("건너뜀(캡처 없음):", slug)
            return None
        return {**field_look(ss, slug, [ss.load_screen(CODING / first, None, FIELD_W)], PLAIN), "alts": {}}
    store = CODING / spec_src["store"]
    spec = load_json(store / "shots.json")
    alts: dict[str, list[str]] = {}
    for code, locale in STORE_LOCALE.items():
        folder = store / "screenshots" / "iphone" / locale
        if not (folder / "01.png").exists():
            continue
        out = dest / "store" / code
        out.mkdir(parents=True, exist_ok=True)
        for i in range(1, PANO + 1):
            magick(folder / f"{i:02d}.png", "-strip", "-resize", "480x", "-quality", "82", out / f"{i:02d}.webp")
        caps = spec["captions"].get(locale) or spec["captions"].get(spec.get("captionFrom", {}).get(locale, ""), [])
        alts[code] = [c.replace("\n", " ") for c in caps[:PANO]]
    if not alts:
        print("건너뜀(합성본 없음):", slug)
        return None
    if spec["mode"] == "line":
        (dest / "field.webp").unlink(missing_ok=True)
        return {"mode": "line", "ink": "dark", "color": spec.get("line", {}).get("bg", "#FFFFFF"), "alts": alts}
    repo = store.parents[1]
    device = spec["devices"]["iphone"]
    src = spec.get("fieldFrom") or "ko"
    cl = spec.get("captureFrom", {}).get(src, src)
    screens = [ss.load_screen(repo / c.format(locale=cl), device.get("crop"), FIELD_W) for c in device["captures"]]
    return {**field_look(ss, slug, screens, spec), "alts": alts}


def import_looks(slugs: list[str]) -> None:
    path = ROOT / "content" / "looks.json"
    looks = load_json(path) if path.exists() else {}
    for slug in slugs:
        found = import_look(slug)
        if found:
            looks[slug] = found
            print("모양:", slug, found["mode"], found["ink"], found["color"])
    path.write_text(json.dumps(dict(sorted(looks.items())), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def import_site_og() -> None:
    (ROOT / "assets").mkdir(exist_ok=True)
    magick("-size", "1200x630", "xc:#0A0A0B", "-fill", "#F2F2F3", "-font", FONT, "-pointsize", "150",
           "-gravity", "center", "-annotate", "+0+0", "kvndh", "-strip", "-quality", "85", ROOT / "assets" / "og.jpg")


def main(argv: list[str]) -> int:
    if argv and argv[0] == "--looks":
        import_looks(argv[1:] or list(load_json(ROOT / "content" / "asset-sources.json")))
        return 0
    slugs = argv or list(load_json(ROOT / "content" / "asset-sources.json"))
    for slug in slugs:
        import_app(slug)
        print("가져옴:", slug)
    if not argv:
        import_site_og()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
