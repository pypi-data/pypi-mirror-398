"""Connection management for cockroachdb-mcp."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import psycopg
from psycopg import AsyncConnection
from psycopg.rows import dict_row

from .config import settings


@dataclass
class ConnectionState:
    """State of a CockroachDB connection."""

    connection: AsyncConnection[dict[str, Any]] | None = None
    connected_at: datetime | None = None
    cluster_id: str | None = None
    version: str | None = None
    database: str | None = None
    in_transaction: bool = False


@dataclass
class ConnectionManager:
    """Manages CockroachDB connections."""

    _state: ConnectionState = field(default_factory=ConnectionState)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    @property
    def connection(self) -> AsyncConnection[dict[str, Any]] | None:
        """Get the current connection."""
        return self._state.connection

    @property
    def is_connected(self) -> bool:
        """Check if connected."""
        return self._state.connection is not None and not self._state.connection.closed

    @property
    def current_database(self) -> str | None:
        """Get the current database name."""
        return self._state.database

    @property
    def in_transaction(self) -> bool:
        """Check if in an active transaction."""
        return self._state.in_transaction

    async def connect(self) -> dict[str, Any]:
        """Connect to CockroachDB cluster.

        Returns:
            Connection status and cluster info.
        """
        async with self._lock:
            if self._state.connection is not None and not self._state.connection.closed:
                return {
                    "status": "already_connected",
                    "cluster_id": self._state.cluster_id,
                    "version": self._state.version,
                    "database": self._state.database,
                    "connected_at": self._state.connected_at.isoformat()
                    if self._state.connected_at
                    else None,
                }

            # Build connection parameters
            conn_params: dict[str, Any] = {
                "host": settings.host,
                "port": settings.port,
                "user": settings.user,
                "dbname": settings.database,
                "row_factory": dict_row,
                "autocommit": True,
            }

            if settings.password:
                conn_params["password"] = settings.password

            # SSL configuration
            if settings.sslmode != "disable":
                conn_params["sslmode"] = settings.sslmode
                if settings.sslrootcert:
                    conn_params["sslrootcert"] = settings.sslrootcert

            # CockroachDB Cloud cluster option
            if settings.cluster:
                conn_params["options"] = f"--cluster={settings.cluster}"

            # Connect with timeout
            try:
                conn = await asyncio.wait_for(
                    psycopg.AsyncConnection.connect(**conn_params),
                    timeout=settings.timeout,
                )

                # Get cluster info
                async with conn.cursor() as cur:
                    await cur.execute("SELECT version()")
                    version_row = await cur.fetchone()
                    version = version_row["version"] if version_row else None

                    await cur.execute("SHOW CLUSTER SETTING cluster.organization")
                    org_row = await cur.fetchone()
                    cluster_id = (
                        org_row["cluster.organization"]
                        if org_row and org_row.get("cluster.organization")
                        else "local"
                    )

                self._state.connection = conn
                self._state.connected_at = datetime.now()
                self._state.cluster_id = cluster_id
                self._state.version = version
                self._state.database = settings.database
                self._state.in_transaction = False

                return {
                    "status": "connected",
                    "cluster_id": self._state.cluster_id,
                    "version": self._state.version,
                    "database": self._state.database,
                    "host": settings.host,
                    "port": settings.port,
                    "connected_at": self._state.connected_at.isoformat(),
                }
            except asyncio.TimeoutError as e:
                raise ConnectionError(
                    f"Connection to CockroachDB timed out after {settings.timeout}s"
                ) from e
            except Exception as e:
                raise ConnectionError(f"Failed to connect to CockroachDB: {e}") from e

    async def disconnect(self) -> dict[str, Any]:
        """Disconnect from CockroachDB cluster.

        Returns:
            Disconnection status.
        """
        async with self._lock:
            if self._state.connection is None:
                return {"status": "not_connected"}

            try:
                await self._state.connection.close()
            except Exception:
                pass  # Ignore errors on close

            database = self._state.database
            self._state = ConnectionState()

            return {
                "status": "disconnected",
                "database": database,
            }

    async def ensure_connected(self) -> AsyncConnection[dict[str, Any]]:
        """Ensure connection exists, connecting if needed.

        Returns:
            The database connection.

        Raises:
            ConnectionError: If not connected and auto-connect fails.
        """
        if self._state.connection is None or self._state.connection.closed:
            await self.connect()

        if self._state.connection is None:
            raise ConnectionError("Not connected to CockroachDB")

        return self._state.connection

    async def switch_database(self, database: str) -> dict[str, Any]:
        """Switch to a different database.

        Args:
            database: Database name to switch to.

        Returns:
            Switch status.
        """
        # Check if database is blocked
        if database in settings.blocked_databases_list:
            return {"status": "error", "error": f"Database '{database}' is blocked"}

        async with self._lock:
            if self._state.connection is not None:
                try:
                    await self._state.connection.close()
                except Exception:
                    pass

            # Reconnect with new database
            old_database = settings.database
            # Temporarily modify settings for reconnection
            # Note: This is a workaround; in production, use a new connection
            self._state = ConnectionState()

        # Create new connection to the target database
        conn_params: dict[str, Any] = {
            "host": settings.host,
            "port": settings.port,
            "user": settings.user,
            "dbname": database,
            "row_factory": dict_row,
            "autocommit": True,
        }

        if settings.password:
            conn_params["password"] = settings.password

        if settings.sslmode != "disable":
            conn_params["sslmode"] = settings.sslmode
            if settings.sslrootcert:
                conn_params["sslrootcert"] = settings.sslrootcert

        if settings.cluster:
            conn_params["options"] = f"--cluster={settings.cluster}"

        try:
            conn = await asyncio.wait_for(
                psycopg.AsyncConnection.connect(**conn_params),
                timeout=settings.timeout,
            )

            async with self._lock:
                self._state.connection = conn
                self._state.connected_at = datetime.now()
                self._state.database = database
                self._state.in_transaction = False

            return {
                "status": "switched",
                "previous_database": old_database,
                "current_database": database,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def begin_transaction(self) -> dict[str, Any]:
        """Begin a database transaction.

        Returns:
            Transaction status.
        """
        conn = await self.ensure_connected()

        if self._state.in_transaction:
            return {"status": "error", "error": "Transaction already in progress"}

        try:
            # Disable autocommit for transaction
            await conn.set_autocommit(False)
            self._state.in_transaction = True
            return {"status": "started", "message": "Transaction started"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def commit_transaction(self) -> dict[str, Any]:
        """Commit the current transaction.

        Returns:
            Commit status.
        """
        conn = await self.ensure_connected()

        if not self._state.in_transaction:
            return {"status": "error", "error": "No transaction in progress"}

        try:
            await conn.commit()
            await conn.set_autocommit(True)
            self._state.in_transaction = False
            return {"status": "committed", "message": "Transaction committed"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def rollback_transaction(self) -> dict[str, Any]:
        """Rollback the current transaction.

        Returns:
            Rollback status.
        """
        conn = await self.ensure_connected()

        if not self._state.in_transaction:
            return {"status": "error", "error": "No transaction in progress"}

        try:
            await conn.rollback()
            await conn.set_autocommit(True)
            self._state.in_transaction = False
            return {"status": "rolled_back", "message": "Transaction rolled back"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def execute_query(
        self,
        query: str,
        params: tuple[Any, ...] | None = None,
        max_rows: int | None = None,
    ) -> dict[str, Any]:
        """Execute a query and return results.

        Args:
            query: SQL query to execute.
            params: Query parameters.
            max_rows: Maximum rows to return.

        Returns:
            Query results.
        """
        conn = await self.ensure_connected()

        effective_max_rows = max_rows if max_rows is not None else settings.max_rows

        try:
            async with conn.cursor() as cur:
                if params:
                    await cur.execute(query, params)
                else:
                    await cur.execute(query)

                # Check if query returns results
                if cur.description is None:
                    # Non-SELECT query (INSERT, UPDATE, DELETE, etc.)
                    return {
                        "status": "success",
                        "rows_affected": cur.rowcount,
                        "message": f"{cur.rowcount} row(s) affected",
                    }

                # Fetch results with limit
                rows = await cur.fetchmany(effective_max_rows)
                total_fetched = len(rows)

                # Check if there are more rows
                has_more = False
                if total_fetched == effective_max_rows:
                    extra = await cur.fetchone()
                    has_more = extra is not None

                # Get column names
                columns = [desc.name for desc in cur.description]

                return {
                    "status": "success",
                    "columns": columns,
                    "rows": rows,
                    "row_count": total_fetched,
                    "has_more": has_more,
                    "max_rows": effective_max_rows,
                }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def get_connection_info(self) -> dict[str, Any]:
        """Get current connection information.

        Returns:
            Connection state information.
        """
        if not self.is_connected:
            return {"status": "not_connected"}

        return {
            "status": "connected",
            "cluster_id": self._state.cluster_id,
            "version": self._state.version,
            "database": self._state.database,
            "in_transaction": self._state.in_transaction,
            "connected_at": self._state.connected_at.isoformat()
            if self._state.connected_at
            else None,
        }


# Global connection manager instance
connection_manager = ConnectionManager()
