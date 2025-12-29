# aws-s3-risk-footprint

A CLI tool to analyze AWS S3 **regional distribution and security risk**.

`aws-s3-risk-footprint` provides fast, read-only visibility into where your S3 data lives, how it is distributed across AWS regions, and whether any buckets present elevated security risk — all directly from the terminal.

Designed for cloud security engineers, GRC teams, and AWS practitioners who need lightweight visibility without relying on the AWS Console.

---

## Features

- Regional footprint view of S3 buckets across AWS regions
- Bucket counts by region (data locality & sprawl)
- Expandable inventory of individual bucket names
- Security risk analysis (e.g. public bucket exposure)
- Optional object count inspection
- AWS identity awareness (`whoami`)
- Uses existing AWS credentials (no secrets stored)

---

## Installation
```bash
pip install aws-s3-risk-footprint
```

After installation, the CLI command is:
```bash
aws-s3-risk
```

---

## Usage

### Show regional distribution
```bash
aws-s3-risk map
```

Displays a regional summary of S3 buckets to help assess data residency and bucket sprawl.

**Example output:**
```
Total S3 Buckets: 29

AWS S3 REGIONAL DISTRIBUTION
------------------------------
ap-south-1      █                    1
eu-central-1    █                    1
us-east-1       ████████████████████ 15
us-west-1       ████████████████     12

WEST (Americas)
---------------
us-west-1       [████████████████] 12

EAST (Americas)
---------------
us-east-1       [████████████████████] 15

EUROPE
------
eu-central-1    [█] 1

APAC
----
ap-south-1      [█] 1

```

### Expand bucket inventory
```bash
aws-s3-risk expand
```
**Example output:**
```
Total S3 Buckets: 29

AWS S3 BUCKET FOOTPRINT
==================================================

us-east-1 (15)
--------------
• analytics-query-results-us-east-1
• cloudtrail-logs-central
• infrastructure-templates-us-east-1
• data-lake-athena-results
• vpc-flow-logs-primary
• app-artifacts-prod
• application-backups
• security-audit-logs
• config-recorder-storage
• ssm-inventory-data
• elasticbeanstalk-assets
• monitoring-metrics-store
• global-app-assets-us-east-1
• billing-reports-bucket
• public-site-content

us-west-1 (12)
--------------
• media-assets-prod
• backup-archive-west
• application-logs-west
• replication-target-west
• analytics-stage-west
• app-artifacts-dev
• monitoring-snapshots
• lambda-deployments
• terraform-state-west
• ci-cd-artifacts
• image-processing-input
• image-processing-output

eu-central-1 (1)
----------------
• eu-customer-exports

ap-south-1 (1)
--------------
• apac-ingestion-bucket
```

**Filter by region:**
```bash
aws-s3-risk expand --region us-east-1
```

### Analyze security risk
```bash
aws-s3-risk risk
```

Buckets are classified into **LOW** / **MEDIUM** / **HIGH** risk based on observable exposure signals such as public access configuration, bucket policy status, and object-level accessibility.

**Example output:**
```
AWS S3 RISK SUMMARY
========================================
HIGH RISK   : 2 buckets
MEDIUM RISK : 5 buckets
LOW RISK    : 22 buckets

High-Risk Buckets
----------------------------------------
- marketing-assets-prod (us-east-1)
- legacy-logs-2019 (us-west-1)
```

**Include object counts** (may incur additional API calls):
```bash
aws-s3-risk risk --objects
```

**Example output:**
```
Total S3 Buckets: 29

AWS S3 RISK SUMMARY
========================================
HIGH RISK   : 8 buckets
MEDIUM RISK : 0 buckets
LOW RISK    : 21 buckets

High-Risk Buckets
----------------------------------------
• public-web-assets (us-east-1) — 1 object
• elasticbeanstalk-app-assets (us-east-1) — 1 object
• marketing-site-content (us-east-1) — 1 object
• dev-artifacts-storage (us-west-1) — 1 object
• application-backups-dev (us-west-1) — 3 objects
• prod-artifacts-legacy (us-west-1) — 1 object
• prod-logs-unrestricted (us-west-1) — 1 object
• apac-ingestion-endpoint (ap-south-1) — 1 object

```
### Show AWS execution context
```bash
aws-s3-risk whoami
```

Displays the AWS identity (user or role) used to execute the tool.

**Example output:**
```
AWS Identity
==============================
Account ID : 123456789010
ARN        : arn:aws:iam::123456789010:user/cli-user
```

### Use a specific AWS profile
```bash
aws-s3-risk risk --profile production
```

---

## Use Cases

- Cloud security posture reviews
- Data residency & compliance (e.g. GDPR, CCPA)
- Identifying publicly exposed S3 buckets
- AWS account hygiene and inventory audits
- Pre-migration or architecture assessments

---

## Permissions Required

This tool is **read-only** and requires the following AWS IAM permissions:

- `s3:ListAllMyBuckets`
- `s3:GetBucketLocation`
- `s3:GetBucketPolicyStatus`
- `s3:GetBucketPublicAccessBlock`
- `s3:GetBucketAcl`
- `s3:ListBucket` *(optional, for object counts)*

**No write actions are performed.**

---

## Authentication

Uses standard AWS credential resolution via `boto3`:

- AWS CLI credentials (`~/.aws/credentials`)
- Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
- IAM roles
- AWS SSO sessions

**No credentials are stored or transmitted by this tool.**

---

## Requirements

- Python 3.7+
- `boto3` >= 1.26.0

---

## Disclaimer
This tool does not modify AWS resources and is not a substitute for a full security audit.

---

## License

MIT License

---
