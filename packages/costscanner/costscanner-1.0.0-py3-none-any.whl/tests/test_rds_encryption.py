from main import check_unencrypted_rds

def test_unencrypted_rds_detects_issue():
    resources = [
        {
            "type": "aws_db_instance",
            "name": "demo-rds",
            "file": "demo.tf",
            "parsed": {
                "resource": [
                    {
                        "aws_db_instance": {
                            "demo-rds": {
                                # No storage_encrypted block → should trigger issue
                            }
                        }
                    }
                ]
            }
        }
    ]

    issues = check_unencrypted_rds(resources)

    assert len(issues) == 1
    assert issues[0]["rule"] == "unencrypted_rds"
    assert "encrypted" in issues[0]["details"].lower()
