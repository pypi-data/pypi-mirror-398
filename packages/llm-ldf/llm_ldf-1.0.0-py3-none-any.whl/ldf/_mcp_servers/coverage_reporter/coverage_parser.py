"""
Coverage Parser Module

Parses test coverage data from various formats (pytest-cov, Jest, etc.).
"""

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("coverage_reporter")


class CoverageParser:
    """Parse coverage data files from multiple formats."""

    # Coverage file locations to check
    COVERAGE_FILES = [
        ".coverage",
        "coverage.json",
        ".coverage.json",
        "coverage/coverage-final.json",
        "coverage/coverage-summary.json",
        ".ldf/coverage.json",
    ]

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self._cached_data = None
        self._cache_mtime = 0.0

    def _get_coverage_mtime(self) -> float:
        """Get the latest modification time of coverage files.

        Returns:
            Latest mtime of any existing coverage file, or 0.0 if none exist.
        """
        mtimes = []
        for rel_path in self.COVERAGE_FILES:
            coverage_file = self.project_root / rel_path
            if coverage_file.exists():
                try:
                    mtimes.append(coverage_file.stat().st_mtime)
                except OSError:
                    continue
        return max(mtimes) if mtimes else 0.0

    def invalidate_cache(self) -> None:
        """Explicitly invalidate the coverage cache."""
        self._cached_data = None
        self._cache_mtime = 0.0
        logger.debug("Coverage cache invalidated")

    def parse_coverage(self, force_reload: bool = False) -> dict[str, Any]:
        """
        Parse coverage data from available sources.

        Args:
            force_reload: If True, bypass cache and reload from disk.

        Supports:
        - Python: .coverage (coverage.py)
        - Python: coverage.json (pytest-cov JSON output)
        - Node.js: coverage/coverage-final.json (Jest)
        - Node.js: coverage/coverage-summary.json (Jest)

        Returns:
            {
                "summary": {
                    "num_statements": 1000,
                    "covered_lines": 850,
                    "percent_covered": 85.0
                },
                "files": {
                    "src/services/auth.py": {
                        "path": "src/services/auth.py",
                        "summary": {...},
                        "missing_lines": [45, 67, 89]
                    }
                }
            }
        """
        # Check if cache is valid (not forced and mtime unchanged)
        current_mtime = self._get_coverage_mtime()
        if not force_reload and self._cached_data is not None:
            if current_mtime <= self._cache_mtime:
                logger.debug("Returning cached coverage data")
                return self._cached_data
            else:
                logger.debug("Coverage files changed, invalidating cache")

        # Try different coverage sources
        parsers = [
            (self.project_root / ".coverage", self._parse_coverage_py),
            (self.project_root / "coverage.json", self._parse_coverage_json),
            (self.project_root / ".coverage.json", self._parse_coverage_json),
            (self.project_root / "coverage" / "coverage-final.json", self._parse_jest_coverage),
            (self.project_root / "coverage" / "coverage-summary.json", self._parse_jest_summary),
            (self.project_root / ".ldf" / "coverage.json", self._parse_coverage_json),
        ]

        for path, parser_func in parsers:
            if path.exists():
                try:
                    self._cached_data = parser_func(path)
                    self._cache_mtime = current_mtime
                    logger.info(f"Parsed coverage from: {path}")
                    return self._cached_data
                except Exception as e:
                    logger.warning(f"Failed to parse {path}: {e}")
                    continue

        raise FileNotFoundError(
            "No coverage data found. Supported formats:\n"
            "  - Python: pytest --cov=. --cov-report=json\n"
            "  - Node.js: jest --coverage --coverageReporters=json"
        )

    def _parse_coverage_py(self, coverage_file: Path) -> dict[str, Any]:
        """Parse .coverage file using coverage.py API."""
        try:
            from coverage import Coverage
        except ImportError:
            raise RuntimeError("coverage module not found. Install: pip install coverage")

        cov = Coverage(data_file=str(coverage_file))
        cov.load()

        files_data = {}
        total_statements = 0
        total_covered = 0

        measured_files = cov.get_data().measured_files()

        for file_path in measured_files:
            if not Path(file_path).exists():
                continue

            try:
                # Use public analysis2() API instead of private _analyze()
                # Returns: (filename, statements, excluded, missing, missing_formatted)
                _, statements_set, _, missing_set, _ = cov.analysis2(file_path)
                num_statements = len(statements_set)
                num_missing = len(missing_set)
                covered = num_statements - num_missing
                percent = (covered / num_statements * 100) if num_statements > 0 else 0.0

                try:
                    rel_path = str(Path(file_path).relative_to(self.project_root))
                except ValueError:
                    rel_path = file_path

                files_data[rel_path] = {
                    "path": rel_path,
                    "summary": {
                        "num_statements": num_statements,
                        "covered_lines": covered,
                        "percent_covered": round(percent, 2),
                    },
                    "missing_lines": sorted(missing_set),
                }

                total_statements += num_statements
                total_covered += covered

            except Exception as e:
                logger.warning(f"Could not analyze {file_path}: {e}")
                continue

        overall_percent = (total_covered / total_statements * 100) if total_statements > 0 else 0.0

        return {
            "summary": {
                "num_statements": total_statements,
                "covered_lines": total_covered,
                "percent_covered": round(overall_percent, 2),
            },
            "files": files_data,
        }

    def _parse_coverage_json(self, json_file: Path) -> dict[str, Any]:
        """Parse coverage.json (pytest-cov JSON format)."""
        with open(json_file) as f:
            data = json.load(f)

        # Handle pytest-cov format
        if "totals" in data:
            totals = data["totals"]
            files_data = {}

            for file_path, file_info in data.get("files", {}).items():
                summary = file_info.get("summary", {})
                try:
                    rel_path = str(Path(file_path).relative_to(self.project_root))
                except ValueError:
                    rel_path = file_path

                files_data[rel_path] = {
                    "path": rel_path,
                    "summary": {
                        "num_statements": summary.get("num_statements", 0),
                        "covered_lines": summary.get("covered_lines", 0),
                        "percent_covered": round(summary.get("percent_covered", 0), 2),
                    },
                    "missing_lines": file_info.get("missing_lines", []),
                }

            return {
                "summary": {
                    "num_statements": totals.get("num_statements", 0),
                    "covered_lines": totals.get("covered_lines", 0),
                    "percent_covered": round(totals.get("percent_covered", 0), 2),
                },
                "files": files_data,
            }

        raise ValueError("Unknown coverage.json format")

    def _parse_jest_coverage(self, json_file: Path) -> dict[str, Any]:
        """Parse Jest coverage-final.json format."""
        with open(json_file) as f:
            data = json.load(f)

        files_data = {}
        total_statements = 0
        total_covered = 0

        for file_path, file_info in data.items():
            statements = file_info.get("s", {})
            total = len(statements)
            covered = sum(1 for v in statements.values() if v > 0)
            percent = (covered / total * 100) if total > 0 else 0.0

            try:
                rel_path = str(Path(file_path).relative_to(self.project_root))
            except ValueError:
                rel_path = file_path

            # Find uncovered line numbers
            statement_map = file_info.get("statementMap", {})
            missing_lines = [
                statement_map[key]["start"]["line"]
                for key, value in statements.items()
                if value == 0 and key in statement_map
            ]

            files_data[rel_path] = {
                "path": rel_path,
                "summary": {
                    "num_statements": total,
                    "covered_lines": covered,
                    "percent_covered": round(percent, 2),
                },
                "missing_lines": sorted(set(missing_lines)),
            }

            total_statements += total
            total_covered += covered

        overall_percent = (total_covered / total_statements * 100) if total_statements > 0 else 0.0

        return {
            "summary": {
                "num_statements": total_statements,
                "covered_lines": total_covered,
                "percent_covered": round(overall_percent, 2),
            },
            "files": files_data,
        }

    def _parse_jest_summary(self, json_file: Path) -> dict[str, Any]:
        """Parse Jest coverage-summary.json format."""
        with open(json_file) as f:
            data = json.load(f)

        total = data.get("total", {})
        lines = total.get("lines", {})

        files_data = {}
        for file_path, file_info in data.items():
            if file_path == "total":
                continue

            file_lines = file_info.get("lines", {})
            try:
                rel_path = str(Path(file_path).relative_to(self.project_root))
            except ValueError:
                rel_path = file_path

            files_data[rel_path] = {
                "path": rel_path,
                "summary": {
                    "num_statements": file_lines.get("total", 0),
                    "covered_lines": file_lines.get("covered", 0),
                    "percent_covered": round(file_lines.get("pct", 0), 2),
                },
                "missing_lines": [],  # Not available in summary format
            }

        return {
            "summary": {
                "num_statements": lines.get("total", 0),
                "covered_lines": lines.get("covered", 0),
                "percent_covered": round(lines.get("pct", 0), 2),
            },
            "files": files_data,
        }

    def get_coverage_for_path(self, path_pattern: str) -> dict[str, Any]:
        """Get coverage data for files matching pattern."""
        coverage_data = self.parse_coverage()

        matching_files = {
            file_path: file_data
            for file_path, file_data in coverage_data["files"].items()
            if path_pattern in file_path
        }

        if not matching_files:
            return {"pattern": path_pattern, "files": [], "total_coverage": 0.0}

        total_lines = sum(f["summary"]["num_statements"] for f in matching_files.values())
        covered_lines = sum(f["summary"]["covered_lines"] for f in matching_files.values())
        avg_coverage = (covered_lines / total_lines * 100) if total_lines > 0 else 0.0

        return {
            "pattern": path_pattern,
            "file_count": len(matching_files),
            "total_coverage": round(avg_coverage, 2),
            "files": list(matching_files.values()),
        }
