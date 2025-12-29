"""Tests for LDF update functionality."""

import pytest

from ldf import __version__
from ldf.init import FRAMEWORK_DIR, compute_file_checksum, initialize_project
from ldf.update import (
    Conflict,
    FileChange,
    UpdateDiff,
    UpdateResult,
    _copy_framework_file,
    _diff_question_packs,
    _is_file_modified,
    apply_updates,
    check_for_updates,
    get_update_diff,
    load_project_config,
    print_update_check,
    print_update_diff,
    print_update_result,
    save_project_config,
)


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project with LDF initialized."""
    project_root = tmp_path / "test-project"
    project_root.mkdir()

    # Initialize LDF in non-interactive mode
    initialize_project(
        project_path=project_root,
        preset="custom",
        question_packs=["security", "testing"],
        mcp_servers=["spec_inspector"],
        non_interactive=True,
    )

    return project_root


@pytest.fixture
def temp_project_old_version(temp_project):
    """Create a project with an older framework version."""
    config = load_project_config(temp_project)
    # v1.1 schema stores version in ldf.version
    if "ldf" not in config:
        config["ldf"] = {}
    config["ldf"]["version"] = "0.0.1"
    # Also set legacy field for backwards compat
    config["framework_version"] = "0.0.1"
    save_project_config(temp_project, config)
    return temp_project


class TestCheckForUpdates:
    """Tests for check_for_updates()."""

    def test_check_detects_version_difference(self, temp_project_old_version):
        """Should detect when framework version differs from project version."""
        info = check_for_updates(temp_project_old_version)

        assert info.current_version == "0.0.1"
        assert info.latest_version == __version__
        assert info.has_updates is True

    def test_check_reports_no_updates_when_current(self, temp_project):
        """Should report no updates when versions match."""
        info = check_for_updates(temp_project)

        assert info.current_version == __version__
        assert info.latest_version == __version__
        assert info.has_updates is False

    def test_check_lists_updatable_components(self, temp_project):
        """Should list all updatable components."""
        info = check_for_updates(temp_project)

        assert "templates" in info.updatable_components
        assert "macros" in info.updatable_components
        assert "question-packs" in info.updatable_components


class TestGetUpdateDiff:
    """Tests for get_update_diff()."""

    def test_dry_run_shows_unchanged_files(self, temp_project):
        """Should show files as unchanged when they match framework."""
        diff = get_update_diff(temp_project)

        # Templates should show as unchanged since they were just copied
        unchanged_templates = [p for p in diff.files_unchanged if "templates/" in p]
        assert len(unchanged_templates) > 0

    def test_dry_run_detects_modified_templates(self, temp_project):
        """Should detect when template files have been modified."""
        # Modify a template
        template_path = temp_project / ".ldf" / "templates" / "requirements.md"
        original_content = template_path.read_text()
        template_path.write_text(original_content + "\n\n# Custom addition")

        diff = get_update_diff(temp_project, components=["templates"])

        # Should show the modified template as needing update
        update_paths = [c.path for c in diff.files_to_update]
        assert "templates/requirements.md" in update_paths

    def test_detects_user_modified_question_packs(self, temp_project):
        """Should detect when user has modified a question pack."""
        # Get the config with checksums
        config = load_project_config(temp_project)
        _original_checksums = config.get("_checksums", {})  # noqa: F841 - stored for reference

        # Modify the security question pack (now in core/ subdirectory)
        pack_path = temp_project / ".ldf" / "question-packs" / "core" / "security.yaml"
        original_content = pack_path.read_text()
        pack_path.write_text(original_content + "\n\n# User customization")

        # Now simulate a framework update by changing the checksum expectation
        # (In real usage, the framework source would have changed)
        # For testing, we modify the stored checksum to something different
        config["_checksums"]["question-packs/core/security.yaml"] = "fake_old_checksum"
        save_project_config(temp_project, config)

        diff = get_update_diff(temp_project, components=["question-packs"])

        # Should show as a conflict since checksum doesn't match
        conflict_paths = [c.file_path for c in diff.conflicts]
        assert "question-packs/core/security.yaml" in conflict_paths

    def test_filters_by_component(self, temp_project):
        """Should only show changes for specified components."""
        diff = get_update_diff(temp_project, components=["templates"])

        # Should only have templates-related paths
        all_paths = (
            [c.path for c in diff.files_to_update]
            + [c.path for c in diff.files_to_add]
            + diff.files_unchanged
        )

        for path in all_paths:
            assert path.startswith("templates/"), f"Unexpected path: {path}"


class TestApplyUpdates:
    """Tests for apply_updates()."""

    def test_update_replaces_templates(self, temp_project):
        """Should replace template files with framework versions."""
        # Modify a template
        template_path = temp_project / ".ldf" / "templates" / "design.md"
        template_path.write_text("# Modified template\n")

        result = apply_updates(temp_project, components=["templates"])

        assert result.success is True
        assert any("templates/design.md" in f for f in result.files_updated)

        # Verify content matches framework
        framework_content = (FRAMEWORK_DIR / "templates" / "design.md").read_text()
        updated_content = template_path.read_text()
        assert updated_content == framework_content

    def test_update_replaces_macros(self, temp_project):
        """Should replace macro files with framework versions."""
        # Modify a macro
        macro_path = temp_project / ".ldf" / "macros" / "clarify-first.md"
        macro_path.write_text("# Modified macro\n")

        result = apply_updates(temp_project, components=["macros"])

        assert result.success is True
        assert any("macros/clarify-first.md" in f for f in result.files_updated)

    def test_update_preserves_modified_question_packs_when_skipped(self, temp_project):
        """Should preserve user-modified question packs when skip is chosen."""
        # Modify a question pack (v1.1 schema: files are in core/ subdirectory)
        pack_path = temp_project / ".ldf" / "question-packs" / "core" / "security.yaml"
        custom_content = "# My custom security questions\n"
        pack_path.write_text(custom_content)

        # Simulate a framework update scenario by changing the stored checksum
        config = load_project_config(temp_project)
        config["_checksums"]["question-packs/core/security.yaml"] = "old_checksum"
        save_project_config(temp_project, config)

        # Apply with skip resolution
        result = apply_updates(
            temp_project,
            components=["question-packs"],
            conflict_resolutions={"question-packs/core/security.yaml": "skip"},
        )

        assert result.success is True
        # Content should be preserved
        assert pack_path.read_text() == custom_content

    def test_update_overwrites_when_use_framework(self, temp_project):
        """Should overwrite user changes when use_framework is chosen."""
        # Modify a question pack (v1.1 schema: files are in core/ subdirectory)
        pack_path = temp_project / ".ldf" / "question-packs" / "core" / "security.yaml"
        pack_path.write_text("# My custom security questions\n")

        # Simulate a framework update scenario
        config = load_project_config(temp_project)
        config["_checksums"]["question-packs/core/security.yaml"] = "old_checksum"
        save_project_config(temp_project, config)

        # Apply with use_framework resolution
        result = apply_updates(
            temp_project,
            components=["question-packs"],
            conflict_resolutions={"question-packs/core/security.yaml": "use_framework"},
        )

        assert result.success is True
        # Content should match framework
        framework_content = (
            FRAMEWORK_DIR / "question-packs" / "core" / "security.yaml"
        ).read_text()
        assert pack_path.read_text() == framework_content

    def test_update_updates_version_in_config(self, temp_project_old_version):
        """Should update framework_version in config after successful update."""
        result = apply_updates(temp_project_old_version)

        assert result.success is True

        config = load_project_config(temp_project_old_version)
        assert config["framework_version"] == __version__
        assert "framework_updated" in config

    def test_update_never_touches_specs(self, temp_project):
        """Should never modify files in specs/ directory."""
        # Create a spec
        spec_dir = temp_project / ".ldf" / "specs" / "test-feature"
        spec_dir.mkdir(parents=True)
        req_file = spec_dir / "requirements.md"
        custom_content = "# My custom spec\n"
        req_file.write_text(custom_content)

        _result = apply_updates(temp_project)

        # Spec should be untouched
        assert req_file.read_text() == custom_content

    def test_update_never_touches_answerpacks(self, temp_project):
        """Should never modify files in answerpacks/ directory."""
        # Create an answerpack
        answerpack_dir = temp_project / ".ldf" / "answerpacks" / "test-feature"
        answerpack_dir.mkdir(parents=True)
        answers_file = answerpack_dir / "security.yaml"
        custom_content = "answers:\n  - question: test\n    answer: yes\n"
        answers_file.write_text(custom_content)

        _result = apply_updates(temp_project)

        # Answerpack should be untouched
        assert answers_file.read_text() == custom_content

    def test_update_with_only_flag(self, temp_project):
        """Should only update specified components."""
        # Modify both templates and macros
        template_path = temp_project / ".ldf" / "templates" / "design.md"
        macro_path = temp_project / ".ldf" / "macros" / "clarify-first.md"

        template_path.write_text("# Modified\n")
        macro_path.write_text("# Modified\n")

        # Only update templates
        _result = apply_updates(temp_project, components=["templates"])

        # Template should be updated
        framework_template = (FRAMEWORK_DIR / "templates" / "design.md").read_text()
        assert template_path.read_text() == framework_template

        # Macro should still be modified
        assert macro_path.read_text() == "# Modified\n"

    def test_update_dry_run_does_not_modify(self, temp_project):
        """Dry run should not modify any files."""
        # Modify a template
        template_path = temp_project / ".ldf" / "templates" / "design.md"
        modified_content = "# Modified template\n"
        template_path.write_text(modified_content)

        _result = apply_updates(temp_project, dry_run=True)

        # File should not be changed
        assert template_path.read_text() == modified_content


class TestChecksums:
    """Tests for checksum functionality."""

    def test_update_stores_checksums_on_init(self, temp_project):
        """Init should store checksums for question packs."""
        config = load_project_config(temp_project)

        assert "_checksums" in config
        # v1.1 schema: question packs are in core/ subdirectory
        assert "question-packs/core/security.yaml" in config["_checksums"]
        assert "question-packs/core/testing.yaml" in config["_checksums"]

    def test_checksums_match_file_content(self, temp_project):
        """Stored checksums should match actual file content."""
        config = load_project_config(temp_project)
        checksums = config.get("_checksums", {})

        for relative_path, stored_checksum in checksums.items():
            file_path = temp_project / ".ldf" / relative_path
            if file_path.exists():
                actual_checksum = compute_file_checksum(file_path)
                assert actual_checksum == stored_checksum, f"Checksum mismatch for {relative_path}"


class TestEdgeCases:
    """Tests for edge cases."""

    def test_project_without_version_tracking(self, temp_project):
        """Should handle projects initialized before version tracking."""
        # Remove version tracking fields (both v1.1 and legacy)
        config = load_project_config(temp_project)
        config.pop("framework_version", None)
        config.pop("framework_updated", None)
        config.pop("_checksums", None)
        # v1.1 schema stores version in ldf.version - remove it too
        if "ldf" in config and "version" in config["ldf"]:
            del config["ldf"]["version"]
        save_project_config(temp_project, config)

        info = check_for_updates(temp_project)

        assert info.current_version == "0.0.0"
        assert info.has_updates is True

    def test_missing_framework_file_handled(self, temp_project):
        """Should handle missing framework files gracefully."""
        # This is mainly a defensive test - framework files should always exist
        diff = get_update_diff(temp_project)
        # Should complete without error
        assert isinstance(diff, UpdateDiff)

    def test_empty_project_directory(self, tmp_path):
        """Should handle project with no .ldf directory."""
        project_root = tmp_path / "empty-project"
        project_root.mkdir()

        info = check_for_updates(project_root)

        # Should return empty/default values without crashing
        assert info.current_version == "0.0.0"
        assert info.updatable_components == []


class TestIsFileModified:
    """Tests for _is_file_modified function."""

    def test_returns_true_when_no_checksum(self, temp_project):
        """Should return True when no checksum is stored."""
        config = load_project_config(temp_project)
        config["_checksums"] = {}
        save_project_config(temp_project, config)

        result = _is_file_modified(temp_project, "templates/design.md", config)
        assert result is True

    def test_returns_true_when_file_missing(self, temp_project):
        """Should return True when file doesn't exist."""
        config = load_project_config(temp_project)
        config["_checksums"]["nonexistent/file.md"] = "somechecksum"

        result = _is_file_modified(temp_project, "nonexistent/file.md", config)
        assert result is True

    def test_returns_false_when_checksums_match(self, temp_project):
        """Should return False when checksums match."""
        config = load_project_config(temp_project)
        # Get actual checksum of existing file
        file_path = temp_project / ".ldf" / "templates" / "design.md"
        actual_checksum = compute_file_checksum(file_path)
        config["_checksums"]["templates/design.md"] = actual_checksum
        save_project_config(temp_project, config)

        result = _is_file_modified(temp_project, "templates/design.md", config)
        assert result is False


class TestDiffQuestionPacks:
    """Tests for _diff_question_packs function."""

    def test_handles_missing_dest_dir(self, tmp_path):
        """Should handle when question-packs dir doesn't exist."""
        project_root = tmp_path / "project"
        ldf_dir = project_root / ".ldf"
        ldf_dir.mkdir(parents=True)

        config = {"question_packs": ["security"]}
        diff = UpdateDiff()

        _diff_question_packs(project_root, config, diff)

        # Should return without adding anything
        assert len(diff.files_to_add) == 0

    def test_handles_pack_not_in_framework(self, temp_project):
        """Should handle packs that don't exist in framework."""
        config = load_project_config(temp_project)
        config["question_packs"] = ["nonexistent-pack"]
        save_project_config(temp_project, config)

        diff = UpdateDiff()
        _diff_question_packs(temp_project, config, diff)

        # Should not add any files for nonexistent pack
        assert not any("nonexistent-pack" in c.path for c in diff.files_to_add)

    def test_adds_missing_pack_from_dest(self, temp_project):
        """Should add pack if it exists in framework but not in project."""
        # Add a new pack to config that doesn't exist in project
        config = load_project_config(temp_project)
        # v1.1 schema: question_packs is {core: [...], optional: [...]}
        qp = config.get("question_packs", {})
        if isinstance(qp, dict):
            if "core" not in qp:
                qp["core"] = []
            qp["core"].append("api-design")  # A pack from framework
            config["question_packs"] = qp
        else:
            # Legacy flat list
            config["question_packs"].append("api-design")
        save_project_config(temp_project, config)

        # Remove the pack file from project if it exists
        pack_path_core = temp_project / ".ldf" / "question-packs" / "core" / "api-design.yaml"
        pack_path_flat = temp_project / ".ldf" / "question-packs" / "api-design.yaml"
        for pack_path in [pack_path_core, pack_path_flat]:
            if pack_path.exists():
                pack_path.unlink()

        diff = UpdateDiff()
        _diff_question_packs(temp_project, config, diff)

        # Should add the pack (path depends on where it's expected)
        add_paths = [c.path for c in diff.files_to_add]
        assert any("api-design.yaml" in p for p in add_paths)


class TestCopyFrameworkFile:
    """Tests for _copy_framework_file function."""

    def test_copies_template_file(self, temp_project):
        """Should copy template file from framework."""
        ldf_dir = temp_project / ".ldf"
        checksums = {}

        _copy_framework_file(ldf_dir, "templates/design.md", checksums)

        assert (ldf_dir / "templates" / "design.md").exists()
        assert "templates/design.md" in checksums

    def test_copies_macro_file(self, temp_project):
        """Should copy macro file from framework."""
        ldf_dir = temp_project / ".ldf"
        checksums = {}

        _copy_framework_file(ldf_dir, "macros/clarify-first.md", checksums)

        assert (ldf_dir / "macros" / "clarify-first.md").exists()
        assert "macros/clarify-first.md" in checksums

    def test_copies_question_pack_from_core(self, temp_project):
        """Should copy question pack from core directory."""
        ldf_dir = temp_project / ".ldf"
        checksums = {}

        _copy_framework_file(ldf_dir, "question-packs/security.yaml", checksums)

        assert (ldf_dir / "question-packs" / "security.yaml").exists()
        assert "question-packs/security.yaml" in checksums

    def test_copies_question_pack_from_domain(self, temp_project):
        """Should copy question pack from domain directory if not in core."""
        from ldf.update import FRAMEWORK_DIR

        ldf_dir = temp_project / ".ldf"
        checksums = {}

        # Create a mock domain pack (domain directory may not exist)
        domain_dir = FRAMEWORK_DIR / "question-packs" / "domain"
        domain_dir.mkdir(parents=True, exist_ok=True)
        domain_pack = domain_dir / "fintech.yaml"
        domain_pack.write_text("questions:\n  - id: test\n    text: Test question\n")

        try:
            _copy_framework_file(ldf_dir, "question-packs/fintech.yaml", checksums)
            assert (ldf_dir / "question-packs" / "fintech.yaml").exists()
        finally:
            # Clean up the mock domain pack
            if domain_pack.exists():
                domain_pack.unlink()
            # Only remove domain dir if it's empty
            if domain_dir.exists() and not any(domain_dir.iterdir()):
                domain_dir.rmdir()

    def test_raises_for_unknown_component(self, temp_project):
        """Should raise ValueError for unknown component."""
        ldf_dir = temp_project / ".ldf"
        checksums = {}

        with pytest.raises(ValueError, match="Unknown component"):
            _copy_framework_file(ldf_dir, "unknown/file.md", checksums)

    def test_raises_for_missing_source(self, temp_project):
        """Should raise FileNotFoundError for missing source file."""
        ldf_dir = temp_project / ".ldf"
        checksums = {}

        with pytest.raises(FileNotFoundError, match="Source file not found"):
            _copy_framework_file(ldf_dir, "templates/nonexistent.md", checksums)


class TestApplyUpdatesEdgeCases:
    """Edge case tests for apply_updates."""

    def test_handles_add_error(self, temp_project, monkeypatch):
        """Should handle errors during file addition."""
        # Modify template to trigger update
        template_path = temp_project / ".ldf" / "templates" / "design.md"
        template_path.unlink()  # Remove file to trigger add

        # Mock _copy_framework_file to fail
        def mock_copy(*args, **kwargs):
            raise PermissionError("Cannot write file")

        monkeypatch.setattr("ldf.update._copy_framework_file", mock_copy)

        result = apply_updates(temp_project, components=["templates"])

        assert result.success is False
        assert len(result.errors) > 0

    def test_handles_update_error(self, temp_project, monkeypatch):
        """Should handle errors during file update."""
        # Modify template to trigger update
        template_path = temp_project / ".ldf" / "templates" / "design.md"
        template_path.write_text("# Modified\n")

        # Mock _copy_framework_file to fail
        def mock_copy(*args, **kwargs):
            raise OSError("Disk full")

        monkeypatch.setattr("ldf.update._copy_framework_file", mock_copy)

        result = apply_updates(temp_project, components=["templates"])

        assert result.success is False
        assert any("Failed to update" in e for e in result.errors)

    def test_keep_local_resolution(self, temp_project):
        """Should preserve local file with keep_local resolution."""
        # Modify a question pack (v1.1 schema: files are in core/ subdirectory)
        pack_path = temp_project / ".ldf" / "question-packs" / "core" / "security.yaml"
        custom_content = "# Keep my content\n"
        pack_path.write_text(custom_content)

        # Simulate conflict
        config = load_project_config(temp_project)
        config["_checksums"]["question-packs/core/security.yaml"] = "fake_checksum"
        save_project_config(temp_project, config)

        result = apply_updates(
            temp_project,
            components=["question-packs"],
            conflict_resolutions={"question-packs/core/security.yaml": "keep_local"},
        )

        assert result.success is True
        assert any("kept local" in f for f in result.files_skipped)
        assert pack_path.read_text() == custom_content

    def test_dry_run_with_conflict_resolution(self, temp_project):
        """Should show would-replace message in dry run."""
        # Modify a question pack (v1.1 schema: files are in core/ subdirectory)
        pack_path = temp_project / ".ldf" / "question-packs" / "core" / "security.yaml"
        pack_path.write_text("# Modified\n")

        # Simulate conflict
        config = load_project_config(temp_project)
        config["_checksums"]["question-packs/core/security.yaml"] = "fake_checksum"
        save_project_config(temp_project, config)

        result = apply_updates(
            temp_project,
            components=["question-packs"],
            conflict_resolutions={"question-packs/core/security.yaml": "use_framework"},
            dry_run=True,
        )

        assert result.success is True
        assert any("would replace" in f for f in result.files_updated)

    def test_conflict_use_framework_error(self, temp_project, monkeypatch):
        """Should handle error when replacing conflict file."""
        # Modify a question pack (v1.1 schema: files are in core/ subdirectory)
        pack_path = temp_project / ".ldf" / "question-packs" / "core" / "security.yaml"
        pack_path.write_text("# Modified\n")

        # Simulate conflict
        config = load_project_config(temp_project)
        config["_checksums"]["question-packs/core/security.yaml"] = "fake_checksum"
        save_project_config(temp_project, config)

        # Mock _copy_framework_file to fail
        def mock_copy(*args, **kwargs):
            raise OSError("Write error")

        monkeypatch.setattr("ldf.update._copy_framework_file", mock_copy)

        result = apply_updates(
            temp_project,
            components=["question-packs"],
            conflict_resolutions={"question-packs/core/security.yaml": "use_framework"},
        )

        assert result.success is False


class TestPrintUpdateCheck:
    """Tests for print_update_check function."""

    def test_prints_up_to_date(self, temp_project, capsys):
        """Should print up to date message when no updates."""
        from ldf.update import UpdateInfo

        info = UpdateInfo(
            current_version=__version__,
            latest_version=__version__,
            has_updates=False,
            updatable_components=["templates"],
        )

        print_update_check(info)

        captured = capsys.readouterr()
        assert "up to date" in captured.out

    def test_prints_updates_available(self, capsys):
        """Should print updates available message."""
        from ldf.update import UpdateInfo

        info = UpdateInfo(
            current_version="0.0.1",
            latest_version=__version__,
            has_updates=True,
            updatable_components=["templates", "macros"],
        )

        print_update_check(info)

        captured = capsys.readouterr()
        assert "Updates available" in captured.out
        assert "templates" in captured.out
        assert "macros" in captured.out


class TestPrintUpdateDiff:
    """Tests for print_update_diff function."""

    def test_prints_all_change_types(self, capsys):
        """Should print all change types."""
        diff = UpdateDiff(
            files_to_add=[FileChange("templates/new.md", "add", "New file")],
            files_to_update=[FileChange("templates/design.md", "update", "Updated")],
            conflicts=[Conflict("question-packs/security.yaml", "user_modified")],
            files_unchanged=["macros/clarify-first.md"],
        )

        print_update_diff(diff)

        captured = capsys.readouterr()
        assert "+" in captured.out  # Add symbol
        assert "~" in captured.out  # Update symbol
        assert "!" in captured.out  # Conflict symbol
        assert "=" in captured.out  # Unchanged symbol

    def test_prints_dry_run_message(self, capsys):
        """Should print dry run preview message."""
        diff = UpdateDiff(files_to_update=[FileChange("templates/design.md", "update", "Updated")])

        print_update_diff(diff, dry_run=True)

        captured = capsys.readouterr()
        assert "Preview of changes" in captured.out
        assert "Would update" in captured.out

    def test_prints_no_changes_message(self, capsys):
        """Should print no changes message."""
        diff = UpdateDiff()

        print_update_diff(diff)

        captured = capsys.readouterr()
        assert "No changes needed" in captured.out

    def test_prints_conflict_summary(self, capsys):
        """Should print conflict summary."""
        diff = UpdateDiff(
            conflicts=[
                Conflict("file1.yaml", "user_modified"),
                Conflict("file2.yaml", "user_modified"),
            ]
        )

        print_update_diff(diff)

        captured = capsys.readouterr()
        assert "2 file(s) with local changes" in captured.out


class TestPrintUpdateResult:
    """Tests for print_update_result function."""

    def test_prints_updated_files(self, capsys):
        """Should print updated files list."""
        result = UpdateResult(
            success=True,
            files_updated=["[+] templates/new.md", "[~] templates/design.md"],
        )

        print_update_result(result)

        captured = capsys.readouterr()
        assert "Updated files" in captured.out
        assert "templates/new.md" in captured.out

    def test_prints_skipped_files(self, capsys):
        """Should print skipped files list."""
        result = UpdateResult(
            success=True,
            files_skipped=["[!] question-packs/security.yaml (skipped)"],
        )

        print_update_result(result)

        captured = capsys.readouterr()
        assert "Skipped files" in captured.out
        assert "security.yaml" in captured.out

    def test_prints_errors(self, capsys):
        """Should print error messages."""
        result = UpdateResult(
            success=False,
            errors=["Failed to write templates/design.md", "Permission denied"],
        )

        print_update_result(result)

        captured = capsys.readouterr()
        assert "Errors" in captured.out
        assert "Failed to write" in captured.out

    def test_prints_success_message(self, capsys):
        """Should print success message."""
        result = UpdateResult(success=True)

        print_update_result(result)

        captured = capsys.readouterr()
        assert "Update complete" in captured.out

    def test_prints_failure_message(self, capsys):
        """Should print failure message."""
        result = UpdateResult(success=False, errors=["Error"])

        print_update_result(result)

        captured = capsys.readouterr()
        assert "completed with errors" in captured.out


class TestGetUpdateDiffEdgeCases:
    """Edge case tests for get_update_diff."""

    def test_ignores_unknown_component(self, temp_project):
        """Should ignore unknown components."""
        diff = get_update_diff(temp_project, components=["unknown-component"])

        assert len(diff.files_to_add) == 0
        assert len(diff.files_to_update) == 0

    def test_source_file_missing(self, temp_project, monkeypatch):
        """Should handle missing source file in framework."""
        # Mock COMPONENTS to have a file that doesn't exist
        from ldf import update

        orig_components = update.COMPONENTS.copy()
        update.COMPONENTS["templates"]["files"] = ["nonexistent.md"]

        try:
            diff = get_update_diff(temp_project, components=["templates"])
            # Should complete without error
            assert isinstance(diff, UpdateDiff)
        finally:
            update.COMPONENTS = orig_components
