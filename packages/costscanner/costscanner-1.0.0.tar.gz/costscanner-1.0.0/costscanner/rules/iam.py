def check_iam_inline_policy(resources):
    issues = []

    for r in resources:
        parsed = r.get("parsed", {})
        resource_blocks = parsed.get("resource", [])

        for block in resource_blocks:
            if "aws_iam_role_policy" in block:
                for name, props in block["aws_iam_role_policy"].items():
                    issues.append({
                        "rule": "iam_inline_policy",
                        "severity": "high",
                        "details": f"IAM inline policy '{name}' detected in file {r['file']}",
                        "estimated_monthly_saving_usd": 0
                    })

    return issues
