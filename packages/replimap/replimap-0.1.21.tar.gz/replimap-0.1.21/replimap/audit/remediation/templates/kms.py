"""
KMS remediation templates.

Generates Terraform code to fix KMS security issues.
"""

from __future__ import annotations


def _sanitize_resource_name(resource_name: str) -> str:
    """Sanitize a resource name for use in Terraform resource identifiers."""
    # Remove common prefixes
    for prefix in ["aws_kms_key.", "aws_kms_alias."]:
        resource_name = resource_name.replace(prefix, "")
    # Replace any non-alphanumeric characters with underscores
    return "".join(c if c.isalnum() else "_" for c in resource_name).strip("_")


def generate_kms_rotation(
    key_id: str,
    resource_name: str,
    description: str = "KMS key with rotation enabled",
) -> str:
    """
    Generate KMS key rotation configuration.

    Remediates: CKV_AWS_7

    Args:
        key_id: The KMS key ID or ARN
        resource_name: The Terraform resource name
        description: Description for the key

    Returns:
        Terraform HCL for KMS key with rotation
    """
    safe_name = _sanitize_resource_name(resource_name)

    return f'''# KMS Key Rotation
# Remediates: CKV_AWS_7
# Key: {key_id}
#
# Automatic key rotation rotates the backing key material annually.
# Benefits:
# - No application changes required
# - Previous versions retained for decryption
# - Meets compliance requirements
#
# Note: Only supported for symmetric CMKs (not asymmetric).

resource "aws_kms_key" "{safe_name}" {{
  description             = "{description}"
  deletion_window_in_days = 30

  enable_key_rotation = true  # Enable automatic annual rotation

  tags = {{
    Name = "{safe_name}"
  }}
}}

# Optional: Add a human-readable alias
resource "aws_kms_alias" "{safe_name}" {{
  name          = "alias/{safe_name}"
  target_key_id = aws_kms_key.{safe_name}.key_id
}}

# To enable via AWS CLI:
# aws kms enable-key-rotation --key-id {key_id}

# Import commands:
# terraform import aws_kms_key.{safe_name} {key_id}
'''


def generate_kms_policy(
    key_id: str,
    resource_name: str,
    account_id: str = "REPLACE_WITH_ACCOUNT_ID",
    admin_role_arns: list[str] | None = None,
) -> str:
    """
    Generate KMS key policy with least privilege.

    Remediates: CKV_AWS_33

    Args:
        key_id: The KMS key ID or ARN
        resource_name: The Terraform resource name
        account_id: AWS account ID
        admin_role_arns: List of admin role ARNs

    Returns:
        Terraform HCL for KMS key with restrictive policy
    """
    safe_name = _sanitize_resource_name(resource_name)

    if admin_role_arns:
        admin_arns = ", ".join(f'"{arn}"' for arn in admin_role_arns)
        admin_principal = f"AWS = [{admin_arns}]"
    else:
        admin_principal = (
            f'AWS = "arn:aws:iam::{account_id}:role/REPLACE_WITH_ADMIN_ROLE"'
        )

    return f'''# KMS Key Policy - Least Privilege
# Remediates: CKV_AWS_33
# Key: {key_id}
#
# This policy follows the principle of least privilege:
# - Root account has full access (required for key management)
# - Specific admin roles can manage the key
# - Service roles have limited usage permissions
#
# WARNING: Review and customize these permissions for your use case.

resource "aws_kms_key" "{safe_name}" {{
  description             = "KMS key with restrictive policy"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  policy = jsonencode({{
    Version = "2012-10-17"
    Id      = "{safe_name}-key-policy"
    Statement = [
      {{
        Sid    = "EnableRootAccountAccess"
        Effect = "Allow"
        Principal = {{
          AWS = "arn:aws:iam::{account_id}:root"
        }}
        Action   = "kms:*"
        Resource = "*"
      }},
      {{
        Sid    = "AllowKeyAdministrators"
        Effect = "Allow"
        Principal = {{
          {admin_principal}
        }}
        Action = [
          "kms:Create*",
          "kms:Describe*",
          "kms:Enable*",
          "kms:List*",
          "kms:Put*",
          "kms:Update*",
          "kms:Revoke*",
          "kms:Disable*",
          "kms:Get*",
          "kms:Delete*",
          "kms:TagResource",
          "kms:UntagResource",
          "kms:ScheduleKeyDeletion",
          "kms:CancelKeyDeletion"
        ]
        Resource = "*"
      }},
      {{
        Sid    = "AllowKeyUsage"
        Effect = "Allow"
        Principal = {{
          AWS = "arn:aws:iam::{account_id}:root"
        }}
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ]
        Resource = "*"
        Condition = {{
          StringEquals = {{
            "kms:CallerAccount" = "{account_id}"
          }}
        }}
      }},
      {{
        Sid    = "AllowServiceUsage"
        Effect = "Allow"
        Principal = {{
          Service = [
            "s3.amazonaws.com",
            "rds.amazonaws.com",
            "logs.amazonaws.com"
          ]
        }}
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:DescribeKey",
          "kms:CreateGrant"
        ]
        Resource = "*"
        Condition = {{
          StringEquals = {{
            "kms:CallerAccount" = "{account_id}"
          }}
        }}
      }}
    ]
  }})

  tags = {{
    Name = "{safe_name}"
  }}
}}

resource "aws_kms_alias" "{safe_name}" {{
  name          = "alias/{safe_name}"
  target_key_id = aws_kms_key.{safe_name}.key_id
}}

# Import commands:
# terraform import aws_kms_key.{safe_name} {key_id}

# To update policy via AWS CLI:
# aws kms put-key-policy --key-id {key_id} --policy-name default --policy file://policy.json
'''
