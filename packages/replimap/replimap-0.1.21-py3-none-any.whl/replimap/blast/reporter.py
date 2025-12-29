"""
Blast radius report formatting.

Generates console output, JSON, and HTML reports for blast radius analysis.
"""

from __future__ import annotations

import json
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from replimap.blast.models import BlastRadiusResult, ImpactLevel

console = Console()


class BlastRadiusReporter:
    """Generate blast radius reports in various formats."""

    def to_console(self, result: BlastRadiusResult) -> None:
        """Print blast radius to console."""
        # Header
        impact_color = self._get_impact_color(result.overall_impact)

        console.print("\n[bold]Blast Radius Analysis[/bold]\n")

        # Summary panel
        summary = f"""
[bold]Center Resource:[/bold] {result.center_resource.id}
[bold]Type:[/bold] {result.center_resource.type}
[bold]Name:[/bold] {result.center_resource.name}

[{impact_color}]Overall Impact: {result.overall_impact.value} ({result.overall_score}/100)[/{impact_color}]
[bold]Total Affected:[/bold] {result.total_affected} resources
[bold]Max Depth:[/bold] {result.max_depth} levels
"""
        console.print(
            Panel(summary.strip(), title="Summary", border_style=impact_color)
        )

        # Warnings
        if result.warnings:
            console.print("\n[bold yellow]Warnings:[/bold yellow]")
            for warning in result.warnings:
                console.print(f"  [yellow]![/yellow] {warning}")

        # Impact zones
        console.print("\n[bold]Impact Zones:[/bold]\n")

        for zone in result.zones:
            if zone.depth == 0:
                zone_label = "[red]Blast Center[/red]"
            else:
                zone_label = f"Depth {zone.depth}"

            console.print(
                f"[bold]{zone_label}[/bold] ({len(zone.resources)} resources, "
                f"score: {zone.total_impact_score})"
            )

            for resource in zone.resources[:10]:  # Limit display
                color = self._get_impact_color(resource.impact_level)
                console.print(
                    f"  [{color}]{resource.impact_level.value:8}[/{color}] "
                    f"{resource.type}: {resource.id}"
                )

            if len(zone.resources) > 10:
                console.print(f"  [dim]... and {len(zone.resources) - 10} more[/dim]")

            console.print()

        # Safe deletion order
        if result.safe_deletion_order:
            console.print("[bold]Safe Deletion Order:[/bold]\n")
            for i, resource_id in enumerate(result.safe_deletion_order[:15], 1):
                console.print(f"  {i:2}. {resource_id}")

            if len(result.safe_deletion_order) > 15:
                remaining = len(result.safe_deletion_order) - 15
                console.print(f"  [dim]... and {remaining} more[/dim]")

    def to_tree(self, result: BlastRadiusResult) -> None:
        """Print blast radius as a tree."""
        center = result.center_resource
        tree = Tree(f"[bold red]{center.type}[/bold red]: {center.id} ({center.name})")

        self._build_tree(tree, center.id, result, visited=set())

        console.print("\n[bold]Dependency Tree:[/bold]\n")
        console.print(tree)

    def _build_tree(
        self,
        parent: Tree,
        resource_id: str,
        result: BlastRadiusResult,
        visited: set[str],
    ) -> None:
        """Recursively build tree."""
        if resource_id in visited:
            return
        visited.add(resource_id)

        # Find dependents (resources that depend on this one)
        for resource in result.affected_resources:
            if resource_id in resource.depends_on:
                color = self._get_impact_color(resource.impact_level)
                label = f"[{color}]{resource.type}[/{color}]: {resource.id}"
                branch = parent.add(label)
                self._build_tree(branch, resource.id, result, visited)

    def to_json(self, result: BlastRadiusResult, output_path: Path) -> Path:
        """Export to JSON."""
        data = result.to_dict()
        output_path.write_text(json.dumps(data, indent=2))
        console.print(f"[green]Exported to {output_path}[/green]")
        return output_path

    def to_html(self, result: BlastRadiusResult, output_path: Path) -> Path:
        """Export to HTML with D3.js visualization."""
        html = self._generate_html(result)
        output_path.write_text(html)
        console.print(f"[green]Exported to {output_path}[/green]")
        return output_path

    def to_table(self, result: BlastRadiusResult) -> None:
        """Print affected resources as a table."""
        table = Table(title="Affected Resources")
        table.add_column("Depth", justify="center")
        table.add_column("Resource ID", style="cyan")
        table.add_column("Type")
        table.add_column("Name")
        table.add_column("Impact", justify="center")
        table.add_column("Score", justify="right")

        for resource in sorted(result.affected_resources, key=lambda r: r.depth):
            color = self._get_impact_color(resource.impact_level)
            table.add_row(
                str(resource.depth),
                resource.id[:40] + ("..." if len(resource.id) > 40 else ""),
                resource.type,
                resource.name[:30] + ("..." if len(resource.name) > 30 else ""),
                f"[{color}]{resource.impact_level.value}[/{color}]",
                str(resource.impact_score),
            )

        console.print(table)

    def _get_impact_color(self, level: ImpactLevel) -> str:
        """Get color for impact level."""
        colors = {
            ImpactLevel.CRITICAL: "red bold",
            ImpactLevel.HIGH: "red",
            ImpactLevel.MEDIUM: "yellow",
            ImpactLevel.LOW: "blue",
            ImpactLevel.NONE: "dim",
        }
        return colors.get(level, "white")

    def _generate_html(self, result: BlastRadiusResult) -> str:
        """Generate HTML report with D3.js visualization."""
        # Prepare nodes for D3.js
        nodes_js = []
        for resource in result.affected_resources:
            color = {
                ImpactLevel.CRITICAL: "#e74c3c",
                ImpactLevel.HIGH: "#e67e22",
                ImpactLevel.MEDIUM: "#f1c40f",
                ImpactLevel.LOW: "#3498db",
                ImpactLevel.NONE: "#95a5a6",
            }.get(resource.impact_level, "#95a5a6")

            size = 10 + (resource.impact_score / 10)

            nodes_js.append(
                {
                    "id": resource.id,
                    "type": resource.type,
                    "name": resource.name,
                    "impact": resource.impact_level.value,
                    "score": resource.impact_score,
                    "depth": resource.depth,
                    "color": color,
                    "size": size,
                    "isCenter": resource.depth == 0,
                }
            )

        # Prepare edges for D3.js
        edges_js = []
        affected_ids = {r.id for r in result.affected_resources}
        for resource in result.affected_resources:
            for dep_id in resource.depends_on:
                if dep_id in affected_ids:
                    edges_js.append(
                        {
                            "source": resource.id,
                            "target": dep_id,
                        }
                    )

        # Generate warnings HTML
        warnings_html = ""
        if result.warnings:
            warnings_html = "\n".join(
                f'<div class="warning">{w}</div>' for w in result.warnings
            )

        # Generate zone summary
        zones_html = ""
        for zone in result.zones:
            zone_class = "zone-center" if zone.depth == 0 else ""
            zones_html += f"""
            <div class="zone {zone_class}">
                <strong>Depth {zone.depth}</strong>: {len(zone.resources)} resources
                (Score: {zone.total_impact_score})
            </div>
            """

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Blast Radius: {result.center_resource.id}</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        * {{
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            background: #1a1a2e;
            color: #eee;
        }}
        #header {{
            background: linear-gradient(135deg, #16213e 0%, #1a1a2e 100%);
            padding: 20px 30px;
            border-bottom: 1px solid #333;
        }}
        #header h1 {{
            margin: 0 0 10px 0;
            font-size: 24px;
        }}
        #header .subtitle {{
            color: #888;
            font-size: 14px;
        }}
        .stats {{
            display: flex;
            gap: 30px;
            margin-top: 15px;
        }}
        .stat {{
            text-align: center;
        }}
        .stat-value {{
            font-size: 28px;
            font-weight: bold;
        }}
        .stat-label {{
            font-size: 12px;
            color: #888;
            text-transform: uppercase;
        }}
        .stat-critical {{ color: #e74c3c; }}
        .stat-high {{ color: #e67e22; }}
        .stat-medium {{ color: #f1c40f; }}
        .warning {{
            background: #44350a;
            border-left: 4px solid #f1c40f;
            color: #f1c40f;
            padding: 10px 15px;
            margin: 5px 30px;
            font-size: 14px;
        }}
        .zones {{
            padding: 15px 30px;
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }}
        .zone {{
            background: #222;
            padding: 10px 15px;
            border-radius: 5px;
            font-size: 13px;
        }}
        .zone-center {{
            border: 2px solid #e74c3c;
        }}
        #graph {{
            width: 100%;
            height: calc(100vh - 250px);
            min-height: 400px;
        }}
        .tooltip {{
            position: absolute;
            background: #333;
            border: 1px solid #555;
            padding: 10px;
            border-radius: 5px;
            font-size: 12px;
            pointer-events: none;
            z-index: 100;
        }}
        .node text {{
            font-size: 10px;
            fill: #ccc;
        }}
        .link {{
            stroke: #555;
            stroke-opacity: 0.6;
        }}
        .node-center circle {{
            stroke: #fff;
            stroke-width: 3px;
        }}
        #deletion-order {{
            padding: 20px 30px;
            background: #16213e;
        }}
        #deletion-order h3 {{
            margin: 0 0 10px 0;
            font-size: 16px;
        }}
        #deletion-order ol {{
            margin: 0;
            padding-left: 20px;
            columns: 2;
        }}
        #deletion-order li {{
            font-size: 13px;
            color: #aaa;
            margin-bottom: 5px;
        }}
    </style>
</head>
<body>
    <div id="header">
        <h1>Blast Radius Analysis</h1>
        <div class="subtitle">
            <strong>{result.center_resource.type}</strong>: {result.center_resource.id}
            ({result.center_resource.name})
        </div>
        <div class="stats">
            <div class="stat">
                <div class="stat-value stat-{result.overall_impact.value.lower()}">{result.overall_impact.value}</div>
                <div class="stat-label">Impact Level</div>
            </div>
            <div class="stat">
                <div class="stat-value">{result.total_affected}</div>
                <div class="stat-label">Affected Resources</div>
            </div>
            <div class="stat">
                <div class="stat-value">{result.max_depth}</div>
                <div class="stat-label">Max Depth</div>
            </div>
            <div class="stat">
                <div class="stat-value">{result.overall_score}/100</div>
                <div class="stat-label">Impact Score</div>
            </div>
        </div>
    </div>
    {warnings_html}
    <div class="zones">{zones_html}</div>
    <div id="graph"></div>
    <div id="deletion-order">
        <h3>Safe Deletion Order</h3>
        <ol>
            {"".join(f"<li>{rid}</li>" for rid in result.safe_deletion_order[:20])}
            {f"<li>... and {len(result.safe_deletion_order) - 20} more</li>" if len(result.safe_deletion_order) > 20 else ""}
        </ol>
    </div>

    <div class="tooltip" style="display: none;"></div>

    <script>
        const nodes = {json.dumps(nodes_js)};
        const links = {json.dumps(edges_js)};

        const width = window.innerWidth;
        const height = Math.max(400, window.innerHeight - 300);

        const svg = d3.select("#graph")
            .append("svg")
            .attr("width", "100%")
            .attr("height", height)
            .attr("viewBox", [0, 0, width, height]);

        // Add arrow marker for edges
        svg.append("defs").append("marker")
            .attr("id", "arrow")
            .attr("viewBox", "0 -5 10 10")
            .attr("refX", 20)
            .attr("refY", 0)
            .attr("markerWidth", 6)
            .attr("markerHeight", 6)
            .attr("orient", "auto")
            .append("path")
            .attr("d", "M0,-5L10,0L0,5")
            .attr("fill", "#555");

        const simulation = d3.forceSimulation(nodes)
            .force("link", d3.forceLink(links).id(d => d.id).distance(120))
            .force("charge", d3.forceManyBody().strength(-300))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collision", d3.forceCollide().radius(d => d.size + 10));

        const link = svg.append("g")
            .selectAll("line")
            .data(links)
            .join("line")
            .attr("class", "link")
            .attr("marker-end", "url(#arrow)");

        const node = svg.append("g")
            .selectAll("g")
            .data(nodes)
            .join("g")
            .attr("class", d => d.isCenter ? "node node-center" : "node")
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));

        node.append("circle")
            .attr("r", d => d.size)
            .attr("fill", d => d.color);

        node.append("text")
            .text(d => d.id.substring(0, 20))
            .attr("x", d => d.size + 5)
            .attr("y", 3);

        // Tooltip
        const tooltip = d3.select(".tooltip");

        node.on("mouseover", (event, d) => {{
            tooltip.style("display", "block")
                .html(`
                    <strong>${{d.type}}</strong><br/>
                    ID: ${{d.id}}<br/>
                    Name: ${{d.name}}<br/>
                    Impact: ${{d.impact}} (${{d.score}}/100)<br/>
                    Depth: ${{d.depth}}
                `)
                .style("left", (event.pageX + 15) + "px")
                .style("top", (event.pageY - 10) + "px");
        }})
        .on("mouseout", () => {{
            tooltip.style("display", "none");
        }});

        simulation.on("tick", () => {{
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);

            node.attr("transform", d => `translate(${{d.x}},${{d.y}})`);
        }});

        function dragstarted(event) {{
            if (!event.active) simulation.alphaTarget(0.3).restart();
            event.subject.fx = event.subject.x;
            event.subject.fy = event.subject.y;
        }}

        function dragged(event) {{
            event.subject.fx = event.x;
            event.subject.fy = event.y;
        }}

        function dragended(event) {{
            if (!event.active) simulation.alphaTarget(0);
            event.subject.fx = null;
            event.subject.fy = null;
        }}
    </script>
</body>
</html>"""
