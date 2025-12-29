"""
RDS Scanner for RepliMap.

Scans RDS instances and DB subnet groups for replication.
Passwords and sensitive data are NOT captured.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, ClassVar

from botocore.exceptions import ClientError

from replimap.core.models import DependencyType, ResourceNode, ResourceType

from .base import BaseScanner, ScannerRegistry

if TYPE_CHECKING:
    from replimap.core import GraphEngine


logger = logging.getLogger(__name__)


@ScannerRegistry.register
class RDSScanner(BaseScanner):
    """
    Scans RDS instances and DB subnet groups.

    Captures:
    - DB instance identifier and configuration
    - Engine, engine version
    - Instance class (will be downsized by transformer)
    - Storage configuration
    - Network configuration (VPC, subnets, security groups)
    - Parameter groups (by reference)
    - Multi-AZ configuration

    Does NOT capture:
    - Master password
    - Snapshots
    - Performance Insights data
    """

    resource_types: ClassVar[list[str]] = [
        "aws_db_instance",
        "aws_db_subnet_group",
    ]

    # RDS resources reference subnets and security groups for dependency edges
    depends_on_types: ClassVar[list[str]] = [
        "aws_subnet",
        "aws_security_group",
    ]

    def scan(self, graph: GraphEngine) -> None:
        """Scan all RDS resources and add to graph."""
        logger.info(f"Scanning RDS resources in {self.region}...")

        try:
            rds = self.get_client("rds")

            # Scan in dependency order
            self._scan_db_subnet_groups(rds, graph)
            self._scan_db_instances(rds, graph)

        except ClientError as e:
            self._handle_aws_error(e, "RDS scanning")

    def _scan_db_subnet_groups(self, rds: Any, graph: GraphEngine) -> None:
        """Scan all DB subnet groups."""
        logger.debug("Scanning DB Subnet Groups...")

        paginator = rds.get_paginator("describe_db_subnet_groups")
        for page in paginator.paginate():
            for group in page.get("DBSubnetGroups", []):
                group_name = group["DBSubnetGroupName"]

                # Extract subnet IDs
                subnet_ids = [
                    subnet["SubnetIdentifier"] for subnet in group.get("Subnets", [])
                ]

                # Get the VPC ID from the first subnet if available
                vpc_id = group.get("VpcId")

                config = {
                    "name": group_name,
                    "description": group.get("DBSubnetGroupDescription", ""),
                    "subnet_ids": subnet_ids,
                    "vpc_id": vpc_id,
                }

                # Use a special tag format for resources without AWS tags
                tags = {"Name": group_name}

                node = ResourceNode(
                    id=group_name,
                    resource_type=ResourceType.DB_SUBNET_GROUP,
                    region=self.region,
                    config=config,
                    arn=group.get("DBSubnetGroupArn"),
                    tags=tags,
                )

                graph.add_resource(node)

                # Add dependencies to subnets
                for subnet_id in subnet_ids:
                    if graph.get_resource(subnet_id):
                        graph.add_dependency(
                            group_name, subnet_id, DependencyType.REFERENCES
                        )

                logger.debug(f"Added DB Subnet Group: {group_name}")

    def _scan_db_instances(self, rds: Any, graph: GraphEngine) -> None:
        """Scan all RDS DB instances."""
        logger.debug("Scanning RDS instances...")

        paginator = rds.get_paginator("describe_db_instances")
        for page in paginator.paginate():
            for instance in page.get("DBInstances", []):
                self._process_db_instance(instance, graph)

    def _process_db_instance(
        self, instance: dict[str, Any], graph: GraphEngine
    ) -> None:
        """
        Process a single RDS DB instance.

        Args:
            instance: AWS RDS instance data
            graph: Graph to add the resource to
        """
        db_id = instance["DBInstanceIdentifier"]
        status = instance.get("DBInstanceStatus", "unknown")

        # Skip instances that are being deleted
        if status in ("deleting", "deleted"):
            logger.debug(f"Skipping deleted instance: {db_id}")
            return

        # Extract security group IDs
        security_groups = [
            sg["VpcSecurityGroupId"] for sg in instance.get("VpcSecurityGroups", [])
        ]

        # Extract parameter groups
        parameter_groups = [
            {
                "name": pg["DBParameterGroupName"],
                "status": pg.get("ParameterApplyStatus", ""),
            }
            for pg in instance.get("DBParameterGroups", [])
        ]

        # Extract option groups
        option_groups = [
            og["OptionGroupName"] for og in instance.get("OptionGroupMemberships", [])
        ]

        config = {
            "identifier": db_id,
            "engine": instance["Engine"],
            "engine_version": instance.get("EngineVersion"),
            "instance_class": instance["DBInstanceClass"],
            "allocated_storage": instance.get("AllocatedStorage"),
            "storage_type": instance.get("StorageType", "gp2"),
            "storage_encrypted": instance.get("StorageEncrypted", False),
            "kms_key_id": instance.get("KmsKeyId"),
            "multi_az": instance.get("MultiAZ", False),
            "availability_zone": instance.get("AvailabilityZone"),
            "db_subnet_group_name": instance.get("DBSubnetGroup", {}).get(
                "DBSubnetGroupName"
            ),
            "vpc_security_group_ids": security_groups,
            "parameter_group_name": (
                parameter_groups[0]["name"] if parameter_groups else None
            ),
            "option_group_name": option_groups[0] if option_groups else None,
            "backup_retention_period": instance.get("BackupRetentionPeriod", 0),
            "backup_window": instance.get("PreferredBackupWindow"),
            "maintenance_window": instance.get("PreferredMaintenanceWindow"),
            "auto_minor_version_upgrade": instance.get("AutoMinorVersionUpgrade", True),
            "publicly_accessible": instance.get("PubliclyAccessible", False),
            "deletion_protection": instance.get("DeletionProtection", False),
            "db_name": instance.get("DBName"),
            "port": instance.get("DbInstancePort")
            or instance.get("Endpoint", {}).get("Port"),
            "master_username": instance.get("MasterUsername"),
            # Note: password is NOT captured
            "iam_database_authentication_enabled": instance.get(
                "IAMDatabaseAuthenticationEnabled", False
            ),
            "performance_insights_enabled": instance.get(
                "PerformanceInsightsEnabled", False
            ),
            "enabled_cloudwatch_logs_exports": instance.get(
                "EnabledCloudwatchLogsExports", []
            ),
            "status": status,
            "endpoint": instance.get("Endpoint", {}).get("Address"),
        }

        # Get tags
        tags = {tag["Key"]: tag["Value"] for tag in instance.get("TagList", [])}
        if "Name" not in tags:
            tags["Name"] = db_id

        node = ResourceNode(
            id=db_id,
            resource_type=ResourceType.RDS_INSTANCE,
            region=self.region,
            config=config,
            arn=instance.get("DBInstanceArn"),
            tags=tags,
        )

        graph.add_resource(node)

        # Add dependencies
        self._add_dependencies(node, config, graph)

        logger.debug(
            f"Added RDS instance: {db_id} ({instance['Engine']} "
            f"{instance['DBInstanceClass']})"
        )

    def _add_dependencies(
        self,
        node: ResourceNode,
        config: dict[str, Any],
        graph: GraphEngine,
    ) -> None:
        """
        Add dependency edges for an RDS instance.

        Dependencies:
        - RDS -> Security Groups (uses)
        - RDS -> DB Subnet Group (references)
        """
        db_id = node.id

        # Security group dependencies
        for sg_id in config.get("vpc_security_group_ids", []):
            if graph.get_resource(sg_id):
                graph.add_dependency(db_id, sg_id, DependencyType.USES)

        # DB Subnet Group dependency
        subnet_group = config.get("db_subnet_group_name")
        if subnet_group and graph.get_resource(subnet_group):
            graph.add_dependency(db_id, subnet_group, DependencyType.REFERENCES)
