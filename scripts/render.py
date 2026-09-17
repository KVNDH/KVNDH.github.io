"""페이지 HTML 을 만든다. 틀은 templates/*.html (string.Template), 모양은 C안(Dark Gallery)."""
from __future__ import annotations

import json
import re
from string import Template

from sitelib import Site, app_store_url, esc, page_path

KIND_UI_KEY = {"about": "navAbout", "support": "navSupport", "privacy": "navPrivacy"}
TILE_POSITIONS = ["t-feature", "t-p2", "t-p3", "t-p4", "t-p5"]
GLOBE = (
    '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/>'
    '<path d="M3 12h18M12 3c2.4 2.6 3.7 5.6 3.7 9s-1.3 6.4-3.7 9c-2.4-2.6-3.7-5.6-3.7-9S9.6 5.6 12 3z"/></svg>'
)


def tpl(site: Site, name: str) -> Template:
    return Template((site.root / "templates" / name).read_text(encoding="utf-8"))


def css(site: Site) -> str:
    return (site.root / "templates" / "style.css").read_text(encoding="utf-8")


def accent_style(app: dict) -> str:
    style = (
        f"--acc:{app['accent']};--ink:{app['accentText']};--glow:{app['glow']};"
        f"--p-acc:{app['paperAccent']}"
    )
    if app.get("button"):
        style += f";--btn:{app['button']};--btn-tx:{app['buttonText']}"
    return style


def asset(slug: str, name: str) -> str:
    return f"/assets/{slug}/{name}"


def shot_path(site: Site, slug: str, lang: str, index: int = 1) -> str:
    name = f"{index:02d}.webp"
    for code in (lang, "en", "ko"):
        if (site.root / "assets" / slug / "shots" / code / name).exists():
            return asset(slug, f"shots/{code}/{name}")
    raise FileNotFoundError(f"no screenshot {name} for {slug}")


def fill(text: str, **values: str) -> str:
    for key, value in values.items():
        text = text.replace("{" + key + "}", value)
    return text


def items(values: list[str]) -> str:
    return "".join(f"<li>{esc(v)}</li>" for v in values)


def paragraphs(values: list[str], cls: str = "") -> str:
    attr = f' class="{cls}"' if cls else ""
    return "".join(f"<p{attr}>{esc(v)}</p>" for v in values)


def shot_alt(site: Site, copy: dict, lang: str) -> str:
    return copy.get("hero", {}).get("shotAlt") or f'{copy["name"]} {site.ui[lang]["screenshot"]}'


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


def lang_links(site: Site, lang: str, slug: str | None, kind: str) -> str:
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
    return "".join(entries)


def lang_menu(site: Site, lang: str, slug: str | None, kind: str) -> str:
    label = esc(site.ui[lang]["language"])
    return (
        f'<details class="lang"><summary aria-label="{label}">{GLOBE}'
        f'<span>{esc(site.lang(lang)["label"])}</span></summary>'
        f'<ul aria-label="{label}">{lang_links(site, lang, slug, kind)}</ul></details>'
    )


def hub_footer(site: Site, lang: str) -> str:
    ui = site.ui[lang]
    email = site.config["contact"]
    privacy = "".join(
        f'<li><a href="{page_path(lang, app["slug"], "privacy")}">{esc(site.app_copy(app["slug"], lang)["name"])}</a></li>'
        for app in site.apps if site.has_pages(app["slug"], lang)
    )
    privacy_block = f'<div><h2>{esc(ui["navPrivacy"])}</h2><ul>{privacy}</ul></div>' if privacy else "<div></div>"
    return (
        '<footer class="sf">'
        f'<div class="sf-l"><a class="wm" href="{page_path(lang)}">kvndh</a></div>'
        f'<div><h2>{esc(ui["contactTitle"])}</h2><ul><li><a href="mailto:{email}">{email}</a></li></ul></div>'
        f"{privacy_block}"
        f'<div class="sf-l"><h2>{esc(ui["language"])}</h2><ul class="langs">{lang_links(site, lang, None, "about")}</ul></div>'
        '<p class="copy">© kvndh</p>'
        "</footer>"
    )


def app_footer(site: Site, lang: str, slug: str) -> str:
    ui = site.ui[lang]
    email = site.config["contact"]
    name = site.app_copy(slug, lang)["name"]
    return (
        '<footer class="sf-c">'
        f'<a class="wm" href="{page_path(lang)}">kvndh</a>'
        f'<span>{esc(ui["contactTitle"])} <a href="mailto:{email}">{email}</a></span>'
        f'<a href="{page_path(lang, slug, "privacy")}">{esc(name)} {esc(ui["navPrivacy"])}</a>'
        '<p class="copy">© kvndh</p>'
        "</footer>"
    )


def app_bar(site: Site, lang: str, slug: str, current: str) -> str:
    ui, app, copy = site.ui[lang], site.app(slug), site.app_copy(slug, lang)
    tabs = []
    for kind in ("about", "support", "privacy"):
        mark = ' aria-current="page"' if kind == current else ""
        tabs.append(f'<li><a href="{page_path(lang, slug, kind)}"{mark}>{esc(ui[KIND_UI_KEY[kind]])}</a></li>')
    return tpl(site, "app_bar.html").substitute(
        name=esc(copy["name"]),
        about=page_path(lang, slug),
        icon=asset(slug, "icon-180.webp"),
        tabs="".join(tabs),
        store=app_store_url(app["appStoreId"]),
        get=esc(ui["getOnAppStore"]),
    )


def page(site: Site, *, lang: str, slug: str | None, kind: str, title: str, description: str,
         content: str, footer: str, bar: str = "", page_style: str = "", extra_head: str = "",
         og_image: str = "/assets/og.jpg") -> str:
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
        skip_label=esc(site.ui[lang]["skip"]),
        page_style=esc(page_style),
        hub_path=page_path(lang),
        lang_menu=lang_menu(site, lang, slug, kind),
        app_bar=bar,
        content=content,
        footer=footer,
    )


def render_hub(site: Site, lang: str) -> str:
    ui = site.ui[lang]
    tiles = []
    for position, app in zip(TILE_POSITIONS, [a for a in site.apps if site.app_copy(a["slug"], lang)]):
        slug = app["slug"]
        copy = site.app_copy(slug, lang)
        linked = site.has_pages(slug, lang)
        name = (
            f'<a class="tile-link" href="{page_path(lang, slug)}">{esc(copy["name"])}</a>' if linked
            else esc(copy["name"])
        )
        tiles.append(tpl(site, "tile.html").substitute(
            position=position,
            style=esc(accent_style(app)),
            icon=asset(slug, "icon-180.webp"),
            name=name,
            subtitle=esc(copy["subtitle"]),
            hook=f'<p class="hook">{esc(copy["summary"])}</p>' if position == "t-feature" else "",
            more=f'<span class="more" aria-hidden="true">{esc(ui["learnMore"])} →</span>' if linked else "",
            store=app_store_url(app["appStoreId"]),
            store_label=esc(fill(ui["storeLabel"], name=copy["name"])),
            crop=esc(app.get("shotCrop", "")),
            shot=shot_path(site, slug, lang),
            shot_alt=esc(shot_alt(site, copy, lang)),
        ))
    names = ", ".join(site.app_copy(a["slug"], lang)["name"] for a in site.apps if site.app_copy(a["slug"], lang))
    content = tpl(site, "hub.html").substitute(title=esc(ui["hubMetaTitle"]), tiles="\n".join(tiles))
    return page(site, lang=lang, slug=None, kind="about", title=ui["hubMetaTitle"], description=names,
                content=content, footer=hub_footer(site, lang))


def glyph(site: Site, slug: str, name: str) -> str:
    """붓 그림. assets/<app>/glyphs/<name>.svg 가 있으면 인라인(강조색을 따른다), 없으면 CSS 도형."""
    path = site.root / "assets" / slug / "glyphs" / f"{name}.svg"
    if not path.exists():
        return f'<span class="g g-{esc(name)}"></span>'
    svg = path.read_text(encoding="utf-8").strip()
    svg = re.sub(r"<\?xml[^>]*>\s*", "", svg)
    svg = re.sub(r'\s(?:role|aria-label)="[^"]*"', "", svg)
    svg = svg.replace("<svg ", '<svg aria-hidden="true" focusable="false" ', 1)
    return f'<span class="g-svg">{svg}</span>'


def render_visual(site: Site, lang: str, slug: str, visual: dict) -> str:
    kind = visual["type"]
    if kind == "crop":
        focus = f' style="--cy:{esc(visual["focus"])}"' if visual.get("focus") else ""
        return (
            f'<figure class="feat-vis crop"{focus}><img src="{shot_path(site, slug, lang, visual.get("shot", 1))}" '
            f'alt="{esc(visual["alt"])}" loading="lazy"><figcaption>{esc(visual["caption"])}</figcaption></figure>'
        )
    if kind == "kit":
        tools = "".join(
            ('<li class="on">' if tool.get("on") else "<li>")
            + (glyph(site, slug, tool["glyph"]) if tool.get("glyph") else "")
            + f'<b>{esc(tool["name"])}</b><small>{esc(tool["desc"])}</small></li>'
            for tool in visual["items"]
        )
        rows = "".join(
            f'<div class="kit-r"><p>{esc(row["label"])}<b>{esc(row["value"])}</b></p>{meter(row)}</div>'
            for row in visual.get("rows", [])
        )
        plain = "" if any(tool.get("glyph") for tool in visual["items"]) else " kit-b--plain"
        return (
            f'<div class="feat-vis kit" role="img" aria-label="{esc(visual["label"])}">'
            f'<ul class="kit-b{plain}">{tools}</ul>{rows}</div>'
        )
    raise ValueError(f"unknown feature visual: {kind}")


def meter(row: dict) -> str:
    if row.get("meter") == "ticks":
        on = ' class="on"'
        marks = "".join(
            f'<i style="--i:{i}"{on if i == row.get("on") else ""}></i>' for i in range(1, row["count"] + 1)
        )
        return f'<div class="ticks">{marks}</div>'
    if row.get("meter") == "levels":
        return '<div class="lv">' + "".join(f'<i style="--i:{i}"></i>' for i in range(1, row["count"] + 1)) + "</div>"
    return ""


def card_extra(visual: dict | None) -> tuple[str, bool]:
    """카드 안 장식. (html, 불릿 대신 쓰는지)"""
    if not visual:
        return "", False
    if visual["type"] == "play":
        return f'<div class="play" aria-hidden="true"><b></b><i></i><span>{esc(visual["label"])}</span></div>', False
    if visual["type"] == "chips":
        return f'<ul class="chips">{items(visual["items"])}</ul>', True
    raise ValueError(f"unknown card visual: {visual['type']}")


def render_sections(site: Site, lang: str, slug: str, sections: list[dict]) -> str:
    out, cards, feature_count = [], [], 0

    def flush_cards() -> None:
        if cards:
            out.append('<section class="duo">' + "".join(cards) + "</section>")
            cards.clear()

    for number, section in enumerate(sections, 1):
        kick = f'<p class="kick">{number:02d}</p>'
        heading = f'<h2>{esc(section["title"])}</h2>'
        body = paragraphs(section["body"], "body")
        bullets = f'<ul class="pts">{items(section["bullets"])}</ul>' if section.get("bullets") else ""
        if section["layout"] == "card":
            extra, replaces = card_extra(section.get("visual"))
            tail = extra if replaces else extra + bullets
            cards.append(f'<div class="card">{kick}{heading}{body}{tail}</div>')
            continue
        flush_cards()
        feature_count += 1
        reverse = " feat-rev" if feature_count % 2 == 0 else ""
        out.append(
            f'<section class="feat{reverse}">{render_visual(site, lang, slug, section["visual"])}'
            f"<div>{kick}{heading}{body}{bullets}</div></section>"
        )
    flush_cards()
    return "\n".join(out)


def render_pro(site: Site, lang: str, pro: dict | None) -> str:
    """Pro 는 고급 기능으로만 소개한다. 가격이나 구매 방식은 적지 않는다."""
    if not pro:
        return ""
    return tpl(site, "pro.html").substitute(
        kick=esc(pro["kick"]),
        title=esc(pro["title"]).replace("\n", "<br>"),
        items=items(pro["items"]),
    )


def render_app(site: Site, lang: str, slug: str) -> str:
    ui, app, copy = site.ui[lang], site.app(slug), site.app_copy(slug, lang)
    email = site.config["contact"]
    content = tpl(site, "app.html").substitute(
        icon=asset(slug, "icon-360.webp"),
        name=esc(copy["name"]),
        subtitle=esc(copy["subtitle"]),
        hook=esc(copy["hero"]["hook"]),
        store=app_store_url(app["appStoreId"]),
        get=esc(ui["getOnAppStore"]),
        meta=f'<span class="meta">{esc(copy["hero"]["meta"])}</span>' if copy["hero"].get("meta") else "",
        shot=shot_path(site, slug, lang),
        shot_alt=esc(shot_alt(site, copy, lang)),
        sections=render_sections(site, lang, slug, copy["sections"]),
        pro=render_pro(site, lang, copy.get("pro")),
        help_title=esc(ui["navSupport"]),
        help_body=esc(ui["helpBody"]),
        support=page_path(lang, slug, "support"),
        support_label=esc(ui["supportPage"]),
        email=email,
    )
    return page(site, lang=lang, slug=slug, kind="about",
                title=f'{copy["name"]}: {copy["subtitle"]}', description=copy["summary"],
                content=content, footer=app_footer(site, lang, slug),
                bar=app_bar(site, lang, slug, "about"), page_style=accent_style(app),
                extra_head=f'<meta name="apple-itunes-app" content="app-id={app["appStoreId"]}">',
                og_image=asset(slug, "og.jpg"))


def render_support(site: Site, lang: str, slug: str) -> str:
    ui, app, copy = site.ui[lang], site.app(slug), site.app_copy(slug, lang)
    faq = "".join(f'<details><summary>{esc(f["q"])}</summary>{paragraphs(f["a"])}</details>' for f in copy["faq"])
    content = tpl(site, "support.html").substitute(
        icon=asset(slug, "icon-180.webp"),
        name=esc(copy["name"]),
        title=esc(ui["faqTitle"]),
        faq=faq,
        contact_title=esc(ui["contactTitle"]),
        contact_body=esc(ui["contactBody"]),
        email=site.config["contact"],
    )
    return page(site, lang=lang, slug=slug, kind="support", title=f'{copy["name"]} {ui["navSupport"]}',
                description=copy["summary"], content=content, footer=app_footer(site, lang, slug),
                bar=app_bar(site, lang, slug, "support"), page_style=accent_style(app),
                og_image=asset(slug, "og.jpg"))


def privacy_section(number: int, section: dict) -> str:
    html = f'<section id="p{number}"><h2><span>{number:02d}</span>{esc(section["title"])}</h2>'
    html += paragraphs(section["paragraphs"])
    if section.get("bullets"):
        html += f'<ul>{items(section["bullets"])}</ul>'
    if section.get("pairs"):
        rows = []
        for pair in section["pairs"]:
            value = esc(pair["value"])
            if "@" in pair["value"]:
                value = f'<a href="mailto:{value}">{value}</a>'
            rows.append(f'<dt>{esc(pair["label"])}</dt><dd>{value}</dd>')
        html += f'<dl>{"".join(rows)}</dl>'
    return html + "</section>"


def render_privacy(site: Site, lang: str, slug: str) -> str:
    ui, app, copy = site.ui[lang], site.app(slug), site.app_copy(slug, lang)
    policy = copy["privacy"]
    toc = "".join(f'<li><a href="#p{i}">{esc(s["title"])}</a></li>' for i, s in enumerate(policy["sections"], 1))
    body = "".join(privacy_section(i, s) for i, s in enumerate(policy["sections"], 1))
    date = esc(policy["effectiveDate"])
    content = tpl(site, "privacy.html").substitute(
        toc_label=esc(ui["toc"]),
        toc=toc,
        icon=asset(slug, "icon-180.webp"),
        name=esc(copy["name"]),
        title=esc(ui["navPrivacy"]),
        effective_label=esc(ui["effectiveDate"]),
        date=date,
        summary_label=esc(ui["summaryLabel"]),
        summary=esc(policy["summary"]),
        intro=paragraphs(policy["intro"]),
        body=body,
        end=fill(esc(ui["effectiveFrom"]), date=date),
    )
    return page(site, lang=lang, slug=slug, kind="privacy", title=policy["title"], description=policy["summary"],
                content=content, footer=app_footer(site, lang, slug),
                bar=app_bar(site, lang, slug, "privacy"), page_style=accent_style(app),
                og_image=asset(slug, "og.jpg"))


def language_items(site: Site) -> str:
    return "".join(
        f'<li><a href="{page_path(option["code"])}" lang="{esc(option["htmlLang"])}">{esc(option["label"])}</a></li>'
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
