# MCP Server Setup Guide

Complete guide for configuring LDF's MCP (Model Context Protocol) servers with your AI coding assistant.

## Overview

LDF provides two MCP servers that give your AI assistant real-time access to your project's spec status and test coverage, saving ~90% of tokens compared to reading files directly.

**Supported Tools:** Claude Code, Gemini CLI, Codex CLI, and other MCP-compatible assistants.

| Server | Purpose | Token Savings |
|--------|---------|---------------|
| **spec_inspector** | Spec status, guardrail coverage, task tracking | ~90% |
| **coverage_reporter** | Test coverage metrics, untested code | ~85% |

## Prerequisites

1. **An MCP-compatible AI tool** (Claude Code, Gemini CLI, or Codex CLI)
2. **Python 3.10+** for running MCP servers
3. **MCP SDK** installed: `pip install mcp`

## Quick Setup

### 1. Install Dependencies

```bash
# MCP servers are bundled with ldf - just install ldf
pip install llm-ldf

# Or install with MCP extras for the mcp library
pip install llm-ldf[mcp]
```

### 2. Configure Your AI Tool

Create the MCP config file for your tool:

| Tool | Config Location |
|------|-----------------|
| Claude Code | `.agent/mcp.json` |
| Gemini CLI | `.gemini/settings.json` |
| Codex CLI | See Codex docs |

**Example (Claude Code format):**

```json
{
  "mcpServers": {
    "spec_inspector": {
      "command": "python",
      "args": ["/path/to/ldf/_mcp_servers/spec_inspector/server.py"],
      "env": {
        "LDF_ROOT": "/path/to/project",
        "SPECS_DIR": "/path/to/project/.ldf/specs"
      }
    },
    "coverage_reporter": {
      "command": "python",
      "args": ["/path/to/ldf/_mcp_servers/coverage_reporter/server.py"],
      "env": {
        "PROJECT_ROOT": "/path/to/project"
      }
    }
  }
}
```

**Note:** Use `ldf mcp-config` to generate the correct absolute paths for your system.

### 3. Verify Setup

Restart your AI tool and check that the MCP servers are loaded. You should see the new tools available.

## Server Configuration

### Spec Inspector

Environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `LDF_ROOT` | Project root directory | Current directory |
| `SPECS_DIR` | Path to specs (relative to LDF_ROOT) | `.ldf/specs` |

Available tools:

| Tool | Description |
|------|-------------|
| `get_spec_status` | Get spec status, phases, guardrail coverage |
| `get_guardrail_coverage` | Get guardrail coverage matrix |
| `get_tasks` | List tasks with optional status filter |
| `validate_answerpacks` | Check answerpack completeness |
| `lint_spec` | Run spec linter validation |
| `list_specs` | List all available specs |

### Coverage Reporter

Environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `PROJECT_ROOT` | Project root directory | Current directory |
| `COVERAGE_FILE` | Coverage data file path | `.coverage` |

Available tools:

| Tool | Description |
|------|-------------|
| `get_coverage_summary` | Get overall coverage metrics |
| `get_service_coverage` | Get coverage for specific service |
| `get_guardrail_coverage` | Get coverage for guardrail tests |
| `get_untested_functions` | List uncovered lines |
| `validate_coverage` | Check if coverage meets thresholds |

## Quick Configuration with CLI

The easiest way to configure MCP servers is using the LDF CLI:

```bash
# Generate MCP configuration for current project
mkdir -p .agent && ldf mcp-config > .agent/mcp.json

# Generate for a different project directory
ldf mcp-config -r /path/to/my-project > .agent/mcp.json

# Only include specific servers
ldf mcp-config -s spec_inspector > .agent/mcp.json
```

## Advanced Configuration

### Custom Project Root

For projects in different locations:

```bash
# Generate config pointing to a specific project
ldf mcp-config -r /path/to/my-project > .agent/mcp.json
```

### Using Virtual Environments

If using a venv, you may want to modify the generated config to use your project's Python:

```json
{
  "mcpServers": {
    "spec_inspector": {
      "command": "/path/to/my-project/.venv/bin/python",
      "args": ["..."],
      "env": {
        "LDF_ROOT": "/path/to/my-project"
      }
    }
  }
}
```

### Multiple Projects

Configure servers per-project in each project's MCP config file.

## How AI Tools Use MCP

When working on your project, your AI assistant can now:

1. **Check spec status** without reading markdown files:
   ```
   Tool: get_spec_status
   Input: {"spec_name": "user-auth"}
   ```

2. **Get task progress** instantly:
   ```
   Tool: get_tasks
   Input: {"spec_name": "user-auth", "status": "pending"}
   ```

3. **Verify coverage** before committing:
   ```
   Tool: validate_coverage
   Input: {"service_name": "auth"}
   ```

## Generating Coverage Data

Before using coverage_reporter, generate coverage data:

### Python (pytest)

```bash
pytest --cov=. --cov-report=json
```

This creates `.coverage` and optionally `coverage.json`.

### Node.js (Jest)

```bash
jest --coverage --coverageReporters=json
```

This creates `coverage/coverage-final.json`.

### Go

```bash
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out -o coverage.html
```

## Troubleshooting

### Server Not Starting

1. Check Python version: `python --version` (need 3.10+)
2. Check MCP SDK: `pip show mcp`
3. Check logs: Run server directly to see errors:
   ```bash
   python -m ldf._mcp_servers.spec_inspector.server
   ```

### No Specs Found

1. Verify `.ldf/specs/` directory exists
2. Check `SPECS_DIR` environment variable
3. Ensure specs have proper directory structure

### No Coverage Data

1. Run tests with coverage enabled
2. Check coverage file exists: `ls -la .coverage*`
3. Verify `PROJECT_ROOT` is set correctly

### Tools Not Appearing

1. Restart your AI tool
2. Check your MCP config file is valid JSON
3. Verify file paths are correct

## Optional: Database Inspector

For projects with PostgreSQL, you can add the db_inspector server:

1. Copy the template from `ldf/_mcp_servers/db_inspector/template/` to your project
2. Configure database connection in the server
3. Add to `.agent/mcp.json`:
   ```json
   "db_inspector": {
     "command": "python",
     "args": ["-m", "ldf._mcp_servers.db_inspector.template.server"],
     "env": {
       "DATABASE_URL": "postgresql://user:pass@localhost/db"
     }
   }
   ```

See [db_inspector/README.md](./db_inspector/README.md) for details.

## Token Efficiency

MCP servers dramatically reduce token usage:

| Operation | Without MCP | With MCP | Savings |
|-----------|-------------|----------|---------|
| Get spec status | ~5,000 | ~200 | 96% |
| List tasks | ~3,000 | ~150 | 95% |
| Check coverage | ~10,000 | ~200 | 98% |
| Validate guardrails | ~2,000 | ~100 | 95% |

This means:
- Faster responses
- Lower API costs
- More context available for actual work

## Related Documentation

- [Spec Inspector README](./spec_inspector/README.md)
- [Coverage Reporter README](./coverage_reporter/README.md)
- [LDF Getting Started](../docs/getting-started.md)
