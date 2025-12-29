"""
Terraform Variable Naming Utilities.

Provides standardized naming for Terraform variables to ensure
consistency between Generator and Right-Sizer.

Naming Pattern: {resource_type}_{resource_name}_{attribute}
Example: aws_instance_web_server_instance_type

The Seven Laws of Sovereign Code:
3. Simplicity is the Ultimate Sophistication - If you can derive it, don't store it.
"""

from __future__ import annotations

import re


def sanitize_name(name: str) -> str:
    """
    Sanitize a name for use in Terraform variable names.

    Args:
        name: Raw name (may contain special characters)

    Returns:
        Sanitized name (lowercase, underscores only)

    Examples:
        >>> sanitize_name("web-server")
        'web_server'
        >>> sanitize_name("main.db")
        'main_db'
        >>> sanitize_name("MyResource-123")
        'myresource_123'
    """
    # Replace non-alphanumeric (except underscore) with underscore
    clean_name = re.sub(r"[^a-zA-Z0-9_]", "_", name)

    # Collapse multiple underscores
    clean_name = re.sub(r"_+", "_", clean_name)

    # Lowercase and strip leading/trailing underscores
    return clean_name.lower().strip("_")


def get_variable_name(resource_type: str, resource_name: str, attribute: str) -> str:
    """
    Generate standardized Terraform variable name.

    Uses fully qualified naming for collision prevention:
    {resource_type}_{resource_name}_{attribute}

    Args:
        resource_type: AWS resource type (e.g., "aws_instance", "aws_db_instance")
        resource_name: Resource name/identifier (e.g., "web_server", "main_db")
        attribute: Attribute name (e.g., "instance_type", "instance_class")

    Returns:
        Sanitized variable name (lowercase, underscores only)

    Examples:
        >>> get_variable_name("aws_instance", "web-server", "instance_type")
        'aws_instance_web_server_instance_type'

        >>> get_variable_name("aws_db_instance", "main.db", "instance_class")
        'aws_db_instance_main_db_instance_class'
    """
    # Combine parts
    raw_name = f"{resource_type}_{resource_name}_{attribute}"

    return sanitize_name(raw_name)


def get_variable_name_for_resource(
    resource_type: str,
    resource_name: str,
) -> dict[str, str]:
    """
    Get all relevant variable names for a resource type.

    Returns a dict mapping attribute names to variable names.

    Args:
        resource_type: AWS resource type
        resource_name: Resource name/identifier

    Returns:
        Dict of {attribute: variable_name}

    Example:
        >>> get_variable_name_for_resource("aws_db_instance", "main")
        {
            'instance_class': 'aws_db_instance_main_instance_class',
            'storage_type': 'aws_db_instance_main_storage_type',
            'multi_az': 'aws_db_instance_main_multi_az',
            'allocated_storage': 'aws_db_instance_main_allocated_storage'
        }
    """
    # Define attributes per resource type
    RESOURCE_ATTRIBUTES: dict[str, list[str]] = {
        "aws_instance": [
            "instance_type",
        ],
        "aws_db_instance": [
            "instance_class",
            "storage_type",
            "allocated_storage",
            "multi_az",
        ],
        "aws_elasticache_cluster": [
            "node_type",
            "num_cache_nodes",
        ],
        "aws_elasticache_replication_group": [
            "node_type",
            "num_cache_clusters",
        ],
        "aws_launch_template": [
            "instance_type",
        ],
    }

    attributes = RESOURCE_ATTRIBUTES.get(resource_type, ["instance_type"])

    return {
        attr: get_variable_name(resource_type, resource_name, attr)
        for attr in attributes
    }


# Mapping of resource types to their primary "size" attribute
INSTANCE_SIZE_ATTRIBUTE: dict[str, str] = {
    "aws_instance": "instance_type",
    "aws_db_instance": "instance_class",
    "aws_elasticache_cluster": "node_type",
    "aws_elasticache_replication_group": "node_type",
    "aws_elasticsearch_domain": "instance_type",
    "aws_opensearch_domain": "instance_type",
    "aws_launch_template": "instance_type",
}

# Mapping of Terraform resource types to their description prefix
RESOURCE_DESCRIPTIONS: dict[str, str] = {
    "aws_instance": "EC2 instance",
    "aws_db_instance": "RDS instance",
    "aws_elasticache_cluster": "ElastiCache cluster",
    "aws_elasticache_replication_group": "ElastiCache replication group",
    "aws_launch_template": "Launch Template",
}


def get_size_variable_name(resource_type: str, resource_name: str) -> str:
    """
    Get the variable name for the primary "size" attribute of a resource.

    This is the most commonly overridden attribute for Right-Sizer.

    Args:
        resource_type: AWS resource type
        resource_name: Resource name/identifier

    Returns:
        Variable name for the size attribute

    Example:
        >>> get_size_variable_name("aws_instance", "web")
        'aws_instance_web_instance_type'

        >>> get_size_variable_name("aws_db_instance", "main")
        'aws_db_instance_main_instance_class'
    """
    attribute = INSTANCE_SIZE_ATTRIBUTE.get(resource_type, "instance_type")
    return get_variable_name(resource_type, resource_name, attribute)


def get_size_attribute(resource_type: str) -> str:
    """
    Get the size attribute name for a resource type.

    Args:
        resource_type: AWS resource type

    Returns:
        Attribute name (e.g., "instance_type", "instance_class", "node_type")

    Example:
        >>> get_size_attribute("aws_instance")
        'instance_type'
        >>> get_size_attribute("aws_db_instance")
        'instance_class'
        >>> get_size_attribute("aws_elasticache_cluster")
        'node_type'
    """
    return INSTANCE_SIZE_ATTRIBUTE.get(resource_type, "instance_type")


def get_resource_description(resource_type: str) -> str:
    """
    Get human-readable description for a resource type.

    Args:
        resource_type: AWS resource type

    Returns:
        Human-readable description

    Example:
        >>> get_resource_description("aws_instance")
        'EC2 instance'
        >>> get_resource_description("aws_db_instance")
        'RDS instance'
    """
    return RESOURCE_DESCRIPTIONS.get(resource_type, resource_type)
