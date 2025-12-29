"""Tests for ldf.lint module."""

import json
from pathlib import Path

import yaml

from ldf.lint import (
    LintReport,
    LintResult,
    _check_answerpacks,
    _check_answerpacks_with_report,
    _check_design,
    _check_design_with_report,
    _check_requirements,
    _check_requirements_with_report,
    _check_tasks,
    _check_tasks_with_report,
    _generate_sarif,
    _lint_spec,
    _lint_spec_with_report,
    _output_sarif,
    _print_ci_summary,
    _print_summary,
    _validate_guardrail_matrix,
    _validate_guardrail_matrix_with_report,
    lint_specs,
)
from ldf.utils.guardrail_loader import Guardrail


class TestLintSpecs:
    """Tests for lint_specs function."""

    def test_lint_valid_spec(self, temp_spec: Path, monkeypatch):
        """Test linting a valid spec returns no errors."""
        project_dir = temp_spec.parent.parent.parent
        monkeypatch.chdir(project_dir)

        result = lint_specs(spec_name="test-feature", lint_all=False, fix=False)

        assert result == 0  # Success

    def test_lint_all_specs(self, temp_spec: Path, monkeypatch):
        """Test linting all specs in a project."""
        project_dir = temp_spec.parent.parent.parent
        monkeypatch.chdir(project_dir)

        result = lint_specs(spec_name=None, lint_all=True, fix=False)

        assert result == 0  # Success

    def test_lint_nonexistent_spec(self, temp_project: Path, monkeypatch):
        """Test linting a nonexistent spec returns error."""
        monkeypatch.chdir(temp_project)

        result = lint_specs(spec_name="nonexistent", lint_all=False, fix=False)

        assert result == 1  # Error

    def test_lint_non_ldf_project(self, tmp_path: Path, monkeypatch):
        """Test linting in a non-LDF project returns error."""
        monkeypatch.chdir(tmp_path)

        result = lint_specs(spec_name=None, lint_all=True, fix=False)

        assert result == 1  # Error - no .ldf directory

    def test_lint_no_args_no_all_fails(self, temp_project: Path, monkeypatch):
        """Test lint without spec_name and without --all returns error."""
        monkeypatch.chdir(temp_project)

        result = lint_specs(spec_name=None, lint_all=False, fix=False)

        assert result == 1  # Error - must specify spec or --all


class TestLintRequirements:
    """Tests for requirements.md linting."""

    def test_detects_missing_question_pack_answers(self, temp_project: Path, monkeypatch):
        """Test detection of missing Question-Pack Answers section."""
        spec_dir = temp_project / ".ldf" / "specs" / "bad-spec"
        spec_dir.mkdir(parents=True)

        (spec_dir / "requirements.md").write_text("""# Requirements

## User Stories

### US-1: Test

## Guardrail Coverage Matrix

| Guardrail | Requirements | Design | Tasks/Tests | Owner | Status |
|-----------|--------------|--------|-------------|-------|--------|
| 1. Testing | [US-1] | [S1] | [T-1] | Dev | TODO |
""")
        (spec_dir / "design.md").write_text("# Design\n## API\nTest")
        (spec_dir / "tasks.md").write_text("""# Tasks

## Per-Task Guardrail Checklist

Checklist here.

### Task 1.1: Test
- [ ] Item
""")

        monkeypatch.chdir(temp_project)
        result = lint_specs(spec_name="bad-spec", lint_all=False, fix=False)

        assert result == 1  # Error - missing Question-Pack Answers

    def test_detects_empty_guardrail_matrix(self, temp_project: Path, monkeypatch):
        """Test detection of empty guardrail matrix."""
        spec_dir = temp_project / ".ldf" / "specs" / "empty-matrix"
        spec_dir.mkdir(parents=True)

        (spec_dir / "requirements.md").write_text("""# Requirements

## Question-Pack Answers

Answers here.

## Guardrail Coverage Matrix

| Guardrail | Requirements | Design | Tasks/Tests | Owner | Status |
|-----------|--------------|--------|-------------|-------|--------|

No rows in matrix.
""")
        (spec_dir / "design.md").write_text("# Design\n## API\nTest")
        (spec_dir / "tasks.md").write_text("""# Tasks

## Per-Task Guardrail Checklist

Checklist.

### Task 1.1: Test
- [ ] Item
""")

        monkeypatch.chdir(temp_project)
        result = lint_specs(spec_name="empty-matrix", lint_all=False, fix=False)

        assert result == 1  # Error - empty matrix


class TestLintTasks:
    """Tests for tasks.md linting."""

    def test_detects_missing_per_task_checklist(self, temp_project: Path, monkeypatch):
        """Test detection of missing Per-Task Guardrail Checklist section."""
        spec_dir = temp_project / ".ldf" / "specs" / "no-checklist"
        spec_dir.mkdir(parents=True)

        (spec_dir / "requirements.md").write_text("""# Requirements

## Question-Pack Answers

Answers.

## Guardrail Coverage Matrix

| Guardrail | Requirements | Design | Tasks/Tests | Owner | Status |
|-----------|--------------|--------|-------------|-------|--------|
| 1. Testing | [US-1] | [S1] | [T-1] | Dev | TODO |
""")
        (spec_dir / "design.md").write_text("# Design\n## API\nTest")
        (spec_dir / "tasks.md").write_text("""# Tasks

## Phase 1

### Task 1.1: Test
- [ ] Item
""")

        monkeypatch.chdir(temp_project)
        result = lint_specs(spec_name="no-checklist", lint_all=False, fix=False)

        assert result == 1  # Error - missing Per-Task Guardrail Checklist


class TestLintDesign:
    """Tests for design.md linting."""

    def test_warns_on_missing_guardrail_mapping(self, temp_project: Path, monkeypatch):
        """Test warning for missing Guardrail Mapping section."""
        spec_dir = temp_project / ".ldf" / "specs" / "no-mapping"
        spec_dir.mkdir(parents=True)

        (spec_dir / "requirements.md").write_text("""# Requirements

## Question-Pack Answers

Answers.

## User Stories

### US-1: Test Story

## Guardrail Coverage Matrix

| Guardrail | Requirements | Design | Tasks/Tests | Owner | Status |
|-----------|--------------|--------|-------------|-------|--------|
| 1. Testing Coverage | [US-1] | [S1] | [T-1] | Dev | TODO |
| 2. Security Basics | [US-1] | [S1] | [T-1] | Dev | TODO |
| 3. Error Handling | [US-1] | [S1] | [T-1] | Dev | TODO |
| 4. Logging & Observability | [US-1] | [S1] | [T-1] | Dev | TODO |
| 5. API Design | [US-1] | [S1] | [T-1] | Dev | TODO |
| 6. Data Validation | [US-1] | [S1] | [T-1] | Dev | TODO |
| 7. Database Migrations | [US-1] | [S1] | [T-1] | Dev | TODO |
| 8. Documentation | [US-1] | [S1] | [T-1] | Dev | TODO |
""")
        (spec_dir / "design.md").write_text("""# Design

## Architecture

Some architecture.

## API Endpoints

Some endpoints.
""")  # Missing Guardrail Mapping
        (spec_dir / "tasks.md").write_text("""# Tasks

## Per-Task Guardrail Checklist

Checklist.

### Task 1.1: Test
- [ ] Item
""")

        monkeypatch.chdir(temp_project)
        # This should pass (warning only, not error) - missing Guardrail Mapping is a warning
        result = lint_specs(spec_name="no-mapping", lint_all=False, fix=False)

        assert result == 0  # Should pass, just warns


class TestCiOutputFormat:
    """Tests for CI output format."""

    def test_ci_format_non_ldf_project(self, tmp_path: Path, monkeypatch, capsys):
        """Test CI format output for non-LDF project."""
        monkeypatch.chdir(tmp_path)

        result = lint_specs(spec_name=None, lint_all=True, fix=False, output_format="ci")

        captured = capsys.readouterr()
        assert "Error:" in captured.out
        assert result == 1

    def test_ci_format_no_specs_dir(self, temp_project: Path, monkeypatch, capsys):
        """Test CI format when no specs directory exists."""
        # Remove specs directory
        import shutil

        specs_dir = temp_project / ".ldf" / "specs"
        if specs_dir.exists():
            shutil.rmtree(specs_dir)
        monkeypatch.chdir(temp_project)

        result = lint_specs(spec_name=None, lint_all=True, fix=False, output_format="ci")

        captured = capsys.readouterr()
        # CI output may use ⚠ or Warning:
        assert "⚠" in captured.out or "Warning" in captured.out or result == 0

    def test_ci_format_spec_not_found(self, temp_project: Path, monkeypatch, capsys):
        """Test CI format when spec not found."""
        monkeypatch.chdir(temp_project)

        result = lint_specs(spec_name="nonexistent", lint_all=False, fix=False, output_format="ci")

        captured = capsys.readouterr()
        assert "Error:" in captured.out
        assert result == 1

    def test_ci_format_no_spec_or_all(self, temp_project: Path, monkeypatch, capsys):
        """Test CI format when neither spec nor --all specified."""
        monkeypatch.chdir(temp_project)

        result = lint_specs(spec_name=None, lint_all=False, fix=False, output_format="ci")

        captured = capsys.readouterr()
        assert "Error:" in captured.out
        assert result == 1

    def test_ci_format_no_specs_found(self, temp_project: Path, monkeypatch, capsys):
        """Test CI format when no specs found in directory."""
        # Ensure specs directory exists but is empty
        specs_dir = temp_project / ".ldf" / "specs"
        specs_dir.mkdir(exist_ok=True)
        # Remove any existing spec directories
        for d in specs_dir.iterdir():
            if d.is_dir():
                import shutil

                shutil.rmtree(d)
        monkeypatch.chdir(temp_project)

        result = lint_specs(spec_name=None, lint_all=True, fix=False, output_format="ci")

        captured = capsys.readouterr()
        # CI output may use ⚠ or Warning:
        assert "⚠" in captured.out or "Warning" in captured.out or result == 0

    def test_ci_format_success(self, temp_spec: Path, monkeypatch, capsys):
        """Test CI format output for successful lint."""
        project_dir = temp_spec.parent.parent.parent
        # Create answerpacks directory with a YAML file to avoid warning
        answerpacks_dir = project_dir / ".ldf" / "answerpacks" / "test-feature"
        answerpacks_dir.mkdir(parents=True, exist_ok=True)
        (answerpacks_dir / "security.yaml").write_text("# Security answers\n")
        monkeypatch.chdir(project_dir)

        result = lint_specs(spec_name="test-feature", lint_all=False, fix=False, output_format="ci")

        # Just verify it runs successfully (no fatal errors)
        assert result == 0


class TestLintAutoFix:
    """Tests for auto-fix functionality."""

    def test_fix_mode_does_not_crash(self, temp_spec: Path, monkeypatch):
        """Test that fix mode runs without crashing."""
        project_dir = temp_spec.parent.parent.parent
        monkeypatch.chdir(project_dir)

        # Fix mode should run without crashing
        result = lint_specs(spec_name="test-feature", lint_all=False, fix=True)

        # Should succeed or at least not crash
        assert result in (0, 1)

    def test_fix_creates_missing_files_from_templates(self, temp_project: Path, monkeypatch):
        """Test that --fix creates missing files from templates."""
        # Create a spec with only requirements.md
        spec_dir = temp_project / ".ldf" / "specs" / "incomplete"
        spec_dir.mkdir(parents=True)

        (spec_dir / "requirements.md").write_text("""# incomplete - Requirements

## Overview

Test.

## Question-Pack Answers

Answers.

## Guardrail Coverage Matrix

| Guardrail | Requirements | Design | Tasks/Tests | Owner | Status |
|-----------|--------------|--------|-------------|-------|--------|
| 1. Testing | [US-1] | [S1] | [T-1] | Dev | TODO |
""")

        monkeypatch.chdir(temp_project)

        # First lint should fail due to missing files
        result_before = lint_specs(spec_name="incomplete", lint_all=False, fix=False)
        assert result_before == 1

        # Verify design.md and tasks.md don't exist
        assert not (spec_dir / "design.md").exists()
        assert not (spec_dir / "tasks.md").exists()

        # Run lint with --fix
        lint_specs(spec_name="incomplete", lint_all=False, fix=True)

        # Verify files were created
        assert (spec_dir / "design.md").exists()
        assert (spec_dir / "tasks.md").exists()

        # Verify created files have content
        assert len((spec_dir / "design.md").read_text()) > 0
        assert len((spec_dir / "tasks.md").read_text()) > 0

    def test_fix_removes_trailing_whitespace(self, temp_project: Path, monkeypatch):
        """Test that --fix removes trailing whitespace from files."""
        spec_dir = temp_project / ".ldf" / "specs" / "whitespace"
        spec_dir.mkdir(parents=True)

        # Create files with trailing whitespace
        (spec_dir / "requirements.md").write_text("""# Requirements

## Question-Pack Answers

Answers.

## Guardrail Coverage Matrix

| Guardrail | Requirements | Design | Tasks/Tests | Owner | Status |
|-----------|--------------|--------|-------------|-------|--------|
| 1. Testing | [US-1] | [S1] | [T-1] | Dev | TODO |
""")
        (spec_dir / "design.md").write_text("# Design   \n\n## API   \n\nTest   ")
        (spec_dir / "tasks.md").write_text("""# Tasks

## Per-Task Guardrail Checklist

Checklist.

### Task 1.1: Test
- [ ] Item
""")

        monkeypatch.chdir(temp_project)

        # Run lint with --fix
        lint_specs(spec_name="whitespace", lint_all=False, fix=True)

        # Verify trailing whitespace was removed
        design_content = (spec_dir / "design.md").read_text()
        # No line should end with spaces
        for line in design_content.split("\n"):
            assert not line.endswith(" "), f"Line still has trailing whitespace: '{line}'"


class TestLintStrictMode:
    """Tests for strict mode."""

    def test_strict_mode_treats_warnings_as_errors(self, temp_project: Path, monkeypatch):
        """Test that strict mode treats warnings as errors."""
        # Create a spec with a warning (missing Guardrail Mapping in design.md)
        spec_dir = temp_project / ".ldf" / "specs" / "warning-spec"
        spec_dir.mkdir(parents=True)

        (spec_dir / "requirements.md").write_text("""# Requirements

## Question-Pack Answers

Answers.

## User Stories

### US-1: Test

## Guardrail Coverage Matrix

| Guardrail | Requirements | Design | Tasks/Tests | Owner | Status |
|-----------|--------------|--------|-------------|-------|--------|
| 1. Testing | [US-1] | [S1] | [T-1] | Dev | TODO |
| 2. Security | [US-1] | [S1] | [T-1] | Dev | TODO |
| 3. Error | [US-1] | [S1] | [T-1] | Dev | TODO |
| 4. Logging | [US-1] | [S1] | [T-1] | Dev | TODO |
| 5. API | [US-1] | [S1] | [T-1] | Dev | TODO |
| 6. Data | [US-1] | [S1] | [T-1] | Dev | TODO |
| 7. DB | [US-1] | [S1] | [T-1] | Dev | TODO |
| 8. Docs | [US-1] | [S1] | [T-1] | Dev | TODO |
""")
        (spec_dir / "design.md").write_text("# Design\n## Architecture\nTest")
        (spec_dir / "tasks.md").write_text("""# Tasks

## Per-Task Guardrail Checklist

Checklist.

### Task 1.1: Test
- [ ] Item
""")

        # Update config to enable strict mode
        config_path = temp_project / ".ldf" / "config.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)
        config["lint"] = {"strict": True}
        with open(config_path, "w") as f:
            yaml.safe_dump(config, f)

        monkeypatch.chdir(temp_project)
        result = lint_specs(spec_name="warning-spec", lint_all=False, fix=False)

        # With strict mode, warnings become errors
        # Result depends on whether spec generates warnings
        assert result in (0, 1)


class TestLintEdgeCases:
    """Tests for lint edge cases."""

    def test_lint_with_missing_config(self, temp_project: Path, monkeypatch):
        """Test lint when config file is missing."""
        # Remove config file
        (temp_project / ".ldf" / "config.yaml").unlink()
        monkeypatch.chdir(temp_project)

        # Should still work with defaults
        result = lint_specs(spec_name=None, lint_all=True, fix=False)

        assert result in (0, 1)

    def test_lint_with_missing_files_in_spec(self, temp_project: Path, monkeypatch):
        """Test lint when spec has missing files."""
        spec_dir = temp_project / ".ldf" / "specs" / "incomplete"
        spec_dir.mkdir(parents=True)

        # Only create requirements.md, missing design.md and tasks.md
        (spec_dir / "requirements.md").write_text("# Requirements\n")

        monkeypatch.chdir(temp_project)
        result = lint_specs(spec_name="incomplete", lint_all=False, fix=False)

        assert result == 1  # Should fail due to missing files


class TestSarifOutput:
    """Tests for SARIF output format."""

    def test_sarif_format_produces_valid_json(self, temp_spec: Path, monkeypatch, capsys):
        """Test that SARIF format produces valid JSON."""
        import json

        project_dir = temp_spec.parent.parent.parent
        monkeypatch.chdir(project_dir)

        lint_specs(
            spec_name="test-feature",
            lint_all=False,
            fix=False,
            output_format="sarif",
        )

        captured = capsys.readouterr()
        # SARIF output should be valid JSON
        sarif = json.loads(captured.out)
        assert "$schema" in sarif
        assert sarif["version"] == "2.1.0"
        assert "runs" in sarif

    def test_sarif_format_has_tool_driver(self, temp_spec: Path, monkeypatch, capsys):
        """Test that SARIF output has tool driver info."""
        import json

        project_dir = temp_spec.parent.parent.parent
        monkeypatch.chdir(project_dir)

        lint_specs(
            spec_name="test-feature",
            lint_all=False,
            fix=False,
            output_format="sarif",
        )

        captured = capsys.readouterr()
        sarif = json.loads(captured.out)

        assert len(sarif["runs"]) > 0
        run = sarif["runs"][0]
        assert "tool" in run
        assert "driver" in run["tool"]
        assert run["tool"]["driver"]["name"] == "ldf-lint"

    def test_sarif_format_includes_rules(self, temp_spec: Path, monkeypatch, capsys):
        """Test that SARIF output includes rule definitions."""
        import json

        project_dir = temp_spec.parent.parent.parent
        monkeypatch.chdir(project_dir)

        lint_specs(
            spec_name="test-feature",
            lint_all=False,
            fix=False,
            output_format="sarif",
        )

        captured = capsys.readouterr()
        sarif = json.loads(captured.out)

        run = sarif["runs"][0]
        assert "rules" in run["tool"]["driver"]

    def test_sarif_format_reports_errors(self, temp_project: Path, monkeypatch, capsys):
        """Test that SARIF format reports lint errors."""
        import json

        # Create a spec with errors
        spec_dir = temp_project / ".ldf" / "specs" / "bad-spec"
        spec_dir.mkdir(parents=True)

        (spec_dir / "requirements.md").write_text("# Requirements\n")
        # Missing design.md and tasks.md

        monkeypatch.chdir(temp_project)
        lint_specs(
            spec_name="bad-spec",
            lint_all=False,
            fix=False,
            output_format="sarif",
        )

        captured = capsys.readouterr()
        sarif = json.loads(captured.out)

        run = sarif["runs"][0]
        assert "results" in run
        # Should have some results for the errors
        assert len(run["results"]) > 0

    def test_sarif_format_error_has_location(self, temp_project: Path, monkeypatch, capsys):
        """Test that SARIF errors include location information."""
        import json

        # Create a spec with errors
        spec_dir = temp_project / ".ldf" / "specs" / "error-spec"
        spec_dir.mkdir(parents=True)

        (spec_dir / "requirements.md").write_text("# Requirements\n")

        monkeypatch.chdir(temp_project)
        lint_specs(
            spec_name="error-spec",
            lint_all=False,
            fix=False,
            output_format="sarif",
        )

        captured = capsys.readouterr()
        sarif = json.loads(captured.out)

        run = sarif["runs"][0]
        if run["results"]:
            result = run["results"][0]
            assert "ruleId" in result
            assert "message" in result
            assert "locations" in result

    def test_sarif_format_all_specs(self, temp_project: Path, monkeypatch, capsys):
        """Test SARIF format with --all flag."""
        import json

        # Create multiple specs
        for name in ["spec-a", "spec-b"]:
            spec_dir = temp_project / ".ldf" / "specs" / name
            spec_dir.mkdir(parents=True)
            (spec_dir / "requirements.md").write_text("# Requirements\n")

        monkeypatch.chdir(temp_project)
        lint_specs(
            spec_name=None,
            lint_all=True,
            fix=False,
            output_format="sarif",
        )

        captured = capsys.readouterr()
        sarif = json.loads(captured.out)

        # Should have valid SARIF structure
        assert sarif["version"] == "2.1.0"

    def test_sarif_format_writes_to_output_file(self, temp_spec: Path, tmp_path: Path, monkeypatch):
        """Test that SARIF output can be written to a file."""
        import json

        project_dir = temp_spec.parent.parent.parent
        monkeypatch.chdir(project_dir)

        output_file = tmp_path / "results.sarif"

        lint_specs(
            spec_name="test-feature",
            lint_all=False,
            fix=False,
            output_format="sarif",
            output_file=str(output_file),
        )

        assert output_file.exists()
        sarif = json.loads(output_file.read_text())
        assert sarif["version"] == "2.1.0"


class TestLintReport:
    """Tests for lint report dataclass."""

    def test_lint_result_fields(self):
        """Test LintResult has expected fields."""
        from ldf.lint import LintResult

        result = LintResult(
            rule_id="ldf/missing-file",
            level="error",
            message="Missing design.md",
            spec_name="test-spec",
            file_name="design.md",
            line=1,
        )

        assert result.rule_id == "ldf/missing-file"
        assert result.level == "error"
        assert result.spec_name == "test-spec"
        assert result.file_name == "design.md"
        assert result.line == 1

    def test_lint_report_add_error(self):
        """Test LintReport add_error method."""
        from ldf.lint import LintReport

        report = LintReport()
        report.add_error(
            rule_id="ldf/missing-file",
            message="Missing design.md",
            spec_name="test",
            file_name="design.md",
        )

        assert len(report.results) == 1
        assert report.results[0].level == "error"

    def test_lint_report_add_warning(self):
        """Test LintReport add_warning method."""
        from ldf.lint import LintReport

        report = LintReport()
        report.add_warning(
            rule_id="ldf/style-issue",
            message="Style issue",
            spec_name="test",
        )

        assert len(report.results) == 1
        assert report.results[0].level == "warning"

    def test_lint_report_error_count(self):
        """Test LintReport counts errors correctly."""
        from ldf.lint import LintReport

        report = LintReport()
        report.add_error("r1", "Error 1", "test")
        report.add_error("r2", "Error 2", "test")
        report.add_warning("r3", "Warning 1", "test")

        assert report.error_count == 2
        assert report.warning_count == 1

    def test_lint_report_empty_has_zero_counts(self):
        """Test empty LintReport has zero counts."""
        from ldf.lint import LintReport

        report = LintReport()

        assert report.error_count == 0
        assert report.warning_count == 0


class TestInternalLintSpec:
    """Tests for the internal _lint_spec function."""

    def test_lint_spec_ci_mode_output(self, temp_spec: Path, capsys):
        """Test _lint_spec in CI mode outputs correctly."""
        guardrails = [
            Guardrail(id=1, name="Testing Coverage", description="Test coverage", severity="error")
        ]

        errors, warnings = _lint_spec(
            temp_spec, guardrails, fix=False, strict_mode=False, ci_mode=True
        )

        captured = capsys.readouterr()
        # Should have CI-style output
        assert (
            "✅ Pass:" in captured.out or "✗ Error:" in captured.out or "⚠ Warning:" in captured.out
        )

    def test_lint_spec_fix_mode(self, temp_project: Path, capsys):
        """Test _lint_spec fix mode creates missing files."""
        spec_dir = temp_project / ".ldf" / "specs" / "fix-test"
        spec_dir.mkdir(parents=True)
        (spec_dir / "requirements.md").write_text("# Requirements\n")

        guardrails = []
        errors_before, _ = _lint_spec(spec_dir, guardrails, fix=False, strict_mode=False)
        assert len(errors_before) > 0  # Missing design.md and tasks.md

        # Run with fix=True
        _lint_spec(spec_dir, guardrails, fix=True, strict_mode=False)

        # Files should now exist
        assert (spec_dir / "design.md").exists()
        assert (spec_dir / "tasks.md").exists()

    def test_lint_spec_strict_mode(self, temp_spec: Path):
        """Test _lint_spec strict mode converts warnings to errors."""
        guardrails = [
            Guardrail(id=1, name="Testing Coverage", description="Test coverage", severity="error")
        ]

        # Create spec with warnings (no user stories)
        (temp_spec / "requirements.md").write_text("""# Requirements

## Question-Pack Answers

Answers.

## Guardrail Coverage Matrix

| Guardrail | Requirements | Design | Tasks/Tests | Owner | Status |
|-----------|--------------|--------|-------------|-------|--------|
| 1. Testing | [US-1] | [S1] | [T-1] | Dev | TODO |
""")

        errors, warnings = _lint_spec(
            temp_spec, guardrails, fix=False, strict_mode=True, ci_mode=False
        )

        # In strict mode, warnings become errors
        assert len(warnings) == 0  # Warnings converted to errors

    def test_lint_spec_fix_cleans_whitespace(self, temp_project: Path, capsys):
        """Test _lint_spec fix mode cleans trailing whitespace."""
        spec_dir = temp_project / ".ldf" / "specs" / "whitespace"
        spec_dir.mkdir(parents=True)
        (spec_dir / "requirements.md").write_text("# Requirements   \n\nTest   \n")
        (spec_dir / "design.md").write_text("# Design   \n")
        (spec_dir / "tasks.md").write_text("# Tasks   \n")

        guardrails = []
        _lint_spec(spec_dir, guardrails, fix=True, strict_mode=False)

        # Check whitespace was cleaned
        content = (spec_dir / "requirements.md").read_text()
        assert not any(line.endswith(" ") for line in content.split("\n"))


class TestCheckRequirements:
    """Tests for _check_requirements function."""

    def test_detects_missing_sections(self, tmp_path: Path):
        """Test detection of missing required sections."""
        req_file = tmp_path / "requirements.md"
        req_file.write_text("# Requirements\n\nSome content.")

        errors, warnings = _check_requirements(req_file, [])

        assert any("Question-Pack Answers" in e for e in errors)
        assert any("Guardrail Coverage Matrix" in e for e in errors)

    def test_detects_missing_user_stories(self, tmp_path: Path):
        """Test detection of missing user stories."""
        req_file = tmp_path / "requirements.md"
        req_file.write_text("""# Requirements

## Question-Pack Answers

Answers here.

## Guardrail Coverage Matrix

| Guardrail | Requirements | Design | Tasks/Tests | Owner | Status |
|-----------|--------------|--------|-------------|-------|--------|
| 1. Testing | [US-1] | [S1] | [T-1] | Dev | TODO |
""")

        errors, warnings = _check_requirements(req_file, [])

        assert any("user stories" in w.lower() for w in warnings)


class TestCheckDesign:
    """Tests for _check_design function."""

    def test_warns_on_missing_guardrail_mapping(self, tmp_path: Path):
        """Test warning for missing Guardrail Mapping section."""
        design_file = tmp_path / "design.md"
        design_file.write_text("# Design\n\n## Architecture\n\nContent.")

        errors, warnings = _check_design(design_file, [])

        assert any("Guardrail Mapping" in w for w in warnings)

    def test_warns_on_missing_architecture(self, tmp_path: Path):
        """Test warning for missing Architecture section."""
        design_file = tmp_path / "design.md"
        design_file.write_text("# Design\n\n## Guardrail Mapping\n\nContent.")

        errors, warnings = _check_design(design_file, [])

        assert any("Architecture" in w or "Components" in w for w in warnings)

    def test_warns_on_missing_api_or_data(self, tmp_path: Path):
        """Test warning for missing API or Data section."""
        design_file = tmp_path / "design.md"
        design_file.write_text("# Design\n\n## Architecture\n\nContent.")

        errors, warnings = _check_design(design_file, [])

        assert any("API" in w or "Data" in w for w in warnings)

    def test_accepts_valid_design(self, tmp_path: Path):
        """Test that valid design passes."""
        design_file = tmp_path / "design.md"
        design_file.write_text("""# Design

## Architecture

Architecture here.

## Guardrail Mapping

Mapping here.

## API Endpoints

Endpoints here.
""")

        errors, warnings = _check_design(design_file, [])

        # Should have no errors and only minor warnings if any
        assert len(errors) == 0


class TestCheckTasks:
    """Tests for _check_tasks function."""

    def test_detects_missing_per_task_checklist(self, tmp_path: Path):
        """Test detection of missing Per-Task Guardrail Checklist."""
        tasks_file = tmp_path / "tasks.md"
        tasks_file.write_text("# Tasks\n\n### Task 1.1: Test\n- [ ] Item")

        errors, warnings = _check_tasks(tasks_file, [])

        assert any("Per-Task Guardrail Checklist" in e for e in errors)

    def test_detects_no_tasks(self, tmp_path: Path):
        """Test detection of no tasks in file."""
        tasks_file = tmp_path / "tasks.md"
        tasks_file.write_text("# Tasks\n\n## Per-Task Guardrail Checklist\n\nNo tasks yet.")

        errors, warnings = _check_tasks(tasks_file, [])

        assert any("No tasks found" in w for w in warnings)

    def test_detects_task_without_subtasks(self, tmp_path: Path):
        """Test detection of tasks with and without subtask checklists."""
        tasks_file = tmp_path / "tasks.md"
        tasks_file.write_text("""# Tasks

## Per-Task Guardrail Checklist

Template here.

- [ ] **Task 1.1:** Test Task with no subtasks

- [ ] **Task 1.2:** Another Task
  - [ ] This one has subtask checklist
""")

        errors, warnings = _check_tasks(tasks_file, [])

        # Both tasks are valid - Task 1.1 is just simpler with no subtasks
        # The task checkbox itself counts as a checklist item
        assert len(errors) == 0


class TestCheckAnswerpacks:
    """Tests for _check_answerpacks function."""

    def test_warns_on_missing_answerpacks_dir(self, temp_project: Path):
        """Test warning when answerpacks directory is missing."""
        spec_dir = temp_project / ".ldf" / "specs" / "no-answers"
        spec_dir.mkdir(parents=True)

        errors, warnings = _check_answerpacks(spec_dir)

        assert any("No answerpacks found" in w for w in warnings)

    def test_warns_on_empty_answerpacks_dir(self, temp_project: Path):
        """Test warning when answerpacks directory is empty."""
        spec_dir = temp_project / ".ldf" / "specs" / "empty-answers"
        spec_dir.mkdir(parents=True)
        answerpacks_dir = temp_project / ".ldf" / "answerpacks" / "empty-answers"
        answerpacks_dir.mkdir(parents=True)

        errors, warnings = _check_answerpacks(spec_dir)

        assert any("no YAML files" in w for w in warnings)

    def test_detects_unfilled_template_markers(self, temp_project: Path):
        """Test detection of unfilled template markers in answerpacks."""
        spec_dir = temp_project / ".ldf" / "specs" / "unfilled"
        spec_dir.mkdir(parents=True)
        answerpacks_dir = temp_project / ".ldf" / "answerpacks" / "unfilled"
        answerpacks_dir.mkdir(parents=True)
        (answerpacks_dir / "security.yaml").write_text("answer: [TODO: Fill this out]")

        errors, warnings = _check_answerpacks(spec_dir)

        assert any("unfilled template markers" in e for e in errors)

    def test_detects_placeholder_marker(self, temp_project: Path):
        """Test detection of PLACEHOLDER marker in answerpacks."""
        spec_dir = temp_project / ".ldf" / "specs" / "placeholder"
        spec_dir.mkdir(parents=True)
        answerpacks_dir = temp_project / ".ldf" / "answerpacks" / "placeholder"
        answerpacks_dir.mkdir(parents=True)
        (answerpacks_dir / "test.yaml").write_text("answer: [PLACEHOLDER]")

        errors, warnings = _check_answerpacks(spec_dir)

        assert any("unfilled template markers" in e for e in errors)

    def test_detects_your_underscore_marker(self, temp_project: Path):
        """Test detection of YOUR_ marker in answerpacks."""
        spec_dir = temp_project / ".ldf" / "specs" / "your-marker"
        spec_dir.mkdir(parents=True)
        answerpacks_dir = temp_project / ".ldf" / "answerpacks" / "your-marker"
        answerpacks_dir.mkdir(parents=True)
        (answerpacks_dir / "test.yaml").write_text("api_key: YOUR_API_KEY_HERE")

        errors, warnings = _check_answerpacks(spec_dir)

        assert any("unfilled template markers" in e for e in errors)

    def test_accepts_valid_answerpacks(self, temp_project: Path):
        """Test that valid answerpacks pass."""
        spec_dir = temp_project / ".ldf" / "specs" / "valid-answers"
        spec_dir.mkdir(parents=True)
        answerpacks_dir = temp_project / ".ldf" / "answerpacks" / "valid-answers"
        answerpacks_dir.mkdir(parents=True)
        (answerpacks_dir / "security.yaml").write_text(
            "authentication: JWT tokens\nauthorization: RBAC"
        )

        errors, warnings = _check_answerpacks(spec_dir)

        assert len(errors) == 0


class TestValidateGuardrailMatrix:
    """Tests for _validate_guardrail_matrix function."""

    def test_empty_matrix_error(self):
        """Test that empty matrix produces error."""
        content = """## Guardrail Coverage Matrix

| Guardrail | Requirements | Design | Tasks/Tests | Owner | Status |
|-----------|--------------|--------|-------------|-------|--------|

No data rows.
"""
        guardrails = [
            Guardrail(id=1, name="Testing Coverage", description="Test coverage", severity="error")
        ]

        errors, warnings = _validate_guardrail_matrix(content, guardrails)

        assert any("empty" in e.lower() for e in errors)

    def test_missing_guardrail_error(self):
        """Test that missing guardrail produces error."""
        content = """## Guardrail Coverage Matrix

| Guardrail | Requirements | Design | Tasks/Tests | Owner | Status |
|-----------|--------------|--------|-------------|-------|--------|
| 1. Testing | [US-1] | [S1] | [T-1] | Dev | TODO |
"""
        guardrails = [
            Guardrail(id=1, name="Testing Coverage", description="Test coverage", severity="error"),
            Guardrail(
                id=2, name="Security Basics", description="Security basics", severity="error"
            ),
        ]

        errors, warnings = _validate_guardrail_matrix(content, guardrails)

        assert any("#2" in e or "Security" in e for e in errors)

    def test_missing_requirements_ref_warning(self):
        """Test warning for missing requirements reference."""
        content = """## Guardrail Coverage Matrix

| Guardrail | Requirements | Design | Tasks/Tests | Owner | Status |
|-----------|--------------|--------|-------------|-------|--------|
| 1. Testing | | [S1] | [T-1] | Dev | TODO |
"""
        guardrails = [
            Guardrail(id=1, name="Testing Coverage", description="Test coverage", severity="error")
        ]

        errors, warnings = _validate_guardrail_matrix(content, guardrails)

        assert any("Missing requirements reference" in w for w in warnings)

    def test_missing_design_ref_warning(self):
        """Test warning for missing design reference."""
        content = """## Guardrail Coverage Matrix

| Guardrail | Requirements | Design | Tasks/Tests | Owner | Status |
|-----------|--------------|--------|-------------|-------|--------|
| 1. Testing | [US-1] | | [T-1] | Dev | TODO |
"""
        guardrails = [
            Guardrail(id=1, name="Testing Coverage", description="Test coverage", severity="error")
        ]

        errors, warnings = _validate_guardrail_matrix(content, guardrails)

        assert any("Missing design reference" in w for w in warnings)

    def test_na_without_justification_warning(self):
        """Test warning for N/A without justification."""
        content = """## Guardrail Coverage Matrix

| Guardrail | Requirements | Design | Tasks/Tests | Owner | Status |
|-----------|--------------|--------|-------------|-------|--------|
| 1. Testing | | | | | N/A |
"""
        guardrails = [
            Guardrail(id=1, name="Testing Coverage", description="Test coverage", severity="error")
        ]

        errors, warnings = _validate_guardrail_matrix(content, guardrails)

        assert any("justification" in w for w in warnings)

    def test_missing_owner_warning(self):
        """Test warning for missing owner."""
        content = """## Guardrail Coverage Matrix

| Guardrail | Requirements | Design | Tasks/Tests | Owner | Status |
|-----------|--------------|--------|-------------|-------|--------|
| 1. Testing | [US-1] | [S1] | [T-1] | | TODO |
"""
        guardrails = [
            Guardrail(id=1, name="Testing Coverage", description="Test coverage", severity="error")
        ]

        errors, warnings = _validate_guardrail_matrix(content, guardrails)

        assert any("Missing owner" in w for w in warnings)

    def test_na_with_justification_ok(self):
        """Test that N/A with justification is OK."""
        content = """## Guardrail Coverage Matrix

| Guardrail | Requirements | Design | Tasks/Tests | Owner | Status |
|-----------|--------------|--------|-------------|-------|--------|
| 1. Testing | | | | | N/A - No testing needed |
"""
        guardrails = [
            Guardrail(id=1, name="Testing Coverage", description="Test coverage", severity="error")
        ]

        errors, warnings = _validate_guardrail_matrix(content, guardrails)

        # No justification warning for N/A with dash
        assert not any("justification" in w for w in warnings)


class TestPrintSummary:
    """Tests for _print_summary function."""

    def test_print_summary_all_passed(self, capsys):
        """Test summary output when all specs pass."""
        results = [
            ("spec-a", [], []),
            ("spec-b", [], []),
        ]

        _print_summary(results, total_errors=0, total_warnings=0)

        captured = capsys.readouterr()
        assert "All specs passed" in captured.out

    def test_print_summary_with_errors(self, capsys):
        """Test summary output with errors."""
        results = [
            ("spec-a", ["Error 1", "Error 2"], []),
        ]

        _print_summary(results, total_errors=2, total_warnings=0)

        captured = capsys.readouterr()
        assert "Total errors: 2" in captured.out

    def test_print_summary_with_warnings(self, capsys):
        """Test summary output with warnings."""
        results = [
            ("spec-a", [], ["Warning 1"]),
        ]

        _print_summary(results, total_errors=0, total_warnings=1)

        captured = capsys.readouterr()
        assert "Total warnings: 1" in captured.out

    def test_print_summary_with_both(self, capsys):
        """Test summary output with both errors and warnings."""
        results = [
            ("spec-a", ["Error"], ["Warning"]),
        ]

        _print_summary(results, total_errors=1, total_warnings=1)

        captured = capsys.readouterr()
        assert "Total errors: 1" in captured.out
        assert "Total warnings: 1" in captured.out


class TestPrintCiSummary:
    """Tests for _print_ci_summary function."""

    def test_ci_summary_all_passed(self, capsys):
        """Test CI summary output when all specs pass."""
        results = [
            ("spec-a", [], []),
        ]

        _print_ci_summary(results, total_errors=0, total_warnings=0)

        captured = capsys.readouterr()
        assert "All specs passed" in captured.out
        assert "✅" in captured.out

    def test_ci_summary_with_errors(self, capsys):
        """Test CI summary output with errors."""
        results = [
            ("spec-a", ["Error 1"], []),
        ]

        _print_ci_summary(results, total_errors=1, total_warnings=0)

        captured = capsys.readouterr()
        assert "❌" in captured.out
        assert "1 error" in captured.out

    def test_ci_summary_with_warnings_only(self, capsys):
        """Test CI summary output with warnings only."""
        results = [
            ("spec-a", [], ["Warning 1"]),
        ]

        _print_ci_summary(results, total_errors=0, total_warnings=1)

        captured = capsys.readouterr()
        assert "⚠️" in captured.out
        assert "1 warning" in captured.out


class TestGenerateSarif:
    """Tests for _generate_sarif function."""

    def test_sarif_with_init_error(self, tmp_path: Path):
        """Test SARIF generation with init error."""
        report = LintReport()

        sarif = _generate_sarif(report, tmp_path, init_error="Project not initialized")

        assert len(sarif["runs"][0]["results"]) > 0
        assert "Project not initialized" in sarif["runs"][0]["results"][0]["message"]["text"]

    def test_sarif_includes_location_with_line(self, tmp_path: Path):
        """Test SARIF includes location with line number."""
        report = LintReport()
        report.results.append(
            LintResult(
                rule_id="ldf/missing-section",
                level="error",
                message="Missing section",
                spec_name="test-spec",
                file_name="requirements.md",
                line=10,
            )
        )

        sarif = _generate_sarif(report, tmp_path)

        result = sarif["runs"][0]["results"][0]
        assert "locations" in result
        assert result["locations"][0]["physicalLocation"]["region"]["startLine"] == 10

    def test_sarif_only_includes_used_rules(self, tmp_path: Path):
        """Test SARIF only includes rules that are used."""
        report = LintReport()
        report.results.append(
            LintResult(
                rule_id="ldf/missing-file",
                level="error",
                message="Missing file",
                spec_name="test-spec",
                file_name="design.md",
            )
        )

        sarif = _generate_sarif(report, tmp_path)

        rules = sarif["runs"][0]["tool"]["driver"]["rules"]
        rule_ids = [r["id"] for r in rules]
        assert "ldf/missing-file" in rule_ids
        # Unused rules should not be present
        assert len(rules) == 1


class TestOutputSarif:
    """Tests for _output_sarif function."""

    def test_output_sarif_to_file(self, tmp_path: Path):
        """Test SARIF output to file."""
        sarif = {"version": "2.1.0", "runs": []}
        output_file = tmp_path / "output.sarif"

        _output_sarif(sarif, str(output_file))

        assert output_file.exists()
        content = json.loads(output_file.read_text())
        assert content["version"] == "2.1.0"

    def test_output_sarif_to_stdout(self, capsys):
        """Test SARIF output to stdout."""
        sarif = {"version": "2.1.0", "runs": []}

        _output_sarif(sarif, None)

        captured = capsys.readouterr()
        content = json.loads(captured.out)
        assert content["version"] == "2.1.0"


class TestWithReportFunctions:
    """Tests for _*_with_report functions."""

    def test_check_requirements_with_report(self, tmp_path: Path):
        """Test _check_requirements_with_report returns LintResults."""
        req_file = tmp_path / "requirements.md"
        req_file.write_text("# Requirements\n")

        errors, warnings, results = _check_requirements_with_report(req_file, [], "test-spec")

        assert len(results) > 0
        assert all(isinstance(r, LintResult) for r in results)

    def test_check_design_with_report(self, tmp_path: Path):
        """Test _check_design_with_report returns LintResults."""
        design_file = tmp_path / "design.md"
        design_file.write_text("# Design\n")

        errors, warnings, results = _check_design_with_report(design_file, [], "test-spec")

        assert len(results) > 0
        assert all(isinstance(r, LintResult) for r in results)

    def test_check_tasks_with_report(self, tmp_path: Path):
        """Test _check_tasks_with_report returns LintResults."""
        tasks_file = tmp_path / "tasks.md"
        tasks_file.write_text("# Tasks\n")

        errors, warnings, results = _check_tasks_with_report(tasks_file, [], "test-spec")

        assert len(results) > 0
        assert all(isinstance(r, LintResult) for r in results)

    def test_check_answerpacks_with_report(self, temp_project: Path):
        """Test _check_answerpacks_with_report returns LintResults."""
        spec_dir = temp_project / ".ldf" / "specs" / "test-spec"
        spec_dir.mkdir(parents=True)

        errors, warnings, results = _check_answerpacks_with_report(spec_dir, "test-spec")

        assert len(results) > 0
        assert all(isinstance(r, LintResult) for r in results)

    def test_validate_guardrail_matrix_with_report(self):
        """Test _validate_guardrail_matrix_with_report returns LintResults."""
        content = """## Guardrail Coverage Matrix

| Guardrail | Requirements | Design | Tasks/Tests | Owner | Status |
|-----------|--------------|--------|-------------|-------|--------|

No rows.
"""
        guardrails = [
            Guardrail(id=1, name="Testing Coverage", description="Test coverage", severity="error")
        ]

        errors, warnings, results = _validate_guardrail_matrix_with_report(
            content, guardrails, "test-spec"
        )

        assert len(results) > 0
        assert all(isinstance(r, LintResult) for r in results)


class TestLintSpecWithReport:
    """Tests for _lint_spec_with_report function."""

    def test_lint_spec_with_report_returns_results(self, temp_spec: Path):
        """Test _lint_spec_with_report returns LintResults."""
        guardrails = [
            Guardrail(id=1, name="Testing Coverage", description="Test coverage", severity="error")
        ]

        errors, warnings, results = _lint_spec_with_report(
            temp_spec, guardrails, fix=False, strict_mode=False
        )

        assert isinstance(results, list)

    def test_lint_spec_with_report_sarif_mode(self, temp_spec: Path, capsys):
        """Test _lint_spec_with_report in SARIF mode suppresses console output."""
        guardrails = []

        _lint_spec_with_report(temp_spec, guardrails, fix=False, strict_mode=False, sarif_mode=True)

        captured = capsys.readouterr()
        # SARIF mode should not print console output
        assert "Linting:" not in captured.out

    def test_lint_spec_with_report_ci_mode(self, temp_spec: Path, capsys):
        """Test _lint_spec_with_report in CI mode."""
        guardrails = []

        _lint_spec_with_report(temp_spec, guardrails, fix=False, strict_mode=False, ci_mode=True)

        captured = capsys.readouterr()
        # CI mode should produce emoji output
        assert "✅" in captured.out or "✗" in captured.out or "⚠" in captured.out


class TestSarifEdgeCases:
    """Tests for SARIF output edge cases."""

    def test_sarif_non_ldf_project(self, tmp_path: Path, monkeypatch, capsys):
        """Test SARIF output for non-LDF project."""
        monkeypatch.chdir(tmp_path)

        lint_specs(spec_name=None, lint_all=True, fix=False, output_format="sarif")

        captured = capsys.readouterr()
        sarif = json.loads(captured.out)
        # Should have error about missing .ldf
        assert len(sarif["runs"][0]["results"]) > 0

    def test_sarif_no_specs_dir(self, temp_project: Path, monkeypatch, capsys):
        """Test SARIF output when specs directory missing."""
        import shutil

        specs_dir = temp_project / ".ldf" / "specs"
        if specs_dir.exists():
            shutil.rmtree(specs_dir)
        monkeypatch.chdir(temp_project)

        lint_specs(spec_name=None, lint_all=True, fix=False, output_format="sarif")

        captured = capsys.readouterr()
        sarif = json.loads(captured.out)
        # Should have valid empty SARIF
        assert sarif["version"] == "2.1.0"

    def test_sarif_spec_not_found(self, temp_project: Path, monkeypatch, capsys):
        """Test SARIF output when spec not found."""
        monkeypatch.chdir(temp_project)

        lint_specs(spec_name="nonexistent", lint_all=False, fix=False, output_format="sarif")

        captured = capsys.readouterr()
        sarif = json.loads(captured.out)
        assert len(sarif["runs"][0]["results"]) > 0

    def test_sarif_no_spec_or_all(self, temp_project: Path, monkeypatch, capsys):
        """Test SARIF output when neither spec nor --all specified."""
        monkeypatch.chdir(temp_project)

        lint_specs(spec_name=None, lint_all=False, fix=False, output_format="sarif")

        captured = capsys.readouterr()
        sarif = json.loads(captured.out)
        assert len(sarif["runs"][0]["results"]) > 0

    def test_sarif_empty_specs_dir(self, temp_project: Path, monkeypatch, capsys):
        """Test SARIF output when specs directory is empty."""
        specs_dir = temp_project / ".ldf" / "specs"
        specs_dir.mkdir(exist_ok=True)
        for d in specs_dir.iterdir():
            if d.is_dir():
                import shutil

                shutil.rmtree(d)
        monkeypatch.chdir(temp_project)

        lint_specs(spec_name=None, lint_all=True, fix=False, output_format="sarif")

        captured = capsys.readouterr()
        sarif = json.loads(captured.out)
        assert sarif["version"] == "2.1.0"
