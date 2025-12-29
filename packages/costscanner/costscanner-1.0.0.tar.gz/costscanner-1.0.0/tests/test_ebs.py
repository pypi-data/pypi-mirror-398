from main import check_unattached_ebs

def test_unattached_ebs_detects_issue():
    resources = [
        {
            "type": "aws_ebs_volume",
            "name": "demo-ebs",
            "file": "demo.tf",
            "parsed": {
                "resource": [
                    {
                        "aws_ebs_volume": {
                            "demo-ebs": {
                                # No "attachment" block → should trigger issue
                            }
                        }
                    }
                ]
            }
        }
    ]

    issues = check_unattached_ebs(resources)

    assert len(issues) == 1
    assert issues[0]["rule"] == "unattached_ebs"
    assert "ebs" in issues[0]["details"].lower()
