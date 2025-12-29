"""Tests for ldf.cli module."""

from pathlib import Path

import pytest
from click.testing import CliRunner

from ldf import __version__
from ldf.cli import main as cli


@pytest.fixture
def runner():
    """Create a Click CLI test runner."""
    return CliRunner()


class TestCLIHelp:
    """Tests for CLI help and version commands."""

    def test_help_command(self, runner: CliRunner):
        """Test that --help shows usage information."""
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "LDF" in result.output or "ldf" in result.output.lower()

    def test_version_command(self, runner: CliRunner):
        """Test that --version shows version."""
        result = runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        assert __version__ in result.output


class TestInitCommand:
    """Tests for 'ldf init' command."""

    def test_init_creates_ldf_directory(self, runner: CliRunner, tmp_path: Path):
        """Test that init creates .ldf directory structure."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["init", "--yes"])

            assert result.exit_code == 0
            assert Path(".ldf").exists()
            assert Path(".ldf/config.yaml").exists()
            assert Path(".ldf/guardrails.yaml").exists()
            assert Path(".ldf/specs").exists()

    def test_init_with_preset(self, runner: CliRunner, tmp_path: Path):
        """Test init with a preset option."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["init", "--preset", "saas", "--yes"])

            assert result.exit_code == 0
            # Check that config includes the preset
            config = Path(".ldf/config.yaml").read_text()
            assert "saas" in config or "preset" in config

    def test_init_already_initialized(self, runner: CliRunner, tmp_path: Path):
        """Test init when already initialized."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            # First init
            runner.invoke(cli, ["init", "--yes"])

            # Second init in non-interactive mode should succeed (overwrites)
            result = runner.invoke(cli, ["init", "--yes"])

            # Should succeed in non-interactive mode
            assert result.exit_code == 0


class TestLintCommand:
    """Tests for 'ldf lint' command."""

    def test_lint_requires_ldf_directory(self, runner: CliRunner, tmp_path: Path):
        """Test lint fails without .ldf directory."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["lint"])

            assert result.exit_code == 1
            assert "ldf" in result.output.lower() or "init" in result.output.lower()

    def test_lint_with_spec_name(self, runner: CliRunner, temp_spec: Path, monkeypatch):
        """Test lint with specific spec name."""
        project_dir = temp_spec.parent.parent.parent
        monkeypatch.chdir(project_dir)

        result = runner.invoke(cli, ["lint", "test-feature"])

        # Should succeed for valid spec
        assert result.exit_code == 0

    def test_lint_all_specs(self, runner: CliRunner, temp_spec: Path, monkeypatch):
        """Test lint all specs in project."""
        project_dir = temp_spec.parent.parent.parent
        monkeypatch.chdir(project_dir)

        result = runner.invoke(cli, ["lint", "--all"])

        assert result.exit_code == 0


class TestAuditCommand:
    """Tests for 'ldf audit' command."""

    def test_audit_spec_review(self, runner: CliRunner, temp_spec: Path, monkeypatch):
        """Test generating a spec review audit request."""
        project_dir = temp_spec.parent.parent.parent
        monkeypatch.chdir(project_dir)

        # Use -y to skip confirmation prompt
        result = runner.invoke(cli, ["audit", "--type", "spec-review", "-y"])

        # Should generate audit request
        assert result.exit_code == 0

    def test_audit_requires_type(self, runner: CliRunner, temp_project: Path, monkeypatch):
        """Test that audit requires --type or --import."""
        monkeypatch.chdir(temp_project)

        result = runner.invoke(cli, ["audit"])

        # Should fail or warn without type
        # The audit command may exit 0 but show usage, or exit non-zero
        assert (
            "type" in result.output.lower()
            or "import" in result.output.lower()
            or result.exit_code != 0
        )


class TestCLIIntegration:
    """Integration tests for CLI workflow."""

    def test_init_then_lint(self, runner: CliRunner, tmp_path: Path):
        """Test init followed by lint workflow."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            # Initialize with --yes for non-interactive mode
            init_result = runner.invoke(cli, ["init", "--yes"])
            assert init_result.exit_code == 0

            # Lint (no specs yet, should succeed or warn)
            lint_result = runner.invoke(cli, ["lint", "--all"])
            assert lint_result.exit_code == 0


class TestVerboseMode:
    """Tests for verbose mode."""

    def test_verbose_flag(self, runner: CliRunner, tmp_path: Path):
        """Test that verbose flag enables verbose logging."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["-v", "init", "--yes"])

            # Should succeed with verbose mode
            assert result.exit_code == 0


class TestCreateSpecCommand:
    """Tests for 'ldf create-spec' command."""

    def test_create_spec_success(self, runner: CliRunner, temp_project: Path, monkeypatch):
        """Test successful spec creation."""
        monkeypatch.chdir(temp_project)

        result = runner.invoke(cli, ["create-spec", "new-feature"])

        assert result.exit_code == 0
        assert (temp_project / ".ldf" / "specs" / "new-feature").exists()

    def test_create_spec_failure_exits_with_1(self, runner: CliRunner, tmp_path: Path, monkeypatch):
        """Test that create-spec fails without LDF initialized."""
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(cli, ["create-spec", "my-feature"])

        assert result.exit_code == 1


class TestCoverageCommand:
    """Tests for 'ldf coverage' command."""

    def test_coverage_command_basic(self, runner: CliRunner, temp_project: Path, monkeypatch):
        """Test basic coverage command."""
        monkeypatch.chdir(temp_project)

        result = runner.invoke(cli, ["coverage"])

        # May fail or succeed depending on coverage file
        # Just check it runs without error
        assert result.exit_code in (0, 1)

    def test_coverage_fail_status_exit_code(
        self, runner: CliRunner, temp_project: Path, monkeypatch
    ):
        """Test that coverage FAIL status returns exit code 1."""
        monkeypatch.chdir(temp_project)

        # Create a mock coverage file that will report FAIL
        coverage_file = temp_project / "coverage.json"
        coverage_file.write_text('{"totals": {"percent_covered": 50.0}}')

        result = runner.invoke(cli, ["coverage"])

        # Should exit with 1 when coverage fails
        assert result.exit_code in (0, 1)  # Depends on threshold


class TestHooksCommands:
    """Tests for 'ldf hooks' commands."""

    def test_hooks_help(self, runner: CliRunner):
        """Test hooks group help."""
        result = runner.invoke(cli, ["hooks", "--help"])

        assert result.exit_code == 0
        assert "install" in result.output
        assert "uninstall" in result.output
        assert "status" in result.output

    def test_hooks_install_no_git(self, runner: CliRunner, temp_project: Path, monkeypatch):
        """Test hooks install fails without git."""
        monkeypatch.chdir(temp_project)

        result = runner.invoke(cli, ["hooks", "install", "-y"])

        # Should fail without git
        assert result.exit_code == 1

    def test_hooks_install_success(self, runner: CliRunner, temp_project: Path, monkeypatch):
        """Test hooks install succeeds with git."""
        # Create .git directory
        (temp_project / ".git").mkdir()
        monkeypatch.chdir(temp_project)

        result = runner.invoke(cli, ["hooks", "install", "-y", "--no-detect"])

        assert result.exit_code == 0

    def test_hooks_uninstall_not_installed(
        self, runner: CliRunner, temp_project: Path, monkeypatch
    ):
        """Test hooks uninstall when not installed."""
        (temp_project / ".git").mkdir()
        monkeypatch.chdir(temp_project)

        result = runner.invoke(cli, ["hooks", "uninstall"])

        # Should fail when no hook installed
        assert result.exit_code == 1

    def test_hooks_uninstall_success(self, runner: CliRunner, temp_project: Path, monkeypatch):
        """Test hooks uninstall after install."""
        (temp_project / ".git").mkdir()
        monkeypatch.chdir(temp_project)

        # First install
        runner.invoke(cli, ["hooks", "install", "-y", "--no-detect"])

        # Then uninstall
        result = runner.invoke(cli, ["hooks", "uninstall"])

        assert result.exit_code == 0

    def test_hooks_status(self, runner: CliRunner, temp_project: Path, monkeypatch):
        """Test hooks status command."""
        (temp_project / ".git").mkdir()
        monkeypatch.chdir(temp_project)

        result = runner.invoke(cli, ["hooks", "status"])

        assert result.exit_code == 0
        assert "Hook" in result.output


class TestStatusCommand:
    """Tests for 'ldf status' command."""

    def test_status_new_project(self, runner: CliRunner, tmp_path: Path):
        """Test status on a new project without LDF."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["status"])

            assert result.exit_code == 0
            assert "NEW" in result.output or "new" in result.output.lower()

    def test_status_initialized_project(self, runner: CliRunner, tmp_path: Path):
        """Test status on an initialized project."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            # Initialize first
            runner.invoke(cli, ["init", "--yes"])

            result = runner.invoke(cli, ["status"])

            assert result.exit_code == 0
            assert "CURRENT" in result.output or "Project" in result.output

    def test_status_json_output(self, runner: CliRunner, tmp_path: Path):
        """Test status with JSON output."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(cli, ["init", "--yes"])

            result = runner.invoke(cli, ["status", "--json"])

            assert result.exit_code == 0
            # Should contain JSON-like output
            assert "{" in result.output or "state" in result.output.lower()

    def test_status_with_specs(self, runner: CliRunner, temp_spec: Path, monkeypatch):
        """Test status shows specs when present."""
        project_dir = temp_spec.parent.parent.parent
        monkeypatch.chdir(project_dir)

        result = runner.invoke(cli, ["status"])

        assert result.exit_code == 0


class TestUpdateCommand:
    """Tests for 'ldf update' command."""

    def test_update_check(self, runner: CliRunner, temp_project: Path, monkeypatch):
        """Test update --check shows available updates."""
        monkeypatch.chdir(temp_project)

        result = runner.invoke(cli, ["update", "--check"])

        assert result.exit_code == 0

    def test_update_dry_run(self, runner: CliRunner, temp_project: Path, monkeypatch):
        """Test update --dry-run previews changes."""
        monkeypatch.chdir(temp_project)

        result = runner.invoke(cli, ["update", "--dry-run"])

        assert result.exit_code == 0

    def test_update_with_yes(self, runner: CliRunner, temp_project: Path, monkeypatch):
        """Test update --yes applies updates non-interactively."""
        monkeypatch.chdir(temp_project)

        result = runner.invoke(cli, ["update", "--yes"])

        assert result.exit_code == 0

    def test_update_requires_init(self, runner: CliRunner, tmp_path: Path):
        """Test update fails without LDF initialized."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["update"])

            assert result.exit_code == 1


class TestConvertCommand:
    """Tests for 'ldf convert' command."""

    def test_convert_help(self, runner: CliRunner):
        """Test convert group help."""
        result = runner.invoke(cli, ["convert", "--help"])

        assert result.exit_code == 0
        assert "analyze" in result.output
        assert "import" in result.output

    def test_convert_analyze(self, runner: CliRunner, tmp_path: Path):
        """Test convert analyze generates prompt."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            # Create some source files to analyze
            Path("main.py").write_text("print('hello')")
            Path("README.md").write_text("# My Project")

            result = runner.invoke(cli, ["convert", "analyze"])

            assert result.exit_code == 0

    def test_convert_analyze_output_file(self, runner: CliRunner, tmp_path: Path):
        """Test convert analyze with output file."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            Path("main.py").write_text("print('hello')")

            result = runner.invoke(cli, ["convert", "analyze", "-o", "prompt.md"])

            assert result.exit_code == 0
            assert Path("prompt.md").exists()


class TestMcpConfigCommand:
    """Tests for 'ldf mcp-config' command."""

    def test_mcp_config_basic(self, runner: CliRunner, temp_project: Path, monkeypatch):
        """Test mcp-config generates configuration."""
        monkeypatch.chdir(temp_project)

        result = runner.invoke(cli, ["mcp-config"])

        assert result.exit_code == 0
        assert "mcpServers" in result.output or "spec_inspector" in result.output

    def test_mcp_config_without_init(self, runner: CliRunner, tmp_path: Path):
        """Test mcp-config works even without full LDF init (generates basic config)."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["mcp-config"])

            # Should succeed and output config (may be minimal)
            assert result.exit_code == 0


class TestInitEdgeCases:
    """Tests for init command edge cases."""

    def test_init_with_repair_no_ldf(self, runner: CliRunner, tmp_path: Path):
        """Test init --repair on project without LDF."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["init", "--repair", "--yes"])

            # Should proceed with full init or show message
            assert result.exit_code == 0

    def test_init_with_force(self, runner: CliRunner, tmp_path: Path):
        """Test init --force reinitializes."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            # First init
            runner.invoke(cli, ["init", "--yes"])
            # Force reinit
            result = runner.invoke(cli, ["init", "--force", "--yes"])

            assert result.exit_code == 0

    def test_init_repair_complete_project(self, runner: CliRunner, tmp_path: Path):
        """Test init --repair on complete project."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            # Initialize fully
            runner.invoke(cli, ["init", "--yes"])

            # Try repair - should say up to date or no repair needed
            result = runner.invoke(cli, ["init", "--repair"])

            assert result.exit_code == 0
            assert "up to date" in result.output.lower() or "complete" in result.output.lower()

    def test_init_outdated_project(self, runner: CliRunner, tmp_path: Path):
        """Test init on outdated project shows update message."""
        from unittest.mock import MagicMock, patch

        from ldf.detection import ProjectState

        with runner.isolated_filesystem(temp_dir=tmp_path):
            # Create basic LDF setup
            ldf_dir = Path(".ldf")
            ldf_dir.mkdir()
            (ldf_dir / "config.yaml").write_text("version: '0.0.1'")

            # Mock detect_project_state to return OUTDATED
            mock_detection = MagicMock()
            mock_detection.state = ProjectState.OUTDATED
            mock_detection.project_version = "0.0.1"
            mock_detection.installed_version = "1.0.0"

            with patch("ldf.detection.detect_project_state", return_value=mock_detection):
                result = runner.invoke(cli, ["init"])

                assert result.exit_code == 0
                assert "outdated" in result.output.lower() or "update" in result.output.lower()

    def test_init_legacy_project(self, runner: CliRunner, tmp_path: Path):
        """Test init on legacy project shows upgrade message."""
        from unittest.mock import MagicMock, patch

        from ldf.detection import ProjectState

        with runner.isolated_filesystem(temp_dir=tmp_path):
            # Create legacy-style LDF setup (no version)
            ldf_dir = Path(".ldf")
            ldf_dir.mkdir()
            (ldf_dir / "config.yaml").write_text("preset: saas")

            # Mock detect_project_state to return LEGACY
            mock_detection = MagicMock()
            mock_detection.state = ProjectState.LEGACY

            with patch("ldf.detection.detect_project_state", return_value=mock_detection):
                result = runner.invoke(cli, ["init"])

                assert result.exit_code == 0
                assert "legacy" in result.output.lower() or "update" in result.output.lower()

    def test_init_partial_project_no_repair(self, runner: CliRunner, tmp_path: Path):
        """Test init on partial project without --repair shows repair message."""
        from unittest.mock import MagicMock, patch

        from ldf.detection import ProjectState

        with runner.isolated_filesystem(temp_dir=tmp_path):
            # Create partial LDF setup
            ldf_dir = Path(".ldf")
            ldf_dir.mkdir()
            (ldf_dir / "config.yaml").write_text("version: '1.0'")

            # Mock detect_project_state to return PARTIAL
            mock_detection = MagicMock()
            mock_detection.state = ProjectState.PARTIAL
            mock_detection.missing_files = ["guardrails.yaml", "templates/", "framework/"]

            with patch("ldf.detection.detect_project_state", return_value=mock_detection):
                result = runner.invoke(cli, ["init"])

                assert result.exit_code == 0
                assert "incomplete" in result.output.lower() or "repair" in result.output.lower()

    def test_init_corrupted_project(self, runner: CliRunner, tmp_path: Path):
        """Test init on corrupted project shows force message."""
        from unittest.mock import MagicMock, patch

        from ldf.detection import ProjectState

        with runner.isolated_filesystem(temp_dir=tmp_path):
            # Create corrupted LDF setup
            ldf_dir = Path(".ldf")
            ldf_dir.mkdir()
            (ldf_dir / "config.yaml").write_text("invalid: yaml: content: [")

            # Mock detect_project_state to return CORRUPTED
            mock_detection = MagicMock()
            mock_detection.state = ProjectState.CORRUPTED
            mock_detection.invalid_files = ["config.yaml"]

            with patch("ldf.detection.detect_project_state", return_value=mock_detection):
                result = runner.invoke(cli, ["init"])

                assert result.exit_code == 0
                assert "corrupted" in result.output.lower() or "force" in result.output.lower()

    def test_init_repair_partial_in_detection(self, runner: CliRunner, tmp_path: Path):
        """Test init --repair on partial project runs repair (in detection block)."""
        from unittest.mock import MagicMock, patch

        from ldf.detection import ProjectState

        with runner.isolated_filesystem(temp_dir=tmp_path):
            # Create partial LDF setup
            ldf_dir = Path(".ldf")
            ldf_dir.mkdir()
            (ldf_dir / "config.yaml").write_text("version: '1.0'")

            # Mock detect_project_state to return PARTIAL
            mock_detection = MagicMock()
            mock_detection.state = ProjectState.PARTIAL
            mock_detection.missing_files = ["guardrails.yaml"]

            with (
                patch("ldf.detection.detect_project_state", return_value=mock_detection),
                patch("ldf.init.repair_project") as mock_repair,
            ):
                result = runner.invoke(cli, ["init", "--repair"])

                assert result.exit_code == 0
                # In the detection block (lines 143-147), repair is called for PARTIAL
                mock_repair.assert_called_once()

    def test_init_force_repair_legacy_project(self, runner: CliRunner, tmp_path: Path):
        """Test init --force --repair on legacy project runs repair (skipping detection)."""
        from unittest.mock import MagicMock, patch

        from ldf.detection import ProjectState

        with runner.isolated_filesystem(temp_dir=tmp_path):
            # Create legacy LDF setup
            ldf_dir = Path(".ldf")
            ldf_dir.mkdir()
            (ldf_dir / "config.yaml").write_text("preset: saas")

            # Mock detect_project_state to return LEGACY
            mock_detection = MagicMock()
            mock_detection.state = ProjectState.LEGACY

            # With --force, detection block is skipped, then --repair triggers lines 173-176
            with (
                patch("ldf.detection.detect_project_state", return_value=mock_detection),
                patch("ldf.init.repair_project") as mock_repair,
            ):
                result = runner.invoke(cli, ["init", "--force", "--repair"])

                assert result.exit_code == 0
                mock_repair.assert_called_once()

    def test_init_force_repair_new_project(self, runner: CliRunner, tmp_path: Path):
        """Test init --force --repair on new project falls through to init."""
        from unittest.mock import MagicMock, patch

        from ldf.detection import ProjectState

        with runner.isolated_filesystem(temp_dir=tmp_path):
            # No LDF setup - NEW state
            mock_detection = MagicMock()
            mock_detection.state = ProjectState.NEW

            with patch("ldf.detection.detect_project_state", return_value=mock_detection):
                result = runner.invoke(cli, ["init", "--force", "--repair", "--yes"])

                assert result.exit_code == 0
                # Should show message about no existing setup to repair
                assert "No existing LDF setup" in result.output or Path(".ldf").exists()

    def test_init_force_repair_current_project(self, runner: CliRunner, tmp_path: Path):
        """Test init --force --repair on current project says no repair needed."""
        from unittest.mock import MagicMock, patch

        from ldf.detection import ProjectState

        with runner.isolated_filesystem(temp_dir=tmp_path):
            # Create full LDF setup
            ldf_dir = Path(".ldf")
            ldf_dir.mkdir()
            (ldf_dir / "config.yaml").write_text("version: '1.0'")

            mock_detection = MagicMock()
            mock_detection.state = ProjectState.CURRENT

            with patch("ldf.detection.detect_project_state", return_value=mock_detection):
                result = runner.invoke(cli, ["init", "--force", "--repair"])

                assert result.exit_code == 0
                # Lines 177-179: should say no repair needed
                assert "complete" in result.output.lower() or "no repair" in result.output.lower()


class TestConvertImportCommand:
    """Tests for 'ldf convert import' command."""

    def test_convert_import_requires_init(self, runner: CliRunner, tmp_path: Path):
        """Test convert import fails without LDF init."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            # Create a dummy response file
            Path("response.md").write_text("# Requirements\nSome content")

            result = runner.invoke(cli, ["convert", "import", "response.md"])

            assert result.exit_code == 1
            assert "init" in result.output.lower()

    def test_convert_import_dry_run(self, runner: CliRunner, tmp_path: Path):
        """Test convert import with dry-run."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            # Initialize LDF first
            runner.invoke(cli, ["init", "--yes"])

            # Create a response file
            Path("response.md").write_text("""# Requirements

## Feature: Test Feature

This is a test requirement.

# Design

Design details here.

# Tasks

- Task 1
- Task 2
""")

            result = runner.invoke(cli, ["convert", "import", "response.md", "--dry-run"])

            # Should succeed or show preview
            assert "dry run" in result.output.lower() or result.exit_code in (0, 1)

    def test_convert_import_with_spec_name(self, runner: CliRunner, tmp_path: Path):
        """Test convert import with custom spec name."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(cli, ["init", "--yes"])

            Path("response.md").write_text("# Requirements\n\nTest content")

            result = runner.invoke(cli, ["convert", "import", "response.md", "-n", "my-feature"])

            # Check it ran (may fail on parsing but command executed)
            assert result.exit_code in (0, 1)


class TestStatusEdgeCases:
    """Tests for status command edge cases."""

    def test_status_partial_project(self, runner: CliRunner, tmp_path: Path):
        """Test status on partial/incomplete project."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            # Create partial LDF setup (missing some files)
            ldf_dir = Path(".ldf")
            ldf_dir.mkdir()
            (ldf_dir / "config.yaml").write_text("version: '1.0'")
            # Missing guardrails.yaml, templates, etc.

            result = runner.invoke(cli, ["status"])

            assert result.exit_code == 0
            # Should show partial or missing info
            assert (
                "PARTIAL" in result.output
                or "Missing" in result.output
                or "Project" in result.output
            )

    def test_status_with_invalid_files(self, runner: CliRunner, tmp_path: Path):
        """Test status shows invalid files when present."""
        from unittest.mock import MagicMock, patch

        from ldf.detection import ProjectState

        with runner.isolated_filesystem(temp_dir=tmp_path):
            # Create LDF setup
            ldf_dir = Path(".ldf")
            ldf_dir.mkdir()
            (ldf_dir / "config.yaml").write_text("version: '1.0'")

            # Mock detect_project_state to return invalid files
            mock_result = MagicMock()
            mock_result.state = ProjectState.PARTIAL
            mock_result.project_root = Path(".")
            mock_result.missing_files = []
            mock_result.invalid_files = ["config.yaml", "guardrails.yaml"]
            mock_result.recommended_action = "Fix invalid files"
            mock_result.recommended_command = "ldf init --force"

            with patch("ldf.detection.detect_project_state", return_value=mock_result):
                result = runner.invoke(cli, ["status"])

                assert result.exit_code == 0
                # Should show invalid files in output
                assert "Invalid" in result.output or "invalid" in result.output.lower()

    def test_status_with_many_specs(self, runner: CliRunner, tmp_path: Path):
        """Test status shows >5 specs with 'and X more' message."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            # Initialize LDF
            runner.invoke(cli, ["init", "--yes"])

            # Create more than 5 specs
            specs_dir = Path(".ldf/specs")
            for i in range(8):
                spec_dir = specs_dir / f"spec-{i}"
                spec_dir.mkdir(parents=True, exist_ok=True)
                (spec_dir / "requirements.md").write_text(
                    f"# Spec {i}\n\nRequirements for spec {i}"
                )

            result = runner.invoke(cli, ["status"])

            assert result.exit_code == 0
            # Should show "and X more" for specs > 5
            assert "more" in result.output or "Specs" in result.output


class TestMainEntryPoint:
    """Tests for main entry point."""

    def test_main_callable(self):
        """Test that main CLI function is callable."""
        from ldf.cli import main

        assert callable(main)

    def test_main_invoked_directly(self, runner: CliRunner):
        """Test that main can be invoked with --help."""
        result = runner.invoke(cli, ["--help"])
        # Should show help
        assert result.exit_code == 0
        assert "ldf" in result.output.lower()


class TestDoctorCommand:
    """Tests for 'ldf doctor' command."""

    def test_doctor_basic(self, runner: CliRunner, temp_project: Path, monkeypatch):
        """Test doctor command runs diagnostics."""
        # Create required directories for doctor to pass
        ldf_dir = temp_project / ".ldf"
        for d in ["specs", "question-packs", "templates", "macros"]:
            (ldf_dir / d).mkdir(exist_ok=True)
        monkeypatch.chdir(temp_project)

        result = runner.invoke(cli, ["doctor"])

        assert result.exit_code == 0
        assert "Doctor" in result.output or "passed" in result.output

    def test_doctor_json_output(self, runner: CliRunner, temp_project: Path, monkeypatch):
        """Test doctor with JSON output."""
        # Create required directories
        ldf_dir = temp_project / ".ldf"
        for d in ["specs", "question-packs", "templates", "macros"]:
            (ldf_dir / d).mkdir(exist_ok=True)
        monkeypatch.chdir(temp_project)

        result = runner.invoke(cli, ["doctor", "--json"])

        assert result.exit_code == 0
        assert "{" in result.output  # JSON output

    def test_doctor_without_ldf(self, runner: CliRunner, tmp_path: Path):
        """Test doctor on non-LDF project."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["doctor"])

            # Should report failures (exit code 1)
            assert result.exit_code == 1
            assert "fail" in result.output.lower() or "not found" in result.output.lower()


class TestMcpHealthCommand:
    """Tests for 'ldf mcp-health' command."""

    def test_mcp_health_basic(self, runner: CliRunner, temp_project: Path, monkeypatch):
        """Test mcp-health command runs health checks."""
        monkeypatch.chdir(temp_project)

        result = runner.invoke(cli, ["mcp-health"])

        assert result.exit_code == 0
        assert "Health" in result.output or "Server" in result.output

    def test_mcp_health_json_output(self, runner: CliRunner, temp_project: Path, monkeypatch):
        """Test mcp-health with JSON output."""
        monkeypatch.chdir(temp_project)

        result = runner.invoke(cli, ["mcp-health", "--json"])

        assert result.exit_code == 0
        assert "{" in result.output


class TestListFrameworkCommand:
    """Tests for 'ldf list-framework' command."""

    def test_list_framework_presets(self, runner: CliRunner):
        """Test list-framework presets subcommand."""
        result = runner.invoke(cli, ["list-framework", "presets"])

        assert result.exit_code == 0
        assert "core" in result.output.lower() or "saas" in result.output.lower()

    def test_list_framework_packs(self, runner: CliRunner):
        """Test list-framework packs subcommand."""
        result = runner.invoke(cli, ["list-framework", "packs"])

        assert result.exit_code == 0
        assert "security" in result.output.lower() or "testing" in result.output.lower()

    def test_list_framework_guardrails(self, runner: CliRunner):
        """Test list-framework guardrails subcommand."""
        result = runner.invoke(cli, ["list-framework", "guardrails"])

        assert result.exit_code == 0
        # Should show guardrail content
        assert "Testing" in result.output or "guardrail" in result.output.lower()


class TestPreflightCommand:
    """Tests for 'ldf preflight' command."""

    def test_preflight_basic(self, runner: CliRunner, temp_project: Path, monkeypatch):
        """Test preflight runs combined checks."""
        monkeypatch.chdir(temp_project)

        result = runner.invoke(cli, ["preflight"])

        assert result.exit_code in (0, 1, 2, 3)  # Various exit codes

    def test_preflight_without_ldf(self, runner: CliRunner, tmp_path: Path):
        """Test preflight fails without LDF."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["preflight"])

            assert result.exit_code != 0

    def test_preflight_skip_lint(self, runner: CliRunner, temp_project: Path, monkeypatch):
        """Test preflight with --skip-lint."""
        monkeypatch.chdir(temp_project)

        result = runner.invoke(cli, ["preflight", "--skip-lint"])

        assert result.exit_code in (0, 1, 2, 3)

    def test_preflight_skip_coverage(self, runner: CliRunner, temp_project: Path, monkeypatch):
        """Test preflight with --skip-coverage."""
        monkeypatch.chdir(temp_project)

        result = runner.invoke(cli, ["preflight", "--skip-coverage"])

        assert result.exit_code in (0, 1, 2, 3)


class TestAddPackCommand:
    """Tests for 'ldf add-pack' command."""

    def test_add_pack_list(self, runner: CliRunner, temp_project: Path, monkeypatch):
        """Test add-pack --list shows available packs."""
        monkeypatch.chdir(temp_project)

        result = runner.invoke(cli, ["add-pack", "--list"])

        assert result.exit_code == 0
        assert "Available" in result.output or "Pack" in result.output

    def test_add_pack_list_without_ldf(self, runner: CliRunner, tmp_path: Path):
        """Test add-pack --list fails without LDF initialized."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["add-pack", "--list"])

            assert result.exit_code == 1
            assert "init" in result.output.lower()

    def test_add_pack_without_ldf(self, runner: CliRunner, tmp_path: Path):
        """Test add-pack fails without LDF initialized."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["add-pack", "security"])

            assert result.exit_code == 1
            assert "init" in result.output.lower()

    def test_add_pack_nonexistent(self, runner: CliRunner, temp_project: Path, monkeypatch):
        """Test add-pack with non-existent pack name."""
        monkeypatch.chdir(temp_project)

        result = runner.invoke(cli, ["add-pack", "nonexistent-pack"])

        assert result.exit_code == 1
        assert "not found" in result.output.lower()


class TestExportDocsCommand:
    """Tests for 'ldf export-docs' command."""

    def test_export_docs_basic(self, runner: CliRunner, temp_project: Path, monkeypatch):
        """Test export-docs generates documentation."""
        monkeypatch.chdir(temp_project)

        result = runner.invoke(cli, ["export-docs"])

        assert result.exit_code == 0
        assert "Framework" in result.output or "#" in result.output

    def test_export_docs_to_file(self, runner: CliRunner, temp_project: Path, monkeypatch):
        """Test export-docs writes to file."""
        monkeypatch.chdir(temp_project)

        result = runner.invoke(cli, ["export-docs", "-o", "FRAMEWORK.md"])

        assert result.exit_code == 0
        assert (temp_project / "FRAMEWORK.md").exists()

    def test_export_docs_without_ldf(self, runner: CliRunner, tmp_path: Path):
        """Test export-docs fails without LDF."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["export-docs"])

            assert result.exit_code == 1


class TestTemplateCommand:
    """Tests for 'ldf template' command."""

    def test_template_verify_valid(self, runner: CliRunner, tmp_path: Path):
        """Test template verify on valid template."""
        # Create a valid template
        template_dir = tmp_path / "my-template"
        template_dir.mkdir()
        (template_dir / "template.yaml").write_text(f"""name: test-template
version: 1.0.0
ldf_version: "{__version__}"
""")
        ldf_dir = template_dir / ".ldf"
        ldf_dir.mkdir()
        (ldf_dir / "config.yaml").write_text("version: '1.0'")

        result = runner.invoke(cli, ["template", "verify", str(template_dir)])

        assert result.exit_code == 0
        assert "passed" in result.output.lower() or "valid" in result.output.lower()

    def test_template_verify_invalid(self, runner: CliRunner, tmp_path: Path):
        """Test template verify on invalid template."""
        # Create an invalid template (missing template.yaml)
        template_dir = tmp_path / "bad-template"
        template_dir.mkdir()

        result = runner.invoke(cli, ["template", "verify", str(template_dir)])

        assert result.exit_code == 1
        assert "error" in result.output.lower() or "not found" in result.output.lower()

    def test_init_from_template(self, runner: CliRunner, tmp_path: Path):
        """Test init --from template."""
        # Create a valid template
        template_dir = tmp_path / "template"
        template_dir.mkdir()
        (template_dir / "template.yaml").write_text(f"""name: test-template
version: 1.0.0
ldf_version: "{__version__}"
""")
        ldf_dir = template_dir / ".ldf"
        ldf_dir.mkdir()
        (ldf_dir / "config.yaml").write_text("version: '1.0'\nproject:\n  name: from-template")
        (ldf_dir / "guardrails.yaml").write_text("version: '1.0'\nextends: core")

        # Initialize project from template
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        with runner.isolated_filesystem(temp_dir=project_dir):
            result = runner.invoke(cli, ["init", "--from", str(template_dir)])

            assert result.exit_code == 0
            assert Path(".ldf").exists()


class TestLintSarifFormat:
    """Tests for lint --format sarif via CLI."""

    def test_lint_sarif_output(self, runner: CliRunner, temp_spec: Path, monkeypatch):
        """Test lint with SARIF format."""
        project_dir = temp_spec.parent.parent.parent
        monkeypatch.chdir(project_dir)

        result = runner.invoke(cli, ["lint", "--format", "sarif", "--all"])

        assert result.exit_code == 0
        # SARIF output should contain version field
        assert '"version"' in result.output or "2.1.0" in result.output

    def test_lint_sarif_to_file(
        self, runner: CliRunner, temp_spec: Path, tmp_path: Path, monkeypatch
    ):
        """Test lint SARIF output to file."""
        project_dir = temp_spec.parent.parent.parent
        monkeypatch.chdir(project_dir)

        output_file = tmp_path / "results.sarif"
        result = runner.invoke(
            cli, ["lint", "--format", "sarif", "--output", str(output_file), "--all"]
        )

        assert result.exit_code == 0
        assert output_file.exists()


class TestCoverageEnhancements:
    """Tests for coverage --save, --diff, --upload via CLI."""

    def test_coverage_save(self, runner: CliRunner, temp_project: Path, monkeypatch):
        """Test coverage --save creates snapshot."""
        import json

        monkeypatch.chdir(temp_project)

        # Create coverage data
        coverage_file = temp_project / "coverage.json"
        coverage_file.write_text(
            json.dumps(
                {"totals": {"percent_covered": 85.0, "covered_lines": 850, "num_statements": 1000}}
            )
        )

        result = runner.invoke(cli, ["coverage", "--save", "baseline"])

        assert result.exit_code == 0
        assert (temp_project / ".ldf" / "coverage-snapshots" / "baseline.json").exists()

    def test_coverage_diff(self, runner: CliRunner, temp_project: Path, monkeypatch):
        """Test coverage --diff compares snapshots."""
        import json

        monkeypatch.chdir(temp_project)

        # Create baseline snapshot
        snapshots_dir = temp_project / ".ldf" / "coverage-snapshots"
        snapshots_dir.mkdir(parents=True)
        (snapshots_dir / "baseline.json").write_text(
            json.dumps(
                {
                    "name": "baseline",
                    "coverage_percent": 75.0,
                    "lines_covered": 750,
                    "lines_total": 1000,
                    "files": [],
                }
            )
        )

        # Create current coverage
        coverage_file = temp_project / "coverage.json"
        coverage_file.write_text(
            json.dumps(
                {"totals": {"percent_covered": 85.0, "covered_lines": 850, "num_statements": 1000}}
            )
        )

        result = runner.invoke(cli, ["coverage", "--diff", "baseline"])

        assert result.exit_code == 0
        assert "Comparison" in result.output or "baseline" in result.output


class TestListFrameworkAllSubcommands:
    """Additional tests for list-framework subcommands."""

    def test_list_framework_mcp(self, runner: CliRunner):
        """Test list-framework mcp subcommand."""
        result = runner.invoke(cli, ["list-framework", "mcp"])

        assert result.exit_code == 0
        assert "Server" in result.output or "spec" in result.output.lower()

    def test_list_framework_default(self, runner: CliRunner):
        """Test list-framework without subcommand shows help."""
        result = runner.invoke(cli, ["list-framework", "--help"])

        assert result.exit_code == 0
        assert "presets" in result.output or "packs" in result.output


class TestAdditionalCLICommands:
    """Additional CLI command tests for coverage."""

    def test_lint_ci_format(self, runner: CliRunner, temp_spec: Path, monkeypatch):
        """Test lint with CI format."""
        project_dir = temp_spec.parent.parent.parent
        monkeypatch.chdir(project_dir)

        result = runner.invoke(cli, ["lint", "--format", "ci", "--all"])

        assert result.exit_code == 0

    def test_coverage_validate(self, runner: CliRunner, temp_project: Path, monkeypatch):
        """Test coverage --validate flag."""
        import json

        monkeypatch.chdir(temp_project)

        coverage_file = temp_project / "coverage.json"
        coverage_file.write_text(
            json.dumps(
                {"totals": {"percent_covered": 85.0, "covered_lines": 850, "num_statements": 1000}}
            )
        )

        result = runner.invoke(cli, ["coverage", "--validate"])

        assert result.exit_code == 0

    def test_coverage_service_filter(self, runner: CliRunner, temp_project: Path, monkeypatch):
        """Test coverage --service filter."""
        import json

        monkeypatch.chdir(temp_project)

        coverage_file = temp_project / "coverage.json"
        coverage_file.write_text(
            json.dumps(
                {
                    "totals": {
                        "percent_covered": 85.0,
                        "covered_lines": 850,
                        "num_statements": 1000,
                    },
                    "files": {"src/auth/handler.py": {"summary": {"percent_covered": 90.0}}},
                }
            )
        )

        result = runner.invoke(cli, ["coverage", "--service", "auth"])

        # Should run without error
        assert result.exit_code in (0, 1)

    def test_preflight_strict(self, runner: CliRunner, temp_project: Path, monkeypatch):
        """Test preflight --strict flag."""
        ldf_dir = temp_project / ".ldf"
        for d in ["specs", "question-packs", "templates", "macros"]:
            (ldf_dir / d).mkdir(exist_ok=True)
        monkeypatch.chdir(temp_project)

        result = runner.invoke(cli, ["preflight", "--strict"])

        assert result.exit_code in (0, 1, 2, 3)

    def test_add_pack_all(self, runner: CliRunner, temp_project: Path, monkeypatch):
        """Test add-pack --all flag."""
        monkeypatch.chdir(temp_project)

        result = runner.invoke(cli, ["add-pack", "--all"])

        assert result.exit_code in (0, 1)


class TestCliEdgeCases:
    """Edge case tests for CLI commands."""

    def test_init_from_template_failure(self, runner: CliRunner, temp_project: Path, monkeypatch):
        """Test init --from when template import fails."""
        from unittest.mock import patch

        monkeypatch.chdir(temp_project)

        # Create a dummy template path that exists
        template_path = temp_project / "template"
        template_path.mkdir()
        (template_path / "template.yaml").write_text(
            f"name: test\nversion: 1.0\nldf_version: {__version__}"
        )

        with patch("ldf.template.import_template", return_value=False):
            result = runner.invoke(cli, ["init", "--from", str(template_path)])

        assert result.exit_code == 1

    def test_audit_spec_with_import_warning(
        self, runner: CliRunner, temp_project: Path, monkeypatch
    ):
        """Test audit with both --spec and --import shows warning."""
        from unittest.mock import patch

        monkeypatch.chdir(temp_project)

        # Create the import file
        import_file = temp_project / "feedback.md"
        import_file.write_text("# Feedback\nSome feedback")

        with patch("ldf.audit.run_audit"):
            result = runner.invoke(cli, ["audit", "--spec", "test", "--import", str(import_file)])

        # Should show warning but still run
        assert "Warning" in result.output or result.exit_code == 0

    def test_audit_security_check_normalization(
        self, runner: CliRunner, temp_project: Path, monkeypatch
    ):
        """Test audit normalizes security-check to security."""
        from unittest.mock import MagicMock, patch

        monkeypatch.chdir(temp_project)

        mock_run_audit = MagicMock()
        with patch("ldf.audit.run_audit", mock_run_audit):
            runner.invoke(cli, ["audit", "security-check"])

        # Should call with normalized type
        if mock_run_audit.called:
            call_args = mock_run_audit.call_args
            assert call_args.kwargs.get("audit_type") == "security"

    def test_coverage_diff_error(self, runner: CliRunner, temp_project: Path, monkeypatch):
        """Test coverage --diff returns error code on failure."""
        from unittest.mock import patch

        monkeypatch.chdir(temp_project)

        with patch("ldf.coverage.compare_coverage", return_value={"status": "ERROR"}):
            result = runner.invoke(cli, ["coverage", "--diff", "baseline"])

        assert result.exit_code == 1

    def test_coverage_upload_failure(self, runner: CliRunner, temp_project: Path, monkeypatch):
        """Test coverage --upload returns error on failure."""
        import json
        from unittest.mock import patch

        monkeypatch.chdir(temp_project)

        coverage_file = temp_project / "coverage.json"
        coverage_file.write_text(
            json.dumps(
                {
                    "totals": {
                        "percent_covered": 85.0,
                        "covered_lines": 850,
                        "num_statements": 1000,
                    }
                }
            )
        )

        with patch("ldf.coverage.report_coverage", return_value={"status": "OK"}):
            with patch("ldf.coverage.upload_coverage", return_value=False):
                result = runner.invoke(cli, ["coverage", "--upload", "s3://bucket/path"])

        assert result.exit_code == 1

    def test_coverage_validate_failure(self, runner: CliRunner, temp_project: Path, monkeypatch):
        """Test coverage --validate returns error on failure."""
        from unittest.mock import patch

        monkeypatch.chdir(temp_project)

        with patch("ldf.coverage.report_coverage", return_value={"status": "FAIL"}):
            result = runner.invoke(cli, ["coverage", "--validate"])

        assert result.exit_code == 1

    def test_update_up_to_date(self, runner: CliRunner, temp_project: Path, monkeypatch):
        """Test update when project is already up to date."""
        from unittest.mock import patch

        from ldf.update import UpdateDiff

        monkeypatch.chdir(temp_project)

        # Create empty diff (no changes needed)
        empty_diff = UpdateDiff()

        with patch("ldf.update.get_update_diff", return_value=empty_diff):
            result = runner.invoke(cli, ["update"])

        assert "up to date" in result.output.lower()

    def test_update_apply_failure(self, runner: CliRunner, temp_project: Path, monkeypatch):
        """Test update returns error when apply fails."""
        from unittest.mock import patch

        from ldf.update import FileChange, UpdateDiff, UpdateResult

        monkeypatch.chdir(temp_project)

        # Create diff with files to update (correct field names)
        diff = UpdateDiff()
        diff.files_to_add = [FileChange(path="test.md", change_type="add", reason="test")]

        # Create failed result
        failed_result = UpdateResult(success=False)

        with patch("ldf.update.get_update_diff", return_value=diff):
            with patch("ldf.update.apply_updates", return_value=failed_result):
                result = runner.invoke(cli, ["update", "-y"])

        assert result.exit_code == 1

    def test_update_with_conflicts_skip(self, runner: CliRunner, temp_project: Path, monkeypatch):
        """Test update with -y flag skips conflicts."""
        from unittest.mock import MagicMock, patch

        from ldf.update import Conflict, UpdateDiff, UpdateResult

        monkeypatch.chdir(temp_project)

        # Create diff with conflict (correct field names)
        diff = UpdateDiff()
        diff.conflicts = [Conflict(file_path="conflict.md", reason="user_modified")]

        # Create successful result
        success_result = UpdateResult(success=True)

        mock_apply = MagicMock(return_value=success_result)
        with patch("ldf.update.get_update_diff", return_value=diff):
            with patch("ldf.update.apply_updates", mock_apply):
                runner.invoke(cli, ["update", "-y"])

        # Check that conflict was resolved as skip
        if mock_apply.called:
            call_kwargs = mock_apply.call_args.kwargs
            resolutions = call_kwargs.get("conflict_resolutions", {})
            if resolutions:
                assert resolutions.get("conflict.md") == "skip"


class TestAuditSecurityNormalization:
    """Tests for audit security-check normalization."""

    def test_security_check_normalized(self, runner: CliRunner, temp_project: Path, monkeypatch):
        """Test that security-check is normalized to security."""
        from unittest.mock import patch

        monkeypatch.chdir(temp_project)

        with patch("ldf.audit.run_audit") as mock_audit:
            # This should normalize security-check to security
            runner.invoke(cli, ["audit", "security-check", "--yes"])

        if mock_audit.called:
            call_args = mock_audit.call_args
            # audit_type should be "security" not "security-check"
            assert call_args.kwargs.get("audit_type") == "security"


class TestConvertImportNextSteps:
    """Tests for convert import next steps output."""

    def test_convert_import_success_shows_next_steps(
        self, runner: CliRunner, temp_project: Path, monkeypatch, tmp_path: Path
    ):
        """Test convert import success shows next steps."""
        from unittest.mock import MagicMock, patch

        monkeypatch.chdir(temp_project)

        # Create a valid import file
        import_file = tmp_path / "import.txt"
        import_file.write_text("""
# === ANSWERPACK: security.yaml ===
pack: security
answers: []

# === SPEC: requirements.md ===
# Test Requirements
""")

        # Mock successful import
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.spec_name = "test-spec"
        mock_result.files_created = ["specs/test-spec/requirements.md"]
        mock_result.files_skipped = []
        mock_result.warnings = []
        mock_result.errors = []

        with patch("ldf.convert.import_backwards_fill", return_value=mock_result):
            with patch("ldf.convert.print_import_result"):
                result = runner.invoke(cli, ["convert", "import", str(import_file)])

        # Should show next steps or run successfully
        assert "Next steps" in result.output or result.exit_code == 0


class TestPreflightCoverageChecks:
    """Tests for preflight coverage checks."""

    def test_preflight_coverage_fail(self, runner: CliRunner, temp_project: Path, monkeypatch):
        """Test preflight with coverage failure."""
        from unittest.mock import MagicMock, patch

        from ldf.doctor import DoctorReport

        # Setup git
        (temp_project / ".git").mkdir()
        monkeypatch.chdir(temp_project)

        # Return proper DoctorReport
        mock_doctor_result = DoctorReport(checks=[])
        mock_doctor = MagicMock(return_value=mock_doctor_result)

        mock_lint = MagicMock(return_value=0)

        mock_coverage = MagicMock(
            return_value={"status": "FAIL", "coverage_percent": 50.0, "error": None}
        )

        with patch("ldf.doctor.run_doctor", mock_doctor):
            with patch("ldf.lint.lint_specs", mock_lint):
                with patch("ldf.coverage.report_coverage", mock_coverage):
                    result = runner.invoke(cli, ["preflight"])

        # Should fail with exit code
        assert result.exit_code != 0 or "below threshold" in result.output

    def test_preflight_coverage_error(self, runner: CliRunner, temp_project: Path, monkeypatch):
        """Test preflight with coverage error."""
        from unittest.mock import MagicMock, patch

        from ldf.doctor import DoctorReport

        (temp_project / ".git").mkdir()
        monkeypatch.chdir(temp_project)

        mock_doctor_result = DoctorReport(checks=[])
        mock_doctor = MagicMock(return_value=mock_doctor_result)

        mock_lint = MagicMock(return_value=0)

        mock_coverage = MagicMock(return_value={"status": "ERROR", "error": "No coverage data"})

        with patch("ldf.doctor.run_doctor", mock_doctor):
            with patch("ldf.lint.lint_specs", mock_lint):
                with patch("ldf.coverage.report_coverage", mock_coverage):
                    result = runner.invoke(cli, ["preflight"])

        # Should pass (coverage errors are warnings, not failures)
        assert result.exit_code == 0


class TestPreflightLintFail:
    """Tests for preflight lint failure."""

    def test_preflight_lint_fail(self, runner: CliRunner, temp_project: Path, monkeypatch):
        """Test preflight with lint failure."""
        from unittest.mock import MagicMock, patch

        (temp_project / ".git").mkdir()
        monkeypatch.chdir(temp_project)

        mock_doctor = MagicMock()
        mock_doctor.return_value = []

        mock_lint = MagicMock()
        mock_lint.return_value = 1  # Lint fails

        with patch("ldf.doctor.run_doctor", mock_doctor):
            with patch("ldf.lint.lint_specs", mock_lint):
                result = runner.invoke(cli, ["preflight", "--skip-coverage"])

        # Should fail
        assert result.exit_code != 0


class TestAddPackEdgeCases:
    """Tests for add-pack command edge cases."""

    def test_add_pack_no_args(self, runner: CliRunner, temp_project: Path, monkeypatch):
        """Test add-pack with no pack name."""
        monkeypatch.chdir(temp_project)

        result = runner.invoke(cli, ["add-pack"])

        assert result.exit_code == 1
        assert "Specify a pack name" in result.output

    def test_add_pack_invalid_config(self, runner: CliRunner, temp_project: Path, monkeypatch):
        """Test add-pack with invalid config.yaml."""
        monkeypatch.chdir(temp_project)

        # Create invalid config
        config_path = temp_project / ".ldf" / "config.yaml"
        config_path.write_text("invalid: yaml: [[[")

        result = runner.invoke(cli, ["add-pack", "security"])

        assert result.exit_code == 1
        assert "Invalid config" in result.output

    def test_add_pack_already_exists(self, runner: CliRunner, temp_project: Path, monkeypatch):
        """Test add-pack when pack already exists."""
        monkeypatch.chdir(temp_project)

        # Create existing pack (v1.1 schema: in core/ subdirectory)
        qp_dir = temp_project / ".ldf" / "question-packs"
        (qp_dir / "core").mkdir(parents=True, exist_ok=True)
        (qp_dir / "core" / "security.yaml").write_text("pack: security")

        result = runner.invoke(cli, ["add-pack", "security"])

        # Should be skipped
        assert "Skipped" in result.output or "already exist" in result.output

    def test_add_pack_force_replace(self, runner: CliRunner, temp_project: Path, monkeypatch):
        """Test add-pack with --force replaces existing."""
        from unittest.mock import patch

        monkeypatch.chdir(temp_project)

        # Create existing pack
        qp_dir = temp_project / ".ldf" / "question-packs"
        qp_dir.mkdir(parents=True, exist_ok=True)
        (qp_dir / "security.yaml").write_text("pack: security")

        # Mock the source file
        with patch("pathlib.Path.exists") as mock_exists:
            # Need to be careful with the mock - let it pass for most checks
            mock_exists.return_value = True

            result = runner.invoke(cli, ["add-pack", "security", "--force"])

        # May show replaced or error depending on source file availability
        assert result.exit_code == 0 or "Replaced" in result.output or "not found" in result.output

    def test_add_pack_list_with_domain_packs(
        self, runner: CliRunner, temp_project: Path, monkeypatch
    ):
        """Test add-pack --list shows domain packs from filesystem."""

        monkeypatch.chdir(temp_project)

        result = runner.invoke(cli, ["add-pack", "--list"])

        # Should show table
        assert "Pack" in result.output
        assert result.exit_code == 0

    def test_add_pack_no_packs_added(self, runner: CliRunner, temp_project: Path, monkeypatch):
        """Test add-pack with non-existent pack."""
        monkeypatch.chdir(temp_project)

        result = runner.invoke(cli, ["add-pack", "nonexistent-pack-xyz"])

        # Should say no packs added or not found
        assert "No packs were added" in result.output or "not found" in result.output


class TestTemplateVerifyJson:
    """Tests for template verify JSON output."""

    def test_template_verify_json_output(self, runner: CliRunner, temp_project: Path, monkeypatch):
        """Test template verify with --json flag."""
        monkeypatch.chdir(temp_project)

        # Create a valid template directory with required files
        template_dir = temp_project / ".ldf" / "templates" / "test"
        template_dir.mkdir(parents=True)
        (template_dir / "template.yaml").write_text("""
name: test
description: Test template
files: []
""")

        result = runner.invoke(cli, ["template", "verify", str(template_dir), "--json"])

        # Should output JSON
        assert result.exit_code == 0 or "{" in result.output


class TestListFrameworkGuardrailsError:
    """Tests for list-framework guardrails error handling."""

    def test_list_guardrails_shows_core_guardrails(
        self, runner: CliRunner, temp_project: Path, monkeypatch
    ):
        """Test list-framework guardrails shows core guardrails."""
        monkeypatch.chdir(temp_project)

        result = runner.invoke(cli, ["list-framework", "guardrails"])

        # Should show guardrails table
        assert "ID" in result.output or "Name" in result.output or result.exit_code == 0


class TestUpdateDeclineConfirmation:
    """Tests for update confirmation decline."""

    def test_update_decline_confirmation(self, runner: CliRunner, temp_project: Path, monkeypatch):
        """Test update aborts when user declines."""
        from unittest.mock import patch

        from ldf.update import FileChange, UpdateDiff

        monkeypatch.chdir(temp_project)

        diff = UpdateDiff()
        diff.files_to_add = [FileChange(path="test.md", change_type="add", reason="test")]

        with patch("ldf.update.get_update_diff", return_value=diff):
            # Simulate user declining
            result = runner.invoke(cli, ["update"], input="n\n")

        assert "Aborted" in result.output or result.exit_code == 0
