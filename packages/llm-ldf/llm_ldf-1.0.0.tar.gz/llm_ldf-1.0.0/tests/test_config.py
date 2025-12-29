"""Tests for ldf.utils.config module."""

from pathlib import Path

import pytest

from ldf.utils.config import (
    get_answerpacks_dir,
    get_config_value,
    get_default_config,
    get_specs_dir,
    get_templates_dir,
    load_config,
    save_config,
)


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_valid_config(self, temp_project: Path):
        """Test loading a valid config file."""
        config = load_config(temp_project)

        assert config is not None
        assert "version" in config
        assert "project" in config

    def test_raises_on_missing_config(self, tmp_path: Path):
        """Test that missing config raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError) as exc_info:
            load_config(tmp_path)

        assert "ldf init" in str(exc_info.value)

    def test_returns_empty_dict_for_empty_file(self, tmp_path: Path):
        """Test loading an empty config file."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()
        config_path = ldf_dir / "config.yaml"
        config_path.write_text("")

        config = load_config(tmp_path)
        assert config == {}


class TestGetConfigValue:
    """Tests for get_config_value function."""

    def test_get_simple_value(self, temp_project: Path):
        """Test getting a simple config value."""
        value = get_config_value("version", project_root=temp_project)
        assert value == "1.0"

    def test_get_nested_value(self, temp_project: Path):
        """Test getting a nested config value."""
        value = get_config_value("project.name", project_root=temp_project)
        assert value == "test-project"

    def test_returns_default_on_missing_key(self, temp_project: Path):
        """Test that missing key returns default."""
        value = get_config_value("nonexistent.key", default="fallback", project_root=temp_project)
        assert value == "fallback"

    def test_returns_default_on_missing_config(self, tmp_path: Path):
        """Test that missing config returns default."""
        value = get_config_value("any.key", default="fallback", project_root=tmp_path)
        assert value == "fallback"

    def test_get_deeply_nested_value(self, temp_project: Path):
        """Test getting a deeply nested value."""
        value = get_config_value("guardrails.preset", project_root=temp_project)
        assert value == "core"


class TestGetSpecsDir:
    """Tests for get_specs_dir function."""

    def test_returns_default_specs_dir(self, temp_project: Path):
        """Test getting default specs directory."""
        specs_dir = get_specs_dir(temp_project)

        assert specs_dir == temp_project / ".ldf" / "specs"

    def test_specs_dir_exists(self, temp_project: Path):
        """Test that returned specs dir exists."""
        specs_dir = get_specs_dir(temp_project)

        assert specs_dir.exists()


class TestGetAnswerpacksDir:
    """Tests for get_answerpacks_dir function."""

    def test_returns_answerpacks_dir(self, temp_project: Path):
        """Test getting answerpacks directory."""
        answerpacks_dir = get_answerpacks_dir(temp_project)

        assert answerpacks_dir == temp_project / ".ldf" / "answerpacks"


class TestGetTemplatesDir:
    """Tests for get_templates_dir function."""

    def test_returns_templates_dir(self, temp_project: Path):
        """Test getting templates directory."""
        templates_dir = get_templates_dir(temp_project)

        assert templates_dir == temp_project / ".ldf" / "templates"


class TestGetDefaultConfig:
    """Tests for get_default_config function."""

    def test_returns_valid_config(self):
        """Test that default config has all required keys (v1.1 schema)."""
        config = get_default_config()

        assert "_schema_version" in config
        assert config["_schema_version"] == "1.1"
        assert "project" in config
        assert "ldf" in config
        assert "question_packs" in config
        assert "mcp_servers" in config
        assert "lint" in config

    def test_default_preset_is_custom(self):
        """Test that default preset is custom (v1.1 schema: ldf.preset)."""
        config = get_default_config()

        assert config["ldf"]["preset"] == "custom"

    def test_has_default_question_packs(self):
        """Test that default config has question packs (v1.1 schema: core/optional)."""
        config = get_default_config()

        assert "core" in config["question_packs"]
        assert "security" in config["question_packs"]["core"]
        assert "testing" in config["question_packs"]["core"]


class TestSaveConfig:
    """Tests for save_config function."""

    def test_saves_config_file(self, tmp_path: Path):
        """Test saving config to file."""
        config = {"version": "1.0", "project": {"name": "test"}}

        save_config(config, tmp_path)

        config_path = tmp_path / ".ldf" / "config.yaml"
        assert config_path.exists()

    def test_creates_ldf_directory(self, tmp_path: Path):
        """Test that save_config creates .ldf directory."""
        config = {"version": "1.0"}

        save_config(config, tmp_path)

        assert (tmp_path / ".ldf").exists()

    def test_saved_config_is_readable(self, tmp_path: Path):
        """Test that saved config can be loaded."""
        config = {"version": "2.0", "project": {"name": "roundtrip"}}

        save_config(config, tmp_path)
        loaded = load_config(tmp_path)

        assert loaded["version"] == "2.0"
        assert loaded["project"]["name"] == "roundtrip"


class TestConfigFunctionsWithCwd:
    """Tests for config functions using cwd as default."""

    def test_load_config_uses_cwd(self, temp_project: Path, monkeypatch):
        """Test load_config uses cwd when no project_root provided."""
        monkeypatch.chdir(temp_project)

        config = load_config()

        assert config is not None
        assert "version" in config

    def test_get_specs_dir_uses_cwd(self, temp_project: Path, monkeypatch):
        """Test get_specs_dir uses cwd when no project_root provided."""
        monkeypatch.chdir(temp_project)

        specs_dir = get_specs_dir()

        assert specs_dir == temp_project / ".ldf" / "specs"

    def test_get_answerpacks_dir_uses_cwd(self, temp_project: Path, monkeypatch):
        """Test get_answerpacks_dir uses cwd when no project_root provided."""
        monkeypatch.chdir(temp_project)

        answerpacks_dir = get_answerpacks_dir()

        assert answerpacks_dir == temp_project / ".ldf" / "answerpacks"

    def test_get_templates_dir_uses_cwd(self, temp_project: Path, monkeypatch):
        """Test get_templates_dir uses cwd when no project_root provided."""
        monkeypatch.chdir(temp_project)

        templates_dir = get_templates_dir()

        assert templates_dir == temp_project / ".ldf" / "templates"

    def test_save_config_uses_cwd(self, tmp_path: Path, monkeypatch):
        """Test save_config uses cwd when no project_root provided."""
        monkeypatch.chdir(tmp_path)
        config = {"version": "1.0", "project": {"name": "cwd-test"}}

        save_config(config)

        config_path = tmp_path / ".ldf" / "config.yaml"
        assert config_path.exists()
