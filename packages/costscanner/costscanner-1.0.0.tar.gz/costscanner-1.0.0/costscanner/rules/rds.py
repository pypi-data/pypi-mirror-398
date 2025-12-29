def check_unencrypted_rds(resources):
    issues = []
    for r in resources:
        for block in r["parsed"].get("resource", []):
            if "aws_db_instance" in block:
                db_block = block["aws_db_instance"]
                for name, attrs in db_block.items():
                    if not attrs.get("storage_encrypted", False):
                        issues.append({
                            "rule": "unencrypted_rds",
                            "resource": f"{r['file']}:aws_db_instance.{name}",
                            "severity": "high",
                            "estimated_monthly_saving_usd": 0,
                            "details": "RDS instance storage is not encrypted",
                            "recommendation": "Enable storage encryption for compliance and security"
                        })
    return issues


def check_unused_rds_snapshot(resources):
    issues = []
    snapshot_names = set()
    instance_refs = set()

    for r in resources:
        parsed = r.get("parsed", {})
        for block in parsed.get("resource", []):
            if "aws_db_snapshot" in block:
                for name in block["aws_db_snapshot"]:
                    snapshot_names.add((r["file"], name))
            if "aws_db_instance" in block:
                for _, attrs in block["aws_db_instance"].items():
                    snapshot_id = attrs.get("snapshot_identifier")
                    if snapshot_id:
                        instance_refs.add(snapshot_id)

    for file, name in snapshot_names:
        if name not in instance_refs:
            issues.append({
                "rule": "unused_rds_snapshot",
                "resource": f"{file}:aws_db_snapshot.{name}",
                "severity": "medium",
                "estimated_monthly_saving_usd": 10.0,
                "details": "RDS snapshot appears unused",
                "recommendation": "Delete or archive unused snapshots to reduce storage cost"
            })

    return issues
