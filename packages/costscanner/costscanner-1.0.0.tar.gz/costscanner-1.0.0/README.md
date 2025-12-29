🌟 CostScanner
Terraform cost & security scanner for cloud optimization.

   ____            _     _____
  / ___|___   ___ | | __| ____|_ __   __ _  ___ ___ _ __   ___ _ __
 | |   / _ \ / _ \| |/ /|  _| | '_ \ / _` |/ __/ _ \ '_ \ / _ \ '__|
 | |__| (_) | (_) |   < | |___| | | | (_| | (_|  __/ | | |  __/ |
  \____\___/ \___/|_|\_\|_____|_| |_|\__,_|\___\___|_| |_|\___|_|


A fast, modular Terraform cost & security scanner for cloud optimization.
CostScanner analyzes Terraform files to detect misconfigurations, security risks, and cost‑wasting resources. It provides clear findings, estimated monthly savings, and supports both table and JSON output — perfect for CI pipelines, DevOps workflows, and cloud cost governance.

🚀 Features
🔍 Static analysis of Terraform files (no cloud credentials needed)

💰 Cost optimization (unused EIPs, unattached EBS, unused snapshots…)

🔐 Security misconfiguration detection (open SGs, unencrypted RDS, public S3…)

📊 Beautiful CLI output (table or JSON)

🎯 Filtering by severity, rule, or minimum savings

🧩 Modular rule engine — easy to extend

📁 Works offline and supports any Terraform project structure

📸 Example Output
Code
Scan Results
+------------------------+-----------------------------+----------+-------------+-------------------+
| Rule                  | Resource                    | Severity | Savings ($) | Message           |
+------------------------+-----------------------------+----------+-------------+-------------------+
| unused_eip            | sample_network.tf:aws_eip   | medium   | 3.60        | No message provided|
| unattached_ebs        | sample_ec2.ebs.tf:aws_ebs   | medium   | 16.00       | No message provided|
| s3_versioning_disabl..| sample_s3.tf:aws_s3_bucket  | high     | 0.00        | No message provided|
| unencrypted_rds       | sample_rds.tf:aws_db_inst.. | high     | 10.00       | No message provided|
| iam_inline_policy     | iam_inline_policy.tf:aws_.. | high     | 0.00        | No message provided|
| unused_rds_snapshot   | unused_rds_snapshot.tf:aw.. | medium   | 1.00        | No message provided|
| open_security_group   | sample_sg.tf:aws_security.. | critical | 0.00        | No message provided|
+------------------------+-----------------------------+----------+-------------+-------------------+

📦 Installation
Clone the repository:

bash
git clone https://github.com/yourusername/cost-scanner.git
cd cost-scanner

Install dependencies:
bash
pip install -r requirements.txt

🧠 Usage

Basic scan
bash
python -m costscanner.cli sample-repos/

Table output
bash
python -m costscanner.cli sample-repos/ --format table

JSON output
bash
python -m costscanner.cli sample-repos/ --format json

Save JSON to file
bash
python -m costscanner.cli sample-repos/ --format json --output report.json

Filter by severity
bash
python -m costscanner.cli sample-repos/ --severity high

Filter by rule
bash
python -m costscanner.cli sample-repos/ --rule unencrypted_rds

Filter by minimum savings
bash
python -m costscanner.cli sample-repos/ --min-cost 5

🧩 Supported Rules
| Rule Name               | Icon | Severity | Savings (Monthly) | Description |
|-------------------------|------|----------|--------------------|-------------|
| unused_eip              | 🟧   | **Medium** (Orange)   | ~$3.60            | Elastic IP is allocated but not associated with any instance — AWS charges for unused EIPs. |
| unattached_ebs          | 🟧   | **Medium** (Orange)   | ~$16.00           | EBS volume exists but is not attached to any EC2 instance — still incurs storage costs. |
| s3_versioning_disabled  | 🟨   | **High** (Yellow)     | $0                | S3 bucket versioning is disabled — increases risk of accidental deletion or overwrite. |
| unencrypted_rds         | 🟨   | **High** (Yellow)     | $0                | RDS instance lacks encryption — sensitive data may be exposed. |
| iam_inline_policy       | 🟦   | **Low** (Blue)        | $0                | IAM user or role uses inline policies — harder to manage and audit than managed policies. |
| unused_rds_snapshot     | 🟧   | **Medium** (Orange)   | ~$1–$5            | RDS snapshot is not linked to any active instance — unnecessary storage cost. |
| open_security_group     | 🔴   | **Critical** (Red)    | $0                | Security group allows unrestricted inbound access (0.0.0.0/0) — major security risk. |
| public_s3_bucket        | 🔴   | **Critical** (Red)    | $0                | S3 bucket is publicly accessible — data exposure risk. |
| unencrypted_s3_bucket   | 🟨   | **High** (Yellow)     | $0                | S3 bucket lacks server‑side encryption — data stored unprotected. |
| overprovisioned_ec2     | 🟧   | **Medium** (Orange)   | ~$20–$100+        | EC2 instance type is larger than required — potential cost optimization opportunity. |

🏗️ Architecture
Code
Terraform Files
      ↓
Parser (HCL → Python objects)
      ↓
Rule Engine (runs all rules)
      ↓
Report Generator (table / JSON)
      ↓
CLI Output

🧪 Testing
Run all tests:

bash
pytest

Recommended test structure:

Code
tests/
├── unit/
│   ├── test_rules.py
│   ├── test_parser.py
│   └── test_report.py
└── integration/
    ├── sample_repos/
    └── test_full_scan.py

🤝 Contributing
Contributions are welcome! You can help by:

Adding new rules

Improving the parser

Enhancing the report generator

Writing integration tests

Improving documentation

Fork → Branch → PR.

💬 Why I Built This
CostScanner was created to:

Practice real-world cloud security & cost optimization

Build a modular, testable Python CLI tool

Demonstrate DevOps, IaC, and automation skills

Create a portfolio project that hiring managers immediately understand

It’s designed to be simple, fast, and easy to extend.

🛣️ Roadmap
HTML report output

Rule metadata registry (rules.yaml)

GitHub Actions CI

Auto-discovery of rules

Plugin system for custom rules

VS Code extension

📄 License
MIT License — free to use, modify, and distribute.
