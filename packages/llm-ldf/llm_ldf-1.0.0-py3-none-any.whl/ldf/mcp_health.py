"""LDF MCP Health - Check MCP server readiness."""

import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

from ldf.utils.console import console


class HealthStatus(Enum):
    """Health status of an MCP server."""

    READY = "ready"
    WARNING = "warning"
    SKIP = "skip"
    ERROR = "error"


@dataclass
class ServerHealth:
    """Health check result for a single MCP server."""

    name: str
    status: HealthStatus
    message: str
    details: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON output."""
        result: dict[str, Any] = {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
        }
        if self.details:
            result["details"] = self.details
        return result


@dataclass
class HealthReport:
    """Complete health report for all MCP servers."""

    servers: list[ServerHealth]

    @property
    def ready_count(self) -> int:
        """Count of ready servers."""
        return sum(1 for s in self.servers if s.status == HealthStatus.READY)

    @property
    def skipped_count(self) -> int:
        """Count of skipped servers."""
        return sum(1 for s in self.servers if s.status == HealthStatus.SKIP)

    @property
    def error_count(self) -> int:
        """Count of servers with errors."""
        return sum(1 for s in self.servers if s.status == HealthStatus.ERROR)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON output."""
        return {
            "servers": [s.to_dict() for s in self.servers],
            "summary": {
                "ready": self.ready_count,
                "skipped": self.skipped_count,
                "errors": self.error_count,
            },
        }


def check_spec_inspector(project_root: Path) -> ServerHealth:
    """Check spec_inspector server health.

    Verifies:
    - .ldf/specs/ directory readable
    - guardrails.yaml valid
    - Can count specs and guardrails
    """
    ldf_dir = project_root / ".ldf"
    specs_dir = ldf_dir / "specs"
    guardrails_path = ldf_dir / "guardrails.yaml"

    # Check specs directory
    if not specs_dir.exists():
        return ServerHealth(
            name="spec_inspector",
            status=HealthStatus.WARNING,
            message="No specs directory",
            details={"specs_count": 0},
        )

    # Count specs
    spec_count = 0
    for item in specs_dir.iterdir():
        if item.is_dir() and (item / "requirements.md").exists():
            spec_count += 1

    # Check guardrails
    guardrail_count = 0
    try:
        if guardrails_path.exists():
            with open(guardrails_path) as f:
                guardrails = yaml.safe_load(f) or {}
            # Count base guardrails (8 core)
            guardrail_count = 8  # Core guardrails
            # Add preset-specific if configured
            preset = guardrails.get("preset", "custom")
            preset_counts = {"saas": 5, "fintech": 7, "healthcare": 6, "api-only": 4}
            guardrail_count += preset_counts.get(preset, 0)
    except yaml.YAMLError:
        return ServerHealth(
            name="spec_inspector",
            status=HealthStatus.ERROR,
            message="guardrails.yaml invalid",
        )

    return ServerHealth(
        name="spec_inspector",
        status=HealthStatus.READY,
        message=f"{spec_count} specs, {guardrail_count} guardrails",
        details={"specs_count": spec_count, "guardrails_count": guardrail_count},
    )


def check_coverage_reporter(project_root: Path) -> ServerHealth:
    """Check coverage_reporter server health.

    Verifies:
    - Coverage file exists and is parseable
    - Can read overall coverage percentage
    """
    # Check common coverage file locations
    coverage_locations = [
        project_root / "coverage.json",
        project_root / ".coverage.json",
        project_root / "htmlcov" / "status.json",
        project_root / "coverage" / "coverage-final.json",
        project_root / ".ldf" / "coverage.json",
    ]

    # Also check COVERAGE_FILE env var
    env_coverage = os.environ.get("COVERAGE_FILE")
    if env_coverage:
        coverage_locations.insert(0, Path(env_coverage))

    coverage_path = None
    for loc in coverage_locations:
        if loc.exists():
            coverage_path = loc
            break

    if not coverage_path:
        return ServerHealth(
            name="coverage_reporter",
            status=HealthStatus.WARNING,
            message="No coverage file found",
            details={"searched": [str(loc) for loc in coverage_locations[:3]]},
        )

    # Try to parse coverage
    try:
        import json

        with open(coverage_path) as f:
            data = json.load(f)

        # Extract overall percentage based on format
        overall = None
        if "totals" in data and "percent_covered" in data["totals"]:
            # pytest-cov format
            overall = data["totals"]["percent_covered"]
        elif "total" in data:
            # Jest format
            total = data["total"]
            if "lines" in total and "pct" in total["lines"]:
                overall = total["lines"]["pct"]

        if overall is not None:
            return ServerHealth(
                name="coverage_reporter",
                status=HealthStatus.READY,
                message=f"{overall:.1f}% coverage",
                details={"overall": overall, "file": str(coverage_path)},
            )
        else:
            return ServerHealth(
                name="coverage_reporter",
                status=HealthStatus.WARNING,
                message="Coverage file format not recognized",
                details={"file": str(coverage_path)},
            )

    except (json.JSONDecodeError, OSError) as e:
        return ServerHealth(
            name="coverage_reporter",
            status=HealthStatus.ERROR,
            message=f"Cannot read coverage: {e}",
        )


def check_db_inspector(project_root: Path) -> ServerHealth:
    """Check db_inspector server health.

    Verifies:
    - DATABASE_URL environment variable is set
    """
    database_url = os.environ.get("DATABASE_URL")

    if not database_url:
        return ServerHealth(
            name="db_inspector",
            status=HealthStatus.SKIP,
            message="DATABASE_URL not configured",
        )

    # Basic URL validation (don't actually connect)
    if database_url.startswith(("postgres://", "postgresql://")):
        return ServerHealth(
            name="db_inspector",
            status=HealthStatus.READY,
            message="PostgreSQL configured",
            details={"type": "postgresql"},
        )
    else:
        return ServerHealth(
            name="db_inspector",
            status=HealthStatus.WARNING,
            message="Unknown database type",
        )


def run_mcp_health(project_root: Path | None = None) -> HealthReport:
    """Run health checks for all configured MCP servers.

    Args:
        project_root: Project directory (defaults to cwd)

    Returns:
        HealthReport with all server statuses
    """
    if project_root is None:
        project_root = Path.cwd()

    # Load config to see which servers are enabled
    config_path = project_root / ".ldf" / "config.yaml"
    configured_servers = []

    if config_path.exists():
        try:
            with open(config_path) as f:
                config = yaml.safe_load(f) or {}
            configured_servers = config.get("mcp_servers", [])
        except yaml.YAMLError:
            pass

    # Default servers if none configured
    if not configured_servers:
        configured_servers = ["spec_inspector", "coverage_reporter"]

    # Run health checks
    report = HealthReport(servers=[])

    server_checks = {
        "spec_inspector": check_spec_inspector,
        "coverage_reporter": check_coverage_reporter,
        "db_inspector": check_db_inspector,
    }

    for server in configured_servers:
        check_fn = server_checks.get(server)
        if check_fn:
            health = check_fn(project_root)
            report.servers.append(health)
        else:
            report.servers.append(
                ServerHealth(
                    name=server,
                    status=HealthStatus.SKIP,
                    message="Unknown server type",
                )
            )

    return report


def print_health_report(report: HealthReport) -> None:
    """Print health report to console."""
    from rich.table import Table

    console.print()
    console.print("[bold]MCP Server Health[/bold]")
    console.print("━" * 50)

    table = Table(show_header=True, header_style="bold")
    table.add_column("Server", style="cyan")
    table.add_column("Status")
    table.add_column("Details")

    status_icons = {
        HealthStatus.READY: "[green]✓ Ready[/green]",
        HealthStatus.WARNING: "[yellow]⚠ Warning[/yellow]",
        HealthStatus.SKIP: "[dim]○ Skip[/dim]",
        HealthStatus.ERROR: "[red]✗ Error[/red]",
    }

    for server in report.servers:
        icon = status_icons[server.status]
        table.add_row(server.name, icon, server.message)

    console.print(table)
    console.print("━" * 50)
    console.print(
        f"[bold]{report.ready_count}[/bold] ready, [bold]{report.skipped_count}[/bold] skipped"
    )
    if report.error_count > 0:
        console.print(f"[bold red]{report.error_count}[/bold red] errors")
    console.print()
