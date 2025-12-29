"""
Remediation templates for generating Terraform fix code.

Each template module provides functions that generate Terraform HCL
for specific security remediation scenarios.
"""

from replimap.audit.remediation.templates.ec2 import (
    generate_ebs_encryption,
    generate_ec2_detailed_monitoring,
    generate_ec2_imdsv2,
    generate_security_group_restrict,
)
from replimap.audit.remediation.templates.kms import (
    generate_kms_policy,
    generate_kms_rotation,
)
from replimap.audit.remediation.templates.rds import (
    generate_rds_deletion_protection,
    generate_rds_encryption,
    generate_rds_iam_auth,
    generate_rds_monitoring,
    generate_rds_multi_az,
)
from replimap.audit.remediation.templates.s3 import (
    generate_s3_encryption,
    generate_s3_logging,
    generate_s3_public_access_block,
    generate_s3_ssl_policy,
    generate_s3_versioning,
)

__all__ = [
    # S3
    "generate_s3_encryption",
    "generate_s3_versioning",
    "generate_s3_logging",
    "generate_s3_public_access_block",
    "generate_s3_ssl_policy",
    # EC2
    "generate_ec2_imdsv2",
    "generate_ebs_encryption",
    "generate_ec2_detailed_monitoring",
    "generate_security_group_restrict",
    # RDS
    "generate_rds_encryption",
    "generate_rds_multi_az",
    "generate_rds_deletion_protection",
    "generate_rds_monitoring",
    "generate_rds_iam_auth",
    # KMS
    "generate_kms_rotation",
    "generate_kms_policy",
]
