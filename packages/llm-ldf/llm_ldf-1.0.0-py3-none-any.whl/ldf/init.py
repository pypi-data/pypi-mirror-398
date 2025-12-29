"""LDF project initialization."""

import hashlib
import shutil
from datetime import datetime
from pathlib import Path

import yaml
from rich.panel import Panel
from rich.prompt import Confirm

from ldf import __version__
from ldf.prompts import (
    confirm_initialization,
    prompt_custom_guardrails,
    prompt_guardrail_mode,
    prompt_install_hooks,
    prompt_mcp_servers,
    prompt_preset,
    prompt_project_path,
    prompt_question_packs,
)
from ldf.utils.console import console
from ldf.utils.descriptions import get_all_mcp_servers, get_core_packs, is_mcp_server_default
from ldf.utils.hooks import get_git_hooks_dir

# Framework paths (relative to package)
FRAMEWORK_DIR = Path(__file__).parent / "_framework"


def compute_file_checksum(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def initialize_project(
    project_path: Path | None = None,
    preset: str | None = None,
    question_packs: list[str] | None = None,
    mcp_servers: list[str] | None = None,
    non_interactive: bool = False,
    install_hooks: bool = False,
    custom_guardrails: list[int] | None = None,
) -> None:
    """Initialize LDF in the specified or current project directory.

    Args:
        project_path: Project directory path (created if doesn't exist).
            If None, prompts interactively or uses cwd in non-interactive mode.
        preset: Guardrail preset (saas, fintech, healthcare, api-only, custom)
        question_packs: List of question packs to include
        mcp_servers: List of MCP servers to enable
        non_interactive: Skip prompts and use defaults
        install_hooks: Whether to install pre-commit hooks
        custom_guardrails: List of guardrail IDs when using custom mode
    """
    # Step 1: Determine project path
    if project_path is None and not non_interactive:
        try:
            project_path = prompt_project_path()
        except KeyboardInterrupt:
            console.print("\n[red]Aborted[/red]")
            return
    elif project_path is None:
        project_path = Path.cwd()

    project_root = Path(project_path).resolve()

    # Step 2: Create directory if needed
    if not project_root.exists():
        project_root.mkdir(parents=True)
        console.print(f"[green]Created directory:[/green] {project_root}")

    # Early git check - warn if hooks requested but no git repo
    if install_hooks and get_git_hooks_dir(project_root) is None:
        console.print("[yellow]Warning: Not a git repository.[/yellow]")
        console.print(
            "[dim]Hooks will not be installed. "
            "Run 'git init' first, then 'ldf hooks install'.[/dim]"
        )
        install_hooks = False

    ldf_dir = project_root / ".ldf"

    # Check if already initialized
    if ldf_dir.exists() and not non_interactive:
        if not Confirm.ask("[yellow].ldf/ already exists. Overwrite?[/yellow]"):
            console.print("[red]Aborted[/red]")
            return

    console.print(
        Panel.fit(
            f"[bold blue]Initializing LDF in {project_root.name}[/bold blue]",
            title="LDF Setup",
        )
    )

    # Step 3: Interactive configuration
    if not non_interactive:
        try:
            # Guardrail mode selection (preset vs custom)
            if preset is None and custom_guardrails is None:
                guardrail_mode = prompt_guardrail_mode()

                if guardrail_mode == "custom":
                    # Custom mode: select individual guardrails
                    custom_guardrails = prompt_custom_guardrails()
                    preset = "custom"
                else:
                    # Preset mode: select a preset
                    preset = prompt_preset()
            elif preset is None:
                preset = "custom"  # custom_guardrails provided via CLI

            # Question packs (with preset-based recommendations)
            if question_packs is None:
                question_packs = prompt_question_packs(preset)

            # MCP servers
            if mcp_servers is None:
                mcp_servers = prompt_mcp_servers()

            # Hooks prompt
            if not install_hooks:
                install_hooks = prompt_install_hooks()

            # Confirmation
            if not confirm_initialization(
                project_root, preset, question_packs, mcp_servers, install_hooks
            ):
                console.print("\n[red]Aborted[/red]")
                return

        except KeyboardInterrupt:
            console.print("\n[red]Aborted[/red]")
            return

    # Ensure defaults for non-interactive mode
    if preset is None:
        preset = "custom"
    if not question_packs:
        question_packs = list(get_core_packs())
    if mcp_servers is None:
        # Get default MCP servers from descriptions
        mcp_servers = [s for s in get_all_mcp_servers() if is_mcp_server_default(s)]
        if not mcp_servers:
            mcp_servers = ["spec_inspector", "coverage_reporter"]

    console.print()

    # Create directory structure
    _create_directories(ldf_dir)

    # Create guardrails
    _create_guardrails(ldf_dir, preset, custom_guardrails)

    # Copy question packs (returns checksums for modification detection)
    checksums = _copy_question_packs(ldf_dir, question_packs)

    # Copy templates
    _copy_templates(ldf_dir)

    # Create configuration (after question packs so we have checksums)
    _create_config(ldf_dir, preset, question_packs, mcp_servers, checksums)

    # Copy macros
    _copy_macros(ldf_dir)

    # Create AGENT.md
    _create_agent_md(project_root, preset, question_packs)

    # Create .agent directory for commands
    _create_agent_commands(project_root)

    # Install hooks if requested
    hooks_installed = False
    if install_hooks:
        from ldf.hooks import install_hooks as do_install_hooks

        console.print()
        hooks_installed = do_install_hooks(
            detect_linters=not non_interactive,
            non_interactive=non_interactive,
            project_root=project_root,
        )

    # Summary
    _print_summary(project_root, preset, question_packs, mcp_servers, hooks_installed)


def _create_directories(ldf_dir: Path) -> None:
    """Create the .ldf directory structure."""
    dirs = [
        ldf_dir,
        ldf_dir / "specs",
        ldf_dir / "question-packs",
        ldf_dir / "question-packs" / "core",
        ldf_dir / "question-packs" / "optional",
        ldf_dir / "answerpacks",
        ldf_dir / "templates",
        ldf_dir / "audit-history",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    console.print("  [green]✓[/green] Created .ldf/ directory structure")


def _create_config(
    ldf_dir: Path,
    preset: str,
    question_packs: list[str],
    mcp_servers: list[str],
    checksums: dict[str, str] | None = None,
) -> None:
    """Create the LDF configuration file with v1.1 schema."""
    # Split question packs into core and optional
    core_packs = {"security", "testing", "api-design", "data-model"}
    core = [p for p in question_packs if p in core_packs]
    optional = [p for p in question_packs if p not in core_packs]

    config = {
        "_schema_version": "1.1",
        "project": {
            "name": ldf_dir.parent.name,
            "version": "1.0.0",
            "specs_dir": ".ldf/specs",
        },
        "ldf": {
            "version": __version__,
            "preset": preset,
            "updated": datetime.now().isoformat(),
        },
        "question_packs": {
            "core": core,
            "optional": optional,
        },
        "mcp_servers": {
            "enabled": bool(mcp_servers),
            "servers": mcp_servers,
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
    }

    # Store checksums for modification detection during updates
    if checksums:
        config["_checksums"] = checksums

    config_path = ldf_dir / "config.yaml"
    with open(config_path, "w") as f:
        yaml.safe_dump(config, f, default_flow_style=False, sort_keys=False)
    console.print("  [green]✓[/green] Created config.yaml")


def _create_guardrails(
    ldf_dir: Path,
    preset: str,
    custom_guardrails: list[int] | None = None,
) -> None:
    """Create the guardrails configuration file.

    Args:
        ldf_dir: LDF directory path
        preset: Preset name (or "custom" for custom selection)
        custom_guardrails: List of guardrail IDs when using custom mode
    """
    guardrails: dict[str, str | list[str] | list[int] | dict[str, str] | None] = {
        "extends": "core",
        "preset": preset if preset != "custom" else None,
        "overrides": {},
        "disabled": [],
        "custom": [],
    }

    # Store selected guardrail IDs for custom mode
    if custom_guardrails:
        guardrails["selected_ids"] = custom_guardrails

    # Remove None values
    guardrails = {k: v for k, v in guardrails.items() if v is not None}

    guardrails_path = ldf_dir / "guardrails.yaml"
    with open(guardrails_path, "w") as f:
        yaml.safe_dump(guardrails, f, default_flow_style=False, sort_keys=False)

    if custom_guardrails:
        console.print(
            f"  [green]✓[/green] Created guardrails.yaml "
            f"({len(custom_guardrails)} guardrails selected)"
        )
    else:
        console.print(f"  [green]✓[/green] Created guardrails.yaml (preset: {preset})")


def _copy_question_packs(ldf_dir: Path, packs: list[str]) -> dict[str, str]:
    """Copy selected question packs to the project.

    Returns:
        Dictionary mapping relative file paths to their checksums.
    """
    source_dir = FRAMEWORK_DIR / "question-packs"
    dest_dir = ldf_dir / "question-packs"

    checksums: dict[str, str] = {}
    copied = 0
    for pack in packs:
        # Check core packs first
        source = source_dir / "core" / f"{pack}.yaml"
        subdir = "core"

        if not source.exists():
            # Check optional packs
            source = source_dir / "optional" / f"{pack}.yaml"
            subdir = "optional"

        if source.exists():
            # Copy to appropriate subdirectory
            dest = dest_dir / subdir / f"{pack}.yaml"
            shutil.copy(source, dest)
            # Store checksum with relative path including subdirectory
            checksums[f"question-packs/{subdir}/{pack}.yaml"] = compute_file_checksum(dest)
            copied += 1
        else:
            # Create placeholder in optional (for custom packs)
            placeholder = dest_dir / "optional" / f"{pack}.yaml"
            placeholder.write_text(f"# {pack} question pack\n# TODO: Add questions\n")
            checksums[f"question-packs/optional/{pack}.yaml"] = compute_file_checksum(placeholder)
            copied += 1

    console.print(f"  [green]✓[/green] Copied {copied} question packs")
    return checksums


def _copy_templates(ldf_dir: Path) -> None:
    """Copy spec templates to the project."""
    source_dir = FRAMEWORK_DIR / "templates"
    dest_dir = ldf_dir / "templates"

    templates = ["requirements.md", "design.md", "tasks.md"]
    for template in templates:
        source = source_dir / template
        if source.exists():
            shutil.copy(source, dest_dir / template)

    console.print("  [green]✓[/green] Copied spec templates")


def _copy_macros(ldf_dir: Path) -> None:
    """Copy macros to the project."""
    source_dir = FRAMEWORK_DIR / "macros"
    dest_dir = ldf_dir / "macros"
    dest_dir.mkdir(exist_ok=True)

    macros = ["clarify-first.md", "coverage-gate.md", "task-guardrails.md"]
    for macro in macros:
        source = source_dir / macro
        if source.exists():
            shutil.copy(source, dest_dir / macro)

    console.print("  [green]✓[/green] Copied enforcement macros")


def _create_agent_md(project_root: Path, preset: str, question_packs: list[str]) -> None:
    """Create AGENT.md file for AI assistant integration."""
    coverage_threshold = "90%" if preset == "fintech" else "80%"

    content = f"""# Project Instructions for Claude Code

## Project Overview
**Name:** {project_root.name}
**Framework:** LDF (LLM Development Framework)
**Preset:** {preset}
**Initialized:** {datetime.now().strftime("%Y-%m-%d")}

---

## Development Methodology

This project uses **LDF** - a spec-driven development approach with three phases:

### Phase 1: Requirements
- **Location:** `.ldf/specs/{{feature}}/requirements.md`
- **Template:** `.ldf/templates/requirements.md`
- **Command:** `/project:create-spec {{feature-name}}`

### Phase 2: Design
- **Location:** `.ldf/specs/{{feature}}/design.md`
- **Template:** `.ldf/templates/design.md`

### Phase 3: Tasks
- **Location:** `.ldf/specs/{{feature}}/tasks.md`
- **Template:** `.ldf/templates/tasks.md`

**CRITICAL RULE:** Do NOT write code until all three phases are approved.

---

## Guardrails

This project enforces the following guardrails (see `.ldf/guardrails.yaml`):

### Core Guardrails (Always Active)
1. **Testing Coverage** - Minimum {coverage_threshold} coverage
2. **Security Basics** - OWASP Top 10 prevention
3. **Error Handling** - Consistent error responses
4. **Logging & Observability** - Structured logging, correlation IDs
5. **API Design** - Versioning, pagination, error format
6. **Data Validation** - Input validation at boundaries
7. **Database Migrations** - Reversible, separate from backfills
8. **Documentation** - API docs, inline comments

### Preset Guardrails ({preset})
See `.ldf/guardrails.yaml` for additional guardrails from the {preset} preset.

---

## Question Packs

Before writing requirements, answer questions from these packs:
{chr(10).join(f"- `{pack}`" for pack in question_packs)}

Answers are captured in `.ldf/answerpacks/{{feature}}/`.

---

## Custom Commands

### `/project:create-spec {{feature-name}}`
Create a new feature specification:
1. Load relevant question-packs
2. Ask clarifying questions (clarify-first macro)
3. Generate requirements.md
4. Wait for approval
5. Generate design.md
6. Wait for approval
7. Generate tasks.md
8. Ready for implementation

### `/project:implement-task {{spec-name}} {{task-number}}`
Implement a specific task:
1. Load spec context
2. Check dependencies
3. Run task-guardrails macro
4. Implement code + tests
5. Update task status

### `/project:review-spec {{spec-name}}`
Review spec for completeness:
1. Run coverage-gate macro
2. Validate guardrail coverage matrix
3. Check answerpacks populated
4. Report issues

---

## Validation

```bash
ldf lint                  # Validate all specs
ldf lint {{spec-name}}    # Validate single spec
ldf audit --type spec-review  # Generate audit for other AI
```

---

## Notes for Claude

- **Read specs first:** Always check `.ldf/specs/` before coding
- **Respect phases:** Don't skip requirements → design → tasks
- **Use macros:** Run clarify-first, coverage-gate, task-guardrails
- **Test after changes:** Verify coverage meets thresholds
- **Commit incrementally:** Commit after each completed task
- **Update progress:** Mark tasks complete in tasks.md

**Development Flow:** Plan → Design → Task → Implement → Test → Commit
"""

    agent_md_path = project_root / "AGENT.md"

    # Don't overwrite if exists (unless it's a LDF-generated one)
    if agent_md_path.exists():
        existing = agent_md_path.read_text()
        if "LDF" not in existing and "LLM Development Framework" not in existing:
            # Backup existing
            backup_path = project_root / "AGENT.md.backup"
            shutil.copy(agent_md_path, backup_path)
            console.print("  [yellow]![/yellow] Backed up existing AGENT.md to AGENT.md.backup")

    agent_md_path.write_text(content)
    console.print("  [green]✓[/green] Created AGENT.md")


def _create_agent_commands(project_root: Path) -> None:
    """Create .agent/commands directory with slash commands."""
    commands_dir = project_root / ".agent" / "commands"
    commands_dir.mkdir(parents=True, exist_ok=True)

    # Create spec command
    create_spec_cmd = """# Create a new feature specification

## Arguments
- `feature-name`: Name of the feature to create (required)

## Process

1. **Load Question Packs**
   - Read `.ldf/config.yaml` for configured packs
   - Load pack files from `.ldf/question-packs/`

2. **Run Clarify-First Macro**
   - Ask all critical questions from loaded packs
   - Capture answers in `.ldf/answerpacks/{feature}/`
   - Block if critical questions unanswered

3. **Create Spec Directory**
   - Create `.ldf/specs/{feature}/`

4. **Generate requirements.md**
   - Use template from `.ldf/templates/requirements.md`
   - Include question-pack answers summary
   - Include guardrail coverage matrix
   - Add user stories based on answers

5. **Wait for Approval**
   - Present requirements to user
   - Run `ldf lint {feature}` to validate
   - Get explicit approval before continuing

6. **Generate design.md**
   - Use template from `.ldf/templates/design.md`
   - Map guardrails to design components
   - Include architecture diagrams
   - Define API endpoints and data models

7. **Wait for Approval**
   - Present design to user
   - Validate guardrail mapping complete
   - Get explicit approval before continuing

8. **Generate tasks.md**
   - Use template from `.ldf/templates/tasks.md`
   - Break work into <4 hour tasks
   - Include per-task guardrail checklist
   - Add dependencies and test requirements

9. **Final Validation**
   - Run `ldf lint {feature}`
   - Confirm all sections complete
   - Ready for implementation
"""

    (commands_dir / "create-spec.md").write_text(create_spec_cmd)

    # Create implement-task command
    implement_task_cmd = """# Implement a specific task from a spec

## Arguments
- `spec-name`: Name of the spec (required)
- `task-number`: Task number to implement (e.g., "2.1") (required)

## Process

1. **Load Spec Context**
   - Read `.ldf/specs/{spec}/requirements.md`
   - Read `.ldf/specs/{spec}/design.md`
   - Read `.ldf/specs/{spec}/tasks.md`
   - Find the specific task

2. **Check Dependencies**
   - Verify dependent tasks are complete
   - Block if dependencies not met

3. **Run Task-Guardrails Macro**
   - Load active guardrails from `.ldf/guardrails.yaml`
   - Present checklist for this task
   - Verify each applicable guardrail addressed
   - Block if critical guardrails not addressed

4. **Implement Code**
   - Follow the design from design.md
   - Implement the task description
   - Add proper error handling
   - Follow project coding patterns

5. **Write Tests**
   - Unit tests for business logic
   - Integration tests for APIs
   - Meet coverage threshold

6. **Update Task Status**
   - Mark task as complete in tasks.md
   - Add commit reference

7. **Commit**
   - Stage changes
   - Commit with reference to spec and task
"""

    (commands_dir / "implement-task.md").write_text(implement_task_cmd)

    # Create review-spec command
    review_spec_cmd = """# Review a spec for completeness

## Arguments
- `spec-name`: Name of the spec to review (required)

## Process

1. **Load Spec Files**
   - Check requirements.md exists
   - Check design.md exists
   - Check tasks.md exists

2. **Run Coverage-Gate Macro**
   - Validate guardrail coverage matrix
   - Check all active guardrails have entries
   - Verify no empty cells (or N/A with justification)

3. **Validate Answerpacks**
   - Check `.ldf/answerpacks/{spec}/` exists
   - Verify critical questions answered
   - Flag any template markers remaining

4. **Run Linter**
   - Execute `ldf lint {spec}`
   - Report errors and warnings

5. **Generate Report**
   - Summary of spec status
   - List of issues found
   - Recommendations for fixes
"""

    (commands_dir / "review-spec.md").write_text(review_spec_cmd)

    console.print("  [green]✓[/green] Created .agent/commands/")


def _print_summary(
    project_root: Path,
    preset: str,
    question_packs: list[str],
    mcp_servers: list[str],
    hooks_installed: bool = False,
) -> None:
    """Print initialization summary."""
    console.print()
    console.print(
        Panel.fit(
            "[bold green]LDF initialized successfully![/bold green]",
            title="Complete",
        )
    )

    console.print("\n[bold]Configuration:[/bold]")
    console.print(f"  Preset: [cyan]{preset}[/cyan]")
    console.print(f"  Question packs: [cyan]{', '.join(question_packs)}[/cyan]")
    console.print(f"  MCP servers: [cyan]{', '.join(mcp_servers)}[/cyan]")
    if hooks_installed:
        console.print("  Pre-commit hooks: [green]installed[/green]")

    console.print("\n[bold]Created files:[/bold]")
    console.print("  .ldf/")
    console.print("  ├── config.yaml")
    console.print("  ├── guardrails.yaml")
    console.print("  ├── specs/")
    console.print("  ├── templates/")
    console.print("  ├── question-packs/")
    console.print("  ├── answerpacks/")
    console.print("  └── macros/")
    console.print("  .agent/commands/")
    console.print("  AGENT.md")
    if hooks_installed:
        console.print("  .git/hooks/pre-commit")

    console.print("\n[bold]Next steps:[/bold]")
    console.print("  1. Review [cyan].ldf/config.yaml[/cyan] and customize as needed")
    console.print("  2. Review [cyan]AGENT.md[/cyan] and update project-specific sections")
    console.print(
        "  3. Run [cyan]/project:create-spec <feature-name>[/cyan] to create your first spec"
    )
    if not hooks_installed:
        console.print(
            "  4. (Optional) Run [cyan]ldf hooks install[/cyan] to add pre-commit validation"
        )
    console.print()


def repair_project(project_root: Path) -> None:
    """Repair an incomplete LDF setup by adding missing files.

    Only creates files that don't exist - never overwrites existing files.
    Uses existing config values if available, otherwise uses defaults.

    Args:
        project_root: Project directory path
    """
    project_root = Path(project_root).resolve()
    ldf_dir = project_root / ".ldf"

    # Load existing config if available
    config_path = ldf_dir / "config.yaml"
    if config_path.exists():
        try:
            with open(config_path) as f:
                config = yaml.safe_load(f) or {}
        except Exception:
            config = {}
    else:
        config = {}

    # Extract settings from config or use defaults
    # Handle v1.1 schema: ldf.preset or guardrails.preset
    preset = config.get("ldf", {}).get("preset") or config.get("guardrails", {}).get("preset", "custom")

    # Handle v1.1 schema: question_packs.core + question_packs.optional
    qp_config = config.get("question_packs", list(get_core_packs()))
    if isinstance(qp_config, dict):
        # v1.1 schema
        question_packs = qp_config.get("core", []) + qp_config.get("optional", [])
    else:
        # Legacy flat list
        question_packs = qp_config

    # Handle v1.1 schema: mcp_servers.servers
    mcp_config = config.get("mcp_servers", ["spec_inspector", "coverage_reporter"])
    if isinstance(mcp_config, dict):
        mcp_servers = mcp_config.get("servers", ["spec_inspector", "coverage_reporter"])
    else:
        mcp_servers = mcp_config

    repaired = []

    # Ensure directories exist
    dirs = [
        ldf_dir,
        ldf_dir / "specs",
        ldf_dir / "question-packs",
        ldf_dir / "question-packs" / "core",
        ldf_dir / "question-packs" / "optional",
        ldf_dir / "answerpacks",
        ldf_dir / "templates",
        ldf_dir / "macros",
        ldf_dir / "audit-history",
    ]
    for d in dirs:
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            repaired.append(f"Created {d.relative_to(project_root)}/")

    # Repair config.yaml if missing or incomplete
    if not config_path.exists():
        checksums = _copy_question_packs(ldf_dir, question_packs)
        _create_config(ldf_dir, preset, question_packs, mcp_servers, checksums)
        repaired.append("Created config.yaml")
    else:
        # Add missing fields to existing config
        updated = False
        if "framework_version" not in config:
            config["framework_version"] = __version__
            config["framework_updated"] = datetime.now().isoformat()
            updated = True
        if "_checksums" not in config:
            # Compute checksums for existing question packs
            checksums = {}
            qp_dir = ldf_dir / "question-packs"
            if qp_dir.exists():
                for qp_file in qp_dir.glob("*.yaml"):
                    rel_path = f"question-packs/{qp_file.name}"
                    checksums[rel_path] = compute_file_checksum(qp_file)
            if checksums:
                config["_checksums"] = checksums
                updated = True
        if updated:
            with open(config_path, "w") as f:
                yaml.safe_dump(config, f, default_flow_style=False, sort_keys=False)
            repaired.append("Updated config.yaml with missing fields")

    # Repair guardrails.yaml
    guardrails_path = ldf_dir / "guardrails.yaml"
    if not guardrails_path.exists():
        _create_guardrails(ldf_dir, preset)
        repaired.append("Created guardrails.yaml")

    # Repair question packs
    qp_dir = ldf_dir / "question-packs"
    existing_packs = set()
    if qp_dir.exists():
        # Check both core/ and optional/ subdirectories
        for subdir in ["core", "optional"]:
            subdir_path = qp_dir / subdir
            if subdir_path.exists():
                existing_packs.update(f.stem for f in subdir_path.glob("*.yaml"))

    missing_packs = set(question_packs) - existing_packs
    if missing_packs:
        source_dir = FRAMEWORK_DIR / "question-packs"
        for pack in missing_packs:
            # Check core first
            source = source_dir / "core" / f"{pack}.yaml"
            subdir = "core"
            if not source.exists():
                # Check optional
                source = source_dir / "optional" / f"{pack}.yaml"
                subdir = "optional"

            if source.exists():
                dest = qp_dir / subdir / f"{pack}.yaml"
                shutil.copy(source, dest)
                repaired.append(f"Added question pack: {pack} ({subdir})")

    # Repair templates
    templates_dir = ldf_dir / "templates"
    for template in ["requirements.md", "design.md", "tasks.md"]:
        dest = templates_dir / template
        if not dest.exists():
            source = FRAMEWORK_DIR / "templates" / template
            if source.exists():
                shutil.copy(source, dest)
                repaired.append(f"Added template: {template}")

    # Repair macros
    macros_dir = ldf_dir / "macros"
    for macro in ["clarify-first.md", "coverage-gate.md", "task-guardrails.md"]:
        dest = macros_dir / macro
        if not dest.exists():
            source = FRAMEWORK_DIR / "macros" / macro
            if source.exists():
                shutil.copy(source, dest)
                repaired.append(f"Added macro: {macro}")

    # Repair AGENT.md
    agent_md = project_root / "AGENT.md"
    if not agent_md.exists():
        _create_agent_md(project_root, preset, question_packs)
        repaired.append("Created AGENT.md")

    # Repair .agent/commands
    commands_dir = project_root / ".agent" / "commands"
    if not commands_dir.exists() or not any(commands_dir.glob("*.md")):
        _create_agent_commands(project_root)
        repaired.append("Created .agent/commands/")

    # Print summary
    console.print()
    if repaired:
        console.print("[green]Repair complete![/green]")
        console.print()
        console.print("[bold]Repaired:[/bold]")
        for item in repaired:
            console.print(f"  [green]✓[/green] {item}")
    else:
        console.print("[green]No repairs needed - setup is complete.[/green]")
    console.print()
