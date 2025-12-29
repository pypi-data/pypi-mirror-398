"""
S3 remediation templates.

Generates Terraform code to fix S3 security issues.
"""

from __future__ import annotations


def _sanitize_resource_name(resource_name: str) -> str:
    """Sanitize a resource name for use in Terraform resource identifiers."""
    # Remove aws_s3_bucket. prefix if present
    name = resource_name.replace("aws_s3_bucket.", "")
    # Replace any non-alphanumeric characters with underscores
    return "".join(c if c.isalnum() else "_" for c in name).strip("_")


def generate_s3_encryption(
    bucket_name: str,
    resource_name: str,
    use_kms: bool = False,
    kms_key_id: str | None = None,
) -> str:
    """
    Generate S3 bucket encryption configuration.

    Remediates: CKV_AWS_19, CKV_AWS_145

    Args:
        bucket_name: The S3 bucket name
        resource_name: The Terraform resource name
        use_kms: Whether to use KMS encryption instead of AES256
        kms_key_id: Optional KMS key ID for KMS encryption

    Returns:
        Terraform HCL for S3 encryption configuration
    """
    safe_name = _sanitize_resource_name(resource_name)

    if use_kms:
        kms_key_line = (
            f'  kms_master_key_id = "{kms_key_id}"'
            if kms_key_id
            else "  kms_master_key_id = aws_kms_key.s3.arn"
        )
        return f'''# S3 Bucket Encryption - KMS
# Remediates: CKV_AWS_19, CKV_AWS_145
# Bucket: {bucket_name}

resource "aws_s3_bucket_server_side_encryption_configuration" "{safe_name}_encryption" {{
  bucket = "{bucket_name}"

  rule {{
    apply_server_side_encryption_by_default {{
      sse_algorithm     = "aws:kms"
{kms_key_line}
    }}
    bucket_key_enabled = true
  }}
}}

# Import command:
# terraform import aws_s3_bucket_server_side_encryption_configuration.{safe_name}_encryption {bucket_name}
'''
    else:
        return f'''# S3 Bucket Encryption - AES256
# Remediates: CKV_AWS_19
# Bucket: {bucket_name}

resource "aws_s3_bucket_server_side_encryption_configuration" "{safe_name}_encryption" {{
  bucket = "{bucket_name}"

  rule {{
    apply_server_side_encryption_by_default {{
      sse_algorithm = "AES256"
    }}
  }}
}}

# Import command:
# terraform import aws_s3_bucket_server_side_encryption_configuration.{safe_name}_encryption {bucket_name}
'''


def generate_s3_versioning(bucket_name: str, resource_name: str) -> str:
    """
    Generate S3 bucket versioning configuration.

    Remediates: CKV_AWS_18

    Args:
        bucket_name: The S3 bucket name
        resource_name: The Terraform resource name

    Returns:
        Terraform HCL for S3 versioning configuration
    """
    safe_name = _sanitize_resource_name(resource_name)

    return f'''# S3 Bucket Versioning
# Remediates: CKV_AWS_18
# Bucket: {bucket_name}

resource "aws_s3_bucket_versioning" "{safe_name}_versioning" {{
  bucket = "{bucket_name}"

  versioning_configuration {{
    status = "Enabled"
  }}
}}

# Import command:
# terraform import aws_s3_bucket_versioning.{safe_name}_versioning {bucket_name}
'''


def generate_s3_logging(
    bucket_name: str,
    resource_name: str,
    target_bucket: str | None = None,
    target_prefix: str | None = None,
) -> str:
    """
    Generate S3 bucket logging configuration.

    Remediates: CKV_AWS_21

    Args:
        bucket_name: The S3 bucket name
        resource_name: The Terraform resource name
        target_bucket: Target bucket for logs (uses placeholder if not specified)
        target_prefix: Prefix for log objects

    Returns:
        Terraform HCL for S3 logging configuration
    """
    safe_name = _sanitize_resource_name(resource_name)
    target = target_bucket or "REPLACE_WITH_LOG_BUCKET_NAME"
    prefix = target_prefix or f"s3-access-logs/{bucket_name}/"

    return f'''# S3 Bucket Logging
# Remediates: CKV_AWS_21
# Bucket: {bucket_name}
#
# NOTE: You must specify a target logging bucket.
# The target bucket must have proper ACLs configured.

resource "aws_s3_bucket_logging" "{safe_name}_logging" {{
  bucket = "{bucket_name}"

  target_bucket = "{target}"
  target_prefix = "{prefix}"
}}

# Import command:
# terraform import aws_s3_bucket_logging.{safe_name}_logging {bucket_name}
'''


def generate_s3_public_access_block(bucket_name: str, resource_name: str) -> str:
    """
    Generate S3 bucket public access block configuration.

    Remediates: CKV_AWS_53, CKV_AWS_54, CKV_AWS_55, CKV_AWS_56, CKV_AWS_57

    Args:
        bucket_name: The S3 bucket name
        resource_name: The Terraform resource name

    Returns:
        Terraform HCL for S3 public access block
    """
    safe_name = _sanitize_resource_name(resource_name)

    return f'''# S3 Bucket Public Access Block
# Remediates: CKV_AWS_53, CKV_AWS_54, CKV_AWS_55, CKV_AWS_56, CKV_AWS_57
# Bucket: {bucket_name}
#
# WARNING: This will block ALL public access to the bucket.
# Review your use case before applying.

resource "aws_s3_bucket_public_access_block" "{safe_name}_public_access" {{
  bucket = "{bucket_name}"

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}}

# Import command:
# terraform import aws_s3_bucket_public_access_block.{safe_name}_public_access {bucket_name}
'''


def generate_s3_ssl_policy(bucket_name: str, resource_name: str) -> str:
    """
    Generate S3 bucket policy enforcing SSL/TLS.

    Remediates: CKV_AWS_20

    Args:
        bucket_name: The S3 bucket name
        resource_name: The Terraform resource name

    Returns:
        Terraform HCL for S3 SSL-only policy
    """
    safe_name = _sanitize_resource_name(resource_name)

    return f'''# S3 Bucket SSL-Only Policy
# Remediates: CKV_AWS_20
# Bucket: {bucket_name}
#
# WARNING: This policy denies all non-HTTPS requests.
# Ensure all applications use HTTPS before applying.
#
# NOTE: If the bucket already has a policy, you must MERGE this
# statement with the existing policy rather than replacing it.

resource "aws_s3_bucket_policy" "{safe_name}_ssl_policy" {{
  bucket = "{bucket_name}"

  policy = jsonencode({{
    Version = "2012-10-17"
    Statement = [
      {{
        Sid       = "EnforceSSLOnly"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:*"
        Resource = [
          "arn:aws:s3:::{bucket_name}",
          "arn:aws:s3:::{bucket_name}/*"
        ]
        Condition = {{
          Bool = {{
            "aws:SecureTransport" = "false"
          }}
        }}
      }}
    ]
  }})
}}

# Import command:
# terraform import aws_s3_bucket_policy.{safe_name}_ssl_policy {bucket_name}
'''
