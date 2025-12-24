"""CockroachDB MCP Server - Main entry point."""

from __future__ import annotations

import argparse
import sys
from typing import Any

from mcp.server.fastmcp import FastMCP

from .config import settings
from .connection import connection_manager
from .tools import cluster, crud, query, tables

# Initialize FastMCP server
mcp = FastMCP("cockroachdb-mcp")


# =============================================================================
# Connection Tools
# =============================================================================


@mcp.tool()
async def connect() -> dict[str, Any]:
    """Connect to the CockroachDB cluster.

    Uses configuration from environment variables (CRDB_HOST, CRDB_USER, etc.).

    Returns:
        Connection status and cluster information.
    """
    try:
        return await connection_manager.connect()
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
async def disconnect() -> dict[str, Any]:
    """Disconnect from the CockroachDB cluster.

    Returns:
        Disconnection status.
    """
    return await connection_manager.disconnect()


@mcp.tool()
async def cluster_status() -> dict[str, Any]:
    """Get the health status of the CockroachDB cluster.

    Returns:
        Cluster health including node count and live nodes.
    """
    try:
        return await cluster.cluster_health()
    except Exception as e:
        return {"status": "error", "error": str(e)}


# =============================================================================
# Query Tools
# =============================================================================


@mcp.tool()
async def execute_query(sql: str, max_rows: int | None = None) -> dict[str, Any]:
    """Execute a SQL query.

    Args:
        sql: SQL statement to execute.
        max_rows: Maximum rows to return (default: from config).

    Returns:
        Query results with columns and rows.
    """
    try:
        return await query.execute_query(sql, max_rows)
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
async def validate_query(sql: str) -> dict[str, Any]:
    """Check if a query is safe to execute without running it.

    Args:
        sql: SQL statement to validate.

    Returns:
        Validation result with any issues found.
    """
    try:
        return await query.validate_query(sql)
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
async def explain_query(sql: str, analyze: bool = False) -> dict[str, Any]:
    """Get the execution plan for a query.

    Args:
        sql: SQL query to explain.
        analyze: If True, actually execute to get runtime stats.

    Returns:
        Query execution plan.
    """
    try:
        return await query.explain_query(sql, analyze)
    except Exception as e:
        return {"status": "error", "error": str(e)}


# =============================================================================
# Schema Discovery Tools
# =============================================================================


@mcp.tool()
async def list_databases(include_system: bool = False) -> dict[str, Any]:
    """List all databases in the cluster.

    Args:
        include_system: Include system databases (postgres, defaultdb, etc.).

    Returns:
        List of databases.
    """
    try:
        return await tables.list_databases(include_system)
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
async def list_schemas() -> dict[str, Any]:
    """List schemas in the current database.

    Returns:
        List of schemas.
    """
    try:
        return await tables.list_schemas()
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
async def list_tables(
    schema: str | None = None,
    include_views: bool = True,
    include_system: bool = False,
) -> dict[str, Any]:
    """List all tables in the database.

    Args:
        schema: Filter by schema name (default: all user schemas).
        include_views: Include views in results.
        include_system: Include system tables.

    Returns:
        List of tables with schema, name, and type.
    """
    try:
        return await tables.list_tables(schema, include_views, include_system)
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
async def describe_table(table: str) -> dict[str, Any]:
    """Get detailed column information for a table.

    Args:
        table: Table name (schema.table or just table for public schema).

    Returns:
        Table structure with columns, indexes, and primary key.
    """
    try:
        return await tables.describe_table(table)
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
async def get_table_stats(table: str) -> dict[str, Any]:
    """Get statistics for a table.

    Args:
        table: Table name (schema.table or just table).

    Returns:
        Table statistics including row count and size.
    """
    try:
        return await tables.get_table_stats(table)
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
async def get_foreign_keys(table: str) -> dict[str, Any]:
    """Get foreign key constraints for a table.

    Args:
        table: Table name (schema.table or just table).

    Returns:
        Foreign key information.
    """
    try:
        return await tables.get_foreign_keys(table)
    except Exception as e:
        return {"status": "error", "error": str(e)}


# =============================================================================
# CRUD Tools
# =============================================================================


@mcp.tool()
async def read_rows(
    table: str,
    id_value: str | int | None = None,
    id_column: str = "id",
    where: str | None = None,
    columns: list[str] | None = None,
    order_by: str | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    """Read rows from a table.

    Args:
        table: Table name (schema.table or just table).
        id_value: Primary key value for single row lookup.
        id_column: Name of the ID column (default: 'id').
        where: WHERE clause (without 'WHERE').
        columns: List of columns to return (default: all).
        order_by: ORDER BY clause (without 'ORDER BY').
        limit: Maximum rows to return.

    Returns:
        Query results.
    """
    try:
        return await crud.read_rows(table, id_value, id_column, where, columns, order_by, limit)
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
async def insert_row(
    table: str,
    data: dict[str, Any],
    returning: list[str] | None = None,
) -> dict[str, Any]:
    """Insert a new row into a table.

    Args:
        table: Table name (schema.table or just table).
        data: Column names and values to insert.
        returning: Columns to return from inserted row.

    Returns:
        Insert result.
    """
    try:
        return await crud.insert_row(table, data, returning)
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
async def update_row(
    table: str,
    id_value: str | int,
    data: dict[str, Any],
    id_column: str = "id",
    returning: list[str] | None = None,
) -> dict[str, Any]:
    """Update an existing row by primary key.

    Args:
        table: Table name (schema.table or just table).
        id_value: Primary key value.
        data: Column names and new values.
        id_column: Name of the ID column (default: 'id').
        returning: Columns to return from updated row.

    Returns:
        Update result.
    """
    try:
        return await crud.update_row(table, id_value, data, id_column, returning)
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
async def delete_row(
    table: str,
    id_value: str | int,
    id_column: str = "id",
) -> dict[str, Any]:
    """Delete a row by primary key.

    Args:
        table: Table name (schema.table or just table).
        id_value: Primary key value.
        id_column: Name of the ID column (default: 'id').

    Returns:
        Delete result.
    """
    try:
        return await crud.delete_row(table, id_value, id_column)
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
async def upsert_row(
    table: str,
    data: dict[str, Any],
    conflict_columns: list[str],
    update_columns: list[str] | None = None,
    returning: list[str] | None = None,
) -> dict[str, Any]:
    """Insert or update a row (UPSERT).

    Args:
        table: Table name (schema.table or just table).
        data: Column names and values.
        conflict_columns: Columns to check for conflicts (usually primary key).
        update_columns: Columns to update on conflict (default: all except conflict columns).
        returning: Columns to return.

    Returns:
        Upsert result.
    """
    try:
        return await crud.upsert_row(table, data, conflict_columns, update_columns, returning)
    except Exception as e:
        return {"status": "error", "error": str(e)}


# =============================================================================
# Database Tools
# =============================================================================


@mcp.tool()
async def switch_database(database_name: str) -> dict[str, Any]:
    """Switch the active database context.

    Args:
        database_name: Database to switch to.

    Returns:
        Switch status.
    """
    try:
        return await connection_manager.switch_database(database_name)
    except Exception as e:
        return {"status": "error", "error": str(e)}


# =============================================================================
# Transaction Tools
# =============================================================================


@mcp.tool()
async def begin_transaction() -> dict[str, Any]:
    """Begin a database transaction.

    Returns:
        Transaction status.
    """
    try:
        return await connection_manager.begin_transaction()
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
async def commit_transaction() -> dict[str, Any]:
    """Commit the current transaction.

    Returns:
        Commit status.
    """
    try:
        return await connection_manager.commit_transaction()
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
async def rollback_transaction() -> dict[str, Any]:
    """Rollback the current transaction.

    Returns:
        Rollback status.
    """
    try:
        return await connection_manager.rollback_transaction()
    except Exception as e:
        return {"status": "error", "error": str(e)}


# =============================================================================
# Cluster Tools
# =============================================================================


@mcp.tool()
async def list_nodes() -> dict[str, Any]:
    """List all nodes in the CockroachDB cluster.

    Returns:
        List of cluster nodes with their status.
    """
    try:
        return await cluster.list_nodes()
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
async def node_status(node_id: int | None = None) -> dict[str, Any]:
    """Get detailed status for a node.

    Args:
        node_id: Specific node ID (optional, returns all if not specified).

    Returns:
        Node status information.
    """
    try:
        return await cluster.node_status(node_id)
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
async def show_regions() -> dict[str, Any]:
    """Show database regions for multi-region clusters.

    Returns:
        Region information.
    """
    try:
        return await cluster.show_regions()
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
async def show_jobs(
    job_type: str | None = None,
    status: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """Show background jobs in the cluster.

    Args:
        job_type: Filter by job type (BACKUP, RESTORE, IMPORT, etc.).
        status: Filter by status (running, succeeded, failed, etc.).
        limit: Maximum jobs to return.

    Returns:
        List of jobs.
    """
    try:
        return await cluster.show_jobs(job_type, status, limit)
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
async def show_sessions(active_only: bool = True) -> dict[str, Any]:
    """Show active sessions in the cluster.

    Args:
        active_only: Only show sessions with active queries.

    Returns:
        List of sessions.
    """
    try:
        return await cluster.show_sessions(active_only)
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
async def show_statements(limit: int = 20) -> dict[str, Any]:
    """Show active statements in the cluster.

    Args:
        limit: Maximum statements to return.

    Returns:
        List of active statements.
    """
    try:
        return await cluster.show_statements(limit)
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
async def cancel_query(query_id: str) -> dict[str, Any]:
    """Cancel a running query.

    Args:
        query_id: The query ID to cancel.

    Returns:
        Cancellation result.
    """
    try:
        return await cluster.cancel_query(query_id)
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
async def show_ranges(table: str | None = None, limit: int = 50) -> dict[str, Any]:
    """Show range distribution in the cluster.

    Args:
        table: Optional table to filter ranges.
        limit: Maximum ranges to return.

    Returns:
        Range distribution information.
    """
    try:
        return await cluster.show_ranges(table, limit)
    except Exception as e:
        return {"status": "error", "error": str(e)}


@mcp.tool()
async def show_zone_config(table: str | None = None) -> dict[str, Any]:
    """Show zone configurations.

    Args:
        table: Optional table to get zone config for.

    Returns:
        Zone configuration.
    """
    try:
        return await cluster.show_zone_config(table)
    except Exception as e:
        return {"status": "error", "error": str(e)}


# =============================================================================
# CLI Entry Point
# =============================================================================


def main() -> None:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="CockroachDB MCP Server - Connect AI assistants to CockroachDB"
    )
    parser.add_argument(
        "--http",
        action="store_true",
        help="Run as HTTP/SSE server (legacy mode)",
    )
    parser.add_argument(
        "--streamable-http",
        action="store_true",
        help="Run as Streamable HTTP server for Claude.ai Integrations",
    )
    parser.add_argument(
        "--host",
        type=str,
        default=None,
        help="HTTP server host (overrides CRDB_HTTP_HOST env var)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="HTTP server port (overrides CRDB_HTTP_PORT env var)",
    )

    args = parser.parse_args()

    # Determine host and port
    host = args.host or settings.http_host
    port = args.port or settings.http_port

    if args.streamable_http:
        # Streamable HTTP mode for Claude.ai
        print(f"Starting CockroachDB MCP Server (Streamable HTTP) on {host}:{port}")
        # TODO: Implement streamable HTTP with OAuth
        print("Streamable HTTP mode not yet implemented")
        sys.exit(1)
    elif args.http:
        # Legacy HTTP/SSE mode
        print(f"Starting CockroachDB MCP Server (HTTP/SSE) on {host}:{port}")
        # TODO: Implement HTTP/SSE mode
        print("HTTP/SSE mode not yet implemented")
        sys.exit(1)
    else:
        # Default stdio mode
        print("Starting CockroachDB MCP Server (stdio)", file=sys.stderr)
        mcp.run()


if __name__ == "__main__":
    main()
