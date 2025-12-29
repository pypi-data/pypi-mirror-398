# Spec Inspector MCP Server

Real-time queries for spec status, guardrail coverage, and task dependencies without requiring your AI assistant to read large markdown files.

## Installation

```bash
# MCP servers are bundled with ldf - just install ldf
pip install llm-ldf

# Or install with MCP extras
pip install llm-ldf[mcp]
```

## Configuration

The easiest way to configure is using the LDF CLI:

```bash
# Generate MCP configuration for your project
mkdir -p .agent && ldf mcp-config > .agent/mcp.json
```

Or manually add to your MCP settings (e.g., `.agent/mcp.json` for Claude Code):

```json
{
  "mcpServers": {
    "spec_inspector": {
      "command": "python",
      "args": ["-m", "ldf._mcp_servers.spec_inspector.server"],
      "env": {
        "LDF_ROOT": "/path/to/your/project",
        "SPECS_DIR": ".ldf/specs"
      }
    }
  }
}
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LDF_ROOT` | Project root directory | Current directory |
| `SPECS_DIR` | Path to specs directory (relative to LDF_ROOT) | `.ldf/specs` |
| `LDF_MAX_CONCURRENT_LINTS` | Max concurrent lint operations | `3` |
| `LDF_LINT_TIMEOUT` | Lint operation timeout in seconds | `10.0` |
| `LDF_LINT_CACHE_TTL` | Lint cache TTL in seconds | `60.0` |

## Available Tools

### `get_spec_status`

Get overall spec status and metadata.

```json
{
  "spec_name": "user-auth"
}
```

Returns:
- Phase completion status (requirements, design, tasks)
- Guardrail coverage summary
- Task summary (total, pending, in_progress, completed)
- Available answerpacks

### `get_guardrail_coverage`

Get guardrail coverage matrix for a spec.

```json
{
  "spec_name": "user-auth"
}
```

Returns:
- Full guardrail matrix from requirements.md
- Missing guardrails (based on active guardrails from `.ldf/guardrails.yaml`)
- Compliance status

### `get_tasks`

List tasks with optional status filter.

```json
{
  "spec_name": "user-auth",
  "status": "pending"  // optional: pending, in_progress, completed, all
}
```

Returns:
- Task list with ID, title, status
- Checklist progress (completed/total)
- Estimated hours and dependencies

### `validate_answerpacks`

Check if answerpacks are populated (not templates).

```json
{
  "spec_name": "user-auth"
}
```

Returns:
- Validation status
- List of issues (template markers found)

### `lint_spec`

Run spec linter validation.

```json
{
  "spec_name": "user-auth"
}
```

Returns:
- Pass/Fail status
- Errors and warnings
- Linter output

### `list_specs`

List all available specs.

```json
{}
```

Returns:
- Count of specs
- Sorted list of spec names

## Token Efficiency

This server saves ~90% tokens compared to reading full spec files:

| Operation | Without MCP | With MCP |
|-----------|-------------|----------|
| Get spec status | ~5,000 tokens | ~200 tokens |
| Check task progress | ~3,000 tokens | ~150 tokens |
| Validate guardrails | ~2,000 tokens | ~100 tokens |

## Development

```bash
# Test the server locally
python server.py

# Run with debug logging
LOG_LEVEL=DEBUG python server.py
```

## Related

- [Coverage Reporter](../coverage_reporter/) - Test coverage metrics
- [MCP Setup Guide](../MCP_SETUP.md) - Complete configuration guide
