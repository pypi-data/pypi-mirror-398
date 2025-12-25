# cockroachdb-mcp Product Requirements Document

## Overview

**cockroachdb-mcp** is an MCP (Model Context Protocol) server that enables AI assistants like Claude to interact with CockroachDB clusters through natural language. Users can query, analyze, and manage distributed SQL data without writing complex queries.

## Vision

Provide seamless natural language access to CockroachDB's distributed SQL capabilities, allowing users to leverage the power of a globally distributed database through conversational AI.

## Target Users

- DevOps engineers managing CockroachDB clusters
- Data analysts querying distributed data
- Application developers prototyping queries
- DBAs monitoring cluster health

---

## Core Features

### 1. Connection Management

| Feature | Description | Priority |
|---------|-------------|----------|
| `connect` | Connect to CockroachDB cluster | P0 |
| `disconnect` | Close connections | P0 |
| `list_connections` | Show active connections | P1 |
| `cluster_status` | Get cluster health and node status | P0 |
| `node_status` | Get individual node details | P1 |

**Configuration:**
- `CRDB_HOST` - CockroachDB host (required)
- `CRDB_PORT` - Port (default: 26257)
- `CRDB_USER` - Username (required)
- `CRDB_PASSWORD` - Password
- `CRDB_DATABASE` - Database name (required)
- `CRDB_SSLMODE` - SSL mode (disable, require, verify-ca, verify-full)
- `CRDB_SSLROOTCERT` - Path to CA certificate
- `CRDB_CLUSTER` - CockroachDB Cloud cluster ID (for serverless)
- `CRDB_TIMEOUT` - Connection timeout

### 2. Query Execution

| Feature | Description | Priority |
|---------|-------------|----------|
| `execute_query` | Execute SELECT queries | P0 |
| `validate_query` | Validate query safety | P0 |
| `explain_query` | Get query execution plan | P1 |
| `explain_analyze` | Get query plan with execution stats | P1 |

**Safety Controls:**
- `CRDB_READ_ONLY` - Disable write operations
- `CRDB_MAX_ROWS` - Maximum rows per query (default: 1000)
- `CRDB_QUERY_TIMEOUT` - Query timeout seconds
- `CRDB_BLOCKED_COMMANDS` - Commands to block

### 3. Schema Discovery

| Feature | Description | Priority |
|---------|-------------|----------|
| `list_databases` | List all databases | P0 |
| `list_tables` | List tables and views | P0 |
| `describe_table` | Get column information | P0 |
| `list_indexes` | List indexes on a table | P1 |
| `get_constraints` | Get table constraints | P1 |
| `list_schemas` | List schemas in database | P1 |

### 4. CRUD Operations

| Feature | Description | Priority |
|---------|-------------|----------|
| `read_rows` | Read rows by key or filter | P0 |
| `insert_row` | Insert a new row | P1 |
| `update_row` | Update existing row | P1 |
| `delete_row` | Delete row by key | P1 |
| `upsert_row` | Insert or update row | P1 |

### 5. Data Export

| Feature | Description | Priority |
|---------|-------------|----------|
| `export_to_json` | Export query results to JSON | P1 |
| `export_to_csv` | Export query results to CSV | P1 |

### 6. Database Management

| Feature | Description | Priority |
|---------|-------------|----------|
| `switch_database` | Change database context | P0 |
| `get_database_info` | Get database statistics | P1 |
| `list_users` | List database users | P2 |
| `list_roles` | List database roles | P2 |

### 7. Transaction Management

| Feature | Description | Priority |
|---------|-------------|----------|
| `begin_transaction` | Start a transaction | P1 |
| `commit_transaction` | Commit transaction | P1 |
| `rollback_transaction` | Rollback transaction | P1 |
| `get_transaction_status` | Check transaction state | P1 |
| `savepoint` | Create savepoint | P2 |

---

## CockroachDB-Specific Features

### 8. Cluster Operations

| Feature | Description | Priority |
|---------|-------------|----------|
| `cluster_health` | Overall cluster health | P0 |
| `list_nodes` | List all cluster nodes | P1 |
| `node_details` | Get node metrics | P1 |
| `list_ranges` | List range distribution | P2 |
| `show_zones` | Show zone configurations | P2 |

### 9. Distributed Features

| Feature | Description | Priority |
|---------|-------------|----------|
| `show_regions` | Show database regions | P1 |
| `show_locality` | Show node localities | P1 |
| `show_ranges` | Show range locations | P2 |
| `show_partitions` | Show table partitions | P2 |

### 10. Performance Tools

| Feature | Description | Priority |
|---------|-------------|----------|
| `show_statements` | Active statements | P1 |
| `show_sessions` | Active sessions | P1 |
| `show_jobs` | Background jobs | P1 |
| `cancel_query` | Cancel running query | P2 |

---

## Infrastructure Features

### 11. Knowledge Persistence

Store learned information about the CockroachDB cluster across sessions.

| Feature | Description | Priority |
|---------|-------------|----------|
| `save_knowledge` | Save discovered information | P0 |
| `list_knowledge` | List saved topics | P0 |
| `get_all_knowledge` | Retrieve all knowledge | P0 |
| `get_knowledge_topic` | Get specific topic | P1 |
| `search_knowledge` | Search saved knowledge | P1 |
| `delete_knowledge` | Remove a topic | P2 |

**What to save:**
- Table purposes and relationships
- Column meanings and data types
- Common query patterns
- Cluster topology notes
- Performance observations

**Configuration:**
- `CRDB_KNOWLEDGE_PATH` - Custom knowledge file path (default: `~/.cockroachdb-mcp/knowledge.md`)

### 12. Connection Watchdog

Automatic recovery from hung or stale connections.

| Feature | Description |
|---------|-------------|
| Health monitoring | Periodic connection pings |
| Auto-reconnection | Reconnect on failure |
| Timeout detection | Detect hung queries |

**Configuration:**
- `CRDB_WATCHDOG_ENABLED` - Enable watchdog (default: true)
- `CRDB_WATCHDOG_INTERVAL` - Check interval seconds (default: 30)
- `CRDB_WATCHDOG_TIMEOUT` - Query timeout seconds (default: 60)

### 13. Audit Logging

Track all operations for security and debugging.

**Configuration:**
- `CRDB_AUDIT_ENABLED` - Enable audit logging
- `CRDB_AUDIT_PATH` - Audit log file path
- `CRDB_AUDIT_LEVEL` - Logging level

---

## Deployment Modes

### 14. Local Mode (stdio)

Default mode for Claude Desktop integration.

```bash
cockroachdb-mcp
```

### 15. HTTP/SSE Mode

Centralized server for multiple users.

```bash
cockroachdb-mcp --http --host 0.0.0.0 --port 8080
```

**Configuration:**
- `CRDB_HTTP_HOST` - HTTP server host
- `CRDB_HTTP_PORT` - HTTP server port
- `CRDB_HTTP_CORS_ORIGINS` - CORS allowed origins

### 16. Streamable HTTP Mode (Claude.ai)

For Claude.ai Custom Connector integration with OAuth.

```bash
cockroachdb-mcp --streamable-http --host 0.0.0.0 --port 8080
```

---

## OAuth Integration

### 17. OAuth 2.0 Support

Full OAuth authentication for Claude.ai integration.

| Feature | Description |
|---------|-------------|
| Dynamic Client Registration | RFC 7591 compliant |
| Authorization Code Flow | With PKCE support |
| Token Refresh | Automatic token renewal |
| Token Revocation | Secure logout |

**Supported Identity Providers:**
- Cisco Duo
- Auth0
- Azure AD / Entra ID
- Okta
- Generic OIDC

**Configuration:**
- `CRDB_AUTH_ENABLED` - Enable OAuth
- `CRDB_AUTH_ISSUER_URL` - OAuth issuer URL
- `CRDB_IDP_PROVIDER` - IdP type (duo, auth0, oidc)
- `CRDB_IDP_DISCOVERY_URL` - OIDC discovery URL
- `CRDB_IDP_CLIENT_ID` - IdP client ID
- `CRDB_IDP_CLIENT_SECRET` - IdP client secret
- `CRDB_IDP_SCOPES` - OAuth scopes
- `CRDB_TOKEN_EXPIRY_SECONDS` - Access token lifetime
- `CRDB_REFRESH_TOKEN_EXPIRY_SECONDS` - Refresh token lifetime

---

## MCP Resources

### 18. Built-in Resources

| Resource | Description |
|----------|-------------|
| `cockroachdb://knowledge` | All saved knowledge |
| `cockroachdb://syntax_help` | SQL syntax reference |
| `cockroachdb://query_examples` | Example queries |

---

## Safety & Security

### 19. Safety Controls

| Feature | Description | Default |
|---------|-------------|---------|
| Read-only mode | Block all write operations | false |
| Result limits | Cap query results | 1000 |
| Database blocklist | Hide sensitive databases | [] |
| Schema restrictions | Limit to specific schemas | [] |
| Query validation | Validate before execution | true |
| Command blocklist | Block dangerous commands | DROP, TRUNCATE... |

**Default blocked commands:**
- `DROP`, `TRUNCATE`, `ALTER`
- `GRANT`, `REVOKE`
- `CREATE USER`, `DROP USER`

### 20. Security Features

- SSL/TLS encryption
- Certificate authentication
- Credentials never logged
- Parameterized queries (SQL injection prevention)
- CockroachDB Cloud API key support

---

## Technical Specifications

### Dependencies

- `psycopg` or `asyncpg` - PostgreSQL driver (CockroachDB is PG-compatible)
- `mcp` - Model Context Protocol SDK
- `pydantic-settings` - Configuration management
- `httpx` - HTTP client for OAuth
- `uvicorn` - ASGI server

### Python Version

- Python 3.10+

### Project Structure

```
src/cockroachdb_mcp/
├── __init__.py
├── server.py              # FastMCP server entry point
├── connection.py          # Connection management
├── config.py              # Pydantic settings
├── tools/
│   ├── __init__.py
│   ├── query.py           # Query execution
│   ├── tables.py          # Schema discovery
│   ├── crud.py            # CRUD operations
│   ├── databases.py       # Database management
│   ├── transaction.py     # Transaction management
│   ├── cluster.py         # Cluster operations
│   ├── export.py          # Data export
│   └── knowledge.py       # Knowledge persistence
├── auth/
│   ├── __init__.py
│   ├── provider.py        # OAuth provider
│   ├── storage.py         # Token storage
│   ├── callback.py        # OAuth callback handler
│   └── idp/
│       ├── __init__.py
│       ├── base.py        # Base IdP adapter
│       ├── duo.py         # Cisco Duo
│       ├── auth0.py       # Auth0
│       └── oidc.py        # Generic OIDC
├── resources/
│   ├── __init__.py
│   ├── knowledge.py       # Knowledge resource
│   ├── syntax_help.py     # SQL reference
│   └── examples.py        # Example queries
└── utils/
    ├── __init__.py
    ├── safety.py          # Query validation
    ├── watchdog.py        # Connection watchdog
    ├── knowledge.py       # Knowledge file manager
    └── audit.py           # Audit logging
```

---

## Milestones

### v0.1.0 - Foundation
- [ ] Connection management
- [ ] Basic query execution
- [ ] Table listing and description
- [ ] Configuration with pydantic-settings
- [ ] CLI entry point

### v0.2.0 - Core Features
- [ ] Full query capabilities
- [ ] CRUD operations
- [ ] Database switching
- [ ] Data export
- [ ] Safety controls

### v0.3.0 - Knowledge & Resources
- [ ] Knowledge persistence
- [ ] MCP resources
- [ ] Query examples
- [ ] Syntax help

### v0.4.0 - Infrastructure
- [ ] Connection watchdog
- [ ] Audit logging
- [ ] HTTP/SSE mode
- [ ] Transaction support

### v0.5.0 - CockroachDB Features
- [ ] Cluster operations
- [ ] Node status
- [ ] Distributed query info
- [ ] Performance tools

### v0.6.0 - OAuth & Claude.ai
- [ ] Streamable HTTP mode
- [ ] OAuth provider
- [ ] IdP adapters (Duo, Auth0, OIDC)
- [ ] Claude.ai integration

### v1.0.0 - Production Ready
- [ ] Comprehensive documentation
- [ ] Full test coverage
- [ ] Performance optimization
- [ ] Security audit

---

## Success Metrics

- Query response time < 2s for typical queries
- 99% uptime for HTTP deployments
- Zero credential leaks in logs
- Full feature parity with pymssql-mcp OAuth

---

## References

- [pymssql-mcp](https://github.com/bpamiri/pymssql-mcp) - Reference implementation
- [u2-mcp](https://github.com/bpamiri/u2-mcp) - Reference implementation
- [CockroachDB Documentation](https://www.cockroachlabs.com/docs/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
