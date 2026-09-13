#!/usr/bin/env python3
"""Build the static Pages site from its source and extracted catalog."""

import argparse
from datetime import datetime, timezone
from html import escape, unescape
import json
from pathlib import Path
import re
import shutil
import subprocess
from urllib.parse import unquote, urlsplit, urlunsplit
import xml.etree.ElementTree as ET


SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
ASSETS = ("search.js", "agent-access.html", "llms.txt", "og-image.png", "og-image.svg")


def normalize_public_base_url(value):
    """Use an explicit HTTPS origin and optional path, always ending in a slash."""
    if not isinstance(value, str) or not value or any(c.isspace() for c in value):
        raise ValueError("public_base_url must be an HTTPS URL without whitespace")
    try:
        parts = urlsplit(value)
        port = parts.port
    except ValueError as exc:
        raise ValueError("public_base_url is malformed") from exc
    if (parts.scheme != "https" or not parts.hostname or parts.username is not None
            or parts.password is not None or parts.query or parts.fragment
            or "?" in value or "#" in value or "\\" in value):
        raise ValueError("public_base_url must use HTTPS without credentials, query, or fragment")
    if port is not None and port != 443:
        raise ValueError("public_base_url must use the default HTTPS port")
    host = parts.hostname.lower()
    if not re.fullmatch(r"[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?", host):
        raise ValueError("public_base_url must have a valid public hostname")
    if any(not label or len(label) > 63 or label.startswith("-") or label.endswith("-")
           for label in host.split(".")):
        raise ValueError("public_base_url must have a valid public hostname")
    path = parts.path
    if re.search(r"%(?![0-9a-fA-F]{2})", path):
        raise ValueError("public_base_url contains an invalid escape")
    decoded = unquote(path)
    if (any(c.isspace() or ord(c) < 32 for c in decoded)
            or any(c in decoded for c in '\\?#<>"\'')
            or "//" in decoded or any(p in (".", "..") for p in decoded.split("/"))):
        raise ValueError("public_base_url contains an unsafe path")
    return urlunsplit(("https", host, path.rstrip("/") + "/", "", ""))


def parse_timestamp(value):
    if not isinstance(value, str) or "T" not in value:
        raise ValueError("metadata.extracted_at must be an ISO timestamp")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("metadata.extracted_at must be an ISO timestamp") from exc
    # The extractor uses datetime.utcnow().isoformat(), which has no UTC suffix.
    if result.tzinfo is None:
        result = result.replace(tzinfo=timezone.utc)
    return result.astimezone(timezone.utc)


def read_catalog(path):
    catalog = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(catalog, dict) or not isinstance(catalog.get("metadata"), dict):
        raise ValueError("catalog must contain metadata and packages")
    packages = catalog.get("packages")
    total = catalog["metadata"].get("total")
    if not isinstance(packages, list) or not packages:
        raise ValueError("catalog packages must be a nonempty array")
    if type(total) is not int or total != len(packages):
        raise ValueError("metadata.total must match the packages array length")
    if any(not isinstance(package, dict) for package in packages):
        raise ValueError("catalog packages must contain objects")
    return total, parse_timestamp(catalog["metadata"].get("extracted_at"))


def git_modified(source_dir, paths):
    """Ignore checkout mtimes: only tracked content history supplies page dates."""
    try:
        result = subprocess.run(
            ["git", "-C", str(source_dir), "log", "-1", "--format=%cI", "--", *paths],
            check=True, capture_output=True, text=True,
        )
        return parse_timestamp(result.stdout.strip()) if result.stdout.strip() else None
    except (OSError, subprocess.CalledProcessError, ValueError):
        return None


def replace_attribute(document, tag, key, match_value, attribute, value):
    pattern = rf'<{tag}\b[^>]*\b{key}=["\']{re.escape(match_value)}["\'][^>]*>'
    tags = list(re.finditer(pattern, document, re.IGNORECASE))
    if len(tags) != 1:
        raise ValueError(f"expected one {tag} with {key}={match_value}")
    old = tags[0].group()
    attr_pattern = rf'\b{attribute}=["\'][^"\']*["\']'
    replacement, count = re.subn(attr_pattern, lambda _: f'{attribute}="{escape(value, quote=True)}"', old)
    if count != 1:
        raise ValueError(f"expected one {attribute} in {old}")
    return document[:tags[0].start()] + replacement + document[tags[0].end():]


def build_index(document, public_base_url, total, extracted_at):
    document = replace_attribute(document, "link", "rel", "canonical", "href", public_base_url)
    for key, name, value in (
        ("property", "og:url", public_base_url),
        ("property", "og:image", public_base_url + "og-image.png"),
        ("property", "og:image:secure_url", public_base_url + "og-image.png"),
        ("name", "twitter:image", public_base_url + "og-image.png"),
    ):
        document = replace_attribute(document, "meta", key, name, "content", value)
    pattern = r'(<script\s+type="application/ld\+json"\s*>)(.*?)(</script>)'
    matches = list(re.finditer(pattern, document, re.DOTALL))
    if len(matches) != 1:
        raise ValueError("expected one Dataset JSON-LD block")
    dataset = json.loads(matches[0].group(2))
    if dataset.get("@type") != "Dataset":
        raise ValueError("expected Dataset structured data")
    for key in ("numberOfItems", "temporalCoverage", "datePublished", "sameAs"):
        dataset.pop(key, None)
    dataset.update({
        "description": f"Metadata for {total:,} Windows Package Manager packages extracted from microsoft/winget-pkgs.",
        "url": public_base_url,
        "dateModified": extracted_at.isoformat().replace("+00:00", "Z"),
        "variableMeasured": ["id", "name", "version", "publisher"],
        "distribution": {"@type": "DataDownload", "encodingFormat": "application/json",
                         "contentUrl": public_base_url + "packages.json"},
    })
    encoded = json.dumps(dataset, ensure_ascii=False, indent=2).replace("<", "\\u003c")
    document = re.sub(pattern, lambda m: m.group(1) + "\n" + encoded + "\n  " + m.group(3), document, flags=re.DOTALL)
    summary = (dataset["description"] + " "
               f'Catalog updated <time datetime="{extracted_at.isoformat().replace("+00:00", "Z")}">'
               f'{extracted_at.strftime("%d %B %Y").lstrip("0")} UTC</time>'
               ".")
    document, count = re.subn(r'(<p\b[^>]*\bid="catalog-summary"[^>]*>).*?(</p>)',
                              lambda m: m.group(1) + summary + m.group(2), document, flags=re.DOTALL)
    if count != 1:
        raise ValueError("expected one catalog-summary paragraph")
    return document


def build_sitemap(template, public_base_url, home_modified, agent_modified):
    root = ET.fromstring(template)
    ns = {"s": SITEMAP_NS}
    entries = root.findall("s:url", ns)
    locations = {"{{PUBLIC_BASE_URL}}": (public_base_url, home_modified),
                 "{{AGENT_URL}}": (public_base_url + "agent-access.html", agent_modified)}
    if len(entries) != len(locations):
        raise ValueError("sitemap template must contain the homepage and agent page")
    for entry in entries:
        loc = entry.find("s:loc", ns)
        if loc is None or loc.text not in locations:
            raise ValueError("sitemap template contains an unknown location")
        url, modified = locations.pop(loc.text)
        loc.text = url
        for child in list(entry):
            if child is not loc:
                entry.remove(child)
        if modified:
            ET.SubElement(entry, f"{{{SITEMAP_NS}}}lastmod").text = modified.date().isoformat()
    ET.register_namespace("", SITEMAP_NS)
    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="unicode", xml_declaration=True) + "\n"


def build_site(source_dir, output_dir, packages_path=None, public_base_url=None):
    source_dir = Path(source_dir).resolve()
    output_dir = Path(output_dir).resolve()
    packages_path = Path(packages_path).resolve() if packages_path else source_dir / "packages.json"
    if output_dir == source_dir or output_dir in source_dir.parents:
        raise ValueError("output directory must not contain the source directory")
    if public_base_url is None:
        config = json.loads((source_dir / "site_config.json").read_text(encoding="utf-8"))
        public_base_url = config["public_base_url"]
    public_base_url = normalize_public_base_url(public_base_url)
    total, extracted_at = read_catalog(packages_path)
    index_source = (source_dir / "index.html").read_text(encoding="utf-8")
    canonical = re.search(r'<link\b[^>]*\brel="canonical"[^>]*\bhref="([^"]+)"', index_source)
    if canonical is None:
        raise ValueError("expected a source canonical URL")
    source_base_url = normalize_public_base_url(unescape(canonical.group(1)))
    index = build_index(index_source, public_base_url, total, extracted_at)
    agent = (source_dir / "agent-access.html").read_text(encoding="utf-8").replace(
        escape(source_base_url, quote=True), escape(public_base_url, quote=True))
    agent = replace_attribute(agent, "link", "rel", "canonical", "href", public_base_url + "agent-access.html")
    guide = (source_dir / "llms.txt").read_text(encoding="utf-8").replace(source_base_url, public_base_url)
    shared = ["build_site.py", "site_config.json"]
    home_modified = git_modified(source_dir, ["index.html", "search.js", "sitemap.xml", *shared])
    home_modified = max(extracted_at, home_modified) if home_modified else extracted_at
    agent_modified = git_modified(source_dir, ["agent-access.html", *shared])
    sitemap = build_sitemap((source_dir / "sitemap.xml").read_text(encoding="utf-8"),
                            public_base_url, home_modified, agent_modified)
    for asset in ASSETS:
        if not (source_dir / asset).is_file():
            raise ValueError(f"missing site asset: {asset}")
    if not (source_dir / "vendor").is_dir():
        raise ValueError("missing vendor directory")
    output_dir.mkdir(parents=True, exist_ok=True)
    for asset in ASSETS:
        shutil.copy2(source_dir / asset, output_dir / asset)
    shutil.copytree(source_dir / "vendor", output_dir / "vendor", dirs_exist_ok=True)
    shutil.copy2(packages_path, output_dir / "packages.json")
    (output_dir / "index.html").write_text(index, encoding="utf-8")
    (output_dir / "agent-access.html").write_text(agent, encoding="utf-8")
    (output_dir / "llms.txt").write_text(guide, encoding="utf-8")
    (output_dir / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    (output_dir / ".nojekyll").touch()
    destination = escape(public_base_url, quote=True)
    (output_dir / "404.html").write_text(
        '<!DOCTYPE html>\n<html lang="en"><head><meta charset="UTF-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f'<meta http-equiv="refresh" content="0; url={destination}">'
        '<title>Page not found | Winget Package Search</title></head>'
        f'<body><main><h1>Page not found</h1><p><a href="{destination}">'
        'Search WinGet packages</a></p></main></body></html>\n', encoding="utf-8")
    return {"public_base_url": public_base_url, "total": total,
            "extracted_at": extracted_at.isoformat().replace("+00:00", "Z")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--packages", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--public-base-url")
    args = parser.parse_args()
    try:
        result = build_site(args.source_dir, args.output_dir or args.source_dir / "deploy",
                            args.packages, args.public_base_url)
    except (ValueError, KeyError, OSError) as exc:
        parser.exit(1, f"Site build failed: {exc}\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
