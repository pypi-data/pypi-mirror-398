"""
RDS remediation templates.

Generates Terraform code to fix RDS security issues.
"""

from __future__ import annotations


def _sanitize_resource_name(resource_name: str) -> str:
    """Sanitize a resource name for use in Terraform resource identifiers."""
    # Remove common prefixes
    for prefix in ["aws_db_instance.", "aws_rds_cluster."]:
        resource_name = resource_name.replace(prefix, "")
    # Replace any non-alphanumeric characters with underscores
    return "".join(c if c.isalnum() else "_" for c in resource_name).strip("_")


def generate_rds_encryption(
    db_instance_id: str,
    resource_name: str,
    engine: str = "mysql",
    engine_version: str = "8.0",
    instance_class: str = "db.t3.micro",
    kms_key_arn: str | None = None,
) -> str:
    """
    Generate RDS encryption configuration.

    Remediates: CKV_AWS_16, CKV_AWS_17

    Args:
        db_instance_id: The RDS instance identifier
        resource_name: The Terraform resource name
        engine: Database engine
        engine_version: Database engine version
        instance_class: Instance class
        kms_key_arn: Optional KMS key ARN

    Returns:
        Terraform HCL for encrypted RDS instance
    """
    safe_name = _sanitize_resource_name(resource_name)
    kms_line = f'  kms_key_id = "{kms_key_arn}"\n' if kms_key_arn else ""

    return f'''# RDS Encryption at Rest
# Remediates: CKV_AWS_16, CKV_AWS_17
# Instance: {db_instance_id}
#
# WARNING: Existing unencrypted RDS instances cannot be encrypted in-place.
# You must create an encrypted snapshot and restore from it.
#
# Migration steps:
# 1. Create snapshot of unencrypted instance
# 2. Copy snapshot with encryption enabled
# 3. Restore new instance from encrypted snapshot
# 4. Update application connection strings
# 5. Delete old unencrypted instance

resource "aws_db_instance" "{safe_name}" {{
  identifier     = "{db_instance_id}"
  engine         = "{engine}"
  engine_version = "{engine_version}"
  instance_class = "{instance_class}"

  storage_encrypted = true
{kms_line}
  # Add other required configuration:
  # allocated_storage     = 20
  # db_name               = "..."
  # username              = "..."
  # password              = "..."  # Use secrets manager
  # db_subnet_group_name  = "..."
  # vpc_security_group_ids = [...]
  # parameter_group_name  = "..."

  # Recommended security settings:
  publicly_accessible    = false
  skip_final_snapshot    = false
  final_snapshot_identifier = "{db_instance_id}-final"
  deletion_protection    = true
  copy_tags_to_snapshot  = true

  tags = {{
    Name = "{safe_name}"
  }}
}}

# Import command:
# terraform import aws_db_instance.{safe_name} {db_instance_id}

# AWS CLI commands for migration:
# 1. aws rds create-db-snapshot --db-instance-identifier {db_instance_id} --db-snapshot-identifier {db_instance_id}-unencrypted
# 2. aws rds copy-db-snapshot --source-db-snapshot-identifier {db_instance_id}-unencrypted --target-db-snapshot-identifier {db_instance_id}-encrypted --kms-key-id alias/aws/rds
# 3. aws rds restore-db-instance-from-db-snapshot --db-instance-identifier {db_instance_id}-new --db-snapshot-identifier {db_instance_id}-encrypted
'''


def generate_rds_multi_az(
    db_instance_id: str,
    resource_name: str,
) -> str:
    """
    Generate RDS Multi-AZ configuration.

    Remediates: CKV_AWS_157, CKV_AWS_15

    Args:
        db_instance_id: The RDS instance identifier
        resource_name: The Terraform resource name

    Returns:
        Terraform HCL for Multi-AZ RDS
    """
    safe_name = _sanitize_resource_name(resource_name)

    return f'''# RDS Multi-AZ Deployment
# Remediates: CKV_AWS_157, CKV_AWS_15
# Instance: {db_instance_id}
#
# Multi-AZ provides:
# - Automatic failover to standby in another AZ
# - Synchronous replication
# - Minimal downtime during maintenance
#
# NOTE: Multi-AZ doubles your RDS costs.

resource "aws_db_instance" "{safe_name}" {{
  # ... existing configuration ...

  multi_az = true  # Enable Multi-AZ deployment

  # ... rest of configuration ...
}}

# To modify via AWS CLI:
# aws rds modify-db-instance --db-instance-identifier {db_instance_id} --multi-az --apply-immediately

# Import command:
# terraform import aws_db_instance.{safe_name} {db_instance_id}
'''


def generate_rds_deletion_protection(
    db_instance_id: str,
    resource_name: str,
) -> str:
    """
    Generate RDS deletion protection configuration.

    Remediates: CKV_AWS_128

    Args:
        db_instance_id: The RDS instance identifier
        resource_name: The Terraform resource name

    Returns:
        Terraform HCL for deletion protection
    """
    safe_name = _sanitize_resource_name(resource_name)

    return f'''# RDS Deletion Protection
# Remediates: CKV_AWS_128
# Instance: {db_instance_id}
#
# Deletion protection prevents accidental deletion of the database.
# You must disable it before deleting the instance.

resource "aws_db_instance" "{safe_name}" {{
  # ... existing configuration ...

  deletion_protection = true  # Prevent accidental deletion

  # ... rest of configuration ...
}}

# To enable via AWS CLI:
# aws rds modify-db-instance --db-instance-identifier {db_instance_id} --deletion-protection --apply-immediately

# Import command:
# terraform import aws_db_instance.{safe_name} {db_instance_id}
'''


def generate_rds_monitoring(
    db_instance_id: str,
    resource_name: str,
    monitoring_interval: int = 60,
    monitoring_role_arn: str = "REPLACE_WITH_MONITORING_ROLE_ARN",
) -> str:
    """
    Generate RDS Enhanced Monitoring configuration.

    Remediates: CKV_AWS_91

    Args:
        db_instance_id: The RDS instance identifier
        resource_name: The Terraform resource name
        monitoring_interval: Monitoring interval in seconds (1, 5, 10, 15, 30, 60)
        monitoring_role_arn: ARN of the monitoring IAM role

    Returns:
        Terraform HCL for enhanced monitoring
    """
    safe_name = _sanitize_resource_name(resource_name)

    return f'''# RDS Enhanced Monitoring
# Remediates: CKV_AWS_91
# Instance: {db_instance_id}
#
# Enhanced monitoring provides real-time OS metrics at per-second granularity.
# Requires an IAM role with the AmazonRDSEnhancedMonitoringRole policy.

# IAM Role for Enhanced Monitoring
resource "aws_iam_role" "{safe_name}_monitoring" {{
  name = "{safe_name}-rds-monitoring"

  assume_role_policy = jsonencode({{
    Version = "2012-10-17"
    Statement = [{{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {{
        Service = "monitoring.rds.amazonaws.com"
      }}
    }}]
  }})
}}

resource "aws_iam_role_policy_attachment" "{safe_name}_monitoring" {{
  role       = aws_iam_role.{safe_name}_monitoring.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}}

# RDS Instance with Enhanced Monitoring
resource "aws_db_instance" "{safe_name}" {{
  # ... existing configuration ...

  monitoring_interval = {monitoring_interval}  # Seconds: 1, 5, 10, 15, 30, or 60
  monitoring_role_arn = aws_iam_role.{safe_name}_monitoring.arn

  # ... rest of configuration ...
}}

# To enable via AWS CLI:
# 1. Create IAM role (see above)
# 2. aws rds modify-db-instance --db-instance-identifier {db_instance_id} \\
#      --monitoring-interval {monitoring_interval} \\
#      --monitoring-role-arn <role-arn> \\
#      --apply-immediately

# Import command:
# terraform import aws_db_instance.{safe_name} {db_instance_id}
'''


def generate_rds_iam_auth(
    db_instance_id: str,
    resource_name: str,
) -> str:
    """
    Generate RDS IAM authentication configuration.

    Remediates: CKV_AWS_118

    Args:
        db_instance_id: The RDS instance identifier
        resource_name: The Terraform resource name

    Returns:
        Terraform HCL for IAM authentication
    """
    safe_name = _sanitize_resource_name(resource_name)

    return f'''# RDS IAM Database Authentication
# Remediates: CKV_AWS_118
# Instance: {db_instance_id}
#
# IAM authentication uses AWS IAM credentials instead of passwords.
# Benefits:
# - No password management
# - Token-based authentication (15-minute validity)
# - Centralized access management via IAM
#
# Note: Requires application code changes to use IAM auth tokens.

resource "aws_db_instance" "{safe_name}" {{
  # ... existing configuration ...

  iam_database_authentication_enabled = true

  # ... rest of configuration ...
}}

# IAM Policy for database access
resource "aws_iam_policy" "{safe_name}_db_access" {{
  name = "{safe_name}-rds-iam-auth"

  policy = jsonencode({{
    Version = "2012-10-17"
    Statement = [{{
      Effect = "Allow"
      Action = "rds-db:connect"
      Resource = "arn:aws:rds-db:*:*:dbuser:*/*"
    }}]
  }})
}}

# To enable via AWS CLI:
# aws rds modify-db-instance --db-instance-identifier {db_instance_id} \\
#   --enable-iam-database-authentication \\
#   --apply-immediately

# To generate auth token:
# aws rds generate-db-auth-token \\
#   --hostname <endpoint> \\
#   --port 3306 \\
#   --username <db_user>

# Import command:
# terraform import aws_db_instance.{safe_name} {db_instance_id}
'''
