"""Cluster operations for cockroachdb-mcp."""

from __future__ import annotations

from typing import Any

from ..connection import connection_manager


async def cluster_health() -> dict[str, Any]:
    """Get the health status of the CockroachDB cluster.

    Returns:
        Cluster health information.
    """
    conn = await connection_manager.ensure_connected()

    try:
        result: dict[str, Any] = {"status": "healthy"}

        async with conn.cursor() as cur:
            # Get cluster settings
            await cur.execute("SHOW CLUSTER SETTING cluster.organization")
            org_row = await cur.fetchone()
            result["organization"] = org_row.get("cluster.organization") if org_row else None

            # Get version
            await cur.execute("SELECT version()")
            version_row = await cur.fetchone()
            result["version"] = version_row.get("version") if version_row else None

            # Get node count
            await cur.execute("SELECT count(*) as node_count FROM crdb_internal.gossip_nodes")
            node_row = await cur.fetchone()
            result["node_count"] = node_row.get("node_count") if node_row else 0

            # Get live node count
            await cur.execute("""
                SELECT count(*) as live_nodes
                FROM crdb_internal.gossip_nodes
                WHERE is_live = true
            """)
            live_row = await cur.fetchone()
            result["live_nodes"] = live_row.get("live_nodes") if live_row else 0

            # Check if cluster is healthy
            if result["live_nodes"] < result["node_count"]:
                result["status"] = "degraded"
                result["message"] = (
                    f"{result['node_count'] - result['live_nodes']} node(s) are not live"
                )

        return result
    except Exception as e:
        return {"status": "error", "error": str(e)}


async def list_nodes() -> dict[str, Any]:
    """List all nodes in the CockroachDB cluster.

    Returns:
        List of cluster nodes with their status.
    """
    conn = await connection_manager.ensure_connected()

    try:
        async with conn.cursor() as cur:
            await cur.execute("""
                SELECT
                    node_id,
                    address,
                    locality,
                    is_live,
                    CASE WHEN is_live THEN 'live' ELSE 'dead' END as status
                FROM crdb_internal.gossip_nodes
                ORDER BY node_id
            """)
            rows = await cur.fetchall()

        nodes = []
        for row in rows:
            nodes.append(
                {
                    "node_id": row.get("node_id"),
                    "address": row.get("address"),
                    "locality": row.get("locality"),
                    "is_live": row.get("is_live"),
                    "status": row.get("status"),
                }
            )

        live_count = sum(1 for n in nodes if n["is_live"])

        return {
            "nodes": nodes,
            "total_count": len(nodes),
            "live_count": live_count,
            "dead_count": len(nodes) - live_count,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


async def node_status(node_id: int | None = None) -> dict[str, Any]:
    """Get detailed status for a node or all nodes.

    Args:
        node_id: Specific node ID (optional).

    Returns:
        Node status information.
    """
    conn = await connection_manager.ensure_connected()

    try:
        query = """
            SELECT
                node_id,
                address,
                build_tag,
                started_at,
                updated_at,
                locality,
                is_live,
                ranges,
                leases
            FROM crdb_internal.gossip_liveness
        """

        if node_id is not None:
            query += f" WHERE node_id = {node_id}"

        query += " ORDER BY node_id"

        async with conn.cursor() as cur:
            await cur.execute(query)
            rows = await cur.fetchall()

        if node_id is not None and not rows:
            return {"status": "error", "error": f"Node {node_id} not found"}

        nodes = []
        for row in rows:
            nodes.append(
                {
                    "node_id": row.get("node_id"),
                    "address": row.get("address"),
                    "build_tag": row.get("build_tag"),
                    "started_at": str(row.get("started_at")) if row.get("started_at") else None,
                    "updated_at": str(row.get("updated_at")) if row.get("updated_at") else None,
                    "locality": row.get("locality"),
                    "is_live": row.get("is_live"),
                    "ranges": row.get("ranges"),
                    "leases": row.get("leases"),
                }
            )

        if node_id is not None:
            return {"node": nodes[0] if nodes else None}

        return {"nodes": nodes, "count": len(nodes)}
    except Exception as e:
        return {"status": "error", "error": str(e)}


async def show_regions() -> dict[str, Any]:
    """Show database regions for multi-region clusters.

    Returns:
        Region information.
    """
    conn = await connection_manager.ensure_connected()

    try:
        async with conn.cursor() as cur:
            # Get database regions
            await cur.execute("""
                SELECT
                    database_name,
                    primary_region,
                    secondary_region,
                    regions,
                    survival_goal
                FROM crdb_internal.databases
                WHERE database_name = current_database()
            """)
            db_row = await cur.fetchone()

            if not db_row:
                return {
                    "status": "success",
                    "database": connection_manager.current_database,
                    "is_multi_region": False,
                    "message": "Database is not configured for multi-region",
                }

            # Get all regions in the cluster
            await cur.execute("SHOW REGIONS")
            region_rows = await cur.fetchall()

        regions = [row.get("region") for row in region_rows if row.get("region")]

        return {
            "status": "success",
            "database": db_row.get("database_name"),
            "primary_region": db_row.get("primary_region"),
            "secondary_region": db_row.get("secondary_region"),
            "regions": db_row.get("regions"),
            "survival_goal": db_row.get("survival_goal"),
            "cluster_regions": regions,
            "is_multi_region": bool(db_row.get("primary_region")),
        }
    except Exception as e:
        # Multi-region may not be enabled
        if "unknown function" in str(e).lower() or "regions" in str(e).lower():
            return {
                "status": "success",
                "is_multi_region": False,
                "message": "Multi-region is not enabled for this cluster",
            }
        return {"status": "error", "error": str(e)}


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
    conn = await connection_manager.ensure_connected()

    try:
        query = """
            SELECT
                job_id,
                job_type,
                status,
                description,
                created,
                started,
                finished,
                fraction_completed,
                error
            FROM crdb_internal.jobs
            WHERE 1=1
        """

        if job_type:
            query += f" AND job_type = '{job_type.upper()}'"
        if status:
            query += f" AND status = '{status.lower()}'"

        query += f" ORDER BY created DESC LIMIT {limit}"

        async with conn.cursor() as cur:
            await cur.execute(query)
            rows = await cur.fetchall()

        jobs = []
        for row in rows:
            jobs.append(
                {
                    "job_id": str(row.get("job_id")),
                    "job_type": row.get("job_type"),
                    "status": row.get("status"),
                    "description": row.get("description"),
                    "created": str(row.get("created")) if row.get("created") else None,
                    "started": str(row.get("started")) if row.get("started") else None,
                    "finished": str(row.get("finished")) if row.get("finished") else None,
                    "progress": row.get("fraction_completed"),
                    "error": row.get("error"),
                }
            )

        return {"jobs": jobs, "count": len(jobs)}
    except Exception as e:
        return {"status": "error", "error": str(e)}


async def show_sessions(active_only: bool = True) -> dict[str, Any]:
    """Show active sessions in the cluster.

    Args:
        active_only: Only show active sessions.

    Returns:
        List of sessions.
    """
    conn = await connection_manager.ensure_connected()

    try:
        query = """
            SELECT
                session_id,
                node_id,
                user_name,
                client_address,
                application_name,
                active_queries,
                start
            FROM crdb_internal.cluster_sessions
        """

        if active_only:
            query += " WHERE active_queries != '{}'"

        query += " ORDER BY start DESC"

        async with conn.cursor() as cur:
            await cur.execute(query)
            rows = await cur.fetchall()

        sessions = []
        for row in rows:
            sessions.append(
                {
                    "session_id": row.get("session_id"),
                    "node_id": row.get("node_id"),
                    "user": row.get("user_name"),
                    "client_address": row.get("client_address"),
                    "application": row.get("application_name"),
                    "active_queries": row.get("active_queries"),
                    "started": str(row.get("start")) if row.get("start") else None,
                }
            )

        return {"sessions": sessions, "count": len(sessions)}
    except Exception as e:
        return {"status": "error", "error": str(e)}


async def show_statements(limit: int = 20) -> dict[str, Any]:
    """Show active statements in the cluster.

    Args:
        limit: Maximum statements to return.

    Returns:
        List of active statements.
    """
    conn = await connection_manager.ensure_connected()

    try:
        async with conn.cursor() as cur:
            await cur.execute(f"""
                SELECT
                    query_id,
                    node_id,
                    user_name,
                    query,
                    start,
                    phase,
                    application_name
                FROM crdb_internal.cluster_queries
                ORDER BY start DESC
                LIMIT {limit}
            """)
            rows = await cur.fetchall()

        statements = []
        for row in rows:
            statements.append(
                {
                    "query_id": row.get("query_id"),
                    "node_id": row.get("node_id"),
                    "user": row.get("user_name"),
                    "query": row.get("query"),
                    "started": str(row.get("start")) if row.get("start") else None,
                    "phase": row.get("phase"),
                    "application": row.get("application_name"),
                }
            )

        return {"statements": statements, "count": len(statements)}
    except Exception as e:
        return {"status": "error", "error": str(e)}


async def cancel_query(query_id: str) -> dict[str, Any]:
    """Cancel a running query.

    Args:
        query_id: The query ID to cancel.

    Returns:
        Cancellation result.
    """
    conn = await connection_manager.ensure_connected()

    try:
        async with conn.cursor() as cur:
            await cur.execute(f"CANCEL QUERY '{query_id}'")

        return {
            "status": "success",
            "query_id": query_id,
            "message": "Query cancelled",
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


async def show_ranges(table: str | None = None, limit: int = 50) -> dict[str, Any]:
    """Show range distribution in the cluster.

    Args:
        table: Optional table to filter ranges.
        limit: Maximum ranges to return.

    Returns:
        Range distribution information.
    """
    conn = await connection_manager.ensure_connected()

    try:
        if table:
            # Parse table name (schema ignored - CockroachDB ranges use just table_name)
            if "." in table:
                _schema, table_name = table.rsplit(".", 1)
            else:
                table_name = table

            query = f"""
                SELECT
                    range_id,
                    start_pretty,
                    end_pretty,
                    lease_holder,
                    replicas,
                    range_size_mb
                FROM crdb_internal.ranges_no_leases
                WHERE table_name = '{table_name}'
                LIMIT {limit}
            """
        else:
            query = f"""
                SELECT
                    range_id,
                    database_name,
                    table_name,
                    start_pretty,
                    end_pretty,
                    lease_holder,
                    replicas,
                    range_size_mb
                FROM crdb_internal.ranges_no_leases
                LIMIT {limit}
            """

        async with conn.cursor() as cur:
            await cur.execute(query)
            rows = await cur.fetchall()

        ranges = []
        for row in rows:
            range_info: dict[str, Any] = {
                "range_id": row.get("range_id"),
                "start": row.get("start_pretty"),
                "end": row.get("end_pretty"),
                "lease_holder": row.get("lease_holder"),
                "replicas": row.get("replicas"),
                "size_mb": row.get("range_size_mb"),
            }
            if not table:
                range_info["database"] = row.get("database_name")
                range_info["table"] = row.get("table_name")
            ranges.append(range_info)

        return {"ranges": ranges, "count": len(ranges), "table_filter": table}
    except Exception as e:
        return {"status": "error", "error": str(e)}


async def show_zone_config(table: str | None = None) -> dict[str, Any]:
    """Show zone configurations.

    Args:
        table: Optional table to get zone config for.

    Returns:
        Zone configuration.
    """
    conn = await connection_manager.ensure_connected()

    try:
        if table:
            query = f"SHOW ZONE CONFIGURATION FOR TABLE {table}"
        else:
            query = "SHOW ZONE CONFIGURATIONS"

        async with conn.cursor() as cur:
            await cur.execute(query)
            rows = await cur.fetchall()

        configs = []
        for row in rows:
            configs.append(
                {
                    "target": row.get("target"),
                    "raw_config_sql": row.get("raw_config_sql"),
                }
            )

        return {"zone_configs": configs, "count": len(configs), "table_filter": table}
    except Exception as e:
        return {"status": "error", "error": str(e)}
