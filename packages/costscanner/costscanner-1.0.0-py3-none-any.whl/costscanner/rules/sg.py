
def check_open_security_group(resources):
    issues = []
    for r in resources:
        for block in r["parsed"].get("resource", []):
            if "aws_security_group" in block:
                sg_block = block["aws_security_group"]
                for name, attrs in sg_block.items():
                    ingress = attrs.get("ingress", [])
                    for rule in ingress:
                        cidr_blocks = rule.get("cidr_blocks", [])
                        for cidr in cidr_blocks:
                            if cidr == "0.0.0.0/0":
                                issues.append({
                                    "rule": "open_security_group",
                                    "resource": f"{r['file']}:aws_security_group.{name}",
                                    "severity": "critical",
                                    "estimated_monthly_saving_usd": 0,
                                    "details": f"Security group allows access from {cidr}",
                                    "recommendation": "Restrict CIDR blocks to trusted IP ranges"
                               })
    return issues
