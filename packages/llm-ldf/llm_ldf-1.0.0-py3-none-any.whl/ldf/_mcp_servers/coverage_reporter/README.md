# Coverage Reporter MCP Server

Real-time test coverage metrics per service/guardrail without requiring your AI assistant to parse coverage reports.

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
    "coverage_reporter": {
      "command": "python",
      "args": ["-m", "ldf._mcp_servers.coverage_reporter.server"],
      "env": {
        "PROJECT_ROOT": "/path/to/your/project"
      }
    }
  }
}
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PROJECT_ROOT` | Project root directory | Current directory |
| `COVERAGE_FILE` | Path to coverage file | `.coverage` |

## Supported Coverage Formats

| Format | Command | Files |
|--------|---------|-------|
| Python (pytest-cov) | `pytest --cov=. --cov-report=json` | `.coverage`, `coverage.json` |
| Node.js (Jest) | `jest --coverage` | `coverage/coverage-final.json` |
| Node.js (c8) | `c8 npm test` | `coverage/coverage-summary.json` |

## Available Tools

### `get_coverage_summary`

Get overall coverage metrics.

```json
{}
```

Returns:
- Overall coverage percentage
- Lines covered/total
- Files covered count
- Pass/Fail status against threshold

### `get_service_coverage`

Get coverage for specific service.

```json
{
  "service_name": "auth"
}
```

Returns:
- Service coverage percentage
- Per-file coverage breakdown
- Threshold for this service
- Pass/Fail status

### `get_guardrail_test_coverage`

Get test coverage for guardrail-specific tests.

```json
{
  "guardrail_id": 2
}
```

Returns:
- Guardrail name
- Matching test files
- Coverage percentage
- Test count

### `get_untested_functions`

List functions without test coverage.

```json
{
  "service_path": "src/services/auth"
}
```

Returns:
- Untested line numbers
- Coverage percentage
- Guidance for adding tests

### `validate_coverage`

Check if coverage meets thresholds.

```json
{
  "service_name": "auth"
}
```

Returns:
- Valid/Invalid status
- Errors and warnings
- Threshold comparison

## Coverage Thresholds

Default thresholds (can be overridden in `.ldf/guardrails.yaml`):

| Service Pattern | Threshold |
|-----------------|-----------|
| `auth*` | 90% |
| `ledger*` | 90% |
| `billing*` | 90% |
| `payment*` | 90% |
| `*` (default) | 80% |

## Token Efficiency

| Operation | Without MCP | With MCP |
|-----------|-------------|----------|
| Get coverage summary | ~10,000 tokens | ~200 tokens |
| Check service coverage | ~5,000 tokens | ~150 tokens |
| Find untested code | ~8,000 tokens | ~300 tokens |

## Development

```bash
# Generate coverage first
pytest --cov=. --cov-report=json

# Test the server locally
python server.py

# Run with debug logging
LOG_LEVEL=DEBUG python server.py
```

## Related

- [Spec Inspector](../spec_inspector/) - Spec status and validation
- [MCP Setup Guide](../MCP_SETUP.md) - Complete configuration guide
