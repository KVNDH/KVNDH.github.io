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
