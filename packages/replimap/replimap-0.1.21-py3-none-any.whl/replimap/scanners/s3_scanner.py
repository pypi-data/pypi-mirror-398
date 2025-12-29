"""
S3 Scanner for RepliMap.

Scans S3 bucket configurations (not contents) for replication.
S3 buckets are globally unique, so renaming requires adding suffixes.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, ClassVar

from botocore.exceptions import ClientError

from replimap.core.models import ResourceNode, ResourceType

from .base import BaseScanner, ScannerRegistry, parallel_process_items

if TYPE_CHECKING:
    from replimap.core import GraphEngine


logger = logging.getLogger(__name__)


@ScannerRegistry.register
class S3Scanner(BaseScanner):
    """
    Scans S3 bucket configurations.

    Captures:
    - Bucket name and region
    - Versioning configuration
    - Encryption configuration
    - Public access block settings
    - Lifecycle rules (simplified)

    Does NOT capture:
    - Bucket contents/objects
    - Bucket policies (sensitive)
    - CORS configuration
    """

    resource_types: ClassVar[list[str]] = ["aws_s3_bucket"]

    def scan(self, graph: GraphEngine) -> None:
        """Scan all S3 buckets and add to graph."""
        logger.info("Scanning S3 buckets...")

        try:
            s3 = self.get_client("s3")
            self._scan_buckets(s3, graph)

        except ClientError as e:
            self._handle_aws_error(e, "S3 scanning")

    def _scan_buckets(self, s3: Any, graph: GraphEngine) -> None:
        """Scan all S3 buckets with parallel processing."""
        logger.debug("Listing S3 buckets...")

        try:
            response = s3.list_buckets()
        except ClientError as e:
            self._handle_aws_error(e, "list S3 buckets")
            return

        # First pass: identify buckets in target region
        buckets_to_process: list[str] = []
        for bucket in response.get("Buckets", []):
            bucket_name = bucket["Name"]

            # Get bucket region
            try:
                location = s3.get_bucket_location(Bucket=bucket_name)
                bucket_region = location.get("LocationConstraint") or "us-east-1"
            except ClientError as e:
                logger.warning(f"Could not get region for bucket {bucket_name}: {e}")
                continue

            # Only process buckets in the target region
            if bucket_region != self.region:
                logger.debug(f"Skipping bucket {bucket_name} (region: {bucket_region})")
                continue

            buckets_to_process.append(bucket_name)

        if not buckets_to_process:
            logger.debug("No S3 buckets found in target region")
            return

        logger.debug(f"Processing {len(buckets_to_process)} S3 buckets in parallel...")

        # Process buckets in parallel
        def process_bucket(bucket_name: str) -> ResourceNode | None:
            return self._process_bucket(s3, bucket_name, self.region, graph)

        results, failures = parallel_process_items(
            buckets_to_process,
            process_bucket,
            description="S3 bucket",
        )

        logger.debug(
            f"S3 scanning complete: {len(results)} buckets processed, "
            f"{len(failures)} failed"
        )

    def _process_bucket(
        self,
        s3: Any,
        bucket_name: str,
        bucket_region: str,
        graph: GraphEngine,
    ) -> ResourceNode | None:
        """
        Process a single S3 bucket.

        Args:
            s3: S3 client
            bucket_name: Name of the bucket
            bucket_region: Region of the bucket
            graph: Graph to add the resource to

        Returns:
            ResourceNode if successful, None otherwise
        """
        config: dict[str, Any] = {
            "bucket": bucket_name,
        }

        # Get versioning
        try:
            versioning = s3.get_bucket_versioning(Bucket=bucket_name)
            config["versioning"] = {
                "enabled": versioning.get("Status") == "Enabled",
                "mfa_delete": versioning.get("MFADelete") == "Enabled",
            }
        except ClientError as e:
            logger.debug(f"Could not get versioning for {bucket_name}: {e}")
            config["versioning"] = {"enabled": False, "mfa_delete": False}

        # Get encryption
        try:
            encryption = s3.get_bucket_encryption(Bucket=bucket_name)
            rules = encryption.get("ServerSideEncryptionConfiguration", {}).get(
                "Rules", []
            )
            if rules:
                rule = rules[0].get("ApplyServerSideEncryptionByDefault", {})
                config["server_side_encryption_configuration"] = {
                    "sse_algorithm": rule.get("SSEAlgorithm", "AES256"),
                    "kms_master_key_id": rule.get("KMSMasterKeyID"),
                }
        except ClientError as e:
            if "ServerSideEncryptionConfigurationNotFoundError" not in str(e):
                logger.debug(f"Could not get encryption for {bucket_name}: {e}")

        # Get public access block
        try:
            public_access = s3.get_public_access_block(Bucket=bucket_name)
            pab = public_access.get("PublicAccessBlockConfiguration", {})
            config["public_access_block"] = {
                "block_public_acls": pab.get("BlockPublicAcls", False),
                "block_public_policy": pab.get("BlockPublicPolicy", False),
                "ignore_public_acls": pab.get("IgnorePublicAcls", False),
                "restrict_public_buckets": pab.get("RestrictPublicBuckets", False),
            }
        except ClientError as e:
            if "NoSuchPublicAccessBlockConfiguration" not in str(e):
                logger.debug(
                    f"Could not get public access block for {bucket_name}: {e}"
                )

        # Get lifecycle rules (simplified)
        try:
            lifecycle = s3.get_bucket_lifecycle_configuration(Bucket=bucket_name)
            rules = lifecycle.get("Rules", [])
            config["lifecycle_rules"] = [
                self._simplify_lifecycle_rule(rule) for rule in rules
            ]
        except ClientError as e:
            if "NoSuchLifecycleConfiguration" not in str(e):
                logger.debug(f"Could not get lifecycle for {bucket_name}: {e}")

        # Get bucket tags
        tags = {}
        try:
            tagging = s3.get_bucket_tagging(Bucket=bucket_name)
            tags = {tag["Key"]: tag["Value"] for tag in tagging.get("TagSet", [])}
        except ClientError as e:
            if "NoSuchTagSet" not in str(e):
                logger.debug(f"Could not get tags for {bucket_name}: {e}")

        node = ResourceNode(
            id=bucket_name,
            resource_type=ResourceType.S3_BUCKET,
            region=bucket_region,
            config=config,
            arn=f"arn:aws:s3:::{bucket_name}",
            tags=tags,
        )

        graph.add_resource(node)
        logger.debug(f"Added S3 bucket: {bucket_name}")
        return node

    def _simplify_lifecycle_rule(self, rule: dict[str, Any]) -> dict[str, Any]:
        """
        Simplify a lifecycle rule for Terraform generation.

        Args:
            rule: AWS lifecycle rule

        Returns:
            Simplified rule dictionary
        """
        simplified = {
            "id": rule.get("ID", ""),
            "status": rule.get("Status", "Disabled"),
        }

        # Filter (prefix)
        filter_config = rule.get("Filter", {})
        if "Prefix" in filter_config:
            simplified["prefix"] = filter_config["Prefix"]
        elif "Prefix" in rule:  # Legacy format
            simplified["prefix"] = rule["Prefix"]

        # Expiration
        if "Expiration" in rule:
            exp = rule["Expiration"]
            simplified["expiration"] = {
                "days": exp.get("Days"),
                "expired_object_delete_marker": exp.get(
                    "ExpiredObjectDeleteMarker", False
                ),
            }

        # Transitions
        if "Transitions" in rule:
            simplified["transitions"] = [
                {
                    "days": t.get("Days"),
                    "storage_class": t.get("StorageClass"),
                }
                for t in rule["Transitions"]
            ]

        # Noncurrent version expiration
        if "NoncurrentVersionExpiration" in rule:
            simplified["noncurrent_version_expiration"] = {
                "noncurrent_days": rule["NoncurrentVersionExpiration"].get(
                    "NoncurrentDays"
                ),
            }

        return simplified
