"""
Guardrail Tracker Module

Tracks guardrail coverage across specs and calculates compliance metrics.
Works with configurable guardrails from .ldf/guardrails.yaml.
"""

import re
from pathlib import Path
from typing import Any

from spec_parser import SpecParser

# Import the central guardrail loader for parity with CLI
try:
    from ldf.utils.guardrail_loader import Guardrail, get_active_guardrails

    HAS_GUARDRAIL_LOADER = True
except ImportError:
    HAS_GUARDRAIL_LOADER = False


def load_active_guardrails(project_root: Path) -> list[dict[str, Any]]:
    """Load active guardrails using the central guardrail_loader.

    This ensures parity with CLI lint behavior, respecting:
    - Core guardrails
    - Preset guardrails
    - Custom guardrails
    - Overrides
    - Disabled list
    """
    if HAS_GUARDRAIL_LOADER:
        # Use the central loader for consistent behavior with CLI
        guardrails: list[Guardrail] = get_active_guardrails(project_root)
        # Convert Guardrail dataclass to dict for compatibility
        return [
            {
                "id": g.id,
                "name": g.name,
                "description": g.description,
                "severity": g.severity,
                "enabled": g.enabled,
                "checklist": g.checklist,
                "config": g.config,
            }
            for g in guardrails
        ]

    # Fallback to defaults if loader not available (shouldn't happen in practice)
    return get_default_guardrails()


def get_default_guardrails() -> list[dict[str, Any]]:
    """Get default 8 core guardrails (fallback only)."""
    return [
        {"id": 1, "name": "Testing Coverage", "severity": "critical"},
        {"id": 2, "name": "Security Basics", "severity": "critical"},
        {"id": 3, "name": "Error Handling", "severity": "high"},
        {"id": 4, "name": "Logging & Observability", "severity": "high"},
        {"id": 5, "name": "API Design", "severity": "high"},
        {"id": 6, "name": "Data Validation", "severity": "critical"},
        {"id": 7, "name": "Database Migrations", "severity": "high"},
        {"id": 8, "name": "Documentation", "severity": "medium"},
    ]


class GuardrailTracker:
    """Track guardrail coverage and compliance metrics."""

    def __init__(self, specs_dir: Path, project_root: Path | None = None):
        self.specs_dir = specs_dir
        self.project_root = project_root or specs_dir.parent.parent
        self.parser = SpecParser(specs_dir, project_root)
        self._guardrails = None

    @property
    def guardrails(self) -> list[dict[str, Any]]:
        """Get active guardrails (cached)."""
        if self._guardrails is None:
            self._guardrails = load_active_guardrails(self.project_root)
        return self._guardrails

    def get_coverage_summary(self, spec_name: str) -> dict[str, Any]:
        """Get high-level guardrail coverage summary."""
        matrix = self.parser.parse_guardrail_matrix(spec_name)
        expected_count = len(self.guardrails)

        if not matrix:
            return {
                "status": "missing",
                "total": expected_count,
                "addressed": 0,
                "not_applicable": 0,
                "compliance_rate": 0.0,
                "message": "No guardrail coverage matrix found in requirements.md",
            }

        # Count statuses
        addressed = len([row for row in matrix if row["status"].upper() not in ["N/A", "TODO"]])
        not_applicable = len([row for row in matrix if row["status"].upper() == "N/A"])
        todo = len([row for row in matrix if row["status"].upper() == "TODO"])

        compliance_rate = addressed / expected_count if expected_count > 0 else 0.0

        return {
            "status": "complete" if len(matrix) >= expected_count else "incomplete",
            "total": expected_count,
            "matrix_rows": len(matrix),
            "addressed": addressed,
            "todo": todo,
            "not_applicable": not_applicable,
            "compliance_rate": round(compliance_rate, 2),
        }

    def get_coverage_matrix(self, spec_name: str) -> dict[str, Any]:
        """Get full guardrail coverage matrix."""
        matrix = self.parser.parse_guardrail_matrix(spec_name)

        if not matrix:
            return {
                "spec_name": spec_name,
                "status": "missing",
                "rows": [],
                "message": "No guardrail coverage matrix found in requirements.md",
            }

        # Validate matrix has entries for all active guardrails
        missing_guardrails = []
        matrix_ids = set()

        for row in matrix:
            # Extract guardrail ID from first column (e.g., "1. Testing Coverage")
            id_match = re.match(r"(\d+)\.", row["guardrail"])
            if id_match:
                matrix_ids.add(int(id_match.group(1)))

        for guardrail in self.guardrails:
            if guardrail["id"] not in matrix_ids:
                # Try matching by name
                name_found = any(
                    guardrail["name"].lower() in row["guardrail"].lower() for row in matrix
                )
                if not name_found:
                    missing_guardrails.append(f"{guardrail['id']}. {guardrail['name']}")

        return {
            "spec_name": spec_name,
            "status": "complete" if not missing_guardrails else "incomplete",
            "expected_rows": len(self.guardrails),
            "actual_rows": len(matrix),
            "missing_guardrails": missing_guardrails,
            "matrix": matrix,
        }

    def get_guardrail_tasks(self, spec_name: str, guardrail_id: int) -> list[dict[str, Any]]:
        """Get all tasks related to a specific guardrail."""
        tasks_file = self.specs_dir / spec_name / "tasks.md"
        if not tasks_file.exists():
            return []

        content = tasks_file.read_text()
        tasks = self.parser.parse_tasks(spec_name)
        relevant_tasks = []

        # Pattern to find guardrail references in task checklists
        guardrail_pattern = rf"- \[([x ])\] \*\*(?:{guardrail_id}\.|G{guardrail_id}\s)"

        for task in tasks:
            task_id = task["id"]

            # Find task section
            task_section_pattern = (
                rf"#{{2,3}}\s+(?:Task\s+|T-){re.escape(task_id)}:(.+?)(?=\n#{{2,3}}\s|\Z)"
            )
            task_match = re.search(task_section_pattern, content, re.DOTALL)

            if not task_match:
                task_section_pattern = (
                    rf"^- \[[x ]\] \*\*Task\s+{re.escape(task_id)}:\*\*(.+?)(?=\n- \[|\n\n## |\Z)"
                )
                task_match = re.search(task_section_pattern, content, re.DOTALL | re.MULTILINE)

            if task_match:
                task_content = task_match.group(1)

                guardrail_match = re.search(guardrail_pattern, task_content)
                if guardrail_match:
                    full_line_pattern = rf"- \[([x ])\] \*\*(?:{guardrail_id}\.|G{guardrail_id}\s)[^:*]+:?\*?\*?\s*(.+?)(?=\n|$)"
                    full_match = re.search(full_line_pattern, task_content)

                    if full_match:
                        checkbox = full_match.group(1)
                        description = full_match.group(2).strip()

                        if "n/a" not in description.lower():
                            relevant_tasks.append(
                                {
                                    **task,
                                    "guardrail_checked": checkbox == "x",
                                    "guardrail_note": description[:100],
                                }
                            )

        return relevant_tasks

    def validate_coverage(self, spec_name: str) -> dict[str, Any]:
        """Validate that guardrail coverage meets requirements."""
        matrix = self.parser.parse_guardrail_matrix(spec_name)

        if not matrix:
            return {
                "valid": False,
                "errors": ["No guardrail coverage matrix found"],
                "warnings": [],
            }

        errors = []
        warnings = []

        # Check row count
        expected_count = len(self.guardrails)
        if len(matrix) < expected_count:
            errors.append(f"Expected {expected_count} rows, found {len(matrix)}")

        # Check each row
        for row in matrix:
            guardrail = row["guardrail"]

            # Check for empty links (except N/A rows)
            if row["status"].upper() != "N/A":
                if not row["requirements"] or row["requirements"].upper() == "N/A":
                    warnings.append(f"{guardrail}: Missing Requirements link")

                if not row["design"] or row["design"].upper() == "N/A":
                    warnings.append(f"{guardrail}: Missing Design link")

                if not row["tasks_tests"] or row["tasks_tests"].upper() == "N/A":
                    warnings.append(f"{guardrail}: Missing Tasks/Tests link")

                if not row["owner"] or row["owner"].upper() == "N/A":
                    warnings.append(f"{guardrail}: Missing Owner")

            # Check for TODO status
            if row["status"].upper() == "TODO":
                warnings.append(f"{guardrail}: Status is still TODO")

        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    def compare_specs(self, spec1: str, spec2: str) -> dict[str, Any]:
        """Compare guardrail coverage between two specs."""
        coverage1 = self.get_coverage_summary(spec1)
        coverage2 = self.get_coverage_summary(spec2)

        return {
            "spec1": spec1,
            "spec2": spec2,
            "coverage1": coverage1,
            "coverage2": coverage2,
            "compliance_diff": coverage2.get("compliance_rate", 0)
            - coverage1.get("compliance_rate", 0),
        }
