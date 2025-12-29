"""
SOC2 Trust Service Criteria Mapping for Checkov Findings.

Maps Checkov check IDs to SOC2 controls for compliance reporting.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SOC2Control:
    """SOC2 Trust Service Criteria control mapping."""

    control: str
    category: str
    description: str


# Mapping of Checkov check IDs to SOC2 controls
SOC2_MAPPING: dict[str, SOC2Control] = {
    # CC6.1 - Logical and Physical Access Controls
    "CKV_AWS_40": SOC2Control("CC6.1", "Access Control", "IAM Password Policy"),
    "CKV_AWS_41": SOC2Control("CC6.1", "Access Control", "Root Account MFA"),
    "CKV_AWS_23": SOC2Control(
        "CC6.1", "Access Control", "Security Group Ingress Restriction"
    ),
    "CKV_AWS_24": SOC2Control(
        "CC6.1", "Access Control", "Security Group SSH Restriction"
    ),
    "CKV_AWS_25": SOC2Control(
        "CC6.1", "Access Control", "Security Group RDP Restriction"
    ),
    "CKV_AWS_49": SOC2Control("CC6.1", "Access Control", "IAM Policy Least Privilege"),
    "CKV_AWS_62": SOC2Control("CC6.1", "Access Control", "Lambda Not Public"),
    "CKV_AWS_26": SOC2Control("CC6.1", "Access Control", "SNS Topic Encryption"),
    # CC6.6 - Encryption at Rest
    "CKV_AWS_19": SOC2Control("CC6.6", "Encryption", "S3 Bucket Encryption"),
    "CKV_AWS_3": SOC2Control("CC6.6", "Encryption", "EBS Volume Encryption"),
    "CKV_AWS_16": SOC2Control("CC6.6", "Encryption", "RDS Instance Encryption"),
    "CKV_AWS_17": SOC2Control("CC6.6", "Encryption", "RDS Snapshot Encryption"),
    "CKV_AWS_27": SOC2Control("CC6.6", "Encryption", "SQS Queue Encryption"),
    "CKV_AWS_7": SOC2Control("CC6.6", "Encryption", "KMS Key Rotation"),
    "CKV_AWS_33": SOC2Control("CC6.6", "Encryption", "KMS CMK Policy"),
    "CKV_AWS_64": SOC2Control("CC6.6", "Encryption", "Redshift Cluster Encryption"),
    "CKV_AWS_65": SOC2Control("CC6.6", "Encryption", "ECR Repository Encryption"),
    "CKV_AWS_84": SOC2Control("CC6.6", "Encryption", "ElastiCache Encryption at Rest"),
    # CC6.7 - Encryption in Transit
    "CKV_AWS_2": SOC2Control("CC6.7", "Encryption", "ALB HTTPS/TLS"),
    "CKV_AWS_20": SOC2Control("CC6.7", "Encryption", "S3 Bucket SSL Only"),
    "CKV_AWS_83": SOC2Control(
        "CC6.7", "Encryption", "ElastiCache Encryption in Transit"
    ),
    "CKV_AWS_103": SOC2Control("CC6.7", "Encryption", "ALB TLS 1.2+"),
    # CC7.2 - Monitoring and Detection
    "CKV_AWS_67": SOC2Control("CC7.2", "Monitoring", "CloudTrail Enabled"),
    "CKV_AWS_21": SOC2Control("CC7.2", "Monitoring", "S3 Bucket Logging"),
    "CKV_AWS_48": SOC2Control("CC7.2", "Monitoring", "VPC Flow Logs Enabled"),
    "CKV_AWS_35": SOC2Control("CC7.2", "Monitoring", "CloudTrail Log Validation"),
    "CKV_AWS_36": SOC2Control(
        "CC7.2", "Monitoring", "CloudTrail S3 Bucket Access Logging"
    ),
    "CKV_AWS_50": SOC2Control("CC7.2", "Monitoring", "Lambda X-Ray Tracing"),
    "CKV_AWS_76": SOC2Control("CC7.2", "Monitoring", "API Gateway Access Logging"),
    "CKV_AWS_91": SOC2Control("CC7.2", "Monitoring", "RDS Enhanced Monitoring"),
    "CKV_AWS_104": SOC2Control("CC7.2", "Monitoring", "ALB Access Logging"),
    # CC7.3 - Incident Response
    "CKV_AWS_52": SOC2Control("CC7.3", "Monitoring", "GuardDuty Enabled"),
    "CKV_AWS_78": SOC2Control("CC7.3", "Monitoring", "Config Rule Enabled"),
    # CC8.1 - Change Management
    "CKV_AWS_18": SOC2Control("CC8.1", "Change Mgmt", "S3 Bucket Versioning"),
    "CKV_AWS_4": SOC2Control("CC8.1", "Change Mgmt", "EBS Snapshot Encryption"),
    # A1.2 - Availability
    "CKV_AWS_5": SOC2Control("A1.2", "Availability", "DocumentDB Backup Retention"),
    "CKV_AWS_15": SOC2Control("A1.2", "Availability", "RDS Multi-AZ"),
    "CKV_AWS_28": SOC2Control("A1.2", "Availability", "DynamoDB Backup Enabled"),
    "CKV_AWS_128": SOC2Control("A1.2", "Availability", "RDS Deletion Protection"),
}


def get_soc2_mapping(check_id: str) -> SOC2Control | None:
    """
    Get SOC2 control mapping for a Checkov check ID.

    Args:
        check_id: Checkov check ID (e.g., "CKV_AWS_19")

    Returns:
        SOC2Control if mapping exists, None otherwise
    """
    return SOC2_MAPPING.get(check_id)


def get_soc2_summary(check_ids: list[str]) -> dict[str, dict[str, int]]:
    """
    Generate SOC2 control summary from a list of check IDs.

    Args:
        check_ids: List of failed Checkov check IDs

    Returns:
        Dictionary mapping control IDs to category and count
    """
    summary: dict[str, dict[str, int]] = {}

    for check_id in check_ids:
        control = get_soc2_mapping(check_id)
        if control:
            if control.control not in summary:
                summary[control.control] = {
                    "category": control.category,
                    "count": 0,
                }
            summary[control.control]["count"] += 1

    return summary
