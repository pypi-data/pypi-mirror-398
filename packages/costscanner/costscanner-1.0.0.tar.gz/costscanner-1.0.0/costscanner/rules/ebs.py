def check_unattached_ebs(resources):
    price_per_gb = 0.08
    issues = []
    for r in resources:
        for block in r["parsed"].get("resource", []):
            if "aws_ebs_volume" in block:
                volume_block = block["aws_ebs_volume"]
                for name, attrs in volume_block.items():
                    size = attrs.get("size", 100)
                    est = round(float(size) * price_per_gb, 2)
                    issues.append({
                        "rule": "unattached_ebs",
                        "resource": f"{r['file']}:aws_ebs_volume.{name}",
                        "severity": "medium",
                        "estimated_monthly_saving_usd": est,
                        "details": f"EBS volume size ~{size} GB (heuristic demo)",
                        "recommendation": "Delete or snapshot and move to colder storage after verification"
                    })
    return issues
