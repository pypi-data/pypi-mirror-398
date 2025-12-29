"""MCP configuration generator for LDF projects."""

import json
from pathlib import Path
from typing import Any


def get_mcp_servers_dir() -> Path:
    """Get the MCP servers directory path.

    Returns:
        Path to the _mcp_servers directory inside the ldf package.
    """
    return Path(__file__).parent / "_mcp_servers"


def generate_mcp_config(
    project_root: Path | None = None,
    servers: list[str] | None = None,
    output_format: str = "claude",
) -> str:
    """Generate MCP server configuration JSON.

    Args:
        project_root: Project directory (defaults to cwd)
        servers: List of server names to include (defaults to all available)
        output_format: Output format - "claude" wraps in mcpServers, "json" is raw

    Returns:
        JSON string with MCP configuration
    """
    if project_root is None:
        project_root = Path.cwd()
    project_root = project_root.resolve()

    mcp_servers_dir = get_mcp_servers_dir()

    # Available servers
    available_servers = {
        "spec_inspector": {
            "command": "python",
            "args": [str(mcp_servers_dir / "spec_inspector" / "server.py")],
            "env": {
                "LDF_ROOT": str(project_root),
                "SPECS_DIR": str(project_root / ".ldf" / "specs"),
            },
        },
        "coverage_reporter": {
            "command": "python",
            "args": [str(mcp_servers_dir / "coverage_reporter" / "server.py")],
            "env": {
                "PROJECT_ROOT": str(project_root),
            },
        },
    }

    # Filter to requested servers
    if servers:
        config = {name: available_servers[name] for name in servers if name in available_servers}
    else:
        config = available_servers

    # Format output
    output: dict[str, Any]
    if output_format == "claude":
        output = {"mcpServers": config}
    else:
        output = config

    return json.dumps(output, indent=2)


def print_mcp_config(
    project_root: Path | None = None,
    servers: list[str] | None = None,
    output_format: str = "claude",
) -> None:
    """Print MCP configuration to stdout.

    Args:
        project_root: Project directory (defaults to cwd)
        servers: List of server names to include
        output_format: Output format - "claude" or "json"
    """
    config = generate_mcp_config(project_root, servers, output_format)
    print(config)
