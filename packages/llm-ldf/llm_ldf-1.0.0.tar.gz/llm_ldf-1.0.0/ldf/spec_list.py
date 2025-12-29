"""List and display specs in the project."""

import json
from datetime import datetime
from pathlib import Path

from rich.table import Table

from ldf.detection import get_specs_summary
from ldf.utils.console import console


def list_specs(output_format: str = "rich", project_root: Path | None = None) -> None:
    """List all specs in the project with details.

    Args:
        output_format: Output format (rich, json, text)
        project_root: Project root directory (defaults to cwd)
    """
    if project_root is None:
        project_root = Path.cwd()

    ldf_dir = project_root / ".ldf"

    if not ldf_dir.exists():
        console.print("[red]Error: No .ldf directory found.[/red]")
        console.print("Run [cyan]ldf init[/cyan] to initialize a project first.")
        raise SystemExit(1)

    # Get basic spec info
    specs = get_specs_summary(ldf_dir)

    # Enhance with last modified timestamp
    for spec_info in specs:
        spec_dir = ldf_dir / "specs" / spec_info["name"]
        last_modified = _get_last_modified(spec_dir)
        spec_info["last_modified"] = last_modified

    # Sort by name
    specs.sort(key=lambda x: x["name"])

    # Output based on format
    if output_format == "json":
        _print_json(specs)
    elif output_format == "text":
        _print_text(specs)
    else:  # rich
        _print_rich_table(specs)


def _get_last_modified(spec_dir: Path) -> str:
    """Get the last modified timestamp for a spec directory.

    Args:
        spec_dir: Path to spec directory

    Returns:
        ISO formatted timestamp of most recently modified file
    """
    latest_mtime = 0.0

    # Check all markdown files in the spec
    for md_file in ["requirements.md", "design.md", "tasks.md"]:
        file_path = spec_dir / md_file
        if file_path.exists():
            mtime = file_path.stat().st_mtime
            if mtime > latest_mtime:
                latest_mtime = mtime

    # If no files found, use directory mtime
    if latest_mtime == 0.0:
        latest_mtime = spec_dir.stat().st_mtime

    return datetime.fromtimestamp(latest_mtime).isoformat()


def _print_rich_table(specs: list[dict]) -> None:
    """Print specs as a Rich table.

    Args:
        specs: List of spec info dictionaries
    """
    if not specs:
        console.print("[dim]No specs found.[/dim]")
        console.print()
        console.print("Create a new spec with: [cyan]ldf create-spec <name>[/cyan]")
        return

    table = Table(title="Specs", show_header=True)
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Phase")
    table.add_column("Completeness", justify="center")
    table.add_column("Last Modified")

    for spec in specs:
        name = spec["name"]
        status = spec["status"]

        # Phase with color
        if status == "tasks":
            phase = "[green]tasks[/green]"
        elif status == "design":
            phase = "[yellow]design[/yellow]"
        elif status == "requirements":
            phase = "[blue]requirements[/blue]"
        else:
            phase = "[dim]empty[/dim]"

        # Completeness indicators
        req_icon = "[green]✓[/green]" if spec["has_requirements"] else "[dim]✗[/dim]"
        des_icon = "[green]✓[/green]" if spec["has_design"] else "[dim]✗[/dim]"
        task_icon = "[green]✓[/green]" if spec["has_tasks"] else "[dim]✗[/dim]"
        completeness = f"R:{req_icon} D:{des_icon} T:{task_icon}"

        # Format timestamp
        timestamp = spec["last_modified"]
        try:
            dt = datetime.fromisoformat(timestamp)
            formatted_time = dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            formatted_time = timestamp[:16]  # Truncate if parsing fails

        table.add_row(name, phase, completeness, formatted_time)

    console.print(table)
    console.print()
    console.print(f"[dim]Total: {len(specs)} spec(s)[/dim]")
    console.print()
    console.print("[dim]Legend: R=Requirements, D=Design, T=Tasks[/dim]")


def _print_json(specs: list[dict]) -> None:
    """Print specs as JSON.

    Args:
        specs: List of spec info dictionaries
    """
    output = {
        "specs": [
            {
                "name": spec["name"],
                "phase": spec["status"],
                "completeness": {
                    "requirements": spec["has_requirements"],
                    "design": spec["has_design"],
                    "tasks": spec["has_tasks"],
                },
                "last_modified": spec["last_modified"],
            }
            for spec in specs
        ],
        "total": len(specs),
    }

    print(json.dumps(output, indent=2))


def _print_text(specs: list[dict]) -> None:
    """Print specs as plain text.

    Args:
        specs: List of spec info dictionaries
    """
    if not specs:
        print("No specs found.")
        print()
        print("Create a new spec with: ldf create-spec <name>")
        return

    print("Specs")
    print("=" * 80)
    print()

    for spec in specs:
        print(f"Name: {spec['name']}")
        print(f"Phase: {spec['status']}")
        print("Completeness:")
        print(f"  Requirements: {'✓' if spec['has_requirements'] else '✗'}")
        print(f"  Design: {'✓' if spec['has_design'] else '✗'}")
        print(f"  Tasks: {'✓' if spec['has_tasks'] else '✗'}")
        print(f"Last Modified: {spec['last_modified']}")
        print()

    print(f"Total: {len(specs)} spec(s)")
