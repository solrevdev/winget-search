import os
import sys
import yaml
import json

def extract_from_manifest(path):
    try:
        with open(path, encoding="utf-8") as f:
            doc = yaml.safe_load(f)
        return {
            "id": doc.get("PackageIdentifier"),
            "name": doc.get("PackageName"),
            "description": doc.get("Description", ""),
            "publisher": doc.get("Publisher", ""),
            "version": doc.get("PackageVersion", ""),
        }
    except Exception:
        return None

def main(manifests_dir, out_path):
    results = []
    for root, dirs, files in os.walk(manifests_dir):
        for file in files:
            if file.endswith(".yaml") or file.endswith(".yml"):
                data = extract_from_manifest(os.path.join(root, file))
                if data and data["id"]:
                    results.append(data)
    # Deduplicate by id + version (keep latest version if multiple)
    unique = {}
    for pkg in results:
        key = (pkg["id"], pkg["version"])
        if key not in unique or (pkg.get("version", "") > unique[key].get("version", "")):
            unique[key] = pkg
    with open(out_path, "w", encoding="utf-8") as out:
        json.dump(list(unique.values()), out, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python extract_packages.py <manifests_dir> <output_json>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])