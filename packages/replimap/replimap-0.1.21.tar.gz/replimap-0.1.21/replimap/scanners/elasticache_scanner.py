"""
ElastiCache Scanner for RepliMap Phase 2.

Scans ElastiCache Clusters and Subnet Groups.
These resources provide in-memory caching with Redis/Memcached.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, ClassVar

from botocore.exceptions import ClientError

from replimap.core.models import DependencyType, ResourceNode, ResourceType

from .base import BaseScanner, ScannerRegistry

if TYPE_CHECKING:
    from replimap.core import GraphEngine


logger = logging.getLogger(__name__)


@ScannerRegistry.register
class ElastiCacheScanner(BaseScanner):
    """
    Scans ElastiCache resources.

    Dependency chain:
        Subnet <- ElastiCache Subnet Group
        ElastiCache Subnet Group <- ElastiCache Cluster
        Security Group <- ElastiCache Cluster
    """

    resource_types: ClassVar[list[str]] = [
        "aws_elasticache_cluster",
        "aws_elasticache_subnet_group",
    ]

    # ElastiCache resources reference subnets and security groups for dependency edges
    depends_on_types: ClassVar[list[str]] = [
        "aws_subnet",
        "aws_security_group",
    ]

    def scan(self, graph: GraphEngine) -> None:
        """Scan all ElastiCache resources and add to graph."""
        logger.info(f"Scanning ElastiCache resources in {self.region}...")

        try:
            elasticache = self.get_client("elasticache")

            # Scan in dependency order
            self._scan_subnet_groups(elasticache, graph)
            self._scan_clusters(elasticache, graph)

        except ClientError as e:
            self._handle_aws_error(e, "ElastiCache scanning")

    def _scan_subnet_groups(self, elasticache: object, graph: GraphEngine) -> None:
        """Scan all ElastiCache Subnet Groups in the region."""
        logger.debug("Scanning ElastiCache Subnet Groups...")

        paginator = elasticache.get_paginator("describe_cache_subnet_groups")
        for page in paginator.paginate():
            for sg in page.get("CacheSubnetGroups", []):
                sg_name = sg["CacheSubnetGroupName"]
                vpc_id = sg.get("VpcId")

                # Extract subnet IDs
                subnet_ids = [
                    subnet["SubnetIdentifier"] for subnet in sg.get("Subnets", [])
                ]

                node = ResourceNode(
                    id=sg_name,
                    resource_type=ResourceType.ELASTICACHE_SUBNET_GROUP,
                    region=self.region,
                    config={
                        "name": sg_name,
                        "description": sg.get("CacheSubnetGroupDescription"),
                        "vpc_id": vpc_id,
                        "subnet_ids": subnet_ids,
                        "subnets": [
                            {
                                "subnet_identifier": subnet["SubnetIdentifier"],
                                "availability_zone": subnet.get(
                                    "SubnetAvailabilityZone", {}
                                ).get("Name"),
                            }
                            for subnet in sg.get("Subnets", [])
                        ],
                    },
                    arn=sg.get("ARN"),
                    tags={},  # Subnet groups need separate tag lookup
                )

                graph.add_resource(node)

                # Establish dependencies
                for subnet_id in subnet_ids:
                    if graph.get_resource(subnet_id):
                        graph.add_dependency(
                            sg_name, subnet_id, DependencyType.BELONGS_TO
                        )

                logger.debug(f"Added ElastiCache Subnet Group: {sg_name}")

    def _scan_clusters(self, elasticache: object, graph: GraphEngine) -> None:
        """Scan all ElastiCache Clusters in the region."""
        logger.debug("Scanning ElastiCache Clusters...")

        paginator = elasticache.get_paginator("describe_cache_clusters")
        for page in paginator.paginate(ShowCacheNodeInfo=True):
            for cluster in page.get("CacheClusters", []):
                cluster_id = cluster["CacheClusterId"]

                # Get security group IDs
                sg_ids = [
                    sg["SecurityGroupId"] for sg in cluster.get("SecurityGroups", [])
                ]

                # Get cache nodes info
                cache_nodes = []
                for node in cluster.get("CacheNodes", []):
                    cache_nodes.append(
                        {
                            "cache_node_id": node.get("CacheNodeId"),
                            "status": node.get("CacheNodeStatus"),
                            "endpoint": node.get("Endpoint"),
                        }
                    )

                node = ResourceNode(
                    id=cluster_id,
                    resource_type=ResourceType.ELASTICACHE_CLUSTER,
                    region=self.region,
                    config={
                        "cluster_id": cluster_id,
                        "engine": cluster.get("Engine"),
                        "engine_version": cluster.get("EngineVersion"),
                        "node_type": cluster.get("CacheNodeType"),
                        "num_cache_nodes": cluster.get("NumCacheNodes"),
                        "cache_subnet_group_name": cluster.get("CacheSubnetGroupName"),
                        "security_group_ids": sg_ids,
                        "parameter_group_name": cluster.get(
                            "CacheParameterGroup", {}
                        ).get("CacheParameterGroupName"),
                        "availability_zone": cluster.get("PreferredAvailabilityZone"),
                        "port": cluster.get("ConfigurationEndpoint", {}).get("Port")
                        or (
                            cache_nodes[0].get("endpoint", {}).get("Port")
                            if cache_nodes
                            else None
                        ),
                        "cache_nodes": cache_nodes,
                        "snapshot_retention_limit": cluster.get(
                            "SnapshotRetentionLimit"
                        ),
                        "snapshot_window": cluster.get("SnapshotWindow"),
                        "maintenance_window": cluster.get("PreferredMaintenanceWindow"),
                        "auto_minor_version_upgrade": cluster.get(
                            "AutoMinorVersionUpgrade"
                        ),
                    },
                    arn=cluster.get("ARN"),
                    tags={},  # Would need separate tag lookup
                )

                graph.add_resource(node)

                # Establish dependencies
                subnet_group = cluster.get("CacheSubnetGroupName")
                if subnet_group and graph.get_resource(subnet_group):
                    graph.add_dependency(cluster_id, subnet_group, DependencyType.USES)

                for sg_id in sg_ids:
                    if graph.get_resource(sg_id):
                        graph.add_dependency(cluster_id, sg_id, DependencyType.USES)

                logger.debug(
                    f"Added ElastiCache Cluster: {cluster_id} ({cluster.get('Engine')})"
                )


@ScannerRegistry.register
class DBParameterGroupScanner(BaseScanner):
    """
    Scans RDS DB Parameter Groups.

    These define database engine configuration.
    """

    resource_types: ClassVar[list[str]] = [
        "aws_db_parameter_group",
    ]

    def scan(self, graph: GraphEngine) -> None:
        """Scan all DB Parameter Groups and add to graph."""
        logger.info(f"Scanning DB Parameter Groups in {self.region}...")

        try:
            rds = self.get_client("rds")
            self._scan_parameter_groups(rds, graph)
        except ClientError as e:
            self._handle_aws_error(e, "DB Parameter Group scanning")

    def _scan_parameter_groups(self, rds: object, graph: GraphEngine) -> None:
        """Scan all DB Parameter Groups in the region."""
        logger.debug("Scanning DB Parameter Groups...")

        paginator = rds.get_paginator("describe_db_parameter_groups")
        for page in paginator.paginate():
            for pg in page.get("DBParameterGroups", []):
                pg_name = pg["DBParameterGroupName"]

                # Skip default parameter groups
                if pg_name.startswith("default."):
                    continue

                # Get parameters (limited to modified ones for performance)
                params = []
                try:
                    param_paginator = rds.get_paginator("describe_db_parameters")
                    for param_page in param_paginator.paginate(
                        DBParameterGroupName=pg_name,
                        Source="user",  # Only user-modified parameters
                    ):
                        for param in param_page.get("Parameters", []):
                            params.append(
                                {
                                    "name": param.get("ParameterName"),
                                    "value": param.get("ParameterValue"),
                                    "apply_type": param.get("ApplyType"),
                                    "is_modifiable": param.get("IsModifiable"),
                                }
                            )
                except ClientError:
                    pass  # Some parameter groups may not allow listing

                node = ResourceNode(
                    id=pg_name,
                    resource_type=ResourceType.DB_PARAMETER_GROUP,
                    region=self.region,
                    config={
                        "name": pg_name,
                        "family": pg.get("DBParameterGroupFamily"),
                        "description": pg.get("Description"),
                        "parameters": params,
                    },
                    arn=pg.get("DBParameterGroupArn"),
                    tags={},
                )

                graph.add_resource(node)
                logger.debug(f"Added DB Parameter Group: {pg_name}")
