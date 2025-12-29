import argparse
import os
import sys
import json

# Ensure costscanner is importable
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


from costscanner.report import render_table
from costscanner.scanner import scan_project

def main():
    parser = argparse.ArgumentParser(description="Terraform cost & security scanner")
    parser.add_argument("path", help="Path to Terraform files to scan")
    parser.add_argument("--format", choices=["table", "json"], default="table", help="Output format")
    parser.add_argument("--output", help="Save JSON to file")
    parser.add_argument("--min-savings", type=float, help="Filter by minimum savings")
    parser.add_argument("--severity", choices=["low", "medium", "high", "critical"], help="Filter by severity")
    parser.add_argument("--rule", help="Filter by rule name")
    args = parser.parse_args()

    try:
        scan_path = os.path.abspath(args.path)

        if not os.path.exists(scan_path):
            print(f"❌ Error: Path '{scan_path}' does not exist.", file=sys.stderr)
            sys.exit(1)

        issues = scan_project(scan_path)
        issues = scan_project(path)

        # Apply filters
        if args.min_savings:
            issues = [i for i in issues if i.get("savings", 0) >= args.min_savings]
        if args.severity:
            issues = [i for i in issues if i.get("severity") == args.severity]
        if args.rule:
            issues = [i for i in issues if i.get("rule") == args.rule]

        # Output results
        if args.format == "json":
            json_output = json.dumps({"issues": issues}, indent=2)
            if args.output:
                with open(args.output, "w") as f:
                    f.write(json_output)
            else:
                print(json_output)
        else:
            print(render_table(issues))

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
