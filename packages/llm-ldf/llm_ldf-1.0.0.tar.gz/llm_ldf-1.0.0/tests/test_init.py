"""Tests for ldf.init module."""

from pathlib import Path

import yaml

from ldf.init import (
    FRAMEWORK_DIR,
    _copy_macros,
    _copy_question_packs,
    _copy_templates,
    _create_agent_commands,
    _create_agent_md,
    _create_config,
    _create_directories,
    _create_guardrails,
    _print_summary,
    compute_file_checksum,
    initialize_project,
    repair_project,
)
from ldf.utils.descriptions import (
    get_core_packs,
    get_domain_packs,
    get_preset_recommended_packs,
)


class TestFrameworkDir:
    """Test framework directory."""

    def test_framework_dir_exists(self):
        """Test that the framework directory exists."""
        assert FRAMEWORK_DIR.exists()


class TestCreateDirectories:
    """Tests for _create_directories function."""

    def test_creates_all_directories(self, tmp_path: Path):
        """Test that all directories are created."""
        ldf_dir = tmp_path / ".ldf"
        _create_directories(ldf_dir)

        assert ldf_dir.exists()
        assert (ldf_dir / "specs").exists()
        assert (ldf_dir / "question-packs").exists()
        assert (ldf_dir / "answerpacks").exists()
        assert (ldf_dir / "templates").exists()
        assert (ldf_dir / "audit-history").exists()

    def test_idempotent(self, tmp_path: Path):
        """Test creating directories twice is safe."""
        ldf_dir = tmp_path / ".ldf"
        _create_directories(ldf_dir)
        _create_directories(ldf_dir)

        assert ldf_dir.exists()


class TestCreateConfig:
    """Tests for _create_config function."""

    def test_creates_config_file(self, tmp_path: Path):
        """Test that config file is created."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()

        _create_config(ldf_dir, "saas", ["security"], ["spec_inspector"])

        config_path = ldf_dir / "config.yaml"
        assert config_path.exists()

    def test_config_contains_preset(self, tmp_path: Path):
        """Test that config contains the preset."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()

        _create_config(ldf_dir, "fintech", ["security"], ["spec_inspector"])

        config_path = ldf_dir / "config.yaml"
        content = config_path.read_text()
        assert "fintech" in content

    def test_config_contains_question_packs(self, tmp_path: Path):
        """Test that config contains question packs."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()

        _create_config(ldf_dir, "custom", ["security", "testing"], [])

        config_path = ldf_dir / "config.yaml"
        content = config_path.read_text()
        assert "security" in content
        assert "testing" in content


class TestCreateGuardrails:
    """Tests for _create_guardrails function."""

    def test_creates_guardrails_file(self, tmp_path: Path):
        """Test that guardrails file is created."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()

        _create_guardrails(ldf_dir, "custom")

        guardrails_path = ldf_dir / "guardrails.yaml"
        assert guardrails_path.exists()

    def test_guardrails_extends_core(self, tmp_path: Path):
        """Test that guardrails extends core."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()

        _create_guardrails(ldf_dir, "custom")

        guardrails_path = ldf_dir / "guardrails.yaml"
        content = guardrails_path.read_text()
        assert "extends: core" in content

    def test_guardrails_with_preset(self, tmp_path: Path):
        """Test guardrails with a preset."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()

        _create_guardrails(ldf_dir, "saas")

        guardrails_path = ldf_dir / "guardrails.yaml"
        content = guardrails_path.read_text()
        assert "saas" in content

    def test_guardrails_with_custom_ids(self, tmp_path: Path):
        """Test guardrails with custom guardrail IDs."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()

        custom_ids = [1, 2, 3, 9, 10]
        _create_guardrails(ldf_dir, "custom", custom_guardrails=custom_ids)

        guardrails_path = ldf_dir / "guardrails.yaml"
        import yaml

        with open(guardrails_path) as f:
            content = yaml.safe_load(f)

        assert content.get("selected_ids") == custom_ids
        assert content.get("preset") is None  # Custom mode has no preset


class TestInitializeProject:
    """Tests for initialize_project function."""

    def test_non_interactive_creates_all_files(self, tmp_path: Path, monkeypatch):
        """Test non-interactive init creates all files."""
        monkeypatch.chdir(tmp_path)

        initialize_project(
            project_path=tmp_path,
            preset="custom",
            question_packs=[],
            mcp_servers=[],
            non_interactive=True,
        )

        assert (tmp_path / ".ldf").exists()
        assert (tmp_path / ".ldf" / "config.yaml").exists()
        assert (tmp_path / ".ldf" / "guardrails.yaml").exists()
        assert (tmp_path / "AGENT.md").exists()
        assert (tmp_path / ".agent" / "commands").exists()

    def test_creates_agent_commands(self, tmp_path: Path, monkeypatch):
        """Test that agent commands are created."""
        monkeypatch.chdir(tmp_path)

        initialize_project(
            project_path=tmp_path,
            preset="custom",
            question_packs=[],
            mcp_servers=[],
            non_interactive=True,
        )

        commands_dir = tmp_path / ".agent" / "commands"
        assert (commands_dir / "create-spec.md").exists()
        assert (commands_dir / "implement-task.md").exists()
        assert (commands_dir / "review-spec.md").exists()

    def test_custom_preset_uses_defaults(self, tmp_path: Path, monkeypatch):
        """Test that custom preset uses default question packs."""
        monkeypatch.chdir(tmp_path)

        initialize_project(
            project_path=tmp_path,
            preset="custom",
            question_packs=None,
            mcp_servers=None,
            non_interactive=True,
        )

        config_path = tmp_path / ".ldf" / "config.yaml"
        content = config_path.read_text()
        # Should have default question packs when none specified
        assert "security" in content

    def test_overwrite_confirmation_aborted(self, tmp_path: Path, monkeypatch, capsys):
        """Test that overwrite confirmation can abort."""
        monkeypatch.chdir(tmp_path)

        # Create existing .ldf directory
        (tmp_path / ".ldf").mkdir()

        # Mock Confirm.ask to return False
        monkeypatch.setattr("ldf.init.Confirm.ask", lambda *a, **kw: False)

        initialize_project(
            project_path=tmp_path,
            preset="custom",
            question_packs=[],
            mcp_servers=[],
            non_interactive=False,
        )

        captured = capsys.readouterr()
        assert "Aborted" in captured.out

    def test_overwrite_confirmation_accepted(self, tmp_path: Path, monkeypatch):
        """Test that overwrite confirmation can continue."""
        monkeypatch.chdir(tmp_path)

        # Create existing .ldf directory
        (tmp_path / ".ldf").mkdir()

        # Mock Confirm.ask to return True for overwrite
        monkeypatch.setattr("ldf.init.Confirm.ask", lambda *a, **kw: True)

        # Mock prompts module functions to avoid interactive prompts
        monkeypatch.setattr("ldf.init.prompt_guardrail_mode", lambda: "preset")
        monkeypatch.setattr("ldf.init.prompt_preset", lambda: "custom")
        monkeypatch.setattr("ldf.init.prompt_question_packs", lambda preset: ["security"])
        monkeypatch.setattr("ldf.init.prompt_mcp_servers", lambda: ["spec_inspector"])
        monkeypatch.setattr("ldf.init.prompt_install_hooks", lambda: False)
        monkeypatch.setattr("ldf.init.confirm_initialization", lambda *a, **kw: True)

        initialize_project(
            project_path=tmp_path,
            preset=None,
            question_packs=None,
            mcp_servers=None,
            non_interactive=False,
        )

        assert (tmp_path / ".ldf" / "config.yaml").exists()

    def test_with_hooks_installation(self, tmp_path: Path, monkeypatch):
        """Test initialization with hooks installation."""
        monkeypatch.chdir(tmp_path)

        # Create git repo
        (tmp_path / ".git").mkdir()

        initialize_project(
            project_path=tmp_path,
            preset="custom",
            question_packs=[],
            mcp_servers=[],
            non_interactive=True,
            install_hooks=True,
        )

        assert (tmp_path / ".ldf").exists()
        assert (tmp_path / ".git" / "hooks" / "pre-commit").exists()

    def test_creates_project_directory_if_not_exists(self, tmp_path: Path, monkeypatch):
        """Test that project directory is created if it doesn't exist."""
        new_project = tmp_path / "new-project"

        initialize_project(
            project_path=new_project,
            preset="custom",
            question_packs=[],
            mcp_servers=[],
            non_interactive=True,
        )

        assert new_project.exists()
        assert (new_project / ".ldf").exists()


class TestDescriptionsIntegration:
    """Tests for descriptions module integration with init."""

    def test_core_packs_defined(self):
        """Test that core packs are defined in descriptions."""
        core_packs = get_core_packs()
        assert len(core_packs) > 0
        assert "security" in core_packs
        assert "testing" in core_packs

    def test_domain_packs_defined(self):
        """Test that domain packs are defined in descriptions."""
        domain_packs = get_domain_packs()
        assert len(domain_packs) > 0
        assert "billing" in domain_packs
        assert "multi-tenancy" in domain_packs

    def test_preset_recommendations_exist(self):
        """Test that preset recommendations are defined."""
        saas_packs = get_preset_recommended_packs("saas")
        assert len(saas_packs) > 0
        # SaaS should recommend multi-tenancy
        assert "multi-tenancy" in saas_packs


class TestCopyQuestionPacks:
    """Tests for _copy_question_packs function."""

    def test_creates_placeholder_for_missing_pack(self, tmp_path: Path, capsys):
        """Test that missing domain packs get a placeholder in optional/."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()
        qp_dir = ldf_dir / "question-packs"
        qp_dir.mkdir()
        (qp_dir / "core").mkdir()
        (qp_dir / "optional").mkdir()

        _copy_question_packs(ldf_dir, ["nonexistent-pack"])

        # Now placeholders go in the optional/ subdirectory
        placeholder = ldf_dir / "question-packs" / "optional" / "nonexistent-pack.yaml"
        assert placeholder.exists()
        content = placeholder.read_text()
        assert "TODO:" in content


class TestCreateAgentMd:
    """Tests for _create_agent_md function."""

    def test_backup_existing_non_ldf_agent_md(self, tmp_path: Path, capsys):
        """Test that existing non-LDF AGENT.md is backed up."""
        # Create existing AGENT.md without LDF markers
        agent_md = tmp_path / "AGENT.md"
        agent_md.write_text("# My Custom Project Instructions\n\nThis is custom content.")

        _create_agent_md(tmp_path, "custom", ["security"])

        # Should have backed up the original
        backup = tmp_path / "AGENT.md.backup"
        assert backup.exists()
        assert "My Custom Project Instructions" in backup.read_text()

        captured = capsys.readouterr()
        assert "Backed up existing AGENT.md" in captured.out

    def test_no_backup_for_ldf_agent_md(self, tmp_path: Path, capsys):
        """Test that existing LDF AGENT.md is not backed up."""
        # Create existing AGENT.md with LDF marker
        agent_md = tmp_path / "AGENT.md"
        agent_md.write_text("# Project\n**Framework:** LDF\n")

        _create_agent_md(tmp_path, "custom", ["security"])

        # Should NOT have created a backup
        backup = tmp_path / "AGENT.md.backup"
        assert not backup.exists()

    def test_fintech_preset_coverage_threshold(self, tmp_path: Path):
        """Test that fintech preset uses 90% coverage threshold."""
        _create_agent_md(tmp_path, "fintech", ["security"])

        content = (tmp_path / "AGENT.md").read_text()
        assert "90%" in content

    def test_default_preset_coverage_threshold(self, tmp_path: Path):
        """Test that default preset uses 80% coverage threshold."""
        _create_agent_md(tmp_path, "custom", ["security"])

        content = (tmp_path / "AGENT.md").read_text()
        assert "80%" in content


class TestPrintSummary:
    """Tests for _print_summary function."""

    def test_summary_without_hooks(self, tmp_path: Path, capsys):
        """Test summary output without hooks installed."""
        _print_summary(tmp_path, "custom", ["security"], ["spec_inspector"], hooks_installed=False)

        captured = capsys.readouterr()
        assert "LDF initialized successfully" in captured.out
        assert "ldf hooks install" in captured.out  # Suggests installing hooks
        assert "Pre-commit hooks: installed" not in captured.out

    def test_summary_with_hooks(self, tmp_path: Path, capsys):
        """Test summary output with hooks installed."""
        _print_summary(tmp_path, "custom", ["security"], ["spec_inspector"], hooks_installed=True)

        captured = capsys.readouterr()
        assert "LDF initialized successfully" in captured.out
        assert "Pre-commit hooks:" in captured.out
        assert "installed" in captured.out
        assert ".git/hooks/pre-commit" in captured.out


class TestInitializeProjectInteractive:
    """Tests for initialize_project with interactive prompts."""

    def test_interactive_uses_prompts(self, tmp_path: Path, monkeypatch, capsys):
        """Test that interactive mode calls prompt functions."""
        monkeypatch.chdir(tmp_path)

        # Track which prompts were called
        prompts_called = []

        def mock_prompt_guardrail_mode():
            prompts_called.append("guardrail_mode")
            return "preset"

        def mock_prompt_preset():
            prompts_called.append("preset")
            return "custom"

        def mock_prompt_question_packs(preset):
            prompts_called.append("question_packs")
            return ["security"]

        def mock_prompt_mcp_servers():
            prompts_called.append("mcp_servers")
            return ["spec_inspector"]

        def mock_prompt_install_hooks():
            prompts_called.append("install_hooks")
            return False

        def mock_confirm_initialization(*args, **kwargs):
            prompts_called.append("confirm")
            return True

        # Mock all prompts
        monkeypatch.setattr("ldf.init.prompt_guardrail_mode", mock_prompt_guardrail_mode)
        monkeypatch.setattr("ldf.init.prompt_preset", mock_prompt_preset)
        monkeypatch.setattr("ldf.init.prompt_question_packs", mock_prompt_question_packs)
        monkeypatch.setattr("ldf.init.prompt_mcp_servers", mock_prompt_mcp_servers)
        monkeypatch.setattr("ldf.init.prompt_install_hooks", mock_prompt_install_hooks)
        monkeypatch.setattr("ldf.init.confirm_initialization", mock_confirm_initialization)

        initialize_project(
            project_path=tmp_path,
            preset=None,
            question_packs=None,
            mcp_servers=None,
            non_interactive=False,
        )

        # Should have called all prompt functions
        assert "guardrail_mode" in prompts_called
        assert "preset" in prompts_called
        assert "question_packs" in prompts_called
        assert "mcp_servers" in prompts_called
        assert "confirm" in prompts_called


class TestComputeFileChecksum:
    """Tests for compute_file_checksum function."""

    def test_computes_checksum(self, tmp_path: Path):
        """Test that checksum is computed correctly."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")

        checksum = compute_file_checksum(test_file)

        assert checksum is not None
        assert len(checksum) == 64  # SHA256 hex digest is 64 chars
        # Known SHA256 of "Hello, World!"
        assert checksum == "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"

    def test_different_content_different_checksum(self, tmp_path: Path):
        """Test that different content produces different checksums."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("Content A")
        file2.write_text("Content B")

        checksum1 = compute_file_checksum(file1)
        checksum2 = compute_file_checksum(file2)

        assert checksum1 != checksum2

    def test_same_content_same_checksum(self, tmp_path: Path):
        """Test that same content produces same checksums."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("Same content")
        file2.write_text("Same content")

        checksum1 = compute_file_checksum(file1)
        checksum2 = compute_file_checksum(file2)

        assert checksum1 == checksum2

    def test_large_file_checksum(self, tmp_path: Path):
        """Test checksum on a large file (tests chunked reading)."""
        large_file = tmp_path / "large.txt"
        # Create file larger than 8192 bytes (the chunk size)
        large_file.write_text("x" * 20000)

        checksum = compute_file_checksum(large_file)

        assert checksum is not None
        assert len(checksum) == 64


class TestKeyboardInterruptHandling:
    """Tests for KeyboardInterrupt handling in initialize_project."""

    def test_keyboard_interrupt_in_prompt_project_path(self, tmp_path: Path, monkeypatch, capsys):
        """Test KeyboardInterrupt during project path prompt."""
        monkeypatch.chdir(tmp_path)

        def mock_prompt_project_path():
            raise KeyboardInterrupt()

        monkeypatch.setattr("ldf.init.prompt_project_path", mock_prompt_project_path)

        # Call without project_path to trigger prompt
        initialize_project(
            project_path=None,
            preset="custom",
            question_packs=[],
            mcp_servers=[],
            non_interactive=False,
        )

        captured = capsys.readouterr()
        assert "Aborted" in captured.out
        # Should not have created .ldf directory
        assert not (tmp_path / ".ldf").exists()

    def test_keyboard_interrupt_during_interactive_config(
        self, tmp_path: Path, monkeypatch, capsys
    ):
        """Test KeyboardInterrupt during interactive configuration."""
        monkeypatch.chdir(tmp_path)

        def mock_prompt_guardrail_mode():
            raise KeyboardInterrupt()

        monkeypatch.setattr("ldf.init.prompt_guardrail_mode", mock_prompt_guardrail_mode)

        initialize_project(
            project_path=tmp_path,
            preset=None,  # Will trigger guardrail mode prompt first
            question_packs=None,
            mcp_servers=None,
            non_interactive=False,
        )

        captured = capsys.readouterr()
        assert "Aborted" in captured.out

    def test_keyboard_interrupt_during_question_packs_prompt(
        self, tmp_path: Path, monkeypatch, capsys
    ):
        """Test KeyboardInterrupt during question packs prompt."""
        monkeypatch.chdir(tmp_path)

        monkeypatch.setattr("ldf.init.prompt_guardrail_mode", lambda: "preset")
        monkeypatch.setattr("ldf.init.prompt_preset", lambda: "custom")

        def mock_prompt_question_packs(preset):
            raise KeyboardInterrupt()

        monkeypatch.setattr("ldf.init.prompt_question_packs", mock_prompt_question_packs)

        initialize_project(
            project_path=tmp_path,
            preset=None,
            question_packs=None,
            mcp_servers=None,
            non_interactive=False,
        )

        captured = capsys.readouterr()
        assert "Aborted" in captured.out


class TestDefaultMcpServersFallback:
    """Tests for default MCP servers fallback logic."""

    def test_fallback_mcp_servers_when_none_default(self, tmp_path: Path, monkeypatch):
        """Test that fallback MCP servers are used when no servers are marked default."""
        monkeypatch.chdir(tmp_path)

        # Mock get_all_mcp_servers to return servers
        monkeypatch.setattr("ldf.init.get_all_mcp_servers", lambda: ["server1", "server2"])
        # Mock is_mcp_server_default to return False for all
        monkeypatch.setattr("ldf.init.is_mcp_server_default", lambda s: False)

        initialize_project(
            project_path=tmp_path,
            preset="custom",
            question_packs=["security"],
            mcp_servers=None,  # Will trigger default selection
            non_interactive=True,
        )

        config_path = tmp_path / ".ldf" / "config.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Should have fallback servers (v1.1 schema: mcp_servers.servers is a list)
        assert "spec_inspector" in config["mcp_servers"]["servers"]
        assert "coverage_reporter" in config["mcp_servers"]["servers"]


class TestConfirmationAborted:
    """Tests for confirmation dialog being rejected."""

    def test_confirm_initialization_aborted(self, tmp_path: Path, monkeypatch, capsys):
        """Test that rejecting confirmation aborts initialization."""
        monkeypatch.chdir(tmp_path)

        monkeypatch.setattr("ldf.init.prompt_guardrail_mode", lambda: "preset")
        monkeypatch.setattr("ldf.init.prompt_preset", lambda: "custom")
        monkeypatch.setattr("ldf.init.prompt_question_packs", lambda preset: ["security"])
        monkeypatch.setattr("ldf.init.prompt_mcp_servers", lambda: ["spec_inspector"])
        monkeypatch.setattr("ldf.init.prompt_install_hooks", lambda: False)
        monkeypatch.setattr("ldf.init.confirm_initialization", lambda *a, **kw: False)

        initialize_project(
            project_path=tmp_path,
            preset=None,
            question_packs=None,
            mcp_servers=None,
            non_interactive=False,
        )

        captured = capsys.readouterr()
        assert "Aborted" in captured.out


class TestCopyTemplates:
    """Tests for _copy_templates function."""

    def test_copies_all_templates(self, tmp_path: Path):
        """Test that all spec templates are copied."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()
        (ldf_dir / "templates").mkdir()

        _copy_templates(ldf_dir)

        templates_dir = ldf_dir / "templates"
        assert (templates_dir / "requirements.md").exists()
        assert (templates_dir / "design.md").exists()
        assert (templates_dir / "tasks.md").exists()

    def test_handles_missing_source_templates(self, tmp_path: Path, monkeypatch):
        """Test that missing source templates are handled gracefully."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()
        (ldf_dir / "templates").mkdir()

        # Create a temp framework dir without templates
        fake_framework = tmp_path / "fake_framework"
        (fake_framework / "templates").mkdir(parents=True)

        monkeypatch.setattr("ldf.init.FRAMEWORK_DIR", fake_framework)

        # Should not raise an error
        _copy_templates(ldf_dir)


class TestCopyMacros:
    """Tests for _copy_macros function."""

    def test_copies_all_macros(self, tmp_path: Path):
        """Test that all macros are copied."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()

        _copy_macros(ldf_dir)

        macros_dir = ldf_dir / "macros"
        assert macros_dir.exists()
        assert (macros_dir / "clarify-first.md").exists()
        assert (macros_dir / "coverage-gate.md").exists()
        assert (macros_dir / "task-guardrails.md").exists()

    def test_creates_macros_directory(self, tmp_path: Path):
        """Test that macros directory is created if missing."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()

        _copy_macros(ldf_dir)

        assert (ldf_dir / "macros").exists()

    def test_handles_missing_source_macros(self, tmp_path: Path, monkeypatch):
        """Test that missing source macros are handled gracefully."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()

        # Create a temp framework dir without macros
        fake_framework = tmp_path / "fake_framework"
        (fake_framework / "macros").mkdir(parents=True)

        monkeypatch.setattr("ldf.init.FRAMEWORK_DIR", fake_framework)

        # Should not raise an error
        _copy_macros(ldf_dir)


class TestCreateAgentCommands:
    """Tests for _create_agent_commands function."""

    def test_creates_commands_directory(self, tmp_path: Path):
        """Test that .agent/commands directory is created."""
        _create_agent_commands(tmp_path)

        commands_dir = tmp_path / ".agent" / "commands"
        assert commands_dir.exists()

    def test_creates_all_command_files(self, tmp_path: Path):
        """Test that all command files are created."""
        _create_agent_commands(tmp_path)

        commands_dir = tmp_path / ".agent" / "commands"
        assert (commands_dir / "create-spec.md").exists()
        assert (commands_dir / "implement-task.md").exists()
        assert (commands_dir / "review-spec.md").exists()

    def test_command_file_contents(self, tmp_path: Path):
        """Test that command files have expected content."""
        _create_agent_commands(tmp_path)

        commands_dir = tmp_path / ".agent" / "commands"

        create_spec = (commands_dir / "create-spec.md").read_text()
        assert "feature-name" in create_spec
        assert "Question Packs" in create_spec

        implement_task = (commands_dir / "implement-task.md").read_text()
        assert "spec-name" in implement_task
        assert "task-number" in implement_task

        review_spec = (commands_dir / "review-spec.md").read_text()
        assert "Coverage-Gate" in review_spec


class TestRepairProject:
    """Tests for repair_project function."""

    def test_repair_creates_missing_directories(self, tmp_path: Path, capsys):
        """Test that repair creates missing directories."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()
        # Only create config
        (ldf_dir / "config.yaml").write_text("version: '1.0'\n")

        repair_project(tmp_path)

        captured = capsys.readouterr()
        assert "Repair complete" in captured.out
        assert (ldf_dir / "specs").exists()
        assert (ldf_dir / "question-packs").exists()
        assert (ldf_dir / "templates").exists()
        assert (ldf_dir / "macros").exists()
        assert (ldf_dir / "audit-history").exists()

    def test_repair_creates_missing_config(self, tmp_path: Path, capsys):
        """Test that repair creates missing config.yaml."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()
        (ldf_dir / "question-packs").mkdir()

        repair_project(tmp_path)

        captured = capsys.readouterr()
        assert "Created config.yaml" in captured.out
        assert (ldf_dir / "config.yaml").exists()

    def test_repair_creates_missing_guardrails(self, tmp_path: Path, capsys):
        """Test that repair creates missing guardrails.yaml."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()
        (ldf_dir / "config.yaml").write_text("version: '1.0'\n")

        repair_project(tmp_path)

        captured = capsys.readouterr()
        assert "Created guardrails.yaml" in captured.out
        assert (ldf_dir / "guardrails.yaml").exists()

    def test_repair_adds_missing_templates(self, tmp_path: Path, capsys):
        """Test that repair adds missing template files."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()
        (ldf_dir / "config.yaml").write_text("version: '1.0'\n")
        (ldf_dir / "templates").mkdir()
        # Only create one template
        (ldf_dir / "templates" / "requirements.md").write_text("# Requirements\n")

        repair_project(tmp_path)

        captured = capsys.readouterr()
        assert "Added template: design.md" in captured.out
        assert "Added template: tasks.md" in captured.out

    def test_repair_adds_missing_macros(self, tmp_path: Path, capsys):
        """Test that repair adds missing macro files."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()
        (ldf_dir / "config.yaml").write_text("version: '1.0'\n")
        (ldf_dir / "macros").mkdir()

        repair_project(tmp_path)

        captured = capsys.readouterr()
        assert "Added macro:" in captured.out

    def test_repair_adds_missing_question_packs(self, tmp_path: Path, capsys):
        """Test that repair adds missing question packs."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()
        qp_dir = ldf_dir / "question-packs"
        qp_dir.mkdir()
        (qp_dir / "core").mkdir()
        (qp_dir / "optional").mkdir()
        # Use v1.1 schema with core/optional structure
        config = {
            "_schema_version": "1.1",
            "ldf": {"version": "1.0.0"},
            "question_packs": {"core": ["security", "testing"], "optional": []},
        }
        (ldf_dir / "config.yaml").write_text(yaml.safe_dump(config))

        repair_project(tmp_path)

        captured = capsys.readouterr()
        assert "Added question pack:" in captured.out
        # Question packs are now in core/ subdirectory
        assert (ldf_dir / "question-packs" / "core" / "security.yaml").exists()

    def test_repair_creates_agent_md(self, tmp_path: Path, capsys):
        """Test that repair creates missing AGENT.md."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()
        (ldf_dir / "config.yaml").write_text("version: '1.0'\n")

        repair_project(tmp_path)

        captured = capsys.readouterr()
        assert "Created AGENT.md" in captured.out
        assert (tmp_path / "AGENT.md").exists()

    def test_repair_creates_agent_commands(self, tmp_path: Path, capsys):
        """Test that repair creates missing .agent/commands."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()
        (ldf_dir / "config.yaml").write_text("version: '1.0'\n")

        repair_project(tmp_path)

        captured = capsys.readouterr()
        assert "Created .agent/commands/" in captured.out
        assert (tmp_path / ".agent" / "commands" / "create-spec.md").exists()

    def test_repair_updates_config_with_missing_fields(self, tmp_path: Path, capsys):
        """Test that repair adds missing fields to existing config."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()
        (ldf_dir / "question-packs").mkdir()
        # Create config without framework_version or checksums
        config = {"version": "1.0", "question_packs": []}
        (ldf_dir / "config.yaml").write_text(yaml.safe_dump(config))

        repair_project(tmp_path)

        captured = capsys.readouterr()
        assert "Updated config.yaml with missing fields" in captured.out

        # Verify fields were added
        with open(ldf_dir / "config.yaml") as f:
            updated_config = yaml.safe_load(f)
        assert "framework_version" in updated_config

    def test_repair_no_changes_needed(self, tmp_path: Path, capsys, monkeypatch):
        """Test that repair reports when no changes are needed."""
        monkeypatch.chdir(tmp_path)

        # First do a complete initialization
        initialize_project(
            project_path=tmp_path,
            preset="custom",
            question_packs=["security"],
            mcp_servers=["spec_inspector"],
            non_interactive=True,
        )

        # Clear the output
        capsys.readouterr()

        # Now run repair twice - first repair may update config, second should have no changes
        repair_project(tmp_path)
        capsys.readouterr()  # Clear first repair output

        # Second repair should have no changes
        repair_project(tmp_path)

        captured = capsys.readouterr()
        assert "No repairs needed" in captured.out

    def test_repair_handles_corrupt_config(self, tmp_path: Path, capsys):
        """Test that repair handles corrupt config.yaml gracefully."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()
        # Write invalid YAML
        (ldf_dir / "config.yaml").write_text("invalid: yaml: syntax: [broken")

        repair_project(tmp_path)

        # Should still complete (uses defaults when config can't be parsed)
        captured = capsys.readouterr()
        # Should have created/repaired files despite corrupt config
        assert (ldf_dir / "guardrails.yaml").exists() or "No repairs needed" in captured.out

    def test_repair_uses_config_values(self, tmp_path: Path, capsys):
        """Test that repair uses values from existing config."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()
        config = {
            "version": "1.0",
            "guardrails": {"preset": "fintech"},
            "question_packs": ["security", "testing"],
            "mcp_servers": ["spec_inspector"],
            "framework_version": "1.0.0",
            "_checksums": {},
        }
        (ldf_dir / "config.yaml").write_text(yaml.safe_dump(config))

        repair_project(tmp_path)

        # Check that AGENT.md was created with fintech preset (90% coverage)
        agent_md = (tmp_path / "AGENT.md").read_text()
        assert "fintech" in agent_md
        assert "90%" in agent_md

    def test_repair_computes_checksums_for_existing_packs(self, tmp_path: Path, capsys):
        """Test that repair computes checksums for existing question packs."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()
        qp_dir = ldf_dir / "question-packs"
        qp_dir.mkdir()
        # Create a question pack file
        (qp_dir / "security.yaml").write_text("name: security\n")
        # Config without checksums
        config = {"version": "1.0", "question_packs": ["security"]}
        (ldf_dir / "config.yaml").write_text(yaml.safe_dump(config))

        repair_project(tmp_path)

        # Verify checksums were added
        with open(ldf_dir / "config.yaml") as f:
            updated_config = yaml.safe_load(f)
        assert "_checksums" in updated_config
        assert "question-packs/security.yaml" in updated_config["_checksums"]

    def test_repair_from_empty_ldf_dir(self, tmp_path: Path, capsys):
        """Test repair when .ldf directory is completely empty."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()

        repair_project(tmp_path)

        captured = capsys.readouterr()
        assert "Repair complete" in captured.out
        # Should have created all necessary structure
        assert (ldf_dir / "config.yaml").exists()
        assert (ldf_dir / "guardrails.yaml").exists()
        assert (ldf_dir / "specs").exists()
        assert (tmp_path / "AGENT.md").exists()

    def test_repair_with_partial_agent_commands(self, tmp_path: Path, capsys):
        """Test repair when .agent/commands exists but is empty."""
        ldf_dir = tmp_path / ".ldf"
        ldf_dir.mkdir()
        (ldf_dir / "config.yaml").write_text("version: '1.0'\n")

        # Create empty .agent/commands
        commands_dir = tmp_path / ".agent" / "commands"
        commands_dir.mkdir(parents=True)

        repair_project(tmp_path)

        captured = capsys.readouterr()
        assert "Created .agent/commands/" in captured.out
        assert (commands_dir / "create-spec.md").exists()
