"""Schema discovery tools for cockroachdb-mcp."""

from __future__ import annotations

from typing import Any

from ..config import settings
from ..connection import connection_manager


def _is_blocked_database(db_name: str) -> bool:
    """Check if a database is blocked."""
    return db_name in settings.blocked_databases_list


def _is_allowed_schema(schema_name: str) -> bool:
    """Check if a schema is allowed."""
    allowed = settings.allowed_schemas_list
    if allowed is None:
        return True
    return schema_name in allowed


async def list_databases(include_system: bool = False) -> dict[str, Any]:
    """List all databases in the cluster.

    Args:
        include_system: Include system databases.

    Returns:
        List of databases.
    """
    conn = await connection_manager.ensure_connected()

    try:
        async with conn.cursor() as cur:
            await cur.execute("SHOW DATABASES")
            rows = await cur.fetchall()

        databases = []
        system_dbs = {"system", "postgres", "defaultdb", "crdb_internal"}

        for row in rows:
            db_name = row.get("database_name", "")

            # Skip blocked databases
            if _is_blocked_database(db_name):
                continue

            # Skip system databases unless requested
            is_system = db_name in system_dbs
            if is_system and not include_system:
                continue

            databases.append(
                {
                    "name": db_name,
                    "is_system": is_system,
                }
            )

        return {
            "databases": databases,
            "count": len(databases),
            "current_database": connection_manager.current_database,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


async def list_schemas(database: str | None = None) -> dict[str, Any]:
    """List schemas in a database.

    Args:
        database: Database name (uses current if not specified).

    Returns:
        List of schemas.
    """
    conn = await connection_manager.ensure_connected()

    try:
        async with conn.cursor() as cur:
            await cur.execute("""
                SELECT schema_name
                FROM information_schema.schemata
                WHERE catalog_name = current_database()
                ORDER BY schema_name
            """)
            rows = await cur.fetchall()

        schemas = []
        system_schemas = {"crdb_internal", "information_schema", "pg_catalog", "pg_extension"}

        for row in rows:
            schema_name = row.get("schema_name", "")

            # Check if allowed
            if not _is_allowed_schema(schema_name):
                continue

            schemas.append(
                {
                    "name": schema_name,
                    "is_system": schema_name in system_schemas,
                }
            )

        return {
            "schemas": schemas,
            "count": len(schemas),
            "database": database or connection_manager.current_database,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


async def list_tables(
    schema: str | None = None,
    include_views: bool = True,
    include_system: bool = False,
) -> dict[str, Any]:
    """List all tables in the database.

    Args:
        schema: Filter by schema name.
        include_views: Include views in results.
        include_system: Include system tables.

    Returns:
        List of tables.
    """
    conn = await connection_manager.ensure_connected()

    try:
        # Build type filter
        table_types = ["'BASE TABLE'"]
        if include_views:
            table_types.append("'VIEW'")

        type_filter = f"table_type IN ({','.join(table_types)})"

        # Build schema filter
        schema_filter = ""
        if schema:
            schema_filter = f"AND table_schema = '{schema}'"
        elif not include_system:
            schema_filter = """
                AND table_schema NOT IN (
                    'crdb_internal', 'information_schema', 'pg_catalog', 'pg_extension'
                )
            """

        query = f"""
            SELECT
                table_schema,
                table_name,
                table_type
            FROM information_schema.tables
            WHERE {type_filter}
            {schema_filter}
            ORDER BY table_schema, table_name
        """

        async with conn.cursor() as cur:
            await cur.execute(query)
            rows = await cur.fetchall()

        tables = []
        for row in rows:
            schema_name = row.get("table_schema", "")

            # Check if schema is allowed
            if not _is_allowed_schema(schema_name):
                continue

            tables.append(
                {
                    "schema": schema_name,
                    "name": row.get("table_name", ""),
                    "type": "VIEW" if row.get("table_type") == "VIEW" else "TABLE",
                    "full_name": f"{schema_name}.{row.get('table_name', '')}",
                }
            )

        return {
            "tables": tables,
            "count": len(tables),
            "database": connection_manager.current_database,
            "schema_filter": schema,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


async def describe_table(table: str) -> dict[str, Any]:
    """Get detailed column information for a table.

    Args:
        table: Table name (schema.table or just table).

    Returns:
        Table structure with columns, constraints, and indexes.
    """
    conn = await connection_manager.ensure_connected()

    # Parse schema and table name
    if "." in table:
        schema, table_name = table.rsplit(".", 1)
    else:
        schema = "public"
        table_name = table

    # Check if schema is allowed
    if not _is_allowed_schema(schema):
        return {"status": "error", "error": f"Schema '{schema}' is not allowed"}

    result: dict[str, Any] = {
        "schema": schema,
        "table": table_name,
        "full_name": f"{schema}.{table_name}",
    }

    try:
        # Get columns
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT
                    column_name,
                    data_type,
                    is_nullable,
                    column_default,
                    character_maximum_length,
                    numeric_precision,
                    numeric_scale
                FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ordinal_position
            """,
                (schema, table_name),
            )
            column_rows = await cur.fetchall()

        if not column_rows:
            return {"status": "error", "error": f"Table '{table}' not found"}

        columns = []
        for row in column_rows:
            col_info: dict[str, Any] = {
                "name": row.get("column_name"),
                "type": row.get("data_type"),
                "nullable": row.get("is_nullable") == "YES",
                "default": row.get("column_default"),
            }

            # Add length/precision info if available
            if row.get("character_maximum_length"):
                col_info["max_length"] = row.get("character_maximum_length")
            if row.get("numeric_precision"):
                col_info["precision"] = row.get("numeric_precision")
                col_info["scale"] = row.get("numeric_scale")

            columns.append(col_info)

        result["columns"] = columns
        result["column_count"] = len(columns)

        # Get primary key
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT a.attname as column_name
                FROM pg_index i
                JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
                JOIN pg_class c ON c.oid = i.indrelid
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE i.indisprimary
                AND n.nspname = %s
                AND c.relname = %s
            """,
                (schema, table_name),
            )
            pk_rows = await cur.fetchall()

        result["primary_key"] = [row.get("column_name") for row in pk_rows]

        # Get indexes
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT
                    i.relname as index_name,
                    ix.indisunique as is_unique,
                    ix.indisprimary as is_primary,
                    array_agg(a.attname ORDER BY array_position(ix.indkey, a.attnum)) as columns
                FROM pg_index ix
                JOIN pg_class i ON i.oid = ix.indexrelid
                JOIN pg_class t ON t.oid = ix.indrelid
                JOIN pg_namespace n ON n.oid = t.relnamespace
                JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
                WHERE n.nspname = %s AND t.relname = %s
                GROUP BY i.relname, ix.indisunique, ix.indisprimary
            """,
                (schema, table_name),
            )
            index_rows = await cur.fetchall()

        indexes = []
        for row in index_rows:
            indexes.append(
                {
                    "name": row.get("index_name"),
                    "columns": row.get("columns", []),
                    "is_unique": row.get("is_unique", False),
                    "is_primary": row.get("is_primary", False),
                }
            )

        result["indexes"] = indexes

        # Get row count estimate
        async with conn.cursor() as cur:
            await cur.execute(f"SELECT COUNT(*) as count FROM {schema}.{table_name}")
            count_row = await cur.fetchone()
            result["row_count"] = count_row["count"] if count_row else 0

        return result

    except Exception as e:
        return {"status": "error", "error": str(e)}


async def get_table_stats(table: str) -> dict[str, Any]:
    """Get statistics for a table.

    Args:
        table: Table name (schema.table or just table).

    Returns:
        Table statistics.
    """
    conn = await connection_manager.ensure_connected()

    # Parse schema and table name
    if "." in table:
        schema, table_name = table.rsplit(".", 1)
    else:
        schema = "public"
        table_name = table

    # Check if schema is allowed
    if not _is_allowed_schema(schema):
        return {"status": "error", "error": f"Schema '{schema}' is not allowed"}

    try:
        # Get table size and row count
        async with conn.cursor() as cur:
            # Row count
            await cur.execute(f"SELECT COUNT(*) as count FROM {schema}.{table_name}")
            count_row = await cur.fetchone()
            row_count = count_row["count"] if count_row else 0

            # Table size using CockroachDB specific query
            await cur.execute(
                """
                SELECT
                    pg_size_pretty(pg_total_relation_size(%s::regclass)) as total_size,
                    pg_total_relation_size(%s::regclass) as total_bytes
            """,
                (f"{schema}.{table_name}", f"{schema}.{table_name}"),
            )
            size_row = await cur.fetchone()

        return {
            "schema": schema,
            "table": table_name,
            "full_name": f"{schema}.{table_name}",
            "row_count": row_count,
            "total_size": size_row.get("total_size") if size_row else None,
            "total_bytes": size_row.get("total_bytes") if size_row else None,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


async def get_foreign_keys(table: str) -> dict[str, Any]:
    """Get foreign key constraints for a table.

    Args:
        table: Table name (schema.table or just table).

    Returns:
        Foreign key information.
    """
    conn = await connection_manager.ensure_connected()

    # Parse schema and table name
    if "." in table:
        schema, table_name = table.rsplit(".", 1)
    else:
        schema = "public"
        table_name = table

    try:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT
                    tc.constraint_name,
                    kcu.column_name,
                    ccu.table_schema AS foreign_table_schema,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema = %s
                AND tc.table_name = %s
            """,
                (schema, table_name),
            )
            rows = await cur.fetchall()

        foreign_keys = []
        for row in rows:
            foreign_keys.append(
                {
                    "constraint_name": row.get("constraint_name"),
                    "column": row.get("column_name"),
                    "references_schema": row.get("foreign_table_schema"),
                    "references_table": row.get("foreign_table_name"),
                    "references_column": row.get("foreign_column_name"),
                }
            )

        return {
            "schema": schema,
            "table": table_name,
            "foreign_keys": foreign_keys,
            "count": len(foreign_keys),
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
