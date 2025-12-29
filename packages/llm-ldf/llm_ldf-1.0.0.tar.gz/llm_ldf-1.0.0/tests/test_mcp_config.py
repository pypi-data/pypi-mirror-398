"""Tests for ldf.mcp_config module."""

import json
from pathlib import Path

from ldf.mcp_config import generate_mcp_config, get_mcp_servers_dir


class TestGetMcpServersDir:
    """Tests for get_mcp_servers_dir function."""

    def test_returns_path(self):
        """Test that it returns a Path object."""
        path = get_mcp_servers_dir()
        assert isinstance(path, Path)

    def test_path_is_mcp_servers_dir(self):
        """Test that the path is the _mcp_servers directory."""
        path = get_mcp_servers_dir()
        assert path.name == "_mcp_servers"
        assert path.exists()

    def test_path_contains_spec_inspector(self):
        """Test that spec_inspector server exists."""
        path = get_mcp_servers_dir()
        server = path / "spec_inspector" / "server.py"
        assert server.exists()


class TestGenerateMcpConfig:
    """Tests for generate_mcp_config function."""

    def test_returns_json_string(self, tmp_path):
        """Test that it returns a valid JSON string."""
        config = generate_mcp_config(tmp_path)
        parsed = json.loads(config)
        assert isinstance(parsed, dict)

    def test_claude_format_has_wrapper(self, tmp_path):
        """Test that claude format includes mcpServers wrapper."""
        config = generate_mcp_config(tmp_path, output_format="claude")
        parsed = json.loads(config)
        assert "mcpServers" in parsed

    def test_json_format_no_wrapper(self, tmp_path):
        """Test that json format has no mcpServers wrapper."""
        config = generate_mcp_config(tmp_path, output_format="json")
        parsed = json.loads(config)
        assert "mcpServers" not in parsed
        assert "spec_inspector" in parsed

    def test_includes_both_servers_by_default(self, tmp_path):
        """Test that both servers are included by default."""
        config = generate_mcp_config(tmp_path, output_format="json")
        parsed = json.loads(config)
        assert "spec_inspector" in parsed
        assert "coverage_reporter" in parsed

    def test_filter_to_single_server(self, tmp_path):
        """Test filtering to a single server."""
        config = generate_mcp_config(tmp_path, servers=["spec_inspector"], output_format="json")
        parsed = json.loads(config)
        assert "spec_inspector" in parsed
        assert "coverage_reporter" not in parsed

    def test_server_config_structure(self, tmp_path):
        """Test that server config has expected structure."""
        config = generate_mcp_config(tmp_path, output_format="json")
        parsed = json.loads(config)

        spec_inspector = parsed["spec_inspector"]
        assert "command" in spec_inspector
        assert "args" in spec_inspector
        assert "env" in spec_inspector
        assert spec_inspector["command"] == "python"

    def test_paths_are_absolute(self, tmp_path):
        """Test that all paths in config are absolute."""
        config = generate_mcp_config(tmp_path, output_format="json")
        parsed = json.loads(config)

        for server_config in parsed.values():
            # Check args (server script path)
            for arg in server_config["args"]:
                if arg.endswith(".py"):
                    assert Path(arg).is_absolute()

            # Check env vars that are paths
            for key, value in server_config["env"].items():
                if "ROOT" in key or "DIR" in key:
                    assert Path(value).is_absolute()

    def test_uses_cwd_when_no_project_root(self, tmp_path, monkeypatch):
        """Test that it uses cwd when project_root is None."""
        monkeypatch.chdir(tmp_path)
        config = generate_mcp_config(None, output_format="json")
        parsed = json.loads(config)

        # Should contain the tmp_path
        assert str(tmp_path) in parsed["spec_inspector"]["env"]["LDF_ROOT"]

    def test_spec_inspector_env_vars(self, tmp_path):
        """Test that spec_inspector has correct env vars."""
        config = generate_mcp_config(tmp_path, output_format="json")
        parsed = json.loads(config)

        env = parsed["spec_inspector"]["env"]
        assert "LDF_ROOT" in env
        assert "SPECS_DIR" in env
        assert str(tmp_path) in env["LDF_ROOT"]
        assert ".ldf/specs" in env["SPECS_DIR"]

    def test_coverage_reporter_env_vars(self, tmp_path):
        """Test that coverage_reporter has correct env vars."""
        config = generate_mcp_config(tmp_path, output_format="json")
        parsed = json.loads(config)

        env = parsed["coverage_reporter"]["env"]
        assert "PROJECT_ROOT" in env
        assert str(tmp_path) in env["PROJECT_ROOT"]


class TestMcpConfigCli:
    """Tests for the CLI command."""

    def test_command_exists(self):
        """Test that the mcp-config command exists."""
        from click.testing import CliRunner

        from ldf.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["mcp-config", "--help"])
        assert result.exit_code == 0
        assert "Generate MCP server configuration" in result.output

    def test_command_outputs_json(self, tmp_path):
        """Test that command outputs valid JSON."""
        from click.testing import CliRunner

        from ldf.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["mcp-config", "-r", str(tmp_path)])
        assert result.exit_code == 0

        parsed = json.loads(result.output)
        assert "mcpServers" in parsed

    def test_command_with_format_option(self, tmp_path):
        """Test command with --format option."""
        from click.testing import CliRunner

        from ldf.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["mcp-config", "-r", str(tmp_path), "--format", "json"])
        assert result.exit_code == 0

        parsed = json.loads(result.output)
        assert "mcpServers" not in parsed
        assert "spec_inspector" in parsed

    def test_command_with_server_filter(self, tmp_path):
        """Test command with --server option."""
        from click.testing import CliRunner

        from ldf.cli import main

        runner = CliRunner()
        result = runner.invoke(
            main, ["mcp-config", "-r", str(tmp_path), "-s", "spec_inspector", "--format", "json"]
        )
        assert result.exit_code == 0

        parsed = json.loads(result.output)
        assert "spec_inspector" in parsed
        assert "coverage_reporter" not in parsed
