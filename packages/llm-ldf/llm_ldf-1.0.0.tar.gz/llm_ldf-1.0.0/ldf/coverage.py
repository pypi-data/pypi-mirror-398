"""LDF test coverage reporting against guardrail requirements."""

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from rich.panel import Panel
from rich.table import Table

from ldf.utils.config import load_config
from ldf.utils.console import console
from ldf.utils.guardrail_loader import get_active_guardrails, get_guardrail_by_id


def report_coverage(
    service: str | None = None,
    guardrail_id: int | None = None,
    project_root: Path | None = None,
    validate: bool = False,
    verbose: bool = False,
    threshold_override: int | None = None,
) -> dict[str, Any]:
    """Report test coverage against guardrail requirements.

    Args:
        service: Service name for service-specific coverage
        guardrail_id: Guardrail ID for guardrail-specific coverage
        project_root: Project root directory
        validate: If True, return FAIL status when below threshold (for CI)
        verbose: If True, show detailed per-file breakdown
        threshold_override: Override the default coverage threshold

    Returns:
        Coverage report dictionary
    """
    if project_root is None:
        project_root = Path.cwd()

    # Check if LDF is initialized
    ldf_dir = project_root / ".ldf"
    if not ldf_dir.exists():
        console.print("[red]Error: .ldf/ not found. Run 'ldf init' first.[/red]")
        return {"status": "ERROR", "error": "LDF not initialized"}

    # Load configuration
    try:
        config = load_config(project_root)
    except FileNotFoundError:
        console.print("[red]Error: Could not load LDF configuration.[/red]")
        return {"status": "ERROR", "error": "Config not found"}

    # Load guardrails
    guardrails = get_active_guardrails(project_root)

    # Get coverage thresholds - prioritize config.yaml coverage section
    default_threshold = 80
    critical_threshold = 90

    # Check config.yaml for coverage section first (as documented)
    coverage_config = config.get("coverage", {})
    if coverage_config:
        default_threshold = coverage_config.get("default_threshold", 80)
        critical_threshold = coverage_config.get("critical_threshold", 90)
    else:
        # Fall back to guardrail #1 config
        for g in guardrails:
            if g.id == 1:  # Testing Coverage guardrail
                default_threshold = g.config.get("default_threshold", 80)
                critical_threshold = g.config.get("critical_paths_threshold", 90)
                break

    # Apply threshold override if provided
    if threshold_override is not None:
        default_threshold = threshold_override

    # Filter to specific guardrail if requested
    if guardrail_id is not None:
        guardrail = get_guardrail_by_id(guardrail_id, project_root)
        if guardrail:
            console.print(f"[dim]Filtering to guardrail #{guardrail_id}: {guardrail.name}[/dim]\n")
        else:
            console.print(f"[yellow]Warning: Guardrail #{guardrail_id} not found[/yellow]\n")

    console.print(
        Panel.fit(
            f"[bold blue]LDF Coverage Report[/bold blue]\n"
            f"Default threshold: {default_threshold}%\n"
            f"Critical paths: {critical_threshold}%",
            title="Coverage",
        )
    )

    # Try to find and parse coverage data
    coverage_data = _find_coverage_data(project_root)

    if coverage_data is None:
        console.print("\n[yellow]No coverage data found.[/yellow]")
        console.print("\nTo generate coverage data, run your test suite with coverage enabled:")
        console.print("  [dim]# Python (pytest)[/dim]")
        console.print("  pytest --cov=. --cov-report=json")
        console.print("\n  [dim]# Node.js (Jest)[/dim]")
        console.print("  jest --coverage --coverageReporters=json")
        console.print("\n  [dim]# Go[/dim]")
        console.print("  go test -coverprofile=coverage.out ./...")

        return {"status": "ERROR", "error": "No coverage data", "threshold": default_threshold}

    # Filter by service if specified
    if service:
        coverage_data = _filter_by_service(coverage_data, service)
        console.print(f"\n[dim]Filtered to service: {service}[/dim]")

    # Generate report
    report = _generate_report(coverage_data, default_threshold, critical_threshold, guardrail_id)

    # Display report
    _display_report(report, verbose=verbose)

    # Validation message for CI mode
    if validate:
        if report["status"] == "PASS":
            console.print("\n[green]✓ Coverage validation passed[/green]")
        else:
            pct = report["coverage_percent"]
            console.print(
                f"\n[red]✗ Coverage validation failed: {pct:.1f}% < {default_threshold}%[/red]"
            )

    return report


def _find_coverage_data(project_root: Path) -> dict[str, Any] | None:
    """Find and parse coverage data from common locations.

    Args:
        project_root: Project root directory

    Returns:
        Parsed coverage data or None if not found
    """
    # Common coverage file locations
    coverage_files = [
        # Python (pytest-cov)
        project_root / "coverage.json",
        project_root / ".coverage.json",
        project_root / "htmlcov" / "status.json",
        # Node.js (Jest, c8)
        project_root / "coverage" / "coverage-final.json",
        project_root / "coverage" / "coverage-summary.json",
        # Generic
        project_root / ".ldf" / "coverage.json",
    ]

    for coverage_file in coverage_files:
        if coverage_file.exists():
            try:
                with open(coverage_file) as f:
                    data = json.load(f)
                    console.print(f"[dim]Found coverage data: {coverage_file}[/dim]")
                    return _normalize_coverage_data(data, coverage_file)
            except (json.JSONDecodeError, KeyError):
                continue

    # Try to run coverage report command
    return _try_generate_coverage(project_root)


def _try_generate_coverage(project_root: Path) -> dict[str, Any] | None:
    """Try to generate coverage data by running common commands.

    Requires LDF_COVERAGE_WRITE=1 environment variable to enable automatic
    coverage file generation. This prevents unexpected file writes in
    read-only environments.

    Args:
        project_root: Project root directory

    Returns:
        Coverage data or None
    """
    # Check for Python coverage data
    coverage_py = project_root / ".coverage"
    if not coverage_py.exists():
        return None

    # Check if automatic generation is enabled
    if not os.getenv("LDF_COVERAGE_WRITE"):
        console.print(
            "[yellow]Found .coverage file but automatic generation is disabled.[/yellow]\n"
            "[dim]Set LDF_COVERAGE_WRITE=1 to enable, or run manually:[/dim]\n"
            "  coverage json -o .ldf/coverage.json"
        )
        return None

    # Check coverage tool is installed
    if not shutil.which("coverage"):
        console.print(
            "[yellow]Coverage tool not found. Install with: pip install coverage[/yellow]"
        )
        return None

    # Check .ldf directory exists and is writable
    ldf_dir = project_root / ".ldf"
    if not ldf_dir.exists():
        console.print("[red]Error: .ldf directory not found[/red]")
        return None

    if not os.access(ldf_dir, os.W_OK):
        console.print(f"[red]Error: No write permission to {ldf_dir}[/red]")
        return None

    # Notify user and generate
    coverage_file = ldf_dir / "coverage.json"
    console.print(f"[dim]Generating coverage data: {coverage_file}[/dim]")

    try:
        result = subprocess.run(
            ["coverage", "json", "-o", str(coverage_file)],
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            console.print(f"[yellow]Coverage generation failed: {result.stderr}[/yellow]")
            return None

        if coverage_file.exists():
            with open(coverage_file) as f:
                data = json.load(f)
                return _normalize_coverage_data(data, coverage_file)
    except subprocess.SubprocessError as e:
        console.print(f"[yellow]Coverage generation error: {e}[/yellow]")

    return None


def _normalize_coverage_data(data: dict[str, Any], source_file: Path) -> dict[str, Any]:
    """Normalize coverage data from different formats.

    Args:
        data: Raw coverage data
        source_file: Source file path (used to detect format)

    Returns:
        Normalized coverage data
    """
    # Detect format and normalize
    if "totals" in data:
        # pytest-cov format
        return {
            "format": "pytest-cov",
            "totals": {
                "lines_covered": data["totals"].get("covered_lines", 0),
                "lines_total": data["totals"].get("num_statements", 0),
                "percent": data["totals"].get("percent_covered", 0),
            },
            "files": data.get("files", {}),
        }
    elif "total" in data:
        # Jest/c8 summary format
        total = data["total"]
        return {
            "format": "jest",
            "totals": {
                "lines_covered": total.get("lines", {}).get("covered", 0),
                "lines_total": total.get("lines", {}).get("total", 0),
                "percent": total.get("lines", {}).get("pct", 0),
            },
            "files": {k: v for k, v in data.items() if k != "total"},
        }
    else:
        # Unknown format, try to extract basics
        return {
            "format": "unknown",
            "totals": {
                "lines_covered": 0,
                "lines_total": 0,
                "percent": 0,
            },
            "files": data,
        }


def _filter_by_service(coverage_data: dict[str, Any], service: str) -> dict[str, Any]:
    """Filter coverage data to a specific service.

    Args:
        coverage_data: Full coverage data
        service: Service name to filter to

    Returns:
        Filtered coverage data
    """
    if "files" not in coverage_data:
        return coverage_data

    # Filter files that match the service path
    filtered_files = {}
    for filepath, file_data in coverage_data["files"].items():
        if service in filepath:
            filtered_files[filepath] = file_data

    # Recalculate totals
    total_covered = 0
    total_lines = 0

    for filepath, file_data in filtered_files.items():
        if isinstance(file_data, dict):
            if "summary" in file_data:
                total_covered += file_data["summary"].get("covered_lines", 0)
                total_lines += file_data["summary"].get("num_statements", 0)
            elif "lines" in file_data:
                total_covered += file_data["lines"].get("covered", 0)
                total_lines += file_data["lines"].get("total", 0)

    percent = (total_covered / total_lines * 100) if total_lines > 0 else 0

    return {
        "format": coverage_data.get("format", "unknown"),
        "totals": {
            "lines_covered": total_covered,
            "lines_total": total_lines,
            "percent": round(percent, 2),
        },
        "files": filtered_files,
    }


def _generate_report(
    coverage_data: dict[str, Any],
    default_threshold: int,
    critical_threshold: int,
    guardrail_id: int | None = None,
) -> dict[str, Any]:
    """Generate coverage report.

    Args:
        coverage_data: Normalized coverage data
        default_threshold: Default coverage threshold
        critical_threshold: Critical path threshold
        guardrail_id: Optional guardrail ID to focus on

    Returns:
        Coverage report dictionary
    """
    totals = coverage_data.get("totals", {})
    percent = totals.get("percent", 0)

    # Determine if coverage passes thresholds
    passes_default = percent >= default_threshold
    passes_critical = percent >= critical_threshold

    report = {
        "coverage_percent": percent,
        "lines_covered": totals.get("lines_covered", 0),
        "lines_total": totals.get("lines_total", 0),
        "threshold_default": default_threshold,
        "threshold_critical": critical_threshold,
        "passes_default": passes_default,
        "passes_critical": passes_critical,
        "status": "PASS" if passes_default else "FAIL",
        "files": [],
    }

    # Add file-level details
    for filepath, file_data in coverage_data.get("files", {}).items():
        if isinstance(file_data, dict):
            if "summary" in file_data:
                file_percent = file_data["summary"].get("percent_covered", 0)
            elif "lines" in file_data:
                file_percent = file_data["lines"].get("pct", 0)
            else:
                file_percent = 0

            report["files"].append(
                {
                    "path": filepath,
                    "percent": file_percent,
                    "passes": file_percent >= default_threshold,
                }
            )

    # Sort files by coverage (lowest first)
    report["files"].sort(key=lambda x: x["percent"])

    return report


def _display_report(report: dict[str, Any], verbose: bool = False) -> None:
    """Display coverage report.

    Args:
        report: Coverage report dictionary
        verbose: If True, show all files instead of just lowest 10
    """
    console.print()

    # Overall status
    percent = report["coverage_percent"]
    threshold = report["threshold_default"]

    if report["status"] == "PASS":
        console.print(
            f"[bold green]Coverage: {percent:.1f}%[/bold green] (threshold: {threshold}%)"
        )
    else:
        console.print(f"[bold red]Coverage: {percent:.1f}%[/bold red] (threshold: {threshold}%)")

    console.print(f"Lines: {report['lines_covered']}/{report['lines_total']}")

    # Files table (show lowest coverage files, or all files in verbose mode)
    if report["files"]:
        console.print()
        title = "All Files by Coverage" if verbose else "Files by Coverage (Lowest 10)"
        table = Table(title=title, show_header=True, header_style="bold")
        table.add_column("File", style="cyan")
        table.add_column("Coverage", justify="right")
        table.add_column("Status")

        # Show all files in verbose mode, or bottom 10 otherwise
        files_to_show = report["files"] if verbose else report["files"][:10]
        for file_info in files_to_show:
            file_percent = file_info["percent"]
            passes = file_info["passes"]

            if passes:
                status = "[green]PASS[/green]"
                pct_style = "green"
            else:
                status = "[red]FAIL[/red]"
                pct_style = "red"

            table.add_row(
                file_info["path"],
                f"[{pct_style}]{file_percent:.1f}%[/{pct_style}]",
                status,
            )

        console.print(table)

        if not verbose and len(report["files"]) > 10:
            extra = len(report["files"]) - 10
            console.print(f"[dim]... and {extra} more files (use --verbose to show all)[/dim]")

    # Guardrail status
    console.print()
    if report["passes_default"]:
        console.print("[green]Guardrail #1 (Testing Coverage): SATISFIED[/green]")
    else:
        gap = threshold - percent
        console.print("[red]Guardrail #1 (Testing Coverage): NOT SATISFIED[/red]")
        console.print(f"[dim]Need {gap:.1f}% more coverage to meet threshold[/dim]")


def save_coverage_snapshot(
    name: str,
    report: dict[str, Any],
    project_root: Path | None = None,
) -> Path:
    """Save current coverage as a named snapshot.

    Args:
        name: Snapshot name (e.g., 'baseline', 'main', 'pr-123')
        report: Coverage report from report_coverage()
        project_root: Project root directory

    Returns:
        Path to saved snapshot file
    """
    if project_root is None:
        project_root = Path.cwd()

    snapshots_dir = project_root / ".ldf" / "coverage-snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)

    # Create snapshot with timestamp
    from datetime import datetime

    snapshot = {
        "name": name,
        "saved_at": datetime.now().isoformat(),
        "coverage_percent": report.get("coverage_percent", 0),
        "lines_covered": report.get("lines_covered", 0),
        "lines_total": report.get("lines_total", 0),
        "threshold_default": report.get("threshold_default", 80),
        "files": report.get("files", []),
    }

    snapshot_path = snapshots_dir / f"{name}.json"
    with open(snapshot_path, "w") as f:
        json.dump(snapshot, f, indent=2)

    console.print(f"\n[green]✓[/green] Saved coverage snapshot: {snapshot_path}")
    return snapshot_path


def compare_coverage(
    target: str,
    service: str | None = None,
    project_root: Path | None = None,
) -> dict[str, Any]:
    """Compare current coverage with a saved snapshot or file.

    Args:
        target: Snapshot name or file path
        service: Optional service filter
        project_root: Project root directory

    Returns:
        Comparison report
    """
    if project_root is None:
        project_root = Path.cwd()

    # Load baseline (target)
    baseline_path: Path
    if target.endswith(".json") or "/" in target:
        # Treat as file path
        baseline_path = Path(target)
        if not baseline_path.is_absolute():
            baseline_path = project_root / baseline_path
    else:
        # Treat as snapshot name
        baseline_path = project_root / ".ldf" / "coverage-snapshots" / f"{target}.json"

    if not baseline_path.exists():
        console.print(f"[red]Error: Coverage baseline not found: {baseline_path}[/red]")
        console.print("\nAvailable snapshots:")
        snapshots_dir = project_root / ".ldf" / "coverage-snapshots"
        if snapshots_dir.exists():
            for snapshot_file in snapshots_dir.glob("*.json"):
                console.print(f"  - {snapshot_file.stem}")
        else:
            console.print("  [dim]No snapshots saved yet[/dim]")
        return {"status": "ERROR", "error": "Baseline not found"}

    try:
        with open(baseline_path) as f:
            baseline = json.load(f)
    except json.JSONDecodeError as e:
        console.print(f"[red]Error: Invalid JSON in baseline file: {e}[/red]")
        return {"status": "ERROR", "error": "Invalid baseline JSON"}

    # Get current coverage
    coverage_data = _find_coverage_data(project_root)
    if coverage_data is None:
        console.print("[red]Error: No current coverage data found[/red]")
        return {"status": "ERROR", "error": "No current coverage"}

    if service:
        coverage_data = _filter_by_service(coverage_data, service)

    current_report = _generate_report(coverage_data, 80, 90)

    # Calculate diffs
    baseline_percent = baseline.get("coverage_percent", 0)
    current_percent = current_report.get("coverage_percent", 0)
    percent_delta = current_percent - baseline_percent

    baseline_lines = baseline.get("lines_covered", 0)
    current_lines = current_report.get("lines_covered", 0)
    lines_delta = current_lines - baseline_lines

    # Display comparison
    console.print()
    console.print(f"[bold]Coverage Comparison:[/bold] current vs {target}")
    console.print("━" * 50)

    # Overall delta
    delta_color = "green" if percent_delta >= 0 else "red"
    delta_sign = "+" if percent_delta >= 0 else ""
    delta_str = f"{delta_sign}{percent_delta:.1f}%, {delta_sign}{lines_delta} lines"
    console.print(
        f"Overall: {baseline_percent:.1f}% → {current_percent:.1f}% "
        f"[{delta_color}]({delta_str})[/{delta_color}]"
    )
    console.print()

    # Build file maps
    baseline_files = {f.get("path", ""): f for f in baseline.get("files", [])}
    current_files = {f.get("path", ""): f for f in current_report.get("files", [])}

    all_paths = set(baseline_files.keys()) | set(current_files.keys())

    improved: list[tuple[str, float, float, int]] = []
    regressed: list[tuple[str, float, float, int]] = []
    new_files: list[tuple[str, float, int]] = []
    removed_files: list[str] = []

    for path in all_paths:
        baseline_file = baseline_files.get(path)
        current_file = current_files.get(path)

        if baseline_file and not current_file:
            removed_files.append(path)
        elif current_file and not baseline_file:
            pct = current_file.get("percent", 0)
            lines = int(current_file.get("percent", 0) * 100)  # Rough estimate
            new_files.append((path, pct, lines))
        else:
            # Both exist - compare
            baseline_pct = baseline_file.get("percent", 0) if baseline_file else 0
            current_pct = current_file.get("percent", 0) if current_file else 0
            delta = current_pct - baseline_pct

            if delta > 0.5:  # More than 0.5% improvement
                improved.append((path, baseline_pct, current_pct, int(delta)))
            elif delta < -0.5:  # More than 0.5% regression
                regressed.append((path, baseline_pct, current_pct, int(abs(delta))))

    # Show improved files
    if improved:
        improved.sort(key=lambda x: x[3], reverse=True)  # Sort by delta
        console.print(f"[green]Improved ({len(improved)} files):[/green]")
        for path, old_pct, new_pct, _ in improved[:5]:
            d = new_pct - old_pct
            console.print(f"  {path}: {old_pct:.0f}% → {new_pct:.0f}% [green](+{d:.0f}%)[/green]")
        if len(improved) > 5:
            console.print(f"  [dim]... and {len(improved) - 5} more[/dim]")
        console.print()

    # Show regressed files
    if regressed:
        regressed.sort(key=lambda x: x[3], reverse=True)  # Sort by delta
        console.print(f"[red]Regressed ({len(regressed)} files):[/red]")
        for path, old_pct, new_pct, _ in regressed[:5]:
            delta = old_pct - new_pct
            console.print(f"  {path}: {old_pct:.0f}% → {new_pct:.0f}% [red](-{delta:.0f}%)[/red]")
        if len(regressed) > 5:
            console.print(f"  [dim]... and {len(regressed) - 5} more[/dim]")
        console.print()

    # Show new files
    if new_files:
        console.print(f"[cyan]New files ({len(new_files)}):[/cyan]")
        for path, pct, _ in new_files[:3]:
            console.print(f"  {path}: {pct:.0f}%")
        if len(new_files) > 3:
            console.print(f"  [dim]... and {len(new_files) - 3} more[/dim]")
        console.print()

    # Show removed files
    if removed_files:
        console.print(f"[dim]Removed files ({len(removed_files)}):[/dim]")
        for path in removed_files[:3]:
            console.print(f"  {path}")
        if len(removed_files) > 3:
            console.print(f"  [dim]... and {len(removed_files) - 3} more[/dim]")
        console.print()

    console.print("━" * 50)

    # Summary
    if percent_delta > 0:
        status = "improved"
    elif percent_delta < 0:
        status = "regressed"
    else:
        status = "unchanged"
    return {
        "status": "OK",
        "comparison_status": status,
        "baseline_percent": baseline_percent,
        "current_percent": current_percent,
        "percent_delta": percent_delta,
        "lines_delta": lines_delta,
        "improved_count": len(improved),
        "regressed_count": len(regressed),
        "new_files_count": len(new_files),
        "removed_files_count": len(removed_files),
    }


def upload_coverage(
    destination: str,
    report: dict[str, Any],
    project_root: Path | None = None,
) -> bool:
    """Upload coverage report to specified destination.

    Args:
        destination: Upload destination - 'artifact', 's3://bucket/path', or 'file://path'
        report: Coverage report to upload
        project_root: Project root directory

    Returns:
        True if upload succeeded, False otherwise
    """
    if project_root is None:
        project_root = Path.cwd()

    # Prepare coverage data
    from datetime import datetime

    upload_data = {
        "uploaded_at": datetime.now().isoformat(),
        "coverage_percent": report.get("coverage_percent", 0),
        "lines_covered": report.get("lines_covered", 0),
        "lines_total": report.get("lines_total", 0),
        "status": report.get("status", "UNKNOWN"),
        "files": report.get("files", []),
    }

    if destination == "artifact":
        # GitHub Actions artifact upload
        return _upload_to_artifact(upload_data, project_root)
    elif destination.startswith("s3://"):
        # S3 upload
        return _upload_to_s3(upload_data, destination)
    elif destination.startswith("file://"):
        # Local file copy
        return _upload_to_file(upload_data, destination[7:])  # Remove 'file://' prefix
    else:
        console.print(f"[red]Error: Unknown upload destination: {destination}[/red]")
        console.print("\nSupported destinations:")
        console.print("  artifact     - GitHub Actions artifact")
        console.print("  s3://bucket/path - AWS S3")
        console.print("  file://path  - Local file")
        return False


def _upload_to_artifact(data: dict[str, Any], project_root: Path) -> bool:
    """Upload coverage to GitHub Actions artifact."""
    # Check if we're in GitHub Actions
    github_output = os.environ.get("GITHUB_OUTPUT")
    if not github_output:
        console.print("[yellow]Warning: GITHUB_OUTPUT not set - not in GitHub Actions?[/yellow]")

    # Write to artifact path
    artifact_dir = project_root / "coverage-artifact"
    artifact_dir.mkdir(exist_ok=True)

    artifact_file = artifact_dir / "coverage.json"
    with open(artifact_file, "w") as f:
        json.dump(data, f, indent=2)

    console.print(f"\n[green]✓[/green] Coverage artifact created: {artifact_file}")
    console.print("[dim]Add the following step to your workflow to upload:[/dim]")
    console.print("""
    - uses: actions/upload-artifact@v4
      with:
        name: coverage-report
        path: coverage-artifact/
    """)

    return True


def _upload_to_s3(data: dict[str, Any], s3_uri: str) -> bool:
    """Upload coverage to S3."""
    try:
        import boto3  # type: ignore[import-not-found]
    except ImportError:
        console.print("[red]Error: boto3 not installed. Run: pip install boto3[/red]")
        return False

    # Parse S3 URI
    # s3://bucket/path/to/file.json
    parts = s3_uri[5:].split("/", 1)
    if len(parts) < 2:
        console.print(f"[red]Error: Invalid S3 URI: {s3_uri}[/red]")
        console.print("Expected format: s3://bucket/path/to/file.json")
        return False

    bucket = parts[0]
    key = parts[1]

    try:
        s3 = boto3.client("s3")
        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=json.dumps(data, indent=2),
            ContentType="application/json",
        )
        console.print(f"\n[green]✓[/green] Coverage uploaded to: {s3_uri}")
        return True
    except Exception as e:
        console.print(f"[red]Error uploading to S3: {e}[/red]")
        return False


def _upload_to_file(data: dict[str, Any], path: str) -> bool:
    """Copy coverage to local file."""
    file_path = Path(path)

    # Create parent directories if needed
    file_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)
        console.print(f"\n[green]✓[/green] Coverage saved to: {file_path}")
        return True
    except OSError as e:
        console.print(f"[red]Error writing file: {e}[/red]")
        return False
