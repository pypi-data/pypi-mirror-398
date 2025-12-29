"""
Snapshot diff report formatting.

Generates console, JSON, and Markdown reports for snapshot diffs.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from replimap.snapshot.models import ResourceChange, SnapshotDiff

console = Console()


class SnapshotReporter:
    """
    Generate snapshot diff reports in various formats.

    Supports:
    - Console output (Rich formatting)
    - JSON export
    - Markdown export (for SOC2 evidence)
    """

    def to_console(self, diff: SnapshotDiff, verbose: bool = False) -> None:
        """
        Print diff to console with Rich formatting.

        Args:
            diff: The SnapshotDiff to display
            verbose: Show full attribute changes
        """
        # Header
        console.print()
        console.print("[bold blue]📸 Infrastructure Snapshot Diff[/bold blue]")
        console.print()

        # Summary panel
        summary_text = (
            f"[bold]Baseline:[/bold] {diff.baseline_name}\n"
            f"[dim]{diff.baseline_date[:19]}[/dim]\n\n"
            f"[bold]Current:[/bold] {diff.current_name}\n"
            f"[dim]{diff.current_date[:19]}[/dim]\n\n"
            f"[green]+ Added:[/green]    {diff.total_added}\n"
            f"[red]- Removed:[/red]  {diff.total_removed}\n"
            f"[yellow]~ Modified:[/yellow] {diff.total_modified}\n"
            f"[dim]= Unchanged: {diff.total_unchanged}[/dim]"
        )
        console.print(Panel(summary_text, title="Summary", border_style="blue"))

        # No changes case
        if not diff.has_changes:
            console.print()
            console.print("[green]✓ No changes detected[/green]")
            return

        # Critical/High severity changes
        if diff.critical_changes:
            console.print()
            console.print("[bold red]⚠️ High Severity Changes:[/bold red]")
            console.print()
            for change in diff.critical_changes:
                self._print_change(change, highlight=True)

        # Changes by type table
        if diff.by_type:
            console.print()
            console.print("[bold]Changes by Resource Type:[/bold]")
            console.print()

            table = Table()
            table.add_column("Resource Type")
            table.add_column("Added", style="green", justify="right")
            table.add_column("Removed", style="red", justify="right")
            table.add_column("Modified", style="yellow", justify="right")

            for rtype, counts in sorted(diff.by_type.items()):
                if counts["added"] or counts["removed"] or counts["modified"]:
                    table.add_row(
                        rtype.replace("aws_", ""),
                        str(counts["added"]) if counts["added"] else "-",
                        str(counts["removed"]) if counts["removed"] else "-",
                        str(counts["modified"]) if counts["modified"] else "-",
                    )

            console.print(table)

        # Detailed changes
        if diff.changes:
            console.print()
            console.print("[bold]All Changes:[/bold]")
            console.print()

            # Group by change type
            added = diff.get_changes_by_type("added")
            removed = diff.get_changes_by_type("removed")
            modified = diff.get_changes_by_type("modified")

            max_display = 20

            if added:
                console.print("[green]Added Resources:[/green]")
                for change in added[:max_display]:
                    self._print_change(change)
                if len(added) > max_display:
                    console.print(
                        f"[dim]  ... and {len(added) - max_display} more[/dim]"
                    )
                console.print()

            if removed:
                console.print("[red]Removed Resources:[/red]")
                for change in removed[:max_display]:
                    self._print_change(change)
                if len(removed) > max_display:
                    console.print(
                        f"[dim]  ... and {len(removed) - max_display} more[/dim]"
                    )
                console.print()

            if modified:
                console.print("[yellow]Modified Resources:[/yellow]")
                for change in modified[:max_display]:
                    self._print_change(change, show_diff=verbose)
                if len(modified) > max_display:
                    console.print(
                        f"[dim]  ... and {len(modified) - max_display} more[/dim]"
                    )

    def _print_change(
        self,
        change: ResourceChange,
        highlight: bool = False,
        show_diff: bool = False,
    ) -> None:
        """Print a single change."""
        severity_colors = {
            "critical": "red bold",
            "high": "red",
            "medium": "yellow",
            "low": "dim",
        }

        color = severity_colors.get(change.severity, "white")

        if change.change_type == "added":
            prefix = "[green]+[/green]"
        elif change.change_type == "removed":
            prefix = "[red]-[/red]"
        else:
            prefix = "[yellow]~[/yellow]"

        name = change.resource_name or change.resource_id

        if highlight:
            console.print(
                f"  {prefix} [{color}]{change.resource_type}: {name}[/{color}] "
                f"[{change.severity.upper()}]"
            )
        else:
            console.print(f"  {prefix} {change.resource_type}: {name}")

        if show_diff and change.changed_attributes:
            for attr in change.changed_attributes[:5]:
                before_val = change.before.get(attr, "")
                after_val = change.after.get(attr, "")
                # Truncate long values
                before_str = str(before_val)[:50]
                after_str = str(after_val)[:50]
                if len(str(before_val)) > 50:
                    before_str += "..."
                if len(str(after_val)) > 50:
                    after_str += "..."

                console.print(f"      [dim]{attr}:[/dim]")
                console.print(f"        [red]- {before_str}[/red]")
                console.print(f"        [green]+ {after_str}[/green]")

            if len(change.changed_attributes) > 5:
                console.print(
                    f"      [dim]... and {len(change.changed_attributes) - 5} more attributes[/dim]"
                )

    def to_json(self, diff: SnapshotDiff, output_path: Path) -> Path:
        """
        Export diff to JSON.

        Args:
            diff: The SnapshotDiff to export
            output_path: Path for the JSON file

        Returns:
            Path to the created file
        """
        output_path = output_path.with_suffix(".json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(diff.to_dict(), indent=2, default=str))

        console.print(f"[green]✓ Exported to {output_path}[/green]")
        return output_path

    def to_markdown(self, diff: SnapshotDiff, output_path: Path) -> Path:
        """
        Export diff to Markdown.

        Designed for SOC2 CC7.1 (Change Management) evidence.

        Args:
            diff: The SnapshotDiff to export
            output_path: Path for the Markdown file

        Returns:
            Path to the created file
        """
        output_path = output_path.with_suffix(".md")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        md = f"""# Infrastructure Change Report

Generated: {datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")}

## Summary

| Metric | Value |
|--------|-------|
| Baseline Snapshot | {diff.baseline_name} |
| Baseline Date | {diff.baseline_date[:19]} |
| Current Snapshot | {diff.current_name} |
| Current Date | {diff.current_date[:19]} |
| Resources Added | {diff.total_added} |
| Resources Removed | {diff.total_removed} |
| Resources Modified | {diff.total_modified} |
| Resources Unchanged | {diff.total_unchanged} |
| **Total Changes** | **{diff.total_changes}** |

"""

        # Changes by type table
        if diff.by_type:
            md += "## Changes by Resource Type\n\n"
            md += "| Resource Type | Added | Removed | Modified |\n"
            md += "|---------------|-------|---------|----------|\n"

            for rtype, counts in sorted(diff.by_type.items()):
                if counts["added"] or counts["removed"] or counts["modified"]:
                    md += (
                        f"| {rtype} | {counts['added']} | "
                        f"{counts['removed']} | {counts['modified']} |\n"
                    )
            md += "\n"

        # Critical changes
        if diff.critical_changes:
            md += "## ⚠️ High Severity Changes\n\n"
            md += "These changes require immediate attention:\n\n"

            for change in diff.critical_changes:
                md += (
                    f"- **{change.change_type.upper()}** `{change.resource_type}`: "
                    f"`{change.resource_id}` [{change.severity.upper()}]\n"
                )
                if change.changed_attributes:
                    md += f"  - Changed: {', '.join(change.changed_attributes[:5])}\n"
            md += "\n"

        # Detailed changes
        md += "## Detailed Changes\n\n"

        added = diff.get_changes_by_type("added")
        removed = diff.get_changes_by_type("removed")
        modified = diff.get_changes_by_type("modified")

        if added:
            md += "### Added Resources\n\n"
            for change in added[:50]:
                md += f"- `{change.resource_type}`: `{change.resource_id}`"
                if change.resource_name:
                    md += f" ({change.resource_name})"
                md += "\n"
            if len(added) > 50:
                md += f"\n*... and {len(added) - 50} more*\n"
            md += "\n"

        if removed:
            md += "### Removed Resources\n\n"
            for change in removed[:50]:
                md += f"- `{change.resource_type}`: `{change.resource_id}`"
                if change.resource_name:
                    md += f" ({change.resource_name})"
                md += "\n"
            if len(removed) > 50:
                md += f"\n*... and {len(removed) - 50} more*\n"
            md += "\n"

        if modified:
            md += "### Modified Resources\n\n"
            for change in modified[:50]:
                md += f"#### `{change.resource_type}`: `{change.resource_id}`\n\n"
                if change.resource_name:
                    md += f"Name: {change.resource_name}\n\n"
                md += f"Severity: {change.severity}\n\n"
                if change.changed_attributes:
                    md += "Changed attributes:\n"
                    for attr in change.changed_attributes[:10]:
                        before_val = str(change.before.get(attr, ""))[:100]
                        after_val = str(change.after.get(attr, ""))[:100]
                        md += f"- `{attr}`:\n"
                        md += f"  - Before: `{before_val}`\n"
                        md += f"  - After: `{after_val}`\n"
                    if len(change.changed_attributes) > 10:
                        md += f"\n*... and {len(change.changed_attributes) - 10} more attributes*\n"
                md += "\n"

            if len(modified) > 50:
                md += f"\n*... and {len(modified) - 50} more modified resources*\n"

        # Footer
        md += """
---

## SOC2 Compliance Notes

This report supports the following SOC2 Trust Service Criteria:

- **CC7.1 (Change Management)**: Documents infrastructure changes
- **CC7.2 (Monitoring)**: Demonstrates change detection capability
- **A1.2 (Recovery)**: Baseline snapshots for disaster recovery reference

---

*Generated by [RepliMap](https://replimap.com)*
"""

        output_path.write_text(md)
        console.print(f"[green]✓ Exported to {output_path}[/green]")
        return output_path

    def to_html(self, diff: SnapshotDiff, output_path: Path) -> Path:
        """
        Export diff to HTML.

        Args:
            diff: The SnapshotDiff to export
            output_path: Path for the HTML file

        Returns:
            Path to the created file
        """
        output_path = output_path.with_suffix(".html")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate HTML report
        html = self._generate_html(diff)
        output_path.write_text(html)

        console.print(f"[green]✓ Exported to {output_path}[/green]")
        return output_path

    def _generate_html(self, diff: SnapshotDiff) -> str:
        """Generate HTML report content."""
        timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")

        # Build changes by type rows
        by_type_rows = ""
        for rtype, counts in sorted(diff.by_type.items()):
            if counts["added"] or counts["removed"] or counts["modified"]:
                by_type_rows += f"""
                <tr>
                    <td class="px-4 py-2">{rtype}</td>
                    <td class="px-4 py-2 text-green-600">{counts["added"] or "-"}</td>
                    <td class="px-4 py-2 text-red-600">{counts["removed"] or "-"}</td>
                    <td class="px-4 py-2 text-yellow-600">{counts["modified"] or "-"}</td>
                </tr>
                """

        # Build critical changes section
        critical_section = ""
        if diff.critical_changes:
            critical_items = ""
            for c in diff.critical_changes:
                critical_items += f"""
                <div class="p-3 bg-red-50 border border-red-200 rounded mb-2">
                    <span class="font-semibold text-red-700">{c.change_type.upper()}</span>
                    <span class="text-gray-700">{c.resource_type}: {c.resource_id}</span>
                    <span class="ml-2 px-2 py-1 bg-red-100 text-red-800 text-xs rounded">{c.severity.upper()}</span>
                </div>
                """
            critical_section = f"""
            <div class="mb-8">
                <h2 class="text-xl font-bold text-red-600 mb-4">⚠️ High Severity Changes</h2>
                {critical_items}
            </div>
            """

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Infrastructure Change Report - RepliMap</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50 min-h-screen">
    <div class="max-w-6xl mx-auto px-4 py-8">
        <header class="mb-8">
            <h1 class="text-3xl font-bold text-gray-800">📸 Infrastructure Change Report</h1>
            <p class="text-gray-500 mt-2">Generated: {timestamp}</p>
        </header>

        <div class="bg-white rounded-lg shadow p-6 mb-8">
            <h2 class="text-xl font-bold mb-4">Summary</h2>
            <div class="grid grid-cols-2 gap-4 mb-4">
                <div>
                    <p class="text-gray-500">Baseline</p>
                    <p class="font-semibold">{diff.baseline_name}</p>
                    <p class="text-sm text-gray-400">{diff.baseline_date[:19]}</p>
                </div>
                <div>
                    <p class="text-gray-500">Current</p>
                    <p class="font-semibold">{diff.current_name}</p>
                    <p class="text-sm text-gray-400">{diff.current_date[:19]}</p>
                </div>
            </div>
            <div class="grid grid-cols-4 gap-4 text-center">
                <div class="p-4 bg-green-50 rounded">
                    <p class="text-2xl font-bold text-green-600">+{diff.total_added}</p>
                    <p class="text-sm text-gray-500">Added</p>
                </div>
                <div class="p-4 bg-red-50 rounded">
                    <p class="text-2xl font-bold text-red-600">-{diff.total_removed}</p>
                    <p class="text-sm text-gray-500">Removed</p>
                </div>
                <div class="p-4 bg-yellow-50 rounded">
                    <p class="text-2xl font-bold text-yellow-600">~{diff.total_modified}</p>
                    <p class="text-sm text-gray-500">Modified</p>
                </div>
                <div class="p-4 bg-gray-50 rounded">
                    <p class="text-2xl font-bold text-gray-600">={diff.total_unchanged}</p>
                    <p class="text-sm text-gray-500">Unchanged</p>
                </div>
            </div>
        </div>

        {critical_section}

        <div class="bg-white rounded-lg shadow p-6 mb-8">
            <h2 class="text-xl font-bold mb-4">Changes by Resource Type</h2>
            <table class="w-full">
                <thead class="bg-gray-100">
                    <tr>
                        <th class="px-4 py-2 text-left">Resource Type</th>
                        <th class="px-4 py-2 text-left">Added</th>
                        <th class="px-4 py-2 text-left">Removed</th>
                        <th class="px-4 py-2 text-left">Modified</th>
                    </tr>
                </thead>
                <tbody>
                    {by_type_rows}
                </tbody>
            </table>
        </div>

        <footer class="text-center text-gray-400 text-sm mt-8">
            <p>Generated by RepliMap | SOC2 CC7.1 Change Management Evidence</p>
        </footer>
    </div>
</body>
</html>
"""
