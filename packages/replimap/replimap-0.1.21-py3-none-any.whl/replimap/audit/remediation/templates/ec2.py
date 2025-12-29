"""
EC2 and Security Group remediation templates.

Generates Terraform code to fix EC2 and Security Group security issues.
"""

from __future__ import annotations


def _sanitize_resource_name(resource_name: str) -> str:
    """Sanitize a resource name for use in Terraform resource identifiers."""
    # Remove common prefixes
    for prefix in ["aws_instance.", "aws_security_group.", "aws_ebs_volume."]:
        resource_name = resource_name.replace(prefix, "")
    # Replace any non-alphanumeric characters with underscores
    return "".join(c if c.isalnum() else "_" for c in resource_name).strip("_")


def generate_ec2_imdsv2(
    instance_id: str,
    resource_name: str,
    instance_type: str = "t3.micro",
    ami_id: str = "REPLACE_WITH_AMI_ID",
) -> str:
    """
    Generate EC2 instance configuration enforcing IMDSv2.

    Remediates: CKV_AWS_79

    Args:
        instance_id: The EC2 instance ID
        resource_name: The Terraform resource name
        instance_type: The instance type
        ami_id: The AMI ID

    Returns:
        Terraform HCL for IMDSv2 configuration
    """
    safe_name = _sanitize_resource_name(resource_name)

    return f'''# EC2 Instance Metadata Service v2 (IMDSv2)
# Remediates: CKV_AWS_79
# Instance: {instance_id}
#
# IMDSv2 protects against SSRF attacks by requiring session tokens.
#
# NOTE: This is a PARTIAL resource definition. You must add all other
# required attributes from your existing instance configuration.

resource "aws_instance" "{safe_name}" {{
  ami           = "{ami_id}"
  instance_type = "{instance_type}"

  # Enforce IMDSv2
  metadata_options {{
    http_endpoint               = "enabled"
    http_tokens                 = "required"  # Enforces IMDSv2
    http_put_response_hop_limit = 1
    instance_metadata_tags      = "enabled"
  }}

  # Add other required configuration from your existing instance:
  # subnet_id                   = "..."
  # vpc_security_group_ids      = [...]
  # iam_instance_profile        = "..."
  # key_name                    = "..."
  # root_block_device {{ ... }}

  tags = {{
    Name = "{safe_name}"
  }}

  lifecycle {{
    prevent_destroy = true
  }}
}}

# Import command:
# terraform import aws_instance.{safe_name} {instance_id}
'''


def generate_ebs_encryption(
    volume_id: str,
    resource_name: str,
    size: int = 8,
    availability_zone: str = "REPLACE_WITH_AZ",
    kms_key_id: str | None = None,
) -> str:
    """
    Generate EBS volume encryption configuration.

    Remediates: CKV_AWS_3, CKV_AWS_4

    Args:
        volume_id: The EBS volume ID
        resource_name: The Terraform resource name
        size: Volume size in GB
        availability_zone: The availability zone
        kms_key_id: Optional KMS key ID

    Returns:
        Terraform HCL for encrypted EBS volume
    """
    safe_name = _sanitize_resource_name(resource_name)
    kms_line = f'\n  kms_key_id = "{kms_key_id}"' if kms_key_id else ""

    return f'''# EBS Volume Encryption
# Remediates: CKV_AWS_3, CKV_AWS_4
# Volume: {volume_id}
#
# WARNING: Existing unencrypted volumes cannot be encrypted in-place.
# You must create a snapshot, copy it with encryption, then create
# a new volume from the encrypted snapshot.
#
# For in-flight encryption, see AWS documentation on EBS encryption.

resource "aws_ebs_volume" "{safe_name}" {{
  availability_zone = "{availability_zone}"
  size              = {size}
  encrypted         = true{kms_line}

  tags = {{
    Name = "{safe_name}"
  }}
}}

# Import command (for new encrypted volume):
# terraform import aws_ebs_volume.{safe_name} {volume_id}

# Migration steps for existing unencrypted volume:
# 1. Create snapshot: aws ec2 create-snapshot --volume-id {volume_id}
# 2. Copy with encryption: aws ec2 copy-snapshot --source-snapshot-id snap-xxx --encrypted
# 3. Create new volume: aws ec2 create-volume --snapshot-id snap-encrypted-xxx
# 4. Stop instance, detach old volume, attach new volume
'''


def generate_ec2_detailed_monitoring(
    instance_id: str,
    resource_name: str,
) -> str:
    """
    Generate EC2 detailed monitoring configuration.

    Remediates: CKV_AWS_126

    Args:
        instance_id: The EC2 instance ID
        resource_name: The Terraform resource name

    Returns:
        Terraform HCL for detailed monitoring
    """
    safe_name = _sanitize_resource_name(resource_name)

    return f'''# EC2 Detailed Monitoring
# Remediates: CKV_AWS_126
# Instance: {instance_id}
#
# Detailed monitoring provides 1-minute metrics (vs 5-minute basic).
# Note: Detailed monitoring incurs additional CloudWatch charges.
#
# NOTE: This is a PARTIAL resource definition showing the monitoring attribute.
# Merge with your existing instance configuration.

resource "aws_instance" "{safe_name}" {{
  # ... other configuration ...

  monitoring = true  # Enable detailed monitoring

  # ... rest of configuration ...
}}

# To enable via AWS CLI without Terraform:
# aws ec2 monitor-instances --instance-ids {instance_id}

# Import command:
# terraform import aws_instance.{safe_name} {instance_id}
'''


def generate_security_group_restrict(
    security_group_id: str,
    resource_name: str,
    vpc_id: str = "REPLACE_WITH_VPC_ID",
    port: int = 22,
    allowed_cidrs: list[str] | None = None,
    description: str = "Managed by RepliMap",
) -> str:
    """
    Generate security group with restricted ingress rules.

    Remediates: CKV_AWS_23, CKV_AWS_24, CKV_AWS_25

    Args:
        security_group_id: The security group ID
        resource_name: The Terraform resource name
        vpc_id: The VPC ID
        port: The port to restrict (22 for SSH, 3389 for RDP)
        allowed_cidrs: List of allowed CIDR blocks
        description: Security group description

    Returns:
        Terraform HCL for restricted security group
    """
    safe_name = _sanitize_resource_name(resource_name)
    cidrs = allowed_cidrs or ["10.0.0.0/8"]  # Default to RFC1918

    protocol_name = "SSH" if port == 22 else "RDP" if port == 3389 else f"Port {port}"
    check_id = (
        "CKV_AWS_24" if port == 22 else "CKV_AWS_25" if port == 3389 else "CKV_AWS_23"
    )

    cidr_list = ", ".join(f'"{c}"' for c in cidrs)

    return f'''# Security Group - Restricted {protocol_name} Access
# Remediates: {check_id}
# Security Group: {security_group_id}
#
# WARNING: This replaces the security group ingress rules.
# Review allowed CIDRs before applying to ensure you don't lock yourself out.
#
# Best practices:
# - Never use 0.0.0.0/0 for SSH/RDP
# - Use bastion hosts or VPN for admin access
# - Consider AWS Systems Manager Session Manager instead of SSH

resource "aws_security_group" "{safe_name}" {{
  name        = "{safe_name}"
  description = "{description}"
  vpc_id      = "{vpc_id}"

  # Restricted {protocol_name} access
  ingress {{
    description = "{protocol_name} from internal networks only"
    from_port   = {port}
    to_port     = {port}
    protocol    = "tcp"
    cidr_blocks = [{cidr_list}]
  }}

  # Allow all outbound (adjust as needed)
  egress {{
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }}

  tags = {{
    Name = "{safe_name}"
  }}
}}

# Import command:
# terraform import aws_security_group.{safe_name} {security_group_id}

# Alternative: Use security group rules resource to add/modify rules
# without replacing the entire security group:
#
# resource "aws_security_group_rule" "{safe_name}_ssh" {{
#   type              = "ingress"
#   from_port         = {port}
#   to_port           = {port}
#   protocol          = "tcp"
#   cidr_blocks       = [{cidr_list}]
#   security_group_id = "{security_group_id}"
# }}
'''
