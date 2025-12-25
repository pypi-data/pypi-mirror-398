"""Configuration management for elasticsearch-mcp."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Elasticsearch MCP server settings."""

    model_config = SettingsConfigDict(
        env_prefix="ES_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Connection settings
    host: str = Field(default="http://localhost:9200", description="Elasticsearch host URL")
    api_key: str | None = Field(default=None, description="API key for authentication")
    username: str | None = Field(default=None, description="Username for basic auth")
    password: str | None = Field(default=None, description="Password for basic auth")
    cloud_id: str | None = Field(default=None, description="Elastic Cloud ID")
    ca_certs: str | None = Field(default=None, description="Path to CA certificates")
    verify_certs: bool = Field(default=True, description="Verify SSL certificates")
    timeout: int = Field(default=30, description="Connection timeout in seconds")

    # Safety settings
    read_only: bool = Field(default=False, description="Disable write operations")
    max_results: int = Field(default=1000, description="Maximum results per query")
    blocked_indices: str = Field(
        default=".security*,.kibana*,.apm*,.monitoring*",
        description="Comma-separated blocked index patterns",
    )

    # Knowledge persistence
    knowledge_path: str = Field(
        default="~/.elasticsearch-mcp/knowledge.md",
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
    def blocked_indices_list(self) -> list[str]:
        """Get blocked indices as a list."""
        return [i.strip() for i in self.blocked_indices.split(",") if i.strip()]

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


# Global settings instance
settings = Settings()
