"""
Graph Engine for RepliMap.

The GraphEngine is the core data structure that maintains the dependency
graph of AWS resources. It wraps networkx.DiGraph and provides domain-specific
methods for resource management and traversal.

Thread Safety:
    GraphEngine uses a threading.RLock to protect all mutations.
    This allows safe concurrent access from multiple scanner threads.

Phantom Nodes:
    When a resource references another resource that wasn't scanned
    (e.g., due to permission errors or filter exclusion), a "phantom"
    placeholder node is created to maintain graph integrity. This prevents
    crashes in visualization and analysis while making the partial scan
    results visible to users.
"""

from __future__ import annotations

import json
import logging
import re
import threading
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import networkx as nx

from .models import DependencyType, ResourceNode, ResourceType
from .sanitizer import sanitize_resource_config

logger = logging.getLogger(__name__)


class RepliMapJSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder that handles types from AWS/Boto3 responses.

    Handles:
    - datetime objects (from Boto3 timestamps like CreateTime, LaunchTime)
    - set/frozenset (from some Boto3 responses)
    - bytes (from binary data fields)

    This ensures graph.save() never crashes on unexpected types.
    """

    def default(self, obj: Any) -> Any:
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, (set, frozenset)):
            return list(obj)
        if isinstance(obj, bytes):
            return "[BINARY DATA]"
        return super().default(obj)


@dataclass
class SCCResult:
    """
    Result of Strongly Connected Components analysis.

    Attributes:
        components: List of SCCs, each is a set of node IDs
        node_to_scc: Map from node ID to its SCC index
        has_cycles: True if any SCC has size > 1 (actual cycles)
        cycle_groups: Only SCCs with size > 1 (the actual cycles)
    """

    components: list[set[str]]
    node_to_scc: dict[str, int]
    has_cycles: bool
    cycle_groups: list[set[str]]


class TarjanSCC:
    """
    Tarjan's algorithm for finding Strongly Connected Components.

    Time complexity: O(V + E) where V = nodes, E = edges

    After running this:
    1. Each SCC is a set of nodes that can all reach each other
    2. SCCs with size > 1 indicate circular dependencies
    3. The resulting DAG of SCCs can be topologically sorted

    Example use case:
        AWS Security Groups often have mutual references:
        - SG-A allows traffic from SG-B
        - SG-B allows traffic from SG-A
        This creates a cycle that Tarjan's algorithm detects.
    """

    def __init__(self, graph: GraphEngine) -> None:
        """
        Initialize Tarjan's algorithm.

        Args:
            graph: The GraphEngine to analyze
        """
        self.graph = graph
        self.index_counter = 0
        self.stack: list[str] = []
        self.on_stack: set[str] = set()
        self.index: dict[str, int] = {}
        self.lowlink: dict[str, int] = {}
        self.sccs: list[set[str]] = []

    def find_sccs(self) -> SCCResult:
        """
        Find all strongly connected components.

        Returns:
            SCCResult with all analysis data
        """
        # Run Tarjan's algorithm from each unvisited node
        for node_id in self.graph._graph.nodes():
            if node_id not in self.index:
                self._strongconnect(node_id)

        # Build result
        node_to_scc: dict[str, int] = {}
        for i, scc in enumerate(self.sccs):
            for node_id in scc:
                node_to_scc[node_id] = i

        cycle_groups = [scc for scc in self.sccs if len(scc) > 1]

        return SCCResult(
            components=self.sccs,
            node_to_scc=node_to_scc,
            has_cycles=len(cycle_groups) > 0,
            cycle_groups=cycle_groups,
        )

    def _strongconnect(self, node_id: str) -> None:
        """
        Recursive Tarjan algorithm for a single node.

        Args:
            node_id: The node to process
        """
        # Set the depth index for this node
        self.index[node_id] = self.index_counter
        self.lowlink[node_id] = self.index_counter
        self.index_counter += 1
        self.stack.append(node_id)
        self.on_stack.add(node_id)

        # Visit all successors (nodes we depend on)
        for successor in self.graph._graph.successors(node_id):
            if successor not in self.index:
                # Successor has not been visited yet, recurse
                self._strongconnect(successor)
                self.lowlink[node_id] = min(
                    self.lowlink[node_id], self.lowlink[successor]
                )
            elif successor in self.on_stack:
                # Successor is on the stack -> part of current SCC
                self.lowlink[node_id] = min(
                    self.lowlink[node_id], self.index[successor]
                )

        # If node is the root of an SCC, pop the stack
        if self.lowlink[node_id] == self.index[node_id]:
            scc: set[str] = set()
            while True:
                w = self.stack.pop()
                self.on_stack.remove(w)
                scc.add(w)
                if w == node_id:
                    break
            self.sccs.append(scc)


# Patterns for inferring resource type from AWS ID prefix
_AWS_ID_PATTERNS: dict[str, ResourceType] = {
    r"^vpc-": ResourceType.VPC,
    r"^subnet-": ResourceType.SUBNET,
    r"^sg-": ResourceType.SECURITY_GROUP,
    r"^i-": ResourceType.EC2_INSTANCE,
    r"^rtb-": ResourceType.ROUTE_TABLE,
    r"^igw-": ResourceType.INTERNET_GATEWAY,
    r"^nat-": ResourceType.NAT_GATEWAY,
    r"^vpce-": ResourceType.VPC_ENDPOINT,
    r"^lt-": ResourceType.LAUNCH_TEMPLATE,
    r"^asg-": ResourceType.AUTOSCALING_GROUP,
    r"^arn:aws:elasticloadbalancing:": ResourceType.LB,
    r"^arn:aws:rds:": ResourceType.RDS_INSTANCE,
    r"^arn:aws:s3:::": ResourceType.S3_BUCKET,
}


class GraphEngine:
    """
    Manages the dependency graph of AWS resources.

    Resources are stored as nodes in a directed graph, with edges representing
    dependencies. The direction of edges indicates "depends on" relationship:
    if A -> B, then A depends on B (B must exist before A).

    This enables:
    - Topological sorting for correct Terraform ordering
    - Dependency analysis for impact assessment
    - Resource grouping by type for organized output

    Phantom Nodes:
    When add_dependency is called with a non-existent source or target,
    a phantom node is automatically created to maintain graph integrity.
    This allows partial scans to produce usable graphs even when some
    resources couldn't be discovered.
    """

    def __init__(self, create_phantom_nodes: bool = True) -> None:
        """
        Initialize an empty graph.

        Args:
            create_phantom_nodes: If True, automatically create phantom nodes
                for missing dependencies instead of raising errors.
        """
        self._graph: nx.DiGraph = nx.DiGraph()
        self._resources: dict[str, ResourceNode] = {}
        self._lock: threading.RLock = threading.RLock()
        self._phantom_nodes: set[str] = set()
        self._create_phantom_nodes = create_phantom_nodes

    @property
    def node_count(self) -> int:
        """Number of resources in the graph."""
        return self._graph.number_of_nodes()

    @property
    def edge_count(self) -> int:
        """Number of dependencies in the graph."""
        return self._graph.number_of_edges()

    def add_resource(self, node: ResourceNode) -> None:
        """
        Add a resource node to the graph.

        If a resource with the same ID already exists, it will be updated.
        Thread-safe: uses internal lock for concurrent access.

        Security: Config is sanitized BEFORE storage to prevent sensitive
        data (passwords, API keys, UserData) from being persisted to cache.

        Args:
            node: The ResourceNode to add
        """
        # SECURITY: Sanitize config BEFORE locking and storage
        # This runs outside the lock to minimize contention (regex is expensive)
        if node.config:
            sanitized_config = sanitize_resource_config(node.config)
            # Update config in-place (dict is mutable)
            node.config.clear()
            node.config.update(sanitized_config)

        with self._lock:
            self._resources[node.id] = node
            self._graph.add_node(
                node.id,
                resource_type=str(node.resource_type),
                terraform_name=node.terraform_name,
            )
        logger.debug(f"Added resource: {node.id} ({node.resource_type})")

    def add_dependency(
        self,
        source_id: str,
        target_id: str,
        relation_type: DependencyType = DependencyType.BELONGS_TO,
    ) -> None:
        """
        Add a dependency edge between two resources.

        The direction is: source depends on target.
        In Terraform terms, source must reference target.
        Thread-safe: uses internal lock for concurrent access.

        If create_phantom_nodes is True (default), missing resources will
        automatically be created as phantom nodes to maintain graph integrity.

        Args:
            source_id: ID of the dependent resource
            target_id: ID of the resource being depended on
            relation_type: Type of dependency relationship

        Raises:
            ValueError: If either resource doesn't exist and create_phantom_nodes is False
        """
        with self._lock:
            # Handle missing source
            if source_id not in self._resources:
                if self._create_phantom_nodes:
                    self._create_phantom_node(source_id)
                else:
                    raise ValueError(f"Source resource not found: {source_id}")

            # Handle missing target
            if target_id not in self._resources:
                if self._create_phantom_nodes:
                    self._create_phantom_node(target_id)
                else:
                    raise ValueError(f"Target resource not found: {target_id}")

            self._graph.add_edge(source_id, target_id, relation=str(relation_type))
            self._resources[source_id].add_dependency(target_id)
        logger.debug(
            f"Added dependency: {source_id} --[{relation_type}]--> {target_id}"
        )

    def _create_phantom_node(self, node_id: str) -> None:
        """
        Create a phantom placeholder node for a missing resource.

        This is called internally when add_dependency references a
        resource that doesn't exist in the graph.

        Args:
            node_id: The ID of the missing resource
        """
        # Infer resource type from ID pattern
        resource_type = self._infer_type_from_id(node_id)

        phantom = ResourceNode(
            id=node_id,
            resource_type=resource_type,
            region="unknown",
            config={},
            tags={},
            terraform_name=f"phantom_{node_id.replace('-', '_')}",
            original_name=f"[Missing] {node_id}",
            is_phantom=True,
            phantom_reason="Referenced by other resources but not discovered during scan",
        )

        self._resources[node_id] = phantom
        self._graph.add_node(
            node_id,
            resource_type=str(resource_type),
            terraform_name=phantom.terraform_name,
            is_phantom=True,
        )
        self._phantom_nodes.add(node_id)

        logger.warning(
            f"Created phantom node for missing resource: {node_id} (type: {resource_type})"
        )

    def _infer_type_from_id(self, node_id: str) -> ResourceType:
        """
        Infer resource type from AWS ID prefix pattern.

        Args:
            node_id: AWS resource ID or ARN

        Returns:
            Best-guess ResourceType, or VPC as fallback
        """
        for pattern, resource_type in _AWS_ID_PATTERNS.items():
            if re.match(pattern, node_id):
                return resource_type
        # Default to VPC as a reasonable fallback for unknown types
        return ResourceType.VPC

    @property
    def phantom_count(self) -> int:
        """Number of phantom (placeholder) nodes in the graph."""
        return len(self._phantom_nodes)

    def get_phantom_nodes(self) -> list[ResourceNode]:
        """Get all phantom nodes in the graph."""
        return [self._resources[pid] for pid in self._phantom_nodes]

    def is_phantom(self, resource_id: str) -> bool:
        """Check if a resource is a phantom node."""
        return resource_id in self._phantom_nodes

    def get_resource(self, resource_id: str) -> ResourceNode | None:
        """
        Get a resource by its ID.

        Thread-safe: uses internal lock for concurrent access.

        Args:
            resource_id: The AWS resource ID

        Returns:
            The ResourceNode if found, None otherwise
        """
        with self._lock:
            return self._resources.get(resource_id)

    def get_all_resources(self) -> list[ResourceNode]:
        """Get all resources in the graph. Thread-safe."""
        with self._lock:
            return list(self._resources.values())

    def get_resources_by_type(self, resource_type: ResourceType) -> list[ResourceNode]:
        """
        Get all resources of a specific type.

        Thread-safe: uses internal lock for concurrent access.

        Args:
            resource_type: The type of resources to retrieve

        Returns:
            List of ResourceNodes matching the type
        """
        with self._lock:
            return [
                node
                for node in self._resources.values()
                if node.resource_type == resource_type
            ]

    def get_dependencies(self, resource_id: str) -> list[ResourceNode]:
        """
        Get all resources that this resource depends on.

        Args:
            resource_id: The resource to check dependencies for

        Returns:
            List of ResourceNodes that this resource depends on
        """
        if resource_id not in self._graph:
            return []

        dep_ids = list(self._graph.successors(resource_id))
        return [self._resources[rid] for rid in dep_ids if rid in self._resources]

    def get_dependents(self, resource_id: str) -> list[ResourceNode]:
        """
        Get all resources that depend on this resource.

        Args:
            resource_id: The resource to check dependents for

        Returns:
            List of ResourceNodes that depend on this resource
        """
        if resource_id not in self._graph:
            return []

        dep_ids = list(self._graph.predecessors(resource_id))
        return [self._resources[rid] for rid in dep_ids if rid in self._resources]

    def topological_sort(self) -> list[ResourceNode]:
        """
        Return resources in dependency order.

        Resources that have no dependencies come first (e.g., VPCs),
        followed by resources that depend on them (e.g., Subnets, then EC2).

        Returns:
            List of ResourceNodes in dependency order

        Raises:
            ValueError: If the graph contains cycles
        """
        try:
            # Reverse because we want dependencies first
            sorted_ids = list(reversed(list(nx.topological_sort(self._graph))))
            return [self._resources[rid] for rid in sorted_ids]
        except nx.NetworkXUnfeasible as e:
            raise ValueError("Dependency graph contains cycles") from e

    def has_cycles(self) -> bool:
        """Check if the graph contains any cycles."""
        try:
            list(nx.topological_sort(self._graph))
            return False
        except nx.NetworkXUnfeasible:
            return True

    def find_cycles(self) -> list[list[str]]:
        """Find and return all cycles in the graph."""
        try:
            return list(nx.simple_cycles(self._graph))
        except nx.NetworkXNoCycle:
            return []

    def find_strongly_connected_components(self) -> SCCResult:
        """
        Find all strongly connected components using Tarjan's algorithm.

        This is useful for:
        - Detecting circular dependencies (SCCs with size > 1)
        - Safe topological sorting (collapse SCCs into super-nodes)
        - Dependency analysis for blast radius

        AWS Security Groups frequently have mutual references (SG-A allows SG-B,
        SG-B allows SG-A), which creates cycles. This method detects them.

        Returns:
            SCCResult with components, cycle groups, and node mapping
        """
        tarjan = TarjanSCC(self)
        return tarjan.find_sccs()

    def get_safe_dependency_order(self) -> list[ResourceNode]:
        """
        Get topologically sorted node order, handling cycles safely.

        Unlike topological_sort(), this method:
        1. Detects strongly connected components (cycles)
        2. Collapses cycles into "super-nodes" for ordering
        3. Returns nodes in a valid dependency order
        4. Nodes within a cycle are returned in arbitrary order

        This never raises an exception for cyclic graphs.

        Returns:
            List of ResourceNodes in safe dependency order
        """
        scc_result = self.find_strongly_connected_components()

        if scc_result.has_cycles:
            logger.warning(
                f"Found {len(scc_result.cycle_groups)} circular dependency groups. "
                f"Resources in cycles: {sum(len(g) for g in scc_result.cycle_groups)}"
            )

        # Build condensation graph (DAG of SCCs)
        # Each SCC becomes a single node
        condensed = nx.DiGraph()
        for i, _scc in enumerate(scc_result.components):
            condensed.add_node(i)

        # Add edges between SCCs
        for source, target in self._graph.edges():
            source_scc = scc_result.node_to_scc.get(source)
            target_scc = scc_result.node_to_scc.get(target)
            if source_scc is not None and target_scc is not None:
                if source_scc != target_scc:
                    condensed.add_edge(source_scc, target_scc)

        # Topologically sort the condensed graph (guaranteed to work, it's a DAG)
        scc_order = list(reversed(list(nx.topological_sort(condensed))))

        # Flatten back to node order
        result = []
        for scc_idx in scc_order:
            for node_id in scc_result.components[scc_idx]:
                if node_id in self._resources:
                    result.append(self._resources[node_id])

        return result

    def remove_resource(self, resource_id: str) -> bool:
        """
        Remove a resource and all its edges from the graph.

        Args:
            resource_id: The resource to remove

        Returns:
            True if resource was removed, False if it didn't exist
        """
        if resource_id not in self._resources:
            return False

        self._graph.remove_node(resource_id)
        del self._resources[resource_id]
        logger.debug(f"Removed resource: {resource_id}")
        return True

    def get_subgraph(self, resource_ids: list[str]) -> GraphEngine:
        """
        Create a new GraphEngine containing only the specified resources.

        Useful for isolating a subset of resources for targeted operations.

        Args:
            resource_ids: List of resource IDs to include

        Returns:
            New GraphEngine with only the specified resources
        """
        subgraph = GraphEngine()
        for rid in resource_ids:
            if rid in self._resources:
                subgraph.add_resource(self._resources[rid])

        # Add edges that exist between included resources
        for source, target, data in self._graph.edges(data=True):
            if source in resource_ids and target in resource_ids:
                relation = DependencyType(data.get("relation", "belongs_to"))
                subgraph.add_dependency(source, target, relation)

        return subgraph

    def iter_resources(self) -> Iterator[ResourceNode]:
        """Iterate over all resources."""
        yield from self._resources.values()

    def statistics(self) -> dict[str, Any]:
        """
        Get statistics about the graph.

        Returns:
            Dictionary with node count, edge count, type breakdown, and phantom info
        """
        type_counts: dict[str, int] = {}
        for node in self._resources.values():
            type_name = str(node.resource_type)
            type_counts[type_name] = type_counts.get(type_name, 0) + 1

        return {
            "total_resources": self.node_count,
            "total_dependencies": self.edge_count,
            "resources_by_type": type_counts,
            "has_cycles": self.has_cycles(),
            "phantom_count": self.phantom_count,
            "phantom_nodes": list(self._phantom_nodes),
        }

    def merge(self, other: GraphEngine) -> None:
        """
        Merge another graph into this one.

        Used for Map-Reduce pattern where each scanner produces
        an isolated subgraph that is later merged into the final graph.
        This allows lock-free concurrent scanning.

        Merge rules:
        - Real nodes take precedence over phantom nodes
        - Edges are combined additively
        - Metadata is accumulated

        Args:
            other: Another GraphEngine to merge into this one
        """
        with self._lock:
            # Merge nodes
            for node_id, node in other._resources.items():
                if node_id not in self._resources:
                    # New node, add it
                    self.add_resource(node)
                    if node.is_phantom:
                        self._phantom_nodes.add(node_id)
                else:
                    # Existing node - real node wins over phantom
                    existing = self._resources[node_id]
                    if existing.is_phantom and not node.is_phantom:
                        # Replace phantom with real node
                        self._resources[node_id] = node
                        self._graph.nodes[node_id]["resource_type"] = str(
                            node.resource_type
                        )
                        self._graph.nodes[node_id]["terraform_name"] = (
                            node.terraform_name
                        )
                        self._graph.nodes[node_id]["is_phantom"] = False
                        self._phantom_nodes.discard(node_id)
                        logger.debug(
                            f"Replaced phantom node {node_id} with real resource"
                        )

            # Merge edges
            for source, target, data in other._graph.edges(data=True):
                if not self._graph.has_edge(source, target):
                    relation = data.get("relation", str(DependencyType.BELONGS_TO))
                    # Note: We don't call add_dependency here to avoid
                    # re-creating phantom nodes that might have been replaced
                    self._graph.add_edge(source, target, relation=relation)
                    if source in self._resources:
                        self._resources[source].add_dependency(target)

    def to_dict(self) -> dict[str, Any]:
        """
        Export the graph to a serializable dictionary.

        Returns:
            Dictionary representation of the graph
        """
        nodes = [node.to_dict() for node in self._resources.values()]

        edges = []
        for source, target, data in self._graph.edges(data=True):
            edges.append(
                {
                    "source": source,
                    "target": target,
                    "relation": data.get("relation", "belongs_to"),
                }
            )

        return {
            "version": "1.0",
            "nodes": nodes,
            "edges": edges,
            "statistics": self.statistics(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GraphEngine:
        """
        Create a GraphEngine from a dictionary.

        Args:
            data: Dictionary with 'nodes' and 'edges' keys

        Returns:
            Reconstructed GraphEngine
        """
        engine = cls()

        # Add all nodes first
        for node_data in data.get("nodes", []):
            node = ResourceNode.from_dict(node_data)
            engine.add_resource(node)

        # Then add edges
        for edge_data in data.get("edges", []):
            relation = DependencyType(edge_data.get("relation", "belongs_to"))
            try:
                engine.add_dependency(
                    edge_data["source"],
                    edge_data["target"],
                    relation,
                )
            except ValueError as e:
                logger.warning(f"Skipping invalid edge: {e}")

        return engine

    def save(self, path: Path) -> None:
        """
        Save the graph to a JSON file.

        Uses RepliMapJSONEncoder to handle datetime, set, and bytes types
        that may appear in Boto3 responses.

        Args:
            path: Path to save the JSON file
        """
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2, cls=RepliMapJSONEncoder)
        logger.info(f"Graph saved to {path}")

    @classmethod
    def load(cls, path: Path) -> GraphEngine:
        """
        Load a graph from a JSON file.

        Args:
            path: Path to the JSON file

        Returns:
            Loaded GraphEngine
        """
        with open(path) as f:
            data = json.load(f)
        logger.info(f"Graph loaded from {path}")
        return cls.from_dict(data)

    def __repr__(self) -> str:
        return f"GraphEngine(nodes={self.node_count}, edges={self.edge_count})"

    def __len__(self) -> int:
        return self.node_count
