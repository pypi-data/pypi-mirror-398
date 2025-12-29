"""LDF conversion and backwards fill functionality.

Provides tools for converting existing codebases to use LDF,
including AI-assisted spec generation from existing code.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from ldf.utils.console import console


def _sanitize_spec_name(name: str) -> str:
    """Sanitize spec name to prevent path traversal.

    Args:
        name: Spec name to sanitize

    Returns:
        The validated spec name

    Raises:
        ValueError: If the name contains path traversal attempts
    """
    if ".." in name or name.startswith("/") or name.startswith("\\"):
        raise ValueError(f"Invalid spec name: {name}")
    if "/" in name or "\\" in name:
        raise ValueError(f"Spec name cannot contain path separators: {name}")
    return name


@dataclass
class ConversionContext:
    """Context gathered from analyzing an existing codebase."""

    project_root: Path
    detected_languages: list[str] = field(default_factory=list)
    detected_frameworks: list[str] = field(default_factory=list)
    existing_tests: list[Path] = field(default_factory=list)
    existing_docs: list[Path] = field(default_factory=list)
    existing_api_files: list[Path] = field(default_factory=list)
    source_files: list[Path] = field(default_factory=list)
    config_files: list[Path] = field(default_factory=list)

    # Inferred settings
    suggested_preset: str | None = None
    suggested_question_packs: list[str] = field(default_factory=list)


@dataclass
class ImportResult:
    """Result of importing backwards fill content."""

    success: bool
    spec_name: str
    files_created: list[str] = field(default_factory=list)
    files_skipped: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


# Language detection patterns
LANGUAGE_PATTERNS = {
    "python": {
        "extensions": [".py"],
        "config_files": ["pyproject.toml", "setup.py", "requirements.txt", "Pipfile"],
    },
    "typescript": {
        "extensions": [".ts", ".tsx"],
        "config_files": ["tsconfig.json"],
    },
    "javascript": {
        "extensions": [".js", ".jsx", ".mjs"],
        "config_files": ["package.json"],
    },
    "go": {
        "extensions": [".go"],
        "config_files": ["go.mod", "go.sum"],
    },
    "rust": {
        "extensions": [".rs"],
        "config_files": ["Cargo.toml"],
    },
    "java": {
        "extensions": [".java"],
        "config_files": ["pom.xml", "build.gradle"],
    },
}

# Framework detection patterns (keywords in dependencies or imports)
FRAMEWORK_PATTERNS = {
    "fastapi": ["fastapi", "from fastapi"],
    "django": ["django", "from django"],
    "flask": ["flask", "from flask"],
    "express": ["express", '"express"'],
    "nestjs": ["@nestjs", "nestjs"],
    "react": ["react", '"react"'],
    "vue": ["vue", '"vue"'],
    "angular": ["@angular", "angular"],
    "nextjs": ["next", '"next"'],
    "gin": ["github.com/gin-gonic/gin"],
    "echo": ["github.com/labstack/echo"],
    "spring": ["springframework", "spring-boot"],
}

# Preset suggestion patterns
PRESET_PATTERNS = {
    "saas": ["tenant", "subscription", "billing", "plan", "tier", "multi-tenant"],
    "fintech": ["payment", "transaction", "ledger", "balance", "stripe", "invoice"],
    "healthcare": ["patient", "medical", "health", "hipaa", "phi", "diagnosis"],
    "api-only": ["api", "endpoint", "rest", "graphql"],
}

# Directories to skip when scanning
SKIP_DIRS = {
    ".git",
    ".ldf",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    ".env",
    "dist",
    "build",
    "target",
    ".idea",
    ".vscode",
    "coverage",
    ".pytest_cache",
    ".mypy_cache",
}

# Max files to include in analysis
MAX_SOURCE_FILES = 50
MAX_TEST_FILES = 20
MAX_DOC_FILES = 10


def analyze_existing_codebase(project_root: Path) -> ConversionContext:
    """Analyze an existing codebase for conversion context.

    Detects languages, frameworks, existing tests, documentation,
    and suggests appropriate LDF settings.

    Args:
        project_root: Path to the project root directory.

    Returns:
        ConversionContext with analysis results.
    """
    project_root = Path(project_root).resolve()
    ctx = ConversionContext(project_root=project_root)

    # Collect files
    source_files: list[Path] = []
    test_files: list[Path] = []
    doc_files: list[Path] = []
    config_files: list[Path] = []
    api_files: list[Path] = []

    for path in project_root.rglob("*"):
        if path.is_file() and not any(skip in path.parts for skip in SKIP_DIRS):
            rel_path = path.relative_to(project_root)

            # Categorize files
            if path.suffix in (".md", ".rst", ".txt") and "readme" in path.name.lower():
                doc_files.append(rel_path)
            elif path.suffix in (".md", ".rst") and "doc" in str(rel_path).lower():
                doc_files.append(rel_path)
            elif "test" in path.name.lower() or "spec" in path.name.lower():
                test_files.append(rel_path)
            elif path.name in ("openapi.yaml", "openapi.json", "swagger.yaml", "swagger.json"):
                api_files.append(rel_path)
            elif path.suffix in (".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java"):
                source_files.append(rel_path)

            # Check for config files
            for lang, patterns in LANGUAGE_PATTERNS.items():
                if path.name in patterns["config_files"]:
                    config_files.append(rel_path)
                    if lang not in ctx.detected_languages:
                        ctx.detected_languages.append(lang)

    # Detect languages from file extensions
    for path in source_files[:100]:  # Sample first 100
        for lang, patterns in LANGUAGE_PATTERNS.items():
            if path.suffix in patterns["extensions"] and lang not in ctx.detected_languages:
                ctx.detected_languages.append(lang)

    # Detect frameworks by scanning key config files
    framework_search_files = []
    for f in config_files:
        if f.name in ("package.json", "pyproject.toml", "requirements.txt", "go.mod", "Cargo.toml"):
            framework_search_files.append(project_root / f)

    # Also check a few source files for imports
    for f in source_files[:20]:
        framework_search_files.append(project_root / f)

    for fpath in framework_search_files:
        if fpath.exists():
            try:
                content = fpath.read_text(errors="ignore").lower()
                for framework, keywords in FRAMEWORK_PATTERNS.items():
                    if any(p.lower() in content for p in keywords):
                        if framework not in ctx.detected_frameworks:
                            ctx.detected_frameworks.append(framework)
            except Exception:
                pass

    # Suggest preset based on patterns
    preset_scores = {preset: 0 for preset in PRESET_PATTERNS}
    search_content = ""

    # Build search content from key files
    for f in list(config_files)[:5] + list(source_files)[:10] + list(doc_files)[:3]:
        fpath = project_root / f
        if fpath.exists():
            try:
                search_content += fpath.read_text(errors="ignore").lower() + "\n"
            except Exception:
                pass

    for preset, keywords in PRESET_PATTERNS.items():
        for keyword in keywords:
            if keyword in search_content:
                preset_scores[preset] += 1

    # Pick highest scoring preset (or custom if none match)
    max_score = max(preset_scores.values())
    if max_score > 0:
        ctx.suggested_preset = max(preset_scores, key=lambda p: preset_scores[p])
    else:
        ctx.suggested_preset = "custom"

    # Suggest question packs based on detected languages/frameworks
    ctx.suggested_question_packs = ["security", "testing"]  # Always include core

    if ctx.detected_languages:
        ctx.suggested_question_packs.append("api-design")
        ctx.suggested_question_packs.append("data-model")

    # Store files (limited)
    ctx.source_files = sorted(source_files)[:MAX_SOURCE_FILES]
    ctx.existing_tests = sorted(test_files)[:MAX_TEST_FILES]
    ctx.existing_docs = sorted(doc_files)[:MAX_DOC_FILES]
    ctx.config_files = sorted(config_files)
    ctx.existing_api_files = sorted(api_files)

    return ctx


def generate_backwards_fill_prompt(context: ConversionContext) -> str:
    """Generate an AI prompt for backwards fill analysis.

    Creates a comprehensive prompt that an AI can use to analyze
    the existing codebase and generate LDF specs and answerpacks.

    Args:
        context: ConversionContext from codebase analysis.

    Returns:
        Markdown-formatted prompt string.
    """

    # Format file lists
    def format_file_list(files: list[Path], max_items: int = 20) -> str:
        if not files:
            return "  (none found)"
        lines = [f"  - {f}" for f in files[:max_items]]
        if len(files) > max_items:
            lines.append(f"  - ... and {len(files) - max_items} more")
        return "\n".join(lines)

    prompt = f"""# LDF Backwards Fill Analysis Request

## Context

You are analyzing an existing codebase to generate LDF (LLM Development Framework)
specifications and answerpacks. This is a "backwards fill" operation - the code exists,
and we need to document the design decisions that were made.

## Project Information

**Project Root:** {context.project_root}
**Languages Detected:** {", ".join(context.detected_languages) or "Unknown"}
**Frameworks Detected:** {", ".join(context.detected_frameworks) or "None identified"}
**Suggested Preset:** {context.suggested_preset or "custom"}
**Suggested Question Packs:** {", ".join(context.suggested_question_packs)}

## Files to Analyze

### Source Files ({len(context.source_files)} found)
{format_file_list(context.source_files)}

### Test Files ({len(context.existing_tests)} found)
{format_file_list(context.existing_tests)}

### Configuration Files
{format_file_list(context.config_files)}

### Documentation
{format_file_list(context.existing_docs)}

### API Definitions
{format_file_list(context.existing_api_files) if context.existing_api_files else "  (none found)"}

---

## Your Task

Analyze the codebase and generate LDF content. You should:

1. Read the key source files to understand the architecture
2. Identify the main features and components
3. Document the design decisions that were made
4. Generate answerpacks and specs

### 1. Generate Answerpacks

For each question pack domain, create a YAML answerpack by analyzing the code:

**Security (security.yaml):**
- Authentication method (JWT, session, OAuth - look for auth imports/middleware)
- Authorization patterns (RBAC, permissions, decorators)
- Input validation (Pydantic, Zod, manual checks)
- Rate limiting configuration
- Secrets management (env vars, vault, config files)

**Testing (testing.yaml):**
- Test frameworks in use (pytest, jest, go test)
- Coverage targets (if configured in CI/config)
- Test patterns (unit, integration, e2e - based on test file structure)
- Mocking strategies (fixtures, mocks, fakes)

**API Design (api-design.yaml):**
- API style (REST, GraphQL, gRPC)
- Versioning strategy (URL path, header, none)
- Error response format
- Pagination patterns (cursor, offset, none)

**Data Model (data-model.yaml):**
- Database type (PostgreSQL, MySQL, MongoDB, etc.)
- ORM/query builder (SQLAlchemy, Prisma, GORM, etc.)
- Migration approach (Alembic, Prisma migrate, manual)
- ID strategy (UUID, auto-increment, ULID)

### 2. Generate Spec Files

Create an "existing-system" spec that documents the current state:

**requirements.md:**
- Overview section describing the system
- Document major features as user stories (infer from code)
- Create acceptance criteria based on what the code does
- Fill in guardrail coverage matrix based on what exists

**design.md:**
- Document current architecture (components, services, layers)
- List existing API endpoints (from routes/controllers)
- Document data models (from ORM models/schemas)
- Include any diagrams you can infer

**tasks.md:**
- Create phases based on logical groupings
- List tasks as "DONE" since code exists
- Reference actual file paths for each task

---

## Output Format

**IMPORTANT:** Use these exact markers to separate sections. The import tool parses these.

```
# === ANSWERPACK: security.yaml ===
pack: security
feature: existing-system
answers:
  - question: "What authentication method is used?"
    answer: "JWT tokens with refresh token rotation"
    reference: "src/auth/jwt.py:15"
  # ... more answers

# === ANSWERPACK: testing.yaml ===
pack: testing
feature: existing-system
answers:
  # ... answers

# === ANSWERPACK: api-design.yaml ===
# ... etc

# === SPEC: requirements.md ===
# existing-system - Requirements

## Overview
[Description of the system based on code analysis]

## User Stories
[Inferred from code functionality]

## Guardrail Coverage Matrix
[Based on what exists in codebase]

# === SPEC: design.md ===
# existing-system - Design

## Architecture Overview
[Based on code structure]

## Components
[List of main components/services]

## Data Models
[From ORM models]

# === SPEC: tasks.md ===
# existing-system - Tasks

## Phase 1: [Category]
- [x] **Task 1.1:** [Description] - DONE
  - Reference: path/to/file.py
```

---

## Important Guidelines

1. **Base ALL answers on evidence from the code**, not assumptions
2. If something is unclear, note it as "Inferred: [your inference]" or "Unknown: [what's missing]"
3. **Include file paths as references** for each answer when possible
4. Focus on documenting **what IS**, not what should be
5. For the guardrail matrix, mark items as:
   - "DONE" if evidence exists in code
   - "PARTIAL" if partially implemented
   - "TODO" if no evidence found but should exist
   - "N/A" if not applicable to this codebase

---

## Begin Analysis

Please read the source files listed above and generate the answerpacks and specs.
Start with the most important files (main entry points, core services, models).
"""

    return prompt


def import_backwards_fill(
    content: str,
    project_root: Path,
    spec_name: str = "existing-system",
    dry_run: bool = False,
) -> ImportResult:
    """Import AI-generated backwards fill content.

    Parses the AI response and creates answerpack and spec files
    in the appropriate locations.

    Args:
        content: Raw AI response containing answerpacks and specs.
        project_root: Project root directory.
        spec_name: Name for the generated spec (default: "existing-system").
        dry_run: If True, don't create files, just validate.

    Returns:
        ImportResult with details of what was created.
    """
    # Sanitize spec name to prevent path traversal
    try:
        spec_name = _sanitize_spec_name(spec_name)
    except ValueError as e:
        result = ImportResult(success=False, spec_name=spec_name)
        result.errors.append(str(e))
        return result

    result = ImportResult(success=True, spec_name=spec_name)
    project_root = Path(project_root).resolve()
    ldf_dir = project_root / ".ldf"

    # Parse sections using markers
    answerpack_pattern = r"# === ANSWERPACK: (\S+) ===\n(.*?)(?=# ===|$)"
    spec_pattern = r"# === SPEC: (\S+) ===\n(.*?)(?=# ===|$)"

    # Find all answerpack sections
    answerpacks = re.findall(answerpack_pattern, content, re.DOTALL)
    specs = re.findall(spec_pattern, content, re.DOTALL)

    if not answerpacks and not specs:
        result.success = False
        result.errors.append(
            "No valid sections found. Expected markers like '# === ANSWERPACK: security.yaml ===' "
            "or '# === SPEC: requirements.md ==='"
        )
        return result

    # Create directories
    answerpack_dir = ldf_dir / "answerpacks" / spec_name
    spec_dir = ldf_dir / "specs" / spec_name

    if not dry_run:
        answerpack_dir.mkdir(parents=True, exist_ok=True)
        spec_dir.mkdir(parents=True, exist_ok=True)

    # Process answerpacks
    for filename, yaml_content in answerpacks:
        filename = filename.strip()
        yaml_content = yaml_content.strip()

        # Sanitize filename to prevent path traversal
        if ".." in filename or filename.startswith("/") or filename.startswith("\\"):
            result.errors.append(f"Answerpack {filename}: Unsafe filename (path traversal attempt)")
            result.success = False
            continue
        # Only allow simple filenames (no subdirectories)
        if "/" in filename or "\\" in filename:
            result.errors.append(f"Answerpack {filename}: Filename cannot contain path separators")
            result.success = False
            continue

        # Validate YAML
        try:
            parsed = yaml.safe_load(yaml_content)
            if not isinstance(parsed, dict):
                result.warnings.append(f"Answerpack {filename}: Content is not a valid YAML dict")
                continue
        except yaml.YAMLError as e:
            result.errors.append(f"Answerpack {filename}: Invalid YAML - {e}")
            result.success = False
            continue

        # Check for required fields
        if "pack" not in parsed:
            result.warnings.append(f"Answerpack {filename}: Missing 'pack' field")
        if "answers" not in parsed:
            result.warnings.append(f"Answerpack {filename}: Missing 'answers' field")

        dest_path = answerpack_dir / filename
        if not dry_run:
            dest_path.write_text(yaml_content)
        result.files_created.append(f"answerpacks/{spec_name}/{filename}")

    # Process specs
    for filename, md_content in specs:
        filename = filename.strip()
        md_content = md_content.strip()

        # Sanitize filename to prevent path traversal
        if ".." in filename or filename.startswith("/") or filename.startswith("\\"):
            result.errors.append(f"Spec {filename}: Unsafe filename (path traversal attempt)")
            result.success = False
            continue
        # Only allow simple filenames (no subdirectories)
        if "/" in filename or "\\" in filename:
            result.errors.append(f"Spec {filename}: Filename cannot contain path separators")
            result.success = False
            continue

        # Basic validation - check for headers
        if not md_content.startswith("#"):
            result.warnings.append(f"Spec {filename}: Content doesn't start with a markdown header")

        dest_path = spec_dir / filename
        if not dry_run:
            dest_path.write_text(md_content)
        result.files_created.append(f"specs/{spec_name}/{filename}")

    # Check for expected files
    expected_answerpacks = ["security.yaml", "testing.yaml"]
    expected_specs = ["requirements.md", "design.md", "tasks.md"]

    created_answerpacks = [f for f, _ in answerpacks]
    created_specs = [f for f, _ in specs]

    for expected in expected_answerpacks:
        if expected not in created_answerpacks:
            result.warnings.append(f"Missing expected answerpack: {expected}")

    for expected in expected_specs:
        if expected not in created_specs:
            result.warnings.append(f"Missing expected spec: {expected}")

    if result.errors:
        result.success = False

    return result


def print_conversion_context(ctx: ConversionContext) -> None:
    """Print the conversion context in a readable format."""
    console.print()
    console.print("[bold]Codebase Analysis[/bold]")
    console.print("=" * 40)
    console.print()

    console.print(f"[bold]Project:[/bold] {ctx.project_root.name}")
    console.print(f"[bold]Location:[/bold] {ctx.project_root}")
    console.print()

    if ctx.detected_languages:
        console.print(f"[bold]Languages:[/bold] {', '.join(ctx.detected_languages)}")
    else:
        console.print("[bold]Languages:[/bold] [dim]None detected[/dim]")

    if ctx.detected_frameworks:
        console.print(f"[bold]Frameworks:[/bold] {', '.join(ctx.detected_frameworks)}")
    else:
        console.print("[bold]Frameworks:[/bold] [dim]None detected[/dim]")

    console.print()
    console.print(f"[bold]Suggested Preset:[/bold] {ctx.suggested_preset}")
    console.print(f"[bold]Question Packs:[/bold] {', '.join(ctx.suggested_question_packs)}")
    console.print()

    console.print("[bold]Files Found:[/bold]")
    console.print(f"  Source files: {len(ctx.source_files)}")
    console.print(f"  Test files: {len(ctx.existing_tests)}")
    console.print(f"  Documentation: {len(ctx.existing_docs)}")
    console.print(f"  Config files: {len(ctx.config_files)}")
    console.print(f"  API definitions: {len(ctx.existing_api_files)}")
    console.print()


def print_import_result(result: ImportResult) -> None:
    """Print the import result in a readable format."""
    console.print()

    if result.files_created:
        console.print("[bold]Files Created:[/bold]")
        for f in result.files_created:
            console.print(f"  [green]+[/green] {f}")

    if result.files_skipped:
        console.print()
        console.print("[bold]Files Skipped:[/bold]")
        for f in result.files_skipped:
            console.print(f"  [yellow]=[/yellow] {f}")

    if result.warnings:
        console.print()
        console.print("[bold yellow]Warnings:[/bold yellow]")
        for w in result.warnings:
            console.print(f"  [yellow]![/yellow] {w}")

    if result.errors:
        console.print()
        console.print("[bold red]Errors:[/bold red]")
        for e in result.errors:
            console.print(f"  [red]X[/red] {e}")

    console.print()
    if result.success:
        console.print(f"[green]Import complete![/green] Spec created: {result.spec_name}")
        console.print(f"  Location: .ldf/specs/{result.spec_name}/")
        console.print(f"  Answerpacks: .ldf/answerpacks/{result.spec_name}/")
    else:
        console.print("[red]Import failed. Please check errors above.[/red]")
    console.print()
