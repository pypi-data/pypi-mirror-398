"""Tests for ldf.spec module."""

from pathlib import Path

from ldf.spec import create_spec, get_spec_path, list_specs


class TestCreateSpec:
    """Tests for create_spec function."""

    def test_creates_spec_directory(self, temp_project: Path):
        """Test that create_spec creates the spec directory."""
        result = create_spec("test-feature", temp_project)

        assert result is True
        spec_dir = temp_project / ".ldf" / "specs" / "test-feature"
        assert spec_dir.exists()

    def test_creates_requirements_md(self, temp_project: Path):
        """Test that create_spec creates requirements.md."""
        create_spec("test-feature", temp_project)

        requirements = temp_project / ".ldf" / "specs" / "test-feature" / "requirements.md"
        assert requirements.exists()
        content = requirements.read_text()
        assert "test-feature" in content

    def test_creates_design_md(self, temp_project: Path):
        """Test that create_spec creates design.md."""
        create_spec("test-feature", temp_project)

        design = temp_project / ".ldf" / "specs" / "test-feature" / "design.md"
        assert design.exists()
        content = design.read_text()
        assert "test-feature" in content

    def test_creates_tasks_md(self, temp_project: Path):
        """Test that create_spec creates tasks.md."""
        create_spec("test-feature", temp_project)

        tasks = temp_project / ".ldf" / "specs" / "test-feature" / "tasks.md"
        assert tasks.exists()
        content = tasks.read_text()
        assert "test-feature" in content

    def test_creates_answerpack_directory(self, temp_project: Path):
        """Test that create_spec creates the answerpack directory."""
        create_spec("test-feature", temp_project)

        answerpack = temp_project / ".ldf" / "answerpacks" / "test-feature"
        assert answerpack.exists()

    def test_fails_if_ldf_not_initialized(self, tmp_path: Path):
        """Test that create_spec fails if LDF is not initialized."""
        result = create_spec("test-feature", tmp_path)

        assert result is False

    def test_fails_if_spec_already_exists(self, temp_project: Path):
        """Test that create_spec fails if the spec already exists."""
        # Create the spec first
        create_spec("test-feature", temp_project)

        # Try to create it again
        result = create_spec("test-feature", temp_project)

        assert result is False

    def test_replaces_feature_name_placeholder(self, temp_project: Path):
        """Test that create_spec replaces {feature-name} placeholder."""
        # Create templates directory with a placeholder
        templates_dir = temp_project / ".ldf" / "templates"
        templates_dir.mkdir(exist_ok=True)
        (templates_dir / "requirements.md").write_text(
            "# {feature-name} - Requirements\n\nFeature: {feature}\n"
        )

        create_spec("my-cool-feature", temp_project)

        requirements = temp_project / ".ldf" / "specs" / "my-cool-feature" / "requirements.md"
        content = requirements.read_text()
        assert "my-cool-feature" in content
        assert "{feature-name}" not in content
        assert "{feature}" not in content


class TestListSpecs:
    """Tests for list_specs function."""

    def test_returns_empty_list_for_new_project(self, temp_project: Path):
        """Test that list_specs returns empty list for new project."""
        result = list_specs(temp_project)

        assert result == []

    def test_returns_spec_names(self, temp_project: Path):
        """Test that list_specs returns spec names."""
        create_spec("feature-a", temp_project)
        create_spec("feature-b", temp_project)

        result = list_specs(temp_project)

        assert "feature-a" in result
        assert "feature-b" in result

    def test_returns_empty_for_non_ldf_project(self, tmp_path: Path):
        """Test that list_specs returns empty for non-LDF project."""
        result = list_specs(tmp_path)

        assert result == []


class TestGetSpecPath:
    """Tests for get_spec_path function."""

    def test_returns_path_for_existing_spec(self, temp_project: Path):
        """Test that get_spec_path returns path for existing spec."""
        create_spec("test-feature", temp_project)

        result = get_spec_path("test-feature", temp_project)

        assert result is not None
        assert result == temp_project / ".ldf" / "specs" / "test-feature"

    def test_returns_none_for_nonexistent_spec(self, temp_project: Path):
        """Test that get_spec_path returns None for nonexistent spec."""
        result = get_spec_path("nonexistent", temp_project)

        assert result is None

    def test_returns_none_for_non_ldf_project(self, tmp_path: Path):
        """Test that get_spec_path returns None for non-LDF project."""
        result = get_spec_path("test-feature", tmp_path)

        assert result is None


class TestSpecNameSanitization:
    """Tests for spec name path traversal prevention."""

    def test_rejects_path_traversal_with_dotdot(self, temp_project: Path):
        """Test that create_spec rejects names with .. path traversal."""
        result = create_spec("../escape", temp_project)

        assert result is False
        # Ensure no escape directory was created
        escape_dir = temp_project.parent / "escape"
        assert not escape_dir.exists()

    def test_rejects_absolute_path_unix(self, temp_project: Path):
        """Test that create_spec rejects absolute Unix paths."""
        result = create_spec("/etc/passwd", temp_project)

        assert result is False

    def test_rejects_absolute_path_windows(self, temp_project: Path):
        """Test that create_spec rejects absolute Windows paths."""
        result = create_spec("\\Users\\test", temp_project)

        assert result is False

    def test_rejects_forward_slash_in_name(self, temp_project: Path):
        """Test that create_spec rejects names with forward slashes."""
        result = create_spec("my/feature", temp_project)

        assert result is False

    def test_rejects_backslash_in_name(self, temp_project: Path):
        """Test that create_spec rejects names with backslashes."""
        result = create_spec("my\\feature", temp_project)

        assert result is False

    def test_allows_valid_hyphenated_name(self, temp_project: Path):
        """Test that create_spec allows valid hyphenated names."""
        result = create_spec("my-cool-feature", temp_project)

        assert result is True
        assert (temp_project / ".ldf" / "specs" / "my-cool-feature").exists()

    def test_allows_valid_underscored_name(self, temp_project: Path):
        """Test that create_spec allows valid underscored names."""
        result = create_spec("my_cool_feature", temp_project)

        assert result is True
        assert (temp_project / ".ldf" / "specs" / "my_cool_feature").exists()


class TestListSpecsSymlinkSecurity:
    """Security tests for symlink filtering in list_specs."""

    def test_filters_symlink_escaping_specs_dir(self, temp_project: Path):
        """Test that list_specs filters out symlinks pointing outside specs dir."""
        import os

        if os.name == "nt":
            import pytest
            pytest.skip("Symlink tests not supported on Windows")

        # Create a real spec
        create_spec("real-spec", temp_project)

        # Create a symlink pointing outside specs directory
        specs_dir = temp_project / ".ldf" / "specs"
        evil_link = specs_dir / "evil-link"
        evil_link.symlink_to("/etc")

        result = list_specs(temp_project)

        # Should include real spec but not the symlink
        assert "real-spec" in result
        assert "evil-link" not in result

    def test_filters_hidden_directories(self, temp_project: Path):
        """Test that list_specs filters out hidden directories."""
        # Create a real spec
        create_spec("visible-spec", temp_project)

        # Create a hidden directory (should be filtered)
        specs_dir = temp_project / ".ldf" / "specs"
        hidden = specs_dir / ".hidden-spec"
        hidden.mkdir()
        (hidden / "requirements.md").write_text("# Hidden")

        result = list_specs(temp_project)

        assert "visible-spec" in result
        assert ".hidden-spec" not in result


class TestGetSpecPathSymlinkSecurity:
    """Security tests for symlink validation in get_spec_path."""

    def test_returns_none_for_symlink_escape(self, temp_project: Path):
        """Test that get_spec_path returns None for symlinks escaping specs dir."""
        import os

        if os.name == "nt":
            import pytest
            pytest.skip("Symlink tests not supported on Windows")

        # Create specs directory
        specs_dir = temp_project / ".ldf" / "specs"
        specs_dir.mkdir(parents=True, exist_ok=True)

        # Create a symlink pointing outside specs directory
        evil_link = specs_dir / "evil-spec"
        evil_link.symlink_to("/tmp")

        result = get_spec_path("evil-spec", temp_project)

        # Should return None because symlink escapes specs_dir
        assert result is None

    def test_returns_path_for_safe_symlink(self, temp_project: Path):
        """Test that get_spec_path allows symlinks within specs dir."""
        import os

        if os.name == "nt":
            import pytest
            pytest.skip("Symlink tests not supported on Windows")

        # Create a real spec
        create_spec("real-spec", temp_project)

        # Create a symlink within specs directory pointing to the real spec
        specs_dir = temp_project / ".ldf" / "specs"
        alias_link = specs_dir / "spec-alias"
        alias_link.symlink_to(specs_dir / "real-spec")

        result = get_spec_path("spec-alias", temp_project)

        # Should return the path since symlink stays within specs_dir
        assert result is not None
        assert result.name == "spec-alias"
