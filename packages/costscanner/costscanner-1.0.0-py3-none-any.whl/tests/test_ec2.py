from main import check_overprovisioned_ec2

def test_overprovisioned_ec2_detects_issue():
    resources = [
        {
            "type": "aws_instance",
            "name": "demo-ec2",
            "file": "demo.tf",
            "parsed": {
                "resource": [
                    {
                        "aws_instance": {
                            "demo-ec2": {
                                "instance_type": ["m5.4xlarge"]
                            }
                        }
                    }
                ]
            }
        }
    ]

    issues = check_overprovisioned_ec2(resources)

    assert len(issues) == 1
    assert issues[0]["rule"] == "overprovisioned_ec2"
    assert "m5.4xlarge" in issues[0]["details"]
