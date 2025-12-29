"""
Environment detection and filtering for infrastructure graphs.

Detects environment from:
- Resource names (prod, staging, test, dev)
- Tags (Environment, Env, Stage)
- VPC names

Provides visual distinction via color-coded borders and filter controls.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass


@dataclass
class EnvironmentInfo:
    """Environment detection result."""

    name: str  # prod, stage, test, dev, unknown
    color: str  # Border color for visual distinction
    confidence: float  # 0.0 to 1.0


class EnvironmentDetector:
    """
    Detects and tags resources with their environment.

    Strategy:
    1. Check explicit Environment/Env tags (highest confidence)
    2. Check resource name patterns (medium confidence)
    3. Check VPC/parent resource names (lower confidence)
    4. Default to 'unknown' (no confidence)
    """

    # Environment patterns in priority order (first match wins)
    # More specific patterns come first
    PATTERNS: dict[str, list[str]] = {
        "prod": [
            r"\bprod\b",
            r"\bproduction\b",
            r"\bprd\b",
            r"\blive\b",
            r"-prod-",
            r"_prod_",
            r"-prod$",
            r"_prod$",
        ],
        "stage": [
            r"\bstage\b",
            r"\bstaging\b",
            r"\bstg\b",
            r"\buat\b",
            r"\bpreprod\b",
            r"\bpre-prod\b",
            r"-stage-",
            r"_stage_",
            r"-stage$",
            r"_stage$",
        ],
        "test": [
            r"\btest\b",
            r"\btesting\b",
            r"\btst\b",
            r"\bqa\b",
            r"-test-",
            r"_test_",
            r"-test$",
            r"_test$",
        ],
        "dev": [
            r"\bdev\b",
            r"\bdevelopment\b",
            r"\bsandbox\b",
            r"\bexperimental\b",
            r"-dev-",
            r"_dev_",
            r"-dev$",
            r"_dev$",
        ],
    }

    # Environment colors for visual distinction
    # These colors are used for node borders
    COLORS: dict[str, str] = {
        "prod": "#ef4444",  # Red - production is critical
        "stage": "#f59e0b",  # Amber - staging is important
        "test": "#22c55e",  # Green - testing is safe
        "dev": "#3b82f6",  # Blue - development is experimental
        "unknown": "#6b7280",  # Gray - unknown environment
    }

    # Background colors for container boxes (semi-transparent)
    BG_COLORS: dict[str, str] = {
        "prod": "rgba(239, 68, 68, 0.1)",
        "stage": "rgba(245, 158, 11, 0.1)",
        "test": "rgba(34, 197, 94, 0.1)",
        "dev": "rgba(59, 130, 246, 0.1)",
        "unknown": "rgba(107, 114, 128, 0.1)",
    }

    # Tag keys to check for environment (case-insensitive)
    ENVIRONMENT_TAG_KEYS: list[str] = [
        "Environment",
        "Env",
        "Stage",
        "environment",
        "env",
        "stage",
        "ENVIRONMENT",
        "ENV",
    ]

    def detect(self, node: dict[str, Any]) -> EnvironmentInfo:
        """
        Detect environment for a single node.

        Checks in order of confidence:
        1. Environment tag (confidence: 1.0)
        2. Resource name patterns (confidence: 0.8)
        3. ID patterns (confidence: 0.6)

        Args:
            node: Node dictionary with properties

        Returns:
            EnvironmentInfo with detected environment
        """
        # Check tags first (highest confidence)
        env = self._detect_from_tags(node)
        if env:
            return EnvironmentInfo(
                name=env,
                color=self.COLORS[env],
                confidence=1.0,
            )

        # Check resource name
        name = node.get("name", "") or ""
        env = self._match_environment(name)
        if env:
            return EnvironmentInfo(
                name=env,
                color=self.COLORS[env],
                confidence=0.8,
            )

        # Check resource ID
        resource_id = node.get("id", "") or ""
        env = self._match_environment(resource_id)
        if env:
            return EnvironmentInfo(
                name=env,
                color=self.COLORS[env],
                confidence=0.6,
            )

        # Check VPC name if available in properties
        vpc_name = node.get("properties", {}).get("vpc_name", "")
        if vpc_name:
            env = self._match_environment(vpc_name)
            if env:
                return EnvironmentInfo(
                    name=env,
                    color=self.COLORS[env],
                    confidence=0.5,
                )

        return EnvironmentInfo(
            name="unknown",
            color=self.COLORS["unknown"],
            confidence=0.0,
        )

    def _detect_from_tags(self, node: dict[str, Any]) -> str | None:
        """Detect environment from resource tags."""
        tags = node.get("properties", {}).get("tags", {})
        if not isinstance(tags, dict):
            return None

        for tag_key in self.ENVIRONMENT_TAG_KEYS:
            if tag_key in tags:
                tag_value = str(tags[tag_key])
                env = self._match_environment(tag_value)
                if env:
                    return env

        return None

    def _match_environment(self, text: str) -> str | None:
        """Match text against environment patterns."""
        if not text:
            return None

        text_lower = text.lower()

        for env, patterns in self.PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return env

        return None

    def enrich_nodes(self, nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Add environment metadata to all nodes.

        Modifies nodes in place and returns them.

        Args:
            nodes: List of node dictionaries

        Returns:
            Same list with environment data added
        """
        for node in nodes:
            env_info = self.detect(node)
            node["environment"] = env_info.name
            node["env_color"] = env_info.color
            node["env_confidence"] = env_info.confidence

        return nodes

    def get_environments(self, nodes: list[dict[str, Any]]) -> dict[str, int]:
        """
        Get all unique environments and their counts.

        Args:
            nodes: List of node dictionaries (should have environment field)

        Returns:
            Dict of environment name to count
        """
        counts: dict[str, int] = {}
        for node in nodes:
            env = node.get("environment", "unknown")
            counts[env] = counts.get(env, 0) + 1
        return counts

    def propagate_vpc_environment(
        self,
        nodes: list[dict[str, Any]],
        links: list[dict[str, Any]],
    ) -> None:
        """
        Propagate VPC environment to resources without clear environment.

        If a resource has unknown environment but belongs to a VPC
        with known environment, inherit the VPC environment.

        Args:
            nodes: List of node dictionaries
            links: List of link dictionaries
        """
        # Build VPC environment map
        vpc_envs: dict[str, str] = {}
        for node in nodes:
            if node.get("type") == "aws_vpc":
                env = node.get("environment", "unknown")
                if env != "unknown":
                    vpc_envs[node["id"]] = env

        # Build resource to VPC mapping
        resource_vpc: dict[str, str] = {}
        for node in nodes:
            vpc_id = node.get("properties", {}).get("vpc_id")
            if vpc_id:
                resource_vpc[node["id"]] = vpc_id

        # Propagate environment
        for node in nodes:
            if node.get("environment") == "unknown":
                vpc_id = resource_vpc.get(node["id"])
                if vpc_id and vpc_id in vpc_envs:
                    node["environment"] = vpc_envs[vpc_id]
                    node["env_color"] = self.COLORS[vpc_envs[vpc_id]]
                    node["env_confidence"] = 0.4  # Inherited from VPC


def generate_environment_filter_html() -> str:
    """Generate HTML for environment filter buttons."""
    return """
    <div class="env-filter">
        <span class="env-label">Environment</span>
        <button class="env-btn active" data-env="all">All</button>
        <button class="env-btn" data-env="prod">
            <span class="env-dot" style="background: #ef4444"></span>
            Prod
        </button>
        <button class="env-btn" data-env="stage">
            <span class="env-dot" style="background: #f59e0b"></span>
            Stage
        </button>
        <button class="env-btn" data-env="test">
            <span class="env-dot" style="background: #22c55e"></span>
            Test
        </button>
        <button class="env-btn" data-env="dev">
            <span class="env-dot" style="background: #3b82f6"></span>
            Dev
        </button>
    </div>
    """


def generate_environment_filter_js() -> str:
    """Generate JavaScript for environment filtering."""
    return """
    // Environment filter state
    let activeEnvironment = 'all';

    document.querySelectorAll('.env-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.env-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            activeEnvironment = this.dataset.env;
            filterByEnvironment();
        });
    });

    function filterByEnvironment() {
        node.style('display', d => {
            if (activeEnvironment === 'all') return null;
            return d.environment === activeEnvironment ? null : 'none';
        });

        link.style('display', l => {
            if (activeEnvironment === 'all') return null;
            const sourceEnv = getNodeEnv(l.source);
            const targetEnv = getNodeEnv(l.target);
            return (sourceEnv === activeEnvironment || targetEnv === activeEnvironment) ? null : 'none';
        });

        // Also filter container boxes if in hierarchical mode
        if (typeof filterContainersByEnvironment === 'function') {
            filterContainersByEnvironment();
        }
    }

    function getNodeEnv(nodeOrId) {
        const id = typeof nodeOrId === 'object' ? nodeOrId.id : nodeOrId;
        const node = graphData.nodes.find(n => n.id === id);
        return node?.environment || 'unknown';
    }
    """


def generate_environment_styles() -> str:
    """Generate CSS for environment visual distinction."""
    return """
    /* Environment filter */
    .env-filter {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 6px;
        margin-bottom: 12px;
        padding-bottom: 12px;
        border-bottom: 1px solid #334155;
    }

    .env-label {
        font-size: 11px;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        width: 100%;
        margin-bottom: 4px;
    }

    .env-btn {
        padding: 4px 8px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 500;
        border: 1px solid #475569;
        background: #1e293b;
        color: #94a3b8;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 4px;
    }

    .env-btn:hover {
        background: #334155;
        color: #f1f5f9;
    }

    .env-btn.active {
        background: #6366f1;
        border-color: #6366f1;
        color: white;
    }

    .env-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
    }

    /* Node environment border */
    .node circle {
        stroke-width: 3px;
    }

    .node[data-env="prod"] circle {
        stroke: #ef4444 !important;
    }

    .node[data-env="stage"] circle {
        stroke: #f59e0b !important;
    }

    .node[data-env="test"] circle {
        stroke: #22c55e !important;
    }

    .node[data-env="dev"] circle {
        stroke: #3b82f6 !important;
    }

    .node[data-env="unknown"] circle {
        stroke: #6b7280 !important;
    }

    /* Environment badge in details panel */
    .env-badge {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
    }

    .env-badge.prod {
        background: rgba(239, 68, 68, 0.2);
        color: #fca5a5;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }

    .env-badge.stage {
        background: rgba(245, 158, 11, 0.2);
        color: #fcd34d;
        border: 1px solid rgba(245, 158, 11, 0.3);
    }

    .env-badge.test {
        background: rgba(34, 197, 94, 0.2);
        color: #86efac;
        border: 1px solid rgba(34, 197, 94, 0.3);
    }

    .env-badge.dev {
        background: rgba(59, 130, 246, 0.2);
        color: #93c5fd;
        border: 1px solid rgba(59, 130, 246, 0.3);
    }

    .env-badge.unknown {
        background: rgba(107, 114, 128, 0.2);
        color: #d1d5db;
        border: 1px solid rgba(107, 114, 128, 0.3);
    }
    """
