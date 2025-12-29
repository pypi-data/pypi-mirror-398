import os
import hcl2

# ---------------------------------------------------------
# Helper: Parse all .tf files and extract resources
# ---------------------------------------------------------
def load_resources(path):
    resources = []

    for root, _, files in os.walk(path):
        for file in files:
            if file.endswith(".tf"):
                full_path = os.path.join(root, file)

                with open(full_path, "r") as f:
                    try:
                        data = hcl2.load(f)
                    except Exception:
                        continue

            if isinstance(data, dict) and "resource" in data:
                    for resource_type, blocks in data["resource"].items():
                        for name, attrs in blocks.items():
                            resources.append({
                                "file": file,
                                "name": name,
                                "type": resource_type,
                                **attrs
                            })

    return resources


# ---------------------------------------------------------
# RULES (10 total)
# ---------------------------------------------------------

def unused_eip(resources):
    issues = []
    for r in resources:
        if r["type"] == "aws_eip" and "instance" not in r:
            issues.append({
                "rule": "unused_eip",
                "resource": f"{r['file']}:{r['type']}.{r['name']}",
                "severity": "medium",
                "savings": 3.60,
                "message": "Elastic IP is allocated but not associated"
            })
    return issues


def unattached_ebs(resources):
    issues = []
    for r in resources:
        if r["type"] == "aws_ebs_volume" and "attachment" not in r:
            issues.append({
                "rule": "unattached_ebs",
                "resource": f"{r['file']}:{r['type']}.{r['name']}",
                "severity": "medium",
                "savings": 16.00,
                "message": "EBS volume is not attached to any instance"
            })
    return issues


def s3_versioning_disabled(resources):
    issues = []
    for r in resources:
        if r["type"] == "aws_s3_bucket" and "versioning" not in r:
            issues.append({
                "rule": "s3_versioning_disabled",
                "resource": f"{r['file']}:{r['type']}.{r['name']}",
                "severity": "high",
                "savings": 0.0,
                "message": "S3 bucket versioning is disabled"
            })
    return issues


def unencrypted_rds(resources):
    issues = []
    for r in resources:
        if r["type"] == "aws_db_instance" and not r.get("storage_encrypted", False):
            issues.append({
                "rule": "unencrypted_rds",
                "resource": f"{r['file']}:{r['type']}.{r['name']}",
                "severity": "high",
                "savings": 0.0,
                "message": "RDS instance lacks encryption"
            })
    return issues


def iam_inline_policy(resources):
    issues = []
    for r in resources:
        if r["type"] in ["aws_iam_user_policy", "aws_iam_role_policy"]:
            issues.append({
                "rule": "iam_inline_policy",
                "resource": f"{r['file']}:{r['type']}.{r['name']}",
                "severity": "low",
                "savings": 0.0,
                "message": "IAM inline policy detected"
            })
    return issues


def unused_rds_snapshot(resources):
    issues = []
    for r in resources:
        if r["type"] == "aws_db_snapshot":
            issues.append({
                "rule": "unused_rds_snapshot",
                "resource": f"{r['file']}:{r['type']}.{r['name']}",
                "severity": "medium",
                "savings": 5.0,
                "message": "Unused RDS snapshot found"
            })
    return issues


def open_security_group(resources):
    issues = []
    for r in resources:
        if r["type"] == "aws_security_group":
            ingress = r.get("ingress", [])
            for rule in ingress:
                if "cidr_blocks" in rule and "0.0.0.0/0" in rule["cidr_blocks"]:
                    issues.append({
                        "rule": "open_security_group",
                        "resource": f"{r['file']}:{r['type']}.{r['name']}",
                        "severity": "critical",
                        "savings": 0.0,
                        "message": "Security group allows unrestricted access (0.0.0.0/0)"
                    })
    return issues


def public_s3_bucket(resources):
    issues = []
    for r in resources:
        if r["type"] == "aws_s3_bucket" and r.get("acl") in ["public-read", "public-read-write"]:
            issues.append({
                "rule": "public_s3_bucket",
                "resource": f"{r['file']}:{r['type']}.{r['name']}",
                "severity": "critical",
                "savings": 0.0,
                "message": "S3 bucket is publicly accessible"
            })
    return issues


def unencrypted_s3_bucket(resources):
    issues = []
    for r in resources:
        if r["type"] == "aws_s3_bucket" and "server_side_encryption_configuration" not in r:
            issues.append({
                "rule": "unencrypted_s3_bucket",
                "resource": f"{r['file']}:{r['type']}.{r['name']}",
                "severity": "high",
                "savings": 0.0,
                "message": "S3 bucket lacks encryption"
            })
    return issues


def overprovisioned_ec2(resources):
    issues = []
    expensive_types = ["m5.4xlarge", "m5.8xlarge", "c5.9xlarge"]
    for r in resources:
        if r["type"] == "aws_instance" and r.get("instance_type") in expensive_types:
            issues.append({
                "rule": "overprovisioned_ec2",
                "resource": f"{r['file']}:{r['type']}.{r['name']}",
                "severity": "medium",
                "savings": 25.0,
                "message": "EC2 instance may be overprovisioned"
            })
    return issues


# ---------------------------------------------------------
# MAIN SCAN FUNCTION
# ---------------------------------------------------------
def scan_project(path):
    resources = load_resources(path)

    rules = [
        unused_eip,
        unattached_ebs,
        s3_versioning_disabled,
        unencrypted_rds,
        iam_inline_policy,
        unused_rds_snapshot,
        open_security_group,
        public_s3_bucket,
        unencrypted_s3_bucket,
        overprovisioned_ec2
    ]

    issues = []
    for rule in rules:
        issues.extend(rule(resources))

    return issues
