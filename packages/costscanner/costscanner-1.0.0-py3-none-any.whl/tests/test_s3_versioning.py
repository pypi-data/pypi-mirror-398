from main import check_s3_versioning_disabled

def test_s3_versioning_disabled_detects_issue():
    resources = [
        {
            "type": "aws_s3_bucket",
            "name": "demo-bucket",
            "file": "demo.tf",
            "parsed": {
                "resource": [
                    {
                        "aws_s3_bucket": {
                            "demo-bucket": {
                                # No versioning block → should trigger issue
                            }
                        }
                    }
                ]
            }
        }
    ]

    issues = check_s3_versioning_disabled(resources)

    assert len(issues) == 1
    assert issues[0]["rule"] == "s3_versioning_disabled"
    assert "versioning" in issues[0]["details"].lower()
