"""Tests for ldf.mcp_health module."""

import json
from pathlib import Path

from ldf.mcp_health import (
    HealthReport,
    HealthStatus,
    ServerHealth,
    check_coverage_reporter,
    check_db_inspector,
    check_spec_inspector,
    print_health_report,
    run_mcp_health,
)


class TestCheckSpecInspector:
    """Tests for check_spec_inspector function."""

    def test_warns_without_specs_dir(self, temp_project: Path):
        """Test warning when specs directory doesn't exist."""
        specs_dir = temp_project / ".ldf" / "specs"
        if specs_dir.exists():
            specs_dir.rmdir()

        result = check_spec_inspector(temp_project)

        assert result.status == HealthStatus.WARNING
        assert "No specs directory" in result.message

    def test_returns_ready_with_specs(self, temp_project: Path):
        """Test ready status when specs exist."""
        specs_dir = temp_project / ".ldf" / "specs"
        specs_dir.mkdir(exist_ok=True)

        # Create a spec
        spec_dir = specs_dir / "test-spec"
        spec_dir.mkdir()
        (spec_dir / "requirements.md").write_text("# Test")

        result = check_spec_inspector(temp_project)

        assert result.status == HealthStatus.READY
        assert "1 specs" in result.message
        assert result.details is not None
        assert result.details["specs_count"] == 1

    def test_counts_guardrails(self, temp_project: Path):
        """Test counting guardrails."""
        specs_dir = temp_project / ".ldf" / "specs"
        specs_dir.mkdir(exist_ok=True)

        result = check_spec_inspector(temp_project)

        assert result.status == HealthStatus.READY
        assert "guardrails" in result.message
        assert result.details is not None
        assert result.details["guardrails_count"] >= 8  # Core guardrails

    def test_error_on_invalid_guardrails(self, temp_project: Path):
        """Test error when guardrails.yaml is invalid."""
        specs_dir = temp_project / ".ldf" / "specs"
        specs_dir.mkdir(exist_ok=True)

        guardrails_path = temp_project / ".ldf" / "guardrails.yaml"
        guardrails_path.write_text("invalid: yaml: [[[")

        result = check_spec_inspector(temp_project)

        assert result.status == HealthStatus.ERROR
        assert "guardrails.yaml invalid" in result.message


class TestCheckCoverageReporter:
    """Tests for check_coverage_reporter function."""

    def test_warns_without_coverage(self, temp_project: Path, monkeypatch):
        """Test warning when no coverage file exists."""
        monkeypatch.delenv("COVERAGE_FILE", raising=False)

        result = check_coverage_reporter(temp_project)

        assert result.status == HealthStatus.WARNING
        assert "No coverage file found" in result.message

    def test_returns_ready_with_pytest_cov(self, temp_project: Path, monkeypatch):
        """Test ready status with pytest-cov format."""
        monkeypatch.delenv("COVERAGE_FILE", raising=False)

        coverage_file = temp_project / "coverage.json"
        coverage_file.write_text(json.dumps({"totals": {"percent_covered": 85.5}}))

        result = check_coverage_reporter(temp_project)

        assert result.status == HealthStatus.READY
        assert "85.5% coverage" in result.message

    def test_returns_ready_with_jest(self, temp_project: Path, monkeypatch):
        """Test ready status with Jest format."""
        monkeypatch.delenv("COVERAGE_FILE", raising=False)

        coverage_file = temp_project / "coverage.json"
        coverage_file.write_text(json.dumps({"total": {"lines": {"pct": 75.0}}}))

        result = check_coverage_reporter(temp_project)

        assert result.status == HealthStatus.READY
        assert "75.0% coverage" in result.message

    def test_warns_with_unknown_format(self, temp_project: Path, monkeypatch):
        """Test warning with unknown coverage format."""
        monkeypatch.delenv("COVERAGE_FILE", raising=False)

        coverage_file = temp_project / "coverage.json"
        coverage_file.write_text(json.dumps({"some": "data"}))

        result = check_coverage_reporter(temp_project)

        assert result.status == HealthStatus.WARNING
        assert "format not recognized" in result.message

    def test_error_on_invalid_json(self, temp_project: Path, monkeypatch):
        """Test error when coverage file is invalid JSON."""
        monkeypatch.delenv("COVERAGE_FILE", raising=False)

        coverage_file = temp_project / "coverage.json"
        coverage_file.write_text("not valid json")

        result = check_coverage_reporter(temp_project)

        assert result.status == HealthStatus.ERROR
        assert "Cannot read coverage" in result.message

    def test_uses_env_coverage_file(self, temp_project: Path, monkeypatch):
        """Test using COVERAGE_FILE environment variable."""
        custom_file = temp_project / "custom_coverage.json"
        custom_file.write_text(json.dumps({"totals": {"percent_covered": 90.0}}))
        monkeypatch.setenv("COVERAGE_FILE", str(custom_file))

        result = check_coverage_reporter(temp_project)

        assert result.status == HealthStatus.READY
        assert "90.0% coverage" in result.message


class TestCheckDbInspector:
    """Tests for check_db_inspector function."""

    def test_skips_without_database_url(self, temp_project: Path, monkeypatch):
        """Test skip status when DATABASE_URL is not set."""
        monkeypatch.delenv("DATABASE_URL", raising=False)

        result = check_db_inspector(temp_project)

        assert result.status == HealthStatus.SKIP
        assert "DATABASE_URL not configured" in result.message

    def test_ready_with_postgres(self, temp_project: Path, monkeypatch):
        """Test ready status with PostgreSQL URL."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/test")

        result = check_db_inspector(temp_project)

        assert result.status == HealthStatus.READY
        assert "PostgreSQL configured" in result.message
        assert result.details is not None
        assert result.details["type"] == "postgresql"

    def test_ready_with_postgres_alternate(self, temp_project: Path, monkeypatch):
        """Test ready status with postgres:// URL."""
        monkeypatch.setenv("DATABASE_URL", "postgres://localhost/test")

        result = check_db_inspector(temp_project)

        assert result.status == HealthStatus.READY
        assert "PostgreSQL configured" in result.message

    def test_warns_with_unknown_db(self, temp_project: Path, monkeypatch):
        """Test warning with unknown database type."""
        monkeypatch.setenv("DATABASE_URL", "mysql://localhost/test")

        result = check_db_inspector(temp_project)

        assert result.status == HealthStatus.WARNING
        assert "Unknown database type" in result.message


class TestRunMcpHealth:
    """Tests for run_mcp_health function."""

    def test_runs_checks_for_configured_servers(self, temp_project: Path):
        """Test running checks for configured servers."""
        config_path = temp_project / ".ldf" / "config.yaml"
        config_path.write_text("version: '1.0'\nmcp_servers:\n  - spec_inspector")

        report = run_mcp_health(temp_project)

        assert len(report.servers) == 1
        assert report.servers[0].name == "spec_inspector"

    def test_uses_defaults_without_config(self, temp_project: Path):
        """Test using default servers when none configured."""
        config_path = temp_project / ".ldf" / "config.yaml"
        config_path.write_text("version: '1.0'")

        report = run_mcp_health(temp_project)

        # Should use default servers
        server_names = [s.name for s in report.servers]
        assert "spec_inspector" in server_names
        assert "coverage_reporter" in server_names

    def test_handles_unknown_servers(self, temp_project: Path):
        """Test handling unknown server types."""
        config_path = temp_project / ".ldf" / "config.yaml"
        config_path.write_text("version: '1.0'\nmcp_servers:\n  - unknown-server")

        report = run_mcp_health(temp_project)

        assert report.servers[0].status == HealthStatus.SKIP
        assert "Unknown server type" in report.servers[0].message

    def test_uses_cwd_when_none(self, temp_project: Path, monkeypatch):
        """Test using current directory when project_root is None."""
        monkeypatch.chdir(temp_project)

        report = run_mcp_health(None)

        assert len(report.servers) > 0

    def test_handles_invalid_config_yaml(self, temp_project: Path):
        """Test handling invalid config.yaml."""
        config_path = temp_project / ".ldf" / "config.yaml"
        config_path.write_text("invalid: yaml: [[[")

        report = run_mcp_health(temp_project)

        # Should still work with defaults
        assert len(report.servers) > 0


class TestHealthReport:
    """Tests for HealthReport dataclass."""

    def test_counts_statuses(self):
        """Test counting ready/skipped/errors."""
        report = HealthReport(
            servers=[
                ServerHealth("A", HealthStatus.READY, "OK"),
                ServerHealth("B", HealthStatus.READY, "OK"),
                ServerHealth("C", HealthStatus.SKIP, "Skipped"),
                ServerHealth("D", HealthStatus.ERROR, "Failed"),
            ]
        )

        assert report.ready_count == 2
        assert report.skipped_count == 1
        assert report.error_count == 1

    def test_to_dict(self):
        """Test converting to dictionary."""
        report = HealthReport(
            servers=[
                ServerHealth("A", HealthStatus.READY, "OK"),
            ]
        )

        d = report.to_dict()

        assert "servers" in d
        assert "summary" in d
        assert d["summary"]["ready"] == 1


class TestServerHealth:
    """Tests for ServerHealth dataclass."""

    def test_to_dict_without_details(self):
        """Test converting to dict without details."""
        health = ServerHealth("test", HealthStatus.READY, "OK")

        d = health.to_dict()

        assert d["name"] == "test"
        assert d["status"] == "ready"
        assert "details" not in d

    def test_to_dict_with_details(self):
        """Test converting to dict with details."""
        health = ServerHealth(
            "test",
            HealthStatus.READY,
            "OK",
            details={"count": 5},
        )

        d = health.to_dict()

        assert d["details"]["count"] == 5


class TestPrintHealthReport:
    """Tests for print_health_report function."""

    def test_prints_report(self, capsys):
        """Test printing a health report."""
        report = HealthReport(
            servers=[
                ServerHealth("spec_inspector", HealthStatus.READY, "5 specs"),
                ServerHealth("coverage_reporter", HealthStatus.WARNING, "No file"),
                ServerHealth("db_inspector", HealthStatus.SKIP, "Not configured"),
            ]
        )

        print_health_report(report)

        captured = capsys.readouterr()
        assert "MCP Server Health" in captured.out
        assert "spec_inspector" in captured.out
        assert "5 specs" in captured.out
        assert "1 ready" in captured.out
