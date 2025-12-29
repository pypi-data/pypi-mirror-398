#!/usr/bin/env python3
"""
Test Coverage Reporter MCP Server

Provides real-time test coverage metrics per service/guardrail.

Usage:
    python server.py

Environment Variables:
    PROJECT_ROOT: Project root directory (default: current directory)
    COVERAGE_FILE: Path to coverage data file (default: .coverage)

MCP Tools:
    - get_coverage_summary: Get overall coverage metrics
    - get_service_coverage: Get coverage for specific service
    - get_guardrail_test_coverage: Get test coverage for guardrail-specific tests
    - get_untested_functions: List functions without tests
    - validate_coverage: Check if coverage meets thresholds
"""

import asyncio
import fnmatch
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

import yaml
from mcp import types
from mcp.server import Server
from mcp.server.stdio import stdio_server

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from coverage_parser import CoverageParser
from guardrail_validator import GuardrailCoverageValidator

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("coverage_reporter")

# Initialize MCP Server
app = Server("coverage_reporter")

# Initialize with configurable paths
project_root = Path(os.getenv("PROJECT_ROOT", ".")).resolve()
coverage_file = project_root / os.getenv("COVERAGE_FILE", ".coverage")

parser = CoverageParser(project_root)
validator = GuardrailCoverageValidator(project_root)

logger.info(f"Initialized CoverageReporter with root: {project_root}")


# Coverage threshold configuration (can be overridden by .ldf/guardrails.yaml)
DEFAULT_THRESHOLDS = {"auth*": 90.0, "ledger*": 90.0, "billing*": 90.0, "payment*": 90.0, "*": 80.0}


def _load_thresholds(root: Path) -> dict[str, float]:
    """Load coverage thresholds from configuration.

    Priority order:
    1. .ldf/config.yaml coverage section (as documented)
    2. .ldf/guardrails.yaml coverage section or guardrail #1 overrides
    3. Default thresholds

    The config can specify thresholds like:
        coverage:
          default_threshold: 80
          critical_threshold: 90
          critical_services:
            - auth
            - billing
    """
    # Try config.yaml first (as documented in customization.md)
    config_file = root / ".ldf" / "config.yaml"
    if config_file.exists():
        try:
            with open(config_file) as f:
                data = yaml.safe_load(f) or {}

            coverage_config = data.get("coverage", {})
            if coverage_config:
                thresholds = dict(DEFAULT_THRESHOLDS)

                # Load default threshold
                if "default_threshold" in coverage_config:
                    thresholds["*"] = float(coverage_config["default_threshold"])

                # Load critical threshold and apply to critical services
                critical_threshold = coverage_config.get("critical_threshold", 90)
                critical_services = coverage_config.get("critical_services", [])

                if critical_services:
                    for service in critical_services:
                        thresholds[f"{service}*"] = float(critical_threshold)
                else:
                    # Apply to default critical paths
                    for pattern in ["auth*", "ledger*", "billing*", "payment*"]:
                        thresholds[pattern] = float(critical_threshold)

                return thresholds

        except Exception as e:
            logger.warning(f"Failed to load coverage thresholds from config.yaml: {e}")

    # Fallback to guardrails.yaml
    guardrails_file = root / ".ldf" / "guardrails.yaml"
    if guardrails_file.exists():
        try:
            with open(guardrails_file) as f:
                data = yaml.safe_load(f) or {}

            # Check for overrides on guardrail 1 (Testing Coverage)
            overrides = data.get("overrides", {})
            if "1" in overrides and "config" in overrides["1"]:
                gr_config = overrides["1"]["config"]
                thresholds = dict(DEFAULT_THRESHOLDS)

                if "default_threshold" in gr_config:
                    thresholds["*"] = float(gr_config["default_threshold"])
                if "critical_paths_threshold" in gr_config:
                    critical_threshold = float(gr_config["critical_paths_threshold"])
                    for pattern in ["auth*", "ledger*", "billing*", "payment*"]:
                        thresholds[pattern] = critical_threshold

                return thresholds

        except Exception as e:
            logger.warning(f"Failed to load coverage thresholds from guardrails.yaml: {e}")

    # Fallback to defaults
    return dict(DEFAULT_THRESHOLDS)


# Load thresholds on module init
_loaded_thresholds: dict[str, float] | None = None


def get_threshold_for_service(
    service_name: str, thresholds: dict[str, float] | None = None
) -> float:
    """Get coverage threshold for a service name (supports wildcards).

    Args:
        service_name: Name of the service
        thresholds: Optional thresholds dict (if None, uses loaded/default)

    Returns:
        Coverage threshold percentage
    """
    global _loaded_thresholds

    if thresholds is None:
        if _loaded_thresholds is None:
            _loaded_thresholds = _load_thresholds(project_root)
        thresholds = _loaded_thresholds

    service_lower = service_name.lower().replace("_service", "").replace("-service", "")

    for pattern, threshold in thresholds.items():
        if fnmatch.fnmatch(service_lower, pattern):
            return float(threshold)

    return float(thresholds.get("*", 80.0))


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    """List all available MCP tools."""
    return [
        types.Tool(
            name="get_coverage_summary",
            description="Get overall test coverage metrics",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="get_service_coverage",
            description="Get coverage for specific service",
            inputSchema={
                "type": "object",
                "properties": {
                    "service_name": {
                        "type": "string",
                        "description": "Name of service (e.g., 'auth_service')",
                    }
                },
                "required": ["service_name"],
            },
        ),
        types.Tool(
            name="get_guardrail_test_coverage",
            description="Get test coverage for guardrail-specific tests",
            inputSchema={
                "type": "object",
                "properties": {
                    "guardrail_id": {
                        "type": "integer",
                        "description": "Guardrail ID (e.g., 1 for Testing Coverage)",
                    }
                },
                "required": ["guardrail_id"],
            },
        ),
        types.Tool(
            name="get_untested_functions",
            description="List functions without test coverage",
            inputSchema={
                "type": "object",
                "properties": {
                    "service_path": {
                        "type": "string",
                        "description": "Path to service directory (e.g., 'src/services/auth')",
                    }
                },
                "required": ["service_path"],
            },
        ),
        types.Tool(
            name="validate_coverage",
            description="Validate coverage meets thresholds (default: 80%, critical: 90%)",
            inputSchema={
                "type": "object",
                "properties": {
                    "service_name": {"type": "string", "description": "Name of service to validate"}
                },
                "required": ["service_name"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Execute a tool call."""
    logger.info(f"Calling tool: {name} with arguments: {arguments}")

    try:
        if name == "get_coverage_summary":
            result = await get_coverage_summary()
        elif name == "get_service_coverage":
            result = await get_service_coverage(arguments["service_name"])
        elif name == "get_guardrail_test_coverage":
            result = await get_guardrail_test_coverage(arguments["guardrail_id"])
        elif name == "get_untested_functions":
            result = await get_untested_functions(arguments["service_path"])
        elif name == "validate_coverage":
            result = await validate_coverage(arguments["service_name"])
        else:
            raise ValueError(f"Unknown tool: {name}")

        return [types.TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
    except Exception as e:
        logger.error(f"Error executing {name}: {e}", exc_info=True)
        return [types.TextContent(type="text", text=json.dumps({"error": str(e)}, indent=2))]


# Tool implementation functions


async def get_coverage_summary() -> dict[str, Any]:
    """Get overall coverage summary."""
    if not coverage_file.exists():
        return {
            "status": "no_coverage",
            "message": "No coverage file found. Run tests with coverage enabled.",
        }

    try:
        coverage_data = parser.parse_coverage()
    except Exception as e:
        return {"status": "error", "message": str(e)}

    threshold = DEFAULT_THRESHOLDS.get("*", 80.0)
    percent = coverage_data["summary"]["percent_covered"]

    return {
        "status": "success",
        "overall_coverage": percent,
        "lines_covered": coverage_data["summary"]["covered_lines"],
        "lines_total": coverage_data["summary"]["num_statements"],
        "files_covered": len(coverage_data["files"]),
        "threshold": threshold,
        "meets_threshold": percent >= threshold,
        "message": "PASS"
        if percent >= threshold
        else f"FAIL: Coverage {percent:.1f}% < {threshold}%",
    }


async def get_service_coverage(service_name: str) -> dict[str, Any]:
    """Get coverage for specific service."""
    try:
        coverage_data = parser.parse_coverage()
    except Exception as e:
        return {"service_name": service_name, "status": "error", "message": str(e)}

    # Normalize service name for matching
    service_normalized = service_name.lower().replace("_service", "").replace("-service", "")

    # Find service files (flexible matching)
    service_files = []
    for file_path, file_data in coverage_data["files"].items():
        file_lower = file_path.lower()
        if (
            f"/{service_normalized}/" in file_lower
            or f"/{service_normalized}_" in file_lower
            or f"/{service_normalized}." in file_lower
            or file_lower.endswith(f"/{service_normalized}.py")
        ):
            service_files.append(file_data)

    if not service_files:
        return {
            "service_name": service_name,
            "status": "not_found",
            "message": f"No coverage data for service '{service_name}'",
        }

    # Calculate service coverage
    total_lines = sum(f["summary"]["num_statements"] for f in service_files)
    covered_lines = sum(f["summary"]["covered_lines"] for f in service_files)
    coverage_pct = (covered_lines / total_lines * 100) if total_lines > 0 else 0.0

    threshold = get_threshold_for_service(service_name)
    meets_threshold = coverage_pct >= threshold

    return {
        "service_name": service_name,
        "status": "PASS" if meets_threshold else "FAIL",
        "coverage": round(coverage_pct, 2),
        "lines_covered": covered_lines,
        "lines_total": total_lines,
        "threshold": threshold,
        "meets_threshold": meets_threshold,
        "files": [
            {"path": f["path"], "coverage": round(f["summary"]["percent_covered"], 2)}
            for f in service_files
        ],
    }


async def get_guardrail_test_coverage(guardrail_id: int) -> dict[str, Any]:
    """Get test coverage for guardrail-specific tests."""
    guardrail_patterns = validator.get_test_patterns_for_guardrail(guardrail_id)

    if not guardrail_patterns:
        return {
            "guardrail_id": guardrail_id,
            "guardrail_name": validator.get_guardrail_name(guardrail_id),
            "status": "no_patterns",
            "message": "No test patterns defined for this guardrail",
        }

    try:
        coverage_data = parser.parse_coverage()
    except Exception as e:
        return {"guardrail_id": guardrail_id, "status": "error", "message": str(e)}

    # Find test files matching guardrail patterns
    matching_tests = []
    for file_path, file_data in coverage_data["files"].items():
        if "test" in file_path.lower():
            for pattern in guardrail_patterns:
                if pattern.lower() in file_path.lower():
                    matching_tests.append(
                        {
                            "path": file_data["path"],
                            "coverage": round(file_data["summary"]["percent_covered"], 2),
                            "lines_covered": file_data["summary"]["covered_lines"],
                            "lines_total": file_data["summary"]["num_statements"],
                        }
                    )
                    break

    return {
        "guardrail_id": guardrail_id,
        "guardrail_name": validator.get_guardrail_name(guardrail_id),
        "test_count": len(matching_tests),
        "tests": matching_tests,
        "status": "covered" if matching_tests else "not_covered",
    }


async def get_untested_functions(service_path: str) -> dict[str, Any]:
    """List functions without test coverage."""
    try:
        coverage_data = parser.parse_coverage()
    except Exception as e:
        return {"service_path": service_path, "status": "error", "message": str(e)}

    # Find service file
    service_data = None
    for file_path, file_data in coverage_data["files"].items():
        if service_path in file_path:
            service_data = file_data
            break

    if not service_data:
        return {
            "service_path": service_path,
            "status": "not_found",
            "message": "No coverage data found",
        }

    untested_lines = service_data.get("missing_lines", [])

    return {
        "service_path": service_path,
        "untested_line_count": len(untested_lines),
        "untested_lines": untested_lines[:50],  # First 50 lines
        "coverage": round(service_data["summary"]["percent_covered"], 2),
        "message": "Review these lines and add tests",
    }


async def validate_coverage(service_name: str) -> dict[str, Any]:
    """Validate coverage meets thresholds."""
    service_coverage = await get_service_coverage(service_name)

    if service_coverage["status"] == "not_found":
        return {
            "service_name": service_name,
            "valid": False,
            "errors": ["No coverage data found"],
            "message": "Run tests with coverage enabled",
        }

    if service_coverage["status"] == "error":
        return {
            "service_name": service_name,
            "valid": False,
            "errors": [service_coverage.get("message", "Unknown error")],
            "message": "Error reading coverage data",
        }

    errors = []
    warnings = []

    # Check threshold
    if not service_coverage["meets_threshold"]:
        errors.append(
            f"Coverage {service_coverage['coverage']}% < {service_coverage['threshold']}%"
        )

    # Check for completely untested files
    for file_data in service_coverage.get("files", []):
        if file_data["coverage"] == 0.0:
            warnings.append(f"File {file_data['path']} has 0% coverage")

    return {
        "service_name": service_name,
        "valid": len(errors) == 0,
        "coverage": service_coverage["coverage"],
        "threshold": service_coverage["threshold"],
        "errors": errors,
        "warnings": warnings,
        "message": "Coverage meets requirements" if not errors else "Coverage below threshold",
    }


async def main():
    """Run the MCP server using stdio transport."""
    logger.info("Coverage Reporter MCP Server starting (stdio mode)")
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
