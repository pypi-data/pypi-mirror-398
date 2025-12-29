import argparse
import json
from pathlib import Path
import hcl2
import datetime
from colorama import Fore, Style

# -----------------------------
# Color helper
# -----------------------------
def color_severity(sev):
    return {
        "critical": Fore.RED,
        "high": Fore.YELLOW,
        "medium": Fore.CYAN,
        "low": Fore.GREEN
    }.get(sev, Fore.WHITE)

# -----------------------------
# Static file loader
# -----------------------------
def parse_static_files():
    files_to_scan = [
        "costscanner/sample-repos/sample_ec2_overprovisioned.tf",
        "costscanner/sample-repos/sample_s3_unencrypted.tf",
        "costscanner/sample-repos/sample_iam_inline.tf",
        "costscanner/sample-repos/sample_sg.tf",
        "costscanner/sample-repos/sample_rds_unencrypted.tf",
        "costscanner/sample-repos/sample_rds_snapshot.tf",
        "costscanner/sample-repos/sample_s3_versioning.tf",
        "costscanner/sample-repos/sample_ebs.tf",
        "costscanner/sample-repos/sample_eip.tf",
        "costscanner/sample-repos/sample_s3_public.tf"
    ]

    resources = []
    for path in files_to_scan:
        try:
            with open(path, "r") as f:
                parsed = hcl2.load(f)

             # ⭐ ADD THIS DEBUG LINE HERE ⭐
            print(f"\nDEBUG: Parsed {path}:")
            print(parsed)

            resources.append({"file": path, "parsed": parsed})

        except Exception as e:
            print(f"❌ ERROR parsing {path}: {e}")

    return resources



# -----------------------------
# Import rules
# -----------------------------
from costscanner.rules.s3 import (
    check_public_s3_bucket,
    check_s3_versioning_disabled,
    check_unencrypted_s3_bucket
)
from costscanner.rules.eip import check_unused_eip
from costscanner.rules.ebs import check_unattached_ebs
from costscanner.rules.ec2 import check_overprovisioned_ec2
from costscanner.rules.rds import (
    check_unused_rds_snapshot,
    check_unencrypted_rds
)
from costscanner.rules.iam import check_iam_inline_policy
from costscanner.rules.sg import check_open_security_group

# -----------------------------
# Run all rules
# -----------------------------
def run_all_rules(resources):
    issues = []
    issues += check_unused_eip(resources)
    issues += check_unattached_ebs(resources)
    issues += check_s3_versioning_disabled(resources)
    issues += check_unencrypted_rds(resources)
    issues += check_iam_inline_policy(resources)
    issues += check_unused_rds_snapshot(resources)
    issues += check_open_security_group(resources)
    issues += check_public_s3_bucket(resources)
    issues += check_unencrypted_s3_bucket(resources)
    issues += check_overprovisioned_ec2(resources)
    return issues

# -----------------------------
# Report generator
# -----------------------------
def generate_report(issues, output_path):
    total_issues = len(issues)
    total_savings = sum(i.get("estimated_monthly_saving_usd", 0) for i in issues)

    severity_breakdown = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    for i in issues:
        sev = i.get("severity", "low")
        if sev in severity_breakdown:
            severity_breakdown[sev] += 1

    report = {
        "summary": {
            "total_issues": total_issues,
            "total_estimated_monthly_saving_usd": total_savings,
            "severity_breakdown": severity_breakdown
        },
        "timestamp": datetime.datetime.now().isoformat(),
        "issues": issues
    }

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(json.dumps(report, indent=2))

    return report

# -----------------------------
# MAIN
# -----------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--severity", choices=["low", "medium", "high", "critical"])
    parser.add_argument("--cost-only", action="store_true")
    parser.add_argument("--rule")
    parser.add_argument("--format", choices=["json", "csv", "html"], default="json")
    parser.add_argument("--summary", action="store_true", help="Show only one issue per rule")
    parser.add_argument("--grouped", action="store_true", help="Show rule-by-rule breakdown in summary")

    args = parser.parse_args()

    # Load files
    resources = parse_static_files()

    # Run all rules
    issues = run_all_rules(resources)

    #summary mode
    if args.summary:
        seen_rules = set()
        deduped_issues = []
        for issue in issues:
            if issue["rule"] not in seen_rules:
                deduped_issues.append(issue)
                seen_rules.add(issue["rule"])
        issues = deduped_issues

    # Generate report
    report = generate_report(issues, args.output)

     # output formats
    if args.format == "json":
        with open(args.output, "w") as f:
            json.dump(report, f, indent=2)

    elif args.format == "csv":
        import csv
        with open(args.output, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=issues[0].keys())
            writer.writeheader()
            writer.writerows(issues)

    elif args.format == "html":
        from html import escape
        html = """
        <html>
        <head>
            <title>Scan Report</title>
            <style>
                body {{
                    font-family: 'Segoe UI', sans-serif;
                    background-color: #f9f9f9;
                    color: #333;
                    padding: 2rem;
                }}
                h1, h2 {{
                    color: #2c3e50;
                }}
                ul {{
                    list-style-type: none;
                    padding: 0;
                }}
                li {{
                    background: #fff;
                    margin: 0.5rem 0;
                    padding: 0.75rem 1rem;
                    border-left: 5px solid #3498db;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                }}
                li.high {{ border-color: #e67e22; }}
                li.critical {{ border-color: #e74c3c; }}
                li.medium {{ border-color: #f1c40f; }}
                li.low {{ border-color: #2ecc71; }}
                .summary {{
                    background: #ecf0f1;
                    padding: 1rem;
                    border-radius: 5px;
                    margin-bottom: 2rem;
                }}
            </style>
        </head>
        <body>
            <h1>Scan Summary</h1>
            <div class="summary">
                <p><strong>Timestamp:</strong> {timestamp}</p>
                <p><strong>Total Issues:</strong> {total}</p>
                <p><strong>Estimated Monthly Savings:</strong> ${savings}</p>
                <h2>Severity Breakdown</h2>
                <ul>
                    {severity_items}
                </ul>
            </div>
            <h2>Issues</h2>
            <ul>
                {issue_items}
            </ul>
        </body>
        </html>
        """.format(
            timestamp=report["timestamp"],
            total=report["summary"]["total_issues"],
            savings=report["summary"]["total_estimated_monthly_saving_usd"],
            severity_items="\n".join(
                f"<li>{sev.capitalize()}: {count}</li>"
                for sev, count in report["summary"]["severity_breakdown"].items()
            ),
            issue_items="\n".join(
                f"<li class='{issue['severity'].lower()}'><strong>{issue['severity'].upper()}</strong>: {escape(issue['rule'])} — {escape(issue['details'])}</li>"
                for issue in issues
            )
        )

        with open(args.output, "w") as f:
            f.write(html)

    #grouped rule summary block
    if args.grouped:
        from collections import defaultdict
        grouped = defaultdict(list)
        for issue in issues:
            grouped[issue["rule"]].append(issue)

        print("\n================= RULE SUMMARY =================")
        for rule, rule_issues in grouped.items():
            print(f"🔍 {rule}: {len(rule_issues)} affected resources")
            print(f" Example: {rule_issues[0]['details']}")
        print("================================================\n")

    # Apply filters
    if args.severity:
        issues = [i for i in issues if i.get("severity") == args.severity]

    if args.cost_only:
        issues = [i for i in issues if i.get("estimated_monthly_saving_usd", 0) > 0]

    if args.rule:
        issues = [i for i in issues if i.get("rule") == args.rule]



    # Print summary
    print("\n================= SCAN SUMMARY =================")
    print(f"Timestamp: {report['timestamp']}")
    print(f"Total Issues: {report['summary']['total_issues']}")
    print(f"Estimated Monthly Savings: ${report['summary']['total_estimated_monthly_saving_usd']}")
    print("\nSeverity Breakdown:")
    for sev, count in report["summary"]["severity_breakdown"].items():
        print(f"  {sev.capitalize()}: {count}")
    print("================================================\n")





if __name__ == "__main__":
    main()
