"""Tests for ldf.utils.descriptions module."""

from pathlib import Path

import pytest

from ldf.utils.descriptions import (
    format_guardrail_choice,
    format_mcp_server_choice,
    format_pack_choice,
    format_preset_choice,
    get_all_guardrails,
    get_all_mcp_servers,
    get_all_presets,
    get_core_guardrails,
    get_core_packs,
    get_domain_packs,
    get_guardrail_info,
    get_mcp_server_info,
    get_mcp_server_short,
    get_pack_info,
    get_pack_short,
    get_preset_extra_guardrails,
    get_preset_guardrails,
    get_preset_info,
    get_preset_recommended_packs,
    get_preset_short,
    get_term_explanation,
    get_term_info,
    is_core_pack,
    is_mcp_server_default,
    load_descriptions,
)


class TestLoadDescriptions:
    """Tests for load_descriptions function."""

    def test_loads_descriptions_yaml(self):
        """Test that descriptions.yaml is loaded."""
        descriptions = load_descriptions()

        assert isinstance(descriptions, dict)
        assert "presets" in descriptions
        assert "question_packs" in descriptions

    def test_raises_when_file_not_found(self, monkeypatch):
        """Test FileNotFoundError when file doesn't exist."""
        from ldf.utils import descriptions

        # Clear the cache first
        load_descriptions.cache_clear()

        # Mock the path to not exist
        fake_path = Path("/nonexistent/descriptions.yaml")
        monkeypatch.setattr(descriptions, "DESCRIPTIONS_PATH", fake_path)

        with pytest.raises(FileNotFoundError, match="Descriptions file not found"):
            load_descriptions()

        # Restore for other tests
        load_descriptions.cache_clear()


class TestPresetInfo:
    """Tests for preset-related functions."""

    def test_get_preset_info_returns_dict(self):
        """Test getting preset info returns a dictionary."""
        info = get_preset_info("saas")

        assert isinstance(info, dict)

    def test_get_preset_info_unknown_returns_empty(self):
        """Test unknown preset returns empty dict."""
        info = get_preset_info("unknown-preset")

        assert info == {}

    def test_get_preset_short(self):
        """Test getting preset short description."""
        short = get_preset_short("saas")

        assert isinstance(short, str)
        assert len(short) > 0

    def test_get_preset_short_unknown(self):
        """Test unknown preset returns preset name."""
        short = get_preset_short("unknown-preset")

        assert short == "unknown-preset"

    def test_get_preset_extra_guardrails(self):
        """Test getting extra guardrails string."""
        extra = get_preset_extra_guardrails("saas")

        assert isinstance(extra, str)
        # Should start with + or contain guardrail info
        assert "+" in extra or extra.isdigit()

    def test_get_preset_extra_guardrails_unknown(self):
        """Test unknown preset returns +0."""
        extra = get_preset_extra_guardrails("unknown-preset")

        assert extra == "+0"

    def test_get_preset_recommended_packs(self):
        """Test getting recommended packs list."""
        packs = get_preset_recommended_packs("saas")

        assert isinstance(packs, list)

    def test_get_preset_recommended_packs_unknown(self):
        """Test unknown preset returns empty list."""
        packs = get_preset_recommended_packs("unknown-preset")

        assert packs == []

    def test_get_all_presets(self):
        """Test getting all preset names."""
        presets = get_all_presets()

        assert isinstance(presets, list)
        assert len(presets) > 0
        assert "saas" in presets or len(presets) > 0


class TestPackInfo:
    """Tests for question pack-related functions."""

    def test_get_pack_info_returns_dict(self):
        """Test getting pack info returns a dictionary."""
        info = get_pack_info("security")

        assert isinstance(info, dict)

    def test_get_pack_info_unknown_returns_empty(self):
        """Test unknown pack returns empty dict."""
        info = get_pack_info("unknown-pack")

        assert info == {}

    def test_get_pack_short(self):
        """Test getting pack short description."""
        short = get_pack_short("security")

        assert isinstance(short, str)

    def test_get_pack_short_unknown(self):
        """Test unknown pack returns pack name."""
        short = get_pack_short("unknown-pack")

        assert short == "unknown-pack"

    def test_is_core_pack(self):
        """Test checking if pack is core."""
        # security is typically a core pack
        result = is_core_pack("security")

        assert isinstance(result, bool)

    def test_is_core_pack_unknown(self):
        """Test unknown pack returns False."""
        result = is_core_pack("unknown-pack")

        assert result is False

    def test_get_core_packs(self):
        """Test getting list of core packs."""
        packs = get_core_packs()

        assert isinstance(packs, list)

    def test_get_domain_packs(self):
        """Test getting list of domain packs."""
        packs = get_domain_packs()

        assert isinstance(packs, list)


class TestMcpServerInfo:
    """Tests for MCP server-related functions."""

    def test_get_mcp_server_info_returns_dict(self):
        """Test getting MCP server info returns a dictionary."""
        info = get_mcp_server_info("spec_inspector")

        assert isinstance(info, dict)

    def test_get_mcp_server_info_unknown_returns_empty(self):
        """Test unknown server returns empty dict."""
        info = get_mcp_server_info("unknown-server")

        assert info == {}

    def test_get_mcp_server_short(self):
        """Test getting MCP server short description."""
        short = get_mcp_server_short("spec_inspector")

        assert isinstance(short, str)

    def test_get_mcp_server_short_unknown(self):
        """Test unknown server returns server name."""
        short = get_mcp_server_short("unknown-server")

        assert short == "unknown-server"

    def test_is_mcp_server_default(self):
        """Test checking if server is default enabled."""
        result = is_mcp_server_default("spec_inspector")

        assert isinstance(result, bool)

    def test_is_mcp_server_default_unknown(self):
        """Test unknown server returns False."""
        result = is_mcp_server_default("unknown-server")

        assert result is False

    def test_get_all_mcp_servers(self):
        """Test getting list of all MCP servers."""
        servers = get_all_mcp_servers()

        assert isinstance(servers, list)


class TestTermInfo:
    """Tests for glossary term-related functions."""

    def test_get_term_info_returns_dict(self):
        """Test getting term info returns a dictionary."""
        info = get_term_info("RLS")

        assert isinstance(info, dict)

    def test_get_term_info_unknown_returns_empty(self):
        """Test unknown term returns empty dict."""
        info = get_term_info("UNKNOWN_TERM")

        assert info == {}

    def test_get_term_explanation(self):
        """Test getting term explanation."""
        explanation = get_term_explanation("RLS")

        assert isinstance(explanation, str)
        assert len(explanation) > 0

    def test_get_term_explanation_unknown(self):
        """Test unknown term returns the term itself."""
        explanation = get_term_explanation("UNKNOWN_TERM")

        assert explanation == "UNKNOWN_TERM"

    def test_get_term_explanation_with_full_name_and_short(self, monkeypatch):
        """Test term explanation formatting with full name and short."""
        from ldf.utils import descriptions

        # Mock get_term_info to return test data
        def mock_get_term_info(term):
            if term == "TEST":
                return {
                    "full_name": "Test Full Name",
                    "short": "A test description",
                }
            return {}

        monkeypatch.setattr(descriptions, "get_term_info", mock_get_term_info)

        explanation = descriptions.get_term_explanation("TEST")

        assert "TEST" in explanation
        assert "Test Full Name" in explanation
        assert "A test description" in explanation

    def test_get_term_explanation_with_only_short(self, monkeypatch):
        """Test term explanation formatting with only short."""
        from ldf.utils import descriptions

        # Mock get_term_info to return test data with only short
        def mock_get_term_info(term):
            if term == "TEST":
                return {
                    "short": "Just a short description",
                }
            return {}

        monkeypatch.setattr(descriptions, "get_term_info", mock_get_term_info)

        explanation = descriptions.get_term_explanation("TEST")

        assert "Just a short description" in explanation


class TestFormatFunctions:
    """Tests for format_* functions."""

    def test_format_preset_choice(self):
        """Test formatting preset for UI display."""
        formatted = format_preset_choice("saas")

        assert isinstance(formatted, str)
        assert "saas" in formatted
        assert "-" in formatted

    def test_format_pack_choice(self):
        """Test formatting pack for UI display."""
        formatted = format_pack_choice("security")

        assert isinstance(formatted, str)
        assert "security" in formatted
        assert "-" in formatted

    def test_format_mcp_server_choice(self):
        """Test formatting MCP server for UI display."""
        formatted = format_mcp_server_choice("spec_inspector")

        assert isinstance(formatted, str)
        assert "spec_inspector" in formatted
        assert "-" in formatted

    def test_format_guardrail_choice(self):
        """Test formatting guardrail for UI display."""
        guardrail = {"id": 1, "name": "Testing Coverage", "short": "Min coverage"}
        formatted = format_guardrail_choice(guardrail)

        assert isinstance(formatted, str)
        assert "1." in formatted
        assert "Testing Coverage" in formatted
        assert "Min coverage" in formatted


class TestGuardrailInfo:
    """Tests for guardrail-related functions."""

    def test_get_guardrail_info_returns_dict(self):
        """Test getting guardrail info returns a dictionary."""
        # Clear cache to ensure fresh load
        load_descriptions.cache_clear()
        info = get_guardrail_info(1)

        assert isinstance(info, dict)
        assert "name" in info
        assert "short" in info

    def test_get_guardrail_info_unknown_returns_empty(self):
        """Test unknown guardrail returns empty dict."""
        info = get_guardrail_info(999)

        assert info == {}

    def test_get_core_guardrails_returns_list(self):
        """Test getting core guardrails returns list with ids."""
        guardrails = get_core_guardrails()

        assert isinstance(guardrails, list)
        assert len(guardrails) > 0
        # Each should have id and is_core=True
        for g in guardrails:
            assert "id" in g
            assert g.get("is_core", False) is True

    def test_get_core_guardrails_sorted(self):
        """Test core guardrails are sorted by ID."""
        guardrails = get_core_guardrails()

        ids = [g["id"] for g in guardrails]
        assert ids == sorted(ids)

    def test_get_preset_guardrails_returns_list(self):
        """Test getting preset guardrails returns list."""
        guardrails = get_preset_guardrails("saas")

        assert isinstance(guardrails, list)
        # SaaS has extra guardrails
        for g in guardrails:
            assert "id" in g
            assert g.get("preset") == "saas"

    def test_get_preset_guardrails_unknown_returns_empty(self):
        """Test unknown preset returns empty list."""
        guardrails = get_preset_guardrails("unknown-preset")

        assert guardrails == []

    def test_get_all_guardrails_returns_all(self):
        """Test getting all guardrails."""
        guardrails = get_all_guardrails()

        assert isinstance(guardrails, list)
        assert len(guardrails) > 0
        # Should include both core and preset guardrails
        core_count = sum(1 for g in guardrails if g.get("is_core", False))
        preset_count = sum(1 for g in guardrails if g.get("preset"))
        assert core_count > 0
        assert preset_count > 0

    def test_get_all_guardrails_sorted(self):
        """Test all guardrails are sorted by ID."""
        guardrails = get_all_guardrails()

        ids = [g["id"] for g in guardrails]
        assert ids == sorted(ids)
