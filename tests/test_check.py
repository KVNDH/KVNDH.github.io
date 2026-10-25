from __future__ import annotations

import json
import unittest

from tests.fixture import make_site
import build
import check
from sitelib import Site


def site_with(lang: str, field: str, text: str) -> Site:
    site = Site(make_site())
    site.copy[("demo", lang)][field] = text
    return site


class CopyRulesTest(unittest.TestCase):
    def test_clean_copy_passes(self):
        self.assertEqual(check.check_copy(Site(make_site())), [])

    def test_banned_ko_phrases(self):
        for text in ["혁신적인 그림 앱", "지금 바로 받아 보세요", "사진은 기기 밖으로 나가지 않습니다",
                     "iOS 앱을 혼자 만듭니다", "단순한 필터가 아닙니다", "여러분의 사진"]:
            self.assertTrue(check.check_copy(site_with("ko", "summary", text)), text)

    def test_banned_en_phrases(self):
        for text in ["A seamless way to paint", "Not just a filter, but a canvas",
                     "Your photos never leave your device"]:
            self.assertTrue(check.check_copy(site_with("en", "summary", text)), text)

    def test_banned_characters(self):
        for text in ["위치·크기", "붓 — 나이프", "【안내】", "좋습니다!"]:
            self.assertTrue(check.check_copy(site_with("ko", "summary", text)), text)

    def test_ko_haeyo(self):
        self.assertTrue(check.check_copy(site_with("ko", "summary", "사진을 골라요.")))
        self.assertTrue(check.check_copy(site_with("ko", "summary", "바로 써요")))
        self.assertEqual(check.check_copy(site_with("ko", "summary", "필요한 것만 남깁니다.")), [])
        self.assertEqual(check.check_copy(site_with("ko", "summary", "메일로 보내 주세요.")), [])

    def test_ko_bullets_must_be_noun_endings(self):
        site = Site(make_site())
        site.copy[("demo", "ko")]["sections"][0]["bullets"] = ["붓이 세 자루입니다"]
        self.assertTrue(check.check_copy(site))
        site.copy[("demo", "ko")]["sections"][0]["bullets"] = ["붓 세 자루"]
        self.assertEqual(check.check_copy(site), [])

    def test_ko_visual_items_and_meta_must_be_noun_endings(self):
        site = Site(make_site())
        site.copy[("demo", "ko")]["sections"][1]["visual"]["items"][0]["desc"] = "색이 섞입니다"
        self.assertTrue(check.check_copy(site))
        site = Site(make_site())
        site.copy[("demo", "ko")]["hero"]["meta"] = "무료로 씁니다."
        self.assertTrue(check.check_copy(site))

    def test_purchase_model_is_not_marketing(self):
        for text in ["무료, Pro는 한 번 구매", "구독 없이 씁니다", "고급 기능은 Pro"]:
            self.assertTrue(check.check_copy(site_with("ko", "summary", text)), text)
        self.assertTrue(check.check_copy(site_with("en", "summary", "A one-time purchase, no subscription")))
        site = Site(make_site())
        site.copy[("demo", "ko")]["faq"][0]["a"] = ["같은 계정이면 한 번 구매한 Pro가 복원됩니다."]
        self.assertEqual(check.check_copy(site), [])

    def test_ui_strings_are_checked(self):
        site = Site(make_site())
        site.ui["ko"]["learnMore"] = "놀라운 앱"
        self.assertTrue(check.check_copy(site))


class StructureTest(unittest.TestCase):
    def test_matching_structure_passes(self):
        self.assertEqual(check.check_structure(Site(make_site()), release=False), [])

    def test_section_count_mismatch_fails(self):
        site = Site(make_site())
        site.copy[("demo", "en")]["sections"].append({"title": "x", "body": [], "bullets": []})
        self.assertTrue(check.check_structure(site, release=False))

    def test_privacy_needs_twelve_sections(self):
        site = Site(make_site())
        site.copy[("demo", "en")]["privacy"]["sections"].pop()
        self.assertTrue(check.check_structure(site, release=False))

    def test_wrong_layout_visual_pair_fails(self):
        site = Site(make_site())
        site.copy[("demo", "ko")]["sections"][0]["layout"] = "card"
        self.assertTrue(check.check_structure(site, release=False))

    def test_visual_item_count_mismatch_fails(self):
        site = Site(make_site())
        site.copy[("demo", "en")]["sections"][3]["visual"]["items"].append("d")
        self.assertTrue(check.check_structure(site, release=False))

    def test_missing_ui_key_fails(self):
        site = Site(make_site())
        del site.ui["en"]["toc"]
        self.assertTrue(check.check_structure(site, release=False))

    def test_release_requires_all_languages(self):
        self.assertTrue(check.check_structure(Site(make_site()), release=True))

    def add_unreleased(self, root, slug, langs=()):
        site_json = root / "content" / "site.json"
        data = json.loads(site_json.read_text(encoding="utf-8"))
        data["apps"].append({"slug": slug, "accent": "#E63946", "accentText": "#F46A74",
                             "glow": "rgba(230,57,70,.28)", "paperAccent": "#B02C37", "unreleased": True})
        site_json.write_text(json.dumps(data), encoding="utf-8")
        for lang in langs:
            src = root / "content" / "apps" / "demo" / f"{lang}.json"
            dest = root / "content" / "apps" / slug / f"{lang}.json"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    def test_release_skips_icon_only_unreleased_app(self):
        # 문구가 한 언어도 없는 출시 전 앱은 페이지를 만들지 않는다. 흐린 아이콘만 뜬다(2026-09-21 OnPace).
        root = make_site(langs=("ko", "en", "ja"))
        self.add_unreleased(root, "later")
        self.assertEqual(check.check_structure(Site(root), release=True), [])

    def test_release_still_requires_all_languages_once_copy_starts(self):
        root = make_site(langs=("ko", "en", "ja"))
        self.add_unreleased(root, "later", langs=("ko",))
        self.assertTrue(check.check_structure(Site(root), release=True))


class FactsTest(unittest.TestCase):
    def test_unknown_number_in_marketing_copy_fails(self):
        self.assertTrue(check.check_facts(site_with("ko", "summary", "붓 7자루")))

    def test_known_numbers_pass_with_separators(self):
        site = site_with("ko", "summary", "붓 7자루, 긴 변 3,072px, 1.5배")
        site.facts["demo"]["numbers"] = ["7", "3072", "1.5"]
        self.assertEqual(check.check_facts(site), [])

    def test_css_focus_value_is_not_a_fact(self):
        site = Site(make_site())
        site.copy[("demo", "ko")]["sections"][0]["visual"]["focus"] = "-170px"
        self.assertEqual(check.check_facts(site), [])

    def test_ads_app_privacy_must_name_admob(self):
        site = Site(make_site())
        site.facts["demo"]["ads"] = True
        self.assertTrue(check.check_facts(site))
        for lang in ("ko", "en"):
            site.copy[("demo", lang)]["privacy"]["sections"][8]["paragraphs"] = ["Google AdMob"]
        self.assertEqual(check.check_facts(site), [])

    def test_missing_facts_file_fails_when_pages_exist(self):
        site = Site(make_site())
        site.facts["demo"] = None
        self.assertTrue(check.check_facts(site))


class OutputTest(unittest.TestCase):
    def built(self):
        root = make_site()
        site = Site(root)
        build.build(site, root / "docs")
        return site, root / "docs"

    def edit(self, path, old, new):
        path.write_text(path.read_text(encoding="utf-8").replace(old, new), encoding="utf-8")

    def test_built_site_passes(self):
        site, out = self.built()
        self.assertEqual(check.check_output(site, out), [])
        self.assertEqual(check.check_fresh(site, out), [])

    def test_unreleased_app_without_store_id_passes(self):
        # ASC 레코드가 아직 없는 앱(2026-09-21 OnPace)도 흐린 아이콘으로는 올릴 수 있어야 한다.
        root = make_site()
        site_json = root / "content" / "site.json"
        data = json.loads(site_json.read_text(encoding="utf-8"))
        data["apps"].append({"slug": "later", "accent": "#E63946", "accentText": "#F46A74",
                             "glow": "rgba(230,57,70,.28)", "paperAccent": "#B02C37", "unreleased": True})
        site_json.write_text(json.dumps(data), encoding="utf-8")
        icon = root / "assets" / "later" / "icon-180.webp"
        icon.parent.mkdir(parents=True)
        icon.write_bytes(b"x")
        site = Site(root)
        build.build(site, root / "docs")
        self.assertEqual(check.check_output(site, root / "docs"), [])
        self.assertIn("later/icon-180.webp", (root / "docs" / "ko" / "index.html").read_text(encoding="utf-8"))

    def test_missing_app_ads_fails(self):
        site, out = self.built()
        (out / "app-ads.txt").unlink()
        self.assertTrue(check.check_output(site, out))

    def test_wrong_cname_fails(self):
        site, out = self.built()
        (out / "CNAME").write_text("example.com\n")
        self.assertTrue(check.check_output(site, out))

    def test_top_level_support_folder_fails(self):
        site, out = self.built()
        (out / "support").mkdir()
        (out / "support" / "x.html").write_text("<p>x</p>")
        self.assertTrue(check.check_output(site, out))

    def test_broken_internal_link_fails(self):
        site, out = self.built()
        self.edit(out / "ko" / "index.html", "</main>", '<a href="/ko/nope/">x</a></main>')
        self.assertTrue(check.check_output(site, out))

    def test_broken_anchor_fails(self):
        site, out = self.built()
        self.edit(out / "en" / "demo" / "privacy" / "index.html", 'id="p3"', 'id="px"')
        self.assertTrue(check.check_output(site, out))

    def test_external_image_fails(self):
        site, out = self.built()
        self.edit(out / "ko" / "index.html", "</main>", '<img src="https://cdn.example.com/a.png"></main>')
        self.assertTrue(check.check_output(site, out))

    def test_unknown_app_store_id_fails(self):
        site, out = self.built()
        self.edit(out / "ko" / "index.html", "/app/id123", "/app/id999")
        self.assertTrue(check.check_output(site, out))

    def test_stale_output_fails_freshness(self):
        site, out = self.built()
        self.edit(out / "ko" / "index.html", "</main>", "<p>edited</p></main>")
        self.assertTrue(check.check_fresh(site, out))


if __name__ == "__main__":
    unittest.main()
