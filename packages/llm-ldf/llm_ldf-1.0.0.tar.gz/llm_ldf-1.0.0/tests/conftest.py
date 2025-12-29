"""Pytest configuration and fixtures for LDF tests."""

from pathlib import Path

import pytest


@pytest.fixture
def temp_project(tmp_path: Path) -> Path:
    """Create a temporary project directory with LDF initialized."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    # Create .ldf directory structure
    ldf_dir = project_dir / ".ldf"
    ldf_dir.mkdir()

    specs_dir = ldf_dir / "specs"
    specs_dir.mkdir()

    # Create config.yaml
    config_file = ldf_dir / "config.yaml"
    config_file.write_text("""version: "1.0"

project:
  name: "test-project"
  type: "api"

guardrails:
  preset: core
  custom: []

question_packs:
  - core/security
  - core/testing

coverage:
  default_threshold: 80
  critical_threshold: 90
""")

    # Create guardrails.yaml
    guardrails_file = ldf_dir / "guardrails.yaml"
    guardrails_file.write_text("""version: "1.0"
extends: core
""")

    return project_dir


@pytest.fixture
def temp_spec(temp_project: Path) -> Path:
    """Create a temporary spec directory with all three phases."""
    spec_dir = temp_project / ".ldf" / "specs" / "test-feature"
    spec_dir.mkdir(parents=True)

    # Create requirements.md
    requirements = spec_dir / "requirements.md"
    requirements.write_text("""# test-feature - Requirements

## Overview

Test feature for unit tests.

## User Stories

### US-1: Test Story

**As a** user
**I want to** test something
**So that** I can verify it works

**Acceptance Criteria:**
- [ ] AC-1.1: Test passes

## Question-Pack Answers

### Security

**Authentication:**
- Method: JWT tokens

### Testing

**Coverage Requirements:**
- Overall: 80%

## Guardrail Coverage Matrix

| Guardrail | Requirements | Design | Tasks/Tests | Owner | Status |
|-----------|--------------|--------|-------------|-------|--------|
| 1. Testing Coverage | [US-1] | [S1.1] | [T-1.1] | Dev | TODO |
| 2. Security Basics | [US-1] | [S1.2] | [T-1.2] | Dev | TODO |
| 3. Error Handling | [US-1] | [S1.3] | [T-1.3] | Dev | TODO |
| 4. Logging & Observability | [US-1] | [S1.4] | [T-1.4] | Dev | TODO |
| 5. API Design | [US-1] | [S1.5] | [T-1.5] | Dev | TODO |
| 6. Data Validation | [US-1] | [S1.6] | [T-1.6] | Dev | TODO |
| 7. Database Migrations | [US-1] | [S1.7] | [T-1.7] | Dev | TODO |
| 8. Documentation | [US-1] | [S1.8] | [T-1.8] | Dev | TODO |
""")

    # Create design.md
    design = spec_dir / "design.md"
    design.write_text("""# test-feature - Design

## Architecture Overview

Simple test architecture.

## S1: Data Layer

### S1.1: Database Schema

Test schema.

## S2: API Layer

### S2.1: API Endpoints

Test endpoints.

## Guardrail Mapping

| Guardrail | Implementation | Section |
|-----------|---------------|---------|
| 1. Testing | Unit tests | S1.1 |
""")

    # Create tasks.md
    tasks = spec_dir / "tasks.md"
    tasks.write_text("""# test-feature - Tasks

**Status:** Ready for Implementation
**Total Tasks:** 2
**Completed:** 0

## Per-Task Guardrail Checklist

**Reference:** `.ldf/guardrails.yaml`

Before implementing each task, verify applicable guardrails:

- [ ] **1. Testing Coverage:** Unit tests
- [ ] **2. Security Basics:** Input validation
- [ ] **3. Error Handling:** Consistent errors
- [ ] **4. Logging & Observability:** Structured logging
- [ ] **5. API Design:** RESTful
- [ ] **6. Data Validation:** Schema validation
- [ ] **7. Database Migrations:** Reversible
- [ ] **8. Documentation:** API docs

---

## Phase 1: Setup

- [ ] **Task 1.1:** Create project structure
  - [ ] Create directories

- [ ] **Task 1.2:** Implement feature
  - [ ] Implement logic
  - [ ] Write tests
""")

    return spec_dir


@pytest.fixture
def ldf_framework_path() -> Path:
    """Return path to the LDF framework directory."""
    return Path(__file__).parent.parent / "ldf" / "_framework"


@pytest.fixture
def temp_project_with_specs(temp_project: Path) -> Path:
    """Create temp project with multiple specs for audit testing."""
    specs_dir = temp_project / ".ldf" / "specs"

    for spec_name in ["feature-a", "feature-b"]:
        spec_dir = specs_dir / spec_name
        spec_dir.mkdir(parents=True)

        (spec_dir / "requirements.md").write_text(f"""# {spec_name} - Requirements

## Overview

Test feature {spec_name}.

## Question-Pack Answers

### Security

**API Key:** sk-test-12345678901234567890

## Guardrail Coverage Matrix

| Guardrail | Requirements | Design | Tasks/Tests | Owner | Status |
|-----------|--------------|--------|-------------|-------|--------|
| 1. Testing | [US-1] | [S1] | [T-1] | Dev | TODO |
""")
        (spec_dir / "design.md").write_text(f"# {spec_name} - Design\n\n## API\n\nTest")
        (spec_dir / "tasks.md").write_text(
            f"# {spec_name} - Tasks\n\n## Phase 1\n\n### Task 1.1\n- [ ] Test"
        )

    return temp_project


@pytest.fixture
def sample_pytest_coverage_json() -> dict:
    """Sample pytest-cov format coverage data."""
    return {
        "totals": {"covered_lines": 850, "num_statements": 1000, "percent_covered": 85.0},
        "files": {
            "src/services/auth.py": {
                "summary": {"covered_lines": 90, "num_statements": 100, "percent_covered": 90.0},
                "missing_lines": [45, 67],
            },
            "src/services/billing.py": {
                "summary": {"covered_lines": 70, "num_statements": 100, "percent_covered": 70.0},
                "missing_lines": [10, 20, 30],
            },
        },
    }


@pytest.fixture
def sample_jest_coverage_json() -> dict:
    """Sample Jest coverage-summary.json format."""
    return {
        "total": {"lines": {"total": 500, "covered": 400, "pct": 80.0}},
        "/src/components/Auth.tsx": {"lines": {"total": 100, "covered": 95, "pct": 95.0}},
    }


@pytest.fixture
def temp_feedback_file(tmp_path: Path) -> Path:
    """Create a temporary feedback markdown file."""
    feedback = tmp_path / "feedback.md"
    feedback.write_text("""## Findings

### Critical Issues
- Issue 1: Missing input validation

### Suggestions
- Add more test coverage

## Summary
Overall the spec is good.
""")
    return feedback
