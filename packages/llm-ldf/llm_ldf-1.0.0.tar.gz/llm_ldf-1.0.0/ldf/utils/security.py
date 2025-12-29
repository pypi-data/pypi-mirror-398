"""Security utilities for path validation and traversal prevention.

This module provides centralized security validation functions to protect against:
- Path traversal attacks (../, absolute paths)
- Symlink escapes (symlinks pointing outside allowed directories)
- Hidden directory access
- Unicode normalization attacks
- Null byte injection

All validation functions follow a defense-in-depth approach with multiple layers
of security checks.
"""

from pathlib import Path


class SecurityError(ValueError):
    """Exception raised when security validation fails.

    This exception indicates a potential security violation such as:
    - Path traversal attempt
    - Symlink escape
    - Hidden directory access
    - Invalid path construction
    """

    pass


def validate_spec_name(spec_name: str, specs_dir: Path) -> Path:
    """Validate spec_name against path traversal and symlink attacks.

    This function provides comprehensive validation of user-provided spec names
    to prevent:
    1. Path traversal attacks (../, ../../, etc.)
    2. Absolute path references (/etc/passwd, C:\\Windows, etc.)
    3. Hidden directory access (.hidden, .git, etc.)
    4. Path separator injection (sub/dir when not expected)
    5. Symlink escapes (symlinks pointing outside specs_dir)

    Args:
        spec_name: User-provided spec name or directory name from filesystem
        specs_dir: Base specs directory (must be resolved to absolute path)

    Returns:
        Validated absolute resolved path to the spec directory

    Raises:
        SecurityError: If validation fails for any security reason

    Example:
        >>> specs_dir = Path("/project/.ldf/specs").resolve()
        >>> validate_spec_name("my-feature", specs_dir)
        Path('/project/.ldf/specs/my-feature')

        >>> validate_spec_name("../../../etc/passwd", specs_dir)
        SecurityError: Invalid spec name (path traversal detected): ../../../etc/passwd

    Security Checks:
        1. Reject ".." sequences (path traversal)
        2. Reject absolute paths starting with / or \\
        3. Reject hidden directories starting with .
        4. Reject path separators in name (prevents sub/dir injection)
        5. Resolve symlinks with .resolve()
        6. Verify resolved path is within specs_dir using .relative_to()
    """
    # Normalize and sanitize input
    spec_name = _normalize_string(spec_name)

    # Security Check 1: Reject obvious traversal attempts
    if ".." in spec_name:
        raise SecurityError(f"Invalid spec name (path traversal detected): {spec_name}")

    # Security Check 2: Reject absolute paths
    if spec_name.startswith("/") or spec_name.startswith("\\"):
        raise SecurityError(f"Invalid spec name (absolute path not allowed): {spec_name}")

    # Windows absolute path check (C:\, D:\, etc.)
    if len(spec_name) >= 2 and spec_name[1] == ":":
        raise SecurityError(f"Invalid spec name (absolute path not allowed): {spec_name}")

    # Security Check 3: Reject hidden directories
    if spec_name.startswith("."):
        raise SecurityError(f"Invalid spec name (hidden directory): {spec_name}")

    # Security Check 4: Reject path separators (prevents nested path injection)
    if "/" in spec_name or "\\" in spec_name:
        raise SecurityError(f"Spec name cannot contain path separators: {spec_name}")

    # Ensure specs_dir is resolved to absolute path
    specs_dir = specs_dir.resolve()

    # Construct and resolve the full path (this follows symlinks)
    spec_path = (specs_dir / spec_name).resolve()

    # Security Check 5: Verify resolved path is within specs_dir
    try:
        spec_path.relative_to(specs_dir)
    except ValueError:
        raise SecurityError(f"Spec path escapes specs directory: {spec_name}")

    # Security Check 6: Prevent targeting the base directory itself
    if spec_path == specs_dir:
        raise SecurityError(f"Spec name cannot target base directory: {spec_name}")

    return spec_path


def validate_spec_path_safe(spec_path: Path, base_dir: Path) -> Path:
    """Validate that a resolved path is safely within base_dir.

    This function ensures that a given path (which may be a symlink) resolves
    to a location within the specified base directory. Use this when you have
    a Path object (from iteration, etc.) and need to verify it's safe.

    Args:
        spec_path: Path to validate (can be a symlink)
        base_dir: Base directory that must contain spec_path

    Returns:
        Resolved absolute path (with symlinks followed)

    Raises:
        SecurityError: If resolved path is outside base_dir or equals base_dir

    Example:
        >>> base = Path("/project/.ldf/specs").resolve()
        >>> spec = base / "my-feature"
        >>> validate_spec_path_safe(spec, base)
        Path('/project/.ldf/specs/my-feature')

        >>> external = Path("/etc/passwd")
        >>> validate_spec_path_safe(external, base)
        SecurityError: Path escapes base directory: /etc/passwd
    """
    # Resolve both paths to absolute (follows symlinks)
    base_dir = base_dir.resolve()
    spec_path = spec_path.resolve()

    # Verify spec_path is within base_dir
    try:
        spec_path.relative_to(base_dir)
    except ValueError:
        raise SecurityError(f"Path escapes base directory: {spec_path}")

    # Prevent targeting the base directory itself
    if spec_path == base_dir:
        raise SecurityError(f"Path cannot target base directory: {spec_path}")

    return spec_path


def is_safe_directory_entry(path: Path, base_dir: Path) -> bool:
    """Check if a directory entry is safe during iteration.

    Use this function when iterating over directory contents (e.g., via .iterdir())
    to filter out potentially dangerous entries:
    - Symlinks pointing outside base_dir
    - Hidden directories (starting with .)
    - Special directories (. and ..)
    - Entries that would fail validate_spec_path_safe()

    This is safer than just checking `d.is_dir()` because it validates that
    symlinks don't escape the base directory.

    Args:
        path: Directory entry to check
        base_dir: Base directory that should contain the entry

    Returns:
        True if the entry is safe to include, False to filter out

    Example:
        >>> specs_dir = Path("/project/.ldf/specs").resolve()
        >>> for d in specs_dir.iterdir():
        ...     if d.is_dir() and is_safe_directory_entry(d, specs_dir):
        ...         print(f"Safe: {d.name}")
        ...     else:
        ...         print(f"Filtered: {d.name}")

    Security Filtering:
        - Returns False for hidden directories (.git, .hidden, etc.)
        - Returns False for symlinks pointing outside base_dir
        - Returns False for special directories (., ..)
        - Returns True for normal directories within base_dir
        - Returns True for symlinks within base_dir (pointing to valid targets)
    """
    # Filter out special directory entries
    if path.name in (".", ".."):
        return False

    # Filter out hidden directories
    if path.name.startswith("."):
        return False

    # Validate that path is safely within base_dir
    try:
        validate_spec_path_safe(path, base_dir)
        return True
    except SecurityError:
        return False


def _normalize_string(s: str) -> str:
    """Normalize string to prevent Unicode and encoding attacks.

    Protects against:
    - Unicode normalization attacks (é vs é)
    - Null byte injection (test\\x00/../../etc)
    - Overlong UTF-8 sequences

    Args:
        s: String to normalize

    Returns:
        Normalized string safe for path operations
    """
    import unicodedata

    # Normalize to NFC (composed form) to prevent normalization attacks
    normalized = unicodedata.normalize("NFC", s)

    # Remove null bytes (can cause path truncation in some systems)
    cleaned = normalized.replace("\x00", "")

    return cleaned
