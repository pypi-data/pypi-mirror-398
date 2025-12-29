"""LDF Git hook utilities."""

import stat
from pathlib import Path
from typing import Any, cast

from jinja2 import Template

from ldf.utils.config import load_config, save_config

# Marker to identify LDF-managed hooks
LDF_HOOK_MARKER = "# LDF Pre-Commit Hook - Auto-generated"

# Framework paths (inside ldf package)
FRAMEWORK_DIR = Path(__file__).parent.parent / "_framework"
PRE_COMMIT_TEMPLATE_PATH = FRAMEWORK_DIR / "hooks" / "pre-commit.sh.j2"


def get_default_hooks_config() -> dict[str, Any]:
    """Get default hooks configuration."""
    return {
        "enabled": True,
        "pre_commit": {
            "run_on_all_commits": True,
            "strict": False,
            "spec_lint": True,
            "python": {
                "enabled": False,
                "tools": ["ruff"],
            },
            "typescript": {
                "enabled": False,
                "tools": ["eslint"],
            },
            "go": {
                "enabled": False,
                "tools": ["golangci-lint"],
            },
        },
    }


def detect_project_languages(project_root: Path | None = None) -> dict[str, bool]:
    """Detect which programming languages are used in the project.

    Scans for common project files to determine language usage.

    Args:
        project_root: Project root directory (defaults to cwd)

    Returns:
        Dictionary with language keys and boolean values indicating presence
    """
    if project_root is None:
        project_root = Path.cwd()

    return {
        "python": (project_root / "pyproject.toml").exists()
        or (project_root / "setup.py").exists()
        or (project_root / "requirements.txt").exists(),
        "typescript": (project_root / "package.json").exists()
        or (project_root / "tsconfig.json").exists(),
        "go": (project_root / "go.mod").exists(),
    }


def get_hook_config(project_root: Path | None = None) -> dict[str, Any]:
    """Load hook configuration from project config.

    Args:
        project_root: Project root directory

    Returns:
        Hook configuration dictionary (or defaults if not configured)
    """
    try:
        config = load_config(project_root)
        return cast(dict[str, Any], config.get("hooks", get_default_hooks_config()))
    except FileNotFoundError:
        return get_default_hooks_config()


def get_git_hooks_dir(project_root: Path | None = None) -> Path | None:
    """Get the .git/hooks directory path.

    Args:
        project_root: Project root directory

    Returns:
        Path to .git/hooks or None if not a git repo
    """
    if project_root is None:
        project_root = Path.cwd()

    git_dir = project_root / ".git"
    if not git_dir.exists():
        return None

    hooks_dir = git_dir / "hooks"
    return hooks_dir


def is_hook_installed(project_root: Path | None = None) -> bool:
    """Check if LDF pre-commit hook is installed.

    Args:
        project_root: Project root directory

    Returns:
        True if LDF hook is installed, False otherwise
    """
    hooks_dir = get_git_hooks_dir(project_root)
    if hooks_dir is None:
        return False

    hook_path = hooks_dir / "pre-commit"
    if not hook_path.exists():
        return False

    # Check for LDF marker
    content = hook_path.read_text()
    return LDF_HOOK_MARKER in content


def generate_precommit_script(hook_config: dict[str, Any]) -> str:
    """Generate the pre-commit hook script from configuration.

    Args:
        hook_config: Hook configuration dictionary

    Returns:
        Generated bash script content
    """
    pre_commit_config = hook_config.get("pre_commit", {})

    # Load template from file
    if not PRE_COMMIT_TEMPLATE_PATH.exists():
        raise RuntimeError(
            f"Pre-commit template not found at {PRE_COMMIT_TEMPLATE_PATH}. "
            "This may indicate a broken LDF installation."
        )

    template_content = PRE_COMMIT_TEMPLATE_PATH.read_text()
    template = Template(template_content)

    return template.render(
        run_on_all_commits=pre_commit_config.get("run_on_all_commits", True),
        strict=pre_commit_config.get("strict", False),
        spec_lint=pre_commit_config.get("spec_lint", True),
        python_enabled=pre_commit_config.get("python", {}).get("enabled", False),
        python_tools=pre_commit_config.get("python", {}).get("tools", ["ruff"]),
        typescript_enabled=pre_commit_config.get("typescript", {}).get("enabled", False),
        typescript_tools=pre_commit_config.get("typescript", {}).get("tools", ["eslint"]),
        go_enabled=pre_commit_config.get("go", {}).get("enabled", False),
        go_tools=pre_commit_config.get("go", {}).get("tools", ["golangci-lint"]),
    )


def install_hook(hook_config: dict[str, Any], project_root: Path | None = None) -> bool:
    """Install the pre-commit hook.

    Args:
        hook_config: Hook configuration dictionary
        project_root: Project root directory

    Returns:
        True if successful, False otherwise

    Raises:
        RuntimeError: If not a git repository
    """
    hooks_dir = get_git_hooks_dir(project_root)
    if hooks_dir is None:
        raise RuntimeError("Not a git repository. Initialize git first with 'git init'.")

    # Create hooks directory if it doesn't exist
    hooks_dir.mkdir(parents=True, exist_ok=True)

    # Generate and write the hook script
    script_content = generate_precommit_script(hook_config)
    hook_path = hooks_dir / "pre-commit"

    hook_path.write_text(script_content)

    # Make executable
    current_mode = hook_path.stat().st_mode
    hook_path.chmod(current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    return True


def uninstall_hook(project_root: Path | None = None) -> bool:
    """Remove the LDF pre-commit hook.

    Args:
        project_root: Project root directory

    Returns:
        True if hook was removed, False if it wasn't installed
    """
    hooks_dir = get_git_hooks_dir(project_root)
    if hooks_dir is None:
        return False

    hook_path = hooks_dir / "pre-commit"
    if not hook_path.exists():
        return False

    # Only remove if it's a LDF hook
    content = hook_path.read_text()
    if LDF_HOOK_MARKER not in content:
        return False

    hook_path.unlink()
    return True


def update_config_with_hooks(hook_config: dict[str, Any], project_root: Path | None = None) -> None:
    """Update the project config with hook settings.

    Args:
        hook_config: Hook configuration to save
        project_root: Project root directory
    """
    if project_root is None:
        project_root = Path.cwd()

    try:
        config = load_config(project_root)
    except FileNotFoundError:
        config = {}

    config["hooks"] = hook_config
    save_config(config, project_root)
