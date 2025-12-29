import sys
import json
sys.path.insert(0, ".")

from costscanner.scanner import load_resources, scan_project

def main():
    print("\n📂 Static scan mode")

    resources = load_resources()
    print(f"\n📦 Parsed resources count: {len(resources)}")

    if not resources:
        print("⚠️ No resources found. Check your file list.")
    else:
        print("\n🔍 Resource types found:")
        for r in resources:
            print(f" - {r.get('type')} ({r.get('name')})")

    issues = scan_project()  # no folder argument

    print(f"\n🚨 Total issues found: {len(issues)}")

    rules = sorted(set(i["rule"] for i in issues))
    print("\n✅ Rules triggered:")
    for r in rules:
        print(f" - {r}")

    print("\n🧾 Full issues JSON:")
    print(json.dumps(issues, indent=2))

if __name__ == "__main__":
    main()
