"""LDF framework update functionality.

Handles updating framework files while preserving user customizations.
"""

import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import cast

import yaml

from ldf import __version__
from ldf.init import FRAMEWORK_DIR, compute_file_checksum
from ldf.utils.console import console


@dataclass
class UpdateInfo:
    """Information about available updates."""

    current_version: str
    latest_version: str
    has_updates: bool
    updatable_components: list[str] = field(default_factory=list)


@dataclass
class FileChange:
    """Represents a file that will be changed."""

    path: str  # Relative path within .ldf/
    change_type: str  # "update", "add", "remove"
    reason: str  # Description of why this change is happening


@dataclass
class Conflict:
    """Represents a file conflict requiring user resolution."""

    file_path: str
    reason: str  # "user_modified", "removed_in_new_version"
    resolution_options: list[str] = field(default_factory=list)


@dataclass
class UpdateDiff:
    """Full diff of changes to apply."""

    files_to_update: list[FileChange] = field(default_factory=list)
    files_to_add: list[FileChange] = field(default_factory=list)
    conflicts: list[Conflict] = field(default_factory=list)
    files_unchanged: list[str] = field(default_factory=list)


@dataclass
class UpdateResult:
    """Result of applying updates."""

    success: bool
    files_updated: list[str] = field(default_factory=list)
    files_skipped: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


# Component definitions
COMPONENTS = {
    "templates": {
        "source": FRAMEWORK_DIR / "templates",
        "dest": "templates",
        "files": ["requirements.md", "design.md", "tasks.md"],
        "strategy": "replace",
    },
    "macros": {
        "source": FRAMEWORK_DIR / "macros",
        "dest": "macros",
        "files": ["clarify-first.md", "coverage-gate.md", "task-guardrails.md"],
        "strategy": "replace",
    },
    "question-packs": {
        "source_core": FRAMEWORK_DIR / "question-packs" / "core",
        "source_domain": FRAMEWORK_DIR / "question-packs" / "domain",
        "dest": "question-packs",
        "strategy": "replace_if_unmodified",  # Check checksums
    },
}


def load_project_config(project_root: Path) -> dict:
    """Load the project's LDF configuration."""
    config_path = project_root / ".ldf" / "config.yaml"
    if not config_path.exists():
        return {}
    with open(config_path) as f:
        return yaml.safe_load(f) or {}


def save_project_config(project_root: Path, config: dict) -> None:
    """Save the project's LDF configuration."""
    config_path = project_root / ".ldf" / "config.yaml"
    with open(config_path, "w") as f:
        yaml.safe_dump(config, f, default_flow_style=False, sort_keys=False)


def check_for_updates(project_root: Path) -> UpdateInfo:
    """Check if framework updates are available.

    Args:
        project_root: Path to the project root directory.

    Returns:
        UpdateInfo with version comparison and available components.
    """
    config = load_project_config(project_root)
    # Support both v1.1 schema (ldf.version) and legacy (framework_version)
    current_version = config.get("ldf", {}).get("version") or config.get(
        "framework_version", "0.0.0"
    )
    latest_version = __version__

    # Determine if updates are available
    has_updates = current_version != latest_version

    # List updatable components
    updatable_components = []
    ldf_dir = project_root / ".ldf"

    for component_name, component_info in COMPONENTS.items():
        dest = cast(str, component_info["dest"])
        dest_dir = ldf_dir / dest
        if dest_dir.exists():
            updatable_components.append(component_name)

    return UpdateInfo(
        current_version=current_version,
        latest_version=latest_version,
        has_updates=has_updates,
        updatable_components=updatable_components,
    )


def _is_file_modified(project_root: Path, relative_path: str, config: dict) -> bool:
    """Check if a file has been modified from its original state.

    Uses checksums stored during init to detect modifications.
    """
    checksums = config.get("_checksums", {})
    original_checksum = checksums.get(relative_path)

    if original_checksum is None:
        # No checksum stored - assume modified to be safe
        return True

    file_path = project_root / ".ldf" / relative_path
    if not file_path.exists():
        return True

    current_checksum = compute_file_checksum(file_path)
    return bool(current_checksum != original_checksum)


def get_update_diff(project_root: Path, components: list[str] | None = None) -> UpdateDiff:
    """Compute the diff of changes that would be applied.

    Args:
        project_root: Path to the project root directory.
        components: List of components to check. None means all.

    Returns:
        UpdateDiff with files to update, add, and conflicts.
    """
    config = load_project_config(project_root)
    ldf_dir = project_root / ".ldf"
    diff = UpdateDiff()

    # Filter components if specified
    check_components = components if components else list(COMPONENTS.keys())

    for component_name in check_components:
        if component_name not in COMPONENTS:
            continue

        component_info = COMPONENTS[component_name]
        _strategy = component_info["strategy"]  # noqa: F841 - reserved for future use

        if component_name == "question-packs":
            # Special handling for question packs
            _diff_question_packs(project_root, config, diff)
        else:
            # Handle templates and macros
            source_dir = cast(Path, component_info["source"])
            dest_dir = ldf_dir / cast(str, component_info["dest"])

            for filename in cast(list[str], component_info["files"]):
                source_file = source_dir / filename
                dest_file = dest_dir / filename
                relative_path = f"{component_info['dest']}/{filename}"

                if not source_file.exists():
                    continue

                if not dest_file.exists():
                    # File doesn't exist in project - add it
                    diff.files_to_add.append(
                        FileChange(
                            path=relative_path,
                            change_type="add",
                            reason="New file from framework",
                        )
                    )
                else:
                    # Check if content differs
                    source_checksum = compute_file_checksum(source_file)
                    dest_checksum = compute_file_checksum(dest_file)

                    if source_checksum == dest_checksum:
                        diff.files_unchanged.append(relative_path)
                    else:
                        diff.files_to_update.append(
                            FileChange(
                                path=relative_path,
                                change_type="update",
                                reason="Framework update",
                            )
                        )

    return diff


def _diff_question_packs(project_root: Path, config: dict, diff: UpdateDiff) -> None:
    """Compute diff for question packs with modification detection."""
    ldf_dir = project_root / ".ldf"
    dest_dir = ldf_dir / "question-packs"

    if not dest_dir.exists():
        return

    # Get configured question packs - handle both flat list and v1.1 dict structure
    qp_config = config.get("question_packs", [])
    if isinstance(qp_config, dict):
        # v1.1 schema: {core: [...], optional: [...]}
        configured_packs = qp_config.get("core", []) + qp_config.get("optional", [])
    else:
        # Legacy flat list
        configured_packs = qp_config

    source_core = FRAMEWORK_DIR / "question-packs" / "core"
    source_domain = FRAMEWORK_DIR / "question-packs" / "domain"

    for pack_name in configured_packs:
        # Find source file - check core first, then domain
        source_file = source_core / f"{pack_name}.yaml"
        dest_subdir = "core"
        if not source_file.exists():
            source_file = source_domain / f"{pack_name}.yaml"
            dest_subdir = "optional"

        # v1.1 schema: files are in core/ or optional/ subdirectories
        dest_file_v11 = dest_dir / dest_subdir / f"{pack_name}.yaml"
        # Legacy: files directly in question-packs/
        dest_file_legacy = dest_dir / f"{pack_name}.yaml"

        # Check which path exists
        if dest_file_v11.exists():
            dest_file = dest_file_v11
            relative_path = f"question-packs/{dest_subdir}/{pack_name}.yaml"
        elif dest_file_legacy.exists():
            dest_file = dest_file_legacy
            relative_path = f"question-packs/{pack_name}.yaml"
        else:
            dest_file = None
            # For new files, use v1.1 path
            relative_path = f"question-packs/{dest_subdir}/{pack_name}.yaml"

        if not source_file.exists():
            # No framework source for this pack
            continue

        if dest_file is None:
            # Pack doesn't exist in project - add it
            diff.files_to_add.append(
                FileChange(
                    path=relative_path,
                    change_type="add",
                    reason="New question pack from framework",
                )
            )
            continue

        # Check if source and dest differ
        source_checksum = compute_file_checksum(source_file)
        dest_checksum = compute_file_checksum(dest_file)

        if source_checksum == dest_checksum:
            diff.files_unchanged.append(relative_path)
            continue

        # Source differs from dest - check if user modified it
        if _is_file_modified(project_root, relative_path, config):
            # User has modified this file - create conflict
            diff.conflicts.append(
                Conflict(
                    file_path=relative_path,
                    reason="user_modified",
                    resolution_options=["keep_local", "use_framework", "skip"],
                )
            )
        else:
            # File wasn't modified by user, safe to update
            diff.files_to_update.append(
                FileChange(
                    path=relative_path,
                    change_type="update",
                    reason="Framework update",
                )
            )


def apply_updates(
    project_root: Path,
    components: list[str] | None = None,
    dry_run: bool = False,
    conflict_resolutions: dict[str, str] | None = None,
) -> UpdateResult:
    """Apply framework updates to the project.

    Args:
        project_root: Path to the project root directory.
        components: List of components to update. None means all.
        dry_run: If True, don't actually apply changes.
        conflict_resolutions: Dict mapping conflict file paths to resolution choices.

    Returns:
        UpdateResult with details of what was updated.
    """
    if conflict_resolutions is None:
        conflict_resolutions = {}

    result = UpdateResult(success=True)
    config = load_project_config(project_root)
    ldf_dir = project_root / ".ldf"
    checksums = config.get("_checksums", {})

    # Get the diff
    diff = get_update_diff(project_root, components)

    # Apply file additions
    for change in diff.files_to_add:
        if dry_run:
            result.files_updated.append(f"[+] {change.path}")
            continue

        try:
            _copy_framework_file(ldf_dir, change.path, checksums)
            result.files_updated.append(f"[+] {change.path}")
        except Exception as e:
            result.errors.append(f"Failed to add {change.path}: {e}")
            result.success = False

    # Apply file updates
    for change in diff.files_to_update:
        if dry_run:
            result.files_updated.append(f"[~] {change.path}")
            continue

        try:
            _copy_framework_file(ldf_dir, change.path, checksums)
            result.files_updated.append(f"[~] {change.path}")
        except Exception as e:
            result.errors.append(f"Failed to update {change.path}: {e}")
            result.success = False

    # Handle conflicts based on resolutions
    for conflict in diff.conflicts:
        resolution = conflict_resolutions.get(conflict.file_path, "skip")

        if resolution == "skip":
            result.files_skipped.append(f"[!] {conflict.file_path} (skipped)")
        elif resolution == "keep_local":
            result.files_skipped.append(f"[=] {conflict.file_path} (kept local)")
        elif resolution == "use_framework":
            if dry_run:
                result.files_updated.append(f"[~] {conflict.file_path} (would replace)")
                continue

            try:
                _copy_framework_file(ldf_dir, conflict.file_path, checksums)
                result.files_updated.append(f"[~] {conflict.file_path} (replaced)")
            except Exception as e:
                result.errors.append(f"Failed to update {conflict.file_path}: {e}")
                result.success = False

    # Update config with new version and checksums
    if not dry_run and result.success:
        config["framework_version"] = __version__
        config["framework_updated"] = datetime.now().isoformat()
        config["_checksums"] = checksums
        save_project_config(project_root, config)

    return result


def _copy_framework_file(ldf_dir: Path, relative_path: str, checksums: dict) -> None:
    """Copy a file from the framework to the project.

    Args:
        ldf_dir: Path to the .ldf directory.
        relative_path: Relative path within .ldf (e.g., "templates/design.md").
        checksums: Dict to update with new checksum.
    """
    parts = relative_path.split("/")
    component = parts[0]
    filename = "/".join(parts[1:])

    # Determine source path
    if component == "templates":
        source = FRAMEWORK_DIR / "templates" / filename
    elif component == "macros":
        source = FRAMEWORK_DIR / "macros" / filename
    elif component == "question-packs":
        # Handle both v1.1 paths (question-packs/core/security.yaml)
        # and legacy paths (question-packs/security.yaml)
        if filename.startswith("core/") or filename.startswith("optional/"):
            # v1.1 path: question-packs/core/security.yaml
            # Map optional/ to domain/ in framework source
            if filename.startswith("optional/"):
                source = FRAMEWORK_DIR / "question-packs" / "domain" / filename[9:]
            else:
                source = FRAMEWORK_DIR / "question-packs" / filename
        else:
            # Legacy path: question-packs/security.yaml
            # Check core first, then domain
            source = FRAMEWORK_DIR / "question-packs" / "core" / filename
            if not source.exists():
                source = FRAMEWORK_DIR / "question-packs" / "domain" / filename
    else:
        raise ValueError(f"Unknown component: {component}")

    if not source.exists():
        raise FileNotFoundError(f"Source file not found: {source}")

    dest = ldf_dir / relative_path
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(source, dest)

    # Update checksum
    checksums[relative_path] = compute_file_checksum(dest)


def print_update_check(info: UpdateInfo) -> None:
    """Print the update check results."""
    console.print()
    console.print(f"[bold]Current framework version:[/bold] {info.current_version}")
    console.print(f"[bold]Latest framework version:[/bold]  {info.latest_version}")
    console.print()

    if not info.has_updates:
        console.print("[green]Your project is up to date![/green]")
        return

    console.print("[yellow]Updates available:[/yellow]")
    for component in info.updatable_components:
        console.print(f"  - {component}/")

    console.print()
    console.print("Run [cyan]ldf update --dry-run[/cyan] to preview changes.")


def print_update_diff(diff: UpdateDiff, dry_run: bool = False) -> None:
    """Print the update diff in a readable format."""
    console.print()

    if dry_run:
        console.print("[bold]Preview of changes:[/bold]")
    else:
        console.print("[bold]Changes to apply:[/bold]")

    console.print()

    # Group by component
    by_component: dict[str, list[str]] = {}

    for change in diff.files_to_add:
        component = change.path.split("/")[0]
        by_component.setdefault(component, []).append(f"  [green]+[/green] {change.path}")

    for change in diff.files_to_update:
        component = change.path.split("/")[0]
        by_component.setdefault(component, []).append(f"  [yellow]~[/yellow] {change.path}")

    for conflict in diff.conflicts:
        component = conflict.file_path.split("/")[0]
        by_component.setdefault(component, []).append(
            f"  [red]![/red] {conflict.file_path} [dim](LOCAL CHANGES)[/dim]"
        )

    for path in diff.files_unchanged:
        component = path.split("/")[0]
        by_component.setdefault(component, []).append(
            f"  [dim]=[/dim] {path} [dim](no changes)[/dim]"
        )

    # Print by component
    for component in sorted(by_component.keys()):
        console.print(f"[bold]{component}/[/bold]")
        for line in by_component[component]:
            console.print(line)
        console.print()

    # Summary
    total_changes = len(diff.files_to_add) + len(diff.files_to_update)
    if diff.conflicts:
        console.print(
            f"[yellow]{len(diff.conflicts)} file(s) with local changes require resolution.[/yellow]"
        )
    if total_changes > 0:
        action = "Would update" if dry_run else "Will update"
        console.print(f"{action} {total_changes} file(s).")
    elif not diff.conflicts:
        console.print("[green]No changes needed.[/green]")


def print_update_result(result: UpdateResult) -> None:
    """Print the update result summary."""
    console.print()

    if result.files_updated:
        console.print("[bold]Updated files:[/bold]")
        for f in result.files_updated:
            console.print(f"  {f}")

    if result.files_skipped:
        console.print()
        console.print("[bold]Skipped files:[/bold]")
        for f in result.files_skipped:
            console.print(f"  {f}")

    if result.errors:
        console.print()
        console.print("[bold red]Errors:[/bold red]")
        for e in result.errors:
            console.print(f"  [red]{e}[/red]")

    console.print()
    if result.success:
        console.print("[green]Update complete![/green]")
    else:
        console.print("[red]Update completed with errors.[/red]")
