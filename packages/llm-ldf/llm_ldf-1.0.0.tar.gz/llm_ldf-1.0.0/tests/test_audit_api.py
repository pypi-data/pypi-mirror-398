"""Tests for ldf/audit_api.py - API integration for automated audits."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ldf import __version__
from ldf.audit_api import (
    AuditConfig,
    AuditResponse,
    ChatGPTAuditor,
    GeminiAuditor,
    _resolve_env_var,
    get_auditor,
    load_api_config,
    run_api_audit,
    save_audit_response,
)


class TestAuditConfig:
    """Tests for AuditConfig dataclass."""

    def test_audit_config_creation(self):
        """Test creating an AuditConfig."""
        config = AuditConfig(
            provider="chatgpt",
            api_key="test-key",
            model="gpt-4",
            timeout=60,
            max_tokens=2048,
        )
        assert config.provider == "chatgpt"
        assert config.api_key == "test-key"
        assert config.model == "gpt-4"
        assert config.timeout == 60
        assert config.max_tokens == 2048

    def test_audit_config_defaults(self):
        """Test AuditConfig default values."""
        config = AuditConfig(
            provider="gemini",
            api_key="test-key",
            model="gemini-pro",
        )
        assert config.timeout == 120
        assert config.max_tokens == 4096


class TestAuditResponse:
    """Tests for AuditResponse dataclass."""

    def test_audit_response_success(self):
        """Test successful AuditResponse."""
        response = AuditResponse(
            success=True,
            provider="chatgpt",
            audit_type="spec-review",
            spec_name="test-spec",
            content="## Findings\n\nNo issues found.",
            timestamp="2024-01-15T10:00:00",
        )
        assert response.success is True
        assert response.provider == "chatgpt"
        assert response.errors == []
        assert response.usage == {}

    def test_audit_response_failure(self):
        """Test failed AuditResponse."""
        response = AuditResponse(
            success=False,
            provider="gemini",
            audit_type="security",
            spec_name=None,
            content="",
            timestamp="2024-01-15T10:00:00",
            errors=["API error: rate limit exceeded"],
        )
        assert response.success is False
        assert len(response.errors) == 1
        assert "rate limit" in response.errors[0]


class TestResolveEnvVar:
    """Tests for environment variable resolution."""

    def test_resolve_env_var_simple(self, monkeypatch):
        """Test resolving a simple env var."""
        monkeypatch.setenv("TEST_API_KEY", "secret123")
        result = _resolve_env_var("${TEST_API_KEY}")
        assert result == "secret123"

    def test_resolve_env_var_embedded(self, monkeypatch):
        """Test resolving embedded env var."""
        monkeypatch.setenv("API_KEY", "abc123")
        result = _resolve_env_var("Bearer ${API_KEY}")
        assert result == "Bearer abc123"

    def test_resolve_env_var_missing(self, monkeypatch):
        """Test resolving missing env var returns empty."""
        monkeypatch.delenv("NONEXISTENT_VAR", raising=False)
        result = _resolve_env_var("${NONEXISTENT_VAR}")
        assert result == ""

    def test_resolve_env_var_no_var(self):
        """Test string without env var is unchanged."""
        result = _resolve_env_var("plain-string")
        assert result == "plain-string"

    def test_resolve_env_var_empty(self):
        """Test empty string returns empty."""
        result = _resolve_env_var("")
        assert result == ""


class TestLoadApiConfig:
    """Tests for loading API configuration."""

    def test_load_api_config_no_config_file(self, tmp_path):
        """Test loading config when no file exists."""
        configs = load_api_config(tmp_path)
        assert configs == {}

    def test_load_api_config_no_audit_api_section(self, tmp_path):
        """Test loading config without audit_api section."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()
        config_file = ldf_dir / "config.yaml"
        config_file.write_text(f"framework_version: '{__version__}'\n")

        configs = load_api_config(tmp_path)
        assert configs == {}

    def test_load_api_config_chatgpt(self, tmp_path, monkeypatch):
        """Test loading ChatGPT config."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test123")

        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()
        config_file = ldf_dir / "config.yaml"
        config_file.write_text("""
audit_api:
  chatgpt:
    api_key: ${OPENAI_API_KEY}
    model: gpt-4o
    timeout: 180
""")

        configs = load_api_config(tmp_path)
        assert "chatgpt" in configs
        assert configs["chatgpt"].api_key == "sk-test123"
        assert configs["chatgpt"].model == "gpt-4o"
        assert configs["chatgpt"].timeout == 180

    def test_load_api_config_gemini(self, tmp_path, monkeypatch):
        """Test loading Gemini config."""
        monkeypatch.setenv("GOOGLE_API_KEY", "AIza-test")

        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()
        config_file = ldf_dir / "config.yaml"
        config_file.write_text("""
audit_api:
  gemini:
    api_key: ${GOOGLE_API_KEY}
    model: gemini-pro
""")

        configs = load_api_config(tmp_path)
        assert "gemini" in configs
        assert configs["gemini"].api_key == "AIza-test"
        assert configs["gemini"].model == "gemini-pro"

    def test_load_api_config_both_providers(self, tmp_path, monkeypatch):
        """Test loading config for both providers."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.setenv("GOOGLE_API_KEY", "AIza-test")

        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()
        config_file = ldf_dir / "config.yaml"
        config_file.write_text("""
audit_api:
  chatgpt:
    api_key: ${OPENAI_API_KEY}
    model: gpt-4
  gemini:
    api_key: ${GOOGLE_API_KEY}
    model: gemini-pro
""")

        configs = load_api_config(tmp_path)
        assert len(configs) == 2
        assert "chatgpt" in configs
        assert "gemini" in configs

    def test_load_api_config_missing_api_key(self, tmp_path, monkeypatch):
        """Test config not loaded if API key is empty."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()
        config_file = ldf_dir / "config.yaml"
        config_file.write_text("""
audit_api:
  chatgpt:
    api_key: ${OPENAI_API_KEY}
    model: gpt-4
""")

        configs = load_api_config(tmp_path)
        assert "chatgpt" not in configs


class TestGetAuditor:
    """Tests for getting auditor instances."""

    def test_get_auditor_chatgpt(self, tmp_path, monkeypatch):
        """Test getting ChatGPT auditor."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

        configs = {
            "chatgpt": AuditConfig(
                provider="chatgpt",
                api_key="sk-test",
                model="gpt-4",
            )
        }

        auditor = get_auditor("chatgpt", configs)
        assert isinstance(auditor, ChatGPTAuditor)

    def test_get_auditor_gemini(self):
        """Test getting Gemini auditor."""
        configs = {
            "gemini": AuditConfig(
                provider="gemini",
                api_key="AIza-test",
                model="gemini-pro",
            )
        }

        auditor = get_auditor("gemini", configs)
        assert isinstance(auditor, GeminiAuditor)

    def test_get_auditor_not_configured(self):
        """Test getting auditor when not configured."""
        auditor = get_auditor("chatgpt", {})
        assert auditor is None

    def test_get_auditor_unknown_provider(self):
        """Test getting auditor for unknown provider."""
        configs = {
            "unknown": AuditConfig(
                provider="unknown",
                api_key="test",
                model="test-model",
            )
        }
        auditor = get_auditor("unknown", configs)
        assert auditor is None


class TestSaveAuditResponse:
    """Tests for saving audit responses."""

    def test_save_audit_response_success(self, tmp_path):
        """Test saving a successful audit response."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()

        response = AuditResponse(
            success=True,
            provider="chatgpt",
            audit_type="spec-review",
            spec_name="user-auth",
            content="## Findings\n\nNo issues found.",
            timestamp="2024-01-15T10:00:00",
            usage={"total_tokens": 1500},
        )

        saved_path = save_audit_response(response, tmp_path)

        assert saved_path.exists()
        assert "spec-review" in saved_path.name
        assert "user-auth" in saved_path.name
        assert "chatgpt" in saved_path.name

        content = saved_path.read_text()
        assert "# Audit Response: spec-review" in content
        assert "**Provider:** chatgpt" in content
        assert "**Spec:** user-auth" in content
        assert "**Status:** Success" in content
        assert "## Findings" in content

    def test_save_audit_response_failure(self, tmp_path):
        """Test saving a failed audit response."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()

        response = AuditResponse(
            success=False,
            provider="gemini",
            audit_type="security",
            spec_name=None,
            content="",
            timestamp="2024-01-15T10:00:00",
            errors=["API error: timeout", "Retry failed"],
        )

        saved_path = save_audit_response(response, tmp_path)

        assert saved_path.exists()
        content = saved_path.read_text()
        assert "**Status:** Failed" in content
        assert "## Errors" in content
        assert "API error: timeout" in content
        assert "Retry failed" in content

    def test_save_audit_response_no_spec_name(self, tmp_path):
        """Test saving response without spec name."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()

        response = AuditResponse(
            success=True,
            provider="chatgpt",
            audit_type="full",
            spec_name=None,
            content="Full audit results",
            timestamp="2024-01-15T10:00:00",
        )

        saved_path = save_audit_response(response, tmp_path)

        assert saved_path.exists()
        content = saved_path.read_text()
        assert "**Spec:** all" in content


class TestChatGPTAuditor:
    """Tests for ChatGPT auditor."""

    def test_provider_name(self):
        """Test ChatGPT auditor provider name."""
        config = AuditConfig(
            provider="chatgpt",
            api_key="test",
            model="gpt-4",
        )
        auditor = ChatGPTAuditor(config)
        assert auditor.provider_name == "chatgpt"


class TestGeminiAuditor:
    """Tests for Gemini auditor."""

    def test_provider_name(self):
        """Test Gemini auditor provider name."""
        config = AuditConfig(
            provider="gemini",
            api_key="test",
            model="gemini-pro",
        )
        auditor = GeminiAuditor(config)
        assert auditor.provider_name == "gemini"


class TestSystemPrompts:
    """Tests for audit type system prompts."""

    def test_chatgpt_system_prompts(self):
        """Test ChatGPT system prompts for different audit types."""
        config = AuditConfig(
            provider="chatgpt",
            api_key="test",
            model="gpt-4",
        )
        auditor = ChatGPTAuditor(config)

        # Test various audit types have appropriate prompts
        prompt = auditor._get_system_prompt("spec-review")
        assert "requirements" in prompt.lower()

        prompt = auditor._get_system_prompt("security")
        assert "security" in prompt.lower() or "OWASP" in prompt

        prompt = auditor._get_system_prompt("gap-analysis")
        assert "missing" in prompt.lower() or "gap" in prompt.lower()

        prompt = auditor._get_system_prompt("full")
        assert "comprehensive" in prompt.lower()

    def test_gemini_system_prompts(self):
        """Test Gemini system prompts for different audit types."""
        config = AuditConfig(
            provider="gemini",
            api_key="test",
            model="gemini-pro",
        )
        auditor = GeminiAuditor(config)

        # Test various audit types have appropriate prompts
        prompt = auditor._get_system_prompt("edge-cases")
        assert "edge" in prompt.lower() or "boundary" in prompt.lower()

        prompt = auditor._get_system_prompt("architecture")
        assert "architecture" in prompt.lower() or "design" in prompt.lower()


class TestChatGPTAuditorAudit:
    """Tests for ChatGPT auditor audit method."""

    @pytest.mark.asyncio
    async def test_audit_success(self):
        """Test successful ChatGPT audit with mocked API."""
        config = AuditConfig(
            provider="chatgpt",
            api_key="test-key",
            model="gpt-4",
            timeout=10,
        )
        auditor = ChatGPTAuditor(config)

        # Create mock response
        mock_message = MagicMock()
        mock_message.content = "## Findings\n\nNo issues found."
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_usage = MagicMock()
        mock_usage.prompt_tokens = 100
        mock_usage.completion_tokens = 50
        mock_usage.total_tokens = 150
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage

        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        # Mock the openai module at import time
        mock_openai = MagicMock()
        mock_openai.AsyncOpenAI.return_value = mock_client

        with patch.dict("sys.modules", {"openai": mock_openai}):
            response = await auditor.audit("test prompt", "spec-review", "test-spec")

        assert response.success is True
        assert response.content == "## Findings\n\nNo issues found."
        assert response.usage["total_tokens"] == 150

    @pytest.mark.asyncio
    async def test_audit_timeout(self):
        """Test ChatGPT audit timeout."""
        config = AuditConfig(
            provider="chatgpt",
            api_key="test-key",
            model="gpt-4",
            timeout=1,
        )
        auditor = ChatGPTAuditor(config)

        async def slow_response(*args, **kwargs):
            await asyncio.sleep(10)

        mock_client = MagicMock()
        mock_client.chat.completions.create = slow_response

        mock_openai = MagicMock()
        mock_openai.AsyncOpenAI.return_value = mock_client

        with patch.dict("sys.modules", {"openai": mock_openai}):
            response = await auditor.audit("test prompt", "spec-review")

        assert response.success is False
        assert "timed out" in response.errors[0]

    @pytest.mark.asyncio
    async def test_audit_api_error(self):
        """Test ChatGPT audit API error handling."""
        config = AuditConfig(
            provider="chatgpt",
            api_key="test-key",
            model="gpt-4",
        )
        auditor = ChatGPTAuditor(config)

        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=Exception("API rate limit exceeded")
        )

        mock_openai = MagicMock()
        mock_openai.AsyncOpenAI.return_value = mock_client

        with patch.dict("sys.modules", {"openai": mock_openai}):
            response = await auditor.audit("test prompt", "spec-review")

        assert response.success is False
        assert "API error" in response.errors[0]

    @pytest.mark.asyncio
    async def test_audit_no_usage_data(self):
        """Test ChatGPT audit when response has no usage data."""
        config = AuditConfig(
            provider="chatgpt",
            api_key="test-key",
            model="gpt-4",
        )
        auditor = ChatGPTAuditor(config)

        mock_message = MagicMock()
        mock_message.content = "Response"
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = None

        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        mock_openai = MagicMock()
        mock_openai.AsyncOpenAI.return_value = mock_client

        with patch.dict("sys.modules", {"openai": mock_openai}):
            response = await auditor.audit("test prompt", "spec-review")

        assert response.success is True
        assert response.usage["total_tokens"] == 0


class TestGeminiAuditorAudit:
    """Tests for Gemini auditor audit method."""

    @pytest.mark.asyncio
    async def test_audit_success(self):
        """Test successful Gemini audit with mocked API."""
        import types

        config = AuditConfig(
            provider="gemini",
            api_key="test-key",
            model="gemini-pro",
            timeout=10,
        )
        auditor = GeminiAuditor(config)

        mock_response = MagicMock()
        mock_response.text = "## Findings\n\nAll good."

        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response

        # Create a proper module mock
        mock_genai = types.ModuleType("google.generativeai")
        mock_genai.configure = MagicMock()
        mock_genai.GenerativeModel = MagicMock(return_value=mock_model)

        mock_google = types.ModuleType("google")
        mock_google.generativeai = mock_genai

        with patch.dict("sys.modules", {"google.generativeai": mock_genai, "google": mock_google}):
            response = await auditor.audit("test prompt", "security")

        assert response.success is True
        assert response.content == "## Findings\n\nAll good."

    @pytest.mark.asyncio
    async def test_audit_timeout(self):
        """Test Gemini audit timeout."""
        import types

        config = AuditConfig(
            provider="gemini",
            api_key="test-key",
            model="gemini-pro",
            timeout=1,
        )
        auditor = GeminiAuditor(config)

        def slow_generate(*args, **kwargs):
            import time

            time.sleep(10)

        mock_model = MagicMock()
        mock_model.generate_content = slow_generate

        mock_genai = types.ModuleType("google.generativeai")
        mock_genai.configure = MagicMock()
        mock_genai.GenerativeModel = MagicMock(return_value=mock_model)

        mock_google = types.ModuleType("google")
        mock_google.generativeai = mock_genai

        with patch.dict("sys.modules", {"google.generativeai": mock_genai, "google": mock_google}):
            response = await auditor.audit("test prompt", "spec-review")

        assert response.success is False
        assert "timed out" in response.errors[0]

    @pytest.mark.asyncio
    async def test_audit_api_error(self):
        """Test Gemini audit API error handling."""
        import types

        config = AuditConfig(
            provider="gemini",
            api_key="test-key",
            model="gemini-pro",
        )
        auditor = GeminiAuditor(config)

        mock_model = MagicMock()
        mock_model.generate_content.side_effect = Exception("Quota exceeded")

        mock_genai = types.ModuleType("google.generativeai")
        mock_genai.configure = MagicMock()
        mock_genai.GenerativeModel = MagicMock(return_value=mock_model)

        mock_google = types.ModuleType("google")
        mock_google.generativeai = mock_genai

        with patch.dict("sys.modules", {"google.generativeai": mock_genai, "google": mock_google}):
            response = await auditor.audit("test prompt", "spec-review")

        assert response.success is False
        assert "API error" in response.errors[0]


class TestRunApiAudit:
    """Tests for run_api_audit function."""

    @pytest.mark.asyncio
    async def test_run_api_audit_provider_not_configured(self, tmp_path, monkeypatch):
        """Test run_api_audit when provider is not configured."""
        monkeypatch.chdir(tmp_path)
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()
        (ldf_dir / "config.yaml").write_text("version: '1.0'\n")

        response = await run_api_audit(
            provider="chatgpt",
            audit_type="spec-review",
            prompt="Test prompt",
        )

        assert response.success is False
        assert "not configured" in response.errors[0]

    @pytest.mark.asyncio
    async def test_run_api_audit_success(self, tmp_path, monkeypatch, capsys):
        """Test run_api_audit success path."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()
        (ldf_dir / "config.yaml").write_text("""
audit_api:
  chatgpt:
    api_key: ${OPENAI_API_KEY}
    model: gpt-4
""")

        mock_response = AuditResponse(
            success=True,
            provider="chatgpt",
            audit_type="spec-review",
            spec_name=None,
            content="## Findings",
            timestamp="2024-01-15T10:00:00",
            usage={"total_tokens": 100},
        )

        with patch.object(ChatGPTAuditor, "audit", return_value=mock_response):
            response = await run_api_audit(
                provider="chatgpt",
                audit_type="spec-review",
                prompt="Test prompt",
            )

        assert response.success is True
        captured = capsys.readouterr()
        assert "Audit complete" in captured.out
        assert "100" in captured.out  # tokens

    @pytest.mark.asyncio
    async def test_run_api_audit_failure(self, tmp_path, monkeypatch, capsys):
        """Test run_api_audit failure path."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()
        (ldf_dir / "config.yaml").write_text("""
audit_api:
  chatgpt:
    api_key: ${OPENAI_API_KEY}
    model: gpt-4
""")

        mock_response = AuditResponse(
            success=False,
            provider="chatgpt",
            audit_type="spec-review",
            spec_name=None,
            content="",
            timestamp="2024-01-15T10:00:00",
            errors=["API timeout"],
        )

        with patch.object(ChatGPTAuditor, "audit", return_value=mock_response):
            response = await run_api_audit(
                provider="chatgpt",
                audit_type="spec-review",
                prompt="Test prompt",
            )

        assert response.success is False
        captured = capsys.readouterr()
        assert "failed" in captured.out.lower()


class TestLoadApiConfigEdgeCases:
    """Tests for edge cases in load_api_config."""

    def test_load_api_config_default_cwd(self, tmp_path, monkeypatch):
        """Test load_api_config uses cwd when no path given."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()
        (ldf_dir / "config.yaml").write_text("""
audit_api:
  chatgpt:
    api_key: ${OPENAI_API_KEY}
    model: gpt-4
""")

        configs = load_api_config()  # No path argument
        assert "chatgpt" in configs

    def test_load_api_config_corrupt_yaml(self, tmp_path):
        """Test load_api_config handles corrupt YAML."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()
        (ldf_dir / "config.yaml").write_text("invalid: yaml: [broken")

        configs = load_api_config(tmp_path)
        assert configs == {}


class TestSaveAuditResponseEdgeCases:
    """Tests for edge cases in save_audit_response."""

    def test_save_audit_response_default_cwd(self, tmp_path, monkeypatch):
        """Test save_audit_response uses cwd when no path given."""
        monkeypatch.chdir(tmp_path)
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()

        response = AuditResponse(
            success=True,
            provider="chatgpt",
            audit_type="spec-review",
            spec_name=None,
            content="Test content",
            timestamp="2024-01-15T10:00:00",
        )

        saved_path = save_audit_response(response)  # No path argument
        assert saved_path.exists()
        assert saved_path.parent == ldf_dir / "audit-history"

    def test_save_audit_response_creates_audit_history_dir(self, tmp_path):
        """Test save_audit_response creates audit-history if missing."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()
        # Don't create audit-history

        response = AuditResponse(
            success=True,
            provider="chatgpt",
            audit_type="full",
            spec_name=None,
            content="Test",
            timestamp="2024-01-15T10:00:00",
        )

        saved_path = save_audit_response(response, tmp_path)
        assert saved_path.exists()
        assert (ldf_dir / "audit-history").exists()


class TestSaveAuditResponseSecurity:
    """Security tests for path traversal prevention in save_audit_response."""

    def test_spec_name_path_traversal_sanitized(self, tmp_path):
        """Test that path traversal in spec_name is sanitized."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()

        response = AuditResponse(
            success=True,
            provider="chatgpt",
            audit_type="spec-review",
            spec_name="../../../etc/passwd",  # Malicious spec_name
            content="Test content",
            timestamp="2024-01-15T10:00:00",
        )

        saved_path = save_audit_response(response, tmp_path)

        # File should be saved in audit-history, not escaped
        assert saved_path.parent == ldf_dir / "audit-history"
        # Path separators should be replaced with underscores
        assert "../" not in saved_path.name
        assert "_" in saved_path.name  # .. and / replaced with _

    def test_audit_type_path_traversal_sanitized(self, tmp_path):
        """Test that path traversal in audit_type is sanitized."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()

        response = AuditResponse(
            success=True,
            provider="chatgpt",
            audit_type="../../malicious",  # Malicious audit_type
            spec_name="test-spec",
            content="Test content",
            timestamp="2024-01-15T10:00:00",
        )

        saved_path = save_audit_response(response, tmp_path)

        # File should be saved in audit-history, not escaped
        assert saved_path.parent == ldf_dir / "audit-history"
        assert "../" not in saved_path.name

    def test_provider_path_traversal_sanitized(self, tmp_path):
        """Test that path traversal in provider is sanitized."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()

        response = AuditResponse(
            success=True,
            provider="../../../etc/shadow",  # Malicious provider
            audit_type="spec-review",
            spec_name=None,
            content="Test content",
            timestamp="2024-01-15T10:00:00",
        )

        saved_path = save_audit_response(response, tmp_path)

        # File should be saved in audit-history, not escaped
        assert saved_path.parent == ldf_dir / "audit-history"
        assert "../" not in saved_path.name

    def test_combined_path_traversal_attempts(self, tmp_path):
        """Test that combined path traversal attempts are blocked."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()

        response = AuditResponse(
            success=True,
            provider="..\\..\\windows\\system32",  # Windows path traversal
            audit_type="..%2F..%2Fetc",  # URL-encoded (not decoded, but safe)
            spec_name="..\\..\\sensitive",  # Backslash traversal
            content="Test content",
            timestamp="2024-01-15T10:00:00",
        )

        saved_path = save_audit_response(response, tmp_path)

        # File should be saved in audit-history, not escaped
        assert saved_path.parent == ldf_dir / "audit-history"
        assert "\\" not in saved_path.name.replace("_", "")  # Backslashes sanitized
