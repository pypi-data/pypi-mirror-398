from main import check_open_security_group

def test_open_security_group_detects_issue():
    resources = [
        {
            "type": "aws_security_group",
            "name": "demo",
            "file": "demo.tf",
            "parsed": {
                "resource": [
                    {
                        "aws_security_group": {
                            "demo": {
                                "ingress": [
                                    {
                                        "cidr_blocks": ["0.0.0.0/0"]
                                    }
                                ]
                            }
                        }
                    }
                ]
            }
        }
    ]

    issues = check_open_security_group(resources)

    assert len(issues) == 1
    assert issues[0]["rule"] == "open_security_group"
    assert "0.0.0.0" in issues[0]["details"]
