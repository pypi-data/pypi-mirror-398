"""
Storage Scanner for RepliMap Phase 2.

Scans EBS Volumes and S3 Bucket Policies.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any, ClassVar

from botocore.exceptions import ClientError

from replimap.core.models import DependencyType, ResourceNode, ResourceType

from .base import BaseScanner, ScannerRegistry

if TYPE_CHECKING:
    from replimap.core import GraphEngine


logger = logging.getLogger(__name__)


@ScannerRegistry.register
class EBSScanner(BaseScanner):
    """
    Scans EBS Volumes.

    Only scans unattached volumes or volumes not already captured via EC2.
    Depends on EC2Scanner to establish instance-volume dependency edges.
    """

    resource_types: ClassVar[list[str]] = [
        "aws_ebs_volume",
    ]

    # EBS volumes reference EC2 instances for attachment dependencies
    depends_on_types: ClassVar[list[str]] = [
        "aws_instance",
    ]

    def scan(self, graph: GraphEngine) -> None:
        """Scan all EBS Volumes and add to graph."""
        logger.info(f"Scanning EBS Volumes in {self.region}...")

        try:
            ec2 = self.get_client("ec2")
            self._scan_volumes(ec2, graph)
        except ClientError as e:
            self._handle_aws_error(e, "EBS scanning")

    def _scan_volumes(self, ec2: Any, graph: GraphEngine) -> None:
        """Scan all EBS Volumes in the region."""
        logger.debug("Scanning EBS Volumes...")

        paginator = ec2.get_paginator("describe_volumes")
        for page in paginator.paginate():
            for volume in page.get("Volumes", []):
                vol_id = volume["VolumeId"]
                tags = self._extract_tags(volume.get("Tags"))

                # Get attachments
                attachments = []
                for att in volume.get("Attachments", []):
                    attachments.append(
                        {
                            "instance_id": att.get("InstanceId"),
                            "device": att.get("Device"),
                            "state": att.get("State"),
                            "delete_on_termination": att.get("DeleteOnTermination"),
                        }
                    )

                node = ResourceNode(
                    id=vol_id,
                    resource_type=ResourceType.EBS_VOLUME,
                    region=self.region,
                    config={
                        "availability_zone": volume.get("AvailabilityZone"),
                        "size": volume.get("Size"),
                        "volume_type": volume.get("VolumeType"),
                        "iops": volume.get("Iops"),
                        "throughput": volume.get("Throughput"),
                        "encrypted": volume.get("Encrypted"),
                        "kms_key_id": volume.get("KmsKeyId"),
                        "snapshot_id": volume.get("SnapshotId"),
                        "state": volume.get("State"),
                        "attachments": attachments,
                        "multi_attach_enabled": volume.get("MultiAttachEnabled"),
                    },
                    arn=f"arn:aws:ec2:{self.region}::volume/{vol_id}",
                    tags=tags,
                )

                graph.add_resource(node)

                # Add dependency on attached instances
                for att in attachments:
                    instance_id = att.get("instance_id")
                    if instance_id and graph.get_resource(instance_id):
                        graph.add_dependency(
                            vol_id, instance_id, DependencyType.BELONGS_TO
                        )

                logger.debug(
                    f"Added EBS Volume: {vol_id} ({volume.get('Size')}GB {volume.get('VolumeType')})"
                )


@ScannerRegistry.register
class S3PolicyScanner(BaseScanner):
    """
    Scans S3 Bucket Policies.

    Captures bucket policies separately for easier policy management.
    Depends on S3Scanner to discover buckets first.
    """

    resource_types: ClassVar[list[str]] = [
        "aws_s3_bucket_policy",
    ]

    # Must run after S3Scanner populates buckets in the graph
    depends_on_types: ClassVar[list[str]] = [
        "aws_s3_bucket",
    ]

    def scan(self, graph: GraphEngine) -> None:
        """Scan all S3 Bucket Policies and add to graph."""
        logger.info(f"Scanning S3 Bucket Policies in {self.region}...")

        try:
            s3 = self.get_client("s3")
            self._scan_bucket_policies(s3, graph)
        except ClientError as e:
            self._handle_aws_error(e, "S3 Policy scanning")

    def _scan_bucket_policies(self, s3: Any, graph: GraphEngine) -> None:
        """Scan policies for all S3 Buckets."""
        logger.debug("Scanning S3 Bucket Policies...")

        # Get all buckets that are in our graph
        bucket_resources = graph.get_resources_by_type(ResourceType.S3_BUCKET)

        for bucket_resource in bucket_resources:
            bucket_name = (
                bucket_resource.config.get("bucket_name") or bucket_resource.id
            )

            try:
                policy_resp = s3.get_bucket_policy(Bucket=bucket_name)
                policy_str = policy_resp.get("Policy", "{}")

                # Parse the policy JSON
                try:
                    policy = json.loads(policy_str)
                except json.JSONDecodeError:
                    policy = {}

                policy_id = f"{bucket_name}-policy"
                node = ResourceNode(
                    id=policy_id,
                    resource_type=ResourceType.S3_BUCKET_POLICY,
                    region=self.region,
                    config={
                        "bucket": bucket_name,
                        "policy": policy,
                        "policy_json": policy_str,
                    },
                    arn=f"arn:aws:s3:::{bucket_name}",
                    tags={},
                )

                graph.add_resource(node)

                # Add dependency on bucket
                graph.add_dependency(
                    policy_id, bucket_resource.id, DependencyType.BELONGS_TO
                )

                logger.debug(f"Added S3 Bucket Policy: {bucket_name}")

            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code", "")
                if error_code == "NoSuchBucketPolicy":
                    # Bucket has no policy, skip
                    continue
                elif error_code == "AccessDenied":
                    logger.warning(f"Access denied for bucket policy: {bucket_name}")
                    continue
                raise
