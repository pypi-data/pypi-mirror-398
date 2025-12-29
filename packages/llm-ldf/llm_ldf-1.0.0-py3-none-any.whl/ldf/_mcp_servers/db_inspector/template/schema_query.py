"""
Database Schema Query Utilities

Provides async PostgreSQL queries for schema inspection, RLS policies, and indexes.

This is a template - customize queries for your specific schema needs.
"""

from typing import Any

import asyncpg


class SchemaQuery:
    """Async PostgreSQL schema query utilities."""

    def __init__(self, database_url: str):
        """Initialize with database URL."""
        self.database_url = database_url
        self._pool: asyncpg.Pool | None = None

    async def _get_pool(self) -> asyncpg.Pool:
        """Get or create connection pool."""
        if self._pool is None:
            self._pool = await asyncpg.create_pool(self.database_url, min_size=1, max_size=5)
        return self._pool

    async def _fetch(self, query: str, *args) -> list[dict]:
        """Execute query and return results as list of dicts."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]

    async def _fetchrow(self, query: str, *args) -> dict | None:
        """Execute query and return single row as dict."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(query, *args)
            return dict(row) if row else None

    async def list_tables(
        self, schema: str = "public", include_rls: bool = False
    ) -> list[dict[str, Any]]:
        """
        List all tables in schema (excludes system tables).

        Args:
            schema: Database schema name
            include_rls: Include RLS enabled status

        Returns:
            List of table info dicts
        """
        if include_rls:
            query = """
                SELECT
                    t.table_name,
                    t.table_type,
                    c.relrowsecurity as rls_enabled,
                    c.relforcerowsecurity as rls_forced
                FROM information_schema.tables t
                JOIN pg_class c ON c.relname = t.table_name
                JOIN pg_namespace n ON n.oid = c.relnamespace AND n.nspname = t.table_schema
                WHERE t.table_schema = $1
                    AND t.table_type = 'BASE TABLE'
                ORDER BY t.table_name
            """
        else:
            query = """
                SELECT
                    table_name,
                    table_type
                FROM information_schema.tables
                WHERE table_schema = $1
                    AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """

        return await self._fetch(query, schema)

    async def get_table_schema(self, table_name: str, schema: str = "public") -> dict[str, Any]:
        """
        Get table structure (columns, types, constraints, nullability).

        Args:
            table_name: Name of the table
            schema: Database schema name

        Returns:
            Dict with table info and columns
        """
        # Get columns
        columns_query = """
            SELECT
                column_name,
                data_type,
                udt_name,
                is_nullable,
                column_default,
                character_maximum_length,
                numeric_precision,
                numeric_scale
            FROM information_schema.columns
            WHERE table_schema = $1 AND table_name = $2
            ORDER BY ordinal_position
        """
        columns = await self._fetch(columns_query, schema, table_name)

        # Get primary key
        pk_query = """
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            WHERE tc.constraint_type = 'PRIMARY KEY'
                AND tc.table_schema = $1
                AND tc.table_name = $2
            ORDER BY kcu.ordinal_position
        """
        pk_columns = await self._fetch(pk_query, schema, table_name)

        return {
            "table_name": table_name,
            "schema": schema,
            "columns": columns,
            "primary_key": [row["column_name"] for row in pk_columns],
        }

    async def get_rls_policies(
        self, table_name: str, schema: str = "public"
    ) -> list[dict[str, Any]]:
        """
        List all RLS policies for a table.

        Args:
            table_name: Name of the table
            schema: Database schema name

        Returns:
            List of policy info dicts
        """
        query = """
            SELECT
                pol.polname as policy_name,
                CASE pol.polcmd
                    WHEN 'r' THEN 'SELECT'
                    WHEN 'a' THEN 'INSERT'
                    WHEN 'w' THEN 'UPDATE'
                    WHEN 'd' THEN 'DELETE'
                    WHEN '*' THEN 'ALL'
                END as command,
                CASE pol.polpermissive
                    WHEN true THEN 'PERMISSIVE'
                    ELSE 'RESTRICTIVE'
                END as type,
                pg_get_expr(pol.polqual, pol.polrelid) as using_expression,
                pg_get_expr(pol.polwithcheck, pol.polrelid) as with_check_expression,
                ARRAY(
                    SELECT rolname FROM pg_roles WHERE oid = ANY(pol.polroles)
                ) as roles
            FROM pg_policy pol
            JOIN pg_class c ON c.oid = pol.polrelid
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE c.relname = $1 AND n.nspname = $2
            ORDER BY pol.polname
        """
        return await self._fetch(query, table_name, schema)

    async def explain_rls_policy(
        self, table_name: str, policy_name: str, schema: str = "public"
    ) -> dict[str, Any] | None:
        """
        Get detailed RLS policy definition (USING/CHECK clauses).

        Args:
            table_name: Name of the table
            policy_name: Name of the policy
            schema: Database schema name

        Returns:
            Policy details dict or None if not found
        """
        query = """
            SELECT
                pol.polname as policy_name,
                c.relname as table_name,
                n.nspname as schema_name,
                CASE pol.polcmd
                    WHEN 'r' THEN 'SELECT'
                    WHEN 'a' THEN 'INSERT'
                    WHEN 'w' THEN 'UPDATE'
                    WHEN 'd' THEN 'DELETE'
                    WHEN '*' THEN 'ALL'
                END as command,
                CASE pol.polpermissive
                    WHEN true THEN 'PERMISSIVE'
                    ELSE 'RESTRICTIVE'
                END as type,
                pg_get_expr(pol.polqual, pol.polrelid) as using_clause,
                pg_get_expr(pol.polwithcheck, pol.polrelid) as with_check_clause,
                ARRAY(
                    SELECT rolname FROM pg_roles WHERE oid = ANY(pol.polroles)
                ) as applies_to_roles
            FROM pg_policy pol
            JOIN pg_class c ON c.oid = pol.polrelid
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE c.relname = $1 AND n.nspname = $2 AND pol.polname = $3
        """
        return await self._fetchrow(query, table_name, schema, policy_name)

    async def get_indexes(self, table_name: str, schema: str = "public") -> list[dict[str, Any]]:
        """
        List all indexes for a table.

        Args:
            table_name: Name of the table
            schema: Database schema name

        Returns:
            List of index info dicts
        """
        query = """
            SELECT
                i.relname as index_name,
                ix.indisunique as is_unique,
                ix.indisprimary as is_primary,
                am.amname as index_type,
                ARRAY(
                    SELECT pg_get_indexdef(ix.indexrelid, k + 1, true)
                    FROM generate_subscripts(ix.indkey, 1) as k
                    ORDER BY k
                ) as columns,
                pg_get_indexdef(ix.indexrelid) as definition
            FROM pg_index ix
            JOIN pg_class t ON t.oid = ix.indrelid
            JOIN pg_class i ON i.oid = ix.indexrelid
            JOIN pg_namespace n ON n.oid = t.relnamespace
            JOIN pg_am am ON am.oid = i.relam
            WHERE t.relname = $1 AND n.nspname = $2
            ORDER BY i.relname
        """
        return await self._fetch(query, table_name, schema)

    async def validate_constraints(self, table_name: str, schema: str = "public") -> dict[str, Any]:
        """
        Check UNIQUE, CHECK, and FK constraints for a table.

        Args:
            table_name: Name of the table
            schema: Database schema name

        Returns:
            Dict with categorized constraints
        """
        query = """
            SELECT
                tc.constraint_name,
                tc.constraint_type,
                CASE
                    WHEN tc.constraint_type = 'CHECK' THEN
                        (SELECT pg_get_constraintdef(c.oid)
                         FROM pg_constraint c
                         JOIN pg_namespace n ON n.oid = c.connamespace
                         WHERE c.conname = tc.constraint_name AND n.nspname = tc.table_schema)
                    ELSE NULL
                END as check_clause,
                CASE
                    WHEN tc.constraint_type = 'FOREIGN KEY' THEN
                        (SELECT ccu.table_name
                         FROM information_schema.constraint_column_usage ccu
                         WHERE ccu.constraint_name = tc.constraint_name
                           AND ccu.constraint_schema = tc.constraint_schema
                         LIMIT 1)
                    ELSE NULL
                END as references_table,
                ARRAY(
                    SELECT kcu.column_name
                    FROM information_schema.key_column_usage kcu
                    WHERE kcu.constraint_name = tc.constraint_name
                      AND kcu.constraint_schema = tc.constraint_schema
                    ORDER BY kcu.ordinal_position
                ) as columns
            FROM information_schema.table_constraints tc
            WHERE tc.table_schema = $1
              AND tc.table_name = $2
              AND tc.constraint_type IN ('UNIQUE', 'CHECK', 'FOREIGN KEY')
            ORDER BY tc.constraint_type, tc.constraint_name
        """
        rows = await self._fetch(query, schema, table_name)

        # Categorize constraints
        result = {
            "table_name": table_name,
            "schema": schema,
            "unique_constraints": [],
            "check_constraints": [],
            "foreign_keys": [],
        }

        for row in rows:
            if row["constraint_type"] == "UNIQUE":
                result["unique_constraints"].append(
                    {
                        "name": row["constraint_name"],
                        "columns": row["columns"],
                    }
                )
            elif row["constraint_type"] == "CHECK":
                result["check_constraints"].append(
                    {
                        "name": row["constraint_name"],
                        "definition": row["check_clause"],
                    }
                )
            elif row["constraint_type"] == "FOREIGN KEY":
                result["foreign_keys"].append(
                    {
                        "name": row["constraint_name"],
                        "columns": row["columns"],
                        "references_table": row["references_table"],
                    }
                )

        return result

    async def check_rls_enabled(self, table_name: str, schema: str = "public") -> dict[str, Any]:
        """
        Check if RLS is enabled and forced on a table.

        Args:
            table_name: Name of the table
            schema: Database schema name

        Returns:
            Dict with RLS status
        """
        query = """
            SELECT
                c.relname as table_name,
                n.nspname as schema_name,
                c.relrowsecurity as rls_enabled,
                c.relforcerowsecurity as rls_forced
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE c.relname = $1 AND n.nspname = $2
        """
        row = await self._fetchrow(query, table_name, schema)

        if not row:
            return {
                "table_name": table_name,
                "schema": schema,
                "exists": False,
                "rls_enabled": False,
                "rls_forced": False,
            }

        return {
            "table_name": table_name,
            "schema": schema,
            "exists": True,
            "rls_enabled": row["rls_enabled"],
            "rls_forced": row["rls_forced"],
        }

    async def get_migration_history(self) -> list[dict[str, Any]]:
        """
        Get Alembic migration history from alembic_version table.

        Returns:
            List of migration version records
        """
        # Check if alembic_version table exists
        check_query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name = 'alembic_version'
            ) as exists
        """
        result = await self._fetchrow(check_query)

        if not result or not result["exists"]:
            return []

        query = """
            SELECT version_num
            FROM alembic_version
            ORDER BY version_num
        """
        return await self._fetch(query)

    async def close(self):
        """Close connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None
