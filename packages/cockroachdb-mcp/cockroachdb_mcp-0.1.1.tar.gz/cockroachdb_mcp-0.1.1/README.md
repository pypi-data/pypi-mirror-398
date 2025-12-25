# cockroachdb-mcp

An MCP (Model Context Protocol) server for CockroachDB clusters. Enables AI assistants like Claude to query and interact with CockroachDB through natural language.

[![PyPI version](https://badge.fury.io/py/cockroachdb-mcp.svg)](https://badge.fury.io/py/cockroachdb-mcp)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

## Features

- **Natural Language Queries**: Ask Claude about your data in plain English
- **Schema Discovery**: Explore databases, tables, columns, and indexes
- **CRUD Operations**: Read, insert, update, and delete rows safely
- **Cluster Operations**: Monitor cluster health and node status
- **Multi-Region Support**: Query distributed data across regions
- **Data Export**: Export query results to JSON or CSV
- **Transaction Support**: Begin, commit, and rollback transactions
- **Knowledge Persistence**: Claude remembers what it learns about your cluster
- **Safety Controls**: Read-only mode, command blocking, row limits
- **Connection Watchdog**: Automatic recovery from hung connections
- **OAuth Integration**: Deploy as a Claude.ai Custom Connector with SSO

## Quick Start

### 1. Install

```bash
pip install cockroachdb-mcp
```

### 2. Configure Claude Desktop

Edit your Claude Desktop config file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "cockroachdb": {
      "command": "cockroachdb-mcp",
      "env": {
        "CRDB_HOST": "your-cluster.cockroachlabs.cloud",
        "CRDB_USER": "your-username",
        "CRDB_PASSWORD": "your-password",
        "CRDB_DATABASE": "your-database",
        "CRDB_CLUSTER": "your-cluster-id",
        "CRDB_READ_ONLY": "true"
      }
    }
  }
}
```

### 3. Restart Claude Desktop

Quit and reopen Claude Desktop. You'll see a hammer icon indicating tools are available.

### 4. Start Chatting

Ask Claude about your CockroachDB data:

> "What tables are available?"

> "Describe the users table"

> "Show me the top 10 orders by total amount"

> "What's the cluster health status?"

## Documentation

| Guide | Description |
|-------|-------------|
| [Installation](docs/installation.md) | Complete installation guide |
| [Configuration](docs/configuration.md) | All configuration options |
| [Tools Reference](docs/tools.md) | Detailed tool documentation |
| [Usage Examples](docs/examples.md) | Common usage patterns |
| [OAuth Setup](docs/oauth.md) | Claude.ai integration with SSO |

## Available Tools

### Connection & Cluster
| Tool | Description |
|------|-------------|
| `connect` | Connect to the cluster |
| `disconnect` | Close connections |
| `cluster_status` | Get cluster health |
| `list_nodes` | List cluster nodes |

### Schema Discovery
| Tool | Description |
|------|-------------|
| `list_databases` | List all databases |
| `list_tables` | List tables and views |
| `describe_table` | Get column information |

### Query Execution
| Tool | Description |
|------|-------------|
| `execute_query` | Run SELECT queries |
| `validate_query` | Check query safety |

### CRUD Operations
| Tool | Description |
|------|-------------|
| `read_rows` | Read rows by key or filter |
| `insert_row` | Insert a new row |
| `update_row` | Update existing row |
| `delete_row` | Delete row by key |

### Transactions
| Tool | Description |
|------|-------------|
| `begin_transaction` | Start transaction |
| `commit_transaction` | Commit changes |
| `rollback_transaction` | Rollback changes |

### Export & Knowledge
| Tool | Description |
|------|-------------|
| `export_to_json` | Export to JSON |
| `export_to_csv` | Export to CSV |
| `save_knowledge` | Save learned info |
| `get_all_knowledge` | Retrieve knowledge |

## Configuration

### Required Variables

| Variable | Description |
|----------|-------------|
| `CRDB_HOST` | CockroachDB host |
| `CRDB_USER` | Database username |
| `CRDB_DATABASE` | Database name |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CRDB_PORT` | `26257` | Database port |
| `CRDB_PASSWORD` | | Database password |
| `CRDB_CLUSTER` | | Cloud cluster ID |
| `CRDB_SSLMODE` | `require` | SSL mode |

### Safety Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `CRDB_READ_ONLY` | `false` | Block write operations |
| `CRDB_MAX_ROWS` | `1000` | Max rows per query |
| `CRDB_BLOCKED_COMMANDS` | `DROP,...` | Commands to block |

## Deployment Modes

### Local (Default)

```bash
cockroachdb-mcp
```

### HTTP/SSE Server

```bash
cockroachdb-mcp --http --host 0.0.0.0 --port 8080
```

### Streamable HTTP (Claude.ai)

```bash
cockroachdb-mcp --streamable-http --host 0.0.0.0 --port 8080
```

## Development

```bash
# Clone repository
git clone https://github.com/bpamiri/cockroachdb-mcp.git
cd cockroachdb-mcp

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint and format
ruff check .
ruff format .

# Type check
mypy src/
```

## Security

- Passwords and credentials are never logged
- Configurable command blocklist
- Optional read-only mode
- Result size limits
- Query validation
- SSL/TLS encryption support

## License

Apache-2.0. See [LICENSE](LICENSE) for details.

## Links

- [PyPI Package](https://pypi.org/project/cockroachdb-mcp/)
- [GitHub Repository](https://github.com/bpamiri/cockroachdb-mcp)
- [Issue Tracker](https://github.com/bpamiri/cockroachdb-mcp/issues)
- [CockroachDB Documentation](https://www.cockroachlabs.com/docs/)
- [MCP Documentation](https://modelcontextprotocol.io/)
