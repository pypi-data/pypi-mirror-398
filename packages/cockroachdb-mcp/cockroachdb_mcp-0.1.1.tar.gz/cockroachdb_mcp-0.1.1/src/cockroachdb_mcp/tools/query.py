"""Query execution tools for cockroachdb-mcp."""

from __future__ import annotations

import re
from typing import Any

from ..config import settings
from ..connection import connection_manager


def _is_blocked_command(query: str) -> tuple[bool, str | None]:
    """Check if a query contains blocked commands.

    Args:
        query: SQL query to check.

    Returns:
        Tuple of (is_blocked, blocked_command).
    """
    query_upper = query.upper().strip()

    for cmd in settings.blocked_commands_list:
        # Match command at start of query or after whitespace
        pattern = rf"(^|\s){re.escape(cmd)}(\s|$)"
        if re.search(pattern, query_upper):
            return True, cmd

    return False, None


def _is_select_query(query: str) -> bool:
    """Check if query is a SELECT statement."""
    query_stripped = query.strip().upper()
    return query_stripped.startswith("SELECT") or query_stripped.startswith("WITH")


def _is_read_only_query(query: str) -> bool:
    """Check if query is read-only (SELECT, SHOW, EXPLAIN, etc.)."""
    query_stripped = query.strip().upper()
    read_only_prefixes = (
        "SELECT",
        "SHOW",
        "EXPLAIN",
        "WITH",
        "DESCRIBE",
        "DESC",
    )
    return query_stripped.startswith(read_only_prefixes)


async def validate_query(query: str) -> dict[str, Any]:
    """Validate a SQL query without executing it.

    Args:
        query: SQL query to validate.

    Returns:
        Validation result with is_valid and any issues.
    """
    issues: list[str] = []

    # Check for empty query
    if not query or not query.strip():
        return {
            "is_valid": False,
            "issues": ["Query is empty"],
            "query_type": None,
        }

    # Check for blocked commands
    is_blocked, blocked_cmd = _is_blocked_command(query)
    if is_blocked:
        issues.append(f"Blocked command: {blocked_cmd}")

    # Check read-only mode
    if settings.read_only and not _is_read_only_query(query):
        issues.append("Server is in read-only mode; only SELECT/SHOW/EXPLAIN allowed")

    # Determine query type
    query_upper = query.strip().upper()
    if query_upper.startswith("SELECT") or query_upper.startswith("WITH"):
        query_type = "SELECT"
    elif query_upper.startswith("INSERT"):
        query_type = "INSERT"
    elif query_upper.startswith("UPDATE"):
        query_type = "UPDATE"
    elif query_upper.startswith("DELETE"):
        query_type = "DELETE"
    elif query_upper.startswith("SHOW"):
        query_type = "SHOW"
    elif query_upper.startswith("EXPLAIN"):
        query_type = "EXPLAIN"
    else:
        query_type = "OTHER"

    return {
        "is_valid": len(issues) == 0,
        "issues": issues,
        "query_type": query_type,
        "is_read_only": _is_read_only_query(query),
    }


async def execute_query(
    query: str,
    max_rows: int | None = None,
) -> dict[str, Any]:
    """Execute a SQL query.

    Args:
        query: SQL query to execute.
        max_rows: Maximum rows to return.

    Returns:
        Query results.
    """
    # Validate first
    validation = await validate_query(query)
    if not validation["is_valid"]:
        return {
            "status": "error",
            "error": "Query validation failed",
            "issues": validation["issues"],
        }

    return await connection_manager.execute_query(query, max_rows=max_rows)


async def explain_query(query: str, analyze: bool = False) -> dict[str, Any]:
    """Get the execution plan for a query.

    Args:
        query: SQL query to explain.
        analyze: If True, actually execute to get runtime stats.

    Returns:
        Execution plan.
    """
    # Validate the underlying query
    validation = await validate_query(query)
    if not validation["is_valid"]:
        return {
            "status": "error",
            "error": "Query validation failed",
            "issues": validation["issues"],
        }

    # Build EXPLAIN query
    if analyze:
        explain_query_str = f"EXPLAIN ANALYZE {query}"
    else:
        explain_query_str = f"EXPLAIN {query}"

    result = await connection_manager.execute_query(explain_query_str)

    if result.get("status") == "error":
        return result

    # Format the plan output
    plan_lines = []
    for row in result.get("rows", []):
        # CockroachDB returns plan in 'info' column
        if "info" in row:
            plan_lines.append(row["info"])
        else:
            # Fallback for different column names
            plan_lines.append(str(list(row.values())[0]) if row else "")

    return {
        "status": "success",
        "query": query,
        "analyzed": analyze,
        "plan": "\n".join(plan_lines),
    }


async def count_rows(
    table: str,
    where: str | None = None,
) -> dict[str, Any]:
    """Count rows in a table.

    Args:
        table: Table name.
        where: Optional WHERE clause (without 'WHERE').

    Returns:
        Row count.
    """
    # Basic SQL injection prevention for table name
    if not re.match(r"^[\w.]+$", table):
        return {"status": "error", "error": "Invalid table name"}

    query = f"SELECT COUNT(*) as count FROM {table}"
    if where:
        query += f" WHERE {where}"

    result = await connection_manager.execute_query(query)

    if result.get("status") == "error":
        return result

    rows = result.get("rows", [])
    count = rows[0]["count"] if rows else 0

    return {
        "status": "success",
        "table": table,
        "count": count,
        "where": where,
    }
