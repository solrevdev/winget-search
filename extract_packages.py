import os
import sys
import yaml
import json
import datetime

class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        return super().default(obj)

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
    except Exception as e:
        print(f"Failed to parse {path}: {e}")
        return None

def main(manifests_dir, out_path):
    results = []
    count_files = 0
    for root, dirs, files in os.walk(manifests_dir):
        for file in files:
            if file.endswith(".yaml") or file.endswith(".yml"):
                count_files += 1
                data = extract_from_manifest(os.path.join(root, file))
                if data and data["id"]:
                    results.append(data)
    print(f"Total manifest YAML files found: {count_files}")
    print(f"Total valid packages found: {len(results)}")
    # Deduplicate by id + version (keep latest version if multiple)
    unique = {}
    for pkg in results:
        key = (pkg["id"], pkg["version"])
        if key not in unique or (pkg.get("version", "") > unique[key].get("version", "")):
            unique[key] = pkg
    print(f"Unique packages extracted: {len(unique)}")
    with open(out_path, "w", encoding="utf-8") as out:
        json.dump(list(unique.values()), out, indent=2, ensure_ascii=False, cls=EnhancedJSONEncoder)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python extract_packages.py <manifests_dir> <output_json>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
