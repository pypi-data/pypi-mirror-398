"""LDF Doctor - Diagnose common setup issues."""

import json
import subprocess
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

import yaml

from ldf.utils.console import console


class CheckStatus(Enum):
    """Status of a diagnostic check."""

    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


@dataclass
class CheckResult:
    """Result of a single diagnostic check."""

    name: str
    status: CheckStatus
    message: str
    fix_hint: str | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON output."""
        result = {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
        }
        if self.fix_hint:
            result["fix_hint"] = self.fix_hint
        return result


@dataclass
class DoctorReport:
    """Complete doctor report with all check results."""

    checks: list[CheckResult] = field(default_factory=list)

    @property
    def passed(self) -> int:
        """Count of passed checks."""
        return sum(1 for c in self.checks if c.status == CheckStatus.PASS)

    @property
    def warnings(self) -> int:
        """Count of warnings."""
        return sum(1 for c in self.checks if c.status == CheckStatus.WARN)

    @property
    def failed(self) -> int:
        """Count of failures."""
        return sum(1 for c in self.checks if c.status == CheckStatus.FAIL)

    @property
    def success(self) -> bool:
        """True if no failures."""
        return self.failed == 0

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON output."""
        return {
            "checks": [c.to_dict() for c in self.checks],
            "summary": {
                "passed": self.passed,
                "warnings": self.warnings,
                "failed": self.failed,
                "success": self.success,
            },
        }


def check_project_structure(project_root: Path) -> CheckResult:
    """Check that .ldf/ directory exists with required subdirectories."""
    ldf_dir = project_root / ".ldf"

    if not ldf_dir.exists():
        return CheckResult(
            name="Project structure",
            status=CheckStatus.FAIL,
            message=".ldf/ directory not found",
            fix_hint="Run: ldf init",
        )

    required_dirs = ["specs", "question-packs", "templates", "macros"]
    missing = [d for d in required_dirs if not (ldf_dir / d).exists()]

    if missing:
        return CheckResult(
            name="Project structure",
            status=CheckStatus.WARN,
            message=f"Missing directories: {', '.join(missing)}",
            fix_hint="Run: ldf init --repair",
        )

    return CheckResult(
        name="Project structure",
        status=CheckStatus.PASS,
        message=".ldf/ exists with required dirs",
    )


def check_config(project_root: Path) -> CheckResult:
    """Check that config.yaml exists and is valid."""
    config_path = project_root / ".ldf" / "config.yaml"

    if not config_path.exists():
        return CheckResult(
            name="Configuration",
            status=CheckStatus.FAIL,
            message="config.yaml not found",
            fix_hint="Run: ldf init",
        )

    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)

        if not isinstance(config, dict):
            return CheckResult(
                name="Configuration",
                status=CheckStatus.FAIL,
                message="config.yaml is not a valid YAML mapping",
                fix_hint="Check config.yaml syntax",
            )

        # Check required keys
        required_keys = ["version"]
        missing_keys = [k for k in required_keys if k not in config]
        if missing_keys:
            return CheckResult(
                name="Configuration",
                status=CheckStatus.WARN,
                message=f"Missing keys: {', '.join(missing_keys)}",
                fix_hint="Run: ldf update",
            )

        return CheckResult(
            name="Configuration",
            status=CheckStatus.PASS,
            message="config.yaml valid",
        )

    except yaml.YAMLError as e:
        return CheckResult(
            name="Configuration",
            status=CheckStatus.FAIL,
            message=f"YAML parse error: {e}",
            fix_hint="Fix YAML syntax in config.yaml",
        )


def check_guardrails(project_root: Path) -> CheckResult:
    """Check that guardrails.yaml exists and is valid."""
    guardrails_path = project_root / ".ldf" / "guardrails.yaml"

    if not guardrails_path.exists():
        return CheckResult(
            name="Guardrails",
            status=CheckStatus.FAIL,
            message="guardrails.yaml not found",
            fix_hint="Run: ldf init",
        )

    try:
        with open(guardrails_path) as f:
            guardrails = yaml.safe_load(f)

        if not isinstance(guardrails, dict):
            return CheckResult(
                name="Guardrails",
                status=CheckStatus.FAIL,
                message="guardrails.yaml is not a valid YAML mapping",
                fix_hint="Check guardrails.yaml syntax",
            )

        # Count active guardrails
        preset = guardrails.get("preset", "custom")

        return CheckResult(
            name="Guardrails",
            status=CheckStatus.PASS,
            message=f"guardrails.yaml valid (preset: {preset})",
        )

    except yaml.YAMLError as e:
        return CheckResult(
            name="Guardrails",
            status=CheckStatus.FAIL,
            message=f"YAML parse error: {e}",
            fix_hint="Fix YAML syntax in guardrails.yaml",
        )


def check_question_packs(project_root: Path) -> CheckResult:
    """Check that configured question packs exist."""
    config_path = project_root / ".ldf" / "config.yaml"
    packs_dir = project_root / ".ldf" / "question-packs"

    if not config_path.exists():
        return CheckResult(
            name="Question packs",
            status=CheckStatus.WARN,
            message="Cannot check packs - config.yaml missing",
        )

    try:
        with open(config_path) as f:
            config = yaml.safe_load(f) or {}

        configured_packs = config.get("question_packs", [])
        if not configured_packs:
            return CheckResult(
                name="Question packs",
                status=CheckStatus.PASS,
                message="No question packs configured",
            )

        if not packs_dir.exists():
            return CheckResult(
                name="Question packs",
                status=CheckStatus.FAIL,
                message="question-packs/ directory not found",
                fix_hint="Run: ldf init --repair",
            )

        # Check each configured pack exists
        missing = []
        for pack in configured_packs:
            pack_file = packs_dir / f"{pack}.yaml"
            if not pack_file.exists():
                missing.append(pack)

        if missing:
            return CheckResult(
                name="Question packs",
                status=CheckStatus.WARN,
                message=f"Missing packs: {', '.join(missing)}",
                fix_hint=f"Run: ldf add-pack {missing[0]}",
            )

        return CheckResult(
            name="Question packs",
            status=CheckStatus.PASS,
            message=f"{len(configured_packs)}/{len(configured_packs)} packs found",
        )

    except yaml.YAMLError:
        return CheckResult(
            name="Question packs",
            status=CheckStatus.WARN,
            message="Cannot check packs - config.yaml invalid",
        )


def check_mcp_servers(project_root: Path) -> CheckResult:
    """Check that configured MCP servers are available."""
    config_path = project_root / ".ldf" / "config.yaml"

    if not config_path.exists():
        return CheckResult(
            name="MCP servers",
            status=CheckStatus.WARN,
            message="Cannot check MCP - config.yaml missing",
        )

    try:
        with open(config_path) as f:
            config = yaml.safe_load(f) or {}

        configured_servers = config.get("mcp_servers", [])
        if not configured_servers:
            return CheckResult(
                name="MCP servers",
                status=CheckStatus.PASS,
                message="No MCP servers configured",
            )

        # Check each server directory exists in the package
        from importlib.resources import files

        try:
            mcp_servers_pkg = files("ldf._mcp_servers")
        except (ModuleNotFoundError, TypeError):
            return CheckResult(
                name="MCP servers",
                status=CheckStatus.WARN,
                message="Cannot locate MCP servers package",
            )

        missing = []
        for server in configured_servers:
            # Normalize to underscore format (new standard)
            server_dir = server.replace("-", "_")
            try:
                # Check if server.py exists in the server directory
                server_path = mcp_servers_pkg.joinpath(server_dir).joinpath("server.py")
                if not server_path.is_file():
                    missing.append(server)
            except (TypeError, AttributeError):
                # Fallback: check filesystem directly
                import ldf._mcp_servers

                pkg_dir = Path(ldf._mcp_servers.__file__).parent
                if not (pkg_dir / server_dir / "server.py").exists():
                    missing.append(server)

        if missing:
            return CheckResult(
                name="MCP servers",
                status=CheckStatus.WARN,
                message=f"Missing servers: {', '.join(missing)}",
                fix_hint="Check server names in config",
            )

        return CheckResult(
            name="MCP servers",
            status=CheckStatus.PASS,
            message=f"{len(configured_servers)} servers available",
        )

    except yaml.YAMLError:
        return CheckResult(
            name="MCP servers",
            status=CheckStatus.WARN,
            message="Cannot check MCP - config.yaml invalid",
        )


def check_required_deps() -> CheckResult:
    """Check that required dependencies are installed."""
    required = ["click", "yaml", "rich", "jinja2", "questionary"]
    missing = []

    for dep in required:
        try:
            if dep == "yaml":
                import yaml  # noqa: F401
            elif dep == "click":
                import click  # noqa: F401
            elif dep == "rich":
                import rich  # noqa: F401
            elif dep == "jinja2":
                import jinja2  # noqa: F401
            elif dep == "questionary":
                import questionary  # noqa: F401
        except ImportError:
            missing.append(dep)

    if missing:
        return CheckResult(
            name="Required dependencies",
            status=CheckStatus.FAIL,
            message=f"Missing: {', '.join(missing)}",
            fix_hint="Run: pip install llm-ldf",
        )

    return CheckResult(
        name="Required dependencies",
        status=CheckStatus.PASS,
        message="All required packages installed",
    )


def check_mcp_deps(project_root: Path) -> CheckResult:
    """Check that MCP dependencies are installed if MCP servers are configured."""
    config_path = project_root / ".ldf" / "config.yaml"

    # If no config or no MCP servers, skip this check
    if not config_path.exists():
        return CheckResult(
            name="MCP dependencies",
            status=CheckStatus.PASS,
            message="No MCP servers configured",
        )

    try:
        with open(config_path) as f:
            config = yaml.safe_load(f) or {}

        if not config.get("mcp_servers"):
            return CheckResult(
                name="MCP dependencies",
                status=CheckStatus.PASS,
                message="No MCP servers configured",
            )

        # Check MCP package
        missing = []
        try:
            import mcp  # type: ignore[import-not-found]  # noqa: F401
        except ImportError:
            missing.append("mcp")

        # Check coverage package (needed by coverage_reporter)
        if "coverage_reporter" in config.get("mcp_servers", []):
            try:
                import coverage  # noqa: F401
            except ImportError:
                missing.append("coverage")

        if missing:
            return CheckResult(
                name="MCP dependencies",
                status=CheckStatus.WARN,
                message=f"Missing: {', '.join(missing)}",
                fix_hint="Run: pip install 'ldf[mcp]'",
            )

        return CheckResult(
            name="MCP dependencies",
            status=CheckStatus.PASS,
            message="MCP packages installed",
        )

    except yaml.YAMLError:
        return CheckResult(
            name="MCP dependencies",
            status=CheckStatus.WARN,
            message="Cannot check - config.yaml invalid",
        )


def check_git_hooks(project_root: Path) -> CheckResult:
    """Check git hooks installation status."""
    git_dir = project_root / ".git"
    hooks_dir = git_dir / "hooks"
    pre_commit = hooks_dir / "pre-commit"

    if not git_dir.exists():
        return CheckResult(
            name="Git hooks",
            status=CheckStatus.PASS,
            message="Not a git repository (hooks N/A)",
        )

    if not pre_commit.exists():
        return CheckResult(
            name="Git hooks",
            status=CheckStatus.PASS,
            message="No pre-commit hook installed",
        )

    # Check if it's an LDF hook
    try:
        content = pre_commit.read_text()
        if "ldf" in content.lower():
            return CheckResult(
                name="Git hooks",
                status=CheckStatus.PASS,
                message="LDF pre-commit hook installed",
            )
        else:
            return CheckResult(
                name="Git hooks",
                status=CheckStatus.PASS,
                message="Non-LDF pre-commit hook present",
            )
    except OSError:
        return CheckResult(
            name="Git hooks",
            status=CheckStatus.WARN,
            message="Cannot read pre-commit hook",
        )


def check_mcp_json(project_root: Path) -> CheckResult:
    """Check if .agent/mcp.json is up to date with config."""
    mcp_json_path = project_root / ".agent" / "mcp.json"
    config_path = project_root / ".ldf" / "config.yaml"

    if not mcp_json_path.exists():
        return CheckResult(
            name="MCP config file",
            status=CheckStatus.PASS,
            message=".agent/mcp.json not present (optional)",
        )

    if not config_path.exists():
        return CheckResult(
            name="MCP config file",
            status=CheckStatus.WARN,
            message=".agent/mcp.json exists but no LDF config",
        )

    try:
        with open(config_path) as f:
            config = yaml.safe_load(f) or {}

        with open(mcp_json_path) as f:
            mcp_json = json.load(f)

        # Normalize to underscore form (both hyphen and underscore variants accepted in config)
        configured_servers = set(s.replace("-", "_") for s in config.get("mcp_servers", []))
        if not configured_servers:
            return CheckResult(
                name="MCP config file",
                status=CheckStatus.PASS,
                message=".agent/mcp.json exists (no LDF servers configured)",
            )

        # Check if configured servers are in mcp.json
        mcp_servers = mcp_json.get("mcpServers", {})
        json_servers = set()
        for name in mcp_servers:
            args = mcp_servers[name].get("args", [])
            args_str = str(args)
            # Check for both Python module paths and file paths
            is_ldf_server = (
                "ldf._mcp_servers" in args_str  # Python module path
                or "_mcp_servers" in args_str  # File path
                or "ldf/_mcp_servers" in args_str  # Relative file path
            )
            if is_ldf_server:
                # Normalize to underscore form (the new standard)
                json_servers.add(name.replace("-", "_"))

        missing_from_json = configured_servers - json_servers
        if missing_from_json:
            return CheckResult(
                name="MCP config file",
                status=CheckStatus.WARN,
                message=f".agent/mcp.json missing: {', '.join(missing_from_json)}",
                fix_hint="Run: ldf mcp-config > .agent/mcp.json",
            )

        return CheckResult(
            name="MCP config file",
            status=CheckStatus.PASS,
            message=".agent/mcp.json up to date",
        )

    except (json.JSONDecodeError, yaml.YAMLError) as e:
        return CheckResult(
            name="MCP config file",
            status=CheckStatus.WARN,
            message=f"Parse error: {e}",
        )


def run_doctor(
    project_root: Path | None = None,
    fix: bool = False,
) -> DoctorReport:
    """Run all diagnostic checks.

    Args:
        project_root: Project directory (defaults to cwd)
        fix: Attempt to auto-fix issues where possible

    Returns:
        DoctorReport with all check results
    """
    if project_root is None:
        project_root = Path.cwd()

    report = DoctorReport()

    # Run all checks
    report.checks.append(check_project_structure(project_root))
    report.checks.append(check_config(project_root))
    report.checks.append(check_guardrails(project_root))
    report.checks.append(check_question_packs(project_root))
    report.checks.append(check_mcp_servers(project_root))
    report.checks.append(check_required_deps())
    report.checks.append(check_mcp_deps(project_root))
    report.checks.append(check_git_hooks(project_root))
    report.checks.append(check_mcp_json(project_root))

    # Auto-fix if requested
    if fix:
        for check in report.checks:
            if check.status == CheckStatus.FAIL and check.fix_hint:
                if "ldf init" in check.fix_hint:
                    # Run init --repair for fixable issues
                    try:
                        subprocess.run(
                            [sys.executable, "-m", "ldf", "init", "--repair", "--yes"],
                            cwd=project_root,
                            capture_output=True,
                        )
                    except Exception:
                        pass

    return report


def print_report(report: DoctorReport) -> None:
    """Print doctor report to console."""

    console.print()
    console.print("[bold]LDF Doctor[/bold]")
    console.print("━" * 50)

    status_icons = {
        CheckStatus.PASS: "[green]✓[/green]",
        CheckStatus.WARN: "[yellow]⚠[/yellow]",
        CheckStatus.FAIL: "[red]✗[/red]",
    }

    for check in report.checks:
        icon = status_icons[check.status]
        console.print(f"{icon} {check.name:20} {check.message}")
        if check.fix_hint and check.status != CheckStatus.PASS:
            console.print(f"  [dim]→ {check.fix_hint}[/dim]")

    console.print("━" * 50)
    console.print(
        f"[bold]{report.passed}[/bold] passed, "
        f"[bold yellow]{report.warnings}[/bold yellow] warnings, "
        f"[bold red]{report.failed}[/bold red] failed"
    )
    console.print()
