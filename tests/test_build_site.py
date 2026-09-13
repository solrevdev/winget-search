import json
from datetime import datetime, timezone
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
import re
import shutil
import struct
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from build_site import ASSETS, SITEMAP_NS, build_site, git_modified, normalize_public_base_url


class Tags(HTMLParser):
    def __init__(self, document):
        super().__init__()
        self.tags = []
        self.feed(document)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))

    def attribute(self, tag, key, value, attribute):
        matches = [attrs[attribute] for name, attrs in self.tags
                   if name == tag and attrs.get(key) == value]
        if len(matches) != 1:
            raise AssertionError(f"expected one {tag} {key}={value}, got {matches}")
        return matches[0]


class BuildSiteTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="winget-seo-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        self.source.mkdir()
        self.output = self.root / "deploy"
        repo = Path(__file__).resolve().parents[1]
        for filename in (*ASSETS, "index.html", "sitemap.xml"):
            shutil.copy2(repo / filename, self.source / filename)
        shutil.copytree(repo / "vendor", self.source / "vendor")
        (self.source / "site_config.json").write_text(json.dumps({"public_base_url": "https://example.com/tools/"}))
        self.catalog = {"metadata": {"total": 2, "extracted_at": "2026-09-12T20:15:30.123456"},
                        "packages": [{"id": "Example.App", "name": "Example"}, {"id": "Example.Tool"}]}
        self.save_catalog()

    def save_catalog(self):
        (self.source / "packages.json").write_text(json.dumps(self.catalog), encoding="utf-8")

    def build(self, **kwargs):
        with patch("build_site.git_modified", return_value=None):
            return build_site(self.source, self.output, **kwargs)

    def test_url_rules_cover_custom_domains_and_github_pages(self):
        for raw, expected in (
            ("https://solrevdev.com/winget-search", "https://solrevdev.com/winget-search/"),
            ("https://example.com", "https://example.com/"),
            ("https://user.github.io/", "https://user.github.io/"),
            ("https://user.github.io/project/", "https://user.github.io/project/"),
            ("https://EXAMPLE.com:443/nested/project/", "https://example.com/nested/project/"),
        ):
            with self.subTest(raw=raw):
                self.assertEqual(normalize_public_base_url(raw), expected)

    def test_url_rules_reject_ambiguous_or_unsafe_values(self):
        for value in (None, "", "http://example.com/", "/project/", "https://",
                      "https://user:secret@example.com/", "https://example.com/?q=x",
                      "https://example.com/#x", "https://example.com/?", "https://example.com/#",
                      "https://example.com:abc/", "https://example.com:8080/", "https://bad..com/",
                      "https://example.com/a/../b", "https://example.com/%2e%2e/",
                      "https://example.com/a//b", "https://example.com/a\\b", "https://example.com/%QQ",
                      "https://example.com/space here", "https://example.com/%0a"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                normalize_public_base_url(value)

    def test_generated_metadata_and_redirect_share_one_public_url(self):
        for base in ("https://example.com", "https://user.github.io/project", "https://user.github.io/",
                     "https://solrevdev.com/winget-search/nested/", "https://example.com/a&b/"):
            with self.subTest(base=base):
                result = self.build(public_base_url=base)
                normalized = base.rstrip("/") + "/"
                self.assertEqual(result["public_base_url"], normalized)
                index = Tags((self.output / "index.html").read_text())
                self.assertEqual(index.attribute("link", "rel", "canonical", "href"), normalized)
                self.assertEqual(index.attribute("meta", "property", "og:url", "content"), normalized)
                for key, value in (("property", "og:image"), ("property", "og:image:secure_url"), ("name", "twitter:image")):
                    self.assertEqual(index.attribute("meta", key, value, "content"), normalized + "og-image.png")
                agent = Tags((self.output / "agent-access.html").read_text())
                self.assertEqual(agent.attribute("link", "rel", "canonical", "href"), normalized + "agent-access.html")
                for filename in ("agent-access.html", "llms.txt"):
                    guide = (self.output / filename).read_text()
                    if filename.endswith(".html"):
                        if "&" in normalized:
                            self.assertIn("a&amp;b/", guide)
                        guide = unescape(guide)
                    self.assertIn("curl -fsSL " + normalized + "packages.json", guide)
                    self.assertIn("Invoke-RestMethod -Uri '" + normalized + "packages.json'", guide)
                    if not normalized.startswith("https://solrevdev.com/winget-search/"):
                        self.assertNotIn("https://solrevdev.com/winget-search/", guide)
                redirect = Tags((self.output / "404.html").read_text())
                self.assertEqual(redirect.attribute("meta", "http-equiv", "refresh", "content"), "0; url=" + normalized)
                sitemap = ET.parse(self.output / "sitemap.xml")
                self.assertEqual([node.text for node in sitemap.findall(f".//{{{SITEMAP_NS}}}loc")],
                                 [normalized, normalized + "agent-access.html"])

    def test_dataset_count_freshness_fields_and_visible_summary(self):
        result = self.build()
        document = (self.output / "index.html").read_text()
        dataset = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', document, re.S).group(1))
        self.assertEqual(result["total"], 2)
        self.assertIn("2 Windows Package Manager packages", dataset["description"])
        self.assertEqual(dataset["dateModified"], "2026-09-12T20:15:30.123456Z")
        self.assertEqual(dataset["variableMeasured"], ["id", "name", "version", "publisher"])
        self.assertEqual(dataset["distribution"]["contentUrl"], "https://example.com/tools/packages.json")
        self.assertEqual(dataset["creator"]["url"], "https://github.com/solrevdev")
        self.assertEqual(dataset["license"], "https://spdx.org/licenses/MIT.html")
        for invalid in ("numberOfItems", "temporalCoverage", "datePublished", "sameAs"):
            self.assertNotIn(invalid, dataset)
        summary = re.search(r'<p[^>]*id="catalog-summary"[^>]*>(.*?)</p>', document, re.S).group(1)
        self.assertIn(dataset["description"], summary)
        self.assertIn('datetime="2026-09-12T20:15:30.123456Z"', summary)
        self.assertIn("12 September 2026 UTC", summary)

    def test_offset_timestamp_is_normalized_to_utc(self):
        self.catalog["metadata"]["extracted_at"] = "2026-09-13T00:30:00+02:00"
        self.save_catalog()
        self.assertEqual(self.build()["extracted_at"], "2026-09-12T22:30:00Z")

    def test_invalid_catalog_fails_before_creating_output(self):
        for catalog in ({}, [], {"metadata": {}, "packages": []},
                        {"metadata": {"total": 1, "extracted_at": "2026-09-12T00:00:00Z"}, "packages": [{}, {}]},
                        {"metadata": {"total": True, "extracted_at": "2026-09-12T00:00:00Z"}, "packages": [{}]},
                        {"metadata": {"total": 1, "extracted_at": "2026-09-12"}, "packages": [{}]},
                        {"metadata": {"total": 1, "extracted_at": "bad"}, "packages": [{}]},
                        {"metadata": {"total": 1, "extracted_at": "2026-09-12T00:00:00Z"}, "packages": [None]}):
            with self.subTest(catalog=catalog):
                self.catalog = catalog
                self.save_catalog()
                with self.assertRaises(ValueError):
                    self.build()
                self.assertFalse(self.output.exists())

    def test_sitemap_uses_catalog_date_and_omits_unknown_agent_date(self):
        self.build()
        entries = ET.parse(self.output / "sitemap.xml").findall(f"{{{SITEMAP_NS}}}url")
        self.assertEqual(entries[0].find(f"{{{SITEMAP_NS}}}lastmod").text, "2026-09-12")
        self.assertIsNone(entries[1].find(f"{{{SITEMAP_NS}}}lastmod"))
        self.assertEqual({child.tag.rsplit("}", 1)[-1] for entry in entries for child in entry}, {"loc", "lastmod"})

    def test_sitemap_uses_actual_page_dates_not_the_build_date(self):
        dates = [datetime(2026, 9, 14, tzinfo=timezone.utc), datetime(2026, 7, 1, tzinfo=timezone.utc)]
        with patch("build_site.git_modified", side_effect=dates):
            build_site(self.source, self.output)
        values = [node.text for node in ET.parse(self.output / "sitemap.xml").findall(f".//{{{SITEMAP_NS}}}lastmod")]
        self.assertEqual(values, ["2026-09-14", "2026-07-01"])
        self.assertIsNone(git_modified(self.source, ["index.html"]))

    def test_assets_catalog_and_preview_dimensions_are_preserved(self):
        self.build()
        for filename in (*ASSETS, "packages.json"):
            if filename not in ("agent-access.html", "llms.txt"):
                self.assertEqual((self.source / filename).read_bytes(), (self.output / filename).read_bytes())
        for original in (self.source / "vendor").rglob("*"):
            if original.is_file():
                self.assertEqual(original.read_bytes(), (self.output / original.relative_to(self.source)).read_bytes())
        self.assertTrue((self.output / ".nojekyll").is_file())
        png = (self.output / "og-image.png").read_bytes()
        self.assertEqual(png[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(struct.unpack(">II", png[16:24]), (1200, 630))
        ET.parse(self.output / "og-image.svg")

    def test_missing_template_marker_fails_before_writing(self):
        index = self.source / "index.html"
        index.write_text(index.read_text().replace('id="catalog-summary"', 'id="removed"'))
        with self.assertRaisesRegex(ValueError, "catalog-summary"):
            self.build()
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
