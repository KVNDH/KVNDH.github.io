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
    names = ", ".join(site.app_copy(app["slug"], lang)["name"] for app in site.apps if site.app_copy(app["slug"], lang))
    content = tpl(site, "hub.html").substitute(title=esc(ui["hubMetaTitle"]), tiles="\n".join(tiles))
    return page(site, lang=lang, slug=None, kind="about", title=ui["hubMetaTitle"],
                description=names, content=content)


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
