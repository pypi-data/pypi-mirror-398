"""LDF guardrail loading utilities."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from ldf.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class Guardrail:
    """Represents a single guardrail definition."""

    id: int
    name: str
    description: str
    severity: str  # critical, high, medium, low
    enabled: bool = True
    checklist: list[str] = field(default_factory=list)
    config: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Guardrail":
        """Create a Guardrail from a dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            severity=data.get("severity", "medium"),
            enabled=data.get("enabled", True),
            checklist=data.get("checklist", []),
            config=data.get("config", {}),
        )


# Framework paths
FRAMEWORK_DIR = Path(__file__).parent.parent / "_framework"
CORE_GUARDRAILS_PATH = FRAMEWORK_DIR / "guardrails" / "core.yaml"
PRESETS_DIR = FRAMEWORK_DIR / "guardrails" / "presets"


def load_core_guardrails() -> list[Guardrail]:
    """Load the 8 core guardrails from framework/guardrails/core.yaml.

    Returns:
        List of core Guardrail objects
    """
    if not CORE_GUARDRAILS_PATH.exists():
        logger.warning(
            f"Core guardrails file not found at {CORE_GUARDRAILS_PATH}. "
            "Using built-in defaults. This may indicate a broken installation."
        )
        return _get_default_core_guardrails()

    with open(CORE_GUARDRAILS_PATH) as f:
        data = yaml.safe_load(f)

    guardrails = []
    for item in data.get("guardrails", []):
        guardrails.append(Guardrail.from_dict(item))

    return guardrails


def load_preset_guardrails(preset: str) -> list[Guardrail]:
    """Load guardrails from a preset file.

    Args:
        preset: Preset name (saas, fintech, healthcare, api-only)

    Returns:
        List of preset Guardrail objects (empty if preset not found)
    """
    if preset == "custom":
        return []

    preset_path = PRESETS_DIR / f"{preset}.yaml"
    if not preset_path.exists():
        logger.warning(
            f"Guardrail preset '{preset}' not found at {preset_path}. "
            "Continuing with core guardrails only."
        )
        return []

    with open(preset_path) as f:
        data = yaml.safe_load(f)

    guardrails = []
    for item in data.get("guardrails", []):
        guardrails.append(Guardrail.from_dict(item))

    return guardrails


def load_guardrails(project_root: Path | None = None) -> list[Guardrail]:
    """Load all active guardrails for a project.

    Combines:
    1. Core guardrails (always loaded)
    2. Preset guardrails (if configured)
    3. Custom guardrails (if defined)

    Applies overrides and disabled list from project config.

    Args:
        project_root: Project root directory

    Returns:
        List of all active Guardrail objects
    """
    if project_root is None:
        project_root = Path.cwd()

    # Load core guardrails
    guardrails = load_core_guardrails()

    # Load project guardrails config
    project_guardrails_path = project_root / ".ldf" / "guardrails.yaml"
    if project_guardrails_path.exists():
        with open(project_guardrails_path) as f:
            project_config = yaml.safe_load(f) or {}

        # Load preset guardrails
        preset = project_config.get("preset")
        if preset and preset != "custom":
            preset_guardrails = load_preset_guardrails(preset)
            guardrails.extend(preset_guardrails)

        # Apply overrides
        overrides = project_config.get("overrides", {})
        for guardrail in guardrails:
            if str(guardrail.id) in overrides:
                override = overrides[str(guardrail.id)]
                if "enabled" in override:
                    guardrail.enabled = override["enabled"]
                if "config" in override:
                    guardrail.config.update(override["config"])

        # Apply disabled list
        disabled = project_config.get("disabled", [])
        for guardrail in guardrails:
            if guardrail.id in disabled or guardrail.name in disabled:
                guardrail.enabled = False

        # Add custom guardrails
        custom = project_config.get("custom", [])
        for item in custom:
            guardrails.append(Guardrail.from_dict(item))

        # Apply selected_ids filter (from ldf init --custom)
        selected_ids = project_config.get("selected_ids")
        if selected_ids:
            guardrails_by_id = {g.id: g for g in guardrails}
            guardrails = [guardrails_by_id[gid] for gid in selected_ids if gid in guardrails_by_id]
    else:
        logger.info(
            f"No project guardrails config at {project_guardrails_path}. "
            "Using core guardrails only."
        )

    return guardrails


def get_active_guardrails(project_root: Path | None = None) -> list[Guardrail]:
    """Get only enabled guardrails.

    Args:
        project_root: Project root directory

    Returns:
        List of enabled Guardrail objects
    """
    all_guardrails = load_guardrails(project_root)
    return [g for g in all_guardrails if g.enabled]


def get_guardrail_by_id(guardrail_id: int, project_root: Path | None = None) -> Guardrail | None:
    """Get a specific guardrail by ID.

    Args:
        guardrail_id: Guardrail ID number
        project_root: Project root directory

    Returns:
        Guardrail object or None if not found
    """
    for guardrail in load_guardrails(project_root):
        if guardrail.id == guardrail_id:
            return guardrail
    return None


def get_guardrail_by_name(name: str, project_root: Path | None = None) -> Guardrail | None:
    """Get a specific guardrail by name.

    Args:
        name: Guardrail name
        project_root: Project root directory

    Returns:
        Guardrail object or None if not found
    """
    for guardrail in load_guardrails(project_root):
        if guardrail.name.lower() == name.lower():
            return guardrail
    return None


def _get_default_core_guardrails() -> list[Guardrail]:
    """Get default core guardrails if YAML file not found."""
    return [
        Guardrail(
            id=1,
            name="Testing Coverage",
            description="Minimum test coverage thresholds",
            severity="critical",
            checklist=[
                "Unit tests for business logic",
                "Integration tests for APIs",
                "Coverage meets threshold",
            ],
            config={"default_threshold": 80, "critical_paths_threshold": 90},
        ),
        Guardrail(
            id=2,
            name="Security Basics",
            description="OWASP Top 10 prevention",
            severity="critical",
            checklist=[
                "Input validation on all boundaries",
                "SQL injection prevention (parameterized queries)",
                "XSS prevention (output encoding)",
                "Auth checks on protected endpoints",
            ],
        ),
        Guardrail(
            id=3,
            name="Error Handling",
            description="Consistent error responses, no swallowed exceptions",
            severity="high",
            checklist=[
                "Consistent error response format",
                "No swallowed exceptions",
                "Proper HTTP status codes",
            ],
        ),
        Guardrail(
            id=4,
            name="Logging & Observability",
            description="Structured logging, correlation IDs",
            severity="high",
            checklist=[
                "Structured JSON logging",
                "Correlation IDs on requests",
                "No sensitive data in logs",
            ],
        ),
        Guardrail(
            id=5,
            name="API Design",
            description="Versioning, pagination, error format",
            severity="high",
            checklist=[
                "API versioning (/v1/)",
                "Pagination for list endpoints",
                "Consistent error format",
            ],
        ),
        Guardrail(
            id=6,
            name="Data Validation",
            description="Input validation at boundaries",
            severity="critical",
            checklist=[
                "Schema validation for requests",
                "Type coercion handled",
                "Boundary conditions tested",
            ],
        ),
        Guardrail(
            id=7,
            name="Database Migrations",
            description="Reversible, separate from backfills",
            severity="high",
            checklist=[
                "Migration is reversible",
                "Backfills separate from schema changes",
                "No data loss on rollback",
            ],
        ),
        Guardrail(
            id=8,
            name="Documentation",
            description="API docs, README, inline comments for complex logic",
            severity="medium",
            checklist=[
                "API endpoints documented",
                "Complex logic has comments",
                "README updated if needed",
            ],
        ),
    ]
