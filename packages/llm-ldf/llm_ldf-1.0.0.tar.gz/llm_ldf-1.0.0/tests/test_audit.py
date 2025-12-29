"""Tests for ldf.audit module."""

import json
from pathlib import Path
from unittest.mock import patch

import yaml

from ldf.audit import (
    _build_audit_prompt_for_api,
    _build_audit_request,
    _import_feedback,
    _redact_content,
    _run_api_audit,
    run_audit,
)
from ldf.audit_api import AuditResponse


class TestRedaction:
    """Tests for content redaction."""

    def test_redacts_api_keys(self):
        """Test that API key patterns are redacted."""
        content = 'api_key = "sk-1234567890abcdef1234567890abcdef"'
        redacted = _redact_content(content)
        assert "sk-1234567890" not in redacted
        assert "REDACTED" in redacted

    def test_redacts_prefixed_api_keys(self):
        """Test that prefixed API keys (sk-, pk-) are redacted."""
        content = "**API Key:** sk-test-12345678901234567890"
        redacted = _redact_content(content)
        assert "sk-test-12345678901234567890" not in redacted
        assert "[API_KEY_REDACTED]" in redacted

    def test_redacts_bearer_tokens(self):
        """Test that Bearer tokens are redacted."""
        content = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test"
        redacted = _redact_content(content)
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in redacted
        assert "Bearer [REDACTED]" in redacted

    def test_redacts_password_values(self):
        """Test that password values are redacted."""
        content = 'password: "mysecretpassword123"'
        redacted = _redact_content(content)
        assert "mysecretpassword123" not in redacted
        assert "[REDACTED]" in redacted

    def test_redacts_aws_keys(self):
        """Test that AWS keys are redacted."""
        content = "AWS_ACCESS_KEY_ID = AKIAIOSFODNN7EXAMPLE"
        redacted = _redact_content(content)
        assert "AKIAIOSFODNN7EXAMPLE" not in redacted

    def test_redacts_env_var_references(self):
        """Test that secret env var references are redacted."""
        content = "Use ${SECRET_TOKEN} for authentication"
        redacted = _redact_content(content)
        assert "${SECRET_TOKEN}" not in redacted
        assert "[ENV_VAR_REDACTED]" in redacted

    def test_preserves_normal_content(self):
        """Test that normal content is not redacted."""
        content = """# Feature Requirements

## Overview

This feature handles user authentication.

## User Stories

### US-1: Login Flow

Users can log in with email and password.
"""
        redacted = _redact_content(content)
        assert "Feature Requirements" in redacted
        assert "user authentication" in redacted
        assert "Login Flow" in redacted


class TestBuildAuditRequest:
    """Tests for _build_audit_request function."""

    def test_includes_spec_content(self, temp_project_with_specs: Path, monkeypatch):
        """Test that audit request includes spec content."""
        monkeypatch.chdir(temp_project_with_specs)
        specs_dir = temp_project_with_specs / ".ldf" / "specs"
        specs = list(specs_dir.iterdir())

        content = _build_audit_request("spec-review", specs, include_secrets=True)

        assert "feature-a" in content
        assert "feature-b" in content
        assert "Requirements" in content

    def test_redacts_by_default(self, temp_project_with_specs: Path, monkeypatch):
        """Test that secrets are redacted by default."""
        monkeypatch.chdir(temp_project_with_specs)
        specs_dir = temp_project_with_specs / ".ldf" / "specs"
        specs = list(specs_dir.iterdir())

        content = _build_audit_request("spec-review", specs, include_secrets=False)

        # The test spec has "sk-test-12345678901234567890" which should be redacted
        assert "sk-test-12345678901234567890" not in content

    def test_includes_secrets_when_flag_set(self, temp_project_with_specs: Path, monkeypatch):
        """Test that secrets are included when flag is set."""
        monkeypatch.chdir(temp_project_with_specs)
        specs_dir = temp_project_with_specs / ".ldf" / "specs"
        specs = list(specs_dir.iterdir())

        content = _build_audit_request("spec-review", specs, include_secrets=True)

        # When include_secrets=True, the content should be present
        assert "sk-test-12345678901234567890" in content

    def test_includes_correct_instructions(self, temp_project_with_specs: Path, monkeypatch):
        """Test that audit type determines instructions."""
        monkeypatch.chdir(temp_project_with_specs)
        specs_dir = temp_project_with_specs / ".ldf" / "specs"
        specs = list(specs_dir.iterdir())

        spec_review = _build_audit_request("spec-review", specs, include_secrets=False)
        assert "Completeness of requirements" in spec_review

        security = _build_audit_request("security", specs, include_secrets=False)
        assert "OWASP Top 10" in security

    def test_truncates_long_content(self, temp_project: Path, monkeypatch):
        """Test that long spec content is truncated."""
        spec_dir = temp_project / ".ldf" / "specs" / "long-spec"
        spec_dir.mkdir(parents=True)

        # Create a spec with very long content (using text that won't trigger redaction)
        long_content = "# Requirements\n\n" + "This is a long requirement. " * 300
        (spec_dir / "requirements.md").write_text(long_content)
        (spec_dir / "design.md").write_text("# Design")
        (spec_dir / "tasks.md").write_text("# Tasks")

        monkeypatch.chdir(temp_project)

        content = _build_audit_request("spec-review", [spec_dir], include_secrets=False)

        assert "... (truncated)" in content


class TestRunAudit:
    """Tests for run_audit function."""

    def test_requires_type_or_import(self, temp_project: Path, monkeypatch, capsys):
        """Test that audit requires --type or --import."""
        monkeypatch.chdir(temp_project)

        run_audit(None, None, False)

        captured = capsys.readouterr()
        assert "Specify --type or --import" in captured.out

    def test_import_nonexistent_file(self, temp_project: Path, monkeypatch, capsys):
        """Test importing a nonexistent file shows error."""
        monkeypatch.chdir(temp_project)

        run_audit(None, "/nonexistent/path.md", False)

        captured = capsys.readouterr()
        assert "File not found" in captured.out

    def test_import_feedback_saves_to_history(
        self, temp_project: Path, temp_feedback_file: Path, monkeypatch
    ):
        """Test that imported feedback is saved to audit history."""
        monkeypatch.chdir(temp_project)

        run_audit(None, str(temp_feedback_file), False)

        audit_dir = temp_project / ".ldf" / "audit-history"
        assert audit_dir.exists()
        feedback_files = list(audit_dir.glob("feedback-*.md"))
        assert len(feedback_files) == 1


class TestAuditGeneration:
    """Tests for audit request generation."""

    def test_generates_audit_file(self, temp_project_with_specs: Path, monkeypatch):
        """Test that audit generates output file with -y flag."""
        monkeypatch.chdir(temp_project_with_specs)

        run_audit("spec-review", None, False, include_secrets=False, skip_confirm=True)

        output_file = temp_project_with_specs / "audit-request-spec-review.md"
        assert output_file.exists()

    def test_no_specs_shows_warning(self, temp_project: Path, monkeypatch, capsys):
        """Test that no specs shows warning."""
        monkeypatch.chdir(temp_project)

        run_audit("spec-review", None, False, skip_confirm=True)

        captured = capsys.readouterr()
        assert "No specs found" in captured.out

    def test_specs_dir_not_found(self, tmp_path: Path, monkeypatch, capsys):
        """Test that missing specs dir shows error."""
        monkeypatch.chdir(tmp_path)

        run_audit("spec-review", None, False, skip_confirm=True)

        captured = capsys.readouterr()
        assert "specs/ not found" in captured.out or "Run 'ldf init' first" in captured.out

    def test_spec_not_found_by_name(self, temp_project: Path, monkeypatch, capsys):
        """Test that specifying a nonexistent spec shows error."""
        monkeypatch.chdir(temp_project)

        run_audit("spec-review", None, False, skip_confirm=True, spec_name="nonexistent-spec")

        captured = capsys.readouterr()
        assert "not found" in captured.out

    def test_specific_spec_audit(self, temp_project_with_specs: Path, monkeypatch):
        """Test that specific spec can be audited."""
        monkeypatch.chdir(temp_project_with_specs)

        run_audit("spec-review", None, False, skip_confirm=True, spec_name="feature-a")

        output_file = temp_project_with_specs / "audit-request-spec-review.md"
        assert output_file.exists()
        content = output_file.read_text()
        assert "feature-a" in content
        # feature-b should not be in specific spec audit
        assert "feature-b" not in content


class TestAuditConfirmation:
    """Tests for audit confirmation prompts."""

    def test_export_cancelled_by_user(self, temp_project_with_specs: Path, monkeypatch, capsys):
        """Test that user can cancel export."""
        monkeypatch.chdir(temp_project_with_specs)
        monkeypatch.setattr("ldf.audit.Confirm.ask", lambda *a, **kw: False)

        run_audit("spec-review", None, False, include_secrets=False, skip_confirm=False)

        captured = capsys.readouterr()
        assert "Aborted" in captured.out

    def test_export_confirmed(self, temp_project_with_specs: Path, monkeypatch, capsys):
        """Test that user can confirm export."""
        monkeypatch.chdir(temp_project_with_specs)
        monkeypatch.setattr("ldf.audit.Confirm.ask", lambda *a, **kw: True)

        run_audit("spec-review", None, False, include_secrets=False, skip_confirm=False)

        captured = capsys.readouterr()
        assert "Generated:" in captured.out

    def test_secrets_warning_displayed(self, temp_project_with_specs: Path, monkeypatch, capsys):
        """Test that secrets warning is displayed when including secrets."""
        monkeypatch.chdir(temp_project_with_specs)
        monkeypatch.setattr("ldf.audit.Confirm.ask", lambda *a, **kw: True)

        run_audit("spec-review", None, False, include_secrets=True, skip_confirm=False)

        captured = capsys.readouterr()
        assert "SECRETS INCLUDED" in captured.out

    def test_redaction_note_displayed(self, temp_project_with_specs: Path, monkeypatch, capsys):
        """Test that redaction note is displayed when not including secrets."""
        monkeypatch.chdir(temp_project_with_specs)
        monkeypatch.setattr("ldf.audit.Confirm.ask", lambda *a, **kw: True)

        run_audit("spec-review", None, False, include_secrets=False, skip_confirm=False)

        captured = capsys.readouterr()
        assert "redacted" in captured.out.lower()


class TestApiMode:
    """Tests for API automation mode."""

    def test_api_mode_requires_agent(self, temp_project_with_specs: Path, monkeypatch, capsys):
        """Test that API mode requires --agent parameter."""
        monkeypatch.chdir(temp_project_with_specs)

        run_audit("spec-review", None, True, skip_confirm=True)

        captured = capsys.readouterr()
        assert "--api requires --agent" in captured.out
        assert "chatgpt or gemini" in captured.out

    def test_api_mode_unconfigured_provider(
        self, temp_project_with_specs: Path, monkeypatch, capsys
    ):
        """Test that API mode shows error for unconfigured provider."""
        monkeypatch.chdir(temp_project_with_specs)

        run_audit("spec-review", None, True, agent="chatgpt", skip_confirm=True)

        captured = capsys.readouterr()
        assert "not configured" in captured.out
        assert "config.yaml" in captured.out


class TestAllAuditTypes:
    """Tests for all audit type instructions."""

    def test_code_audit_instructions(self, temp_project_with_specs: Path, monkeypatch):
        """Test code-audit audit type instructions."""
        monkeypatch.chdir(temp_project_with_specs)
        specs_dir = temp_project_with_specs / ".ldf" / "specs"
        specs = list(specs_dir.iterdir())

        content = _build_audit_request("code-audit", specs, include_secrets=False)

        assert "Code quality" in content
        assert "Security vulnerabilities" in content

    def test_pre_launch_instructions(self, temp_project_with_specs: Path, monkeypatch):
        """Test pre-launch audit type instructions."""
        monkeypatch.chdir(temp_project_with_specs)
        specs_dir = temp_project_with_specs / ".ldf" / "specs"
        specs = list(specs_dir.iterdir())

        content = _build_audit_request("pre-launch", specs, include_secrets=False)

        assert "Production readiness" in content
        assert "Rollback procedures" in content

    def test_gap_analysis_instructions(self, temp_project_with_specs: Path, monkeypatch):
        """Test gap-analysis audit type instructions."""
        monkeypatch.chdir(temp_project_with_specs)
        specs_dir = temp_project_with_specs / ".ldf" / "specs"
        specs = list(specs_dir.iterdir())

        content = _build_audit_request("gap-analysis", specs, include_secrets=False)

        assert "Missing requirements" in content
        assert "Guardrail coverage gaps" in content

    def test_edge_cases_instructions(self, temp_project_with_specs: Path, monkeypatch):
        """Test edge-cases audit type instructions."""
        monkeypatch.chdir(temp_project_with_specs)
        specs_dir = temp_project_with_specs / ".ldf" / "specs"
        specs = list(specs_dir.iterdir())

        content = _build_audit_request("edge-cases", specs, include_secrets=False)

        assert "Boundary conditions" in content
        assert "Error handling paths" in content

    def test_architecture_instructions(self, temp_project_with_specs: Path, monkeypatch):
        """Test architecture audit type instructions."""
        monkeypatch.chdir(temp_project_with_specs)
        specs_dir = temp_project_with_specs / ".ldf" / "specs"
        specs = list(specs_dir.iterdir())

        content = _build_audit_request("architecture", specs, include_secrets=False)

        assert "Component coupling" in content
        assert "Scalability concerns" in content


class TestAuditOutputFormat:
    """Tests for --output format option."""

    def test_json_output_for_error(self, temp_project: Path, monkeypatch, capsys):
        """Test JSON output format for error cases."""
        monkeypatch.chdir(temp_project)

        # Run audit without required args - should output JSON error
        run_audit(audit_type=None, import_file=None, use_api=False, output_format="json")

        captured = capsys.readouterr()
        import json

        output = json.loads(captured.out)
        assert "error" in output

    def test_json_output_for_api_not_configured(self, temp_project: Path, monkeypatch, capsys):
        """Test JSON output when API is not configured."""
        monkeypatch.chdir(temp_project)

        # Run API audit without configuration
        run_audit(
            audit_type="spec-review",
            import_file=None,
            use_api=True,
            agent="chatgpt",
            output_format="json",
        )

        captured = capsys.readouterr()
        import json

        output = json.loads(captured.out)
        assert "error" in output
        assert "not configured" in output["error"]

    def test_json_output_for_missing_agent(self, temp_project: Path, monkeypatch, capsys):
        """Test JSON output when --api used without --agent."""
        monkeypatch.chdir(temp_project)

        run_audit(
            audit_type="spec-review",
            import_file=None,
            use_api=True,
            agent=None,
            output_format="json",
        )

        captured = capsys.readouterr()
        import json

        output = json.loads(captured.out)
        assert "error" in output
        assert "agent" in output["error"].lower()


class TestBuildAuditPromptForApi:
    """Tests for _build_audit_prompt_for_api function."""

    def test_returns_none_if_no_specs_dir(self, tmp_path: Path, monkeypatch, capsys):
        """Test that function returns None if .ldf/specs doesn't exist."""
        monkeypatch.chdir(tmp_path)

        result = _build_audit_prompt_for_api("spec-review", False, None)

        assert result is None
        captured = capsys.readouterr()
        assert "not found" in captured.out

    def test_returns_none_if_spec_not_found(self, temp_project: Path, monkeypatch, capsys):
        """Test that function returns None if specific spec doesn't exist."""
        monkeypatch.chdir(temp_project)

        result = _build_audit_prompt_for_api("spec-review", False, "nonexistent")

        assert result is None
        captured = capsys.readouterr()
        assert "not found" in captured.out

    def test_returns_none_if_no_specs(self, temp_project: Path, monkeypatch, capsys):
        """Test that function returns None if no specs exist."""
        # Ensure specs directory exists but is empty
        specs_dir = temp_project / ".ldf" / "specs"
        specs_dir.mkdir(exist_ok=True)
        # Remove any existing specs
        for d in specs_dir.iterdir():
            if d.is_dir():
                import shutil

                shutil.rmtree(d)

        monkeypatch.chdir(temp_project)

        result = _build_audit_prompt_for_api("spec-review", False, None)

        assert result is None
        captured = capsys.readouterr()
        assert "No specs found" in captured.out

    def test_returns_prompt_for_specific_spec(self, temp_project_with_specs: Path, monkeypatch):
        """Test that function returns prompt for specific spec."""
        monkeypatch.chdir(temp_project_with_specs)

        result = _build_audit_prompt_for_api("spec-review", False, "feature-a")

        assert result is not None
        assert "feature-a" in result
        assert "feature-b" not in result


class TestRunApiAudit:
    """Tests for _run_api_audit function."""

    def test_unconfigured_gemini_shows_config_example(
        self, temp_project_with_specs: Path, monkeypatch, capsys
    ):
        """Test that unconfigured Gemini shows config example."""
        monkeypatch.chdir(temp_project_with_specs)

        _run_api_audit(
            audit_type="spec-review",
            agent="gemini",
            auto_import=False,
            include_secrets=False,
            skip_confirm=True,
            spec_name=None,
        )

        captured = capsys.readouterr()
        assert "gemini" in captured.out
        assert "not configured" in captured.out
        assert "GOOGLE_API_KEY" in captured.out

    def test_unconfigured_provider_json_output(
        self, temp_project_with_specs: Path, monkeypatch, capsys
    ):
        """Test JSON output for unconfigured provider."""
        monkeypatch.chdir(temp_project_with_specs)

        _run_api_audit(
            audit_type="spec-review",
            agent="chatgpt",
            auto_import=False,
            include_secrets=False,
            skip_confirm=True,
            spec_name=None,
            output_format="json",
        )

        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert "error" in output
        assert "not configured" in output["error"]

    def test_full_audit_runs_multiple_types(
        self, temp_project_with_specs: Path, monkeypatch, capsys
    ):
        """Test that 'full' audit type runs multiple audit types."""
        monkeypatch.chdir(temp_project_with_specs)
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

        # Configure ChatGPT
        config_path = temp_project_with_specs / ".ldf" / "config.yaml"
        config = {
            "version": "1.0",
            "audit_api": {"chatgpt": {"api_key": "${OPENAI_API_KEY}", "model": "gpt-4"}},
        }
        config_path.write_text(yaml.safe_dump(config))

        mock_response = AuditResponse(
            success=True,
            provider="chatgpt",
            audit_type="spec-review",
            spec_name=None,
            content="## Findings\n\nNo issues.",
            timestamp="2024-01-15T10:00:00",
            usage={"total_tokens": 100},
        )

        with patch("ldf.audit_api.run_api_audit", return_value=mock_response):
            with patch("ldf.audit_api.save_audit_response") as mock_save:
                mock_save.return_value = Path("/tmp/saved.md")

                _run_api_audit(
                    audit_type="full",
                    agent="chatgpt",
                    auto_import=False,
                    include_secrets=False,
                    skip_confirm=True,
                    spec_name=None,
                )

        captured = capsys.readouterr()
        assert "Running full audit" in captured.out

    def test_successful_api_audit(self, temp_project_with_specs: Path, monkeypatch, capsys):
        """Test successful API audit."""
        monkeypatch.chdir(temp_project_with_specs)
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

        # Configure ChatGPT
        config_path = temp_project_with_specs / ".ldf" / "config.yaml"
        config = {
            "version": "1.0",
            "audit_api": {"chatgpt": {"api_key": "${OPENAI_API_KEY}", "model": "gpt-4"}},
        }
        config_path.write_text(yaml.safe_dump(config))

        mock_response = AuditResponse(
            success=True,
            provider="chatgpt",
            audit_type="spec-review",
            spec_name=None,
            content="## Findings\n\nNo issues.",
            timestamp="2024-01-15T10:00:00",
            usage={"total_tokens": 100},
        )

        with patch("ldf.audit_api.run_api_audit", return_value=mock_response):
            with patch("ldf.audit_api.save_audit_response") as mock_save:
                mock_save.return_value = Path("/tmp/saved.md")

                _run_api_audit(
                    audit_type="spec-review",
                    agent="chatgpt",
                    auto_import=False,
                    include_secrets=False,
                    skip_confirm=True,
                    spec_name=None,
                )

        captured = capsys.readouterr()
        assert "Saved:" in captured.out
        assert "Audit complete" in captured.out

    def test_successful_api_audit_with_auto_import(
        self, temp_project_with_specs: Path, monkeypatch, capsys
    ):
        """Test successful API audit with auto-import."""
        monkeypatch.chdir(temp_project_with_specs)
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

        # Configure ChatGPT
        config_path = temp_project_with_specs / ".ldf" / "config.yaml"
        config = {
            "version": "1.0",
            "audit_api": {"chatgpt": {"api_key": "${OPENAI_API_KEY}", "model": "gpt-4"}},
        }
        config_path.write_text(yaml.safe_dump(config))

        mock_response = AuditResponse(
            success=True,
            provider="chatgpt",
            audit_type="spec-review",
            spec_name=None,
            content="## Findings\n\nNo issues.",
            timestamp="2024-01-15T10:00:00",
            usage={"total_tokens": 100},
        )

        with patch("ldf.audit_api.run_api_audit", return_value=mock_response):
            with patch("ldf.audit_api.save_audit_response") as mock_save:
                mock_save.return_value = Path("/tmp/saved.md")

                _run_api_audit(
                    audit_type="spec-review",
                    agent="chatgpt",
                    auto_import=True,  # Auto-import enabled
                    include_secrets=False,
                    skip_confirm=True,
                    spec_name=None,
                )

        captured = capsys.readouterr()
        assert "Audit Response" in captured.out
        assert "auto-imported" in captured.out

    def test_failed_api_audit(self, temp_project_with_specs: Path, monkeypatch, capsys):
        """Test failed API audit."""
        monkeypatch.chdir(temp_project_with_specs)
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

        # Configure ChatGPT
        config_path = temp_project_with_specs / ".ldf" / "config.yaml"
        config = {
            "version": "1.0",
            "audit_api": {"chatgpt": {"api_key": "${OPENAI_API_KEY}", "model": "gpt-4"}},
        }
        config_path.write_text(yaml.safe_dump(config))

        mock_response = AuditResponse(
            success=False,
            provider="chatgpt",
            audit_type="spec-review",
            spec_name=None,
            content="",
            timestamp="2024-01-15T10:00:00",
            errors=["API timeout", "Retry failed"],
        )

        with patch("ldf.audit_api.run_api_audit", return_value=mock_response):
            _run_api_audit(
                audit_type="spec-review",
                agent="chatgpt",
                auto_import=False,
                include_secrets=False,
                skip_confirm=True,
                spec_name=None,
            )

        captured = capsys.readouterr()
        assert "failed" in captured.out.lower()
        assert "API timeout" in captured.out

    def test_api_audit_json_output(self, temp_project_with_specs: Path, monkeypatch, capsys):
        """Test API audit with JSON output."""
        monkeypatch.chdir(temp_project_with_specs)
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

        # Configure ChatGPT
        config_path = temp_project_with_specs / ".ldf" / "config.yaml"
        config = {
            "version": "1.0",
            "audit_api": {"chatgpt": {"api_key": "${OPENAI_API_KEY}", "model": "gpt-4"}},
        }
        config_path.write_text(yaml.safe_dump(config))

        mock_response = AuditResponse(
            success=True,
            provider="chatgpt",
            audit_type="spec-review",
            spec_name=None,
            content="## Findings",
            timestamp="2024-01-15T10:00:00",
            usage={"total_tokens": 100},
        )

        with patch("ldf.audit_api.run_api_audit", return_value=mock_response):
            with patch("ldf.audit_api.save_audit_response") as mock_save:
                mock_save.return_value = Path("/tmp/saved.md")

                _run_api_audit(
                    audit_type="spec-review",
                    agent="chatgpt",
                    auto_import=False,
                    include_secrets=False,
                    skip_confirm=True,
                    spec_name=None,
                    output_format="json",
                )

        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["audit_type"] == "spec-review"
        assert output["summary"]["successful"] == 1

    def test_api_audit_returns_early_when_no_specs_dir(
        self, temp_project: Path, monkeypatch, capsys
    ):
        """Test that _run_api_audit returns early when specs directory doesn't exist."""
        import shutil

        import yaml

        monkeypatch.chdir(temp_project)
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

        # Configure chatgpt so the agent config check passes
        config_path = temp_project / ".ldf" / "config.yaml"
        config = {
            "version": "1.0",
            "audit_api": {
                "chatgpt": {
                    "api_key": "${OPENAI_API_KEY}",
                    "model": "gpt-4",
                }
            },
        }
        with open(config_path, "w") as f:
            yaml.safe_dump(config, f)

        # Remove specs directory
        specs_dir = temp_project / ".ldf" / "specs"
        if specs_dir.exists():
            shutil.rmtree(specs_dir)

        # This should return early without error due to missing specs
        _run_api_audit(
            audit_type="spec-review",
            agent="chatgpt",
            auto_import=False,
            include_secrets=False,
            skip_confirm=True,
            spec_name=None,
        )

        captured = capsys.readouterr()
        assert "not found" in captured.out.lower() or "init" in captured.out.lower()


class TestImportFeedback:
    """Tests for _import_feedback function."""

    def test_import_creates_audit_history_dir(self, temp_project: Path, monkeypatch, capsys):
        """Test that import creates audit-history directory."""
        monkeypatch.chdir(temp_project)

        # Create feedback file
        feedback = temp_project / "feedback.md"
        feedback.write_text("## Findings\n\nNo issues.")

        # Ensure audit-history doesn't exist
        audit_dir = temp_project / ".ldf" / "audit-history"
        if audit_dir.exists():
            import shutil

            shutil.rmtree(audit_dir)

        _import_feedback(feedback)

        assert audit_dir.exists()
        files = list(audit_dir.glob("feedback-*.md"))
        assert len(files) == 1

    def test_import_displays_content(self, temp_project: Path, monkeypatch, capsys):
        """Test that import displays the feedback content."""
        monkeypatch.chdir(temp_project)

        # Create feedback file
        feedback = temp_project / "feedback.md"
        feedback.write_text("## Findings\n\nNo issues.")

        _import_feedback(feedback)

        captured = capsys.readouterr()
        assert "Importing feedback" in captured.out


class TestFullAuditType:
    """Tests for 'full' audit type."""

    def test_full_audit_includes_all_sections(self, temp_project_with_specs: Path, monkeypatch):
        """Test that 'full' audit type includes all review sections."""
        monkeypatch.chdir(temp_project_with_specs)
        specs_dir = temp_project_with_specs / ".ldf" / "specs"
        specs = list(specs_dir.iterdir())

        content = _build_audit_request("full", specs, include_secrets=False)

        # Should include content from all audit types
        assert "Requirements completeness" in content
        # "security vulnerabilities" is lowercase in actual content
        assert "security vulnerabilities" in content.lower()
        assert "Missing requirements" in content
        assert "Boundary conditions" in content
        assert "Architecture" in content


class TestAdditionalRedaction:
    """Tests for additional redaction patterns."""

    def test_redacts_github_tokens(self):
        """Test that GitHub tokens are redacted."""
        # Use a format that matches the specific GitHub token pattern
        content = "My token is ghp_1234567890123456789012345678901234567890."
        redacted = _redact_content(content)
        assert "ghp_1234567890" not in redacted
        assert "REDACTED" in redacted

    def test_redacts_slack_tokens(self):
        """Test that Slack tokens are redacted."""
        # Use a format that matches the specific Slack token pattern
        content = "My slack: xoxb-123456789012-1234567890123-AbcDefGhiJklMnoPqrS here"
        redacted = _redact_content(content)
        assert "xoxb-123456789012" not in redacted
        assert "REDACTED" in redacted

    def test_redacts_gitlab_tokens(self):
        """Test that GitLab tokens are redacted."""
        content = "My gitlab: glpat-1234567890abcdefghij here"
        redacted = _redact_content(content)
        assert "glpat-1234567890" not in redacted
        assert "REDACTED" in redacted

    def test_redacts_npm_tokens(self):
        """Test that npm tokens are redacted."""
        content = "NPM token is npm_1234567890abcdefghijklmnopqrstuvwxyz!"
        redacted = _redact_content(content)
        assert "npm_1234567890" not in redacted
        assert "REDACTED" in redacted

    def test_redacts_pem_private_keys(self):
        """Test that PEM private keys are redacted."""
        content = """-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEAn7lqz/abcd1234567890abcd1234567890
-----END RSA PRIVATE KEY-----"""
        redacted = _redact_content(content)
        assert "MIIEowIBAAKCAQEAn7lqz" not in redacted
        assert "[PEM_KEY_REDACTED]" in redacted

    def test_redacts_jwt_tokens(self):
        """Test that JWT tokens are redacted."""
        # JWT tokens are matched by the specific JWT pattern
        content = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
        redacted = _redact_content(content)
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in redacted
        assert "[JWT_REDACTED]" in redacted
