"""
Cost estimate report formatting.

Generates console output, JSON, and HTML reports for cost analysis.
Includes prominent disclaimers about estimate accuracy.
"""

from __future__ import annotations

import json
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from replimap.cost.models import (
    COST_DISCLAIMER_FULL,
    COST_DISCLAIMER_SHORT,
    EXCLUDED_FACTORS,
    CostConfidence,
    CostEstimate,
)

console = Console()


class CostReporter:
    """Generate cost estimate reports in various formats with disclaimers."""

    def to_console(self, estimate: CostEstimate) -> None:
        """Print cost estimate to console with prominent disclaimers."""
        # Header with warning
        console.print()
        console.print("[bold blue]💰 Cost Estimate[/bold blue]")
        console.print(f"[yellow]{COST_DISCLAIMER_SHORT}[/yellow]")
        console.print()

        # Confidence indicator
        confidence_color = self._get_confidence_color(estimate.confidence)

        # Summary panel with range
        summary = f"""
[bold]Monthly Estimate:[/bold] ${estimate.monthly_total:,.2f}
[dim]Range: ${estimate.estimated_range_low:,.2f} - ${estimate.estimated_range_high:,.2f} ({estimate.accuracy_range})[/dim]

[bold]Yearly Estimate:[/bold]  ${estimate.annual_total:,.2f}

[{confidence_color}]Confidence: {estimate.confidence.value} ({estimate.accuracy_range})[/{confidence_color}]
[dim]{estimate.confidence.description}[/dim]

[dim]Resources: {estimate.resource_count} total ({estimate.estimated_resources} priced)
Pricing: On-Demand (standard rates)[/dim]
"""
        console.print(
            Panel(summary.strip(), title="💰 Estimate Summary", border_style="blue")
        )

        # Warnings
        if estimate.warnings:
            console.print()
            for warning in estimate.warnings:
                console.print(f"[yellow]⚠️ {warning}[/yellow]")

        # Cost by category
        if estimate.by_category:
            console.print()
            console.print("[bold]Cost by Category:[/bold]")
            console.print()

            for breakdown in estimate.by_category:
                if breakdown.monthly_total > 0:
                    bar_width = int(breakdown.percentage / 2)  # Scale to max 50 chars
                    bar = "█" * bar_width + "░" * (50 - bar_width)
                    console.print(
                        f"  {breakdown.category.value:12} ${breakdown.monthly_total:>10,.2f} "
                        f"[dim]{bar}[/dim] {breakdown.percentage:5.1f}%"
                    )

        # Top resources table with confidence
        if estimate.top_resources:
            console.print()
            table = Table(title="Top 5 Estimated Costs")
            table.add_column("Resource", style="cyan", max_width=30)
            table.add_column("Type")
            table.add_column("Instance", max_width=15)
            table.add_column("Monthly Est.", justify="right", style="green")
            table.add_column("Confidence")

            for r in estimate.top_resources[:5]:
                conf_color = self._get_confidence_color(r.confidence)
                table.add_row(
                    self._truncate(r.resource_name, 30),
                    r.resource_type.replace("aws_", ""),
                    r.instance_type or "-",
                    f"${r.monthly_cost:,.2f}",
                    f"[{conf_color}]{r.confidence.value.lower()}[/{conf_color}]",
                )

            console.print(table)

        # Cost by region
        if len(estimate.by_region) > 1:
            console.print()
            console.print("[bold]Cost by Region:[/bold]")
            console.print()
            for region, cost in sorted(
                estimate.by_region.items(), key=lambda x: x[1], reverse=True
            ):
                pct = (
                    (cost / estimate.monthly_total * 100)
                    if estimate.monthly_total > 0
                    else 0
                )
                console.print(f"  {region:20} ${cost:>10,.2f} ({pct:5.1f}%)")

        # Optimization recommendations
        if estimate.recommendations:
            console.print()
            console.print("[bold]Optimization Recommendations:[/bold]")
            console.print()

            for i, rec in enumerate(estimate.recommendations[:5], 1):
                effort_color = {
                    "LOW": "green",
                    "MEDIUM": "yellow",
                    "HIGH": "red",
                }.get(rec.effort, "white")

                console.print(
                    f"  [bold]{i}. {rec.title}[/bold] "
                    f"[{effort_color}]({rec.effort} effort)[/{effort_color}]"
                )
                console.print(f"     {rec.description}")
                console.print(
                    f"     [green]Potential savings: ${rec.potential_savings:,.2f}/month[/green]"
                )
                console.print()

            if estimate.total_optimization_potential > 0:
                console.print(
                    f"[bold green]Total Optimization Potential: "
                    f"${estimate.total_optimization_potential:,.2f}/month "
                    f"({estimate.optimization_percentage:.1f}%)[/bold green]"
                )

        # Exclusions panel - always show
        self._print_exclusions()

        # Final disclaimer with links
        console.print()
        console.print(
            Panel(
                "[bold]For accurate cost projections, use:[/bold]\n"
                "• AWS Cost Explorer: https://console.aws.amazon.com/cost-management/\n"
                "• AWS Pricing Calculator: https://calculator.aws/",
                title="📊 Accurate Cost Tools",
                border_style="green",
            )
        )

    def _print_exclusions(self) -> None:
        """Print what's NOT included in the estimate."""
        console.print()
        console.print("[bold yellow]⚠️ NOT Included in This Estimate:[/bold yellow]")
        console.print()

        # Split into two columns
        half = len(EXCLUDED_FACTORS) // 2
        left = EXCLUDED_FACTORS[:half]
        right = EXCLUDED_FACTORS[half:]

        for i in range(max(len(left), len(right))):
            l_item = left[i] if i < len(left) else ""
            r_item = right[i] if i < len(right) else ""
            if l_item and r_item:
                console.print(f"  [dim]✗ {l_item:<35} ✗ {r_item}[/dim]")
            elif l_item:
                console.print(f"  [dim]✗ {l_item}[/dim]")
            elif r_item:
                console.print(f"  [dim]{' ' * 38} ✗ {r_item}[/dim]")

    def to_table(self, estimate: CostEstimate) -> None:
        """Print all resources as a table with disclaimer."""
        # Show disclaimer first
        console.print()
        console.print(f"[yellow]{COST_DISCLAIMER_SHORT}[/yellow]")
        console.print()

        table = Table(title="Resource Costs (Estimates Only)")
        table.add_column("Resource ID", style="cyan", max_width=35)
        table.add_column("Type", max_width=20)
        table.add_column("Category")
        table.add_column("Instance")
        table.add_column("Monthly Est.", justify="right", style="green")
        table.add_column("Annual Est.", justify="right")
        table.add_column("Confidence")

        for r in sorted(
            estimate.resource_costs, key=lambda x: x.monthly_cost, reverse=True
        ):
            confidence_color = self._get_confidence_color(r.confidence)
            table.add_row(
                self._truncate(r.resource_id, 35),
                r.resource_type.replace("aws_", ""),
                r.category.value,
                r.instance_type or "-",
                f"${r.monthly_cost:,.2f}",
                f"${r.annual_cost:,.2f}",
                f"[{confidence_color}]{r.confidence.value}[/{confidence_color}]",
            )

        console.print(table)

        # Show exclusions
        self._print_exclusions()

    def to_json(self, estimate: CostEstimate, output_path: Path) -> Path:
        """Export to JSON with full disclaimer."""
        data = estimate.to_dict()

        # Add full disclaimer at top level
        output = {
            "_disclaimer": COST_DISCLAIMER_FULL.strip(),
            "_generated_by": "RepliMap Cost Estimator",
            "_accuracy_note": f"Estimates are {estimate.accuracy_range} accurate",
            **data,
        }

        output_path.write_text(json.dumps(output, indent=2))
        console.print(f"[green]✓ Exported to {output_path}[/green]")
        console.print("[dim]Note: JSON includes full disclaimer[/dim]")
        return output_path

    def to_markdown(self, estimate: CostEstimate, output_path: Path) -> Path:
        """Export to Markdown with disclaimers."""
        conf = estimate.confidence

        md = f"""# Cost Estimate Report

> ⚠️ **DISCLAIMER:** {COST_DISCLAIMER_SHORT}

## Summary

| Metric | Value |
|--------|-------|
| **Monthly Estimate** | ${estimate.monthly_total:,.2f} |
| **Estimated Range** | ${estimate.estimated_range_low:,.2f} - ${estimate.estimated_range_high:,.2f} |
| **Confidence** | {conf.value} ({conf.accuracy_range}) |
| **Yearly Estimate** | ${estimate.annual_total:,.2f} |
| Resources | {estimate.resource_count} total |
| Pricing Model | On-Demand |

## Cost by Category

| Category | Monthly Est. | % of Total |
|----------|-------------|------------|
"""
        for b in estimate.by_category:
            if b.monthly_total > 0:
                md += f"| {b.category.value} | ${b.monthly_total:,.2f} | {b.percentage:.1f}% |\n"

        md += """
## Top 5 Costs

| Resource | Type | Monthly Est. | Confidence |
|----------|------|-------------|------------|
"""
        for r in estimate.top_resources[:5]:
            md += f"| {r.resource_name[:30]} | {r.resource_type.replace('aws_', '')} | ${r.monthly_cost:,.2f} | {r.confidence.value} |\n"

        md += """
## ⚠️ NOT Included in This Estimate

The following cost factors are **NOT** included and may significantly increase your actual bill:

"""
        for factor in EXCLUDED_FACTORS:
            md += f"- {factor}\n"

        # Add recommendations if any
        if estimate.recommendations:
            md += """
## Optimization Recommendations

"""
            for i, rec in enumerate(estimate.recommendations[:5], 1):
                md += f"### {i}. {rec.title}\n\n"
                md += f"{rec.description}\n\n"
                md += f"**Potential savings:** ${rec.potential_savings:,.2f}/month\n"
                md += f"**Effort:** {rec.effort}\n\n"

            if estimate.total_optimization_potential > 0:
                md += f"\n**Total potential savings:** ${estimate.total_optimization_potential:,.2f}/month ({estimate.optimization_percentage:.1f}%)\n"

        md += f"""
## Important Notes

1. This estimate is based on **standard on-demand pricing** only
2. Actual costs depend on your specific usage patterns
3. Data transfer costs alone can add 10-30% to your bill
4. Reserved Instances and Savings Plans may reduce costs significantly

## For Accurate Cost Projections

- **AWS Cost Explorer:** https://console.aws.amazon.com/cost-management/
- **AWS Pricing Calculator:** https://calculator.aws/

---

*Generated by RepliMap Cost Estimator*
*Confidence: {conf.value} ({conf.accuracy_range})*
*This is an estimate only and should not be used for financial planning without verification.*
"""

        output_path.write_text(md)
        console.print(f"[green]✓ Exported to {output_path}[/green]")
        return output_path

    def to_html(self, estimate: CostEstimate, output_path: Path) -> Path:
        """Export to HTML report with disclaimers."""
        html = self._generate_html(estimate)
        output_path.write_text(html)
        console.print(f"[green]✓ Exported to {output_path}[/green]")
        return output_path

    def to_csv(self, estimate: CostEstimate, output_path: Path) -> Path:
        """Export to CSV with disclaimer header."""
        lines = [
            f"# DISCLAIMER: {COST_DISCLAIMER_SHORT}",
            f"# Confidence: {estimate.confidence.value} ({estimate.accuracy_range})",
            f"# Monthly Total Estimate: ${estimate.monthly_total:,.2f}",
            f"# Range: ${estimate.estimated_range_low:,.2f} - ${estimate.estimated_range_high:,.2f}",
            "#",
            "resource_id,resource_type,category,instance_type,monthly_cost,annual_cost,confidence,accuracy_range",
        ]

        for r in estimate.resource_costs:
            lines.append(
                f'"{r.resource_id}",{r.resource_type},{r.category.value},'
                f"{r.instance_type},{r.monthly_cost:.2f},{r.annual_cost:.2f},"
                f"{r.confidence.value},{r.accuracy_range}"
            )

        output_path.write_text("\n".join(lines))
        console.print(f"[green]✓ Exported to {output_path}[/green]")
        console.print("[dim]Note: CSV includes disclaimer header[/dim]")
        return output_path

    def _get_confidence_color(self, confidence: CostConfidence) -> str:
        """Get color for confidence level."""
        colors = {
            CostConfidence.HIGH: "green",
            CostConfidence.MEDIUM: "yellow",
            CostConfidence.LOW: "red",
            CostConfidence.UNKNOWN: "dim",
        }
        return colors.get(confidence, "white")

    def _truncate(self, text: str, max_len: int) -> str:
        """Truncate text with ellipsis."""
        if len(text) <= max_len:
            return text
        return text[: max_len - 3] + "..."

    def _generate_html(self, estimate: CostEstimate) -> str:
        """Generate HTML report with disclaimers."""
        # Build category chart data
        category_data = [
            {"name": b.category.value, "value": round(b.monthly_total, 2)}
            for b in estimate.by_category
            if b.monthly_total > 0
        ]

        # Build top resources data
        top_data = [
            {
                "id": r.resource_id[:30],
                "type": r.resource_type,
                "cost": round(r.monthly_cost, 2),
                "confidence": r.confidence.value,
            }
            for r in estimate.top_resources[:10]
        ]

        # Build recommendations HTML
        recommendations_html = ""
        for i, rec in enumerate(estimate.recommendations[:5], 1):
            effort_class = rec.effort.lower()
            recommendations_html += f"""
            <div class="recommendation">
                <div class="rec-header">
                    <span class="rec-title">{i}. {rec.title}</span>
                    <span class="effort effort-{effort_class}">{rec.effort}</span>
                </div>
                <p>{rec.description}</p>
                <div class="savings">Potential savings: ${rec.potential_savings:,.2f}/month</div>
            </div>
            """

        # Build warnings HTML
        warnings_html = ""
        if estimate.warnings:
            warnings_html = "\n".join(
                f'<div class="warning">{w}</div>' for w in estimate.warnings
            )

        # Build excluded factors list
        excluded_html = "\n".join(f"<li>{f}</li>" for f in EXCLUDED_FACTORS)

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cost Estimate Report - RepliMap</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            background: #f5f5f5;
            color: #333;
        }}
        .disclaimer-banner {{
            background: #fff3cd;
            border-bottom: 2px solid #ffc107;
            color: #856404;
            padding: 15px 30px;
            text-align: center;
            font-weight: 500;
        }}
        #header {{
            background: linear-gradient(135deg, #1a73e8 0%, #174ea6 100%);
            color: white;
            padding: 30px;
        }}
        #header h1 {{
            margin: 0 0 5px 0;
            font-size: 28px;
        }}
        #header .subtitle {{
            opacity: 0.8;
            font-size: 14px;
        }}
        .stats {{
            display: flex;
            gap: 40px;
            margin-top: 20px;
            flex-wrap: wrap;
        }}
        .stat {{
            text-align: center;
        }}
        .stat-value {{
            font-size: 36px;
            font-weight: bold;
        }}
        .stat-label {{
            font-size: 12px;
            opacity: 0.8;
            text-transform: uppercase;
        }}
        .stat-range {{
            font-size: 12px;
            opacity: 0.7;
            margin-top: 4px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        .card {{
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            padding: 20px;
            margin-bottom: 20px;
        }}
        .card h2 {{
            margin: 0 0 15px 0;
            font-size: 18px;
            color: #333;
        }}
        .warning {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            color: #856404;
            padding: 10px 15px;
            margin: 5px 0;
            font-size: 14px;
        }}
        .exclusions {{
            background: #fef3e6;
            border: 1px solid #f0ad4e;
            border-radius: 8px;
            padding: 20px;
        }}
        .exclusions h2 {{
            color: #856404;
            margin-top: 0;
        }}
        .exclusions ul {{
            columns: 2;
            list-style: none;
            padding: 0;
        }}
        .exclusions li {{
            padding: 4px 0;
            color: #856404;
        }}
        .exclusions li::before {{
            content: "✗ ";
            color: #dc3545;
        }}
        .grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }}
        @media (max-width: 768px) {{
            .grid {{
                grid-template-columns: 1fr;
            }}
            .exclusions ul {{
                columns: 1;
            }}
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        th {{
            font-weight: 600;
            color: #666;
            font-size: 12px;
            text-transform: uppercase;
        }}
        .cost {{
            color: #1a73e8;
            font-weight: 600;
        }}
        .confidence-high {{
            color: #28a745;
        }}
        .confidence-medium {{
            color: #ffc107;
        }}
        .confidence-low {{
            color: #dc3545;
        }}
        .recommendation {{
            background: #f8f9fa;
            border-radius: 6px;
            padding: 15px;
            margin-bottom: 10px;
        }}
        .rec-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }}
        .rec-title {{
            font-weight: 600;
        }}
        .effort {{
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
        }}
        .effort-low {{
            background: #d4edda;
            color: #155724;
        }}
        .effort-medium {{
            background: #fff3cd;
            color: #856404;
        }}
        .effort-high {{
            background: #f8d7da;
            color: #721c24;
        }}
        .savings {{
            color: #28a745;
            font-weight: 600;
            margin-top: 8px;
        }}
        #categoryChart {{
            max-height: 300px;
        }}
        .total-savings {{
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .total-savings .value {{
            font-size: 32px;
            font-weight: bold;
        }}
        .total-savings .label {{
            font-size: 14px;
            opacity: 0.9;
        }}
        .tools-box {{
            background: #d4edda;
            border: 1px solid #28a745;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
        }}
        .tools-box h2 {{
            color: #155724;
            margin-top: 0;
        }}
        .tools-box a {{
            color: #155724;
            font-weight: 500;
        }}
        footer {{
            text-align: center;
            padding: 30px;
            color: #666;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="disclaimer-banner">
        ⚠️ ESTIMATE ONLY - Actual costs may vary significantly. Does not include data transfer, API calls, or usage-based fees.
    </div>

    <div id="header">
        <h1>💰 Cost Estimate Report</h1>
        <div class="subtitle">Confidence: {estimate.confidence.value} ({
            estimate.accuracy_range
        })</div>
        <div class="stats">
            <div class="stat">
                <div class="stat-value">${estimate.monthly_total:,.2f}</div>
                <div class="stat-label">Monthly Estimate</div>
                <div class="stat-range">${estimate.estimated_range_low:,.2f} - ${
            estimate.estimated_range_high:,.2f}</div>
            </div>
            <div class="stat">
                <div class="stat-value">${estimate.annual_total:,.2f}</div>
                <div class="stat-label">Annual Estimate</div>
            </div>
            <div class="stat">
                <div class="stat-value">{estimate.resource_count}</div>
                <div class="stat-label">Resources</div>
            </div>
            <div class="stat">
                <div class="stat-value">{estimate.confidence.value}</div>
                <div class="stat-label">Confidence</div>
            </div>
        </div>
    </div>

    {warnings_html}

    <div class="container">
        <div class="grid">
            <div class="card">
                <h2>Cost by Category</h2>
                <canvas id="categoryChart"></canvas>
            </div>
            <div class="card">
                <h2>Top Resources</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Resource</th>
                            <th>Type</th>
                            <th style="text-align: right">Monthly Est.</th>
                            <th>Confidence</th>
                        </tr>
                    </thead>
                    <tbody>
                        {
            "".join(
                f'''
                        <tr>
                            <td>{r["id"]}</td>
                            <td>{r["type"].replace("aws_", "")}</td>
                            <td class="cost" style="text-align: right">${r["cost"]:,.2f}</td>
                            <td class="confidence-{r["confidence"].lower()}">{r["confidence"]}</td>
                        </tr>
                        '''
                for r in top_data
            )
        }
                    </tbody>
                </table>
            </div>
        </div>

        <div class="exclusions">
            <h2>⚠️ NOT Included in This Estimate</h2>
            <p>The following cost factors are not included and may significantly increase your actual bill:</p>
            <ul>
                {excluded_html}
            </ul>
        </div>

        <div class="card">
            <h2>Optimization Recommendations</h2>
            {
            recommendations_html
            if recommendations_html
            else "<p>No optimization recommendations at this time.</p>"
        }

            {
            f'''
            <div class="total-savings" style="margin-top: 20px">
                <div class="value">${estimate.total_optimization_potential:,.2f}</div>
                <div class="label">Potential Monthly Savings ({estimate.optimization_percentage:.1f}%)</div>
            </div>
            '''
            if estimate.total_optimization_potential > 0
            else ""
        }
        </div>

        <div class="tools-box">
            <h2>📊 For Accurate Cost Projections</h2>
            <p>
                <a href="https://console.aws.amazon.com/cost-management/" target="_blank">AWS Cost Explorer</a> |
                <a href="https://calculator.aws/" target="_blank">AWS Pricing Calculator</a>
            </p>
        </div>

        <div class="card">
            <h2>All Resources</h2>
            <table>
                <thead>
                    <tr>
                        <th>Resource ID</th>
                        <th>Type</th>
                        <th>Category</th>
                        <th>Instance</th>
                        <th style="text-align: right">Monthly Est.</th>
                        <th style="text-align: right">Annual Est.</th>
                        <th>Confidence</th>
                    </tr>
                </thead>
                <tbody>
                    {
            "".join(
                f'''
                    <tr>
                        <td>{r.resource_id[:40]}</td>
                        <td>{r.resource_type.replace("aws_", "")}</td>
                        <td>{r.category.value}</td>
                        <td>{r.instance_type or "-"}</td>
                        <td class="cost" style="text-align: right">${r.monthly_cost:,.2f}</td>
                        <td style="text-align: right">${r.annual_cost:,.2f}</td>
                        <td class="confidence-{r.confidence.value.lower()}">{r.confidence.value}</td>
                    </tr>
                    '''
                for r in sorted(
                    estimate.resource_costs, key=lambda x: x.monthly_cost, reverse=True
                )
            )
        }
                </tbody>
            </table>
        </div>
    </div>

    <footer>
        <p>Generated by RepliMap Cost Estimator</p>
        <p><strong>This is an estimate only.</strong> Actual costs depend on your specific usage patterns and pricing agreements.</p>
    </footer>

    <script>
        const categoryData = {json.dumps(category_data)};

        new Chart(document.getElementById('categoryChart'), {{
            type: 'doughnut',
            data: {{
                labels: categoryData.map(d => d.name),
                datasets: [{{
                    data: categoryData.map(d => d.value),
                    backgroundColor: [
                        '#1a73e8',
                        '#34a853',
                        '#fbbc04',
                        '#ea4335',
                        '#9334e6',
                        '#00acc1',
                        '#ff6f00',
                    ]
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{
                        position: 'right'
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>"""
