import os
import sys
import yaml
import json
import datetime
from packaging import version
import re

class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        return super().default(obj)

def parse_version(ver_str):
    """Parse version string for proper comparison"""
    try:
        return version.parse(ver_str)
    except:
        # Fallback for non-standard versions
        return version.parse("0.0.0")

def is_english_manifest(filepath):
    """Check if manifest is English or default (no locale specified)"""
    # Default manifests (no locale) or English manifests
    return '.locale.' not in filepath or '.locale.en-US.' in filepath

def extract_package_info(manifest_dir):
    """Extract comprehensive package info from a manifest directory"""
    package_info = {
        "id": None,
        "name": None,
        "description": None,
        "publisher": None,
        "version": None,
        "shortDescription": None,
        "tags": [],
        "homepage": None,
        "license": None
    }
    
    # Look for all YAML files in the directory
    yaml_files = []
    for file in os.listdir(manifest_dir):
        if file.endswith(('.yaml', '.yml')):
            yaml_files.append(file)
    
    # Process version manifest first
    version_file = next((f for f in yaml_files if not '.locale.' in f and not '.installer.' in f), None)
    if version_file:
        try:
            with open(os.path.join(manifest_dir, version_file), encoding="utf-8") as f:
                doc = yaml.safe_load(f)
                package_info["id"] = doc.get("PackageIdentifier")
                package_info["version"] = doc.get("PackageVersion")
                package_info["shortDescription"] = doc.get("ShortDescription")
                package_info["tags"] = doc.get("Tags", [])
        except Exception as e:
            print(f"Error parsing version file {version_file}: {e}")
    
    # Look for English locale file
    locale_file = next((f for f in yaml_files if '.locale.en-US.' in f), None)
    if not locale_file:
        # Fallback to default locale
        locale_file = next((f for f in yaml_files if '.locale.' in f and 'en-US' not in f), None)
    
    if locale_file:
        try:
            with open(os.path.join(manifest_dir, locale_file), encoding="utf-8") as f:
                doc = yaml.safe_load(f)
                package_info["name"] = doc.get("PackageName")
                package_info["publisher"] = doc.get("Publisher")
                package_info["description"] = doc.get("Description") or doc.get("ShortDescription")
                package_info["homepage"] = doc.get("PackageUrl")
                package_info["license"] = doc.get("License")
                if not package_info["tags"]:
                    package_info["tags"] = doc.get("Tags", [])
        except Exception as e:
            print(f"Error parsing locale file {locale_file}: {e}")
    
    return package_info if package_info["id"] else None

def find_latest_version_dirs(manifests_dir):
    """Find the latest version directory for each package"""
    packages = {}  # package_id -> (version, directory_path)
    
    for root, dirs, files in os.walk(manifests_dir):
        # Check if this directory contains manifest files
        yaml_files = [f for f in files if f.endswith(('.yaml', '.yml'))]
        if not yaml_files:
            continue
            
        # Extract package ID from path
        rel_path = os.path.relpath(root, manifests_dir)
        path_parts = rel_path.split(os.sep)
        
        # winget structure: publisher/package_name/version/
        if len(path_parts) >= 3:
            package_id = None
            
            # Try to get package ID from a manifest file
            for yaml_file in yaml_files:
                if '.locale.' not in yaml_file and '.installer.' not in yaml_file:
                    try:
                        with open(os.path.join(root, yaml_file), encoding="utf-8") as f:
                            doc = yaml.safe_load(f)
                            package_id = doc.get("PackageIdentifier")
                            version_str = doc.get("PackageVersion")
                            break
                    except:
                        continue
            
            if package_id and version_str:
                if package_id not in packages:
                    packages[package_id] = (version_str, root)
                else:
                    # Compare versions
                    current_ver = parse_version(packages[package_id][0])
                    new_ver = parse_version(version_str)
                    if new_ver > current_ver:
                        packages[package_id] = (version_str, root)
    
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
        }, out, indent=2, ensure_ascii=False, cls=EnhancedJSONEncoder)
    
    print(f"Output written to: {out_path}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python extract_packages.py <manifests_dir> <output_json>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])