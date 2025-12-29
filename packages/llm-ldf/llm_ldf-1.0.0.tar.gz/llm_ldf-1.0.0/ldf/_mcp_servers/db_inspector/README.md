# Database Inspector MCP Server (Optional)

Optional MCP server for inspecting PostgreSQL database schema, RLS policies, and indexes.

## When to Use

Add this server if your project:
- Uses PostgreSQL with Row-Level Security (RLS)
- Needs schema inspection during development
- Has complex migration requirements

## Setup

### 1. Copy Template to Your Project

The db_inspector template files are bundled with LDF. Copy them to your project:

```bash
# Find where ldf is installed
python -c "import ldf; print(ldf.__file__)"
# Copy the template from that location
```

### 2. Install Dependencies

```bash
pip install psycopg2-binary  # PostgreSQL adapter
```

### 3. Configure Database Connection

Set the `DATABASE_URL` environment variable:

```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/mydb"
```

### 4. Add to MCP Configuration

Edit `.agent/mcp.json`:

```json
{
  "mcpServers": {
    "db_inspector": {
      "command": "python",
      "args": ["-m", "ldf._mcp_servers.db_inspector.template.server"],
      "env": {
        "DATABASE_URL": "postgresql://user:pass@localhost:5432/mydb"
      }
    }
  }
}
```

## Available Tools

| Tool | Description |
|------|-------------|
| `list_tables` | List all tables with optional RLS status |
| `get_table_schema` | Get columns, types, constraints |
| `get_rls_policies` | List RLS policies for a table |
| `explain_rls_policy` | Get detailed policy definition |
| `get_indexes` | List indexes for a table |
| `validate_constraints` | Check UNIQUE, CHECK, FK constraints |
| `get_migration_history` | Get Alembic migration history |

## Security Notes

- **Never commit** `DATABASE_URL` with real credentials
- Use environment variables or secrets management
- Consider read-only database users for inspection
- This template connects directly to your database - review the code before using

## Template Structure

```
db_inspector/
├── README.md           # This file
└── template/
    ├── server.py       # MCP server implementation
    ├── schema_query.py # Database query utilities
    └── requirements.txt
```

## Customization

The template provides a starting point. You may want to:
- Add project-specific queries
- Customize RLS inspection for your policies
- Add migration validation for your schema
- Integrate with your specific ORM

## Why Optional?

Unlike spec_inspector and coverage_reporter which work with any project, db_inspector:
- Requires PostgreSQL (not all projects use it)
- Needs database credentials (security consideration)
- Should be customized for each project's schema

That's why it's provided as a template to copy, not a ready-to-use server.
