def check_overprovisioned_ec2(resources):
    issues = []
    for r in resources:
        blocks = r.get("parsed", {}).get("resource", [])
        for block in blocks:
            if "aws_instance" in block:
                for name, props in block["aws_instance"].items():
                    instance_type = props.get("instance_type", "")
                    if instance_type == "t3.large":
                        issues.append({
                            "rule": "overprovisioned_ec2",
                            "severity": "high",
                            "details": f"EC2 instance '{name}' uses oversized type '{instance_type}'",
                            "estimated_monthly_saving_usd": 5.0
                        })
    return issues

