"""Tests for ldf.convert module."""

from pathlib import Path

from ldf.convert import (
    LANGUAGE_PATTERNS,
    SKIP_DIRS,
    ConversionContext,
    ImportResult,
    analyze_existing_codebase,
    generate_backwards_fill_prompt,
    import_backwards_fill,
)


class TestConversionContext:
    """Tests for ConversionContext dataclass."""

    def test_defaults(self, tmp_path):
        """Test default values."""
        ctx = ConversionContext(project_root=tmp_path)

        assert ctx.project_root == tmp_path
        assert ctx.detected_languages == []
        assert ctx.detected_frameworks == []
        assert ctx.existing_tests == []
        assert ctx.existing_docs == []
        assert ctx.source_files == []
        assert ctx.suggested_preset is None
        assert ctx.suggested_question_packs == []


class TestImportResult:
    """Tests for ImportResult dataclass."""

    def test_defaults(self):
        """Test default values."""
        result = ImportResult(success=True, spec_name="test")

        assert result.success is True
        assert result.spec_name == "test"
        assert result.files_created == []
        assert result.errors == []
        assert result.warnings == []


class TestAnalyzeExistingCodebase:
    """Tests for analyze_existing_codebase function."""

    def test_empty_project(self, tmp_path):
        """Test analysis of empty project."""
        ctx = analyze_existing_codebase(tmp_path)

        assert ctx.project_root == tmp_path
        assert ctx.detected_languages == []
        assert ctx.suggested_preset == "custom"

    def test_detects_python_project(self, tmp_path):
        """Test detection of Python project."""
        (tmp_path / "pyproject.toml").write_text("[tool.pytest]")
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("print('hello')")

        ctx = analyze_existing_codebase(tmp_path)

        assert "python" in ctx.detected_languages

    def test_detects_typescript_project(self, tmp_path):
        """Test detection of TypeScript project."""
        (tmp_path / "tsconfig.json").write_text('{"compilerOptions": {}}')
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "app.ts").write_text("export const foo = 1")

        ctx = analyze_existing_codebase(tmp_path)

        assert "typescript" in ctx.detected_languages

    def test_detects_multiple_languages(self, tmp_path):
        """Test detection of multiple languages."""
        (tmp_path / "pyproject.toml").write_text("[tool.pytest]")
        (tmp_path / "package.json").write_text('{"name": "test"}')
        (tmp_path / "app.py").write_text("print('hello')")
        (tmp_path / "app.js").write_text("console.log('hello')")

        ctx = analyze_existing_codebase(tmp_path)

        assert "python" in ctx.detected_languages
        assert "javascript" in ctx.detected_languages

    def test_detects_fastapi_framework(self, tmp_path):
        """Test detection of FastAPI framework."""
        (tmp_path / "requirements.txt").write_text("fastapi>=0.100.0")
        (tmp_path / "app.py").write_text("from fastapi import FastAPI")

        ctx = analyze_existing_codebase(tmp_path)

        assert "fastapi" in ctx.detected_frameworks

    def test_detects_react_framework(self, tmp_path):
        """Test detection of React framework."""
        (tmp_path / "package.json").write_text('{"dependencies": {"react": "^18.0.0"}}')

        ctx = analyze_existing_codebase(tmp_path)

        assert "react" in ctx.detected_frameworks

    def test_suggests_saas_preset(self, tmp_path):
        """Test suggestion of SaaS preset based on patterns."""
        (tmp_path / "models.py").write_text("class Tenant:\n    subscription_id = ...")
        (tmp_path / "billing.py").write_text("def process_subscription():")

        ctx = analyze_existing_codebase(tmp_path)

        assert ctx.suggested_preset == "saas"

    def test_suggests_fintech_preset(self, tmp_path):
        """Test suggestion of fintech preset based on patterns."""
        (tmp_path / "ledger.py").write_text("class Transaction:\n    def process_payment():")

        ctx = analyze_existing_codebase(tmp_path)

        assert ctx.suggested_preset == "fintech"

    def test_suggests_healthcare_preset(self, tmp_path):
        """Test suggestion of healthcare preset based on patterns."""
        (tmp_path / "patient.py").write_text("class Patient:\n    medical_record = ...")

        ctx = analyze_existing_codebase(tmp_path)

        assert ctx.suggested_preset == "healthcare"

    def test_finds_test_files(self, tmp_path):
        """Test detection of test files."""
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "test_main.py").write_text("def test_foo(): pass")
        (tmp_path / "tests" / "test_utils.py").write_text("def test_bar(): pass")

        ctx = analyze_existing_codebase(tmp_path)

        assert len(ctx.existing_tests) >= 2
        assert any("test_main" in str(f) for f in ctx.existing_tests)

    def test_finds_doc_files(self, tmp_path):
        """Test detection of documentation files."""
        (tmp_path / "README.md").write_text("# My Project")
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "guide.md").write_text("# Guide")

        ctx = analyze_existing_codebase(tmp_path)

        assert any("README" in str(f) for f in ctx.existing_docs)

    def test_skips_excluded_directories(self, tmp_path):
        """Test that excluded directories are skipped."""
        (tmp_path / "node_modules").mkdir()
        (tmp_path / "node_modules" / "lodash").mkdir()
        (tmp_path / "node_modules" / "lodash" / "index.js").write_text("module.exports = {}")
        (tmp_path / ".venv").mkdir()
        (tmp_path / ".venv" / "lib" / "python3.10").mkdir(parents=True)
        (tmp_path / ".git").mkdir()
        (tmp_path / ".git" / "config").write_text("")

        # Also add a real source file
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("print('hello')")

        ctx = analyze_existing_codebase(tmp_path)

        # Should not include files from excluded dirs
        for f in ctx.source_files:
            assert "node_modules" not in str(f)
            assert ".venv" not in str(f)
            assert ".git" not in str(f)

    def test_limits_file_counts(self, tmp_path):
        """Test that file counts are limited."""
        # Create many source files
        (tmp_path / "src").mkdir()
        for i in range(100):
            (tmp_path / "src" / f"file_{i}.py").write_text(f"# File {i}")

        ctx = analyze_existing_codebase(tmp_path)

        assert len(ctx.source_files) <= 50  # MAX_SOURCE_FILES

    def test_finds_api_definitions(self, tmp_path):
        """Test detection of API definition files."""
        (tmp_path / "openapi.yaml").write_text("openapi: 3.0.0")

        ctx = analyze_existing_codebase(tmp_path)

        assert len(ctx.existing_api_files) == 1
        assert any("openapi.yaml" in str(f) for f in ctx.existing_api_files)


class TestGenerateBackwardsFillPrompt:
    """Tests for generate_backwards_fill_prompt function."""

    def test_includes_project_info(self, tmp_path):
        """Test that prompt includes project information."""
        ctx = ConversionContext(
            project_root=tmp_path,
            detected_languages=["python"],
            detected_frameworks=["fastapi"],
            suggested_preset="api-only",
            suggested_question_packs=["security", "testing"],
        )

        prompt = generate_backwards_fill_prompt(ctx)

        assert str(tmp_path) in prompt
        assert "python" in prompt
        assert "fastapi" in prompt
        assert "api-only" in prompt

    def test_includes_file_lists(self, tmp_path):
        """Test that prompt includes file lists."""
        ctx = ConversionContext(
            project_root=tmp_path,
            source_files=[Path("src/main.py"), Path("src/utils.py")],
            existing_tests=[Path("tests/test_main.py")],
            existing_docs=[Path("README.md")],
            config_files=[Path("pyproject.toml")],
        )

        prompt = generate_backwards_fill_prompt(ctx)

        assert "src/main.py" in prompt
        assert "tests/test_main.py" in prompt
        assert "README.md" in prompt

    def test_includes_domain_instructions(self, tmp_path):
        """Test that prompt includes domain-specific instructions."""
        ctx = ConversionContext(project_root=tmp_path)

        prompt = generate_backwards_fill_prompt(ctx)

        assert "Security" in prompt
        assert "Testing" in prompt
        assert "API Design" in prompt
        assert "Data Model" in prompt

    def test_includes_output_format(self, tmp_path):
        """Test that prompt includes output format markers."""
        ctx = ConversionContext(project_root=tmp_path)

        prompt = generate_backwards_fill_prompt(ctx)

        assert "# === ANSWERPACK:" in prompt
        assert "# === SPEC:" in prompt
        assert "security.yaml" in prompt
        assert "requirements.md" in prompt

    def test_truncates_long_file_lists(self, tmp_path):
        """Test that long file lists are truncated."""
        source_files = [Path(f"src/file_{i}.py") for i in range(50)]
        ctx = ConversionContext(
            project_root=tmp_path,
            source_files=source_files,
        )

        prompt = generate_backwards_fill_prompt(ctx)

        assert "... and" in prompt  # Truncation indicator


class TestImportBackwardsFill:
    """Tests for import_backwards_fill function."""

    def test_parses_answerpack_sections(self, tmp_path):
        """Test parsing of answerpack sections."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()
        (ldf_dir / "answerpacks").mkdir()
        (ldf_dir / "specs").mkdir()

        content = """
# === ANSWERPACK: security.yaml ===
pack: security
feature: test
answers:
  - question: "What auth?"
    answer: "JWT"

# === ANSWERPACK: testing.yaml ===
pack: testing
feature: test
answers:
  - question: "What framework?"
    answer: "pytest"
"""

        result = import_backwards_fill(content, tmp_path, "test-feature")

        assert result.success is True
        assert "answerpacks/test-feature/security.yaml" in result.files_created
        assert "answerpacks/test-feature/testing.yaml" in result.files_created

    def test_parses_spec_sections(self, tmp_path):
        """Test parsing of spec sections."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()
        (ldf_dir / "answerpacks").mkdir()
        (ldf_dir / "specs").mkdir()

        content = """
# === SPEC: requirements.md ===
# Test Feature - Requirements

## Overview

This is a test.

# === SPEC: design.md ===
# Test Feature - Design

## Architecture

Simple design.
"""

        result = import_backwards_fill(content, tmp_path, "test-feature")

        assert result.success is True
        assert "specs/test-feature/requirements.md" in result.files_created
        assert "specs/test-feature/design.md" in result.files_created

    def test_creates_files_correctly(self, tmp_path):
        """Test that files are created with correct content."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()
        (ldf_dir / "answerpacks").mkdir()
        (ldf_dir / "specs").mkdir()

        content = """
# === ANSWERPACK: security.yaml ===
pack: security
feature: test
answers:
  - question: "What auth?"
    answer: "JWT"

# === SPEC: requirements.md ===
# Test - Requirements

## Overview

Test overview.
"""

        result = import_backwards_fill(content, tmp_path, "my-spec")

        assert result.success is True

        # Check answerpack file
        ap_file = ldf_dir / "answerpacks" / "my-spec" / "security.yaml"
        assert ap_file.exists()
        assert "pack: security" in ap_file.read_text()

        # Check spec file
        spec_file = ldf_dir / "specs" / "my-spec" / "requirements.md"
        assert spec_file.exists()
        assert "# Test - Requirements" in spec_file.read_text()

    def test_dry_run_no_changes(self, tmp_path):
        """Test that dry run doesn't create files."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()
        (ldf_dir / "answerpacks").mkdir()
        (ldf_dir / "specs").mkdir()

        content = """
# === ANSWERPACK: security.yaml ===
pack: security
feature: test
answers: []

# === SPEC: requirements.md ===
# Test - Requirements
"""

        result = import_backwards_fill(content, tmp_path, "test-feature", dry_run=True)

        assert result.success is True
        assert len(result.files_created) == 2

        # Files should NOT exist
        assert not (ldf_dir / "answerpacks" / "test-feature" / "security.yaml").exists()
        assert not (ldf_dir / "specs" / "test-feature" / "requirements.md").exists()

    def test_invalid_yaml_error(self, tmp_path):
        """Test error handling for invalid YAML."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()
        (ldf_dir / "answerpacks").mkdir()
        (ldf_dir / "specs").mkdir()

        content = """
# === ANSWERPACK: security.yaml ===
pack: security
invalid: yaml: [unclosed
"""

        result = import_backwards_fill(content, tmp_path, "test-feature")

        assert result.success is False
        assert any("Invalid YAML" in e for e in result.errors)

    def test_no_sections_error(self, tmp_path):
        """Test error when no valid sections found."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()
        (ldf_dir / "answerpacks").mkdir()
        (ldf_dir / "specs").mkdir()

        content = """
This is just some text without any markers.
No answerpack or spec sections here.
"""

        result = import_backwards_fill(content, tmp_path, "test-feature")

        assert result.success is False
        assert any("No valid sections" in e for e in result.errors)

    def test_warns_missing_expected_files(self, tmp_path):
        """Test warnings for missing expected files."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()
        (ldf_dir / "answerpacks").mkdir()
        (ldf_dir / "specs").mkdir()

        # Only provide one answerpack and one spec
        content = """
# === ANSWERPACK: security.yaml ===
pack: security
feature: test
answers: []

# === SPEC: requirements.md ===
# Test - Requirements

Overview.
"""

        result = import_backwards_fill(content, tmp_path, "test-feature")

        assert result.success is True
        # Should warn about missing expected files
        assert any("testing.yaml" in w for w in result.warnings)
        assert any("design.md" in w or "tasks.md" in w for w in result.warnings)

    def test_warns_non_dict_yaml(self, tmp_path):
        """Test warning for YAML that's not a dict."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()
        (ldf_dir / "answerpacks").mkdir()
        (ldf_dir / "specs").mkdir()

        content = """
# === ANSWERPACK: security.yaml ===
- just a list
- not a dict
"""

        result = import_backwards_fill(content, tmp_path, "test-feature")

        assert any("not a valid YAML dict" in w for w in result.warnings)

    def test_warns_missing_pack_field(self, tmp_path):
        """Test warning for missing 'pack' field in answerpack."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()
        (ldf_dir / "answerpacks").mkdir()
        (ldf_dir / "specs").mkdir()

        content = """
# === ANSWERPACK: security.yaml ===
feature: test
answers:
  - question: "What?"
    answer: "Something"
"""

        result = import_backwards_fill(content, tmp_path, "test-feature")

        assert any("Missing 'pack' field" in w for w in result.warnings)

    def test_default_spec_name(self, tmp_path):
        """Test default spec name is 'existing-system'."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()
        (ldf_dir / "answerpacks").mkdir()
        (ldf_dir / "specs").mkdir()

        content = """
# === SPEC: requirements.md ===
# Requirements
"""

        result = import_backwards_fill(content, tmp_path)

        assert result.spec_name == "existing-system"
        assert "specs/existing-system/requirements.md" in result.files_created


class TestLanguagePatterns:
    """Tests for language detection patterns."""

    def test_all_languages_have_extensions(self):
        """Test that all language patterns have extensions."""
        for lang, patterns in LANGUAGE_PATTERNS.items():
            assert "extensions" in patterns
            assert len(patterns["extensions"]) > 0

    def test_all_languages_have_config_files(self):
        """Test that all language patterns have config files."""
        for lang, patterns in LANGUAGE_PATTERNS.items():
            assert "config_files" in patterns
            assert len(patterns["config_files"]) > 0


class TestSkipDirs:
    """Tests for skip directories constant."""

    def test_common_skip_dirs_included(self):
        """Test that common directories to skip are included."""
        assert ".git" in SKIP_DIRS
        assert "node_modules" in SKIP_DIRS
        assert "__pycache__" in SKIP_DIRS
        assert ".venv" in SKIP_DIRS
        assert "venv" in SKIP_DIRS


class TestAnalyzeCodebaseEdgeCases:
    """Tests for edge cases in analyze_existing_codebase."""

    def test_framework_detection_read_error(self, tmp_path, monkeypatch):
        """Test framework detection handles file read errors."""
        # Create a project with files that will trigger framework search
        (tmp_path / "requirements.txt").write_text("fastapi>=0.100.0")
        (tmp_path / "app.py").write_text("from fastapi import FastAPI")

        # Make one file unreadable by patching
        original_read_text = Path.read_text

        def mock_read_text(self, *args, **kwargs):
            if "app.py" in str(self):
                raise PermissionError("Cannot read file")
            return original_read_text(self, *args, **kwargs)

        monkeypatch.setattr(Path, "read_text", mock_read_text)

        # Should not raise - exception is caught
        ctx = analyze_existing_codebase(tmp_path)
        assert ctx.project_root == tmp_path

    def test_preset_detection_read_error(self, tmp_path, monkeypatch):
        """Test preset detection handles file read errors."""
        # Create config file
        (tmp_path / "config.yaml").write_text("key: value")

        original_read_text = Path.read_text

        call_count = [0]

        def mock_read_text(self, *args, **kwargs):
            call_count[0] += 1
            # Fail on content building phase
            if call_count[0] > 1:
                raise PermissionError("Cannot read file")
            return original_read_text(self, *args, **kwargs)

        monkeypatch.setattr(Path, "read_text", mock_read_text)

        # Should not raise - exception is caught
        ctx = analyze_existing_codebase(tmp_path)
        assert ctx.suggested_preset == "custom"


class TestImportBackwardsFillSecurity:
    """Security tests for import_backwards_fill path traversal prevention."""

    def test_rejects_path_traversal_with_dotdot(self, tmp_path):
        """Test that import_backwards_fill rejects spec names with .. path traversal."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()
        (ldf_dir / "answerpacks").mkdir()
        (ldf_dir / "specs").mkdir()

        content = """
# === SPEC: requirements.md ===
# Test - Requirements
"""

        result = import_backwards_fill(content, tmp_path, "../escape")

        assert result.success is False
        assert any("Invalid spec name" in e for e in result.errors)
        # Ensure no escape directory was created
        escape_dir = tmp_path.parent / "escape"
        assert not escape_dir.exists()

    def test_rejects_absolute_path_unix(self, tmp_path):
        """Test that import_backwards_fill rejects absolute Unix paths."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()

        content = """
# === SPEC: requirements.md ===
# Test - Requirements
"""

        result = import_backwards_fill(content, tmp_path, "/etc/passwd")

        assert result.success is False
        assert any("Invalid spec name" in e for e in result.errors)

    def test_rejects_absolute_path_windows(self, tmp_path):
        """Test that import_backwards_fill rejects absolute Windows paths."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()

        content = """
# === SPEC: requirements.md ===
# Test - Requirements
"""

        result = import_backwards_fill(content, tmp_path, "\\Users\\test")

        assert result.success is False
        assert any("Invalid spec name" in e for e in result.errors)

    def test_rejects_forward_slash_in_name(self, tmp_path):
        """Test that import_backwards_fill rejects names with forward slashes."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()

        content = """
# === SPEC: requirements.md ===
# Test - Requirements
"""

        result = import_backwards_fill(content, tmp_path, "my/feature")

        assert result.success is False
        assert any("path separators" in e for e in result.errors)

    def test_rejects_backslash_in_name(self, tmp_path):
        """Test that import_backwards_fill rejects names with backslashes."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()

        content = """
# === SPEC: requirements.md ===
# Test - Requirements
"""

        result = import_backwards_fill(content, tmp_path, "my\\feature")

        assert result.success is False
        assert any("path separators" in e for e in result.errors)


class TestImportBackwardsFillEdgeCases:
    """Tests for edge cases in import_backwards_fill."""

    def test_warns_missing_answers_field(self, tmp_path):
        """Test warning for missing 'answers' field in answerpack."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()
        (ldf_dir / "answerpacks").mkdir()
        (ldf_dir / "specs").mkdir()

        content = """
# === ANSWERPACK: security.yaml ===
pack: security
feature: test
"""

        result = import_backwards_fill(content, tmp_path, "test-feature")

        assert any("Missing 'answers' field" in w for w in result.warnings)

    def test_warns_spec_no_header(self, tmp_path):
        """Test warning when spec content doesn't start with header."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()
        (ldf_dir / "answerpacks").mkdir()
        (ldf_dir / "specs").mkdir()

        content = """
# === SPEC: requirements.md ===
Not a header, just text content.
Some more text.
"""

        result = import_backwards_fill(content, tmp_path, "test-feature")

        assert any("doesn't start with a markdown header" in w for w in result.warnings)


class TestPrintConversionContext:
    """Tests for print_conversion_context function."""

    def test_prints_no_languages_detected(self, tmp_path, capsys):
        """Test printing when no languages are detected."""
        from ldf.convert import print_conversion_context

        ctx = ConversionContext(
            project_root=tmp_path,
            detected_languages=[],
            detected_frameworks=[],
            suggested_preset="custom",
            suggested_question_packs=[],
        )

        print_conversion_context(ctx)

        captured = capsys.readouterr()
        assert "None detected" in captured.out

    def test_prints_no_frameworks_detected(self, tmp_path, capsys):
        """Test printing when no frameworks are detected."""
        from ldf.convert import print_conversion_context

        ctx = ConversionContext(
            project_root=tmp_path,
            detected_languages=["python"],
            detected_frameworks=[],
            suggested_preset="custom",
            suggested_question_packs=["security"],
        )

        print_conversion_context(ctx)

        captured = capsys.readouterr()
        assert "python" in captured.out
        assert "None detected" in captured.out

    def test_prints_full_context(self, tmp_path, capsys):
        """Test printing full context with all fields."""
        from ldf.convert import print_conversion_context

        ctx = ConversionContext(
            project_root=tmp_path,
            detected_languages=["python", "typescript"],
            detected_frameworks=["fastapi", "react"],
            suggested_preset="saas",
            suggested_question_packs=["security", "testing"],
            source_files=[Path("src/main.py")],
            existing_tests=[Path("tests/test_main.py")],
            existing_docs=[Path("README.md")],
            config_files=[Path("pyproject.toml")],
            existing_api_files=[Path("openapi.yaml")],
        )

        print_conversion_context(ctx)

        captured = capsys.readouterr()
        assert "python, typescript" in captured.out
        assert "fastapi, react" in captured.out
        assert "saas" in captured.out
        assert "Source files: 1" in captured.out


class TestPrintImportResult:
    """Tests for print_import_result function."""

    def test_prints_files_created(self, capsys):
        """Test printing files created section."""
        from ldf.convert import print_import_result

        result = ImportResult(
            success=True,
            spec_name="my-feature",
            files_created=[
                "specs/my-feature/requirements.md",
                "answerpacks/my-feature/security.yaml",
            ],
        )

        print_import_result(result)

        captured = capsys.readouterr()
        assert "Files Created" in captured.out
        assert "specs/my-feature/requirements.md" in captured.out

    def test_prints_files_skipped(self, capsys):
        """Test printing files skipped section."""
        from ldf.convert import print_import_result

        result = ImportResult(
            success=True,
            spec_name="my-feature",
            files_created=["specs/my-feature/requirements.md"],
            files_skipped=["specs/my-feature/design.md"],
        )

        print_import_result(result)

        captured = capsys.readouterr()
        assert "Files Skipped" in captured.out
        assert "design.md" in captured.out

    def test_prints_warnings(self, capsys):
        """Test printing warnings section."""
        from ldf.convert import print_import_result

        result = ImportResult(
            success=True,
            spec_name="my-feature",
            files_created=["specs/my-feature/requirements.md"],
            warnings=["Missing expected file: tasks.md"],
        )

        print_import_result(result)

        captured = capsys.readouterr()
        assert "Warnings" in captured.out
        assert "Missing expected file: tasks.md" in captured.out

    def test_prints_success_message(self, capsys):
        """Test printing success message with spec location."""
        from ldf.convert import print_import_result

        result = ImportResult(
            success=True,
            spec_name="my-feature",
            files_created=["specs/my-feature/requirements.md"],
        )

        print_import_result(result)

        captured = capsys.readouterr()
        assert "Import complete" in captured.out
        assert "my-feature" in captured.out
        assert ".ldf/specs/my-feature/" in captured.out
        assert ".ldf/answerpacks/my-feature/" in captured.out

    def test_prints_failure_message(self, capsys):
        """Test printing failure message."""
        from ldf.convert import print_import_result

        result = ImportResult(
            success=False,
            spec_name="my-feature",
            errors=["Failed to parse YAML"],
        )

        print_import_result(result)

        captured = capsys.readouterr()
        assert "Import failed" in captured.out
        assert "Errors" in captured.out
        assert "Failed to parse YAML" in captured.out
