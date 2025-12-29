"""
Guardrail Coverage Validator Module

Maps guardrails to test patterns and validates coverage.
Works with configurable guardrails from .ldf/guardrails.yaml.
"""

from pathlib import Path
from typing import Any

# Import the central guardrail loader for parity with CLI
try:
    from ldf.utils.guardrail_loader import get_active_guardrails

    HAS_GUARDRAIL_LOADER = True
except ImportError:
    HAS_GUARDRAIL_LOADER = False


class GuardrailCoverageValidator:
    """Validate test coverage for specific guardrails."""

    # Default guardrail names (8 core guardrails) - used as fallback
    DEFAULT_GUARDRAIL_NAMES = {
        1: "Testing Coverage",
        2: "Security Basics",
        3: "Error Handling",
        4: "Logging & Observability",
        5: "API Design",
        6: "Data Validation",
        7: "Database Migrations",
        8: "Documentation",
    }

    # Default test file patterns for guardrails
    DEFAULT_TEST_PATTERNS = {
        1: [],  # Testing (meta-guardrail)
        2: ["security", "auth", "test_.*_security"],  # Security
        3: ["error", "exception", "test_.*_error"],  # Error Handling
        4: ["log", "trace", "telemetry", "otel"],  # Logging
        5: ["api", "router", "endpoint"],  # API Design
        6: ["validation", "validator", "schema"],  # Data Validation
        7: ["migration", "alembic", "schema"],  # Migrations
        8: [],  # Documentation (meta-guardrail)
    }

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path.cwd()
        self._guardrails = None
        self._patterns = None

    def _load_guardrails(self) -> dict[int, str]:
        """Load guardrail names using the central guardrail_loader.

        This ensures parity with CLI lint behavior, respecting:
        - Core guardrails
        - Preset guardrails
        - Custom guardrails
        - Overrides
        - Disabled list
        """
        if self._guardrails is not None:
            return self._guardrails

        self._guardrails = dict(self.DEFAULT_GUARDRAIL_NAMES)

        if HAS_GUARDRAIL_LOADER:
            try:
                # Use the central loader for consistent behavior with CLI
                guardrails = get_active_guardrails(self.project_root)
                # Build name mapping from active guardrails
                self._guardrails = {g.id: g.name for g in guardrails}
            except Exception:
                pass  # Use defaults on error

        return self._guardrails

    def _load_patterns(self) -> dict[int, list[str]]:
        """Load test patterns for guardrails."""
        if self._patterns is not None:
            return self._patterns

        self._patterns = dict(self.DEFAULT_TEST_PATTERNS)

        # Could be extended to load custom patterns from config
        return self._patterns

    def get_guardrail_name(self, guardrail_id: int) -> str:
        """Get guardrail name by ID."""
        guardrails = self._load_guardrails()
        return guardrails.get(guardrail_id, f"Guardrail #{guardrail_id}")

    def get_test_patterns_for_guardrail(self, guardrail_id: int) -> list[str]:
        """Get test file patterns for a guardrail."""
        patterns = self._load_patterns()
        return patterns.get(guardrail_id, [])

    def validate_guardrail_coverage(
        self, guardrail_id: int, coverage_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Validate that a guardrail has adequate test coverage.

        Returns:
            {
                "guardrail_id": 1,
                "guardrail_name": "Testing Coverage",
                "has_tests": True,
                "test_count": 5,
                "average_coverage": 95.0,
                "valid": True
            }
        """
        patterns = self.get_test_patterns_for_guardrail(guardrail_id)

        # Meta-guardrails (Testing, Documentation) don't have specific tests
        if not patterns:
            return {
                "guardrail_id": guardrail_id,
                "guardrail_name": self.get_guardrail_name(guardrail_id),
                "has_tests": False,
                "test_count": 0,
                "average_coverage": 0.0,
                "valid": True,  # Meta-guardrails are valid without specific tests
                "message": "Meta-guardrail - no specific test patterns",
            }

        # Find matching test files
        matching_tests = []
        for file_path, file_data in coverage_data.get("files", {}).items():
            if "test" in file_path.lower():
                for pattern in patterns:
                    if pattern.lower() in file_path.lower():
                        matching_tests.append(file_data)
                        break

        # Calculate average coverage
        if matching_tests:
            total_lines = sum(t["summary"]["num_statements"] for t in matching_tests)
            covered_lines = sum(t["summary"]["covered_lines"] for t in matching_tests)
            avg_coverage = (covered_lines / total_lines * 100) if total_lines > 0 else 0.0
        else:
            avg_coverage = 0.0

        return {
            "guardrail_id": guardrail_id,
            "guardrail_name": self.get_guardrail_name(guardrail_id),
            "has_tests": len(matching_tests) > 0,
            "test_count": len(matching_tests),
            "average_coverage": round(avg_coverage, 2),
            "valid": len(matching_tests) > 0 and avg_coverage >= 80.0,
        }
