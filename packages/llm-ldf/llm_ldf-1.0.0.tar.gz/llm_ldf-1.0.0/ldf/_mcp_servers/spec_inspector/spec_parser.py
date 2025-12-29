"""
Spec Parser Module

Parses spec markdown files (requirements.md, design.md, tasks.md) and YAML answerpacks.
"""

import re
from pathlib import Path
from typing import Any

import yaml

# Status normalization maps for consistent status values
STATUS_SYNONYMS = {
    "completed": {"complete", "completed", "done", "finished", "implemented", "pass", "passed"},
    "in_progress": {"in_progress", "in progress", "wip", "working", "started"},
    "pending": {"pending", "todo", "not started", "planned"},
    "blocked": {"blocked", "on hold", "waiting", "deferred", "future"},
}


def normalize_status(status_value: str) -> str:
    """Normalize status value to standard enum: completed, in_progress, pending, blocked."""
    status_lower = status_value.lower().strip()

    for normalized, synonyms in STATUS_SYNONYMS.items():
        if status_lower in synonyms:
            return normalized

    # Check for partial matches (e.g., "implemented feature" contains "implemented")
    for normalized, synonyms in STATUS_SYNONYMS.items():
        for synonym in synonyms:
            if synonym in status_lower:
                return normalized

    # Return as-is if no match (but lowercase)
    return status_lower


class SpecParser:
    """Parser for spec markdown and YAML files."""

    def __init__(self, specs_dir: Path | str, project_root: Path | str | None = None):
        self.specs_dir = Path(specs_dir) if isinstance(specs_dir, str) else specs_dir
        self.project_root = Path(project_root) if project_root else self.specs_dir.parent.parent

    def parse_spec(self, spec_name: str) -> dict[str, Any]:
        """Parse all spec files and return metadata."""
        spec_path = self.specs_dir / spec_name

        if not spec_path.exists():
            raise ValueError(f"Spec not found: {spec_name}")

        data = {"name": spec_name, "path": str(spec_path), "status": "unknown"}

        # Check which files exist
        req_file = spec_path / "requirements.md"
        design_file = spec_path / "design.md"
        tasks_file = spec_path / "tasks.md"

        if req_file.exists() and design_file.exists() and tasks_file.exists():
            data["status"] = "approved"
        elif req_file.exists() and design_file.exists():
            data["status"] = "design_complete"
        elif req_file.exists():
            data["status"] = "requirements_complete"
        else:
            data["status"] = "incomplete"

        return data

    def parse_tasks(self, spec_name: str) -> list[dict[str, Any]]:
        """
        Parse tasks.md and extract task list.

        Uses the official bold checklist format:
        - [x] **Task 1.1:** Create domain models
          - [x] Sub-item 1
        """
        tasks_file = self.specs_dir / spec_name / "tasks.md"

        if not tasks_file.exists():
            return []

        content = tasks_file.read_text()

        # Check for file-level completion status
        file_complete = self._detect_file_completion(content)

        # Parse bold checklist format (official format only)
        return self._parse_bullet_tasks(content, file_complete)

    def _detect_file_completion(self, content: str) -> bool:
        """Detect if the entire file is marked as complete."""
        tail = content[-2500:] if len(content) > 2500 else content

        status_patterns = [
            r"\*\*Status:\*\*\s*(?:\u2705\s*)?(?:VALIDATION\s+)?COMPLETE",
            r"\*\*Status:\*\*\s*Complete(?:\s*\([^)]+\))?",
            r"\*\*Status:\*\*\s*100%\s*COMPLETE",
            r"\*\*Status:\*\*\s*FULLY\s+IMPLEMENTED",
        ]

        for pattern in status_patterns:
            if re.search(pattern, tail, re.IGNORECASE):
                return True

        if re.search(r"\*\*Completed:\*\*\s*\d{4}-\d{2}-\d{2}", tail):
            return True

        return False

    def _parse_bullet_tasks(
        self, content: str, file_complete: bool = False
    ) -> list[dict[str, Any]]:
        """Parse bullet-format tasks (official format)."""
        tasks = []

        bullet_pattern = (
            r"^- \[([xX ])\] \*\*Task\s+([\d.]+):\*\*\s+(.+?)(?=\n- \[|\n\n## |\n---|\Z)"
        )
        bullet_matches = re.finditer(bullet_pattern, content, re.DOTALL | re.MULTILINE)

        for match in bullet_matches:
            checkbox = match.group(1)
            task_id = match.group(2)
            task_content = match.group(3)

            task_title = task_content.split("\n")[0].strip()

            sub_items = re.findall(r"^\s+- \[([xX ])\]", task_content, re.MULTILINE)
            checklist_total = len(sub_items)
            checklist_completed = len([s for s in sub_items if s.lower() == "x"])

            if file_complete:
                final_status = "completed"
            elif checkbox.lower() == "x":
                final_status = "completed"
            elif checklist_total > 0 and checklist_completed > 0:
                final_status = "in_progress"
            else:
                final_status = "pending"

            estimated_match = re.search(
                r"\*\*Estimated:\*\*\s*([\d.]+)\s*hours?", task_content, re.IGNORECASE
            )
            deps_match = re.search(r"\*\*Dependencies:\*\*\s*(.+?)(?=\n|$)", task_content)

            tasks.append(
                {
                    "id": task_id,
                    "title": task_title,
                    "status": final_status,
                    "estimated_hours": float(estimated_match.group(1)) if estimated_match else 0.0,
                    "dependencies": deps_match.group(1).strip() if deps_match else "None",
                    "checklist_total": checklist_total,
                    "checklist_completed": checklist_completed,
                }
            )

        return tasks

    def list_answerpacks(self, spec_name: str) -> list[str]:
        """List all answerpack YAML files for a spec."""
        # Check spec-local answerpacks
        answerpack_dir = self.specs_dir / spec_name / "answerpacks"
        if answerpack_dir.exists():
            return [f.name for f in answerpack_dir.glob("*.yaml")]

        # Check central answerpacks
        central_dir = self.project_root / ".ldf" / "answerpacks" / spec_name
        if central_dir.exists():
            return [f.name for f in central_dir.glob("*.yaml")]

        return []

    def parse_answerpack(self, spec_name: str, answerpack_name: str) -> dict[str, Any]:
        """Parse a specific answerpack YAML file."""
        # Check spec-local first
        answerpack_file = self.specs_dir / spec_name / "answerpacks" / answerpack_name
        if not answerpack_file.exists():
            # Check central
            answerpack_file = (
                self.project_root / ".ldf" / "answerpacks" / spec_name / answerpack_name
            )

        if not answerpack_file.exists():
            raise ValueError(f"Answerpack not found: {answerpack_name}")

        with open(answerpack_file) as f:
            return yaml.safe_load(f)

    def parse_guardrail_matrix(self, spec_name: str) -> list[dict[str, Any]]:
        """
        Parse guardrail coverage matrix from requirements.md.

        Expected format:
        | Guardrail | Requirements | Design | Tasks/Tests | Owner | Status |
        |-----------|--------------|--------|-------------|-------|--------|
        | 1. Testing Coverage | [US-1] | [S3] | [T-1] | Alice | TODO |
        """
        req_file = self.specs_dir / spec_name / "requirements.md"

        if not req_file.exists():
            return []

        content = req_file.read_text()

        # Find the guardrail coverage matrix section
        matrix_section = re.search(
            r"## Guardrail Coverage Matrix\s*\n+(.*?)(?=\n##|\Z)",
            content,
            re.DOTALL | re.IGNORECASE,
        )

        if not matrix_section:
            return []

        matrix_text = matrix_section.group(1)

        # Parse markdown table
        lines = [line.strip() for line in matrix_text.split("\n") if line.strip()]

        # Skip header and separator
        data_lines = [line for line in lines if not line.startswith("|---")]
        if len(data_lines) < 2:
            return []

        rows = []
        for line in data_lines[1:]:  # Skip header row
            cells = [cell.strip() for cell in line.split("|")[1:-1]]

            if len(cells) >= 5:
                rows.append(
                    {
                        "guardrail": cells[0],
                        "requirements": cells[1],
                        "design": cells[2],
                        "tasks_tests": cells[3],
                        "owner": cells[4],
                        "status": cells[5] if len(cells) > 5 else "TODO",
                    }
                )

        return rows

    def parse_question_pack_answers(self, spec_name: str) -> dict[str, Any]:
        """Parse Question-Pack Answers section from requirements.md."""
        req_file = self.specs_dir / spec_name / "requirements.md"

        if not req_file.exists():
            return {}

        content = req_file.read_text()

        section = re.search(
            r"## Question-Pack Answers\s*\n+(.*?)(?=\n##|\Z)", content, re.DOTALL | re.IGNORECASE
        )

        if not section:
            return {}

        section_text = section.group(1)

        domains = {}
        domain_pattern = r"###\s+(.+?)\s*\((.+?\.yaml)\)\s*\n+(.*?)(?=\n###|\Z)"
        domain_matches = re.finditer(domain_pattern, section_text, re.DOTALL)

        for match in domain_matches:
            domain_name = match.group(1).strip()
            yaml_file = match.group(2).strip()
            answers = match.group(3).strip()

            domains[domain_name] = {"yaml_file": yaml_file, "answers": answers}

        return domains
