from main import run_all_rules

def test_severity_filter_only_returns_matching_issues():
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
        },
        {
            "type": "aws_s3_bucket",
            "name": "demo-bucket",
            "file": "demo.tf",
            "parsed": {
                "resource": [
                    {
                        "aws_s3_bucket": {
                            "demo-bucket": {
                                # No versioning → triggers high severity
                            }
                        }
                    }
                ]
            }
        }
    ]

    all_issues = run_all_rules(resources)
    filtered = [i for i in all_issues if i["severity"] == "high"]

    assert len(filtered) == 1
    assert filtered[0]["rule"] == "s3_versioning_disabled"

def test_rule_filter_only_returns_matching_rule():
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
        },
        {
            "type": "aws_eip",
            "name": "demo-eip",
            "file": "demo.tf",
            "parsed": {
                "resource": [
                    {
                        "aws_eip": {
                            "demo-eip": {
                                # No attachment → triggers unused_eip
                            }
                        }
                    }
                ]
            }
        }
    ]

    all_issues = run_all_rules(resources)
    filtered = [i for i in all_issues if i["rule"] == "unused_eip"]

    assert len(filtered) == 1
    assert filtered[0]["rule"] == "unused_eip"

def test_cost_filter_only_returns_costly_issues():
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
        },
        {
            "type": "aws_s3_bucket",
            "name": "demo-bucket",
            "file": "demo.tf",
            "parsed": {
                "resource": [
                    {
                        "aws_s3_bucket": {
                            "demo-bucket": {
                                # No versioning → security issue, no cost
                            }
                        }
                    }
                ]
            }
        }
    ]

    all_issues = run_all_rules(resources)
    filtered = [i for i in all_issues if i.get("estimated_monthly_saving_usd", 0) > 100]

    assert len(filtered) == 1
    assert filtered[0]["rule"] == "overprovisioned_ec2"
