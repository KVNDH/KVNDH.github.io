"""content/ 와 docs/ 를 검사한다.

사용:
  python3 scripts/check.py            # 지금 있는 언어와 앱만 검사
  python3 scripts/check.py --release  # 8개 언어 x 5개 앱이 모두 있어야 통과
  python3 scripts/check.py --content  # content/ 만 검사 (docs/ 를 보지 않는다. 여러 작업자가 동시에 돌릴 때)
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
    "ko": [r"한 ?번 구매", r"구독(?:이|은)? ?없", r"일회성 구매", r"고급 기능은 Pro", r"혼자서?\s?만[들듭드]", r"단순한 \S+(?:이|가) 아닙니다", r"(?:이|가) 아니라 .{1,30}입니다",
           r"뿐만 아니라", r"더 이상 .{0,12}필요", r"(?:앱|것)을 만듭니다"],
    "en": [r"one-time purchase", r"no subscription", r"\bit'?s not\b.{1,40}\bit'?s\b", r"\bnot\b[^.]{1,40}\bbut\b"],
}

MARKETING_KEYS = ("summary", "subtitle", "hero", "sections", "pro")
HAEYO_OK = ("필요", "중요", "주요", "수요", "세요", "개요", "강요")
NUMBER = re.compile(r"\d+(?:[.,]\d+)*")
REQUIRED_KEYS = ("name", "subtitle", "summary", "hero", "sections", "faq", "privacy")
LAYOUTS = {"feat": ("crop", "kit"), "card": ("play", "chips", None)}
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
    """ko 에서 명사형으로 끝나야 하는 항목들."""
    for i, section in enumerate(copy.get("sections", [])):
        for j, item in enumerate(section.get("bullets", [])):
            yield f"sections[{i}].bullets[{j}]", item
        visual = section.get("visual") or {}
        for j, item in enumerate(visual.get("items", [])):
            if isinstance(item, str):
                yield f"sections[{i}].visual.items[{j}]", item
            else:
                yield f"sections[{i}].visual.items[{j}].desc", item["desc"]
    for j, item in enumerate((copy.get("pro") or {}).get("items", [])):
        yield f"pro.items[{j}]", item
    meta = (copy.get("hero") or {}).get("meta")
    if meta:
        yield "hero.meta", meta


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


def visual_shape(visual: dict | None):
    if not visual:
        return None
    return (visual["type"], len(visual.get("items", [])), len(visual.get("rows", [])))


def shape(copy: dict) -> dict:
    pro = copy.get("pro") or {}
    return {
        "sections": [
            (s.get("layout"), len(s.get("body", [])), len(s.get("bullets", [])), visual_shape(s.get("visual")))
            for s in copy["sections"]
        ],
        "faq": [len(f["a"]) for f in copy["faq"]],
        "pro": bool(copy.get("pro")),
        "pro items": len(pro.get("items", [])),
        "hero meta": bool(copy["hero"].get("meta")),
        "privacy": [
            (len(s.get("paragraphs", [])), len(s.get("bullets", [])), len(s.get("pairs", [])))
            for s in copy["privacy"]["sections"]
        ],
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
            for i, section in enumerate(copy["sections"]):
                visual_type = (section.get("visual") or {}).get("type")
                if section.get("layout") not in LAYOUTS or visual_type not in LAYOUTS[section.get("layout")]:
                    problems.append(f"{slug}/{code}: sections[{i}] layout/visual 조합이 틀림 ({section.get('layout')}, {visual_type})")
            if "hook" not in copy["hero"]:
                problems.append(f"{slug}/{code}: hero.hook 없음")
            if "summary" not in copy["privacy"]:
                problems.append(f"{slug}/{code}: privacy.summary 없음")
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
    if "--content" in argv:
        pass
    elif out.exists():
        problems += check_output(site, out) + check_fresh(site, out)
    else:
        problems.append("docs/ 없음. 먼저 python3 scripts/build.py")
    for problem in problems:
        print("✗", problem)
    print("통과" if not problems else f"문제 {len(problems)}건")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
