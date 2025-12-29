import json
from rich.console import Console
from rich.table import Table
from datetime import datetime
from collections import defaultdict

def render_table(data):
    return "Table rendering not implemented yet"

def generate_report(issues, output_path=None, format="table"):
    timestamp = datetime.utcnow().isoformat()
    total_savings = sum(i.get("estimated_monthly_saving_usd", 0) for i in issues)
    severity_counts = defaultdict(int)
    for i in issues:
        severity_counts[i["severity"]] += 1

    summary = {
        "total_issues": len(issues),
        "total_savings_usd": total_savings,
        "severity_breakdown": severity_counts,
    }

    report = {
        "timestamp": timestamp,
        "summary": summary,
        "issues": issues,
    }

    if format == "json":
        if output_path:
            with open(output_path, "w") as f:
                json.dump(report, f, indent=2)
        else:
            print(json.dumps(report, indent=2))

    elif format == "table":
        console = Console()
        table = Table(title="Scan Results")
        table.add_column("Rule")
        table.add_column("Resource")
        table.add_column("Severity")
        table.add_column("Savings ($)")
        table.add_column("Message")

        for i in issues:
            table.add_row(
                i["rule"],
                i["resource"],
                i["severity"],
                f'{i.get("estimated_monthly_saving_usd", 0):.2f}',
                i.get("message", "No message provided")

            )

        console.print(table)

    return report
