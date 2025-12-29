"""LDF spec linting with configurable guardrail validation."""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from rich.table import Table

from ldf import __version__
from ldf.utils.config import get_specs_dir, load_config
from ldf.utils.console import console
from ldf.utils.guardrail_loader import Guardrail, get_active_guardrails
from ldf.utils.security import SecurityError, is_safe_directory_entry, validate_spec_name
from ldf.utils.spec_parser import (
    extract_guardrail_matrix,
    extract_tasks,
    parse_spec,
)

# SARIF rule definitions - stable rule IDs for consistent reporting
SARIF_RULES = {
    "ldf/missing-file": {
        "id": "ldf/missing-file",
        "name": "MissingRequiredFile",
        "shortDescription": {"text": "Required spec file is missing"},
        "helpUri": "https://github.com/LLMdotInfo/ldf#spec-structure",
    },
    "ldf/missing-section": {
        "id": "ldf/missing-section",
        "name": "MissingRequiredSection",
        "shortDescription": {"text": "Required section is missing from spec file"},
        "helpUri": "https://github.com/LLMdotInfo/ldf#spec-sections",
    },
    "ldf/missing-guardrail-matrix": {
        "id": "ldf/missing-guardrail-matrix",
        "name": "MissingGuardrailCoverageMatrix",
        "shortDescription": {"text": "Guardrail coverage matrix is empty or missing entries"},
        "helpUri": "https://github.com/LLMdotInfo/ldf#guardrail-coverage",
    },
    "ldf/guardrail-not-covered": {
        "id": "ldf/guardrail-not-covered",
        "name": "GuardrailNotCovered",
        "shortDescription": {"text": "Active guardrail is not covered in the matrix"},
        "helpUri": "https://github.com/LLMdotInfo/ldf#guardrail-coverage",
    },
    "ldf/unfilled-answerpack": {
        "id": "ldf/unfilled-answerpack",
        "name": "UnfilledAnswerpack",
        "shortDescription": {"text": "Answerpack contains unfilled template markers"},
        "helpUri": "https://github.com/LLMdotInfo/ldf#answerpacks",
    },
    "ldf/missing-answerpack": {
        "id": "ldf/missing-answerpack",
        "name": "MissingAnswerpack",
        "shortDescription": {"text": "No answerpack found for spec"},
        "helpUri": "https://github.com/LLMdotInfo/ldf#answerpacks",
    },
    "ldf/incomplete-guardrail-row": {
        "id": "ldf/incomplete-guardrail-row",
        "name": "IncompleteGuardrailRow",
        "shortDescription": {"text": "Guardrail matrix row is incomplete"},
        "helpUri": "https://github.com/LLMdotInfo/ldf#guardrail-coverage",
    },
    "ldf/missing-task-checklist": {
        "id": "ldf/missing-task-checklist",
        "name": "MissingTaskChecklist",
        "shortDescription": {"text": "Task is missing checklist items"},
        "helpUri": "https://github.com/LLMdotInfo/ldf#tasks",
    },
    "ldf/parse-error": {
        "id": "ldf/parse-error",
        "name": "SpecParseError",
        "shortDescription": {"text": "Error parsing spec file"},
        "helpUri": "https://github.com/LLMdotInfo/ldf#spec-format",
    },
}


@dataclass
class LintResult:
    """Individual lint result with location info."""

    rule_id: str
    level: str  # "error" or "warning"
    message: str
    spec_name: str
    file_name: str | None = None
    line: int | None = None


@dataclass
class LintReport:
    """Complete lint report for SARIF generation."""

    results: list[LintResult] = field(default_factory=list)
    specs_checked: int = 0

    def add_error(
        self,
        rule_id: str,
        message: str,
        spec_name: str,
        file_name: str | None = None,
        line: int | None = None,
    ) -> None:
        """Add an error result."""
        self.results.append(
            LintResult(
                rule_id=rule_id,
                level="error",
                message=message,
                spec_name=spec_name,
                file_name=file_name,
                line=line,
            )
        )

    def add_warning(
        self,
        rule_id: str,
        message: str,
        spec_name: str,
        file_name: str | None = None,
        line: int | None = None,
    ) -> None:
        """Add a warning result."""
        self.results.append(
            LintResult(
                rule_id=rule_id,
                level="warning",
                message=message,
                spec_name=spec_name,
                file_name=file_name,
                line=line,
            )
        )

    @property
    def error_count(self) -> int:
        """Count of errors."""
        return sum(1 for r in self.results if r.level == "error")

    @property
    def warning_count(self) -> int:
        """Count of warnings."""
        return sum(1 for r in self.results if r.level == "warning")


def lint_specs(
    spec_name: str | None,
    lint_all: bool,
    fix: bool,
    output_format: str = "rich",
    output_file: str | None = None,
    verbose: bool = False,
) -> int:
    """Lint spec files against guardrail requirements.

    Args:
        spec_name: Name of specific spec to lint (or None for all)
        lint_all: Whether to lint all specs
        fix: Whether to auto-fix issues
        output_format: "rich" for terminal, "ci" for GitHub Actions, "sarif" for scanning
        output_file: Output file for sarif format (default: stdout)
        verbose: Show detailed per-file lint output with error messages

    Returns:
        Exit code (0 for success, 1 for failures)
    """
    project_root = Path.cwd()
    ci_mode = output_format == "ci"
    sarif_mode = output_format == "sarif"
    json_mode = output_format == "json"
    text_mode = output_format == "text"

    # Check if LDF is initialized
    ldf_dir = project_root / ".ldf"
    if not ldf_dir.exists():
        if sarif_mode:
            # Output empty SARIF with error
            sarif = _generate_sarif(LintReport(), project_root, init_error=".ldf/ not found")
            _output_sarif(sarif, output_file)
        elif json_mode:
            print(json.dumps({"error": ".ldf/ not found. Run 'ldf init' first.", "exit_code": 1}))
        elif ci_mode or text_mode:
            print("✗ Error: init: .ldf/ not found. Run 'ldf init' first.")
        else:
            console.print("[red]Error: .ldf/ not found. Run 'ldf init' first.[/red]")
        return 1

    specs_dir = get_specs_dir(project_root)

    if not specs_dir.exists():
        if sarif_mode:
            # Output empty SARIF (no issues)
            sarif = _generate_sarif(LintReport(), project_root)
            _output_sarif(sarif, output_file)
        elif ci_mode:
            print("✅ Pass: No specs directory found.")
        else:
            console.print(
                "[yellow]No specs directory found. "
                "Create specs with '/project:create-spec'.[/yellow]"
            )
        return 0

    # Load configuration
    try:
        config = load_config(project_root)
        strict_mode = config.get("lint", {}).get("strict", False)
    except FileNotFoundError:
        strict_mode = False

    # Load active guardrails
    active_guardrails = get_active_guardrails(project_root)
    if not ci_mode and not sarif_mode and not json_mode and not text_mode:
        console.print(f"\n[dim]Active guardrails: {len(active_guardrails)}[/dim]")

    # Find specs to lint
    if spec_name:
        # SECURITY: Validate spec_name to prevent path traversal
        try:
            spec_path = validate_spec_name(spec_name, specs_dir)
        except SecurityError as e:
            if sarif_mode:
                err = f"Invalid spec name: {e}"
                sarif = _generate_sarif(LintReport(), project_root, init_error=err)
                _output_sarif(sarif, output_file)
            elif ci_mode:
                print(f"✗ Error: {spec_name}: Security validation failed - {e}")
            else:
                console.print(f"[red]Error: {e}[/red]")
            return 1

        if not spec_path.exists():
            if sarif_mode:
                err = f"Spec not found: {spec_name}"
                sarif = _generate_sarif(LintReport(), project_root, init_error=err)
                _output_sarif(sarif, output_file)
            elif ci_mode:
                print(f"✗ Error: {spec_name}: Spec not found")
            else:
                console.print(f"[red]Error: Spec not found: {spec_name}[/red]")
            return 1
        specs = [spec_path]
    elif lint_all:
        # SECURITY: Filter out symlinks pointing outside specs_dir and hidden directories
        specs = [
            d for d in specs_dir.iterdir() if d.is_dir() and is_safe_directory_entry(d, specs_dir)
        ]
    else:
        if sarif_mode:
            err = "Specify a spec name or use --all"
            sarif = _generate_sarif(LintReport(), project_root, init_error=err)
            _output_sarif(sarif, output_file)
        elif ci_mode:
            print("✗ Error: cli: Specify a spec name or use --all to lint all specs.")
        else:
            console.print("[red]Error: Specify a spec name or use --all to lint all specs.[/red]")
            console.print("[dim]Usage: ldf lint <spec-name> or ldf lint --all[/dim]")
        return 1

    if not specs:
        if sarif_mode:
            sarif = _generate_sarif(LintReport(), project_root)
            _output_sarif(sarif, output_file)
        elif ci_mode:
            print("✅ Pass: No specs found to lint.")
        else:
            console.print("[yellow]No specs found to lint.[/yellow]")
        return 0

    # Lint each spec
    total_errors = 0
    total_warnings = 0
    results: list[tuple[str, list[str], list[str]]] = []
    lint_report = LintReport()

    for spec_path in specs:
        errors, warnings, spec_results = _lint_spec_with_report(
            spec_path, active_guardrails, fix, strict_mode, ci_mode, sarif_mode
        )
        total_errors += len(errors)
        total_warnings += len(warnings)
        results.append((spec_path.name, errors, warnings))
        lint_report.results.extend(spec_results)
        lint_report.specs_checked += 1

    # Print summary
    if sarif_mode:
        sarif = _generate_sarif(lint_report, project_root)
        _output_sarif(sarif, output_file)
    elif json_mode:
        _print_json_summary(results, total_errors, total_warnings, lint_report.specs_checked)
    elif text_mode:
        _print_text_summary(results, total_errors, total_warnings, verbose=verbose)
    elif ci_mode:
        _print_ci_summary(results, total_errors, total_warnings)
    else:
        _print_summary(results, total_errors, total_warnings, verbose=verbose)

    return 1 if total_errors > 0 else 0


def _lint_spec(
    spec_path: Path,
    guardrails: list[Guardrail],
    fix: bool,
    strict_mode: bool,
    ci_mode: bool = False,
) -> tuple[list[str], list[str]]:
    """Lint a single spec directory.

    Args:
        spec_path: Path to spec directory
        guardrails: List of active guardrails
        fix: Whether to auto-fix issues
        strict_mode: Treat warnings as errors
        ci_mode: Whether to use CI-friendly output

    Returns:
        Tuple of (errors, warnings)
    """
    errors = []
    warnings = []
    fixed_count = 0
    spec_name = spec_path.name

    if not ci_mode:
        console.print(f"\n[bold]Linting: {spec_name}[/bold]")

    # Check required files exist (and fix if requested)
    required_files = ["requirements.md", "design.md", "tasks.md"]
    for filename in required_files:
        filepath = spec_path / filename
        if not filepath.exists():
            if fix:
                # Create from template
                template_path = Path(__file__).parent / "_framework" / "templates" / filename
                if template_path.exists():
                    content = template_path.read_text()
                    # Replace placeholder with spec name
                    content = content.replace("{feature-name}", spec_name)
                    content = content.replace("{{feature-name}}", spec_name)
                    filepath.write_text(content)
                    fixed_count += 1
                    if not ci_mode:
                        console.print(f"  [green]FIXED[/green] Created missing {filename}")
                else:
                    errors.append(f"Missing file: {filename}")
            else:
                errors.append(f"Missing file: {filename}")

    # Parse the spec (re-parse after potential fixes)
    spec_info = parse_spec(spec_path)

    # Add parser errors/warnings
    errors.extend(spec_info.errors)
    warnings.extend(spec_info.warnings)

    # Fix trailing whitespace and missing final newlines
    if fix:
        for filename in required_files:
            filepath = spec_path / filename
            if filepath.exists():
                content = filepath.read_text()
                original = content

                # Remove trailing whitespace from each line
                lines = content.split("\n")
                lines = [line.rstrip() for line in lines]
                content = "\n".join(lines)

                # Ensure file ends with exactly one newline
                content = content.rstrip("\n") + "\n"

                if content != original:
                    filepath.write_text(content)
                    fixed_count += 1
                    if not ci_mode:
                        console.print(f"  [green]FIXED[/green] Cleaned whitespace in {filename}")

    if fix and fixed_count > 0 and not ci_mode:
        console.print(f"  [dim]Fixed {fixed_count} issue(s)[/dim]")

    # Validate requirements.md
    requirements_path = spec_path / "requirements.md"
    if requirements_path.exists():
        req_errors, req_warnings = _check_requirements(requirements_path, guardrails)
        errors.extend(req_errors)
        warnings.extend(req_warnings)

    # Validate design.md
    design_path = spec_path / "design.md"
    if design_path.exists():
        design_errors, design_warnings = _check_design(design_path, guardrails)
        errors.extend(design_errors)
        warnings.extend(design_warnings)

    # Validate tasks.md
    tasks_path = spec_path / "tasks.md"
    if tasks_path.exists():
        tasks_errors, tasks_warnings = _check_tasks(tasks_path, guardrails)
        errors.extend(tasks_errors)
        warnings.extend(tasks_warnings)

    # Check answerpacks
    answerpacks_errors, answerpacks_warnings = _check_answerpacks(spec_path)
    errors.extend(answerpacks_errors)
    warnings.extend(answerpacks_warnings)

    # Output results
    if ci_mode:
        # CI-friendly emoji-prefixed output for GitHub Actions parsing
        for error in errors:
            print(f"✗ Error: {spec_name}: {error}")
        for warning in warnings:
            print(f"⚠ Warning: {spec_name}: {warning}")
        if not errors and not warnings:
            print(f"✅ Pass: {spec_name}")
    else:
        for error in errors:
            console.print(f"  [red]ERROR[/red] {error}")
        for warning in warnings:
            console.print(f"  [yellow]WARN[/yellow] {warning}")
        if not errors and not warnings:
            console.print("  [green]PASSED[/green]")

    # In strict mode, treat warnings as errors
    if strict_mode:
        errors.extend(warnings)
        warnings = []

    return errors, warnings


def _check_requirements(filepath: Path, guardrails: list[Guardrail]) -> tuple[list[str], list[str]]:
    """Check requirements.md for required sections and guardrail coverage.

    Args:
        filepath: Path to requirements.md
        guardrails: List of active guardrails

    Returns:
        Tuple of (errors, warnings)
    """
    errors = []
    warnings = []
    content = filepath.read_text()

    # Required sections
    required_sections = [
        ("## Question-Pack Answers", "Question-Pack Answers section"),
        ("## Guardrail Coverage Matrix", "Guardrail Coverage Matrix"),
    ]

    for marker, name in required_sections:
        if marker not in content:
            errors.append(f"requirements.md: Missing {name}")

    # Check for user stories
    if "## User Stories" not in content and "### US-" not in content:
        warnings.append("requirements.md: No user stories found")

    # Validate guardrail coverage matrix
    if "## Guardrail Coverage Matrix" in content:
        matrix_errors, matrix_warnings = _validate_guardrail_matrix(content, guardrails)
        errors.extend(matrix_errors)
        warnings.extend(matrix_warnings)

    return errors, warnings


def _check_design(filepath: Path, guardrails: list[Guardrail]) -> tuple[list[str], list[str]]:
    """Check design.md for required sections.

    Args:
        filepath: Path to design.md
        guardrails: List of active guardrails

    Returns:
        Tuple of (errors, warnings)
    """
    errors: list[str] = []
    warnings: list[str] = []
    content = filepath.read_text()

    # Check for Guardrail Mapping section
    if "## Guardrail Mapping" not in content:
        warnings.append("design.md: Missing Guardrail Mapping section")

    # Check for architecture section
    if "## Architecture" not in content and "## Components" not in content:
        warnings.append("design.md: No Architecture or Components section")

    # Check for API endpoints or data model (at least one)
    # Flexible matching - look for API, Endpoint, Route in any header
    has_api = bool(re.search(r"##[#]?\s+.*\b(API|Endpoint|Route)", content, re.IGNORECASE))
    has_data = bool(re.search(r"##[#]?\s+.*\b(Data|Schema|Model|Database)", content, re.IGNORECASE))
    if not has_api and not has_data:
        warnings.append("design.md: No API or Data Model section found")

    return errors, warnings


def _check_tasks(filepath: Path, guardrails: list[Guardrail]) -> tuple[list[str], list[str]]:
    """Check tasks.md for required sections and per-task checklists.

    Args:
        filepath: Path to tasks.md
        guardrails: List of active guardrails

    Returns:
        Tuple of (errors, warnings)
    """
    errors = []
    warnings = []
    content = filepath.read_text()

    # Check for Per-Task Guardrail Checklist template
    if "## Per-Task Guardrail Checklist" not in content:
        errors.append("tasks.md: Missing Per-Task Guardrail Checklist")

    # Extract and validate tasks
    tasks = extract_tasks(content)

    if not tasks:
        warnings.append("tasks.md: No tasks found")
    else:
        # Check that each task section has checklist items
        for task in tasks:
            # Look for task section and check for checklist
            task_header = f"{task.id}"
            task_start = content.find(task_header)
            if task_start != -1:
                # Find next task or end
                next_task_pos = len(content)
                for other_task in tasks:
                    if other_task.id != task.id:
                        pos = content.find(other_task.id, task_start + 1)
                        if pos != -1 and pos < next_task_pos:
                            next_task_pos = pos

                task_section = content[task_start:next_task_pos]

                # Check for at least some checklist items
                if "- [ ]" not in task_section and "- [x]" not in task_section:
                    warnings.append(f"tasks.md: Task {task.id} has no checklist items")

    return errors, warnings


def _check_answerpacks(spec_path: Path) -> tuple[list[str], list[str]]:
    """Check answerpacks for the spec.

    Args:
        spec_path: Path to spec directory

    Returns:
        Tuple of (errors, warnings)
    """
    errors = []
    warnings = []

    # Check for answerpacks directory
    # SECURITY: spec_path.name is safe here because spec_path was validated via validate_spec_name
    answerpacks_dir = spec_path.parent.parent / "answerpacks" / spec_path.name
    if not answerpacks_dir.exists():
        warnings.append(f"No answerpacks found at .ldf/answerpacks/{spec_path.name}/")
    else:
        # Check for any YAML files
        yaml_files = list(answerpacks_dir.glob("*.yaml")) + list(answerpacks_dir.glob("*.yml"))
        if not yaml_files:
            warnings.append("Answerpacks directory exists but contains no YAML files")
        else:
            # Check for template markers in answerpacks
            for yaml_file in yaml_files:
                content = yaml_file.read_text()
                if "[TODO" in content or "[PLACEHOLDER" in content or "YOUR_" in content:
                    errors.append(f"Answerpack {yaml_file.name} contains unfilled template markers")

    return errors, warnings


def _validate_guardrail_matrix(
    content: str, guardrails: list[Guardrail]
) -> tuple[list[str], list[str]]:
    """Validate the guardrail coverage matrix against active guardrails.

    Args:
        content: Markdown content containing the matrix
        guardrails: List of active guardrails

    Returns:
        Tuple of (errors, warnings)
    """
    errors: list[str] = []
    warnings: list[str] = []

    matrix = extract_guardrail_matrix(content)

    if not matrix:
        errors.append("Guardrail coverage matrix is empty")
        return errors, warnings

    # Check that all active guardrails have entries
    matrix_ids = {row.guardrail_id for row in matrix}
    for guardrail in guardrails:
        if guardrail.id not in matrix_ids:
            # Try matching by name
            name_match = any(guardrail.name.lower() in row.guardrail_name.lower() for row in matrix)
            if not name_match:
                errors.append(
                    f"Guardrail #{guardrail.id} ({guardrail.name}) not in coverage matrix"
                )

    # Validate each matrix row
    for row in matrix:
        # Check for empty cells
        if not row.requirements_ref and row.status not in ["N/A", "n/a"]:
            warnings.append(f"Guardrail {row.guardrail_id}: Missing requirements reference")

        if not row.design_ref and row.status not in ["N/A", "n/a"]:
            warnings.append(f"Guardrail {row.guardrail_id}: Missing design reference")

        # Check N/A has justification
        if row.status.upper().startswith("N/A") and "-" not in row.status:
            # N/A without justification
            warnings.append(f"Guardrail {row.guardrail_id}: N/A status needs justification")

        # Check owner for non-N/A rows
        if row.status.upper() not in ["N/A"] and not row.owner:
            warnings.append(f"Guardrail {row.guardrail_id}: Missing owner")

    return errors, warnings


def _print_summary(
    results: list[tuple[str, list[str], list[str]]],
    total_errors: int,
    total_warnings: int,
    verbose: bool = False,
) -> None:
    """Print linting summary.

    Args:
        results: List of (spec_name, errors, warnings) tuples
        total_errors: Total error count
        total_warnings: Total warning count
        verbose: Show detailed per-file lint output with error messages
    """
    console.print()

    # Summary table
    table = Table(title="Lint Results", show_header=True, header_style="bold")
    table.add_column("Spec", style="cyan")
    table.add_column("Errors", justify="right")
    table.add_column("Warnings", justify="right")
    table.add_column("Status")

    for spec_name, errors, warnings in results:
        error_count = len(errors)
        warning_count = len(warnings)

        if error_count > 0:
            status = "[red]FAILED[/red]"
        elif warning_count > 0:
            status = "[yellow]WARNINGS[/yellow]"
        else:
            status = "[green]PASSED[/green]"

        table.add_row(
            spec_name,
            str(error_count) if error_count > 0 else "-",
            str(warning_count) if warning_count > 0 else "-",
            status,
        )

    console.print(table)

    # Verbose mode: show detailed errors and warnings per spec
    if verbose:
        for spec_name, errors, warnings in results:
            if errors or warnings:
                console.print(f"\n[bold]{spec_name}[/bold]")
                for error in errors:
                    console.print(f"  [red]error:[/red] {error}")
                for warning in warnings:
                    console.print(f"  [yellow]warning:[/yellow] {warning}")

    # Overall status
    console.print()
    if total_errors == 0 and total_warnings == 0:
        console.print("[bold green]All specs passed validation![/bold green]")
    else:
        if total_errors > 0:
            console.print(f"[bold red]Total errors: {total_errors}[/bold red]")
        if total_warnings > 0:
            console.print(f"[bold yellow]Total warnings: {total_warnings}[/bold yellow]")


def _print_ci_summary(
    results: list[tuple[str, list[str], list[str]]],
    total_errors: int,
    total_warnings: int,
) -> None:
    """Print CI-friendly linting summary.

    Args:
        results: List of (spec_name, errors, warnings) tuples
        total_errors: Total error count
        total_warnings: Total warning count
    """
    print()
    print("=" * 50)
    print("LINT SUMMARY")
    print("=" * 50)

    for spec_name, errors, warnings in results:
        error_count = len(errors)
        warning_count = len(warnings)

        if error_count > 0:
            print(f"❌ {spec_name}: {error_count} error(s), {warning_count} warning(s)")
        elif warning_count > 0:
            print(f"⚠️  {spec_name}: {warning_count} warning(s)")
        else:
            print(f"✅ {spec_name}: PASSED")

    print("=" * 50)
    if total_errors == 0 and total_warnings == 0:
        print("✅ All specs passed validation!")
    else:
        if total_errors > 0:
            print(f"❌ Total errors: {total_errors}")
        if total_warnings > 0:
            print(f"⚠️  Total warnings: {total_warnings}")


def _print_json_summary(
    results: list[tuple[str, list[str], list[str]]],
    total_errors: int,
    total_warnings: int,
    specs_checked: int,
) -> None:
    """Print JSON-formatted linting summary.

    Args:
        results: List of (spec_name, errors, warnings) tuples
        total_errors: Total error count
        total_warnings: Total warning count
        specs_checked: Number of specs checked
    """
    specs_results = []
    for spec_name, errors, warnings in results:
        specs_results.append({
            "spec": spec_name,
            "errors": errors,
            "warnings": warnings,
            "passed": len(errors) == 0 and len(warnings) == 0,
        })

    output = {
        "specs_checked": specs_checked,
        "total_errors": total_errors,
        "total_warnings": total_warnings,
        "passed": total_errors == 0,
        "specs": specs_results,
    }

    print(json.dumps(output, indent=2))


def _print_text_summary(
    results: list[tuple[str, list[str], list[str]]],
    total_errors: int,
    total_warnings: int,
    verbose: bool = False,
) -> None:
    """Print plain text linting summary.

    Args:
        results: List of (spec_name, errors, warnings) tuples
        total_errors: Total error count
        total_warnings: Total warning count
        verbose: Show detailed per-file lint output with error messages
    """
    print()
    print("=" * 50)
    print("LINT SUMMARY")
    print("=" * 50)

    for spec_name, errors, warnings in results:
        error_count = len(errors)
        warning_count = len(warnings)

        if error_count > 0:
            status = f"FAIL ({error_count} error(s), {warning_count} warning(s))"
            print(f"{spec_name}: {status}")
            if verbose:
                for err in errors:
                    print(f"  ERROR: {err}")
                for warn in warnings:
                    print(f"  WARNING: {warn}")
        elif warning_count > 0:
            status = f"WARN ({warning_count} warning(s))"
            print(f"{spec_name}: {status}")
            if verbose:
                for warn in warnings:
                    print(f"  WARNING: {warn}")
        else:
            print(f"{spec_name}: PASS")

    print("=" * 50)
    if total_errors == 0 and total_warnings == 0:
        print("Result: All specs passed validation")
    else:
        print(f"Result: {total_errors} error(s), {total_warnings} warning(s)")


def _lint_spec_with_report(
    spec_path: Path,
    guardrails: list[Guardrail],
    fix: bool,
    strict_mode: bool,
    ci_mode: bool = False,
    sarif_mode: bool = False,
) -> tuple[list[str], list[str], list[LintResult]]:
    """Lint a single spec directory with detailed reporting.

    Args:
        spec_path: Path to spec directory
        guardrails: List of active guardrails
        fix: Whether to auto-fix issues
        strict_mode: Treat warnings as errors
        ci_mode: Whether to use CI-friendly output
        sarif_mode: Whether outputting SARIF (suppress console output)

    Returns:
        Tuple of (errors, warnings, lint_results)
    """
    errors: list[str] = []
    warnings: list[str] = []
    results: list[LintResult] = []
    fixed_count = 0
    spec_name = spec_path.name

    if not ci_mode and not sarif_mode:
        console.print(f"\n[bold]Linting: {spec_name}[/bold]")

    # Check required files exist (and fix if requested)
    required_files = ["requirements.md", "design.md", "tasks.md"]
    for filename in required_files:
        filepath = spec_path / filename
        if not filepath.exists():
            if fix:
                # Create from template
                template_path = Path(__file__).parent / "_framework" / "templates" / filename
                if template_path.exists():
                    content = template_path.read_text()
                    # Replace placeholder with spec name
                    content = content.replace("{feature-name}", spec_name)
                    content = content.replace("{{feature-name}}", spec_name)
                    filepath.write_text(content)
                    fixed_count += 1
                    if not ci_mode and not sarif_mode:
                        console.print(f"  [green]FIXED[/green] Created missing {filename}")
                else:
                    msg = f"Missing file: {filename}"
                    errors.append(msg)
                    results.append(
                        LintResult(
                            rule_id="ldf/missing-file",
                            level="error",
                            message=msg,
                            spec_name=spec_name,
                            file_name=filename,
                        )
                    )
            else:
                msg = f"Missing file: {filename}"
                errors.append(msg)
                results.append(
                    LintResult(
                        rule_id="ldf/missing-file",
                        level="error",
                        message=msg,
                        spec_name=spec_name,
                        file_name=filename,
                    )
                )

    # Parse the spec (re-parse after potential fixes)
    spec_info = parse_spec(spec_path)

    # Add parser errors/warnings
    for err in spec_info.errors:
        errors.append(err)
        results.append(
            LintResult(
                rule_id="ldf/parse-error",
                level="error",
                message=err,
                spec_name=spec_name,
            )
        )
    for warn in spec_info.warnings:
        warnings.append(warn)
        results.append(
            LintResult(
                rule_id="ldf/parse-error",
                level="warning",
                message=warn,
                spec_name=spec_name,
            )
        )

    # Fix trailing whitespace and missing final newlines
    if fix:
        for filename in required_files:
            filepath = spec_path / filename
            if filepath.exists():
                content = filepath.read_text()
                original = content

                # Remove trailing whitespace from each line
                lines = content.split("\n")
                lines = [line.rstrip() for line in lines]
                content = "\n".join(lines)

                # Ensure file ends with exactly one newline
                content = content.rstrip("\n") + "\n"

                if content != original:
                    filepath.write_text(content)
                    fixed_count += 1
                    if not ci_mode and not sarif_mode:
                        console.print(f"  [green]FIXED[/green] Cleaned whitespace in {filename}")

    if fix and fixed_count > 0 and not ci_mode and not sarif_mode:
        console.print(f"  [dim]Fixed {fixed_count} issue(s)[/dim]")

    # Validate requirements.md
    requirements_path = spec_path / "requirements.md"
    if requirements_path.exists():
        req_errors, req_warnings, req_results = _check_requirements_with_report(
            requirements_path, guardrails, spec_name
        )
        errors.extend(req_errors)
        warnings.extend(req_warnings)
        results.extend(req_results)

    # Validate design.md
    design_path = spec_path / "design.md"
    if design_path.exists():
        design_errors, design_warnings, design_results = _check_design_with_report(
            design_path, guardrails, spec_name
        )
        errors.extend(design_errors)
        warnings.extend(design_warnings)
        results.extend(design_results)

    # Validate tasks.md
    tasks_path = spec_path / "tasks.md"
    if tasks_path.exists():
        tasks_errors, tasks_warnings, tasks_results = _check_tasks_with_report(
            tasks_path, guardrails, spec_name
        )
        errors.extend(tasks_errors)
        warnings.extend(tasks_warnings)
        results.extend(tasks_results)

    # Check answerpacks
    ap_errors, ap_warnings, ap_results = _check_answerpacks_with_report(spec_path, spec_name)
    errors.extend(ap_errors)
    warnings.extend(ap_warnings)
    results.extend(ap_results)

    # Output results (non-SARIF modes)
    if ci_mode:
        # CI-friendly emoji-prefixed output for GitHub Actions parsing
        for error in errors:
            print(f"✗ Error: {spec_name}: {error}")
        for warning in warnings:
            print(f"⚠ Warning: {spec_name}: {warning}")
        if not errors and not warnings:
            print(f"✅ Pass: {spec_name}")
    elif not sarif_mode:
        for error in errors:
            console.print(f"  [red]ERROR[/red] {error}")
        for warning in warnings:
            console.print(f"  [yellow]WARN[/yellow] {warning}")
        if not errors and not warnings:
            console.print("  [green]PASSED[/green]")

    # In strict mode, treat warnings as errors
    if strict_mode:
        errors.extend(warnings)
        warnings = []

    return errors, warnings, results


def _check_requirements_with_report(
    filepath: Path, guardrails: list[Guardrail], spec_name: str
) -> tuple[list[str], list[str], list[LintResult]]:
    """Check requirements.md with detailed reporting."""
    errors: list[str] = []
    warnings: list[str] = []
    results: list[LintResult] = []
    content = filepath.read_text()

    # Required sections
    required_sections = [
        ("## Question-Pack Answers", "Question-Pack Answers section"),
        ("## Guardrail Coverage Matrix", "Guardrail Coverage Matrix"),
    ]

    for marker, name in required_sections:
        if marker not in content:
            msg = f"requirements.md: Missing {name}"
            errors.append(msg)
            results.append(
                LintResult(
                    rule_id="ldf/missing-section",
                    level="error",
                    message=msg,
                    spec_name=spec_name,
                    file_name="requirements.md",
                )
            )

    # Check for user stories
    if "## User Stories" not in content and "### US-" not in content:
        msg = "requirements.md: No user stories found"
        warnings.append(msg)
        results.append(
            LintResult(
                rule_id="ldf/missing-section",
                level="warning",
                message=msg,
                spec_name=spec_name,
                file_name="requirements.md",
            )
        )

    # Validate guardrail coverage matrix
    if "## Guardrail Coverage Matrix" in content:
        matrix_errors, matrix_warnings, matrix_results = _validate_guardrail_matrix_with_report(
            content, guardrails, spec_name
        )
        errors.extend(matrix_errors)
        warnings.extend(matrix_warnings)
        results.extend(matrix_results)

    return errors, warnings, results


def _check_design_with_report(
    filepath: Path, guardrails: list[Guardrail], spec_name: str
) -> tuple[list[str], list[str], list[LintResult]]:
    """Check design.md with detailed reporting."""
    errors: list[str] = []
    warnings: list[str] = []
    results: list[LintResult] = []
    content = filepath.read_text()

    # Check for Guardrail Mapping section
    if "## Guardrail Mapping" not in content:
        msg = "design.md: Missing Guardrail Mapping section"
        warnings.append(msg)
        results.append(
            LintResult(
                rule_id="ldf/missing-section",
                level="warning",
                message=msg,
                spec_name=spec_name,
                file_name="design.md",
            )
        )

    # Check for architecture section
    if "## Architecture" not in content and "## Components" not in content:
        msg = "design.md: No Architecture or Components section"
        warnings.append(msg)
        results.append(
            LintResult(
                rule_id="ldf/missing-section",
                level="warning",
                message=msg,
                spec_name=spec_name,
                file_name="design.md",
            )
        )

    # Check for API endpoints or data model (at least one)
    has_api = bool(re.search(r"##[#]?\s+.*\b(API|Endpoint|Route)", content, re.IGNORECASE))
    has_data = bool(re.search(r"##[#]?\s+.*\b(Data|Schema|Model|Database)", content, re.IGNORECASE))
    if not has_api and not has_data:
        msg = "design.md: No API or Data Model section found"
        warnings.append(msg)
        results.append(
            LintResult(
                rule_id="ldf/missing-section",
                level="warning",
                message=msg,
                spec_name=spec_name,
                file_name="design.md",
            )
        )

    return errors, warnings, results


def _check_tasks_with_report(
    filepath: Path, guardrails: list[Guardrail], spec_name: str
) -> tuple[list[str], list[str], list[LintResult]]:
    """Check tasks.md with detailed reporting."""
    errors: list[str] = []
    warnings: list[str] = []
    results: list[LintResult] = []
    content = filepath.read_text()

    # Check for Per-Task Guardrail Checklist template
    if "## Per-Task Guardrail Checklist" not in content:
        msg = "tasks.md: Missing Per-Task Guardrail Checklist"
        errors.append(msg)
        results.append(
            LintResult(
                rule_id="ldf/missing-section",
                level="error",
                message=msg,
                spec_name=spec_name,
                file_name="tasks.md",
            )
        )

    # Extract and validate tasks
    tasks = extract_tasks(content)

    if not tasks:
        msg = "tasks.md: No tasks found"
        warnings.append(msg)
        results.append(
            LintResult(
                rule_id="ldf/missing-section",
                level="warning",
                message=msg,
                spec_name=spec_name,
                file_name="tasks.md",
            )
        )
    else:
        # Check that each task section has checklist items
        for task in tasks:
            # Look for task section and check for checklist
            task_header = f"{task.id}"
            task_start = content.find(task_header)
            if task_start != -1:
                # Find next task or end
                next_task_pos = len(content)
                for other_task in tasks:
                    if other_task.id != task.id:
                        pos = content.find(other_task.id, task_start + 1)
                        if pos != -1 and pos < next_task_pos:
                            next_task_pos = pos

                task_section = content[task_start:next_task_pos]

                # Check for at least some checklist items
                if "- [ ]" not in task_section and "- [x]" not in task_section:
                    msg = f"tasks.md: Task {task.id} has no checklist items"
                    warnings.append(msg)
                    results.append(
                        LintResult(
                            rule_id="ldf/missing-task-checklist",
                            level="warning",
                            message=msg,
                            spec_name=spec_name,
                            file_name="tasks.md",
                        )
                    )

    return errors, warnings, results


def _check_answerpacks_with_report(
    spec_path: Path, spec_name: str
) -> tuple[list[str], list[str], list[LintResult]]:
    """Check answerpacks with detailed reporting."""
    errors: list[str] = []
    warnings: list[str] = []
    results: list[LintResult] = []

    # Check for answerpacks directory
    # SECURITY: spec_path.name is safe here because spec_path was validated via validate_spec_name
    answerpacks_dir = spec_path.parent.parent / "answerpacks" / spec_path.name
    if not answerpacks_dir.exists():
        msg = f"No answerpacks found at .ldf/answerpacks/{spec_path.name}/"
        warnings.append(msg)
        results.append(
            LintResult(
                rule_id="ldf/missing-answerpack",
                level="warning",
                message=msg,
                spec_name=spec_name,
            )
        )
    else:
        # Check for any YAML files
        yaml_files = list(answerpacks_dir.glob("*.yaml")) + list(answerpacks_dir.glob("*.yml"))
        if not yaml_files:
            msg = "Answerpacks directory exists but contains no YAML files"
            warnings.append(msg)
            results.append(
                LintResult(
                    rule_id="ldf/missing-answerpack",
                    level="warning",
                    message=msg,
                    spec_name=spec_name,
                )
            )
        else:
            # Check for template markers in answerpacks
            for yaml_file in yaml_files:
                content = yaml_file.read_text()
                if "[TODO" in content or "[PLACEHOLDER" in content or "YOUR_" in content:
                    msg = f"Answerpack {yaml_file.name} contains unfilled template markers"
                    errors.append(msg)
                    results.append(
                        LintResult(
                            rule_id="ldf/unfilled-answerpack",
                            level="error",
                            message=msg,
                            spec_name=spec_name,
                            file_name=yaml_file.name,
                        )
                    )

    return errors, warnings, results


def _validate_guardrail_matrix_with_report(
    content: str, guardrails: list[Guardrail], spec_name: str
) -> tuple[list[str], list[str], list[LintResult]]:
    """Validate the guardrail coverage matrix with detailed reporting."""
    errors: list[str] = []
    warnings: list[str] = []
    results: list[LintResult] = []

    matrix = extract_guardrail_matrix(content)

    if not matrix:
        msg = "Guardrail coverage matrix is empty"
        errors.append(msg)
        results.append(
            LintResult(
                rule_id="ldf/missing-guardrail-matrix",
                level="error",
                message=msg,
                spec_name=spec_name,
                file_name="requirements.md",
            )
        )
        return errors, warnings, results

    # Check that all active guardrails have entries
    matrix_ids = {row.guardrail_id for row in matrix}
    for guardrail in guardrails:
        if guardrail.id not in matrix_ids:
            # Try matching by name
            name_match = any(guardrail.name.lower() in row.guardrail_name.lower() for row in matrix)
            if not name_match:
                msg = f"Guardrail #{guardrail.id} ({guardrail.name}) not in coverage matrix"
                errors.append(msg)
                results.append(
                    LintResult(
                        rule_id="ldf/guardrail-not-covered",
                        level="error",
                        message=msg,
                        spec_name=spec_name,
                        file_name="requirements.md",
                    )
                )

    # Validate each matrix row
    for row in matrix:
        # Check for empty cells
        if not row.requirements_ref and row.status not in ["N/A", "n/a"]:
            msg = f"Guardrail {row.guardrail_id}: Missing requirements reference"
            warnings.append(msg)
            results.append(
                LintResult(
                    rule_id="ldf/incomplete-guardrail-row",
                    level="warning",
                    message=msg,
                    spec_name=spec_name,
                    file_name="requirements.md",
                )
            )

        if not row.design_ref and row.status not in ["N/A", "n/a"]:
            msg = f"Guardrail {row.guardrail_id}: Missing design reference"
            warnings.append(msg)
            results.append(
                LintResult(
                    rule_id="ldf/incomplete-guardrail-row",
                    level="warning",
                    message=msg,
                    spec_name=spec_name,
                    file_name="requirements.md",
                )
            )

        # Check N/A has justification
        if row.status.upper().startswith("N/A") and "-" not in row.status:
            msg = f"Guardrail {row.guardrail_id}: N/A status needs justification"
            warnings.append(msg)
            results.append(
                LintResult(
                    rule_id="ldf/incomplete-guardrail-row",
                    level="warning",
                    message=msg,
                    spec_name=spec_name,
                    file_name="requirements.md",
                )
            )

        # Check owner for non-N/A rows
        if row.status.upper() not in ["N/A"] and not row.owner:
            msg = f"Guardrail {row.guardrail_id}: Missing owner"
            warnings.append(msg)
            results.append(
                LintResult(
                    rule_id="ldf/incomplete-guardrail-row",
                    level="warning",
                    message=msg,
                    spec_name=spec_name,
                    file_name="requirements.md",
                )
            )

    return errors, warnings, results


def _generate_sarif(
    report: LintReport,
    project_root: Path,
    init_error: str | None = None,
) -> dict[str, Any]:
    """Generate SARIF 2.1.0 output from lint report.

    Args:
        report: LintReport with results
        project_root: Project root for artifact URIs
        init_error: Optional initialization error

    Returns:
        SARIF 2.1.0 compliant dictionary
    """
    # Collect used rule IDs
    used_rules = set()
    for result in report.results:
        used_rules.add(result.rule_id)

    # Build rules array
    rules = []
    for rule_id in sorted(used_rules):
        if rule_id in SARIF_RULES:
            rules.append(SARIF_RULES[rule_id])

    # Build results array
    sarif_results = []
    for result in report.results:
        sarif_result: dict[str, Any] = {
            "ruleId": result.rule_id,
            "level": result.level,
            "message": {"text": result.message},
        }

        # Add location if we have file info
        if result.file_name:
            uri = f".ldf/specs/{result.spec_name}/{result.file_name}"
            location: dict[str, Any] = {"physicalLocation": {"artifactLocation": {"uri": uri}}}
            if result.line:
                location["physicalLocation"]["region"] = {"startLine": result.line}
            sarif_result["locations"] = [location]

        sarif_results.append(sarif_result)

    # Add init error as a result if present
    if init_error:
        sarif_results.append(
            {
                "ruleId": "ldf/parse-error",
                "level": "error",
                "message": {"text": init_error},
            }
        )

    sarif: dict[str, Any] = {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "ldf-lint",
                        "version": __version__,
                        "informationUri": "https://github.com/LLMdotInfo/ldf",
                        "rules": rules,
                    }
                },
                "results": sarif_results,
            }
        ],
    }

    return sarif


def _output_sarif(sarif: dict[str, Any], output_file: str | None) -> None:
    """Output SARIF to file or stdout.

    Args:
        sarif: SARIF dictionary
        output_file: Output file path or None for stdout
    """
    sarif_json = json.dumps(sarif, indent=2)

    if output_file:
        Path(output_file).write_text(sarif_json)
    else:
        print(sarif_json)
