import contextlib
import datetime
import io
import json
import os
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch

import yaml
from packaging.version import Version

from extract_packages import extract_package_info, find_latest_version_dirs, main


class ExtractPackageInfoTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.manifest_dir = self.root / "manifests" / "Example" / "App" / "1.2.3"
        self.manifest_dir.mkdir(parents=True)

    def write_manifest(self, suffix, **fields):
        document = {
            "PackageIdentifier": "Example.App",
            "PackageVersion": "1.2.3",
            **fields,
        }
        path = self.manifest_dir / f"Example.App{suffix}.yaml"
        path.write_text(yaml.safe_dump(document), encoding="utf-8")

    def write_version(self, **fields):
        self.write_manifest("", ManifestType="version", **fields)

    def test_sparse_english_overlays_declared_default_per_field(self):
        self.write_version(DefaultLocale="fr-FR")
        self.write_manifest(
            ".locale.fr-FR", ManifestType="defaultLocale", PackageLocale="fr-FR",
            PackageName="Application", Publisher="Example Publisher",
            Description="Description française", ShortDescription="Résumé",
            Moniker="example", Tags=["editor", "tools"],
            PackageUrl="https://example.com", License="MIT",
        )
        self.write_manifest(
            ".locale.en-US", ManifestType="locale", PackageLocale="en-US",
            Description="Full English description", ShortDescription="English summary",
        )
        result = extract_package_info(self.manifest_dir)
        self.assertEqual(result, {
            "id": "Example.App", "version": "1.2.3", "name": "Application",
            "publisher": "Example Publisher", "description": "Full English description",
            "shortDescription": "English summary", "moniker": "example",
            "tags": ["editor", "tools"], "homepage": "https://example.com",
            "license": "MIT",
        })

    def test_declared_default_wins_over_first_locale_filename(self):
        self.write_version(DefaultLocale="ja-JP")
        self.write_manifest(".locale.de-DE", PackageName="Wrong fallback")
        self.write_manifest(
            ".locale.ja-JP", PackageLocale="ja-JP", PackageName="Default app",
            ShortDescription="Default summary", Moniker="default-app",
        )
        result = extract_package_info(self.manifest_dir)
        self.assertEqual(result["name"], "Default app")
        self.assertEqual(result["description"], "Default summary")
        self.assertEqual(result["shortDescription"], "Default summary")
        self.assertEqual(result["moniker"], "default-app")

    def test_default_locale_manifest_type_supplies_base(self):
        self.write_version()
        self.write_manifest(".locale.de-DE", PackageName="Wrong fallback")
        self.write_manifest(
            ".locale.fr-FR", ManifestType="defaultLocale", PackageName="Default app",
            Publisher="Default publisher",
        )
        self.write_manifest(".locale.en-US", PackageName="English app")
        result = extract_package_info(self.manifest_dir)
        self.assertEqual(result["name"], "English app")
        self.assertEqual(result["publisher"], "Default publisher")

    def test_empty_overrides_keep_default_but_false_and_zero_are_values(self):
        self.write_version(DefaultLocale="fr-FR")
        self.write_manifest(
            ".locale.fr-FR", PackageName="Default app", Publisher="Publisher",
            Description="Full description", ShortDescription="Summary",
            Moniker="example", Tags=["editor"], License="MIT",
        )
        self.write_manifest(
            ".locale.en-US", PackageName=None, Publisher="", Description="  ",
            ShortDescription=None, Moniker="", Tags=[], License=False, PackageVersion=0,
        )
        result = extract_package_info(self.manifest_dir)
        self.assertEqual(result["name"], "Default app")
        self.assertEqual(result["publisher"], "Publisher")
        self.assertEqual(result["description"], "Full description")
        self.assertEqual(result["shortDescription"], "Summary")
        self.assertEqual(result["moniker"], "example")
        self.assertEqual(result["tags"], ["editor"])
        self.assertIs(result["license"], False)
        self.assertEqual(result["version"], 0)

    def test_singleton_keeps_all_metadata(self):
        self.write_manifest(
            "", ManifestType="singleton", PackageName="Single app",
            Publisher="Publisher", Description="Full description",
            ShortDescription="Short description", Moniker="single",
            Tags=["editor", 123], PackageUrl="https://example.com", License="MIT",
        )
        result = extract_package_info(self.manifest_dir)
        self.assertEqual(result["name"], "Single app")
        self.assertEqual(result["publisher"], "Publisher")
        self.assertEqual(result["description"], "Full description")
        self.assertEqual(result["shortDescription"], "Short description")
        self.assertEqual(result["moniker"], "single")
        self.assertEqual(result["tags"], ["editor", "123"])
        self.assertEqual(result["homepage"], "https://example.com")
        self.assertEqual(result["license"], "MIT")

    def test_unmarked_locale_fallback_is_sorted(self):
        self.write_version()
        self.write_manifest(".locale.fr-FR", PackageName="French")
        self.write_manifest(".locale.de-DE", PackageName="German")
        self.assertEqual(extract_package_info(self.manifest_dir)["name"], "German")

    def test_ignores_non_mapping_yaml_and_malformed_files(self):
        self.write_version(DefaultLocale="en-US")
        self.write_manifest(".locale.en-US", PackageName="App", Tags="not a list")
        (self.manifest_dir / "empty.yaml").write_text("", encoding="utf-8")
        (self.manifest_dir / "list.yaml").write_text("- item", encoding="utf-8")
        (self.manifest_dir / "broken.yaml").write_text("key: [", encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            result = extract_package_info(self.manifest_dir)
        self.assertEqual(result["name"], "App")
        self.assertEqual(result["tags"], [])

    def test_skips_installer_yaml_without_parsing(self):
        self.write_version(DefaultLocale="en-US")
        self.write_manifest(".locale.en-US", PackageName="App")
        (self.manifest_dir / "Example.App.installer.yaml").write_text(
            "key: [", encoding="utf-8"
        )
        messages = io.StringIO()
        with contextlib.redirect_stdout(messages):
            result = extract_package_info(self.manifest_dir)
        self.assertEqual(result["name"], "App")
        self.assertEqual(messages.getvalue(), "")

    def test_main_writes_merged_catalog_and_metadata(self):
        self.write_version(DefaultLocale="en-US")
        self.write_manifest(
            ".locale.en-US", ManifestType="defaultLocale", PackageName="App",
            ShortDescription="Summary", Moniker="app",
        )
        output = self.root / "packages.json"
        with contextlib.redirect_stdout(io.StringIO()):
            main(self.root / "manifests", output)
        catalog = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(catalog["metadata"]["total"], 1)
        self.assertEqual(catalog["metadata"]["source"], "microsoft/winget-pkgs")
        self.assertIn("extracted_at", catalog["metadata"])
        self.assertEqual(catalog["packages"][0]["moniker"], "app")
        self.assertEqual(catalog["packages"][0]["shortDescription"], "Summary")
        self.assertEqual(catalog["packages"][0]["id"], "Example.App")


class VersionSelectionTests(unittest.TestCase):
    FIXTURES = Path(__file__).parent / "fixtures" / "version-ordering"
    EXPECTED = {
        "Alibaba.AliWorkbench": "9.63.20N",
        "Authpass.Authpass": "1.9.11_2007",
        "Ablaze.Floorp": "12.16.4@153.0",
        "Artempyanykh.Marksman": datetime.date(2026, 2, 8),
    }

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def manifest(self, value, directory, filename="Example.App.yaml"):
        path = self.root / "Example" / "App" / directory
        path.mkdir(parents=True, exist_ok=True)
        (path / filename).write_text(yaml.safe_dump({
            "PackageIdentifier": "Example.App", "PackageVersion": value,
            "ManifestType": "version", "DefaultLocale": "en-US",
        }), encoding="utf-8")
        return str(path)

    def selections(self, root):
        walk = list(os.walk(root))
        shuffled = list(walk)
        random.Random(42).shuffle(shuffled)
        for entries in (walk, list(reversed(walk)), shuffled):
            entries = [(path, dirs, list(reversed(files))) for path, dirs, files in entries]
            with patch("extract_packages.os.walk", return_value=entries):
                yield find_latest_version_dirs(root)

    def assert_winner(self, values, expected):
        for index, value in enumerate(values):
            self.manifest(value, str(index))
        for selected in self.selections(self.root):
            self.assertEqual(selected["Example.App"][0], expected)

    def test_real_manifests_select_same_newer_versions_in_every_traversal(self):
        for selected in self.selections(self.FIXTURES):
            self.assertEqual({key: value[0] for key, value in selected.items()}, self.EXPECTED)

    def test_standard_version_order_matches_packaging_for_every_pair(self):
        values = ["0.0.0.dev1", "0.0.0rc1", "0.0.0", "1.0.dev1", "1.0a2",
                  "1.0b1", "1.0rc1", "1.0", "1.0+build.2", "1.0+build.10",
                  "1.0.post1", "1.9", "1.10", "2.0.0.1", "1!0.1"]
        for first in values:
            for second in values:
                with self.subTest(first=first, second=second):
                    self.assert_winner([first, second], max([first, second], key=Version))

    def test_date_strings_and_yaml_dates_compare_with_dotted_dates(self):
        for date in ("2026-02-08", datetime.date(2026, 2, 8)):
            with self.subTest(date=date):
                self.assert_winner(["2024.12.18", date], date)

    def test_at_suffix_orders_release_then_numeric_build(self):
        self.assert_winner(["12.16.3@999.0", "12.16.4", "12.16.4@153.9",
                            "12.16.4@153.10"], "12.16.4@153.10")

    def test_unknown_versions_use_numeric_runs(self):
        self.assert_winner(["build9", "build11", "build2"], "build11")

    def test_leading_zero_and_case_ties_use_original_text(self):
        self.assert_winner(["build09", "BUILD9", "build9"], "build9")

    def test_text_and_numeric_tokens_do_not_raise_type_errors(self):
        self.assert_winner(["nightly", "99-custom", "9-custom"], "99-custom")

    def test_recognized_zero_and_prerelease_outrank_unknown_values(self):
        for known in ("0.0.0", "0.0.0rc1"):
            with self.subTest(known=known):
                self.assert_winner(["999-custom", known], known)

    def test_normalizers_reject_invalid_dates_and_non_numeric_at_suffixes(self):
        self.assert_winner(["2026-02-30", "2026-13-01", "99.0@nightly",
                            "99.0@2.0-extra", "1.0"], "1.0")

    def test_equal_standard_versions_use_original_text(self):
        self.assert_winner(["1.0", "1.0.0", "v1.0"], "v1.0")

    def test_equal_versions_use_relative_path(self):
        self.manifest("1.0", "a")
        expected_path = self.manifest("1.0", "z")
        for selected in self.selections(self.root):
            self.assertEqual(selected["Example.App"], ("1.0", expected_path))

    def test_manifest_filename_order_is_stable_and_bad_yaml_is_skipped(self):
        path = Path(self.manifest("2.0", "1", "z.yaml"))
        self.manifest("1.0", "1", "b.yaml")
        (path / "a.yaml").write_text("- not a mapping\n", encoding="utf-8")
        (path / "aa.yaml").write_text("bad: [", encoding="utf-8")
        (path / "ab.yaml").write_text("PackageVersion: 2026-02-30\n", encoding="utf-8")
        for selected in self.selections(self.root):
            self.assertEqual(selected["Example.App"][0], "1.0")

    def test_catalog_keeps_original_versions_and_existing_shape(self):
        output = self.root / "packages.json"
        with contextlib.redirect_stdout(io.StringIO()):
            main(self.FIXTURES, output)
        catalog = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(set(catalog), {"packages", "metadata"})
        self.assertEqual(set(catalog["metadata"]), {"total", "extracted_at", "source"})
        self.assertEqual(catalog["metadata"]["total"], 4)
        self.assertEqual(catalog["metadata"]["source"], "microsoft/winget-pkgs")
        self.assertEqual({pkg["id"]: pkg["version"] for pkg in catalog["packages"]},
                         {key: str(value) for key, value in self.EXPECTED.items()})
        for pkg in catalog["packages"]:
            self.assertEqual(set(pkg), {"id", "name", "description", "publisher",
                             "version", "shortDescription", "moniker", "tags",
                             "homepage", "license"})


if __name__ == "__main__":
    unittest.main()
