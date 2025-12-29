"""
Data models for RepliMap.

ResourceNode is the atomic unit of the graph engine - every AWS resource
becomes a node with its configuration, dependencies, and metadata.

Memory Optimization:
- Uses @dataclass(slots=True) for ~40% memory reduction per instance
- Uses sys.intern() for repeated strings (type, region, vpc_id)
- For 10k+ resources, this saves significant memory

Note: slots=True requires Python 3.10+ (which is our minimum version)
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# Intern common strings to save memory across many ResourceNodes
def _intern_str(value: str | None) -> str | None:
    """Intern a string value if not None."""
    return sys.intern(value) if value else None


class GenerationMode(str, Enum):
    """Mode for Terraform code generation."""

    CLONE = "clone"  # Transform, downsize, abstract variables (default)
    AUDIT = "audit"  # Raw, faithful, no transformations (forensic snapshot)

    def __str__(self) -> str:
        return self.value


class ResourceType(str, Enum):
    """Supported AWS resource types."""

    # Phase 1 (MVP) - Core resources
    VPC = "aws_vpc"
    SUBNET = "aws_subnet"
    SECURITY_GROUP = "aws_security_group"
    EC2_INSTANCE = "aws_instance"
    S3_BUCKET = "aws_s3_bucket"
    RDS_INSTANCE = "aws_db_instance"
    DB_SUBNET_GROUP = "aws_db_subnet_group"

    # Phase 2 - Networking
    ROUTE_TABLE = "aws_route_table"
    ROUTE = "aws_route"
    INTERNET_GATEWAY = "aws_internet_gateway"
    NAT_GATEWAY = "aws_nat_gateway"
    VPC_ENDPOINT = "aws_vpc_endpoint"
    NETWORK_ACL = "aws_network_acl"

    # Phase 2 - Compute
    LAUNCH_TEMPLATE = "aws_launch_template"
    AUTOSCALING_GROUP = "aws_autoscaling_group"
    LB = "aws_lb"
    LB_LISTENER = "aws_lb_listener"
    LB_TARGET_GROUP = "aws_lb_target_group"

    # Phase 2 - Database
    DB_PARAMETER_GROUP = "aws_db_parameter_group"
    ELASTICACHE_CLUSTER = "aws_elasticache_cluster"
    ELASTICACHE_SUBNET_GROUP = "aws_elasticache_subnet_group"

    # Phase 2 - Storage
    S3_BUCKET_POLICY = "aws_s3_bucket_policy"
    EBS_VOLUME = "aws_ebs_volume"

    # Phase 2 - Messaging
    SQS_QUEUE = "aws_sqs_queue"
    SNS_TOPIC = "aws_sns_topic"

    def __str__(self) -> str:
        return self.value


class DependencyType(str, Enum):
    """Types of relationships between resources."""

    BELONGS_TO = "belongs_to"  # e.g., Subnet belongs to VPC
    USES = "uses"  # e.g., EC2 uses Security Group
    REFERENCES = "references"  # e.g., RDS references DB Subnet Group

    def __str__(self) -> str:
        return self.value


@dataclass(slots=True)
class ResourceNode:
    """
    Represents an AWS resource in the dependency graph.

    This is the atomic unit of RepliMap's graph engine. Each AWS resource
    is converted to a ResourceNode containing its configuration and metadata.

    Memory Optimization:
    - Uses slots=True for ~40% memory reduction
    - Interns repeated strings (region) on __post_init__

    Attributes:
        id: Unique identifier (typically AWS resource ID, e.g., 'vpc-12345')
        resource_type: The Terraform resource type (e.g., 'aws_vpc')
        arn: Full AWS ARN if available
        region: AWS region where the resource exists
        config: Raw configuration dictionary from AWS API
        tags: Resource tags as key-value pairs
        dependencies: List of resource IDs this resource depends on
        terraform_name: Sanitized name for Terraform resource block
        original_name: Original Name tag value for reference
        is_phantom: True if this is a placeholder for a missing resource
        phantom_reason: Explanation for why this is a phantom node
    """

    id: str
    resource_type: ResourceType
    region: str
    config: dict[str, Any] = field(default_factory=dict)
    arn: str | None = None
    tags: dict[str, str] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)
    terraform_name: str | None = None
    original_name: str | None = None
    is_phantom: bool = False
    phantom_reason: str | None = None

    def __post_init__(self) -> None:
        """Generate terraform_name from tags if not provided, and intern strings."""
        # Intern the region string to save memory across many nodes
        # (e.g., "us-east-1" repeated 5000 times)
        object.__setattr__(self, "region", _intern_str(self.region))

        if self.terraform_name is None:
            object.__setattr__(self, "terraform_name", self._generate_terraform_name())
        if self.original_name is None:
            object.__setattr__(self, "original_name", self.tags.get("Name", self.id))

    def _generate_terraform_name(self) -> str:
        """
        Generate a valid Terraform resource name.

        Terraform names must:
        - Start with a letter or underscore
        - Contain only letters, digits, underscores, and hyphens
        """
        name = self.tags.get("Name", self.id)

        # Replace invalid characters with underscores
        sanitized = ""
        for char in name:
            if char.isalnum() or char in "_-":
                sanitized += char
            else:
                sanitized += "_"

        # Ensure it starts with a letter or underscore
        if sanitized and not (sanitized[0].isalpha() or sanitized[0] == "_"):
            sanitized = f"r_{sanitized}"

        # Handle empty case
        if not sanitized:
            sanitized = f"resource_{self.id.replace('-', '_')}"

        return sanitized

    def __hash__(self) -> int:
        """Enable use as graph node and in sets."""
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        """Equality based on resource ID."""
        if not isinstance(other, ResourceNode):
            return NotImplemented
        return self.id == other.id

    def add_dependency(self, resource_id: str) -> None:
        """Add a dependency to this resource."""
        if resource_id not in self.dependencies:
            self.dependencies.append(resource_id)

    def get_tag(self, key: str, default: str | None = None) -> str | None:
        """Get a tag value by key."""
        return self.tags.get(key, default)

    def to_dict(self) -> dict[str, Any]:
        """Convert to a serializable dictionary."""
        result = {
            "id": self.id,
            "resource_type": str(self.resource_type),
            "arn": self.arn,
            "region": self.region,
            "config": self.config,
            "tags": self.tags,
            "dependencies": self.dependencies,
            "terraform_name": self.terraform_name,
            "original_name": self.original_name,
        }
        # Only include phantom fields if this is a phantom node
        if self.is_phantom:
            result["is_phantom"] = True
            result["phantom_reason"] = self.phantom_reason
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ResourceNode:
        """Create a ResourceNode from a dictionary."""
        return cls(
            id=data["id"],
            resource_type=ResourceType(data["resource_type"]),
            arn=data.get("arn"),
            region=data["region"],
            config=data.get("config", {}),
            tags=data.get("tags", {}),
            dependencies=data.get("dependencies", []),
            terraform_name=data.get("terraform_name"),
            original_name=data.get("original_name"),
            is_phantom=data.get("is_phantom", False),
            phantom_reason=data.get("phantom_reason"),
        )

    def __repr__(self) -> str:
        return f"ResourceNode(id='{self.id}', type={self.resource_type}, name='{self.original_name}')"
