"""LDF configuration utilities."""

from pathlib import Path
from typing import Any

import yaml
from rich.console import Console

console = Console()


def load_config(project_root: Path | None = None) -> dict[str, Any]:
    """Load LDF configuration from .ldf/config.yaml.

    Args:
        project_root: Project root directory (defaults to cwd)

    Returns:
        Configuration dictionary

    Raises:
        FileNotFoundError: If config file doesn't exist
    """
    if project_root is None:
        project_root = Path.cwd()

    config_path = project_root / ".ldf" / "config.yaml"

    if not config_path.exists():
        raise FileNotFoundError(
            f"LDF config not found: {config_path}\nRun 'ldf init' to initialize the project."
        )

    with open(config_path) as f:
        config = yaml.safe_load(f) or {}

    return config


def get_config_value(key: str, default: Any = None, project_root: Path | None = None) -> Any:
    """Get a specific configuration value using dot notation.

    Args:
        key: Configuration key (e.g., "guardrails.preset")
        default: Default value if key not found
        project_root: Project root directory

    Returns:
        Configuration value or default
    """
    try:
        config = load_config(project_root)
    except FileNotFoundError:
        return default

    parts = key.split(".")
    value = config

    for part in parts:
        if isinstance(value, dict) and part in value:
            value = value[part]
        else:
            return default

    return value


def get_specs_dir(project_root: Path | None = None) -> Path:
    """Get the specs directory path.

    Args:
        project_root: Project root directory

    Returns:
        Path to specs directory
    """
    if project_root is None:
        project_root = Path.cwd()

    specs_dir = get_config_value("project.specs_dir", ".ldf/specs", project_root)
    return project_root / str(specs_dir)


def get_answerpacks_dir(project_root: Path | None = None) -> Path:
    """Get the answerpacks directory path.

    Args:
        project_root: Project root directory

    Returns:
        Path to answerpacks directory
    """
    if project_root is None:
        project_root = Path.cwd()

    return project_root / ".ldf" / "answerpacks"


def get_templates_dir(project_root: Path | None = None) -> Path:
    """Get the templates directory path.

    Args:
        project_root: Project root directory

    Returns:
        Path to templates directory
    """
    if project_root is None:
        project_root = Path.cwd()

    return project_root / ".ldf" / "templates"


def get_default_config() -> dict[str, Any]:
    """Get default LDF configuration (v1.1 schema)."""
    from ldf import __version__

    return {
        "_schema_version": "1.1",
        "project": {
            "name": "unnamed",
            "version": "1.0.0",
            "specs_dir": ".ldf/specs",
        },
        "ldf": {
            "version": __version__,
            "preset": "custom",
        },
        "question_packs": {
            "core": ["security", "testing", "api-design", "data-model"],
            "optional": [],
        },
        "mcp_servers": {
            "enabled": True,
            "servers": ["spec_inspector", "coverage_reporter"],
        },
        "defaults": {
            "coverage_target": 80,
            "strict_mode": False,
        },
        "coverage": {
            "default_threshold": 80,
            "critical_threshold": 90,
        },
        "lint": {
            "strict": False,
            "auto_fix": False,
        },
        "hooks": {
            "enabled": False,
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
        },
    }


def save_config(config: dict[str, Any], project_root: Path | None = None) -> None:
    """Save LDF configuration to .ldf/config.yaml.

    Args:
        config: Configuration dictionary
        project_root: Project root directory (defaults to cwd)
    """
    if project_root is None:
        project_root = Path.cwd()

    config_path = project_root / ".ldf" / "config.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path, "w") as f:
        yaml.safe_dump(config, f, default_flow_style=False, sort_keys=False)
