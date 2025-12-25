# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

cockroachdb-mcp is a Python MCP (Model Context Protocol) server that enables AI assistants to interact with CockroachDB clusters. It uses `psycopg` (PostgreSQL driver) since CockroachDB is PostgreSQL-compatible, and provides tools for querying, CRUD operations, and cluster management.

## Development Commands

```bash
# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest                                      # All tests
pytest tests/test_connection.py             # Single file
pytest --cov=cockroachdb_mcp --cov-report=html    # With coverage

# Linting and type checking
ruff check .
ruff format .
mypy src/
```

## Tech Stack

- **Language**: Python 3.10+
- **MCP Framework**: `mcp` (FastMCP)
- **Database Driver**: `psycopg` (PostgreSQL-compatible)
- **Build System**: hatchling with pyproject.toml
- **Testing**: pytest, pytest-cov, pytest-mock, pytest-asyncio
- **Linting/Formatting**: ruff
- **Type Checking**: mypy
- **Settings**: pydantic-settings (environment variable binding)

## Architecture

```
src/cockroachdb_mcp/
├── server.py           # FastMCP server entry point
├── connection.py       # Connection management
├── config.py           # Pydantic settings, environment config
├── tools/              # MCP tool implementations
│   ├── query.py        # Query execution
│   ├── tables.py       # Schema discovery
│   ├── crud.py         # CRUD operations
│   ├── databases.py    # Database management
│   ├── transaction.py  # Transaction management
│   ├── cluster.py      # Cluster operations
│   ├── export.py       # Data export
│   └── knowledge.py    # Knowledge persistence
├── auth/               # OAuth authentication
│   ├── provider.py     # OAuth provider
│   ├── storage.py      # Token storage
│   └── idp/            # Identity provider adapters
├── resources/          # MCP resources
│   ├── knowledge.py    # Knowledge resource
│   ├── syntax_help.py  # SQL reference
│   └── examples.py     # Example queries
└── utils/
    ├── safety.py       # Query validation
    ├── watchdog.py     # Connection watchdog
    ├── knowledge.py    # Knowledge file manager
    └── audit.py        # Audit logging
```

## Environment Variables

Required: `CRDB_HOST`, `CRDB_USER`, `CRDB_DATABASE`
Optional: `CRDB_PASSWORD`, `CRDB_PORT`, `CRDB_CLUSTER`, `CRDB_SSLMODE`
Safety: `CRDB_READ_ONLY`, `CRDB_MAX_ROWS`, `CRDB_BLOCKED_COMMANDS`

## Coding Standards

- Follow PEP 8; use ruff for linting/formatting
- Maximum line length: 100 characters
- Type hints required for all function signatures
- Google-style docstrings for public APIs

## Key Patterns

**Connection Pattern**: Use `psycopg.AsyncConnection` for async database operations.

**Safety Controls**: SQL validation via blocklist, parameterized queries, read-only mode.

**Schema Discovery**: Use `information_schema` tables for metadata (PostgreSQL-compatible).

**CockroachDB Specifics**: Use `crdb_internal` schema for cluster-specific info.

## Reference Implementations

- [pymssql-mcp](https://github.com/bpamiri/pymssql-mcp) - SQL Server MCP
- [u2-mcp](https://github.com/bpamiri/u2-mcp) - Universe/UniData MCP
- [elasticsearch-mcp](https://github.com/bpamiri/elasticsearch-mcp) - Elasticsearch MCP
