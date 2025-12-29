"""Tests for ldf.hooks and ldf.utils.hooks modules."""

import stat
from pathlib import Path

import pytest

from ldf.hooks import (
    _configure_linters_auto,
    _configure_linters_interactive,
    _print_hook_summary,
    get_hooks_status,
    install_hooks,
    print_hooks_status,
    uninstall_hooks,
)
from ldf.utils.hooks import (
    LDF_HOOK_MARKER,
    detect_project_languages,
    generate_precommit_script,
    get_default_hooks_config,
    get_git_hooks_dir,
    install_hook,
    is_hook_installed,
    uninstall_hook,
    update_config_with_hooks,
)


class TestDetectProjectLanguages:
    """Tests for detect_project_languages function."""

    def test_detect_python_project(self, tmp_path: Path):
        """Test detection of Python project via pyproject.toml."""
        (tmp_path / "pyproject.toml").write_text("[build-system]\n")

        result = detect_project_languages(tmp_path)

        assert result["python"] is True
        assert result["typescript"] is False
        assert result["go"] is False

    def test_detect_python_via_setup_py(self, tmp_path: Path):
        """Test detection of Python project via setup.py."""
        (tmp_path / "setup.py").write_text("from setuptools import setup\n")

        result = detect_project_languages(tmp_path)

        assert result["python"] is True

    def test_detect_python_via_requirements_txt(self, tmp_path: Path):
        """Test detection of Python project via requirements.txt."""
        (tmp_path / "requirements.txt").write_text("flask\n")

        result = detect_project_languages(tmp_path)

        assert result["python"] is True

    def test_detect_typescript_project(self, tmp_path: Path):
        """Test detection of TypeScript project via package.json."""
        (tmp_path / "package.json").write_text('{"name": "test"}\n')

        result = detect_project_languages(tmp_path)

        assert result["typescript"] is True
        assert result["python"] is False
        assert result["go"] is False

    def test_detect_typescript_via_tsconfig(self, tmp_path: Path):
        """Test detection of TypeScript project via tsconfig.json."""
        (tmp_path / "tsconfig.json").write_text('{"compilerOptions": {}}\n')

        result = detect_project_languages(tmp_path)

        assert result["typescript"] is True

    def test_detect_go_project(self, tmp_path: Path):
        """Test detection of Go project via go.mod."""
        (tmp_path / "go.mod").write_text("module test\n")

        result = detect_project_languages(tmp_path)

        assert result["go"] is True
        assert result["python"] is False
        assert result["typescript"] is False

    def test_detect_multi_language_project(self, tmp_path: Path):
        """Test detection of multi-language project."""
        (tmp_path / "pyproject.toml").write_text("[build-system]\n")
        (tmp_path / "package.json").write_text('{"name": "test"}\n')
        (tmp_path / "go.mod").write_text("module test\n")

        result = detect_project_languages(tmp_path)

        assert result["python"] is True
        assert result["typescript"] is True
        assert result["go"] is True

    def test_detect_no_languages(self, tmp_path: Path):
        """Test detection when no language markers present."""
        result = detect_project_languages(tmp_path)

        assert result["python"] is False
        assert result["typescript"] is False
        assert result["go"] is False


class TestGetGitHooksDir:
    """Tests for get_git_hooks_dir function."""

    def test_returns_hooks_dir_in_git_repo(self, tmp_path: Path):
        """Test returns .git/hooks path in a git repository."""
        (tmp_path / ".git").mkdir()

        result = get_git_hooks_dir(tmp_path)

        assert result == tmp_path / ".git" / "hooks"

    def test_returns_none_if_not_git_repo(self, tmp_path: Path):
        """Test returns None if not a git repository."""
        result = get_git_hooks_dir(tmp_path)

        assert result is None


class TestGeneratePrecommitScript:
    """Tests for generate_precommit_script function."""

    def test_generate_minimal_script(self):
        """Test generating script with spec lint only."""
        config = get_default_hooks_config()

        script = generate_precommit_script(config)

        assert LDF_HOOK_MARKER in script
        assert "ldf lint" in script
        assert "ruff" not in script
        assert "eslint" not in script
        assert "golangci-lint" not in script

    def test_generate_script_with_python(self):
        """Test generating script with Python linting enabled."""
        config = get_default_hooks_config()
        config["pre_commit"]["python"]["enabled"] = True

        script = generate_precommit_script(config)

        assert "ruff" in script
        assert LDF_HOOK_MARKER in script

    def test_generate_script_with_typescript(self):
        """Test generating script with TypeScript linting enabled."""
        config = get_default_hooks_config()
        config["pre_commit"]["typescript"]["enabled"] = True

        script = generate_precommit_script(config)

        assert "eslint" in script
        assert LDF_HOOK_MARKER in script

    def test_generate_script_with_go(self):
        """Test generating script with Go linting enabled."""
        config = get_default_hooks_config()
        config["pre_commit"]["go"]["enabled"] = True

        script = generate_precommit_script(config)

        assert "golangci-lint" in script
        assert LDF_HOOK_MARKER in script

    def test_generate_script_with_all_linters(self):
        """Test generating script with all linters enabled."""
        config = get_default_hooks_config()
        config["pre_commit"]["python"]["enabled"] = True
        config["pre_commit"]["typescript"]["enabled"] = True
        config["pre_commit"]["go"]["enabled"] = True

        script = generate_precommit_script(config)

        assert "ruff" in script
        assert "eslint" in script
        assert "golangci-lint" in script

    def test_generate_script_run_on_spec_changes_only(self):
        """Test generating script that only runs on spec changes."""
        config = get_default_hooks_config()
        config["pre_commit"]["run_on_all_commits"] = False

        script = generate_precommit_script(config)

        assert "grep -q" in script  # Checks for spec file detection logic
        assert (
            "RUN_SPEC_LINT=true" not in script.split("\n")[0:10]
        )  # Not unconditionally true at start


class TestInstallHook:
    """Tests for install_hook function."""

    def test_install_creates_hook_file(self, tmp_path: Path):
        """Test that install_hook creates the pre-commit file."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        config = get_default_hooks_config()
        install_hook(config, tmp_path)

        hook_path = git_dir / "hooks" / "pre-commit"
        assert hook_path.exists()

    def test_install_makes_hook_executable(self, tmp_path: Path):
        """Test that install_hook makes the pre-commit file executable."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        config = get_default_hooks_config()
        install_hook(config, tmp_path)

        hook_path = git_dir / "hooks" / "pre-commit"
        mode = hook_path.stat().st_mode
        assert mode & stat.S_IXUSR  # User execute permission

    def test_install_fails_if_not_git_repo(self, tmp_path: Path):
        """Test that install_hook raises error if not a git repository."""
        config = get_default_hooks_config()

        with pytest.raises(RuntimeError, match="Not a git repository"):
            install_hook(config, tmp_path)


class TestUninstallHook:
    """Tests for uninstall_hook function."""

    def test_uninstall_removes_ldf_hook(self, tmp_path: Path):
        """Test that uninstall_hook removes a LDF-managed hook."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir()

        hook_path = hooks_dir / "pre-commit"
        hook_path.write_text(f"{LDF_HOOK_MARKER}\necho test\n")

        result = uninstall_hook(tmp_path)

        assert result is True
        assert not hook_path.exists()

    def test_uninstall_does_not_remove_non_ldf_hook(self, tmp_path: Path):
        """Test that uninstall_hook does not remove non-LDF hooks."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir()

        hook_path = hooks_dir / "pre-commit"
        hook_path.write_text("#!/bin/bash\necho custom hook\n")

        result = uninstall_hook(tmp_path)

        assert result is False
        assert hook_path.exists()

    def test_uninstall_returns_false_if_no_hook(self, tmp_path: Path):
        """Test that uninstall_hook returns False if no hook exists."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        result = uninstall_hook(tmp_path)

        assert result is False


class TestIsHookInstalled:
    """Tests for is_hook_installed function."""

    def test_returns_true_if_ldf_hook_installed(self, tmp_path: Path):
        """Test returns True if LDF hook is installed."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir()
        hook_path = hooks_dir / "pre-commit"
        hook_path.write_text(f"{LDF_HOOK_MARKER}\necho test\n")

        result = is_hook_installed(tmp_path)

        assert result is True

    def test_returns_false_if_non_ldf_hook(self, tmp_path: Path):
        """Test returns False if non-LDF hook is installed."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir()
        hook_path = hooks_dir / "pre-commit"
        hook_path.write_text("#!/bin/bash\necho custom\n")

        result = is_hook_installed(tmp_path)

        assert result is False

    def test_returns_false_if_no_hook(self, tmp_path: Path):
        """Test returns False if no hook exists."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        result = is_hook_installed(tmp_path)

        assert result is False

    def test_returns_false_if_not_git_repo(self, tmp_path: Path):
        """Test returns False if not a git repository."""
        result = is_hook_installed(tmp_path)

        assert result is False


class TestUpdateConfigWithHooks:
    """Tests for update_config_with_hooks function."""

    def test_updates_existing_config(self, temp_project: Path):
        """Test that update_config_with_hooks updates existing config."""
        config = get_default_hooks_config()
        config["pre_commit"]["python"]["enabled"] = True

        update_config_with_hooks(config, temp_project)

        # Read back the config
        import yaml

        config_path = temp_project / ".ldf" / "config.yaml"
        with open(config_path) as f:
            saved_config = yaml.safe_load(f)

        assert "hooks" in saved_config
        assert saved_config["hooks"]["pre_commit"]["python"]["enabled"] is True


class TestGetHooksStatus:
    """Tests for get_hooks_status function."""

    def test_status_in_git_repo_without_hook(self, temp_project: Path):
        """Test status in git repo without hook installed."""
        git_dir = temp_project / ".git"
        git_dir.mkdir()

        status = get_hooks_status(temp_project)

        assert status["is_git_repo"] is True
        assert status["hook_installed"] is False
        assert "config" in status
        assert "detected_languages" in status

    def test_status_with_hook_installed(self, temp_project: Path):
        """Test status with hook installed."""
        git_dir = temp_project / ".git"
        git_dir.mkdir()
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir()
        hook_path = hooks_dir / "pre-commit"
        hook_path.write_text(f"{LDF_HOOK_MARKER}\necho test\n")

        status = get_hooks_status(temp_project)

        assert status["is_git_repo"] is True
        assert status["hook_installed"] is True

    def test_status_not_git_repo(self, tmp_path: Path):
        """Test status when not a git repository."""
        status = get_hooks_status(tmp_path)

        assert status["is_git_repo"] is False
        assert status["hook_installed"] is False


class TestInstallHooksHighLevel:
    """Tests for install_hooks high-level function."""

    def test_install_fails_without_git(self, temp_project: Path, monkeypatch, capsys):
        """Test install_hooks fails gracefully without git."""
        monkeypatch.chdir(temp_project)

        result = install_hooks(
            detect_linters=False, non_interactive=True, project_root=temp_project
        )

        assert result is False

    def test_install_fails_without_ldf(self, tmp_path: Path, monkeypatch, capsys):
        """Test install_hooks fails gracefully without LDF initialization."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        monkeypatch.chdir(tmp_path)

        result = install_hooks(detect_linters=False, non_interactive=True, project_root=tmp_path)

        assert result is False

    def test_install_succeeds_with_git_and_ldf(self, temp_project: Path, monkeypatch):
        """Test install_hooks succeeds with git and LDF."""
        git_dir = temp_project / ".git"
        git_dir.mkdir()
        monkeypatch.chdir(temp_project)

        result = install_hooks(
            detect_linters=False, non_interactive=True, project_root=temp_project
        )

        assert result is True
        assert is_hook_installed(temp_project)


class TestUninstallHooksHighLevel:
    """Tests for uninstall_hooks high-level function."""

    def test_uninstall_removes_installed_hook(self, temp_project: Path, monkeypatch):
        """Test uninstall_hooks removes an installed hook."""
        git_dir = temp_project / ".git"
        git_dir.mkdir()
        monkeypatch.chdir(temp_project)

        # First install
        install_hooks(detect_linters=False, non_interactive=True, project_root=temp_project)
        assert is_hook_installed(temp_project)

        # Then uninstall
        result = uninstall_hooks(temp_project)

        assert result is True
        assert not is_hook_installed(temp_project)

    def test_uninstall_returns_false_if_not_installed(self, temp_project: Path, monkeypatch):
        """Test uninstall_hooks returns False if no hook installed."""
        git_dir = temp_project / ".git"
        git_dir.mkdir()
        monkeypatch.chdir(temp_project)

        result = uninstall_hooks(temp_project)

        assert result is False


class TestDefaultHooksConfig:
    """Tests for get_default_hooks_config function."""

    def test_default_config_structure(self):
        """Test default hooks config has expected structure."""
        config = get_default_hooks_config()

        assert "enabled" in config
        assert "pre_commit" in config
        assert "run_on_all_commits" in config["pre_commit"]
        assert "strict" in config["pre_commit"]
        assert "spec_lint" in config["pre_commit"]
        assert "python" in config["pre_commit"]
        assert "typescript" in config["pre_commit"]
        assert "go" in config["pre_commit"]

    def test_default_config_values(self):
        """Test default hooks config has expected default values."""
        config = get_default_hooks_config()

        assert config["enabled"] is True
        assert config["pre_commit"]["run_on_all_commits"] is True
        assert config["pre_commit"]["strict"] is False
        assert config["pre_commit"]["spec_lint"] is True
        assert config["pre_commit"]["python"]["enabled"] is False
        assert config["pre_commit"]["typescript"]["enabled"] is False
        assert config["pre_commit"]["go"]["enabled"] is False


class TestConfigureLintersInteractive:
    """Tests for _configure_linters_interactive function."""

    def test_interactive_python_enabled(self, monkeypatch, capsys):
        """Test enabling Python linting interactively."""
        config = get_default_hooks_config()
        languages = {"python": True, "typescript": False, "go": False}

        # Mock click.confirm to return True for Python
        confirm_calls = []

        def mock_confirm(prompt, default=False):
            confirm_calls.append(prompt)
            return True

        monkeypatch.setattr("click.confirm", mock_confirm)

        result = _configure_linters_interactive(config, languages)

        assert result["pre_commit"]["python"]["enabled"] is True
        assert result["pre_commit"]["python"]["tools"] == ["ruff"]
        assert len(confirm_calls) == 1

    def test_interactive_python_disabled(self, monkeypatch, capsys):
        """Test disabling Python linting interactively."""
        config = get_default_hooks_config()
        languages = {"python": True, "typescript": False, "go": False}

        monkeypatch.setattr("click.confirm", lambda *a, **kw: False)

        result = _configure_linters_interactive(config, languages)

        assert result["pre_commit"]["python"].get("enabled", False) is False

    def test_interactive_typescript_enabled(self, monkeypatch, capsys):
        """Test enabling TypeScript linting interactively."""
        config = get_default_hooks_config()
        languages = {"python": False, "typescript": True, "go": False}

        monkeypatch.setattr("click.confirm", lambda *a, **kw: True)

        result = _configure_linters_interactive(config, languages)

        assert result["pre_commit"]["typescript"]["enabled"] is True
        assert result["pre_commit"]["typescript"]["tools"] == ["eslint"]

    def test_interactive_go_enabled(self, monkeypatch, capsys):
        """Test enabling Go linting interactively."""
        config = get_default_hooks_config()
        languages = {"python": False, "typescript": False, "go": True}

        monkeypatch.setattr("click.confirm", lambda *a, **kw: True)

        result = _configure_linters_interactive(config, languages)

        assert result["pre_commit"]["go"]["enabled"] is True
        assert result["pre_commit"]["go"]["tools"] == ["golangci-lint"]

    def test_interactive_multi_linter_warning(self, monkeypatch, capsys):
        """Test warning when multiple linters are enabled."""
        config = get_default_hooks_config()
        languages = {"python": True, "typescript": True, "go": True}

        # Enable all linters
        monkeypatch.setattr("click.confirm", lambda *a, **kw: True)

        result = _configure_linters_interactive(config, languages)

        captured = capsys.readouterr()
        assert "Multiple linters enabled" in captured.out
        assert result["pre_commit"]["python"]["enabled"] is True
        assert result["pre_commit"]["typescript"]["enabled"] is True
        assert result["pre_commit"]["go"]["enabled"] is True

    def test_interactive_no_languages_detected(self, monkeypatch, capsys):
        """Test when no languages are detected."""
        config = get_default_hooks_config()
        languages = {"python": False, "typescript": False, "go": False}

        _result = _configure_linters_interactive(config, languages)

        captured = capsys.readouterr()
        assert "Python: not detected" in captured.out
        assert "TypeScript/JS: not detected" in captured.out
        assert "Go: not detected" in captured.out

    def test_interactive_typescript_disabled(self, monkeypatch, capsys):
        """Test disabling TypeScript linting interactively."""
        config = get_default_hooks_config()
        languages = {"python": False, "typescript": True, "go": False}

        monkeypatch.setattr("click.confirm", lambda *a, **kw: False)

        result = _configure_linters_interactive(config, languages)

        captured = capsys.readouterr()
        assert "TypeScript/JS linting disabled" in captured.out
        assert result["pre_commit"]["typescript"].get("enabled", False) is False

    def test_interactive_go_disabled(self, monkeypatch, capsys):
        """Test disabling Go linting interactively."""
        config = get_default_hooks_config()
        languages = {"python": False, "typescript": False, "go": True}

        monkeypatch.setattr("click.confirm", lambda *a, **kw: False)

        result = _configure_linters_interactive(config, languages)

        captured = capsys.readouterr()
        assert "Go linting disabled" in captured.out
        assert result["pre_commit"]["go"].get("enabled", False) is False


class TestConfigureLintersAuto:
    """Tests for _configure_linters_auto function."""

    def test_auto_configure_python(self):
        """Test auto-configuration for Python project."""
        config = get_default_hooks_config()
        languages = {"python": True, "typescript": False, "go": False}

        result = _configure_linters_auto(config, languages)

        assert result["pre_commit"]["python"]["enabled"] is True
        assert result["pre_commit"]["python"]["tools"] == ["ruff"]
        assert result["pre_commit"]["typescript"].get("enabled", False) is False
        assert result["pre_commit"]["go"].get("enabled", False) is False

    def test_auto_configure_typescript(self):
        """Test auto-configuration for TypeScript project."""
        config = get_default_hooks_config()
        languages = {"python": False, "typescript": True, "go": False}

        result = _configure_linters_auto(config, languages)

        assert result["pre_commit"]["typescript"]["enabled"] is True
        assert result["pre_commit"]["typescript"]["tools"] == ["eslint"]

    def test_auto_configure_go(self):
        """Test auto-configuration for Go project."""
        config = get_default_hooks_config()
        languages = {"python": False, "typescript": False, "go": True}

        result = _configure_linters_auto(config, languages)

        assert result["pre_commit"]["go"]["enabled"] is True
        assert result["pre_commit"]["go"]["tools"] == ["golangci-lint"]

    def test_auto_configure_all_languages(self):
        """Test auto-configuration for multi-language project."""
        config = get_default_hooks_config()
        languages = {"python": True, "typescript": True, "go": True}

        result = _configure_linters_auto(config, languages)

        assert result["pre_commit"]["python"]["enabled"] is True
        assert result["pre_commit"]["typescript"]["enabled"] is True
        assert result["pre_commit"]["go"]["enabled"] is True

    def test_auto_configure_no_languages(self):
        """Test auto-configuration when no languages detected."""
        config = get_default_hooks_config()
        languages = {"python": False, "typescript": False, "go": False}

        result = _configure_linters_auto(config, languages)

        assert result["pre_commit"]["python"].get("enabled", False) is False
        assert result["pre_commit"]["typescript"].get("enabled", False) is False
        assert result["pre_commit"]["go"].get("enabled", False) is False


class TestPrintHookSummary:
    """Tests for _print_hook_summary function."""

    def test_summary_spec_lint_only(self, capsys):
        """Test summary with only spec linting enabled."""
        config = get_default_hooks_config()

        _print_hook_summary(config)

        captured = capsys.readouterr()
        assert "LDF spec linting" in captured.out
        assert "Python (ruff)" not in captured.out
        assert "TypeScript/JS (eslint)" not in captured.out
        assert "Go (golangci-lint)" not in captured.out

    def test_summary_with_python(self, capsys):
        """Test summary with Python linting enabled."""
        config = get_default_hooks_config()
        config["pre_commit"]["python"]["enabled"] = True

        _print_hook_summary(config)

        captured = capsys.readouterr()
        assert "LDF spec linting" in captured.out
        assert "Python (ruff)" in captured.out

    def test_summary_with_typescript(self, capsys):
        """Test summary with TypeScript linting enabled."""
        config = get_default_hooks_config()
        config["pre_commit"]["typescript"]["enabled"] = True

        _print_hook_summary(config)

        captured = capsys.readouterr()
        assert "TypeScript/JS (eslint)" in captured.out

    def test_summary_with_go(self, capsys):
        """Test summary with Go linting enabled."""
        config = get_default_hooks_config()
        config["pre_commit"]["go"]["enabled"] = True

        _print_hook_summary(config)

        captured = capsys.readouterr()
        assert "Go (golangci-lint)" in captured.out

    def test_summary_with_all_linters(self, capsys):
        """Test summary with all linters enabled."""
        config = get_default_hooks_config()
        config["pre_commit"]["python"]["enabled"] = True
        config["pre_commit"]["typescript"]["enabled"] = True
        config["pre_commit"]["go"]["enabled"] = True

        _print_hook_summary(config)

        captured = capsys.readouterr()
        assert "LDF spec linting" in captured.out
        assert "Python (ruff)" in captured.out
        assert "TypeScript/JS (eslint)" in captured.out
        assert "Go (golangci-lint)" in captured.out


class TestPrintHooksStatus:
    """Tests for print_hooks_status function."""

    def test_status_not_git_repo(self, tmp_path: Path, capsys):
        """Test status display when not a git repository."""
        print_hooks_status(tmp_path)

        captured = capsys.readouterr()
        assert "Not a git repository" in captured.out

    def test_status_hook_not_installed(self, temp_project: Path, capsys):
        """Test status display when hook is not installed."""
        git_dir = temp_project / ".git"
        git_dir.mkdir()

        print_hooks_status(temp_project)

        captured = capsys.readouterr()
        assert "Hook not installed" in captured.out
        assert "ldf hooks install" in captured.out

    def test_status_hook_installed(self, temp_project: Path, capsys):
        """Test status display when hook is installed."""
        git_dir = temp_project / ".git"
        git_dir.mkdir()
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir()
        hook_path = hooks_dir / "pre-commit"
        hook_path.write_text(f"{LDF_HOOK_MARKER}\necho test\n")

        print_hooks_status(temp_project)

        captured = capsys.readouterr()
        assert "Hook installed" in captured.out

    def test_status_shows_configuration(self, temp_project: Path, capsys):
        """Test status display shows configuration options."""
        git_dir = temp_project / ".git"
        git_dir.mkdir()

        print_hooks_status(temp_project)

        captured = capsys.readouterr()
        assert "Configuration:" in captured.out
        assert "Run on all commits:" in captured.out
        assert "Strict mode:" in captured.out
        assert "Spec linting:" in captured.out

    def test_status_shows_language_linters(self, temp_project: Path, capsys):
        """Test status display shows language linters."""
        git_dir = temp_project / ".git"
        git_dir.mkdir()

        print_hooks_status(temp_project)

        captured = capsys.readouterr()
        assert "Language Linters:" in captured.out
        assert "Python:" in captured.out
        assert "Typescript:" in captured.out
        assert "Go:" in captured.out

    def test_status_shows_detected_languages(self, temp_project: Path, capsys):
        """Test status display shows detected languages."""
        git_dir = temp_project / ".git"
        git_dir.mkdir()
        # Add Python project marker
        (temp_project / "pyproject.toml").write_text("[build-system]\n")

        print_hooks_status(temp_project)

        captured = capsys.readouterr()
        assert "(detected)" in captured.out


class TestInstallHooksReinstall:
    """Tests for install_hooks reinstall confirmation."""

    def test_install_already_exists_reinstall_yes(self, temp_project: Path, monkeypatch):
        """Test reinstalling when user confirms."""
        git_dir = temp_project / ".git"
        git_dir.mkdir()
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir()
        hook_path = hooks_dir / "pre-commit"
        hook_path.write_text(f"{LDF_HOOK_MARKER}\necho old hook\n")

        # Mock click.confirm to return True
        monkeypatch.setattr("click.confirm", lambda *a, **kw: True)

        result = install_hooks(
            detect_linters=False, non_interactive=False, project_root=temp_project
        )

        assert result is True
        assert is_hook_installed(temp_project)

    def test_install_already_exists_reinstall_no(self, temp_project: Path, monkeypatch, capsys):
        """Test cancelling reinstall when user declines."""
        git_dir = temp_project / ".git"
        git_dir.mkdir()
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir()
        hook_path = hooks_dir / "pre-commit"
        hook_path.write_text(f"{LDF_HOOK_MARKER}\necho old hook\n")

        # Mock click.confirm to return False
        monkeypatch.setattr("click.confirm", lambda *a, **kw: False)

        result = install_hooks(
            detect_linters=False, non_interactive=False, project_root=temp_project
        )

        assert result is False
        captured = capsys.readouterr()
        assert "Installation cancelled" in captured.out

    def test_install_already_exists_non_interactive(self, temp_project: Path, capsys):
        """Test reinstalling in non-interactive mode."""
        git_dir = temp_project / ".git"
        git_dir.mkdir()
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir()
        hook_path = hooks_dir / "pre-commit"
        hook_path.write_text(f"{LDF_HOOK_MARKER}\necho old hook\n")

        result = install_hooks(
            detect_linters=False, non_interactive=True, project_root=temp_project
        )

        assert result is True
        captured = capsys.readouterr()
        assert "already installed, reinstalling" in captured.out


class TestInstallHooksWithDetection:
    """Tests for install_hooks with linter detection."""

    def test_install_with_auto_detect_python(self, temp_project: Path, monkeypatch):
        """Test install with auto-detection for Python project."""
        git_dir = temp_project / ".git"
        git_dir.mkdir()
        (temp_project / "pyproject.toml").write_text("[build-system]\n")

        result = install_hooks(detect_linters=True, non_interactive=True, project_root=temp_project)

        assert result is True
        # Verify Python linting was auto-enabled
        import yaml

        config_path = temp_project / ".ldf" / "config.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)
        assert config["hooks"]["pre_commit"]["python"]["enabled"] is True

    def test_install_with_interactive_detection(self, temp_project: Path, monkeypatch):
        """Test install with interactive detection."""
        git_dir = temp_project / ".git"
        git_dir.mkdir()
        (temp_project / "pyproject.toml").write_text("[build-system]\n")

        # Enable Python linting when asked
        monkeypatch.setattr("click.confirm", lambda *a, **kw: True)

        result = install_hooks(
            detect_linters=True, non_interactive=False, project_root=temp_project
        )

        assert result is True

    def test_install_without_detection(self, temp_project: Path, monkeypatch):
        """Test install without linter detection."""
        git_dir = temp_project / ".git"
        git_dir.mkdir()
        (temp_project / "pyproject.toml").write_text("[build-system]\n")

        result = install_hooks(
            detect_linters=False, non_interactive=True, project_root=temp_project
        )

        assert result is True
        # Verify Python linting was NOT auto-enabled
        import yaml

        config_path = temp_project / ".ldf" / "config.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)
        assert config["hooks"]["pre_commit"]["python"]["enabled"] is False


class TestGetHooksStatusDefaultRoot:
    """Tests for get_hooks_status with default project root."""

    def test_status_uses_cwd_by_default(self, temp_project: Path, monkeypatch):
        """Test that get_hooks_status uses cwd when no root provided."""
        git_dir = temp_project / ".git"
        git_dir.mkdir()
        monkeypatch.chdir(temp_project)

        status = get_hooks_status()

        assert status["is_git_repo"] is True


class TestUninstallHooksMessages:
    """Tests for uninstall_hooks console messages."""

    def test_uninstall_hook_not_installed_message(self, temp_project: Path, capsys):
        """Test message when no hook is installed."""
        git_dir = temp_project / ".git"
        git_dir.mkdir()

        result = uninstall_hooks(temp_project)

        assert result is False
        captured = capsys.readouterr()
        assert "No LDF pre-commit hook is installed" in captured.out

    def test_uninstall_success_message(self, temp_project: Path, capsys):
        """Test success message when hook is uninstalled."""
        git_dir = temp_project / ".git"
        git_dir.mkdir()
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir()
        hook_path = hooks_dir / "pre-commit"
        hook_path.write_text(f"{LDF_HOOK_MARKER}\necho test\n")

        result = uninstall_hooks(temp_project)

        assert result is True
        captured = capsys.readouterr()
        assert "uninstalled successfully" in captured.out

    def test_uninstall_failure_message(self, temp_project: Path, monkeypatch, capsys):
        """Test message when uninstall fails."""
        git_dir = temp_project / ".git"
        git_dir.mkdir()
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir()
        hook_path = hooks_dir / "pre-commit"
        hook_path.write_text(f"{LDF_HOOK_MARKER}\necho test\n")

        # Mock uninstall_hook to return False
        monkeypatch.setattr("ldf.hooks.uninstall_hook", lambda *a, **kw: False)

        result = uninstall_hooks(temp_project)

        assert result is False
        captured = capsys.readouterr()
        assert "Failed to uninstall hook" in captured.out


class TestInstallHooksDefaultRoot:
    """Tests for install_hooks with default project root."""

    def test_install_uses_cwd_by_default(self, temp_project: Path, monkeypatch):
        """Test that install_hooks uses cwd when no root provided."""
        git_dir = temp_project / ".git"
        git_dir.mkdir()
        monkeypatch.chdir(temp_project)

        result = install_hooks(detect_linters=False, non_interactive=True)

        assert result is True
        assert is_hook_installed(temp_project)


class TestUninstallHooksDefaultRoot:
    """Tests for uninstall_hooks with default project root."""

    def test_uninstall_uses_cwd_by_default(self, temp_project: Path, monkeypatch):
        """Test that uninstall_hooks uses cwd when no root provided."""
        git_dir = temp_project / ".git"
        git_dir.mkdir()
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir()
        hook_path = hooks_dir / "pre-commit"
        hook_path.write_text(f"{LDF_HOOK_MARKER}\necho test\n")
        monkeypatch.chdir(temp_project)

        result = uninstall_hooks()

        assert result is True
        assert not is_hook_installed(temp_project)


class TestInstallHooksRuntimeError:
    """Tests for install_hooks RuntimeError handling."""

    def test_install_handles_runtime_error(self, temp_project: Path, monkeypatch, capsys):
        """Test that install_hooks handles RuntimeError from install_hook."""
        git_dir = temp_project / ".git"
        git_dir.mkdir()

        # Mock install_hook to raise RuntimeError
        def raise_runtime_error(*args, **kwargs):
            raise RuntimeError("Test error message")

        monkeypatch.setattr("ldf.hooks.install_hook", raise_runtime_error)

        result = install_hooks(
            detect_linters=False, non_interactive=True, project_root=temp_project
        )

        assert result is False
        captured = capsys.readouterr()
        assert "Test error message" in captured.out


class TestUtilsHooksDefaultPaths:
    """Tests for utils/hooks functions using default paths (cwd)."""

    def test_detect_project_languages_uses_cwd(self, tmp_path: Path, monkeypatch):
        """Test detect_project_languages uses cwd when no root provided."""
        (tmp_path / "pyproject.toml").write_text("[build-system]\n")
        monkeypatch.chdir(tmp_path)

        result = detect_project_languages()

        assert result["python"] is True

    def test_get_git_hooks_dir_uses_cwd(self, tmp_path: Path, monkeypatch):
        """Test get_git_hooks_dir uses cwd when no root provided."""
        (tmp_path / ".git").mkdir()
        monkeypatch.chdir(tmp_path)

        result = get_git_hooks_dir()

        assert result == tmp_path / ".git" / "hooks"

    def test_update_config_with_hooks_uses_cwd(self, temp_project: Path, monkeypatch):
        """Test update_config_with_hooks uses cwd when no root provided."""
        monkeypatch.chdir(temp_project)
        config = get_default_hooks_config()

        update_config_with_hooks(config)

        # Verify config was written
        import yaml

        config_path = temp_project / ".ldf" / "config.yaml"
        with open(config_path) as f:
            saved = yaml.safe_load(f)
        assert "hooks" in saved

    def test_update_config_with_hooks_creates_empty_config(self, tmp_path: Path, monkeypatch):
        """Test update_config_with_hooks works when no config exists."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()
        monkeypatch.chdir(tmp_path)
        config = get_default_hooks_config()

        update_config_with_hooks(config, tmp_path)

        import yaml

        config_path = ldf_dir / "config.yaml"
        with open(config_path) as f:
            saved = yaml.safe_load(f)
        assert "hooks" in saved


class TestUninstallHookNotGitRepo:
    """Tests for uninstall_hook when not a git repository."""

    def test_uninstall_returns_false_not_git_repo(self, tmp_path: Path):
        """Test uninstall_hook returns False when not in a git repo."""
        result = uninstall_hook(tmp_path)

        assert result is False


class TestGeneratePrecommitScriptMissingTemplate:
    """Tests for generate_precommit_script when template is missing."""

    def test_raises_runtime_error_when_template_missing(self, monkeypatch):
        """Test RuntimeError when pre-commit template is not found."""
        from ldf.utils import hooks

        # Mock the template path to not exist
        fake_path = Path("/nonexistent/template.j2")
        monkeypatch.setattr(hooks, "PRE_COMMIT_TEMPLATE_PATH", fake_path)

        config = get_default_hooks_config()

        with pytest.raises(RuntimeError, match="Pre-commit template not found"):
            generate_precommit_script(config)
