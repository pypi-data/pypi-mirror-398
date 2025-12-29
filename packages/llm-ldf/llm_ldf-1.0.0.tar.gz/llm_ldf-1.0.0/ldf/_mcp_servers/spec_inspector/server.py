#!/usr/bin/env python3
"""
Spec Inspector MCP Server

Provides real-time queries for spec status, guardrail coverage, and task dependencies
without requiring Claude to read large markdown files.

Usage:
    python server.py

Environment Variables:
    SPECS_DIR: Path to specs directory (default: .ldf/specs)
    LDF_ROOT: Project root directory (default: current directory)
    LDF_MAX_CONCURRENT_LINTS: Max concurrent lint operations (default: 3)
    LDF_LINT_TIMEOUT: Lint operation timeout in seconds (default: 10.0)
    LDF_LINT_CACHE_TTL: Lint cache TTL in seconds (default: 60.0)

MCP Tools:
    - get_spec_status: Get overall spec status and metadata
    - get_guardrail_coverage: Get guardrail coverage matrix for a spec
    - get_tasks: List tasks by status (pending/in_progress/completed)
    - validate_answerpacks: Check answerpack completeness
    - lint_spec: Run spec linter validation (cached, auto-invalidates on file change)
    - list_specs: List all available specs
"""

import asyncio
import json
import logging
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mcp import types
from mcp.server import Server
from mcp.server.stdio import stdio_server

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from guardrail_tracker import GuardrailTracker
from spec_parser import SpecParser

from ldf.utils.security import is_safe_directory_entry

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("spec_inspector")

# Concurrency and timeout configuration
MAX_CONCURRENT_LINTS = int(os.getenv("LDF_MAX_CONCURRENT_LINTS", "3"))
LINT_TIMEOUT = float(os.getenv("LDF_LINT_TIMEOUT", "10.0"))
LINT_CACHE_TTL = float(os.getenv("LDF_LINT_CACHE_TTL", "60.0"))  # Cache results for 60s
MAX_LINT_CACHE_SIZE = int(os.getenv("LDF_MAX_LINT_CACHE_SIZE", "100"))  # Bound cache size

# Semaphore for limiting concurrent lint operations
_lint_semaphore: asyncio.Semaphore | None = None


def _get_lint_semaphore() -> asyncio.Semaphore:
    """Get or create the lint semaphore for concurrency control."""
    global _lint_semaphore
    if _lint_semaphore is None:
        _lint_semaphore = asyncio.Semaphore(MAX_CONCURRENT_LINTS)
    return _lint_semaphore


@dataclass
class LintCacheEntry:
    """Cache entry for lint results."""

    result: dict[str, Any]
    timestamp: float
    spec_mtime: float  # Latest modification time of spec files


# Lint result cache: spec_name -> LintCacheEntry
_lint_cache: dict[str, LintCacheEntry] = {}


def _get_spec_mtime(spec_path: Path) -> float:
    """Get the latest modification time of spec files."""
    if not spec_path.exists():
        return 0.0
    mtimes = []
    for filename in ["requirements.md", "design.md", "tasks.md"]:
        filepath = spec_path / filename
        if filepath.exists():
            mtimes.append(filepath.stat().st_mtime)
    return max(mtimes) if mtimes else 0.0


def _get_cached_lint(spec_name: str, spec_path: Path) -> dict[str, Any] | None:
    """Get cached lint result if valid."""
    if spec_name not in _lint_cache:
        return None

    entry = _lint_cache[spec_name]
    now = time.time()

    # Check TTL
    if now - entry.timestamp > LINT_CACHE_TTL:
        del _lint_cache[spec_name]
        return None

    # Check if spec files changed
    current_mtime = _get_spec_mtime(spec_path)
    if current_mtime > entry.spec_mtime:
        del _lint_cache[spec_name]
        return None

    logger.debug(f"Cache hit for lint_spec({spec_name})")
    return entry.result


def _cache_lint_result(spec_name: str, spec_path: Path, result: dict[str, Any]) -> None:
    """Cache a lint result with bounded cache size."""
    # Evict oldest entries if cache is full
    while len(_lint_cache) >= MAX_LINT_CACHE_SIZE:
        oldest_key = min(_lint_cache.keys(), key=lambda k: _lint_cache[k].timestamp)
        del _lint_cache[oldest_key]
        logger.debug(f"Evicted cache entry for {oldest_key}")

    _lint_cache[spec_name] = LintCacheEntry(
        result=result,
        timestamp=time.time(),
        spec_mtime=_get_spec_mtime(spec_path),
    )


def _validate_spec_name(spec_name: str) -> Path:
    """Validate spec_name doesn't escape specs_dir (path traversal prevention).

    Args:
        spec_name: The spec name from user input

    Returns:
        Validated absolute path to the spec directory

    Raises:
        ValueError: If spec_name contains path traversal or escapes specs_dir
    """
    # Reject obvious traversal attempts
    if ".." in spec_name or spec_name.startswith("/") or spec_name.startswith("\\"):
        raise ValueError(f"Invalid spec name (path traversal detected): {spec_name}")

    # Reject hidden directories
    if spec_name.startswith("."):
        raise ValueError(f"Invalid spec name (hidden directory): {spec_name}")

    # Reject path separators (prevents nested path injection like "foo/.hidden")
    if "/" in spec_name or "\\" in spec_name:
        raise ValueError(f"Spec name cannot contain path separators: {spec_name}")

    spec_path = (specs_dir / spec_name).resolve()

    # Ensure resolved path is under specs_dir
    try:
        spec_path.relative_to(specs_dir.resolve())
    except ValueError:
        raise ValueError(f"Spec path escapes specs directory: {spec_name}")

    return spec_path


# Initialize MCP Server
app = Server("spec_inspector")

# Initialize with configurable paths
ldf_root = Path(os.getenv("LDF_ROOT", ".")).resolve()
specs_dir = Path(os.getenv("SPECS_DIR", ldf_root / ".ldf" / "specs"))

# Make specs_dir absolute if relative
if not specs_dir.is_absolute():
    specs_dir = ldf_root / specs_dir

parser = SpecParser(specs_dir, ldf_root)
tracker = GuardrailTracker(specs_dir, ldf_root)

logger.info(f"Initialized SpecInspector with root: {ldf_root}, specs: {specs_dir}")


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    """List all available MCP tools."""
    return [
        types.Tool(
            name="get_spec_status",
            description="Get status of a spec (approved, in-progress, etc.) with metadata",
            inputSchema={
                "type": "object",
                "properties": {
                    "spec_name": {
                        "type": "string",
                        "description": "Name of the spec (e.g., 'user-auth')",
                    }
                },
                "required": ["spec_name"],
            },
        ),
        types.Tool(
            name="get_guardrail_coverage",
            description="Get guardrail coverage matrix for a spec",
            inputSchema={
                "type": "object",
                "properties": {"spec_name": {"type": "string", "description": "Name of the spec"}},
                "required": ["spec_name"],
            },
        ),
        types.Tool(
            name="get_tasks",
            description="List tasks with optional status filter",
            inputSchema={
                "type": "object",
                "properties": {
                    "spec_name": {"type": "string", "description": "Name of the spec"},
                    "status": {
                        "type": "string",
                        "enum": ["pending", "in_progress", "completed", "all"],
                        "description": "Filter tasks by status (default: all)",
                    },
                },
                "required": ["spec_name"],
            },
        ),
        types.Tool(
            name="validate_answerpacks",
            description="Check if all relevant answerpacks are populated (not templates)",
            inputSchema={
                "type": "object",
                "properties": {"spec_name": {"type": "string", "description": "Name of the spec"}},
                "required": ["spec_name"],
            },
        ),
        types.Tool(
            name="lint_spec",
            description="Run spec linter validation (ldf lint)",
            inputSchema={
                "type": "object",
                "properties": {"spec_name": {"type": "string", "description": "Name of the spec"}},
                "required": ["spec_name"],
            },
        ),
        types.Tool(
            name="list_specs",
            description="List all available specs in .ldf/specs/",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Execute a tool call."""
    logger.info(f"Calling tool: {name} with arguments: {arguments}")

    try:
        if name == "get_spec_status":
            result = await get_spec_status(arguments["spec_name"])
        elif name == "get_guardrail_coverage":
            result = await get_guardrail_coverage(arguments["spec_name"])
        elif name == "get_tasks":
            result = await get_tasks(arguments["spec_name"], arguments.get("status", "all"))
        elif name == "validate_answerpacks":
            result = await validate_answerpacks(arguments["spec_name"])
        elif name == "lint_spec":
            result = await lint_spec(arguments["spec_name"])
        elif name == "list_specs":
            result = await list_specs()
        else:
            raise ValueError(f"Unknown tool: {name}")

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
    except Exception as e:
        logger.error(f"Error executing {name}: {e}", exc_info=True)
        return [types.TextContent(type="text", text=json.dumps({"error": str(e)}, indent=2))]


# Tool implementation functions


async def get_spec_status(spec_name: str) -> dict[str, Any]:
    """Get overall spec status and metadata."""
    spec_path = _validate_spec_name(spec_name)

    if not spec_path.exists():
        raise ValueError(f"Spec not found: {spec_name}")

    # Parse spec files
    spec_data = parser.parse_spec(spec_name)

    # Get guardrail coverage
    coverage = tracker.get_coverage_summary(spec_name)

    # Get task summary
    tasks = parser.parse_tasks(spec_name)
    task_summary = {
        "total": len(tasks),
        "pending": len([t for t in tasks if t["status"] == "pending"]),
        "in_progress": len([t for t in tasks if t["status"] == "in_progress"]),
        "completed": len([t for t in tasks if t["status"] == "completed"]),
        "estimated_hours": sum(t.get("estimated_hours", 0) for t in tasks),
    }

    return {
        "spec_name": spec_name,
        "status": spec_data.get("status", "unknown"),
        "phases": {
            "requirements": "complete" if (spec_path / "requirements.md").exists() else "missing",
            "design": "complete" if (spec_path / "design.md").exists() else "missing",
            "tasks": "complete" if (spec_path / "tasks.md").exists() else "missing",
        },
        "guardrail_coverage": coverage,
        "tasks": task_summary,
        "answerpacks": parser.list_answerpacks(spec_name),
    }


async def get_guardrail_coverage(spec_name: str) -> dict[str, Any]:
    """Get guardrail coverage matrix."""
    _validate_spec_name(spec_name)  # Validate before passing to tracker
    return tracker.get_coverage_matrix(spec_name)


async def get_tasks(spec_name: str, status: str = "all") -> dict[str, Any]:
    """List tasks with optional status filter."""
    _validate_spec_name(spec_name)  # Validate before passing to parser
    tasks = parser.parse_tasks(spec_name)

    if status != "all":
        tasks = [t for t in tasks if t["status"] == status]

    return {"spec_name": spec_name, "filter": status, "count": len(tasks), "tasks": tasks}


async def validate_answerpacks(spec_name: str) -> dict[str, Any]:
    """Check if answerpacks are populated (not templates)."""
    spec_path = _validate_spec_name(spec_name)

    # Check in spec directory
    spec_answerpack_path = spec_path / "answerpacks"

    # Also check in central answerpacks directory
    central_answerpack_path = ldf_root / ".ldf" / "answerpacks" / spec_name

    answerpack_path = None
    if spec_answerpack_path.exists():
        answerpack_path = spec_answerpack_path
    elif central_answerpack_path.exists():
        answerpack_path = central_answerpack_path

    if answerpack_path is None:
        return {
            "spec_name": spec_name,
            "status": "missing",
            "message": "No answerpacks directory found",
        }

    issues = []
    answerpacks = list(answerpack_path.glob("*.yaml")) + list(answerpack_path.glob("*.yml"))

    for answerpack in answerpacks:
        content = answerpack.read_text()
        # Check for template markers
        template_markers = [
            "REPLACE_ME",
            "TODO:",
            "PLACEHOLDER",
            "YOUR_",
            'feature_name: ""',
            "feature_name: ''",
        ]
        for marker in template_markers:
            if marker in content:
                issues.append(
                    {"file": answerpack.name, "issue": f"Contains template marker: {marker}"}
                )
                break

    return {
        "spec_name": spec_name,
        "status": "valid" if not issues else "invalid",
        "answerpack_count": len(answerpacks),
        "issues": issues,
    }


async def lint_spec(spec_name: str) -> dict[str, Any]:
    """Run spec linter validation with async subprocess and concurrency control.

    Uses asyncio.create_subprocess_exec for true async execution and a semaphore
    to limit concurrent lint operations (configurable via LDF_MAX_CONCURRENT_LINTS).

    Results are cached for LDF_LINT_CACHE_TTL seconds (default 60s) and automatically
    invalidated when spec files are modified.
    """
    try:
        spec_path = _validate_spec_name(spec_name)
    except ValueError as e:
        return {"spec_name": spec_name, "status": "ERROR", "message": str(e)}

    if not spec_path.exists():
        return {
            "spec_name": spec_name,
            "status": "ERROR",
            "message": f"Spec not found: {spec_path}",
        }

    # Check cache first
    cached = _get_cached_lint(spec_name, spec_path)
    if cached is not None:
        return cached

    semaphore = _get_lint_semaphore()

    try:
        async with semaphore:
            # Use async subprocess for non-blocking execution
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                "-m",
                "ldf.cli",
                "lint",
                spec_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(ldf_root),
            )

            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=LINT_TIMEOUT)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return {
                    "spec_name": spec_name,
                    "status": "TIMEOUT",
                    "message": f"Linter execution exceeded {LINT_TIMEOUT} seconds",
                }

            result = {
                "spec_name": spec_name,
                "status": "PASS" if process.returncode == 0 else "FAIL",
                "exit_code": process.returncode,
                "output": stdout.decode("utf-8", errors="replace"),
                "errors": stderr.decode("utf-8", errors="replace"),
            }

            # Cache successful results
            _cache_lint_result(spec_name, spec_path, result)
            return result
    except FileNotFoundError:
        # LDF CLI not installed, do basic validation
        result = await _basic_lint(spec_name)
        _cache_lint_result(spec_name, spec_path, result)
        return result
    except Exception as e:
        return {"spec_name": spec_name, "status": "ERROR", "message": str(e)}


async def _basic_lint(spec_name: str) -> dict[str, Any]:
    """Basic linting without ldf CLI."""
    spec_path = _validate_spec_name(spec_name)
    errors = []
    warnings = []

    # Check required files
    for filename in ["requirements.md", "design.md", "tasks.md"]:
        if not (spec_path / filename).exists():
            errors.append(f"Missing file: {filename}")

    # Check requirements.md content
    req_file = spec_path / "requirements.md"
    if req_file.exists():
        content = req_file.read_text()
        if "## Question-Pack Answers" not in content:
            errors.append("requirements.md: Missing Question-Pack Answers section")
        if "## Guardrail Coverage Matrix" not in content:
            errors.append("requirements.md: Missing Guardrail Coverage Matrix")

    # Check tasks.md content
    tasks_file = spec_path / "tasks.md"
    if tasks_file.exists():
        content = tasks_file.read_text()
        if "## Per-Task Guardrail Checklist" not in content:
            warnings.append("tasks.md: Missing Per-Task Guardrail Checklist")

    return {
        "spec_name": spec_name,
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "warnings": warnings,
    }


async def list_specs() -> dict[str, Any]:
    """List all available specs.

    Filters out symlinks escaping specs_dir and hidden directories for security.
    """
    if not specs_dir.exists():
        return {"specs": [], "count": 0}

    # Use is_safe_directory_entry to filter symlinks escaping specs_dir and hidden dirs
    specs = [d.name for d in specs_dir.iterdir()
             if d.is_dir() and is_safe_directory_entry(d, specs_dir)]

    return {"count": len(specs), "specs": sorted(specs)}


async def main():
    """Run the MCP server using stdio transport."""
    logger.info("Spec Inspector MCP Server starting (stdio mode)")
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
