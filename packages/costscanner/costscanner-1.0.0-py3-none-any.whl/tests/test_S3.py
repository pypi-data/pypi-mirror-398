from main import check_unencrypted_s3_bucket

def test_encrypted_s3_bucket_no_issue():
    resources = [
        {
            "type": "aws_s3_bucket",
            "name": "demo",
            "file": "demo.tf",
            "parsed": {
                "resource": [
                    {
                        "aws_s3_bucket": {
                            "demo": {
                                "server_side_encryption_configuration": [
                                    {
                                        "rule": [
                                            {
                                                "apply_server_side_encryption_by_default": [
                                                    {
                                                        "sse_algorithm": ["AES256"]
                                                    }
                                                ]
                                            }
                                        ]
                                    }
                                ]
                            }
                        }
                    }
                ]
            }
        }
    ]

    issues = check_unencrypted_s3_bucket(resources)

    assert len(issues) == 0
