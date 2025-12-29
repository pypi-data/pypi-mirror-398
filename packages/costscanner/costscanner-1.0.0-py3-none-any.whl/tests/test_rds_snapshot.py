from main import check_unused_rds_snapshot

def test_unused_rds_snapshot_detects_issue():
    resources = [
        {
            "type": "aws_db_snapshot",
            "name": "demo-snap",
            "file": "demo.tf",
            "parsed": {
                "resource": [
                    {
                        "aws_db_snapshot": {
                            "demo-snap": {
                                # No tags or usage info → should trigger issue
                            }
                        }
                    }
                ]
            }
        }
    ]

    issues = check_unused_rds_snapshot(resources)

    assert len(issues) == 1
    assert issues[0]["rule"] == "unused_rds_snapshot"
    assert "snapshot" in issues[0]["details"].lower()
