#!/usr/bin/env python3
"""
Database Inspector MCP Server Template

Provides real-time queries for PostgreSQL schema, RLS policies, and indexes.

IMPORTANT: This is a template. Copy to your project and customize as needed.

Usage:
    python server.py

Environment Variables:
    DATABASE_URL: PostgreSQL connection string (required)
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

from mcp import types
from mcp.server import Server
from mcp.server.stdio import stdio_server

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from schema_query import SchemaQuery

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("db_inspector")

# Initialize MCP Server
app = Server("db_inspector")

# Initialize database connection
database_url = os.getenv("DATABASE_URL")
if not database_url:
    logger.error("DATABASE_URL environment variable not set")
    sys.exit(1)

query = SchemaQuery(database_url)
logger.info("Initialized DatabaseInspector")


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    """List all available MCP tools."""
    return [
        types.Tool(
            name="list_tables",
            description="List all tables in the database (excludes system tables)",
            inputSchema={
                "type": "object",
                "properties": {
                    "schema": {
                        "type": "string",
                        "description": "Database schema (default: public)",
                        "default": "public",
                    },
                    "include_rls_status": {
                        "type": "boolean",
                        "description": "Include RLS enabled/disabled status",
                        "default": False,
                    },
                },
            },
        ),
        types.Tool(
            name="get_table_schema",
            description="Get table structure (columns, types, constraints, nullability)",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {"type": "string", "description": "Name of the table"},
                    "schema": {
                        "type": "string",
                        "description": "Database schema (default: public)",
                        "default": "public",
                    },
                },
                "required": ["table_name"],
            },
        ),
        types.Tool(
            name="get_rls_policies",
            description="List all RLS policies for a table",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {"type": "string", "description": "Name of the table"},
                    "schema": {
                        "type": "string",
                        "description": "Database schema (default: public)",
                        "default": "public",
                    },
                },
                "required": ["table_name"],
            },
        ),
        types.Tool(
            name="explain_rls_policy",
            description="Get detailed RLS policy definition (USING/CHECK clauses)",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {"type": "string", "description": "Name of the table"},
                    "policy_name": {"type": "string", "description": "Name of the policy"},
                    "schema": {
                        "type": "string",
                        "description": "Database schema (default: public)",
                        "default": "public",
                    },
                },
                "required": ["table_name", "policy_name"],
            },
        ),
        types.Tool(
            name="get_indexes",
            description="List all indexes for a table",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {"type": "string", "description": "Name of the table"},
                    "schema": {
                        "type": "string",
                        "description": "Database schema (default: public)",
                        "default": "public",
                    },
                },
                "required": ["table_name"],
            },
        ),
        types.Tool(
            name="validate_constraints",
            description="Check UNIQUE, CHECK, and FK constraints for a table",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {"type": "string", "description": "Name of the table"},
                    "schema": {
                        "type": "string",
                        "description": "Database schema (default: public)",
                        "default": "public",
                    },
                },
                "required": ["table_name"],
            },
        ),
        types.Tool(
            name="check_rls_enabled",
            description="Check if RLS is enabled and forced on a table",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {"type": "string", "description": "Name of the table"},
                    "schema": {
                        "type": "string",
                        "description": "Database schema (default: public)",
                        "default": "public",
                    },
                },
                "required": ["table_name"],
            },
        ),
        types.Tool(
            name="get_migration_history",
            description="Get Alembic migration history from alembic_version table",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Execute a tool call."""
    logger.info(f"Calling tool: {name} with arguments: {arguments}")

    try:
        schema = arguments.get("schema", "public")

        if name == "list_tables":
            result = await query.list_tables(
                schema=schema, include_rls=arguments.get("include_rls_status", False)
            )
        elif name == "get_table_schema":
            result = await query.get_table_schema(table_name=arguments["table_name"], schema=schema)
        elif name == "get_rls_policies":
            result = await query.get_rls_policies(table_name=arguments["table_name"], schema=schema)
        elif name == "explain_rls_policy":
            result = await query.explain_rls_policy(
                table_name=arguments["table_name"],
                policy_name=arguments["policy_name"],
                schema=schema,
            )
        elif name == "get_indexes":
            result = await query.get_indexes(table_name=arguments["table_name"], schema=schema)
        elif name == "validate_constraints":
            result = await query.validate_constraints(
                table_name=arguments["table_name"], schema=schema
            )
        elif name == "check_rls_enabled":
            result = await query.check_rls_enabled(
                table_name=arguments["table_name"], schema=schema
            )
        elif name == "get_migration_history":
            result = await query.get_migration_history()
        else:
            raise ValueError(f"Unknown tool: {name}")

        return [types.TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
    except Exception as e:
        logger.error(f"Error executing {name}: {e}", exc_info=True)
        return [types.TextContent(type="text", text=json.dumps({"error": str(e)}, indent=2))]


async def main():
    """Run the MCP server using stdio transport."""
    logger.info("Database Inspector MCP Server starting (stdio mode)")
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
