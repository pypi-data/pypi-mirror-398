"""Tests for ldf.utils.guardrail_loader module."""

from pathlib import Path

import pytest

from ldf.utils.guardrail_loader import (
    Guardrail,
    _get_default_core_guardrails,
    get_active_guardrails,
    get_guardrail_by_id,
    get_guardrail_by_name,
    load_core_guardrails,
    load_guardrails,
    load_preset_guardrails,
)


class TestLoadCoreGuardrails:
    """Tests for load_core_guardrails function."""

    def test_loads_core_guardrails(self):
        """Test loading core guardrails from framework."""
        guardrails = load_core_guardrails()

        assert len(guardrails) == 8
        assert guardrails[0].id == 1
        assert guardrails[0].name == "Testing Coverage"
        assert guardrails[0].severity == "critical"
        assert guardrails[0].enabled is True

    def test_core_guardrails_have_required_fields(self):
        """Test that all core guardrails have required fields."""
        guardrails = load_core_guardrails()

        for g in guardrails:
            assert isinstance(g.id, int)
            assert isinstance(g.name, str)
            assert len(g.name) > 0
            assert g.severity in ("critical", "high", "medium", "low")


class TestLoadPresetGuardrails:
    """Tests for load_preset_guardrails function."""

    def test_loads_saas_preset(self, ldf_framework_path: Path):
        """Test loading SaaS preset guardrails."""
        saas_file = ldf_framework_path / "guardrails" / "presets" / "saas.yaml"
        if not saas_file.exists():
            pytest.skip("SaaS preset not found")

        guardrails = load_preset_guardrails("saas")

        # SaaS preset should have additional guardrails
        assert len(guardrails) > 0
        assert any(g.name == "Multi-Tenancy" or "tenancy" in g.name.lower() for g in guardrails)

    def test_handles_missing_preset(self):
        """Test handling of non-existent preset."""
        guardrails = load_preset_guardrails("nonexistent-preset")

        assert guardrails == []

    def test_custom_preset_returns_empty(self):
        """Test that 'custom' preset returns empty list."""
        guardrails = load_preset_guardrails("custom")

        assert guardrails == []


class TestLoadGuardrails:
    """Tests for load_guardrails function."""

    def test_returns_core_guardrails_for_project(self, temp_project: Path):
        """Test that core guardrails are returned for a project."""
        guardrails = load_guardrails(temp_project)

        assert len(guardrails) == 8
        assert all(isinstance(g, Guardrail) for g in guardrails)

    def test_returns_core_for_non_ldf_project(self, tmp_path: Path):
        """Test returns core guardrails for non-LDF project."""
        guardrails = load_guardrails(tmp_path)

        # Should fall back to core guardrails
        assert len(guardrails) == 8
        assert isinstance(guardrails, list)


class TestGetActiveGuardrails:
    """Tests for get_active_guardrails function."""

    def test_returns_enabled_guardrails(self, temp_project: Path):
        """Test that only enabled guardrails are returned."""
        guardrails = get_active_guardrails(temp_project)

        assert len(guardrails) == 8
        assert all(isinstance(g, Guardrail) for g in guardrails)
        assert all(g.enabled for g in guardrails)

    def test_filters_disabled_guardrails(self, temp_project: Path):
        """Test that disabled guardrails are filtered out."""
        # Update guardrails.yaml to disable one
        guardrails_file = temp_project / ".ldf" / "guardrails.yaml"
        guardrails_file.write_text("""version: "1.0"
extends: core
disabled:
  - 8  # Disable Documentation guardrail
""")

        guardrails = get_active_guardrails(temp_project)

        assert len(guardrails) == 7
        assert not any(g.id == 8 for g in guardrails)


class TestGuardrailDataclass:
    """Tests for Guardrail dataclass."""

    def test_guardrail_creation(self):
        """Test creating a Guardrail instance."""
        guardrail = Guardrail(
            id=1,
            name="Test Guardrail",
            description="A test guardrail",
            severity="high",
            enabled=True,
        )

        assert guardrail.id == 1
        assert guardrail.name == "Test Guardrail"
        assert guardrail.description == "A test guardrail"
        assert guardrail.severity == "high"
        assert guardrail.enabled is True

    def test_guardrail_defaults(self):
        """Test Guardrail default values."""
        guardrail = Guardrail(
            id=1,
            name="Test",
            description="Test",
            severity="medium",
            enabled=True,
        )

        assert guardrail.config == {}

    def test_guardrail_with_config(self):
        """Test Guardrail with custom config."""
        guardrail = Guardrail(
            id=1,
            name="Coverage",
            description="Test coverage",
            severity="critical",
            enabled=True,
            config={"threshold": 80, "critical_paths": 90},
        )

        assert guardrail.config["threshold"] == 80
        assert guardrail.config["critical_paths"] == 90

    def test_guardrail_from_dict(self):
        """Test creating Guardrail from dictionary."""
        data = {
            "id": 99,
            "name": "Custom Check",
            "description": "A custom guardrail",
            "severity": "low",
            "enabled": False,
            "checklist": ["Check item 1", "Check item 2"],
            "config": {"key": "value"},
        }

        guardrail = Guardrail.from_dict(data)

        assert guardrail.id == 99
        assert guardrail.name == "Custom Check"
        assert guardrail.description == "A custom guardrail"
        assert guardrail.severity == "low"
        assert guardrail.enabled is False
        assert len(guardrail.checklist) == 2
        assert guardrail.config == {"key": "value"}

    def test_guardrail_from_dict_minimal(self):
        """Test creating Guardrail from minimal dictionary."""
        data = {
            "id": 1,
            "name": "Minimal",
        }

        guardrail = Guardrail.from_dict(data)

        assert guardrail.id == 1
        assert guardrail.name == "Minimal"
        assert guardrail.description == ""
        assert guardrail.severity == "medium"  # default
        assert guardrail.enabled is True  # default
        assert guardrail.checklist == []  # default
        assert guardrail.config == {}  # default


class TestLoadCoreGuardrailsFallback:
    """Tests for load_core_guardrails fallback behavior."""

    def test_uses_defaults_when_core_file_missing(self, monkeypatch):
        """Test fallback to defaults when core.yaml is missing."""
        from ldf.utils import guardrail_loader

        # Mock the path to not exist
        fake_path = Path("/nonexistent/path/core.yaml")
        monkeypatch.setattr(guardrail_loader, "CORE_GUARDRAILS_PATH", fake_path)

        guardrails = load_core_guardrails()

        # Should return default guardrails
        assert len(guardrails) == 8
        assert guardrails[0].name == "Testing Coverage"


class TestGetDefaultCoreGuardrails:
    """Tests for _get_default_core_guardrails function."""

    def test_returns_eight_guardrails(self):
        """Test that defaults return 8 guardrails."""
        defaults = _get_default_core_guardrails()

        assert len(defaults) == 8

    def test_default_guardrails_have_all_ids(self):
        """Test that default guardrails have IDs 1-8."""
        defaults = _get_default_core_guardrails()
        ids = [g.id for g in defaults]

        assert ids == [1, 2, 3, 4, 5, 6, 7, 8]

    def test_default_guardrails_have_names(self):
        """Test that default guardrails have expected names."""
        defaults = _get_default_core_guardrails()
        names = [g.name for g in defaults]

        assert "Testing Coverage" in names
        assert "Security Basics" in names
        assert "Error Handling" in names


class TestLoadGuardrailsEdgeCases:
    """Edge case tests for load_guardrails function."""

    def test_uses_cwd_when_project_root_is_none(self, temp_project: Path, monkeypatch):
        """Test using cwd when project_root is None."""
        monkeypatch.chdir(temp_project)

        guardrails = load_guardrails(None)

        assert len(guardrails) == 8
        assert all(isinstance(g, Guardrail) for g in guardrails)

    def test_loads_preset_guardrails(self, temp_project: Path, ldf_framework_path: Path):
        """Test loading guardrails with a preset."""
        # Check if saas preset exists
        saas_file = ldf_framework_path / "guardrails" / "presets" / "saas.yaml"
        if not saas_file.exists():
            pytest.skip("SaaS preset not found")

        guardrails_file = temp_project / ".ldf" / "guardrails.yaml"
        guardrails_file.write_text("""version: "1.0"
preset: saas
""")

        guardrails = load_guardrails(temp_project)

        # Should have core + preset guardrails
        assert len(guardrails) > 8

    def test_applies_overrides(self, temp_project: Path):
        """Test applying overrides to guardrails."""
        guardrails_file = temp_project / ".ldf" / "guardrails.yaml"
        guardrails_file.write_text("""version: "1.0"
overrides:
  "1":
    enabled: false
    config:
      threshold: 95
""")

        guardrails = load_guardrails(temp_project)

        guardrail_1 = next(g for g in guardrails if g.id == 1)
        assert guardrail_1.enabled is False
        assert guardrail_1.config.get("threshold") == 95

    def test_adds_custom_guardrails(self, temp_project: Path):
        """Test adding custom guardrails from config."""
        guardrails_file = temp_project / ".ldf" / "guardrails.yaml"
        guardrails_file.write_text("""version: "1.0"
custom:
  - id: 100
    name: "Custom Team Rule"
    description: "A custom rule for the team"
    severity: "medium"
    checklist:
      - "Check custom thing"
""")

        guardrails = load_guardrails(temp_project)

        # Should have 8 core + 1 custom
        assert len(guardrails) == 9
        custom = next((g for g in guardrails if g.id == 100), None)
        assert custom is not None
        assert custom.name == "Custom Team Rule"

    def test_disables_guardrail_by_name(self, temp_project: Path):
        """Test disabling guardrail by name."""
        guardrails_file = temp_project / ".ldf" / "guardrails.yaml"
        guardrails_file.write_text("""version: "1.0"
disabled:
  - "Testing Coverage"
""")

        guardrails = load_guardrails(temp_project)

        testing_coverage = next(g for g in guardrails if g.name == "Testing Coverage")
        assert testing_coverage.enabled is False

    def test_filters_by_selected_ids(self, temp_project: Path):
        """Test filtering guardrails by selected_ids from ldf init --custom."""
        guardrails_file = temp_project / ".ldf" / "guardrails.yaml"
        guardrails_file.write_text("""version: "1.0"
selected_ids:
  - 1
  - 3
  - 5
""")

        guardrails = load_guardrails(temp_project)

        # Should only return the 3 selected guardrails
        assert len(guardrails) == 3
        ids = [g.id for g in guardrails]
        assert ids == [1, 3, 5]

    def test_selected_ids_maintains_order(self, temp_project: Path):
        """Test that selected_ids maintains the specified order."""
        guardrails_file = temp_project / ".ldf" / "guardrails.yaml"
        guardrails_file.write_text("""version: "1.0"
selected_ids:
  - 8
  - 2
  - 5
  - 1
""")

        guardrails = load_guardrails(temp_project)

        ids = [g.id for g in guardrails]
        assert ids == [8, 2, 5, 1]

    def test_selected_ids_ignores_nonexistent(self, temp_project: Path):
        """Test that selected_ids ignores IDs that don't exist."""
        guardrails_file = temp_project / ".ldf" / "guardrails.yaml"
        guardrails_file.write_text("""version: "1.0"
selected_ids:
  - 1
  - 999
  - 3
""")

        guardrails = load_guardrails(temp_project)

        # Should only return guardrails 1 and 3, not 999
        assert len(guardrails) == 2
        ids = [g.id for g in guardrails]
        assert ids == [1, 3]


class TestGetGuardrailById:
    """Tests for get_guardrail_by_id function."""

    def test_finds_guardrail_by_id(self, temp_project: Path):
        """Test finding a guardrail by its ID."""
        guardrail = get_guardrail_by_id(1, temp_project)

        assert guardrail is not None
        assert guardrail.id == 1
        assert guardrail.name == "Testing Coverage"

    def test_returns_none_for_unknown_id(self, temp_project: Path):
        """Test returning None for unknown ID."""
        guardrail = get_guardrail_by_id(999, temp_project)

        assert guardrail is None

    def test_uses_cwd_when_project_root_is_none(self, temp_project: Path, monkeypatch):
        """Test using cwd when project_root is None."""
        monkeypatch.chdir(temp_project)

        guardrail = get_guardrail_by_id(1, None)

        assert guardrail is not None
        assert guardrail.id == 1


class TestGetGuardrailByName:
    """Tests for get_guardrail_by_name function."""

    def test_finds_guardrail_by_name(self, temp_project: Path):
        """Test finding a guardrail by its name."""
        guardrail = get_guardrail_by_name("Testing Coverage", temp_project)

        assert guardrail is not None
        assert guardrail.name == "Testing Coverage"
        assert guardrail.id == 1

    def test_finds_guardrail_case_insensitive(self, temp_project: Path):
        """Test finding a guardrail with case-insensitive name."""
        guardrail = get_guardrail_by_name("testing coverage", temp_project)

        assert guardrail is not None
        assert guardrail.name == "Testing Coverage"

    def test_returns_none_for_unknown_name(self, temp_project: Path):
        """Test returning None for unknown name."""
        guardrail = get_guardrail_by_name("Nonexistent Guardrail", temp_project)

        assert guardrail is None

    def test_uses_cwd_when_project_root_is_none(self, temp_project: Path, monkeypatch):
        """Test using cwd when project_root is None."""
        monkeypatch.chdir(temp_project)

        guardrail = get_guardrail_by_name("Testing Coverage", None)

        assert guardrail is not None
