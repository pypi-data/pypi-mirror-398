"""Tests for ldf.doctor module."""

from pathlib import Path

from ldf.doctor import (
    CheckResult,
    CheckStatus,
    DoctorReport,
    check_config,
    check_git_hooks,
    check_guardrails,
    check_mcp_deps,
    check_mcp_json,
    check_mcp_servers,
    check_project_structure,
    check_question_packs,
    check_required_deps,
    print_report,
    run_doctor,
)


class TestCheckProjectStructure:
    """Tests for check_project_structure function."""

    def test_passes_with_valid_structure(self, temp_project: Path):
        """Test passing when .ldf/ exists with required dirs."""
        # Create required directories
        ldf_dir = temp_project / ".ldf"
        for d in ["specs", "question-packs", "templates", "macros"]:
            (ldf_dir / d).mkdir(exist_ok=True)

        result = check_project_structure(temp_project)

        assert result.status == CheckStatus.PASS
        assert ".ldf/ exists" in result.message

    def test_fails_without_ldf_dir(self, tmp_path: Path):
        """Test failure when .ldf/ doesn't exist."""
        result = check_project_structure(tmp_path)

        assert result.status == CheckStatus.FAIL
        assert ".ldf/ directory not found" in result.message
        assert result.fix_hint is not None

    def test_warns_on_missing_subdirs(self, temp_project: Path):
        """Test warning when subdirectories are missing."""
        # Remove a required directory
        specs_dir = temp_project / ".ldf" / "specs"
        if specs_dir.exists():
            specs_dir.rmdir()

        result = check_project_structure(temp_project)

        assert result.status == CheckStatus.WARN
        assert "Missing directories" in result.message


class TestCheckConfig:
    """Tests for check_config function."""

    def test_passes_with_valid_config(self, temp_project: Path):
        """Test passing with valid config.yaml."""
        result = check_config(temp_project)

        assert result.status == CheckStatus.PASS
        assert "config.yaml valid" in result.message

    def test_fails_without_config(self, tmp_path: Path):
        """Test failure when config.yaml doesn't exist."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()

        result = check_config(tmp_path)

        assert result.status == CheckStatus.FAIL
        assert "not found" in result.message

    def test_fails_with_invalid_yaml(self, temp_project: Path):
        """Test failure with invalid YAML."""
        config_path = temp_project / ".ldf" / "config.yaml"
        config_path.write_text("invalid: yaml: [[[")

        result = check_config(temp_project)

        assert result.status == CheckStatus.FAIL
        assert "YAML parse error" in result.message

    def test_fails_with_non_mapping(self, temp_project: Path):
        """Test failure when config is not a mapping."""
        config_path = temp_project / ".ldf" / "config.yaml"
        config_path.write_text("- just\n- a\n- list")

        result = check_config(temp_project)

        assert result.status == CheckStatus.FAIL
        assert "not a valid YAML mapping" in result.message

    def test_warns_on_missing_version(self, temp_project: Path):
        """Test warning when version key is missing."""
        config_path = temp_project / ".ldf" / "config.yaml"
        config_path.write_text("project:\n  name: test")

        result = check_config(temp_project)

        assert result.status == CheckStatus.WARN
        assert "Missing keys" in result.message


class TestCheckGuardrails:
    """Tests for check_guardrails function."""

    def test_passes_with_valid_guardrails(self, temp_project: Path):
        """Test passing with valid guardrails.yaml."""
        result = check_guardrails(temp_project)

        assert result.status == CheckStatus.PASS
        assert "guardrails.yaml valid" in result.message

    def test_fails_without_guardrails(self, temp_project: Path):
        """Test failure when guardrails.yaml doesn't exist."""
        guardrails_path = temp_project / ".ldf" / "guardrails.yaml"
        guardrails_path.unlink()

        result = check_guardrails(temp_project)

        assert result.status == CheckStatus.FAIL
        assert "not found" in result.message

    def test_fails_with_invalid_yaml(self, temp_project: Path):
        """Test failure with invalid YAML."""
        guardrails_path = temp_project / ".ldf" / "guardrails.yaml"
        guardrails_path.write_text("invalid: yaml: [[[")

        result = check_guardrails(temp_project)

        assert result.status == CheckStatus.FAIL
        assert "YAML parse error" in result.message

    def test_fails_with_non_mapping(self, temp_project: Path):
        """Test failure when guardrails is not a mapping."""
        guardrails_path = temp_project / ".ldf" / "guardrails.yaml"
        guardrails_path.write_text("- just\n- a\n- list")

        result = check_guardrails(temp_project)

        assert result.status == CheckStatus.FAIL
        assert "not a valid YAML mapping" in result.message


class TestCheckQuestionPacks:
    """Tests for check_question_packs function."""

    def test_warns_without_config(self, temp_project: Path):
        """Test warning when config.yaml is missing."""
        config_path = temp_project / ".ldf" / "config.yaml"
        config_path.unlink()

        result = check_question_packs(temp_project)

        assert result.status == CheckStatus.WARN
        assert "config.yaml missing" in result.message

    def test_passes_with_no_packs_configured(self, temp_project: Path):
        """Test passing when no packs are configured."""
        config_path = temp_project / ".ldf" / "config.yaml"
        config_path.write_text("version: '1.0'\nquestion_packs: []")

        result = check_question_packs(temp_project)

        assert result.status == CheckStatus.PASS
        assert "No question packs configured" in result.message

    def test_passes_with_all_packs_present(self, temp_project: Path):
        """Test passing when all configured packs exist."""
        # Update config with a pack
        config_path = temp_project / ".ldf" / "config.yaml"
        config_path.write_text("version: '1.0'\nquestion_packs:\n  - test-pack")

        # Create the pack file
        packs_dir = temp_project / ".ldf" / "question-packs"
        packs_dir.mkdir(exist_ok=True)
        (packs_dir / "test-pack.yaml").write_text("name: test-pack")

        result = check_question_packs(temp_project)

        assert result.status == CheckStatus.PASS
        assert "1/1 packs found" in result.message

    def test_warns_with_missing_packs(self, temp_project: Path):
        """Test warning when configured packs don't exist."""
        config_path = temp_project / ".ldf" / "config.yaml"
        config_path.write_text("version: '1.0'\nquestion_packs:\n  - missing-pack")

        packs_dir = temp_project / ".ldf" / "question-packs"
        packs_dir.mkdir(exist_ok=True)

        result = check_question_packs(temp_project)

        assert result.status == CheckStatus.WARN
        assert "missing-pack" in result.message

    def test_fails_without_packs_dir(self, temp_project: Path):
        """Test failure when question-packs dir doesn't exist."""
        config_path = temp_project / ".ldf" / "config.yaml"
        config_path.write_text("version: '1.0'\nquestion_packs:\n  - test-pack")

        # Remove packs dir if it exists
        packs_dir = temp_project / ".ldf" / "question-packs"
        if packs_dir.exists():
            packs_dir.rmdir()

        result = check_question_packs(temp_project)

        assert result.status == CheckStatus.FAIL

    def test_warns_with_invalid_config_yaml(self, temp_project: Path):
        """Test warning when config.yaml is invalid YAML."""
        config_path = temp_project / ".ldf" / "config.yaml"
        config_path.write_text("invalid: yaml: [[[")

        result = check_question_packs(temp_project)

        assert result.status == CheckStatus.WARN
        assert "config.yaml invalid" in result.message


class TestCheckMcpServers:
    """Tests for check_mcp_servers function."""

    def test_warns_without_config(self, tmp_path: Path):
        """Test warning when config.yaml is missing."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()

        result = check_mcp_servers(tmp_path)

        assert result.status == CheckStatus.WARN

    def test_passes_with_no_servers(self, temp_project: Path):
        """Test passing when no MCP servers are configured."""
        config_path = temp_project / ".ldf" / "config.yaml"
        config_path.write_text("version: '1.0'\nmcp_servers: []")

        result = check_mcp_servers(temp_project)

        assert result.status == CheckStatus.PASS
        assert "No MCP servers configured" in result.message

    def test_passes_with_valid_servers(self, temp_project: Path):
        """Test passing when configured servers exist."""
        config_path = temp_project / ".ldf" / "config.yaml"
        config_path.write_text("version: '1.0'\nmcp_servers:\n  - spec_inspector")

        result = check_mcp_servers(temp_project)

        assert result.status == CheckStatus.PASS
        assert "servers available" in result.message

    def test_warns_with_invalid_yaml(self, temp_project: Path):
        """Test warning when config.yaml is invalid YAML."""
        config_path = temp_project / ".ldf" / "config.yaml"
        config_path.write_text("invalid: yaml: [[[")

        result = check_mcp_servers(temp_project)

        assert result.status == CheckStatus.WARN


class TestCheckRequiredDeps:
    """Tests for check_required_deps function."""

    def test_passes_with_all_deps(self):
        """Test passing when all required deps are installed."""
        result = check_required_deps()

        assert result.status == CheckStatus.PASS
        assert "All required packages installed" in result.message


class TestCheckMcpDeps:
    """Tests for check_mcp_deps function."""

    def test_passes_without_config(self, tmp_path: Path):
        """Test passing when config.yaml doesn't exist."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()

        result = check_mcp_deps(tmp_path)

        assert result.status == CheckStatus.PASS
        assert "No MCP servers configured" in result.message

    def test_passes_without_mcp_servers(self, temp_project: Path):
        """Test passing when no MCP servers are configured."""
        config_path = temp_project / ".ldf" / "config.yaml"
        config_path.write_text("version: '1.0'\nmcp_servers: []")

        result = check_mcp_deps(temp_project)

        assert result.status == CheckStatus.PASS

    def test_warns_with_invalid_yaml(self, temp_project: Path):
        """Test warning when config.yaml is invalid YAML."""
        config_path = temp_project / ".ldf" / "config.yaml"
        config_path.write_text("invalid: yaml: [[[")

        result = check_mcp_deps(temp_project)

        assert result.status == CheckStatus.WARN


class TestCheckGitHooks:
    """Tests for check_git_hooks function."""

    def test_passes_without_git(self, temp_project: Path):
        """Test passing when not a git repository."""
        result = check_git_hooks(temp_project)

        assert result.status == CheckStatus.PASS
        assert "Not a git repository" in result.message

    def test_passes_without_pre_commit(self, temp_project: Path):
        """Test passing when no pre-commit hook exists."""
        git_dir = temp_project / ".git"
        git_dir.mkdir()
        (git_dir / "hooks").mkdir()

        result = check_git_hooks(temp_project)

        assert result.status == CheckStatus.PASS
        assert "No pre-commit hook installed" in result.message

    def test_passes_with_ldf_hook(self, temp_project: Path):
        """Test passing when LDF pre-commit hook is installed."""
        git_dir = temp_project / ".git"
        git_dir.mkdir()
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir()
        pre_commit = hooks_dir / "pre-commit"
        pre_commit.write_text("#!/bin/sh\nldf lint\n")

        result = check_git_hooks(temp_project)

        assert result.status == CheckStatus.PASS
        assert "LDF pre-commit hook installed" in result.message

    def test_passes_with_non_ldf_hook(self, temp_project: Path):
        """Test passing when non-LDF pre-commit hook is installed."""
        git_dir = temp_project / ".git"
        git_dir.mkdir()
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir()
        pre_commit = hooks_dir / "pre-commit"
        pre_commit.write_text("#!/bin/sh\necho 'hello'\n")

        result = check_git_hooks(temp_project)

        assert result.status == CheckStatus.PASS
        assert "Non-LDF pre-commit hook" in result.message


class TestCheckMcpJson:
    """Tests for check_mcp_json function."""

    def test_passes_without_mcp_json(self, temp_project: Path):
        """Test passing when .agent/mcp.json doesn't exist."""
        result = check_mcp_json(temp_project)

        assert result.status == CheckStatus.PASS
        assert "not present" in result.message

    def test_warns_with_mcp_json_no_config(self, tmp_path: Path):
        """Test warning when mcp.json exists but no LDF config."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()
        agent_dir = tmp_path / ".agent"
        agent_dir.mkdir()
        (agent_dir / "mcp.json").write_text('{"mcpServers": {}}')

        result = check_mcp_json(tmp_path)

        assert result.status == CheckStatus.WARN
        assert "no LDF config" in result.message

    def test_passes_with_no_servers_configured(self, temp_project: Path):
        """Test passing when no LDF servers are configured."""
        config_path = temp_project / ".ldf" / "config.yaml"
        config_path.write_text("version: '1.0'\nmcp_servers: []")

        agent_dir = temp_project / ".agent"
        agent_dir.mkdir()
        (agent_dir / "mcp.json").write_text('{"mcpServers": {}}')

        result = check_mcp_json(temp_project)

        assert result.status == CheckStatus.PASS

    def test_warns_on_invalid_json(self, temp_project: Path):
        """Test warning when mcp.json is invalid JSON."""
        agent_dir = temp_project / ".agent"
        agent_dir.mkdir()
        (agent_dir / "mcp.json").write_text("not valid json")

        result = check_mcp_json(temp_project)

        assert result.status == CheckStatus.WARN
        assert "Parse error" in result.message


class TestRunDoctor:
    """Tests for run_doctor function."""

    def test_runs_all_checks(self, temp_project: Path):
        """Test that all checks are run."""
        # Create required structure
        ldf_dir = temp_project / ".ldf"
        for d in ["specs", "question-packs", "templates", "macros"]:
            (ldf_dir / d).mkdir(exist_ok=True)

        report = run_doctor(temp_project)

        assert len(report.checks) >= 8  # At least 8 checks
        assert report.passed > 0

    def test_uses_cwd_when_none(self, temp_project: Path, monkeypatch):
        """Test using current directory when project_root is None."""
        monkeypatch.chdir(temp_project)

        report = run_doctor(None)

        assert len(report.checks) > 0


class TestDoctorReport:
    """Tests for DoctorReport dataclass."""

    def test_counts_statuses(self):
        """Test counting passed/warnings/failed."""
        report = DoctorReport(
            checks=[
                CheckResult("A", CheckStatus.PASS, "OK"),
                CheckResult("B", CheckStatus.PASS, "OK"),
                CheckResult("C", CheckStatus.WARN, "Warning"),
                CheckResult("D", CheckStatus.FAIL, "Failed"),
            ]
        )

        assert report.passed == 2
        assert report.warnings == 1
        assert report.failed == 1
        assert report.success is False

    def test_success_without_failures(self):
        """Test success is True when no failures."""
        report = DoctorReport(
            checks=[
                CheckResult("A", CheckStatus.PASS, "OK"),
                CheckResult("B", CheckStatus.WARN, "Warning"),
            ]
        )

        assert report.success is True

    def test_to_dict(self):
        """Test converting to dictionary."""
        report = DoctorReport(
            checks=[
                CheckResult("A", CheckStatus.PASS, "OK"),
            ]
        )

        d = report.to_dict()

        assert "checks" in d
        assert "summary" in d
        assert d["summary"]["passed"] == 1


class TestCheckResult:
    """Tests for CheckResult dataclass."""

    def test_to_dict_without_fix_hint(self):
        """Test converting to dict without fix hint."""
        result = CheckResult("Test", CheckStatus.PASS, "OK")

        d = result.to_dict()

        assert d["name"] == "Test"
        assert d["status"] == "pass"
        assert "fix_hint" not in d

    def test_to_dict_with_fix_hint(self):
        """Test converting to dict with fix hint."""
        result = CheckResult("Test", CheckStatus.FAIL, "Failed", "Run: ldf init")

        d = result.to_dict()

        assert d["fix_hint"] == "Run: ldf init"


class TestPrintReport:
    """Tests for print_report function."""

    def test_prints_report(self, capsys):
        """Test printing a doctor report."""
        report = DoctorReport(
            checks=[
                CheckResult("A", CheckStatus.PASS, "OK"),
                CheckResult("B", CheckStatus.WARN, "Warning"),
                CheckResult("C", CheckStatus.FAIL, "Failed", "Fix it"),
            ]
        )

        print_report(report)

        captured = capsys.readouterr()
        assert "LDF Doctor" in captured.out
        assert "OK" in captured.out
        assert "Warning" in captured.out
        assert "Failed" in captured.out
        assert "Fix it" in captured.out


class TestCheckMcpServersEdgeCases:
    """Edge case tests for check_mcp_servers."""

    def test_handles_mcp_package_not_found(self, temp_project: Path, monkeypatch):
        """Test handling when MCP package is not found."""
        config_path = temp_project / ".ldf" / "config.yaml"
        config_path.write_text("version: '1.0'\nmcp_servers:\n  - spec_inspector")

        # Mock importlib.resources.files to raise ModuleNotFoundError
        def raise_not_found(pkg):
            raise ModuleNotFoundError("No module named 'ldf._mcp_servers'")

        monkeypatch.setattr("importlib.resources.files", raise_not_found)

        result = check_mcp_servers(temp_project)

        assert result.status == CheckStatus.WARN
        assert "Cannot locate MCP servers package" in result.message

    def test_warns_on_missing_server(self, temp_project: Path, monkeypatch):
        """Test warning when configured server doesn't exist."""
        from unittest.mock import MagicMock

        config_path = temp_project / ".ldf" / "config.yaml"
        config_path.write_text("version: '1.0'\nmcp_servers:\n  - nonexistent-server")

        # Mock to return False for is_file
        # Handle chained joinpath calls: joinpath(server_dir).joinpath("server.py")
        mock_pkg = MagicMock()
        mock_path = MagicMock()
        mock_path.is_file.return_value = False
        mock_pkg.joinpath.return_value.joinpath.return_value = mock_path

        def mock_files(pkg):
            return mock_pkg

        monkeypatch.setattr("importlib.resources.files", mock_files)

        result = check_mcp_servers(temp_project)

        assert result.status == CheckStatus.WARN
        assert "Missing servers" in result.message


class TestCheckRequiredDepsEdgeCases:
    """Edge case tests for check_required_deps."""

    def test_handles_missing_dep(self, monkeypatch):
        """Test failure when a required dependency is missing."""
        import builtins

        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "questionary":
                raise ImportError("No module named 'questionary'")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)

        result = check_required_deps()

        assert result.status == CheckStatus.FAIL
        assert "questionary" in result.message


class TestCheckMcpDepsEdgeCases:
    """Edge case tests for check_mcp_deps."""

    def test_warns_when_mcp_missing(self, temp_project: Path, monkeypatch):
        """Test warning when mcp package is missing."""
        import builtins

        config_path = temp_project / ".ldf" / "config.yaml"
        config_path.write_text("version: '1.0'\nmcp_servers:\n  - spec_inspector")

        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "mcp":
                raise ImportError("No module named 'mcp'")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)

        result = check_mcp_deps(temp_project)

        assert result.status == CheckStatus.WARN
        assert "mcp" in result.message

    def test_warns_when_coverage_missing_for_reporter(self, temp_project: Path, monkeypatch):
        """Test warning when coverage package is missing for coverage_reporter."""
        import builtins

        config_path = temp_project / ".ldf" / "config.yaml"
        config_path.write_text("version: '1.0'\nmcp_servers:\n  - coverage_reporter")

        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "coverage":
                raise ImportError("No module named 'coverage'")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)

        result = check_mcp_deps(temp_project)

        assert result.status == CheckStatus.WARN
        assert "coverage" in result.message

    def test_passes_when_all_mcp_deps_present(self, temp_project: Path):
        """Test passing when all MCP deps are installed."""
        config_path = temp_project / ".ldf" / "config.yaml"
        config_path.write_text("version: '1.0'\nmcp_servers:\n  - spec_inspector")

        result = check_mcp_deps(temp_project)

        # Should pass or warn depending on whether mcp is installed
        assert result.status in (CheckStatus.PASS, CheckStatus.WARN)


class TestCheckGitHooksEdgeCases:
    """Edge case tests for check_git_hooks."""

    def test_warns_on_read_error(self, temp_project: Path, monkeypatch):
        """Test warning when pre-commit hook can't be read."""
        git_dir = temp_project / ".git"
        git_dir.mkdir()
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir()
        pre_commit = hooks_dir / "pre-commit"
        pre_commit.write_text("#!/bin/sh\nldf lint\n")

        # Mock read_text to raise OSError
        def raise_os_error():
            raise OSError("Permission denied")

        from pathlib import Path as PathClass

        original_read_text = PathClass.read_text

        def mock_read_text(self, *args, **kwargs):
            if self.name == "pre-commit":
                raise OSError("Permission denied")
            return original_read_text(self, *args, **kwargs)

        monkeypatch.setattr(PathClass, "read_text", mock_read_text)

        result = check_git_hooks(temp_project)

        assert result.status == CheckStatus.WARN
        assert "Cannot read pre-commit hook" in result.message


class TestCheckMcpJsonEdgeCases:
    """Edge case tests for check_mcp_json."""

    def test_warns_on_missing_servers_in_json(self, temp_project: Path):
        """Test warning when servers in config are missing from mcp.json."""
        import json

        config_path = temp_project / ".ldf" / "config.yaml"
        config_path.write_text(
            "version: '1.0'\nmcp_servers:\n  - spec_inspector\n  - coverage_reporter"
        )

        # Create mcp.json without spec_inspector
        agent_dir = temp_project / ".agent"
        agent_dir.mkdir()
        mcp_json = {"mcpServers": {"other-server": {"args": ["not-ldf"]}}}
        (agent_dir / "mcp.json").write_text(json.dumps(mcp_json))

        result = check_mcp_json(temp_project)

        assert result.status == CheckStatus.WARN
        assert "missing" in result.message.lower()

    def test_passes_with_all_servers_in_json(self, temp_project: Path):
        """Test passing when all configured servers are in mcp.json."""
        import json

        config_path = temp_project / ".ldf" / "config.yaml"
        config_path.write_text("version: '1.0'\nmcp_servers:\n  - spec_inspector")

        # Create mcp.json with spec_inspector
        agent_dir = temp_project / ".agent"
        agent_dir.mkdir()
        mcp_json = {
            "mcpServers": {
                "spec_inspector": {"args": ["-m", "ldf._mcp_servers.spec_inspector.server"]}
            }
        }
        (agent_dir / "mcp.json").write_text(json.dumps(mcp_json))

        result = check_mcp_json(temp_project)

        assert result.status == CheckStatus.PASS
        assert "up to date" in result.message


class TestRunDoctorAutoFix:
    """Tests for run_doctor auto-fix functionality."""

    def test_attempts_fix_when_requested(self, temp_project: Path, monkeypatch):
        """Test that fix=True attempts to auto-fix issues."""
        from unittest.mock import MagicMock

        # Remove a required directory to create a failure
        specs_dir = temp_project / ".ldf" / "specs"
        if specs_dir.exists():
            specs_dir.rmdir()

        # Mock subprocess.run to capture the call
        mock_run = MagicMock()
        monkeypatch.setattr("subprocess.run", mock_run)

        report = run_doctor(temp_project, fix=True)

        # Check that subprocess.run was called with init --repair
        # (if there was a failure with "ldf init" fix_hint)
        if any(
            c.status == CheckStatus.FAIL and c.fix_hint and "ldf init" in c.fix_hint
            for c in report.checks
        ):
            assert mock_run.called

    def test_fix_handles_subprocess_exception(self, temp_project: Path, monkeypatch):
        """Test that fix handles subprocess exceptions gracefully."""

        # Create a failure condition
        config_path = temp_project / ".ldf" / "config.yaml"
        config_path.unlink()

        # Mock subprocess.run to raise an exception
        def raise_exception(*args, **kwargs):
            raise Exception("Subprocess failed")

        monkeypatch.setattr("subprocess.run", raise_exception)

        # Should not raise, just continue
        report = run_doctor(temp_project, fix=True)

        assert report is not None
        assert len(report.checks) > 0
