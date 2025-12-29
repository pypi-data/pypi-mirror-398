"""Team template export functionality."""

import os
import re
import shutil
import tempfile
from pathlib import Path

import yaml
from rich.prompt import Confirm, Prompt

from ldf import __version__
from ldf.audit import REDACTION_PATTERNS
from ldf.utils.console import console


def export_template(
    project_root: Path,
    output_path: Path | None = None,
    include: list[str] | None = None,
    dry_run: bool = False,
    scrub: bool = True,
) -> bool:
    """Export project as a template.

    Args:
        project_root: Project root directory
        output_path: Output path (directory or .zip file)
        include: Components to include (config, guardrails, templates, macros, question-packs)
        dry_run: Preview without creating files
        scrub: Remove project-specific data

    Returns:
        True if export succeeded
    """
    ldf_dir = project_root / ".ldf"

    # Validate source
    if not ldf_dir.exists() or not ldf_dir.is_dir():
        console.print("[red]Error: No .ldf/ directory found.[/red]")
        console.print("Run [cyan]ldf init[/cyan] to initialize a project first.")
        return False

    # Default: include all components except specs, answerpacks, audit-history
    if include is None:
        include = ["config", "guardrails", "templates", "macros", "question-packs"]

    # Determine output path
    if output_path is None:
        output_path = project_root / "template"
    else:
        output_path = Path(output_path)

    # Check if output is zip
    is_zip = output_path.suffix == ".zip"

    if dry_run:
        console.print("[yellow]DRY RUN MODE - No files will be created[/yellow]")
        console.print()

    # Gather template metadata
    if not dry_run:
        console.print("[cyan]Creating template...[/cyan]")
        console.print()

        # Prompt for metadata
        name = Prompt.ask("Template name", default=project_root.name)
        description = Prompt.ask("Template description", default="")
        version = Prompt.ask("Template version", default="1.0.0")
    else:
        # Use defaults in dry-run
        name = project_root.name
        description = ""
        version = "1.0.0"

    # Create temp directory for staging
    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        template_dir = temp_dir / name

        # Security check: scan for secrets
        secret_warnings = _scan_for_secrets(ldf_dir, include)
        if secret_warnings:
            console.print("[yellow]Warning: Potential secrets detected:[/yellow]")
            for warning in secret_warnings:
                console.print(f"  - {warning}")
            console.print()
            if not dry_run:
                if not Confirm.ask("Continue with export?", default=False):
                    console.print("[yellow]Export cancelled.[/yellow]")
                    return False

        # Security check: scan for symlinks
        symlink_warnings = _check_symlinks(ldf_dir)
        if symlink_warnings:
            console.print("[red]Error: Symlinks detected (security risk):[/red]")
            for warning in symlink_warnings:
                console.print(f"  - {warning}")
            console.print()
            console.print("Templates cannot contain symlinks for security reasons.")
            return False

        # Preview mode
        if dry_run:
            console.print("[cyan]Template Export Preview[/cyan]")
            console.print(f"Name: {name}")
            console.print(f"Version: {version}")
            console.print(f"Description: {description}")
            console.print(f"LDF Version: {__version__}")
            console.print(f"Output: {output_path}")
            console.print(f"Scrubbing: {'enabled' if scrub else 'disabled'}")
            console.print()
            console.print("[cyan]Components to include:[/cyan]")

            for component in include:
                source_path = _get_component_path(ldf_dir, component)
                if source_path.exists():
                    if source_path.is_file():
                        size = source_path.stat().st_size
                        console.print(f"  ✓ {component} ({size} bytes)")
                    else:
                        file_count = len(list(source_path.rglob("*")))
                        console.print(f"  ✓ {component} ({file_count} items)")
                else:
                    console.print(f"  ✗ {component} (not found)")

            console.print()
            console.print("[dim]Run without --dry-run to create the template.[/dim]")
            return True

        # Create template directory
        template_dir.mkdir(parents=True, exist_ok=True)

        # Copy components
        for component in include:
            source_path = _get_component_path(ldf_dir, component)

            if not source_path.exists():
                console.print(f"[yellow]Skipping {component} (not found)[/yellow]")
                continue

            # Determine destination path
            if component == "config":
                dest_path = template_dir / "config.yaml"
            elif component == "guardrails":
                dest_path = template_dir / "guardrails.yaml"
            else:
                dest_path = template_dir / component

            # Copy file or directory
            if source_path.is_file():
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                content = source_path.read_text()

                # Scrub if enabled
                if scrub and component == "config":
                    content = _scrub_config(content)

                dest_path.write_text(content)
                console.print(f"  ✓ Copied {component}")
            else:
                shutil.copytree(source_path, dest_path, dirs_exist_ok=True)
                console.print(f"  ✓ Copied {component}")

        # Create template.yaml
        template_metadata = {
            "name": name,
            "version": version,
            "ldf_version": __version__,
            "description": description,
            "components": include,
        }

        template_yaml_path = template_dir / "template.yaml"
        with open(template_yaml_path, "w") as f:
            yaml.dump(template_metadata, f, default_flow_style=False, sort_keys=False)

        console.print("  ✓ Created template.yaml")

        # Create output
        if is_zip:
            # Create zip file
            import zipfile

            # Ensure parent directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for root, dirs, files in os.walk(template_dir):
                    for file in files:
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(template_dir)
                        zf.write(file_path, arcname)

            console.print()
            console.print(f"[green]✓ Template exported to {output_path}[/green]")
        else:
            # Copy directory
            if output_path.exists():
                shutil.rmtree(output_path)
            shutil.copytree(template_dir, output_path)

            console.print()
            console.print(f"[green]✓ Template exported to {output_path}[/green]")

    return True


def _get_component_path(ldf_dir: Path, component: str) -> Path:
    """Get the source path for a component.

    Args:
        ldf_dir: .ldf directory
        component: Component name

    Returns:
        Path to the component
    """
    if component == "config":
        return ldf_dir / "config.yaml"
    elif component == "guardrails":
        return ldf_dir / "guardrails.yaml"
    elif component == "templates":
        return ldf_dir / "templates"
    elif component == "macros":
        return ldf_dir / "macros"
    elif component == "question-packs":
        return ldf_dir / "question-packs"
    else:
        return ldf_dir / component


def _scrub_config(content: str) -> str:
    """Scrub project-specific data from config.yaml.

    Args:
        content: Config file content

    Returns:
        Scrubbed content
    """
    try:
        config = yaml.safe_load(content)

        # Remove project name
        if "project" in config and isinstance(config["project"], dict):
            if "name" in config["project"]:
                config["project"]["name"] = "my-project"

        # Remove checksums
        if "_checksums" in config:
            del config["_checksums"]

        # Remove template metadata if present
        if "_template" in config:
            del config["_template"]

        # Dump back to YAML
        return yaml.dump(config, default_flow_style=False, sort_keys=False)
    except Exception:
        # If parsing fails, return original
        return content


def _scan_for_secrets(ldf_dir: Path, include: list[str]) -> list[str]:
    """Scan for potential secrets in files to be exported.

    Args:
        ldf_dir: .ldf directory
        include: Components to include

    Returns:
        List of warnings
    """
    warnings = []

    for component in include:
        component_path = _get_component_path(ldf_dir, component)

        if not component_path.exists():
            continue

        # Scan files
        if component_path.is_file():
            _scan_file_for_secrets(component_path, warnings)
        else:
            for file_path in component_path.rglob("*"):
                if file_path.is_file():
                    _scan_file_for_secrets(file_path, warnings)

    return warnings


def _scan_file_for_secrets(file_path: Path, warnings: list[str]) -> None:
    """Scan a single file for secrets.

    Args:
        file_path: File to scan
        warnings: List to append warnings to
    """
    # Skip binary files
    try:
        content = file_path.read_text()
    except Exception:
        return

    # Check for secret patterns
    for pattern, _ in REDACTION_PATTERNS:
        if re.search(pattern, content):
            warnings.append(f"{file_path.name}: Potential secret detected")
            break  # Only warn once per file


def _check_symlinks(ldf_dir: Path) -> list[str]:
    """Check for symlinks in the directory tree.

    Args:
        ldf_dir: Directory to check

    Returns:
        List of symlink warnings
    """
    warnings = []

    for root, dirs, files in os.walk(ldf_dir):
        for name in dirs + files:
            path = Path(root) / name
            if path.is_symlink():
                warnings.append(f"{path.relative_to(ldf_dir)}")

    return warnings
