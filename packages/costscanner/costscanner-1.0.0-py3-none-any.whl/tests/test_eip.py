from main import check_unused_eip

def test_unused_eip_detects_issue():
    resources = [
        {
            "type": "aws_eip",
            "name": "demo-eip",
            "file": "demo.tf",
            "parsed": {
                "resource": [
                    {
                        "aws_eip": {
                            "demo-eip": {
                                # No instance attached
                            }
                        }
                    }
                ]
            }
        }
    ]

    issues = check_unused_eip(resources)

    assert len(issues) == 1
    assert issues[0]["rule"] == "unused_eip"
    assert "eip" in issues[0]["details"].lower()
