"""Security tests for LDF path traversal and symlink protection.

This test suite validates all security controls in ldf/utils/security.py:
- Path traversal attack prevention
- Symlink escape protection
- Hidden directory rejection
- Unicode normalization attack prevention
- Null byte injection prevention
- Integration tests for audit.py, lint.py, and template.py
"""

import os
from pathlib import Path

import pytest

from ldf.utils.security import (
    SecurityError,
    is_safe_directory_entry,
    validate_spec_name,
    validate_spec_path_safe,
)


@pytest.fixture
def temp_project(tmp_path: Path) -> Path:
    """Create a temporary LDF project structure."""
    project = tmp_path / "project"
    project.mkdir()

    # Create .ldf directory structure
    ldf_dir = project / ".ldf"
    ldf_dir.mkdir()

    specs_dir = ldf_dir / "specs"
    specs_dir.mkdir()

    answerpacks_dir = ldf_dir / "answerpacks"
    answerpacks_dir.mkdir()

    return project


@pytest.fixture
def specs_dir(temp_project: Path) -> Path:
    """Get the specs directory from temp project."""
    return temp_project / ".ldf" / "specs"


class TestValidateSpecName:
    """Tests for validate_spec_name function."""

    def test_accepts_valid_spec_name(self, specs_dir: Path):
        """Test acceptance of valid spec names."""
        spec_dir = specs_dir / "my-feature"
        spec_dir.mkdir()

        result = validate_spec_name("my-feature", specs_dir)
        assert result == spec_dir.resolve()

    def test_accepts_spec_with_numbers(self, specs_dir: Path):
        """Test acceptance of spec names with numbers."""
        spec_dir = specs_dir / "feature-123"
        spec_dir.mkdir()

        result = validate_spec_name("feature-123", specs_dir)
        assert result == spec_dir.resolve()

    def test_accepts_spec_with_underscores(self, specs_dir: Path):
        """Test acceptance of spec names with underscores."""
        spec_dir = specs_dir / "my_feature"
        spec_dir.mkdir()

        result = validate_spec_name("my_feature", specs_dir)
        assert result == spec_dir.resolve()

    def test_rejects_dotdot_traversal(self, specs_dir: Path):
        """Test rejection of .. path traversal."""
        with pytest.raises(SecurityError, match="path traversal detected"):
            validate_spec_name("../escape", specs_dir)

    def test_rejects_multiple_dotdot_traversal(self, specs_dir: Path):
        """Test rejection of multiple .. sequences."""
        with pytest.raises(SecurityError, match="path traversal detected"):
            validate_spec_name("../../../../etc/passwd", specs_dir)

    def test_rejects_dotdot_in_middle(self, specs_dir: Path):
        """Test rejection of .. in middle of path."""
        with pytest.raises(SecurityError, match="path traversal detected"):
            validate_spec_name("foo/../bar", specs_dir)

    def test_rejects_absolute_unix_path(self, specs_dir: Path):
        """Test rejection of absolute Unix paths."""
        with pytest.raises(SecurityError, match="absolute path not allowed"):
            validate_spec_name("/etc/passwd", specs_dir)

    def test_rejects_absolute_windows_path(self, specs_dir: Path):
        """Test rejection of absolute Windows paths."""
        with pytest.raises(SecurityError, match="absolute path not allowed"):
            validate_spec_name("C:\\Windows\\System32", specs_dir)

    def test_rejects_backslash_prefix(self, specs_dir: Path):
        """Test rejection of backslash-prefixed paths."""
        with pytest.raises(SecurityError, match="absolute path not allowed"):
            validate_spec_name("\\etc\\passwd", specs_dir)

    def test_rejects_hidden_directory(self, specs_dir: Path):
        """Test rejection of hidden directories."""
        with pytest.raises(SecurityError, match="hidden directory"):
            validate_spec_name(".hidden", specs_dir)

    def test_rejects_git_directory(self, specs_dir: Path):
        """Test rejection of .git directory."""
        with pytest.raises(SecurityError, match="hidden directory"):
            validate_spec_name(".git", specs_dir)

    def test_rejects_forward_slash_in_name(self, specs_dir: Path):
        """Test rejection of forward slash in name."""
        with pytest.raises(SecurityError, match="path separators"):
            validate_spec_name("sub/dir", specs_dir)

    def test_rejects_backslash_in_name(self, specs_dir: Path):
        """Test rejection of backslash in name."""
        with pytest.raises(SecurityError, match="path separators"):
            validate_spec_name("sub\\dir", specs_dir)

    def test_rejects_targeting_base_directory(self, specs_dir: Path):
        """Test rejection of paths that target the base directory itself."""
        # This would happen if someone tries to use an empty string or "."
        # We prevent this by checking if resolved path equals specs_dir
        with pytest.raises(SecurityError):
            # Create a symlink that points to specs_dir itself
            if os.name != "nt":  # Skip on Windows
                symlink = specs_dir / "self-link"
                symlink.symlink_to(specs_dir)
                validate_spec_name("self-link", specs_dir)

    def test_rejects_symlink_escape_to_parent(self, specs_dir: Path, tmp_path: Path):
        """Test rejection of symlinks pointing outside specs_dir."""
        # Create external target
        external = tmp_path / "external"
        external.mkdir()
        (external / "secret.txt").write_text("secret data")

        # Create symlink in specs_dir pointing to external
        if os.name != "nt":  # Symlinks work differently on Windows
            symlink = specs_dir / "escape"
            symlink.symlink_to(external)

            with pytest.raises(SecurityError, match="escapes specs directory"):
                validate_spec_name("escape", specs_dir)

    def test_rejects_symlink_escape_to_root(self, specs_dir: Path):
        """Test rejection of symlinks pointing to system directories."""
        if os.name != "nt":  # Unix systems
            symlink = specs_dir / "passwd-link"
            symlink.symlink_to("/etc/passwd")

            with pytest.raises(SecurityError, match="escapes specs directory"):
                validate_spec_name("passwd-link", specs_dir)

    def test_accepts_symlink_within_specs_dir(self, specs_dir: Path):
        """Test acceptance of symlinks that stay within specs_dir."""
        # Create target within specs_dir
        target = specs_dir / "real-spec"
        target.mkdir()

        # Create symlink to it
        if os.name != "nt":  # Symlinks work differently on Windows
            symlink = specs_dir / "alias-spec"
            symlink.symlink_to(target)

            result = validate_spec_name("alias-spec", specs_dir)
            # Should resolve to target
            assert result == target.resolve()

    def test_rejects_null_byte_injection(self, specs_dir: Path):
        """Test rejection of null byte injection attacks."""
        # Null bytes should be stripped, but path separators will still be detected
        # after the null byte is removed
        with pytest.raises(SecurityError):
            validate_spec_name("test\x00/../../etc", specs_dir)


class TestValidateSpecPathSafe:
    """Tests for validate_spec_path_safe function."""

    def test_accepts_path_within_base(self, tmp_path: Path):
        """Test acceptance of path within base directory."""
        base = tmp_path / "base"
        base.mkdir()
        spec = base / "spec"
        spec.mkdir()

        result = validate_spec_path_safe(spec, base)
        assert result == spec.resolve()

    def test_accepts_nested_path_within_base(self, tmp_path: Path):
        """Test acceptance of nested paths within base."""
        base = tmp_path / "base"
        base.mkdir()
        nested = base / "level1" / "level2" / "spec"
        nested.mkdir(parents=True)

        result = validate_spec_path_safe(nested, base)
        assert result == nested.resolve()

    def test_rejects_path_outside_base(self, tmp_path: Path):
        """Test rejection of path outside base directory."""
        base = tmp_path / "base"
        base.mkdir()
        outside = tmp_path / "outside"
        outside.mkdir()

        with pytest.raises(SecurityError, match="escapes base directory"):
            validate_spec_path_safe(outside, base)

    def test_rejects_parent_directory(self, tmp_path: Path):
        """Test rejection of parent directory."""
        base = tmp_path / "base"
        base.mkdir()

        with pytest.raises(SecurityError):
            validate_spec_path_safe(tmp_path, base)

    def test_rejects_symlink_escape(self, tmp_path: Path):
        """Test rejection of symlink pointing outside base."""
        base = tmp_path / "base"
        base.mkdir()
        outside = tmp_path / "outside"
        outside.mkdir()

        if os.name != "nt":  # Symlinks work differently on Windows
            symlink = base / "escape"
            symlink.symlink_to(outside)

            with pytest.raises(SecurityError, match="escapes base directory"):
                validate_spec_path_safe(symlink, base)

    def test_rejects_relative_symlink_escape(self, tmp_path: Path):
        """Test rejection of relative symlink pointing outside base."""
        base = tmp_path / "base"
        base.mkdir()
        outside = tmp_path / "outside"
        outside.mkdir()

        if os.name != "nt":
            symlink = base / "escape"
            symlink.symlink_to("../../outside")

            with pytest.raises(SecurityError):
                validate_spec_path_safe(symlink, base)

    def test_accepts_symlink_within_base(self, tmp_path: Path):
        """Test acceptance of symlink within base."""
        base = tmp_path / "base"
        base.mkdir()
        target = base / "target"
        target.mkdir()

        if os.name != "nt":
            symlink = base / "link"
            symlink.symlink_to(target)

            result = validate_spec_path_safe(symlink, base)
            assert result == target.resolve()

    def test_rejects_targeting_base_itself(self, tmp_path: Path):
        """Test rejection of path that equals base directory."""
        base = tmp_path / "base"
        base.mkdir()

        with pytest.raises(SecurityError, match="cannot target base directory"):
            validate_spec_path_safe(base, base)


class TestIsSafeDirectoryEntry:
    """Tests for is_safe_directory_entry function."""

    def test_accepts_normal_directory(self, tmp_path: Path):
        """Test acceptance of normal directories."""
        base = tmp_path / "base"
        base.mkdir()
        spec = base / "spec"
        spec.mkdir()

        assert is_safe_directory_entry(spec, base) is True

    def test_accepts_directory_with_hyphens(self, tmp_path: Path):
        """Test acceptance of directories with hyphens."""
        base = tmp_path / "base"
        base.mkdir()
        spec = base / "my-feature"
        spec.mkdir()

        assert is_safe_directory_entry(spec, base) is True

    def test_accepts_directory_with_underscores(self, tmp_path: Path):
        """Test acceptance of directories with underscores."""
        base = tmp_path / "base"
        base.mkdir()
        spec = base / "my_feature"
        spec.mkdir()

        assert is_safe_directory_entry(spec, base) is True

    def test_rejects_hidden_directory(self, tmp_path: Path):
        """Test rejection of hidden directories."""
        base = tmp_path / "base"
        base.mkdir()
        hidden = base / ".hidden"
        hidden.mkdir()

        assert is_safe_directory_entry(hidden, base) is False

    def test_rejects_git_directory(self, tmp_path: Path):
        """Test rejection of .git directory."""
        base = tmp_path / "base"
        base.mkdir()
        git = base / ".git"
        git.mkdir()

        assert is_safe_directory_entry(git, base) is False

    def test_rejects_current_directory(self, tmp_path: Path):
        """Test rejection of . directory."""
        base = tmp_path / "base"
        base.mkdir()

        # Simulate . directory entry
        current = base / "."
        assert is_safe_directory_entry(current, base) is False

    def test_rejects_parent_directory(self, tmp_path: Path):
        """Test rejection of .. directory."""
        base = tmp_path / "base"
        base.mkdir()

        # Simulate .. directory entry
        parent = base / ".."
        assert is_safe_directory_entry(parent, base) is False

    def test_rejects_symlink_to_outside(self, tmp_path: Path):
        """Test rejection of symlinks pointing outside base."""
        base = tmp_path / "base"
        base.mkdir()
        outside = tmp_path / "outside"
        outside.mkdir()

        if os.name != "nt":
            symlink = base / "escape"
            symlink.symlink_to(outside)

            assert is_safe_directory_entry(symlink, base) is False

    def test_accepts_symlink_within_base(self, tmp_path: Path):
        """Test acceptance of symlinks within base."""
        base = tmp_path / "base"
        base.mkdir()
        target = base / "target"
        target.mkdir()

        if os.name != "nt":
            symlink = base / "link"
            symlink.symlink_to(target)

            assert is_safe_directory_entry(symlink, base) is True

    def test_filters_during_iteration(self, tmp_path: Path):
        """Test filtering during directory iteration."""
        base = tmp_path / "base"
        base.mkdir()

        # Create various entries
        (base / "good1").mkdir()
        (base / "good2").mkdir()
        (base / ".hidden").mkdir()

        if os.name != "nt":
            outside = tmp_path / "outside"
            outside.mkdir()
            (base / "bad-link").symlink_to(outside)

        # Filter using is_safe_directory_entry
        safe_entries = [
            d.name for d in base.iterdir() if d.is_dir() and is_safe_directory_entry(d, base)
        ]

        assert "good1" in safe_entries
        assert "good2" in safe_entries
        assert ".hidden" not in safe_entries
        if os.name != "nt":
            assert "bad-link" not in safe_entries


class TestSecurityIntegration:
    """Integration tests for security in audit.py, lint.py, and template.py."""

    def test_spec_name_validation_in_audit_workflow(self, temp_project: Path):
        """Test that audit operations would reject path traversal."""
        specs_dir = temp_project / ".ldf" / "specs"

        # This should raise SecurityError
        with pytest.raises(SecurityError):
            validate_spec_name("../../../etc/passwd", specs_dir)

        # Verify no files created outside project
        assert not (temp_project.parent.parent.parent / "etc").exists()

    def test_spec_name_validation_in_lint_workflow(self, temp_project: Path):
        """Test that lint operations would reject path traversal."""
        specs_dir = temp_project / ".ldf" / "specs"

        # This should raise SecurityError
        with pytest.raises(SecurityError):
            validate_spec_name("../../../../etc/passwd", specs_dir)

        # Verify no files accessed outside project
        assert not (temp_project.parent.parent.parent / "etc").exists()

    def test_iteration_filtering_prevents_symlink_escape(self, temp_project: Path):
        """Test that iteration with is_safe_directory_entry filters symlinks."""
        specs_dir = temp_project / ".ldf" / "specs"

        # Create a good spec
        good_spec = specs_dir / "good-spec"
        good_spec.mkdir()

        # Create a symlink escape attempt
        if os.name != "nt":
            external = temp_project.parent / "external"
            external.mkdir()
            (external / "secret.txt").write_text("secret")

            escape_link = specs_dir / "escape"
            escape_link.symlink_to(external)

            # Iteration with filtering should only include good_spec
            safe_specs = [
                d
                for d in specs_dir.iterdir()
                if d.is_dir() and is_safe_directory_entry(d, specs_dir)
            ]

            assert len(safe_specs) == 1
            assert safe_specs[0].name == "good-spec"


class TestUnicodeAndEncodingAttacks:
    """Tests for Unicode normalization and encoding attack prevention."""

    def test_rejects_null_byte_in_name(self, specs_dir: Path):
        """Test rejection of null bytes in spec names."""
        # Null bytes are stripped, but if they're used for injection,
        # the path separator check will catch it
        with pytest.raises(SecurityError):
            validate_spec_name("test\x00../escape", specs_dir)

    def test_handles_unicode_normalization(self, specs_dir: Path):
        """Test handling of Unicode normalization."""
        # Create a spec with composed Unicode
        spec_name = "café"  # é as single character (NFC)
        spec_dir = specs_dir / spec_name
        spec_dir.mkdir()

        # Both composed and decomposed forms should work
        result = validate_spec_name(spec_name, specs_dir)
        assert result.exists()

    def test_rejects_unicode_dot_characters(self, specs_dir: Path):
        """Test rejection of Unicode dot characters that could bypass checks."""
        # Some Unicode characters look like dots but aren't ASCII dots
        # The normalize function should handle these
        fake_dots = "․․"  # U+2024 (one dot leader)
        with pytest.raises(SecurityError):
            validate_spec_name(f"{fake_dots}/escape", specs_dir)


class TestMCPSpecInspectorValidation:
    """Tests for MCP spec inspector's _validate_spec_name function."""

    @pytest.fixture
    def mcp_server_module(self, tmp_path: Path):
        """Set up MCP server module for testing, skip if mcp not installed."""
        import sys

        try:
            import mcp  # noqa: F401
        except ImportError:
            pytest.skip("mcp package not installed")

        sys.path.insert(0, str(Path(__file__).parent.parent / "ldf" / "_mcp_servers" / "spec_inspector"))

        specs_dir = tmp_path / "specs"
        specs_dir.mkdir()

        import server
        original_specs_dir = server.specs_dir
        server.specs_dir = specs_dir

        yield server, specs_dir

        server.specs_dir = original_specs_dir
        sys.path.pop(0)

    def test_rejects_nested_path_with_hidden_dir(self, mcp_server_module):
        """Test rejection of paths like 'foo/.hidden' that access hidden dirs."""
        server, _ = mcp_server_module

        # Should reject nested paths with hidden directories
        with pytest.raises(ValueError, match="path separators"):
            server._validate_spec_name("foo/.hidden")

        # Should reject any path with separators
        with pytest.raises(ValueError, match="path separators"):
            server._validate_spec_name("foo/bar")

        with pytest.raises(ValueError, match="path separators"):
            server._validate_spec_name("a\\b")

    def test_mcp_validation_consistency_with_shared_security(self, mcp_server_module):
        """Test that MCP validation is consistent with shared security utilities."""
        server, specs_dir = mcp_server_module

        # All these should be rejected by both MCP and shared security
        bad_names = [
            "../escape",
            "foo/../bar",
            "/etc/passwd",
            ".hidden",
            "foo/bar",
            "a\\b",
        ]

        for name in bad_names:
            with pytest.raises(ValueError):
                server._validate_spec_name(name)

            with pytest.raises(SecurityError):
                validate_spec_name(name, specs_dir)
