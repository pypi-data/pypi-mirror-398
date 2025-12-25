"""Configuration management for cockroachdb-mcp."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """CockroachDB MCP server settings."""

    model_config = SettingsConfigDict(
        env_prefix="CRDB_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Connection settings
    host: str = Field(default="localhost", description="CockroachDB host")
    port: int = Field(default=26257, description="CockroachDB port")
    user: str = Field(default="root", description="Database username")
    password: str | None = Field(default=None, description="Database password")
    database: str = Field(default="defaultdb", description="Database name")
    sslmode: str = Field(default="require", description="SSL mode")
    sslrootcert: str | None = Field(default=None, description="Path to CA certificate")
    cluster: str | None = Field(default=None, description="CockroachDB Cloud cluster ID")
    timeout: int = Field(default=30, description="Connection timeout in seconds")

    # Safety settings
    read_only: bool = Field(default=False, description="Disable write operations")
    max_rows: int = Field(default=1000, description="Maximum rows per query")
    query_timeout: int = Field(default=60, description="Query timeout in seconds")
    blocked_commands: str = Field(
        default="DROP,TRUNCATE,ALTER,GRANT,REVOKE,CREATE USER,DROP USER",
        description="Comma-separated blocked commands",
    )
    allowed_schemas: str | None = Field(default=None, description="Comma-separated allowed schemas")
    blocked_databases: str = Field(default="", description="Comma-separated blocked databases")

    # Knowledge persistence
    knowledge_path: str = Field(
        default="~/.cockroachdb-mcp/knowledge.md",
        description="Path to knowledge file",
    )

    # Watchdog settings
    watchdog_enabled: bool = Field(default=True, description="Enable connection watchdog")
    watchdog_interval: int = Field(default=30, description="Watchdog check interval (seconds)")
    watchdog_timeout: int = Field(default=60, description="Query timeout (seconds)")

    # Audit settings
    audit_enabled: bool = Field(default=False, description="Enable audit logging")
    audit_path: str | None = Field(default=None, description="Audit log file path")

    # HTTP server settings
    http_host: str = Field(default="0.0.0.0", description="HTTP server host")
    http_port: int = Field(default=8080, description="HTTP server port")
    http_cors_origins: str = Field(default="*", description="CORS allowed origins")

    # OAuth settings
    auth_enabled: bool = Field(default=False, description="Enable OAuth authentication")
    auth_issuer_url: str | None = Field(default=None, description="OAuth issuer URL")
    idp_provider: str | None = Field(default=None, description="IdP type: duo, auth0, oidc")
    idp_discovery_url: str | None = Field(default=None, description="OIDC discovery URL")
    idp_client_id: str | None = Field(default=None, description="IdP client ID")
    idp_client_secret: str | None = Field(default=None, description="IdP client secret")
    idp_scopes: str = Field(
        default="openid profile email groups",
        description="OAuth scopes to request",
    )
    token_expiry_seconds: int = Field(default=3600, description="Access token lifetime")
    refresh_token_expiry_seconds: int = Field(default=2592000, description="Refresh token lifetime")

    @property
    def blocked_commands_list(self) -> list[str]:
        """Get blocked commands as a list."""
        return [c.strip().upper() for c in self.blocked_commands.split(",") if c.strip()]

    @property
    def allowed_schemas_list(self) -> list[str] | None:
        """Get allowed schemas as a list."""
        if not self.allowed_schemas:
            return None
        return [s.strip() for s in self.allowed_schemas.split(",") if s.strip()]

    @property
    def blocked_databases_list(self) -> list[str]:
        """Get blocked databases as a list."""
        return [d.strip() for d in self.blocked_databases.split(",") if d.strip()]

    @property
    def knowledge_file_path(self) -> Path:
        """Get expanded knowledge file path."""
        return Path(self.knowledge_path).expanduser()

    @property
    def cors_origins_list(self) -> list[str]:
        """Get CORS origins as a list."""
        if self.http_cors_origins == "*":
            return ["*"]
        return [o.strip() for o in self.http_cors_origins.split(",") if o.strip()]

    @property
    def connection_string(self) -> str:
        """Build PostgreSQL-compatible connection string."""
        parts = [f"host={self.host}", f"port={self.port}", f"user={self.user}"]
        if self.password:
            parts.append(f"password={self.password}")
        parts.append(f"dbname={self.database}")
        parts.append(f"sslmode={self.sslmode}")
        if self.sslrootcert:
            parts.append(f"sslrootcert={self.sslrootcert}")
        if self.cluster:
            parts.append(f"options=--cluster={self.cluster}")
        return " ".join(parts)


# Global settings instance
settings = Settings()
