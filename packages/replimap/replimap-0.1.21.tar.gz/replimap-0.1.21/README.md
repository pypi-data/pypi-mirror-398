<div align="center">

# RepliMap

[![PyPI](https://img.shields.io/pypi/v/replimap?color=blue)](https://pypi.org/project/replimap/)
[![Downloads](https://img.shields.io/pypi/dm/replimap)](https://pypi.org/project/replimap/)
[![Python](https://img.shields.io/pypi/pyversions/replimap)](https://pypi.org/project/replimap/)
[![Tests](https://github.com/RepliMap/replimap/actions/workflows/test.yml/badge.svg)](https://github.com/RepliMap/replimap/actions/workflows/test.yml)

### Clone AWS Prod to Staging in 5 Minutes. Save 50% on Cloud Costs.

> Stop writing `terraform import` by hand. Stop paying production prices for dev environments.

**Read-only AWS access** | **100% local processing** | **Minutes, not weeks**

[Quick Start](#-quick-start) | [Features](#-features) | [Pricing](#-pricing) | [Full Documentation](docs/technical-reference.md)

</div>

---

## See It In Action

RepliMap doesn't just clone—it **optimizes**. Here's real output from a production scan:

```
╭──────────────────────────────────── Right-Sizer Savings Report ────────────────────────────────╮
│ Right-Sizer Analysis Complete                                                                  │
│                                                                                                │
│ Resources analyzed: 16 (7 EC2, 3 RDS, 6 ElastiCache)                                          │
│                                                                                                │
│ ┌─────────────────────────────────────────────────────────────────┐                            │
│ │  Cost Comparison                                                │                            │
│ ├─────────────────────────────────────────────────────────────────┤                            │
│ │  Original (Production):      $  1,856.58/mo                     │                            │
│ │  Optimized (Dev/Staging):    $    939.75/mo                     │                            │
│ ├─────────────────────────────────────────────────────────────────┤                            │
│ │  Monthly Savings:             $    916.83                       │                            │
│ │  Annual Savings:              $ 11,001.96                       │                            │
│ │  Savings Percentage:                  49%                       │                            │
│ └─────────────────────────────────────────────────────────────────┘                            │
│                                                                                                │
│ Optimizations Applied:                                                                         │
│  • EC2: m5.2xlarge → t3.large (7 instances)                                                   │
│  • RDS: db.r5.xlarge → db.t3.large, Multi-AZ disabled (3 instances)                           │
│  • ElastiCache: cache.r5.large → cache.t3.medium (6 clusters)                                 │
╰────────────────────────────────────────────────────────────────────────────────────────────────╯
```

**One command. Real savings. Production-grade Terraform.**

---

## The Problem RepliMap Solves

| The Old Way (Manual / Terraformer) | With RepliMap |
|:-----------------------------------|:--------------|
| **Weeks** of `terraform import` | **5 minutes** from scan to deploy |
| Staging costs = Production costs | **50% cheaper** with auto-downsizing |
| Hardcoded secrets in generated code | **Auto-sanitized** (SOC2-ready) |
| Messy, monolithic HCL files | **Clean, modular** Terraform |
| Requires write access to AWS | **Read-only** permissions only |
| Manual instance size adjustments | **AI-powered** Right-Sizer |

---

## Quick Start

### 1. Install

```bash
# Recommended: isolated environment
pipx install replimap

# Verify
replimap --version
```

### 2. Clone & Optimize

```bash
replimap clone \
  --profile your-aws-profile \
  --output-dir ./staging-infra \
  --dev-mode  # Activates Right-Sizer cost optimization
```

### 3. Deploy

```bash
cd ./staging-infra
terraform init
terraform plan   # See the optimized instance types!
terraform apply
```

**That's it.** Production infrastructure → Cost-optimized staging in under 5 minutes.

---

## Features

### Free & Open Source

| Feature | Description |
|---------|-------------|
| **Reverse Engineering** | VPC, EC2, RDS, ElastiCache, S3, SQS → Terraform HCL |
| **Security Sanitization** | Passwords, secrets, account IDs auto-stripped |
| **Dependency Graph** | Understands VPC → Subnet → EC2 relationships |
| **100% Local** | Your data never leaves your machine |
| **Read-Only** | Only needs `ReadOnlyAccess` IAM permissions |

### Pro Features (Solo+)

| Feature | Description |
|---------|-------------|
| **Right-Sizer Engine** | AI-powered instance optimization with savings reports |
| **Cost Estimation** | Estimate monthly costs with optimization recommendations |
| **Drift Detection** | Compare Terraform state vs actual AWS resources |
| **Dependency Explorer** | Impact analysis before modifying resources |
| **Multi-Format Output** | Terraform, CloudFormation, Pulumi |

---

## Right-Sizer: The Money-Saving Engine

The **Right-Sizer** is what makes RepliMap unique. It's not just cloning—it's **intelligent optimization**.

```bash
# Conservative mode (default) - balanced performance and cost
replimap clone --profile prod --dev-mode --output-dir ./staging

# Aggressive mode - maximum savings for CI/CD environments
replimap clone --profile prod --dev-mode --dev-strategy aggressive --output-dir ./staging
```

### What Gets Optimized

| Resource | Example Transformation | Typical Savings |
|----------|----------------------|-----------------|
| **EC2** | `m5.2xlarge` → `t3.large` | 60-70% |
| **RDS** | `db.r5.xlarge` → `db.t3.large` + Multi-AZ off | 50-60% |
| **ElastiCache** | `cache.r5.large` → `cache.t3.medium` | 50-60% |
| **Storage** | `gp2` → `gp3` | 20% |

### How It Works

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  1. Scan AWS    │────▶│  2. Generate    │────▶│  3. Right-Size  │
│  (Read-only)    │     │  variables.tf   │     │  .auto.tfvars   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
                                               ┌─────────────────┐
                                               │  Production     │
                                               │  defaults in    │
                                               │  variables.tf   │
                                               │  ────────────   │
                                               │  Dev overrides  │
                                               │  in .auto.tfvars│
                                               └─────────────────┘
```

**Delete `right-sizer.auto.tfvars` to instantly revert to production sizes.**

---

## Pricing

RepliMap is **Open Core**. The CLI and Terraform generation are free forever.

| Plan | Price | Best For |
|------|-------|----------|
| **Free** | $0/mo | Trying out, small projects |
| **Solo** | $29/mo | Individual DevOps engineers |
| **Pro** | $79/mo | Small teams, multiple accounts |
| **Team** | $149/mo | Larger teams with collaboration |
| **Enterprise** | Custom | SSO, audit logs, support SLA |

### Feature Comparison

| Feature | Free | Solo | Pro | Team |
|---------|:----:|:----:|:---:|:----:|
| Terraform Output | Yes | Yes | Yes | Yes |
| Security Sanitization | Yes | Yes | Yes | Yes |
| **Right-Sizer** | No | Yes | Yes | Yes |
| CloudFormation Output | No | No | Yes | Yes |
| Cost Estimation | No | No | Yes | Yes |
| Drift Detection | No | No | Yes | Yes |
| Dependency Explorer | No | No | No | Yes |
| AWS Accounts | 1 | 1 | 3 | 10 |

<div align="center">

[**Get Started Free →**](https://replimap.dev) | [**See All Plans →**](https://replimap.dev/pricing)

</div>

---

## Who Is This For?

- **DevOps Engineers** tired of writing `terraform import` commands
- **Startups** needing staging environments without breaking the bank
- **Platform Teams** standardizing infrastructure across environments
- **Consultants** auditing client AWS infrastructure
- **Anyone** paying too much for non-production AWS environments

---

## FAQ

<details>
<summary><b>Is it safe to run on production AWS?</b></summary>

**Yes!** RepliMap only needs `ReadOnlyAccess`. It cannot modify any resources. Your credentials stay on your machine.
</details>

<details>
<summary><b>What if I don't buy a license?</b></summary>

The CLI is 100% functional for free—full Terraform generation with security sanitization. Right-Sizer adds cost optimization but isn't required.
</details>

<details>
<summary><b>How accurate are the savings estimates?</b></summary>

We use real-time AWS pricing data. Estimates are based on on-demand pricing and are typically within ±10% of actual costs.
</details>

<details>
<summary><b>Does it work with Terraform Cloud / Terragrunt?</b></summary>

Yes! The generated code is standard Terraform HCL compatible with any workflow.
</details>

<details>
<summary><b>What AWS resources are supported?</b></summary>

24 resource types: VPC, Subnets, Security Groups, EC2, RDS, ElastiCache, S3, SQS, SNS, ALB/NLB, ASG, Launch Templates, and more. [See full list →](docs/technical-reference.md#supported-resources-24-types)
</details>

---

## Supported Resources

| Category | Resources |
|----------|-----------|
| **Network** | VPC, Subnets, Security Groups, Route Tables, NAT/Internet Gateways |
| **Compute** | EC2, ASG, Launch Templates, ALB/NLB, Target Groups |
| **Database** | RDS (MySQL, PostgreSQL, Aurora), ElastiCache (Redis, Memcached) |
| **Storage** | S3 Buckets, EBS Volumes |
| **Messaging** | SQS Queues, SNS Topics |

---

## Documentation & Reference

This README provides a high-level overview. For detailed technical documentation:

### [Technical Reference & CLI Guide](docs/technical-reference.md)

- [Installation Options](docs/technical-reference.md#installation)
- [Full CLI Command Reference](docs/technical-reference.md#cli-reference)
- [Configuration Guide](docs/technical-reference.md#configuration)
- [Architecture Deep Dive](docs/technical-reference.md#architecture)
- [Security & IAM Policies](docs/technical-reference.md#security)
- [Graph-Based Selection Engine](docs/technical-reference.md#graph-based-selection-engine)
- [All Supported Resources](docs/technical-reference.md#supported-resources-24-types)

---

## Security

- **Read-Only Access**: Only requires `ReadOnlyAccess` IAM permissions
- **Local Processing**: All data stays on your machine
- **No Data Upload**: Your infrastructure data never leaves your environment
- **SOC2-Ready**: Auto-sanitizes secrets, passwords, and credentials

See [IAM_POLICY.md](./IAM_POLICY.md) for recommended minimal permissions.

---

## License

- **CLI & Terraform Generator**: Proprietary with free tier
- **Right-Sizer API**: Commercial license required (Solo+)

See [LICENSE](./LICENSE) for details.

---

<div align="center">

### Ready to save 50% on your AWS staging bill?

[**Get Started Free →**](https://replimap.dev)

---

Built with care by an AWS Solutions Architect who got tired of writing `terraform import`.

[Twitter](https://twitter.com/davidlu1001) | [Blog](https://replimap.dev/blog) | [Support](mailto:support@replimap.dev)

</div>
