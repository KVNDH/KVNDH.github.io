"""사이트 문구를 사람이 읽고 고치는 txt 로 내보내고, 고친 txt 를 content/ 에 되돌려 넣는다.

사용:
  python3 scripts/copy_txt.py export ko _design/copy/copy-ko.txt
  python3 scripts/copy_txt.py apply ko _design/copy/copy-ko.txt

txt 한 줄은 `[키] 문장` 이다. 키는 건드리지 않고 문장만 고친다. 줄바꿈은 `\\n` 으로 적는다.
없는 키는 거부하고, txt 에 없는 줄은 그대로 둔다.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sitelib import ROOT, load_json  # noqa: E402

SKIP_KEYS = {"layout", "type", "glyph", "meter", "focus", "effectiveDate", "shot"}
LINE = re.compile(r"^\[([^\]]+)\] ?(.*)$")
SECTION_LABELS = {
    "name": "기본", "hero": "첫 화면", "sections": "기능", "pro": "Pro",
    "faq": "자주 묻는 질문", "privacy": "개인정보 처리방침",
}


def _leaves(obj, path: list):
    if isinstance(obj, str):
        yield path, obj
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            yield from _leaves(value, path + [i])
    elif isinstance(obj, dict):
        for key, value in obj.items():
            if key not in SKIP_KEYS:
                yield from _leaves(value, path + [key])


def _files(root: Path, lang: str) -> list[tuple[str, Path]]:
    config = load_json(root / "content" / "site.json")
    files = [("ui", root / "content" / "i18n" / f"{lang}.json")]
    for app in config["apps"]:
        files.append((app["slug"], root / "content" / "apps" / app["slug"] / f"{lang}.json"))
    return [(prefix, path) for prefix, path in files if path.exists()]


def _key(prefix: str, path: list) -> str:
    return ".".join([prefix] + [str(p) for p in path])


def export(root: Path, lang: str) -> str:
    out = [
        f"# kvndh.com 문구 ({lang})",
        "# 줄 맨 앞의 [키] 는 그대로 두고, 뒤의 문장만 고치면 됩니다.",
        "# 한 항목은 한 줄입니다. 줄바꿈이 필요한 곳은 \\n 으로 적습니다.",
        "",
    ]
    for prefix, path in _files(root, lang):
        data = load_json(path)
        title = "공통 화면 문구" if prefix == "ui" else f'{data.get("name", prefix)} ({prefix})'
        out += [f"==================== {title} ====================", ""]
        group = None
        for leaf_path, text in _leaves(data, []):
            head = leaf_path[0]
            if prefix != "ui":
                if head == "sections":
                    section = data["sections"][leaf_path[1]]
                    current = f'기능 {leaf_path[1] + 1:02d} ({section.get("layout")}, {section.get("visual", {}).get("type")})'
                elif head == "privacy" and len(leaf_path) > 2 and leaf_path[1] == "sections":
                    current = f"개인정보 처리방침 {leaf_path[2] + 1:02d}절"
                else:
                    current = SECTION_LABELS.get(head, "기본")
                if current != group:
                    out += ["", f"## {current}"]
                    group = current
            out.append(f"[{_key(prefix, leaf_path)}] {text.replace(chr(10), chr(92) + 'n')}")
        out.append("")
    return "\n".join(out) + "\n"


def _set(data, path: list, value: str) -> bool:
    node = data
    for part in path[:-1]:
        node = node[part]
    last = path[-1]
    if not isinstance(node[last], str):
        raise KeyError(f"not a text field: {path}")
    if node[last] == value:
        return False
    node[last] = value
    return True


def _parse_path(parts: list[str]) -> list:
    return [int(p) if p.isdigit() else p for p in parts]


def apply(root: Path, lang: str, text: str) -> list[str]:
    files = dict(_files(root, lang))
    loaded = {prefix: load_json(path) for prefix, path in files.items()}
    changed: list[str] = []
    for raw in text.splitlines():
        match = LINE.match(raw)
        if not match:
            continue
        key, value = match.group(1), match.group(2).rstrip().replace("\\n", "\n")
        prefix, *rest = key.split(".")
        if prefix not in loaded or not rest:
            raise KeyError(f"unknown key: {key}")
        path = _parse_path(rest)
        try:
            if _set(loaded[prefix], path, value):
                changed.append(key)
        except (KeyError, IndexError, TypeError) as error:
            raise KeyError(f"unknown key: {key}") from error
    for prefix in {k.split(".")[0] for k in changed}:
        files[prefix].write_text(json.dumps(loaded[prefix], ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return changed


def main(argv: list[str]) -> int:
    if len(argv) != 3 or argv[0] not in ("export", "apply"):
        print(__doc__)
        return 2
    command, lang, target = argv
    path = Path(target)
    if command == "export":
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(export(ROOT, lang), encoding="utf-8")
        print(f"내보냄: {path}")
    else:
        changed = apply(ROOT, lang, path.read_text(encoding="utf-8"))
        print(f"바뀐 항목 {len(changed)}개")
        for key in changed:
            print(" ", key)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
