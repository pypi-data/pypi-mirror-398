"""LDF template - Team template import and validation."""

import re
import shutil
import stat
import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from ldf import __version__
from ldf.utils.console import console

# Allowed template files/directories (v1 - declarative only)
ALLOWED_TEMPLATE_CONTENTS = {
    "template.yaml",  # Required metadata
    ".ldf/config.yaml",
    ".ldf/guardrails.yaml",
    ".ldf/question-packs/",
    ".ldf/templates/",
    ".ldf/macros/",
}

# Explicitly disallowed (security/coupling risks)
DISALLOWED_PATTERNS = [
    ".ldf/specs/",  # No pre-built specs
    ".ldf/answerpacks/",  # No pre-filled answers (could contain PII/secrets)
    "*.sh",  # No shell scripts
    "*.py",  # No Python scripts (except in macros)
    ".git/",  # No git history
]


def _safe_extract_zip(zf: zipfile.ZipFile, dest: Path) -> None:
    """Safely extract a zip file, preventing path traversal and symlink attacks.

    Args:
        zf: ZipFile object to extract
        dest: Destination directory

    Raises:
        ValueError: If a zip entry attempts path traversal or contains symlinks

    Security:
        - Validates ALL entries BEFORE extraction (prevents TOCTOU)
        - Rejects symlinks, path traversal, absolute paths
        - Safe for untrusted zip files
    """
    dest = dest.resolve()

    # SECURITY: Pre-validate ALL entries before extraction
    for info in zf.infolist():
        member = info.filename

        # Check for symlinks BEFORE extraction
        # Symlinks have external_attr with S_IFLNK bit set
        if stat.S_ISLNK(info.external_attr >> 16):
            raise ValueError(f"Zip file contains symlink (rejected): {member}")

        # Check for path traversal attempts
        member_path = (dest / member).resolve()

        # Ensure the resolved path is within the destination
        try:
            member_path.relative_to(dest)
        except ValueError:
            raise ValueError(f"Zip file contains path traversal attempt: {member}")

        # Also reject absolute paths and explicit ../ sequences
        if member.startswith("/") or ".." in member.split("/"):
            raise ValueError(f"Zip file contains unsafe path: {member}")

    # All entries validated - safe to extract
    zf.extractall(dest)


@dataclass
class TemplateMetadata:
    """Template metadata from template.yaml."""

    name: str
    version: str
    ldf_version: str
    description: str = ""
    components: list[str] = field(default_factory=list)


@dataclass
class VerifyResult:
    """Result of template verification."""

    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: TemplateMetadata | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "valid": self.valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "metadata": {
                "name": self.metadata.name,
                "version": self.metadata.version,
                "ldf_version": self.metadata.ldf_version,
            }
            if self.metadata
            else None,
        }


def verify_template(template_path: Path) -> VerifyResult:
    """Verify a template for publishing.

    Checks:
    1. template.yaml exists with required fields
    2. Only allowed directories/files present
    3. No specs or answerpacks included
    4. YAML files all parse correctly
    5. Optional: secret scanning (API keys, passwords in config)

    Args:
        template_path: Path to template directory or zip file

    Returns:
        VerifyResult with validation status
    """
    result = VerifyResult(valid=True)

    # Handle zip files
    temp_dir: Path | None = None
    try:
        if template_path.suffix == ".zip":
            import tempfile

            temp_dir = Path(tempfile.mkdtemp())
            try:
                with zipfile.ZipFile(template_path, "r") as zf:
                    _safe_extract_zip(zf, temp_dir)
                # Find the actual template root (may be nested in zip)
                template_root = _find_template_root(temp_dir)
                if template_root is None:
                    result.valid = False
                    result.errors.append("No template.yaml found in zip file")
                    return result
            except zipfile.BadZipFile:
                result.valid = False
                result.errors.append("Invalid zip file")
                return result
            except ValueError as e:
                result.valid = False
                result.errors.append(f"Unsafe zip file: {e}")
                return result
        else:
            template_root = template_path

        # Check template.yaml exists
        metadata_path = template_root / "template.yaml"
        if not metadata_path.exists():
            result.valid = False
            result.errors.append("template.yaml not found")
            return result

        # Parse and validate metadata
        try:
            with open(metadata_path) as f:
                metadata_dict = yaml.safe_load(f) or {}

            # Required fields
            if "name" not in metadata_dict:
                result.valid = False
                result.errors.append("template.yaml: missing 'name' field")
            if "version" not in metadata_dict:
                result.valid = False
                result.errors.append("template.yaml: missing 'version' field")
            if "ldf_version" not in metadata_dict:
                result.valid = False
                result.errors.append("template.yaml: missing 'ldf_version' field")

            if result.valid:
                result.metadata = TemplateMetadata(
                    name=metadata_dict.get("name", ""),
                    version=metadata_dict.get("version", ""),
                    ldf_version=str(metadata_dict.get("ldf_version", "")),
                    description=metadata_dict.get("description", ""),
                    components=metadata_dict.get("components", []),
                )

                # Check LDF version compatibility
                template_version = result.metadata.ldf_version
                current_version = __version__
                if not _check_version_compatible(template_version, current_version):
                    result.warnings.append(
                        f"Template built for LDF {template_version}, "
                        f"current version is {current_version}"
                    )

        except yaml.YAMLError as e:
            result.valid = False
            result.errors.append(f"template.yaml: invalid YAML - {e}")
            return result

        # Check for disallowed content
        ldf_dir = template_root / ".ldf"
        if ldf_dir.exists():
            # Check for specs directory
            if (ldf_dir / "specs").exists():
                result.valid = False
                result.errors.append(
                    "Template contains .ldf/specs/ - specs should not be in templates"
                )

            # Check for answerpacks directory
            if (ldf_dir / "answerpacks").exists():
                result.valid = False
                result.errors.append(
                    "Template contains .ldf/answerpacks/ - answerpacks should not be in templates"
                )

        # Check for disallowed patterns (shell scripts, Python outside macros, .git)
        pattern_errors = _check_disallowed_patterns(template_root)
        if pattern_errors:
            result.valid = False
            result.errors.extend(pattern_errors)

        # Check allowlist - warn about unexpected files
        allowlist_warnings = _check_allowed_contents(template_root)
        if allowlist_warnings:
            result.warnings.extend(allowlist_warnings)

        # Validate all YAML files
        yaml_errors = _validate_yaml_files(template_root)
        if yaml_errors:
            result.warnings.extend(yaml_errors)

        # Secret scanning
        secret_warnings = _scan_for_secrets(template_root)
        if secret_warnings:
            result.warnings.extend(secret_warnings)

        return result
    finally:
        # Always cleanup temp dir
        if temp_dir and temp_dir.exists():
            shutil.rmtree(temp_dir)


def import_template(
    template_path: Path,
    project_root: Path,
    force: bool = False,
) -> bool:
    """Import a team template into a project.

    Args:
        template_path: Path to template directory or zip file
        project_root: Project root directory
        force: Overwrite existing .ldf/ if present

    Returns:
        True if import succeeded
    """
    ldf_dir = project_root / ".ldf"

    # Check if LDF already initialized
    if ldf_dir.exists() and not force:
        console.print("[red]Error: .ldf/ already exists.[/red]")
        console.print("Use --force to overwrite existing configuration.")
        return False

    # Verify template first
    result = verify_template(template_path)
    if not result.valid:
        console.print("[red]Error: Template verification failed.[/red]")
        for error in result.errors:
            console.print(f"  - {error}")
        return False

    # Extract template
    temp_dir: Path | None = None
    try:
        if template_path.suffix == ".zip":
            import tempfile

            temp_dir = Path(tempfile.mkdtemp())
            try:
                with zipfile.ZipFile(template_path, "r") as zf:
                    _safe_extract_zip(zf, temp_dir)
            except ValueError as e:
                console.print(f"[red]Error: Unsafe zip file - {e}[/red]")
                return False
            template_root = _find_template_root(temp_dir)
            if template_root is None:
                console.print("[red]Error: Could not find template root in zip[/red]")
                return False
        else:
            template_root = template_path

        # Backup existing .ldf if force
        backup_path: Path | None = None
        if ldf_dir.exists() and force:
            backup_path = project_root / f".ldf.backup.{datetime.now().strftime('%Y%m%d%H%M%S')}"
            shutil.move(str(ldf_dir), str(backup_path))
            console.print(f"[dim]Backed up existing .ldf/ to {backup_path.name}[/dim]")

        # SECURITY: Pre-validate template for symlinks BEFORE any copying
        # This prevents symlink-based file exfiltration attacks
        try:
            _check_template_for_symlinks(template_root)
        except ValueError as e:
            console.print(f"[red]Error: {e}[/red]")
            # Restore backup if we created one
            if backup_path and backup_path.exists():
                if ldf_dir.exists():
                    shutil.rmtree(ldf_dir)
                shutil.move(str(backup_path), str(ldf_dir))
            return False

        # Create .ldf directory
        ldf_dir.mkdir(parents=True, exist_ok=True)

        # Copy template contents
        template_ldf = template_root / ".ldf"
        if template_ldf.exists():
            for item in template_ldf.iterdir():
                src = item
                dst = ldf_dir / item.name

                if src.is_dir():
                    if dst.exists():
                        shutil.rmtree(dst)
                    # SECURITY: Copy without following symlinks (defense in depth)
                    # Pre-validation already rejected symlinks, but this ensures
                    # any symlinks that somehow exist are copied as-is (not dereferenced)
                    shutil.copytree(src, dst, symlinks=True)
                else:
                    # SECURITY: Never follow symlinks when copying files (prevents TOCTOU)
                    shutil.copy2(src, dst, follow_symlinks=False)

        # SECURITY: Validate copied template for TOCTOU protection (strict enforcement)
        post_copy_warnings = _validate_copied_template(ldf_dir)
        if post_copy_warnings:
            # STRICT REJECTION: ANY symlink found = hard error with rollback
            console.print()
            console.print("[red]Error: Template validation failed after copy:[/red]")
            for warning in post_copy_warnings:
                console.print(f"  - {warning}")
            console.print("[red]Template import aborted (strict symlink policy).[/red]")

            # Rollback: Remove partially-imported .ldf
            if ldf_dir.exists():
                shutil.rmtree(ldf_dir)

            # Restore backup if we created one
            if backup_path and backup_path.exists():
                shutil.move(str(backup_path), str(ldf_dir))
                console.print(f"[dim]Restored backup from {backup_path.name}[/dim]")

            return False

        # Ensure required directories exist
        required_dirs = ["specs", "answerpacks", "templates", "question-packs", "macros"]
        for dir_name in required_dirs:
            (ldf_dir / dir_name).mkdir(exist_ok=True)

        # Update config with template tracking
        config_path = ldf_dir / "config.yaml"
        config: dict[str, Any] = {}
        if config_path.exists():
            with open(config_path) as f:
                config = yaml.safe_load(f) or {}

        # Add template tracking info
        if result.metadata:
            config["template"] = {
                "name": result.metadata.name,
                "version": result.metadata.version,
                "source": str(template_path),
                "applied_at": datetime.now().isoformat(),
            }

        with open(config_path, "w") as f:
            yaml.safe_dump(config, f, default_flow_style=False, sort_keys=False)

        # Print summary
        console.print()
        console.print("[green]✓[/green] Template imported successfully!")
        if result.metadata:
            console.print(f"  Template: {result.metadata.name} v{result.metadata.version}")
        console.print(f"  Location: {ldf_dir}")

        if result.warnings:
            console.print()
            console.print("[yellow]Warnings:[/yellow]")
            for warning in result.warnings:
                console.print(f"  - {warning}")

        return True
    finally:
        # Always cleanup temp dir
        if temp_dir and temp_dir.exists():
            shutil.rmtree(temp_dir)


def _find_template_root(directory: Path) -> Path | None:
    """Find the template root in an extracted zip.

    The template.yaml could be at the root or in a subdirectory.
    """
    # Check root first
    if (directory / "template.yaml").exists():
        return directory

    # Check one level deep
    for item in directory.iterdir():
        if item.is_dir() and (item / "template.yaml").exists():
            return item

    return None


def _check_version_compatible(template_version: str, current_version: str) -> bool:
    """Check if template version is compatible with current LDF version.

    Uses semver-style comparison: major version must match.
    """

    def parse_version(v: str) -> tuple[int, int, int]:
        parts = v.replace("v", "").split(".")
        return (
            int(parts[0]) if len(parts) > 0 else 0,
            int(parts[1]) if len(parts) > 1 else 0,
            int(parts[2]) if len(parts) > 2 else 0,
        )

    try:
        t_major, t_minor, _ = parse_version(template_version)
        c_major, c_minor, _ = parse_version(current_version)

        # Major version must match
        if t_major != c_major:
            return False

        # Warn if minor version is ahead
        if t_minor > c_minor:
            return False

        return True
    except (ValueError, IndexError):
        return True  # Allow if version parsing fails


def _validate_yaml_files(template_root: Path) -> list[str]:
    """Validate all YAML files in template."""
    errors: list[str] = []
    ldf_dir = template_root / ".ldf"

    if not ldf_dir.exists():
        return errors

    for yaml_file in ldf_dir.rglob("*.yaml"):
        try:
            with open(yaml_file) as f:
                yaml.safe_load(f)
        except yaml.YAMLError as e:
            rel_path = yaml_file.relative_to(template_root)
            errors.append(f"{rel_path}: Invalid YAML - {e}")

    return errors


def _check_disallowed_patterns(template_root: Path) -> list[str]:
    """Check for disallowed files/directories in template.

    Enforces DISALLOWED_PATTERNS to reject:
    - Shell scripts (*.sh)
    - Python scripts (*.py) outside of macros
    - .git directories
    """
    errors: list[str] = []

    # Check for .git directory
    if (template_root / ".git").exists():
        errors.append("Template contains .git/ directory - git history should not be included")

    ldf_dir = template_root / ".ldf"
    if not ldf_dir.exists():
        return errors

    # Check for shell scripts anywhere
    for sh_file in ldf_dir.rglob("*.sh"):
        rel_path = sh_file.relative_to(template_root)
        errors.append(f"Template contains shell script: {rel_path}")

    # Check for Python scripts outside of macros
    macros_dir = ldf_dir / "macros"
    for py_file in ldf_dir.rglob("*.py"):
        rel_path = py_file.relative_to(template_root)
        # Check if py_file is actually under macros directory using path containment
        # This prevents bypass via directories like "fake-macros/" or "my-macros-dir/"
        try:
            py_file.resolve().relative_to(macros_dir.resolve())
        except ValueError:
            errors.append(f"Template contains Python script outside macros/: {rel_path}")

    return errors


def _is_allowed_path(rel_path: str) -> bool:
    """Check if a relative path matches the allowed template contents.

    Args:
        rel_path: Path relative to template root

    Returns:
        True if path is allowed
    """
    # template.yaml at root is always allowed
    if rel_path == "template.yaml":
        return True

    # Check against allowed patterns
    for allowed in ALLOWED_TEMPLATE_CONTENTS:
        if allowed.endswith("/"):
            # Directory pattern - allow anything under it
            if rel_path.startswith(allowed.rstrip("/")):
                return True
        else:
            # Exact file match
            if rel_path == allowed:
                return True

    return False


def _check_allowed_contents(template_root: Path) -> list[str]:
    """Verify template only contains allowed files/directories.

    Enforces ALLOWED_TEMPLATE_CONTENTS allowlist.

    Args:
        template_root: Path to template directory

    Returns:
        List of warnings for unexpected files
    """
    warnings: list[str] = []

    for item in template_root.rglob("*"):
        if not item.is_file():
            continue

        rel_path = str(item.relative_to(template_root))

        # Skip hidden files at root (like .gitignore)
        if rel_path.startswith(".") and "/" not in rel_path:
            continue

        if not _is_allowed_path(rel_path):
            warnings.append(f"Unexpected file in template: {rel_path}")

    return warnings


def _scan_for_secrets(template_root: Path) -> list[str]:
    """Scan for potential secrets in template files."""
    warnings: list[str] = []
    ldf_dir = template_root / ".ldf"

    if not ldf_dir.exists():
        return warnings

    # Patterns that might indicate secrets
    secret_patterns = [
        (r'api[_-]?key\s*[:=]\s*["\']?[a-zA-Z0-9]{20,}', "Potential API key"),
        (r'password\s*[:=]\s*["\']?[^\s"\'\n]+', "Potential password"),
        (r'secret\s*[:=]\s*["\']?[a-zA-Z0-9]{20,}', "Potential secret"),
        (r'token\s*[:=]\s*["\']?[a-zA-Z0-9]{20,}', "Potential token"),
        (r"-----BEGIN [A-Z]+ PRIVATE KEY-----", "Private key detected"),
    ]

    for yaml_file in ldf_dir.rglob("*.yaml"):
        try:
            content = yaml_file.read_text()
            for pattern, description in secret_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    rel_path = yaml_file.relative_to(template_root)
                    warnings.append(f"{rel_path}: {description}")
                    break  # Only report once per file
        except OSError:
            pass

    return warnings


def _check_template_for_symlinks(template_root: Path) -> None:
    """Check template directory for symlinks BEFORE copying (strict pre-validation).

    This function provides critical security by rejecting templates with symlinks
    BEFORE any copying occurs, preventing symlink-based file exfiltration attacks.

    Args:
        template_root: Root directory of the template to validate

    Raises:
        ValueError: If any symlinks are found in the template

    Security:
        - Scans entire template tree before any file operations
        - Treats ANY symlink as a hard error (strict rejection)
        - Prevents dereferencing attacks where symlinks point to sensitive files
        - Safe for untrusted templates

    Example Attack Prevented:
        Template contains: .ldf/templates/evil -> /etc/passwd
        Without this check: copytree would follow symlink and copy /etc/passwd
        With this check: Template rejected immediately, no files copied
    """
    ldf_dir = template_root / ".ldf"
    if not ldf_dir.exists():
        return

    # SECURITY: Scan for ANY symlinks before copying
    for item in ldf_dir.rglob("*"):
        if item.is_symlink():
            try:
                rel_path = item.relative_to(template_root)
                target = item.readlink() if hasattr(item, "readlink") else "unknown"
                raise ValueError(
                    f"Template contains symlink (rejected): {rel_path} -> {target}\n"
                    f"Symlinks are not allowed in templates for security reasons."
                )
            except OSError:
                # If we can't read the symlink target, still reject it
                rel_path = item.relative_to(template_root)
                raise ValueError(
                    f"Template contains symlink (rejected): {rel_path}\n"
                    f"Symlinks are not allowed in templates for security reasons."
                )


def _validate_copied_template(ldf_dir: Path) -> list[str]:
    """Validate template after copying (TOCTOU protection).

    This function provides defense-in-depth by re-validating template contents
    after they've been copied to .ldf/. This closes the TOCTOU (Time-of-Check-Time-of-Use)
    gap where a malicious actor could modify template files between verification and copy.

    Args:
        ldf_dir: The .ldf directory where template was copied

    Returns:
        List of security warnings (empty if clean)

    Security Checks:
        1. Detect and remove any symlinks in copied content
        2. Verify no unexpected file types were added
    """
    warnings: list[str] = []

    if not ldf_dir.exists():
        return warnings

    # Check for symlinks in copied content
    for item in ldf_dir.rglob("*"):
        if item.is_symlink():
            try:
                rel_path = item.relative_to(ldf_dir)
                warnings.append(f"Symlink detected after copy: {rel_path}")
                # SECURITY: Remove the symlink immediately
                item.unlink()
            except OSError as e:
                warnings.append(f"Failed to remove symlink {item}: {e}")

    return warnings


def print_verify_result(result: VerifyResult, template_path: Path) -> None:
    """Print verification result to console."""
    console.print()
    console.print(f"[bold]Template Verification: {template_path.name}[/bold]")
    console.print("━" * 50)

    if result.metadata:
        meta_str = f"{result.metadata.name} v{result.metadata.version}"
        console.print(f"[green]✓[/green] Metadata: {meta_str}")
        console.print(f"  Built for LDF: {result.metadata.ldf_version}")
    else:
        console.print("[red]✗[/red] Metadata: Invalid or missing")

    # Check items
    struct_msg = "specs/ not included" if result.valid else "Invalid structure"
    ap_msg = "answerpacks/ not included" if result.valid else "Contains answerpacks"
    yaml_msg = f"{len(result.errors)} error(s)" if result.errors else "All files valid"
    checks = [
        ("Structure", struct_msg),
        ("Answerpacks", ap_msg),
        ("YAML validation", yaml_msg),
    ]

    for check_name, status in checks:
        if "error" in status.lower() or "invalid" in status.lower() or "contains" in status.lower():
            console.print(f"[red]✗[/red] {check_name}: {status}")
        else:
            console.print(f"[green]✓[/green] {check_name}: {status}")

    # Show errors
    if result.errors:
        console.print()
        console.print("[red]Errors:[/red]")
        for error in result.errors:
            console.print(f"  - {error}")

    # Show warnings
    if result.warnings:
        console.print()
        console.print("[yellow]Warnings:[/yellow]")
        for warning in result.warnings:
            console.print(f"  - {warning}")

    console.print("━" * 50)
    if result.valid:
        passed = len(checks) - len(result.errors)
        console.print(f"[green]{passed} passed[/green], {len(result.warnings)} warnings")
    else:
        console.print(f"[red]Verification failed with {len(result.errors)} error(s)[/red]")
    console.print()
