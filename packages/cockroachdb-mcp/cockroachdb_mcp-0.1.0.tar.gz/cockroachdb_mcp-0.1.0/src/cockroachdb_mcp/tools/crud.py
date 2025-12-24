"""CRUD operations for cockroachdb-mcp."""

from __future__ import annotations

import re
from typing import Any

from ..config import settings
from ..connection import connection_manager


def _validate_table_name(table: str) -> tuple[bool, str | None]:
    """Validate table name format.

    Args:
        table: Table name to validate.

    Returns:
        Tuple of (is_valid, error_message).
    """
    # Allow schema.table format
    if not re.match(r"^[\w]+\.[\w]+$|^[\w]+$", table):
        return False, "Invalid table name format"
    return True, None


def _parse_table_name(table: str) -> tuple[str, str]:
    """Parse table name into schema and table.

    Args:
        table: Table name (schema.table or just table).

    Returns:
        Tuple of (schema, table_name).
    """
    if "." in table:
        schema, table_name = table.rsplit(".", 1)
    else:
        schema = "public"
        table_name = table
    return schema, table_name


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
    # Validate table name
    valid, error = _validate_table_name(table)
    if not valid:
        return {"status": "error", "error": error}

    schema, table_name = _parse_table_name(table)

    # Build column list
    if columns:
        # Validate column names
        for col in columns:
            if not re.match(r"^[\w]+$", col):
                return {"status": "error", "error": f"Invalid column name: {col}"}
        col_list = ", ".join(columns)
    else:
        col_list = "*"

    # Build query
    query = f"SELECT {col_list} FROM {schema}.{table_name}"

    # Add WHERE clause
    params: list[Any] = []
    if id_value is not None:
        query += f" WHERE {id_column} = %s"
        params.append(id_value)
    elif where:
        query += f" WHERE {where}"

    # Add ORDER BY
    if order_by:
        query += f" ORDER BY {order_by}"

    # Add LIMIT
    effective_limit = limit if limit is not None else settings.max_rows
    query += f" LIMIT {effective_limit}"

    conn = await connection_manager.ensure_connected()

    try:
        async with conn.cursor() as cur:
            if params:
                await cur.execute(query, tuple(params))
            else:
                await cur.execute(query)

            rows = await cur.fetchall()
            columns_returned = [desc.name for desc in cur.description] if cur.description else []

        return {
            "status": "success",
            "table": f"{schema}.{table_name}",
            "columns": columns_returned,
            "rows": rows,
            "row_count": len(rows),
            "limit": effective_limit,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


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
    # Check read-only mode
    if settings.read_only:
        return {"status": "error", "error": "Server is in read-only mode"}

    # Validate table name
    valid, error = _validate_table_name(table)
    if not valid:
        return {"status": "error", "error": error}

    if not data:
        return {"status": "error", "error": "No data provided"}

    schema, table_name = _parse_table_name(table)

    # Validate column names
    for col in data.keys():
        if not re.match(r"^[\w]+$", col):
            return {"status": "error", "error": f"Invalid column name: {col}"}

    # Build INSERT query
    columns = list(data.keys())
    placeholders = ", ".join(["%s"] * len(columns))
    col_list = ", ".join(columns)
    values = list(data.values())

    query = f"INSERT INTO {schema}.{table_name} ({col_list}) VALUES ({placeholders})"

    # Add RETURNING clause
    if returning:
        for col in returning:
            if not re.match(r"^[\w]+$", col):
                return {"status": "error", "error": f"Invalid column name in returning: {col}"}
        query += f" RETURNING {', '.join(returning)}"

    conn = await connection_manager.ensure_connected()

    try:
        async with conn.cursor() as cur:
            await cur.execute(query, tuple(values))

            if returning:
                row = await cur.fetchone()
                return {
                    "status": "success",
                    "table": f"{schema}.{table_name}",
                    "action": "inserted",
                    "returning": row,
                }
            else:
                return {
                    "status": "success",
                    "table": f"{schema}.{table_name}",
                    "action": "inserted",
                    "rows_affected": cur.rowcount,
                }
    except Exception as e:
        return {"status": "error", "error": str(e)}


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
    # Check read-only mode
    if settings.read_only:
        return {"status": "error", "error": "Server is in read-only mode"}

    # Validate table name
    valid, error = _validate_table_name(table)
    if not valid:
        return {"status": "error", "error": error}

    if not data:
        return {"status": "error", "error": "No data provided"}

    schema, table_name = _parse_table_name(table)

    # Validate column names
    for col in data.keys():
        if not re.match(r"^[\w]+$", col):
            return {"status": "error", "error": f"Invalid column name: {col}"}

    # Build UPDATE query
    set_clauses = [f"{col} = %s" for col in data.keys()]
    set_clause = ", ".join(set_clauses)
    values = list(data.values())
    values.append(id_value)

    query = f"UPDATE {schema}.{table_name} SET {set_clause} WHERE {id_column} = %s"

    # Add RETURNING clause
    if returning:
        for col in returning:
            if not re.match(r"^[\w]+$", col):
                return {"status": "error", "error": f"Invalid column name in returning: {col}"}
        query += f" RETURNING {', '.join(returning)}"

    conn = await connection_manager.ensure_connected()

    try:
        async with conn.cursor() as cur:
            await cur.execute(query, tuple(values))

            if returning:
                row = await cur.fetchone()
                return {
                    "status": "success",
                    "table": f"{schema}.{table_name}",
                    "action": "updated",
                    "id": id_value,
                    "returning": row,
                }
            else:
                return {
                    "status": "success",
                    "table": f"{schema}.{table_name}",
                    "action": "updated",
                    "id": id_value,
                    "rows_affected": cur.rowcount,
                }
    except Exception as e:
        return {"status": "error", "error": str(e)}


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
    # Check read-only mode
    if settings.read_only:
        return {"status": "error", "error": "Server is in read-only mode"}

    # Validate table name
    valid, error = _validate_table_name(table)
    if not valid:
        return {"status": "error", "error": error}

    schema, table_name = _parse_table_name(table)

    query = f"DELETE FROM {schema}.{table_name} WHERE {id_column} = %s"

    conn = await connection_manager.ensure_connected()

    try:
        async with conn.cursor() as cur:
            await cur.execute(query, (id_value,))

            if cur.rowcount == 0:
                return {
                    "status": "warning",
                    "table": f"{schema}.{table_name}",
                    "action": "delete",
                    "id": id_value,
                    "message": "No row found with specified ID",
                    "rows_affected": 0,
                }

            return {
                "status": "success",
                "table": f"{schema}.{table_name}",
                "action": "deleted",
                "id": id_value,
                "rows_affected": cur.rowcount,
            }
    except Exception as e:
        return {"status": "error", "error": str(e)}


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
    # Check read-only mode
    if settings.read_only:
        return {"status": "error", "error": "Server is in read-only mode"}

    # Validate table name
    valid, error = _validate_table_name(table)
    if not valid:
        return {"status": "error", "error": error}

    if not data:
        return {"status": "error", "error": "No data provided"}

    if not conflict_columns:
        return {"status": "error", "error": "No conflict columns specified"}

    schema, table_name = _parse_table_name(table)

    # Validate all column names
    all_columns = list(data.keys()) + conflict_columns + (update_columns or []) + (returning or [])
    for col in all_columns:
        if not re.match(r"^[\w]+$", col):
            return {"status": "error", "error": f"Invalid column name: {col}"}

    # Determine columns to update
    if update_columns is None:
        update_columns = [c for c in data.keys() if c not in conflict_columns]

    if not update_columns:
        return {"status": "error", "error": "No columns to update on conflict"}

    # Build UPSERT query
    columns = list(data.keys())
    placeholders = ", ".join(["%s"] * len(columns))
    col_list = ", ".join(columns)
    values = list(data.values())

    conflict_list = ", ".join(conflict_columns)
    update_set = ", ".join([f"{col} = EXCLUDED.{col}" for col in update_columns])

    query = f"""
        INSERT INTO {schema}.{table_name} ({col_list})
        VALUES ({placeholders})
        ON CONFLICT ({conflict_list}) DO UPDATE SET {update_set}
    """

    # Add RETURNING clause
    if returning:
        query += f" RETURNING {', '.join(returning)}"

    conn = await connection_manager.ensure_connected()

    try:
        async with conn.cursor() as cur:
            await cur.execute(query, tuple(values))

            if returning:
                row = await cur.fetchone()
                return {
                    "status": "success",
                    "table": f"{schema}.{table_name}",
                    "action": "upserted",
                    "returning": row,
                }
            else:
                return {
                    "status": "success",
                    "table": f"{schema}.{table_name}",
                    "action": "upserted",
                    "rows_affected": cur.rowcount,
                }
    except Exception as e:
        return {"status": "error", "error": str(e)}
