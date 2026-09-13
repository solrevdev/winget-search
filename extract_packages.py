import os
import sys
import yaml
import json
import datetime
import re
from packaging import version

class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        return super().default(obj)

def version_sort_key(value):
    """Keep PEP 440 ordering, with a bounded fallback for WinGet versions."""
    text = value.isoformat() if isinstance(value, datetime.date) else str(value)
    try:
        return (1, version.parse(value), text)
    except (version.InvalidVersion, TypeError):
        pass

    # YAML can turn an unquoted date version into datetime.date.
    if re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", text):
        try:
            datetime.date.fromisoformat(text)
        except ValueError:
            pass
        else:
            return (1, version.parse(text.replace("-", ".")), text)
    if re.fullmatch(r"[0-9]+(?:\.[0-9]+)+@[0-9]+(?:\.[0-9]+)+", text):
        return (1, version.parse(text.replace("@", "+")), text)

    # Unknown labels have no universal release order. Keep recognized versions
    # ahead of them, then use natural order and original text to break ties.
    tokens = tuple((1, int(part)) if part.isascii() and part.isdigit()
                   else (0, part.casefold())
                   for part in re.findall(r"[0-9]+|[^0-9]+", text))
    return (0, tokens, text)

def extract_package_info(manifest_dir):
    """Merge default and English metadata, including singleton manifests."""
    documents = []
    for filename in sorted(os.listdir(manifest_dir)):
        if not filename.endswith(('.yaml', '.yml')) or '.installer.' in filename:
            continue
        try:
            with open(os.path.join(manifest_dir, filename), encoding="utf-8") as manifest:
                document = yaml.safe_load(manifest)
            if isinstance(document, dict):
                documents.append((filename, document))
        except (OSError, yaml.YAMLError) as error:
            print(f"Error parsing manifest {filename}: {error}")

    version_doc = next((doc for _, doc in documents
                        if doc.get("ManifestType") in ("version", "singleton")), None)
    if version_doc is None:
        version_doc = next((doc for filename, doc in documents
                            if '.locale.' not in filename and '.installer.' not in filename), {})

    locales = [(filename, doc) for filename, doc in documents
               if doc.get("ManifestType") in ("defaultLocale", "locale")
               or '.locale.' in filename]

    def matches_locale(filename, doc, locale):
        return (doc.get("PackageLocale") == locale
                or f".locale.{locale}." in filename)

    default_locale = version_doc.get("DefaultLocale")
    default_doc = next((doc for filename, doc in locales
                        if default_locale and matches_locale(filename, doc, default_locale)), None)
    if default_doc is None:
        default_doc = next((doc for _, doc in locales
                            if doc.get("ManifestType") == "defaultLocale"), None)
    if default_doc is None:
        default_doc = locales[0][1] if locales else {}
    english_doc = next((doc for filename, doc in locales
                        if matches_locale(filename, doc, "en-US")), {})

    merged = {}
    for document in (version_doc, default_doc, english_doc):
        for key, value in document.items():
            # Sparse translations must not erase metadata from the default locale.
            if value is None or (isinstance(value, str) and not value.strip()):
                continue
            if isinstance(value, (list, dict)) and not value:
                continue
            merged[key] = value

    raw_tags = merged.get("Tags", [])
    package_info = {
        "id": merged.get("PackageIdentifier"),
        "name": merged.get("PackageName"),
        "description": merged.get("Description") or merged.get("ShortDescription"),
        "publisher": merged.get("Publisher"),
        "version": merged.get("PackageVersion"),
        "shortDescription": merged.get("ShortDescription"),
        "moniker": merged.get("Moniker"),
        "tags": [str(tag) for tag in raw_tags if tag] if isinstance(raw_tags, list) else [],
        "homepage": merged.get("PackageUrl"),
        "license": merged.get("License"),
    }
    return package_info if package_info["id"] else None

def find_latest_version_dirs(manifests_dir):
    """Select one version per package without depending on traversal order."""
    packages = {}  # package_id -> (version, directory_path)
    sort_keys = {}

    for root, dirs, files in os.walk(manifests_dir):
        rel_path = os.path.relpath(root, manifests_dir)
        if len(rel_path.split(os.sep)) < 3:
            continue
        for filename in sorted(files):
            if (not filename.endswith(('.yaml', '.yml'))
                    or '.locale.' in filename or '.installer.' in filename):
                continue
            try:
                with open(os.path.join(root, filename), encoding="utf-8") as manifest:
                    doc = yaml.safe_load(manifest)
            except (OSError, yaml.YAMLError, ValueError):
                continue
            if not isinstance(doc, dict):
                continue
            package_id = doc.get("PackageIdentifier")
            value = doc.get("PackageVersion")
            if not isinstance(package_id, str) or not package_id or not value:
                continue
            key = (version_sort_key(value), rel_path.replace(os.sep, "/"))
            if package_id not in sort_keys or key > sort_keys[package_id]:
                packages[package_id] = (value, root)
                sort_keys[package_id] = key
            break

    return packages

def main(manifests_dir, out_path):
    print(f"Scanning manifests in: {manifests_dir}")
    
    # Find latest version directories for each package
    latest_packages = find_latest_version_dirs(manifests_dir)
    print(f"Found {len(latest_packages)} unique packages")
    
    results = []
    processed = 0
    
    for package_id, (version, directory) in latest_packages.items():
        processed += 1
        if processed % 1000 == 0:
            print(f"Processed {processed}/{len(latest_packages)} packages...")
        
        package_info = extract_package_info(directory)
        if package_info:
            results.append(package_info)
    
    print(f"Successfully extracted {len(results)} packages")
    
    # Sort by package ID for consistent output
    results.sort(key=lambda x: x.get("id", "").lower())
    
    # Write results
    with open(out_path, "w", encoding="utf-8") as out:
        json.dump({
            "packages": results,
            "metadata": {
                "total": len(results),
                "extracted_at": datetime.datetime.utcnow().isoformat(),
                "source": "microsoft/winget-pkgs"
            }
        }, out, separators=(",", ":"), ensure_ascii=False, cls=EnhancedJSONEncoder)
    
    print(f"Output written to: {out_path}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python extract_packages.py <manifests_dir> <output_json>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
