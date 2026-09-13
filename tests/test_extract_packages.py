import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

import yaml

from extract_packages import extract_package_info, main


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


if __name__ == "__main__":
    unittest.main()
