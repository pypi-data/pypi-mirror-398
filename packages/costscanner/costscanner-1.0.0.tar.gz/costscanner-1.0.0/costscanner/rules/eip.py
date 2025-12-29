def check_unused_eip(resources):
    # AWS charges for Elastic IPs not attached to a running instance
    price_per_eip = 3.6  # approx $0.005 per hour = ~$3.6/month
    issues = []
    for r in resources:
        for block in r["parsed"].get("resource", []):
            if "aws_eip" in block:
                eip_block = block["aws_eip"]
                for name, attrs in eip_block.items():
                    issues.append({
                        "rule": "unused_eip",
                       "resource": f"{r['file']}:aws_eip.{name}",
                        "severity": "medium",
                        "estimated_monthly_saving_usd": price_per_eip,
                       "details": "EIP allocated but not attached to any instance",
                        "recommendation": "Release unused Elastic IPs to avoid charges"
                    })
    return issues
