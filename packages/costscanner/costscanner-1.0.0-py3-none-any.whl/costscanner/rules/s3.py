import json

def check_public_s3_bucket(resources):
    issues = []
    for r in resources:
        for block in r["parsed"].get("resource", []):
            if "aws_s3_bucket" in block:
                bucket_block = block["aws_s3_bucket"]
                for name, attrs in bucket_block.items():
                    acl = attrs.get("acl")
                    if acl == "public-read":
                        issues.append({
                            "rule": "public_s3_bucket",
                            "resource": f"{r['file']}:aws_s3_bucket.{name}",
                            "severity": "high",
                            "estimated_monthly_saving_usd": 0,
                            "details": "S3 bucket ACL is public-read",
                            "recommendation": "Remove public ACL; use least-privilege bucket policy"
                        })
    return issues


def check_s3_versioning_disabled(resources):
    issues = []

    for r in resources:
        parsed = r.get("parsed", {})
        resource_blocks = parsed.get("resource", [])

        for block in resource_blocks:
            if "aws_s3_bucket" in block:
                for name, props in block["aws_s3_bucket"].items():
                    versioning = props.get("versioning", [{}])[0]
                    enabled = versioning.get("enabled", False)

                    if not enabled:
                        issues.append({
                            "rule": "s3_versioning_disabled",
                            "severity": "high",
                            "details": f"S3 bucket '{name}' does not have versioning enabled",
                            "estimated_monthly_saving_usd": 0
                        })

    return issues


def check_unencrypted_s3_bucket(resources):
    issues = []

    for r in resources:
        parsed = r.get("parsed", {})
        resource_blocks = parsed.get("resource", [])

        for block in resource_blocks:
            if "aws_s3_bucket" in block:
                for name, props in block["aws_s3_bucket"].items():
                    # If no "server_side_encryption_configuration" block → unencrypted
                    if "server_side_encryption_configuration" not in props:
                        issues.append({
                            "rule": "unencrypted_s3_bucket",
                            "severity": "high",
                            "details": f"S3 bucket '{name}' lacks encryption configuration",
                            "estimated_monthly_saving_usd": 0
                        })

    return issues
