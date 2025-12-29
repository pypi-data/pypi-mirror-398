"""Tests for ldf.detection module."""

from ldf import __version__
from ldf.detection import (
    REQUIRED_DIRS,
    DetectionResult,
    ProjectState,
    check_ldf_completeness,
    detect_project_state,
    get_specs_summary,
)


class TestProjectState:
    """Tests for ProjectState enum."""

    def test_state_values(self):
        """Test that all expected states exist."""
        assert ProjectState.NEW.value == "new"
        assert ProjectState.CURRENT.value == "current"
        assert ProjectState.OUTDATED.value == "outdated"
        assert ProjectState.LEGACY.value == "legacy"
        assert ProjectState.PARTIAL.value == "partial"
        assert ProjectState.CORRUPTED.value == "corrupted"


class TestDetectionResult:
    """Tests for DetectionResult dataclass."""

    def test_to_dict(self, tmp_path):
        """Test conversion to dictionary."""
        result = DetectionResult(
            state=ProjectState.NEW,
            project_root=tmp_path,
            installed_version=__version__,
            project_version=None,
            has_config=False,
            has_guardrails=False,
            has_specs_dir=False,
            has_answerpacks_dir=False,
            has_question_packs_dir=False,
            has_templates=False,
            has_macros=False,
            has_agent_md=False,
            has_agent_commands=False,
            missing_files=["config.yaml"],
            invalid_files=[],
            recommended_action="Run 'ldf init'",
            recommended_command="ldf init",
        )

        d = result.to_dict()
        assert d["state"] == "new"
        assert d["installed_version"] == __version__
        assert d["project_version"] is None
        assert d["completeness"]["config"] is False
        assert "config.yaml" in d["missing_files"]
        assert d["recommended_command"] == "ldf init"

    def test_to_json(self, tmp_path):
        """Test conversion to JSON string."""
        result = DetectionResult(
            state=ProjectState.CURRENT,
            project_root=tmp_path,
            installed_version=__version__,
            project_version=__version__,
            has_config=True,
            has_guardrails=True,
            has_specs_dir=True,
            has_answerpacks_dir=True,
            has_question_packs_dir=True,
            has_templates=True,
            has_macros=True,
            has_agent_md=True,
            has_agent_commands=True,
        )

        json_str = result.to_json()
        assert '"state": "current"' in json_str
        assert f'"installed_version": "{__version__}"' in json_str


class TestDetectProjectState:
    """Tests for detect_project_state function."""

    def test_new_project_no_ldf_dir(self, tmp_path):
        """Test detection of new project without .ldf directory."""
        result = detect_project_state(tmp_path)

        assert result.state == ProjectState.NEW
        assert result.project_root == tmp_path
        assert result.installed_version == __version__
        assert result.project_version is None
        assert result.has_config is False
        assert result.recommended_command == "ldf init"

    def test_corrupted_ldf_is_file(self, tmp_path):
        """Test detection when .ldf exists as a file, not directory."""
        ldf_file = tmp_path / ".ldf"
        ldf_file.write_text("not a directory")

        result = detect_project_state(tmp_path)

        assert result.state == ProjectState.CORRUPTED
        assert ".ldf (not a directory)" in result.invalid_files
        assert "force" in result.recommended_command

    def test_current_project_matching_version(self, tmp_path):
        """Test detection of up-to-date project."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()

        # Create required structure (v1.1 schema)
        config_content = f"_schema_version: '1.1'\nldf:\n  version: '{__version__}'"
        (ldf_dir / "config.yaml").write_text(config_content)
        (ldf_dir / "guardrails.yaml").write_text("guardrails: []")
        (ldf_dir / "specs").mkdir()
        (ldf_dir / "answerpacks").mkdir()
        (ldf_dir / "templates").mkdir()
        (ldf_dir / "question-packs").mkdir()
        (ldf_dir / "macros").mkdir()
        (ldf_dir / "templates" / "requirements.md").write_text("# Requirements")
        (ldf_dir / "templates" / "design.md").write_text("# Design")
        (ldf_dir / "templates" / "tasks.md").write_text("# Tasks")
        (ldf_dir / "macros" / "clarify-first.md").write_text("# Clarify")
        (ldf_dir / "macros" / "coverage-gate.md").write_text("# Coverage")
        (ldf_dir / "macros" / "task-guardrails.md").write_text("# Task")
        (ldf_dir / "question-packs" / "core.yaml").write_text("pack: core")

        result = detect_project_state(tmp_path)

        assert result.state == ProjectState.CURRENT
        assert result.project_version == __version__
        assert result.has_config is True
        assert result.has_guardrails is True
        assert result.recommended_command is None

    def test_outdated_project_older_version(self, tmp_path):
        """Test detection of project with older framework version."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()

        # Create structure with old version (v1.1 schema)
        config_content = "_schema_version: '1.1'\nldf:\n  version: '0.0.1'"
        (ldf_dir / "config.yaml").write_text(config_content)
        (ldf_dir / "guardrails.yaml").write_text("guardrails: []")
        (ldf_dir / "specs").mkdir()
        (ldf_dir / "answerpacks").mkdir()
        (ldf_dir / "templates").mkdir()
        (ldf_dir / "question-packs").mkdir()
        (ldf_dir / "macros").mkdir()
        (ldf_dir / "templates" / "requirements.md").write_text("# Requirements")
        (ldf_dir / "templates" / "design.md").write_text("# Design")
        (ldf_dir / "templates" / "tasks.md").write_text("# Tasks")
        (ldf_dir / "macros" / "clarify-first.md").write_text("# Clarify")
        (ldf_dir / "macros" / "coverage-gate.md").write_text("# Coverage")
        (ldf_dir / "macros" / "task-guardrails.md").write_text("# Task")
        (ldf_dir / "question-packs" / "core.yaml").write_text("pack: core")

        result = detect_project_state(tmp_path)

        assert result.state == ProjectState.OUTDATED
        assert result.project_version == "0.0.1"
        assert "update" in result.recommended_command

    def test_legacy_project_no_version(self, tmp_path):
        """Test detection of legacy project without framework_version."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()

        # Create config without framework_version
        (ldf_dir / "config.yaml").write_text("project_name: test")
        (ldf_dir / "guardrails.yaml").write_text("guardrails: []")
        (ldf_dir / "specs").mkdir()
        (ldf_dir / "answerpacks").mkdir()
        (ldf_dir / "templates").mkdir()
        (ldf_dir / "question-packs").mkdir()
        (ldf_dir / "macros").mkdir()
        (ldf_dir / "templates" / "requirements.md").write_text("# Requirements")
        (ldf_dir / "templates" / "design.md").write_text("# Design")
        (ldf_dir / "templates" / "tasks.md").write_text("# Tasks")
        (ldf_dir / "macros" / "clarify-first.md").write_text("# Clarify")
        (ldf_dir / "macros" / "coverage-gate.md").write_text("# Coverage")
        (ldf_dir / "macros" / "task-guardrails.md").write_text("# Task")
        (ldf_dir / "question-packs" / "core.yaml").write_text("pack: core")

        result = detect_project_state(tmp_path)

        assert result.state == ProjectState.LEGACY
        assert result.project_version is None
        assert "update" in result.recommended_command

    def test_partial_project_missing_templates(self, tmp_path):
        """Test detection of project missing some required files."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()

        # Create minimal structure (v1.1 schema)
        config_content = f"_schema_version: '1.1'\nldf:\n  version: '{__version__}'"
        (ldf_dir / "config.yaml").write_text(config_content)
        (ldf_dir / "guardrails.yaml").write_text("guardrails: []")
        (ldf_dir / "specs").mkdir()
        (ldf_dir / "answerpacks").mkdir()
        (ldf_dir / "templates").mkdir()
        (ldf_dir / "question-packs").mkdir()
        (ldf_dir / "question-packs" / "core.yaml").write_text("pack: core")
        # Missing template files and macros

        result = detect_project_state(tmp_path)

        assert result.state == ProjectState.PARTIAL
        assert len(result.missing_files) > 0
        assert "repair" in result.recommended_command

    def test_corrupted_project_invalid_yaml(self, tmp_path):
        """Test detection of project with invalid YAML config."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()

        # Create invalid YAML
        (ldf_dir / "config.yaml").write_text("invalid: yaml: content: [")
        (ldf_dir / "guardrails.yaml").write_text("guardrails: []")
        (ldf_dir / "specs").mkdir()
        (ldf_dir / "answerpacks").mkdir()

        result = detect_project_state(tmp_path)

        assert result.state == ProjectState.CORRUPTED
        assert len(result.invalid_files) > 0
        assert "force" in result.recommended_command

    def test_corrupted_project_empty_config(self, tmp_path):
        """Test detection of project with empty config file."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()

        # Create empty config
        (ldf_dir / "config.yaml").write_text("")
        (ldf_dir / "guardrails.yaml").write_text("guardrails: []")
        (ldf_dir / "specs").mkdir()
        (ldf_dir / "answerpacks").mkdir()

        result = detect_project_state(tmp_path)

        assert result.state == ProjectState.CORRUPTED
        assert any("empty" in f for f in result.invalid_files)

    def test_detection_uses_cwd_when_no_path(self, tmp_path, monkeypatch):
        """Test that detection uses current directory when no path given."""
        monkeypatch.chdir(tmp_path)
        result = detect_project_state()
        assert result.project_root == tmp_path

    def test_detection_with_agent_md(self, tmp_path):
        """Test detection recognizes AGENT.md."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()
        (tmp_path / "AGENT.md").write_text("# Agent Instructions")
        (ldf_dir / "config.yaml").write_text(f"framework_version: '{__version__}'")
        (ldf_dir / "guardrails.yaml").write_text("guardrails: []")
        for d in ["specs", "answerpacks", "templates", "question-packs", "macros"]:
            (ldf_dir / d).mkdir()
        (ldf_dir / "templates" / "requirements.md").write_text("#")
        (ldf_dir / "templates" / "design.md").write_text("#")
        (ldf_dir / "templates" / "tasks.md").write_text("#")
        (ldf_dir / "macros" / "clarify-first.md").write_text("#")
        (ldf_dir / "macros" / "coverage-gate.md").write_text("#")
        (ldf_dir / "macros" / "task-guardrails.md").write_text("#")
        (ldf_dir / "question-packs" / "core.yaml").write_text("pack: core")

        result = detect_project_state(tmp_path)
        assert result.has_agent_md is True

    def test_detection_with_agent_commands(self, tmp_path):
        """Test detection recognizes .agent/commands directory."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()
        agent_commands = tmp_path / ".agent" / "commands"
        agent_commands.mkdir(parents=True)
        (ldf_dir / "config.yaml").write_text(f"framework_version: '{__version__}'")
        (ldf_dir / "guardrails.yaml").write_text("guardrails: []")
        for d in ["specs", "answerpacks", "templates", "question-packs", "macros"]:
            (ldf_dir / d).mkdir()
        (ldf_dir / "templates" / "requirements.md").write_text("#")
        (ldf_dir / "templates" / "design.md").write_text("#")
        (ldf_dir / "templates" / "tasks.md").write_text("#")
        (ldf_dir / "macros" / "clarify-first.md").write_text("#")
        (ldf_dir / "macros" / "coverage-gate.md").write_text("#")
        (ldf_dir / "macros" / "task-guardrails.md").write_text("#")
        (ldf_dir / "question-packs" / "core.yaml").write_text("pack: core")

        result = detect_project_state(tmp_path)
        assert result.has_agent_commands is True


class TestCheckLdfCompleteness:
    """Tests for check_ldf_completeness function."""

    def test_empty_ldf_dir(self, tmp_path):
        """Test completeness check on empty .ldf directory."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()

        missing, invalid = check_ldf_completeness(ldf_dir)

        # Should be missing required files and dirs
        assert "config.yaml" in missing
        assert "guardrails.yaml" in missing
        assert any("specs" in m for m in missing)

    def test_complete_ldf_dir(self, tmp_path):
        """Test completeness check on complete .ldf directory."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()

        # Create all required files
        (ldf_dir / "config.yaml").write_text(f"framework_version: '{__version__}'")
        (ldf_dir / "guardrails.yaml").write_text("guardrails: []")
        for d in REQUIRED_DIRS:
            (ldf_dir / d).mkdir()
        (ldf_dir / "macros").mkdir()  # macros not in REQUIRED_DIRS but needed for completeness
        (ldf_dir / "templates" / "requirements.md").write_text("#")
        (ldf_dir / "templates" / "design.md").write_text("#")
        (ldf_dir / "templates" / "tasks.md").write_text("#")
        (ldf_dir / "macros" / "clarify-first.md").write_text("#")
        (ldf_dir / "macros" / "coverage-gate.md").write_text("#")
        (ldf_dir / "macros" / "task-guardrails.md").write_text("#")
        (ldf_dir / "question-packs" / "core.yaml").write_text("pack: core")

        missing, invalid = check_ldf_completeness(ldf_dir)

        assert len(missing) == 0
        assert len(invalid) == 0

    def test_directory_is_file(self, tmp_path):
        """Test detection of file where directory expected."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()

        # Create 'specs' as a file instead of directory
        (ldf_dir / "config.yaml").write_text(f"framework_version: '{__version__}'")
        (ldf_dir / "guardrails.yaml").write_text("guardrails: []")
        (ldf_dir / "specs").write_text("not a directory")

        missing, invalid = check_ldf_completeness(ldf_dir)

        assert "specs (not a directory)" in invalid


class TestGetSpecsSummary:
    """Tests for get_specs_summary function."""

    def test_no_specs_dir(self, tmp_path):
        """Test summary when specs directory doesn't exist."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()

        summary = get_specs_summary(ldf_dir)
        assert summary == []

    def test_empty_specs_dir(self, tmp_path):
        """Test summary when specs directory is empty."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()
        (ldf_dir / "specs").mkdir()

        summary = get_specs_summary(ldf_dir)
        assert summary == []

    def test_specs_with_various_states(self, tmp_path):
        """Test summary with specs in various states."""
        ldf_dir = tmp_path / ".ldf"
        specs_dir = ldf_dir / "specs"
        specs_dir.mkdir(parents=True)

        # Spec with only requirements
        (specs_dir / "auth").mkdir()
        (specs_dir / "auth" / "requirements.md").write_text("# Auth Requirements")

        # Spec with requirements and design
        (specs_dir / "billing").mkdir()
        (specs_dir / "billing" / "requirements.md").write_text("# Billing Requirements")
        (specs_dir / "billing" / "design.md").write_text("# Billing Design")

        # Spec with all three
        (specs_dir / "complete").mkdir()
        (specs_dir / "complete" / "requirements.md").write_text("# Complete Requirements")
        (specs_dir / "complete" / "design.md").write_text("# Complete Design")
        (specs_dir / "complete" / "tasks.md").write_text("# Complete Tasks")

        # Empty spec
        (specs_dir / "empty").mkdir()

        summary = get_specs_summary(ldf_dir)

        # Should be sorted by name
        assert len(summary) == 4
        assert summary[0]["name"] == "auth"
        assert summary[0]["status"] == "requirements"

        assert summary[1]["name"] == "billing"
        assert summary[1]["status"] == "design"

        assert summary[2]["name"] == "complete"
        assert summary[2]["status"] == "tasks"

        assert summary[3]["name"] == "empty"
        assert summary[3]["status"] == "empty"

    def test_skips_non_directories(self, tmp_path):
        """Test that non-directory items in specs are skipped."""
        ldf_dir = tmp_path / ".ldf"
        specs_dir = ldf_dir / "specs"
        specs_dir.mkdir(parents=True)

        (specs_dir / "valid-spec").mkdir()
        (specs_dir / "valid-spec" / "requirements.md").write_text("# Valid")
        (specs_dir / "not-a-spec.txt").write_text("just a file")

        summary = get_specs_summary(ldf_dir)

        assert len(summary) == 1
        assert summary[0]["name"] == "valid-spec"


class TestDetectProjectStateEdgeCases:
    """Edge case tests for detect_project_state."""

    def test_config_is_list_not_dict(self, tmp_path):
        """Test detection when config.yaml contains a list instead of dict."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()

        (ldf_dir / "config.yaml").write_text("- item1\n- item2\n- item3")
        (ldf_dir / "guardrails.yaml").write_text("guardrails: []")
        (ldf_dir / "specs").mkdir()
        (ldf_dir / "answerpacks").mkdir()

        result = detect_project_state(tmp_path)

        assert result.state == ProjectState.CORRUPTED
        assert any("invalid format" in f for f in result.invalid_files)

    def test_config_read_error(self, tmp_path, monkeypatch):
        """Test detection when config.yaml cannot be read."""

        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()
        (ldf_dir / "config.yaml").write_text("valid: yaml")
        (ldf_dir / "guardrails.yaml").write_text("guardrails: []")
        (ldf_dir / "specs").mkdir()
        (ldf_dir / "answerpacks").mkdir()

        # Mock open to raise an exception
        original_open = open

        def mock_open(file, *args, **kwargs):
            if "config.yaml" in str(file):
                raise PermissionError("Access denied")
            return original_open(file, *args, **kwargs)

        monkeypatch.setattr("builtins.open", mock_open)

        result = detect_project_state(tmp_path)

        assert result.state == ProjectState.CORRUPTED
        assert any("read error" in f for f in result.invalid_files)

    def test_project_newer_than_installed(self, tmp_path):
        """Test detection when project version is newer than installed."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()

        # Set a "future" version (v1.1 schema)
        config_content = "_schema_version: '1.1'\nldf:\n  version: '999.999.999'"
        (ldf_dir / "config.yaml").write_text(config_content)
        (ldf_dir / "guardrails.yaml").write_text("guardrails: []")
        (ldf_dir / "specs").mkdir()
        (ldf_dir / "answerpacks").mkdir()
        (ldf_dir / "templates").mkdir()
        (ldf_dir / "question-packs").mkdir()
        (ldf_dir / "macros").mkdir()
        (ldf_dir / "templates" / "requirements.md").write_text("#")
        (ldf_dir / "templates" / "design.md").write_text("#")
        (ldf_dir / "templates" / "tasks.md").write_text("#")
        (ldf_dir / "macros" / "clarify-first.md").write_text("#")
        (ldf_dir / "macros" / "coverage-gate.md").write_text("#")
        (ldf_dir / "macros" / "task-guardrails.md").write_text("#")
        (ldf_dir / "question-packs" / "core.yaml").write_text("pack: core")

        result = detect_project_state(tmp_path)

        assert result.state == ProjectState.CURRENT
        assert "newer LDF" in result.recommended_action

    def test_version_comparison_without_packaging(self, tmp_path, monkeypatch):
        """Test version comparison when packaging module unavailable."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()

        # Use v1.1 schema
        config_content = "_schema_version: '1.1'\nldf:\n  version: '0.0.1'"
        (ldf_dir / "config.yaml").write_text(config_content)
        (ldf_dir / "guardrails.yaml").write_text("guardrails: []")
        (ldf_dir / "specs").mkdir()
        (ldf_dir / "answerpacks").mkdir()
        (ldf_dir / "templates").mkdir()
        (ldf_dir / "question-packs").mkdir()
        (ldf_dir / "macros").mkdir()
        (ldf_dir / "templates" / "requirements.md").write_text("#")
        (ldf_dir / "templates" / "design.md").write_text("#")
        (ldf_dir / "templates" / "tasks.md").write_text("#")
        (ldf_dir / "macros" / "clarify-first.md").write_text("#")
        (ldf_dir / "macros" / "coverage-gate.md").write_text("#")
        (ldf_dir / "macros" / "task-guardrails.md").write_text("#")
        (ldf_dir / "question-packs" / "core.yaml").write_text("pack: core")

        # Mock packaging.version.Version to raise an exception
        import sys

        original_modules = dict(sys.modules)
        if "packaging.version" in sys.modules:
            del sys.modules["packaging.version"]
        if "packaging" in sys.modules:
            del sys.modules["packaging"]

        # Force the fallback path by making Version raise
        from unittest.mock import MagicMock

        mock_packaging = MagicMock()
        mock_packaging.version.Version.side_effect = Exception("No packaging")
        sys.modules["packaging"] = mock_packaging
        sys.modules["packaging.version"] = mock_packaging.version

        try:
            result = detect_project_state(tmp_path)
            assert result.state == ProjectState.OUTDATED
            assert (
                "Version mismatch" in result.recommended_action
                or "update" in result.recommended_command.lower()
            )
        finally:
            sys.modules.update(original_modules)

    def test_ldf_dir_exists_but_no_config(self, tmp_path):
        """Test detection when .ldf directory exists but config.yaml is missing."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()

        # Create some structure but no config.yaml
        (ldf_dir / "guardrails.yaml").write_text("guardrails: []")
        (ldf_dir / "specs").mkdir()
        (ldf_dir / "answerpacks").mkdir()

        result = detect_project_state(tmp_path)

        # Should be CORRUPTED with "Missing or invalid config" message
        assert result.state == ProjectState.CORRUPTED
        assert (
            "missing" in result.recommended_action.lower()
            or "invalid" in result.recommended_action.lower()
        )
        assert result.has_config is False


class TestCheckLdfCompletenessEdgeCases:
    """Edge case tests for check_ldf_completeness."""

    def test_missing_macros_in_existing_dir(self, tmp_path):
        """Test detection of missing macros when macros dir exists."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()

        (ldf_dir / "config.yaml").write_text(f"framework_version: '{__version__}'")
        (ldf_dir / "guardrails.yaml").write_text("guardrails: []")
        for d in REQUIRED_DIRS:
            (ldf_dir / d).mkdir()
        (ldf_dir / "macros").mkdir()  # Create macros dir but leave it empty
        (ldf_dir / "templates" / "requirements.md").write_text("#")
        (ldf_dir / "templates" / "design.md").write_text("#")
        (ldf_dir / "templates" / "tasks.md").write_text("#")
        (ldf_dir / "question-packs" / "core.yaml").write_text("pack: core")

        missing, invalid = check_ldf_completeness(ldf_dir)

        # Should be missing macro files
        assert any("clarify-first" in m for m in missing)

    def test_empty_question_packs_dir(self, tmp_path):
        """Test detection of empty question-packs directory."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()

        (ldf_dir / "config.yaml").write_text(f"framework_version: '{__version__}'")
        (ldf_dir / "guardrails.yaml").write_text("guardrails: []")
        for d in REQUIRED_DIRS:
            (ldf_dir / d).mkdir()
        (ldf_dir / "templates" / "requirements.md").write_text("#")
        (ldf_dir / "templates" / "design.md").write_text("#")
        (ldf_dir / "templates" / "tasks.md").write_text("#")
        # Don't create any .yaml files in question-packs

        missing, invalid = check_ldf_completeness(ldf_dir)

        # Should indicate missing question packs
        assert any("no packs found" in m for m in missing)


class TestGetSpecsSummarySymlinkSecurity:
    """Security tests for symlink filtering in get_specs_summary."""

    def test_filters_symlink_escaping_specs_dir(self, tmp_path):
        """Test that get_specs_summary filters out symlinks pointing outside specs dir."""
        import os

        if os.name == "nt":
            import pytest
            pytest.skip("Symlink tests not supported on Windows")

        ldf_dir = tmp_path / ".ldf"
        specs_dir = ldf_dir / "specs"
        specs_dir.mkdir(parents=True)

        # Create a real spec
        (specs_dir / "real-spec").mkdir()
        (specs_dir / "real-spec" / "requirements.md").write_text("# Real")

        # Create a symlink pointing outside specs directory
        evil_link = specs_dir / "evil-link"
        evil_link.symlink_to("/etc")

        summary = get_specs_summary(ldf_dir)

        # Should include real spec but not the symlink
        spec_names = [s["name"] for s in summary]
        assert "real-spec" in spec_names
        assert "evil-link" not in spec_names

    def test_filters_hidden_directories(self, tmp_path):
        """Test that get_specs_summary filters out hidden directories."""
        ldf_dir = tmp_path / ".ldf"
        specs_dir = ldf_dir / "specs"
        specs_dir.mkdir(parents=True)

        # Create a visible spec
        (specs_dir / "visible-spec").mkdir()
        (specs_dir / "visible-spec" / "requirements.md").write_text("# Visible")

        # Create a hidden spec (should be filtered)
        (specs_dir / ".hidden-spec").mkdir()
        (specs_dir / ".hidden-spec" / "requirements.md").write_text("# Hidden")

        summary = get_specs_summary(ldf_dir)

        spec_names = [s["name"] for s in summary]
        assert "visible-spec" in spec_names
        assert ".hidden-spec" not in spec_names

    def test_filters_symlink_to_parent_directory(self, tmp_path):
        """Test that symlinks trying to escape via parent references are filtered."""
        import os

        if os.name == "nt":
            import pytest
            pytest.skip("Symlink tests not supported on Windows")

        ldf_dir = tmp_path / ".ldf"
        specs_dir = ldf_dir / "specs"
        specs_dir.mkdir(parents=True)

        # Create external target
        external = tmp_path / "external-secrets"
        external.mkdir()
        (external / "requirements.md").write_text("# Secrets!")

        # Create symlink to parent directory
        escape_link = specs_dir / "escape-attempt"
        escape_link.symlink_to(external)

        summary = get_specs_summary(ldf_dir)

        # Should filter out the escaping symlink
        spec_names = [s["name"] for s in summary]
        assert "escape-attempt" not in spec_names
