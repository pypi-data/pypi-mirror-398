"""Tests for ldf.utils.spec_parser module."""

from pathlib import Path

from ldf.utils.spec_parser import (
    SpecInfo,
    SpecStatus,
    _determine_status,
    extract_guardrail_matrix,
    extract_tasks,
    get_spec_status,
    parse_spec,
)


class TestExtractGuardrailMatrix:
    """Tests for extract_guardrail_matrix function."""

    def test_extracts_valid_matrix(self):
        """Test extraction of a valid guardrail matrix."""
        content = """# Requirements

## Guardrail Coverage Matrix

| Guardrail | Requirements | Design | Tasks/Tests | Owner | Status |
|-----------|--------------|--------|-------------|-------|--------|
| 1. Testing Coverage | [US-1] | [S1] | [T-1] | Dev | TODO |
| 2. Security Basics | [US-2] | [S2] | [T-2] | Dev | Done |

## Other Section
"""
        matrix = extract_guardrail_matrix(content)

        assert len(matrix) == 2
        assert matrix[0].guardrail_id == 1
        assert matrix[0].guardrail_name == "Testing Coverage"
        assert matrix[0].requirements_ref == "[US-1]"
        assert matrix[0].design_ref == "[S1]"
        assert matrix[0].status == "TODO"
        assert matrix[1].guardrail_id == 2
        assert matrix[1].status == "Done"

    def test_extracts_matrix_with_empty_line_after_header(self):
        """Test extraction when there's an empty line after the header."""
        content = """## Guardrail Coverage Matrix

| Guardrail | Requirements | Design | Tasks/Tests | Owner | Status |
|-----------|--------------|--------|-------------|-------|--------|
| 1. Testing | [US-1] | [S1] | [T-1] | Dev | TODO |
"""
        matrix = extract_guardrail_matrix(content)
        assert len(matrix) == 1
        assert matrix[0].guardrail_id == 1

    def test_returns_empty_list_when_no_matrix(self):
        """Test returns empty list when no matrix section exists."""
        content = """# Requirements

## User Stories

Some content here.
"""
        matrix = extract_guardrail_matrix(content)
        assert matrix == []

    def test_handles_na_status(self):
        """Test handling of N/A status in matrix."""
        content = """## Guardrail Coverage Matrix

| Guardrail | Requirements | Design | Tasks/Tests | Owner | Status |
|-----------|--------------|--------|-------------|-------|--------|
| 1. Testing | N/A | N/A | N/A | N/A | N/A - not applicable |
"""
        matrix = extract_guardrail_matrix(content)
        assert len(matrix) == 1
        assert matrix[0].status == "N/A - not applicable"


class TestExtractTasks:
    """Tests for extract_tasks function."""

    def test_extracts_tasks_with_bold_checklist_format(self):
        """Test extraction of tasks with bold checklist format."""
        content = """# Tasks

## Phase 1

- [ ] **Task 1.1:** Setup project
  - [ ] Create directories
  - [ ] Initialize config

## Phase 2

- [ ] **Task 2.1:** Implement feature
  - [ ] Write code
  - [x] Write tests
"""
        tasks = extract_tasks(content)

        assert len(tasks) == 2
        assert tasks[0].id == "1.1"
        assert tasks[0].title == "Setup project"
        assert tasks[0].status == "pending"  # All checkboxes unchecked
        assert tasks[1].id == "2.1"
        assert tasks[1].status == "in_progress"  # Has both checked and unchecked

    def test_extracts_completed_task(self):
        """Test extraction of fully completed task."""
        content = """## Tasks

- [x] **Task 2.1:** Done task
  - [x] Step one
  - [x] Step two
"""
        tasks = extract_tasks(content)
        assert len(tasks) == 1
        assert tasks[0].status == "complete"

    def test_returns_empty_list_when_no_tasks(self):
        """Test returns empty list when no tasks found."""
        content = """# Just some content

No tasks here.
"""
        tasks = extract_tasks(content)
        assert tasks == []

    def test_handles_task_without_subtasks(self):
        """Test handling of task without subtasks."""
        content = """## Phase 1

- [ ] **Task 1.1:** Empty task

- [ ] **Task 1.2:** Another task
  - [ ] One item
"""
        tasks = extract_tasks(content)
        assert len(tasks) == 2


class TestExtractTasksFalsePositivePrevention:
    """Tests that extract_tasks doesn't match spurious task ID patterns."""

    def test_ignores_inline_task_references(self):
        """Test that inline references to task IDs are not matched as tasks."""
        content = """# Tasks

See task 1.1 for prerequisites.
Based on section 2.3, we need to implement feature X.
Per guardrail 1.1 requirements, all code must be tested.

- [ ] **Task 1.1:** Actual task
  - [ ] Step one
  - [ ] Step two

- [ ] **Task 2.3:** Another task
  - [ ] Do something
"""
        tasks = extract_tasks(content)

        # Should only find the two actual tasks, not the inline references
        assert len(tasks) == 2
        assert tasks[0].id == "1.1"
        assert tasks[0].title == "Actual task"
        assert tasks[1].id == "2.3"
        assert tasks[1].title == "Another task"

    def test_ignores_decimal_numbers_that_arent_tasks(self):
        """Test that decimal numbers in regular text aren't matched."""
        content = """## Implementation Notes

Version 1.1 was released last month.
The coverage should be >= 1.1x baseline.
Reference section 3.2 in the documentation.

- [ ] **Task 1.1:** Real task
  - [ ] Implement feature
"""
        tasks = extract_tasks(content)

        # Should only find the one actual task
        assert len(tasks) == 1
        assert tasks[0].id == "1.1"

    def test_ignores_task_ids_without_checkbox(self):
        """Test that task IDs without checkbox markers are not matched."""
        content = """## Tasks

Some paragraph mentioning Task 1.1: this should not match.
Another line with Task 2.3 that should not match.

- [ ] **Task 1.1:** Actual task
  - [ ] Step one

- [ ] **Task 2.3:** Another task
  - [ ] Step two
"""
        tasks = extract_tasks(content)

        assert len(tasks) == 2
        assert tasks[0].id == "1.1"
        assert tasks[1].id == "2.3"

    def test_requires_checkbox_and_bold_markers(self):
        """Test that checkbox and bold markers are required for task detection."""
        content = """
Task 1.1: This should not match (no checkbox or bold)
- Task 1.2: This should not match (no checkbox with space)
- [ ] Task 1.3: This should not match (no bold markers)

- [ ] **Task 1.4:** This should match
  - [ ] Step one
"""
        tasks = extract_tasks(content)

        # Only the one with checkbox and bold markers should match
        assert len(tasks) == 1
        assert tasks[0].id == "1.4"
        assert tasks[0].title == "This should match"


class TestExtractTasksChecklistFormat:
    """Tests for extract_tasks with checklist-style task format."""

    def test_extracts_tasks_in_checklist_format(self):
        """Test extraction of tasks in checklist format (template style)."""
        content = """# Tasks

## Phase 1: Setup

- [ ] **Task 1.1:** Project setup
  - [ ] Create directories
  - [ ] Install dependencies

- [ ] **Task 1.2:** Database schema
  - [ ] Create migration file

## Phase 2: Implementation

- [ ] **Task 2.1:** Implement service
  - [ ] Create service class
  - [x] Write tests
"""
        tasks = extract_tasks(content)

        assert len(tasks) == 3
        assert tasks[0].id == "1.1"
        assert tasks[0].title == "Project setup"
        assert tasks[0].status == "pending"
        assert tasks[1].id == "1.2"
        assert tasks[1].title == "Database schema"
        assert tasks[2].id == "2.1"
        assert tasks[2].title == "Implement service"
        assert tasks[2].status == "in_progress"  # Has both checked and unchecked

    def test_extracts_completed_checklist_task(self):
        """Test extraction of fully completed checklist task."""
        content = """## Tasks

- [x] **Task 1.1:** Completed task
  - [x] Step one
  - [x] Step two
"""
        tasks = extract_tasks(content)
        assert len(tasks) == 1
        assert tasks[0].status == "complete"

    def test_multiple_tasks_across_phases(self):
        """Test multiple tasks across different phases."""
        content = """# Tasks

- [ ] **Task 1.1:** First phase task
  - [ ] Step one

- [ ] **Task 1.2:** Second task in phase 1
  - [ ] Step one

## Phase 2

- [ ] **Task 2.1:** First task in phase 2
  - [ ] Implementation

- [x] **Task 2.2:** Completed task
  - [x] Done
"""
        tasks = extract_tasks(content)

        assert len(tasks) == 4
        assert tasks[0].id == "1.1"
        assert tasks[0].title == "First phase task"
        assert tasks[1].id == "1.2"
        assert tasks[1].title == "Second task in phase 1"
        assert tasks[2].id == "2.1"
        assert tasks[2].title == "First task in phase 2"
        assert tasks[3].id == "2.2"
        assert tasks[3].title == "Completed task"
        assert tasks[3].status == "complete"

    def test_checklist_format_prevents_false_positives(self):
        """Test that checklist format still prevents false positives."""
        content = """# Tasks

See task 1.1 for prerequisites.
Based on version 2.3, we need to implement feature X.

- [ ] **Task 1.1:** Real task
  - [ ] Step one
"""
        tasks = extract_tasks(content)

        # Should only find the actual task, not the inline references
        assert len(tasks) == 1
        assert tasks[0].id == "1.1"
        assert tasks[0].title == "Real task"

    def test_requires_bold_markers(self):
        """Test that tasks without bold markers are not matched."""
        content = """# Tasks

## Phase 1

- [ ] Task 1.1: Setup project (should not match)
  - [ ] Create directories

## Phase 2

- [ ] **Task 2.1:** Configure environment (should match)
  - [ ] Install packages
"""
        tasks = extract_tasks(content)

        # Only the task with bold markers should match
        assert len(tasks) == 1
        assert tasks[0].id == "2.1"
        assert tasks[0].title == "Configure environment (should match)"

    def test_task_status_scoping_with_multiple_tasks_in_same_phase(self):
        """Test that task status is scoped correctly when multiple tasks are in same phase.

        This is a regression test for the bug where Task 1.1's section included
        Tasks 1.2 and 1.3, causing checkboxes from later tasks to affect earlier ones.
        """
        content = """# Tasks

## Phase 1

- [ ] **Task 1.1:** First task
  - [ ] First task subtask 1
  - [ ] First task subtask 2

- [ ] **Task 1.2:** Second task
  - [ ] Second task subtask 1
  - [x] Second task subtask 2

- [x] **Task 1.3:** Third task
  - [x] Third task subtask 1
  - [x] Third task subtask 2
"""
        tasks = extract_tasks(content)

        assert len(tasks) == 3
        # Task 1.1 should be pending (all its subtasks are unchecked)
        assert tasks[0].id == "1.1"
        assert tasks[0].status == "pending"
        # Task 1.2 should be in_progress (one checked, one unchecked)
        assert tasks[1].id == "1.2"
        assert tasks[1].status == "in_progress"
        # Task 1.3 should be complete (all its subtasks are checked)
        assert tasks[2].id == "1.3"
        assert tasks[2].status == "complete"

    def test_subtask_ids_with_three_levels(self):
        """Test extraction of subtask IDs with three levels (e.g., 1.1.1)."""
        content = """# Tasks

## Phase 1

- [ ] **Task 1.1:** Parent task
  - [ ] Step one

- [ ] **Task 1.1.1:** Subtask of 1.1
  - [ ] Subtask step

- [x] **Task 1.1.2:** Another subtask of 1.1
  - [x] Completed step

## Phase 2

- [ ] **Task 2.1:** Another task
  - [ ] Step

- [ ] **Task 2.1.1:** Subtask of 2.1
  - [ ] Step
"""
        tasks = extract_tasks(content)

        assert len(tasks) == 5
        assert tasks[0].id == "1.1"
        assert tasks[0].title == "Parent task"
        assert tasks[1].id == "1.1.1"
        assert tasks[1].title == "Subtask of 1.1"
        assert tasks[1].status == "pending"
        assert tasks[2].id == "1.1.2"
        assert tasks[2].title == "Another subtask of 1.1"
        assert tasks[2].status == "complete"
        assert tasks[3].id == "2.1"
        assert tasks[3].title == "Another task"
        assert tasks[4].id == "2.1.1"
        assert tasks[4].title == "Subtask of 2.1"

    def test_dependencies_with_subtask_ids(self):
        """Test that dependencies can reference subtask IDs."""
        content = """# Tasks

- [ ] **Task 1.1:** First task
  - **Depends on:** None

- [ ] **Task 1.1.1:** Subtask
  - **Depends on:** Task 1.1

- [ ] **Task 2.1:** Another task
  - **Depends on:** Task 1.1, Task 1.1.1
"""
        tasks = extract_tasks(content)

        assert len(tasks) == 3
        assert tasks[0].dependencies == []
        assert tasks[1].dependencies == ["1.1"]
        assert tasks[2].dependencies == ["1.1", "1.1.1"]

    def test_indented_checklists(self):
        """Test that indented checklist tasks are recognized."""
        content = """# Tasks

## Phase 1

  - [ ] **Task 1.1:** Indented task (2 spaces)
    - [ ] Subtask one

    - [ ] **Task 1.2:** Also indented
      - [ ] Subtask two
"""
        tasks = extract_tasks(content)

        assert len(tasks) == 2
        assert tasks[0].id == "1.1"
        assert tasks[0].title == "Indented task (2 spaces)"
        assert tasks[1].id == "1.2"
        assert tasks[1].title == "Also indented"


class TestParseSpec:
    """Tests for parse_spec function."""

    def test_parses_complete_spec(self, temp_spec: Path):
        """Test parsing a complete spec with all three files."""
        spec_info = parse_spec(temp_spec)

        assert spec_info.name == "test-feature"
        assert spec_info.has_requirements is True
        assert spec_info.has_design is True
        assert spec_info.has_tasks is True
        assert len(spec_info.guardrail_matrix) == 8
        assert len(spec_info.tasks) == 2

    def test_parses_spec_with_missing_files(self, tmp_path: Path):
        """Test parsing spec with missing files."""
        spec_dir = tmp_path / "incomplete-spec"
        spec_dir.mkdir()

        # Only create requirements.md
        (spec_dir / "requirements.md").write_text("# Requirements\n")

        spec_info = parse_spec(spec_dir)

        assert spec_info.has_requirements is True
        assert spec_info.has_design is False
        assert spec_info.has_tasks is False
        assert spec_info.status == SpecStatus.REQUIREMENTS_DRAFT

    def test_detects_not_started_status(self, tmp_path: Path):
        """Test detection of NOT_STARTED status."""
        spec_dir = tmp_path / "empty-spec"
        spec_dir.mkdir()

        spec_info = parse_spec(spec_dir)
        assert spec_info.status == SpecStatus.NOT_STARTED

    def test_collects_errors_for_missing_sections(self, tmp_path: Path):
        """Test that errors are collected for missing required sections."""
        spec_dir = tmp_path / "bad-spec"
        spec_dir.mkdir()

        # Requirements without required sections
        (spec_dir / "requirements.md").write_text("""# Requirements

## User Stories
Some stories.
""")

        spec_info = parse_spec(spec_dir)

        assert len(spec_info.errors) > 0
        assert any("Question-Pack Answers" in e for e in spec_info.errors)
        assert any("Guardrail Coverage Matrix" in e for e in spec_info.errors)


class TestSpecStatus:
    """Tests for SpecStatus enum and status detection."""

    def test_status_values(self):
        """Test SpecStatus enum has expected values."""
        assert SpecStatus.NOT_STARTED.value == "not_started"
        assert SpecStatus.REQUIREMENTS_DRAFT.value == "requirements_draft"
        assert SpecStatus.DESIGN_DRAFT.value == "design_draft"
        assert SpecStatus.TASKS_DRAFT.value == "tasks_draft"
        assert SpecStatus.COMPLETE.value == "complete"


class TestGetSpecStatus:
    """Tests for get_spec_status function."""

    def test_returns_not_started_for_empty_spec(self, tmp_path: Path):
        """Test returning NOT_STARTED for empty spec directory."""
        spec_dir = tmp_path / "empty-spec"
        spec_dir.mkdir()

        status = get_spec_status(spec_dir)

        assert status == SpecStatus.NOT_STARTED

    def test_returns_requirements_draft(self, tmp_path: Path):
        """Test returning REQUIREMENTS_DRAFT for spec with unapproved requirements."""
        spec_dir = tmp_path / "spec-with-req"
        spec_dir.mkdir()
        (spec_dir / "requirements.md").write_text("# Requirements\n")

        status = get_spec_status(spec_dir)

        assert status == SpecStatus.REQUIREMENTS_DRAFT


class TestExtractGuardrailMatrixEdgeCases:
    """Edge case tests for extract_guardrail_matrix."""

    def test_handles_guardrail_without_id_prefix(self):
        """Test handling guardrail rows without ID prefix."""
        content = """## Guardrail Coverage Matrix

| Guardrail | Requirements | Design | Tasks/Tests | Owner | Status |
|-----------|--------------|--------|-------------|-------|--------|
| Testing Coverage | [US-1] | [S1] | [T-1] | Dev | TODO |
"""
        matrix = extract_guardrail_matrix(content)

        assert len(matrix) == 1
        assert matrix[0].guardrail_id == 0  # No ID prefix found
        assert matrix[0].guardrail_name == "Testing Coverage"


class TestExtractTasksEdgeCases:
    """Edge case tests for extract_tasks."""

    def test_status_from_subtask_checkboxes(self):
        """Test that status is determined from subtask checkboxes."""
        content = """## Tasks

- [x] **Task 1.1:** Done task
  - [x] Step one completed

- [ ] **Task 1.2:** Mixed task
  - [x] Step one done
  - [ ] Step two pending
"""
        tasks = extract_tasks(content)

        assert len(tasks) == 2
        assert tasks[0].status == "complete"
        assert tasks[1].status == "in_progress"

    def test_uppercase_checkbox_markers(self):
        """Test that uppercase X in checkbox is recognized."""
        content = """## Tasks

- [X] **Task 1.1:** Done with uppercase X
  - [X] Step one
  - [X] Step two
"""
        tasks = extract_tasks(content)

        assert len(tasks) == 1
        assert tasks[0].status == "complete"


class TestApprovalDetection:
    """Tests for approval status detection in spec parsing."""

    def test_detects_requirements_approval_checkbox(self, tmp_path: Path):
        """Test detection of requirements approval via checkbox format."""
        spec_dir = tmp_path / "approved-req-spec"
        spec_dir.mkdir()
        (spec_dir / "requirements.md").write_text("""# Requirements

## Question-Pack Answers
Answers here.

## Guardrail Coverage Matrix

| Guardrail | Requirements | Design | Tasks/Tests | Owner | Status |
|-----------|--------------|--------|-------------|-------|--------|
| 1. Testing | [US-1] | [S1] | [T-1] | Dev | TODO |

## Approval
- [x] Requirements approved
""")

        spec_info = parse_spec(spec_dir)

        assert spec_info.requirements_approved is True
        assert spec_info.status == SpecStatus.REQUIREMENTS_APPROVED

    def test_detects_design_approval_checkbox(self, tmp_path: Path):
        """Test detection of design approval via checkbox format."""
        spec_dir = tmp_path / "approved-design-spec"
        spec_dir.mkdir()
        (spec_dir / "requirements.md").write_text("""# Requirements

## Question-Pack Answers
Answers.

## Guardrail Coverage Matrix
| Guardrail | Requirements | Design | Tasks/Tests | Owner | Status |
|-----------|--------------|--------|-------------|-------|--------|
| 1. Testing | [US-1] | [S1] | [T-1] | Dev | TODO |

Status: Approved
""")
        (spec_dir / "design.md").write_text("""# Design

## Guardrail Mapping
Mapping here.

## Approval
- [x] Design approved
""")

        spec_info = parse_spec(spec_dir)

        assert spec_info.design_approved is True

    def test_detects_tasks_approval_checkbox(self, tmp_path: Path):
        """Test detection of tasks approval via checkbox format."""
        spec_dir = tmp_path / "approved-tasks-spec"
        spec_dir.mkdir()
        (spec_dir / "requirements.md").write_text("""# Requirements

## Question-Pack Answers
Answers.

## Guardrail Coverage Matrix
| Guardrail | Requirements | Design | Tasks/Tests | Owner | Status |
|-----------|--------------|--------|-------------|-------|--------|
| 1. Testing | [US-1] | [S1] | [T-1] | Dev | TODO |

Status: Approved
""")
        (spec_dir / "design.md").write_text("""# Design

## Guardrail Mapping
Mapping.

Status: Approved
""")
        (spec_dir / "tasks.md").write_text("""# Tasks

## Per-Task Guardrail Checklist
Checklist here.

- [ ] **Task 1.1:** Do something
  - [ ] Step one

## Approval
- [x] Tasks approved
""")

        spec_info = parse_spec(spec_dir)

        assert spec_info.tasks_approved is True


class TestDetermineStatus:
    """Tests for _determine_status function."""

    def test_requirements_approved_no_design(self):
        """Test REQUIREMENTS_APPROVED when no design exists."""
        info = SpecInfo(
            name="test",
            status=SpecStatus.NOT_STARTED,
            has_requirements=True,
            requirements_approved=True,
            has_design=False,
        )

        status = _determine_status(info)

        assert status == SpecStatus.REQUIREMENTS_APPROVED

    def test_design_draft(self):
        """Test DESIGN_DRAFT when design not approved."""
        info = SpecInfo(
            name="test",
            status=SpecStatus.NOT_STARTED,
            has_requirements=True,
            requirements_approved=True,
            has_design=True,
            design_approved=False,
        )

        status = _determine_status(info)

        assert status == SpecStatus.DESIGN_DRAFT

    def test_design_approved_no_tasks(self):
        """Test DESIGN_APPROVED when no tasks exist."""
        info = SpecInfo(
            name="test",
            status=SpecStatus.NOT_STARTED,
            has_requirements=True,
            requirements_approved=True,
            has_design=True,
            design_approved=True,
            has_tasks=False,
        )

        status = _determine_status(info)

        assert status == SpecStatus.DESIGN_APPROVED

    def test_tasks_draft(self):
        """Test TASKS_DRAFT when tasks not approved."""
        info = SpecInfo(
            name="test",
            status=SpecStatus.NOT_STARTED,
            has_requirements=True,
            requirements_approved=True,
            has_design=True,
            design_approved=True,
            has_tasks=True,
            tasks_approved=False,
        )

        status = _determine_status(info)

        assert status == SpecStatus.TASKS_DRAFT

    def test_tasks_approved_no_tasks_list(self):
        """Test TASKS_APPROVED when approved but no tasks in list."""
        info = SpecInfo(
            name="test",
            status=SpecStatus.NOT_STARTED,
            has_requirements=True,
            requirements_approved=True,
            has_design=True,
            design_approved=True,
            has_tasks=True,
            tasks_approved=True,
            tasks=[],
        )

        status = _determine_status(info)

        assert status == SpecStatus.TASKS_APPROVED

    def test_in_progress_some_tasks_complete(self):
        """Test IN_PROGRESS when some tasks are complete."""
        from ldf.utils.spec_parser import TaskItem

        info = SpecInfo(
            name="test",
            status=SpecStatus.NOT_STARTED,
            has_requirements=True,
            requirements_approved=True,
            has_design=True,
            design_approved=True,
            has_tasks=True,
            tasks_approved=True,
            tasks=[
                TaskItem(id="1.1", title="Task 1", status="complete"),
                TaskItem(id="1.2", title="Task 2", status="pending"),
            ],
        )

        status = _determine_status(info)

        assert status == SpecStatus.IN_PROGRESS

    def test_complete_all_tasks_done(self):
        """Test COMPLETE when all tasks are complete."""
        from ldf.utils.spec_parser import TaskItem

        info = SpecInfo(
            name="test",
            status=SpecStatus.NOT_STARTED,
            has_requirements=True,
            requirements_approved=True,
            has_design=True,
            design_approved=True,
            has_tasks=True,
            tasks_approved=True,
            tasks=[
                TaskItem(id="1.1", title="Task 1", status="complete"),
                TaskItem(id="1.2", title="Task 2", status="complete"),
            ],
        )

        status = _determine_status(info)

        assert status == SpecStatus.COMPLETE
