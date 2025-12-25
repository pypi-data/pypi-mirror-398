"""
API-specific configuration.

This module contains settings specific to the Control Plane API server.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator, model_validator, AliasChoices
from typing import List, Optional, Dict, Any
import secrets
import os
from control_plane_api.version import get_sdk_version


class APIConfig(BaseSettings):
    """Configuration for Control Plane API server."""

    # ==================== API Server Settings ====================

    api_host: str = Field(
        default="0.0.0.0",
        description="API server host",
    )

    api_port: int = Field(
        default=8000,
        description="API server port",
    )

    api_workers: int = Field(
        default=4,
        description="Number of API worker processes",
    )

    api_title: str = Field(
        default="Agent Control Plane API",
        description="API title for documentation",
    )

    api_version: str = Field(
        default_factory=get_sdk_version,
        description="API version (dynamically read from package metadata)",
    )
    
    api_description: str = Field(
        default="Multi-tenant agent orchestration with Temporal workflows",
        description="API description for documentation",
    )
    
    # ==================== Environment ====================
    
    environment: str = Field(
        default="development",
        description="Environment (development, staging, production)",
    )
    
    debug: bool = Field(
        default=False,
        description="Debug mode",
    )
    
    @validator("debug", pre=True)
    def set_debug_from_env(cls, v, values):
        """Set debug based on environment if not explicitly set."""
        if v is None:
            env = values.get("environment", "development")
            return env == "development"
        return v
    
    # ==================== Database Settings ====================

    database_url: Optional[str] = Field(
        default=None,
        description="PostgreSQL database URL",
        validation_alias=AliasChoices("DATABASE_URL", "database_url"),
    )

    supabase_url: Optional[str] = Field(
        default=None,
        description="Supabase project URL",
        validation_alias=AliasChoices("SUPABASE_URL", "supabase_url"),
    )

    supabase_service_key: Optional[str] = Field(
        default=None,
        description="Supabase service role key",
        validation_alias=AliasChoices("SUPABASE_SERVICE_KEY", "supabase_service_key"),
    )

    supabase_anon_key: Optional[str] = Field(
        default=None,
        description="Supabase anonymous key",
        validation_alias=AliasChoices("SUPABASE_ANON_KEY", "supabase_anon_key"),
    )
    
    database_pool_size: int = Field(
        default=20,
        description="Database connection pool size",
    )
    
    database_max_overflow: int = Field(
        default=40,
        description="Maximum overflow for database pool",
    )
    
    database_pool_timeout: float = Field(
        default=30.0,
        description="Database pool timeout in seconds",
    )
    
    @model_validator(mode='after')
    def validate_database_config(self):
        """Ensure we have either DATABASE_URL or Supabase configuration."""
        # Always try to set database_url from Supabase env vars if not already set
        if not self.database_url:
            supabase_db_url = (
                os.environ.get("SUPABASE_POSTGRES_URL") or
                os.environ.get("SUPABASE_POSTGRES_PRISMA_URL") or
                os.environ.get("SUPABASE_DB_URL")
            )
            if supabase_db_url:
                # Fix URL format for SQLAlchemy 2.0+
                if supabase_db_url.startswith("postgres://"):
                    supabase_db_url = supabase_db_url.replace("postgres://", "postgresql://", 1)
                # Remove invalid Supabase pooler parameters that SQLAlchemy doesn't understand
                supabase_db_url = supabase_db_url.replace("&supa=base-pooler.x", "")
                self.database_url = supabase_db_url
            elif not (self.supabase_url and self.supabase_service_key) and self.environment != "development":
                raise ValueError(
                    "Either DATABASE_URL or Supabase configuration (SUPABASE_URL and SUPABASE_SERVICE_KEY) must be provided"
                )

        # Fix postgres:// to postgresql:// if needed and remove invalid params
        if self.database_url:
            if self.database_url.startswith("postgres://"):
                self.database_url = self.database_url.replace("postgres://", "postgresql://", 1)
            # Remove invalid Supabase pooler parameters from DATABASE_URL
            self.database_url = self.database_url.replace("&supa=base-pooler.x", "")

        return self
    
    # ==================== Redis Settings ====================

    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
        validation_alias=AliasChoices("REDIS_URL", "redis_url"),
    )
    
    redis_host: Optional[str] = Field(
        default=None,
        description="Redis host (overrides URL)",
    )
    
    redis_port: int = Field(
        default=6379,
        description="Redis port",
    )
    
    redis_password: Optional[str] = Field(
        default=None,
        description="Redis password",
    )
    
    redis_db: int = Field(
        default=0,
        description="Redis database number",
    )
    
    redis_pool_size: int = Field(
        default=10,
        description="Redis connection pool size",
    )
    
    # ==================== Temporal Settings ====================
    
    temporal_host: str = Field(
        default="localhost:7233",
        description="Temporal server host:port",
    )
    
    temporal_namespace: str = Field(
        default="default",
        description="Temporal namespace",
    )
    
    temporal_client_cert_path: Optional[str] = Field(
        default=None,
        description="Path to Temporal client certificate",
    )
    
    temporal_client_key_path: Optional[str] = Field(
        default=None,
        description="Path to Temporal client key",
    )
    
    # ==================== Security Settings ====================

    secret_key: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        description="Secret key for JWT signing",
        validation_alias=AliasChoices("SECRET_KEY", "secret_key"),
    )
    
    algorithm: str = Field(
        default="HS256",
        description="JWT signing algorithm",
    )
    
    access_token_expire_minutes: int = Field(
        default=30,
        description="Access token expiration in minutes",
    )
    
    refresh_token_expire_days: int = Field(
        default=30,
        description="Refresh token expiration in days",
    )
    
    # ==================== CORS Settings ====================
    
    cors_origins: List[str] = Field(
        default=["*"],
        description="Allowed CORS origins",
    )
    
    cors_allow_credentials: bool = Field(
        default=True,
        description="Allow credentials in CORS requests",
    )
    
    cors_allow_methods: List[str] = Field(
        default=["*"],
        description="Allowed CORS methods",
    )
    
    cors_allow_headers: List[str] = Field(
        default=["*"],
        description="Allowed CORS headers",
    )
    
    @validator("cors_origins", pre=True)
    def validate_cors_origins(cls, v, values):
        """Validate CORS origins for production."""
        # Allow environment variable to override default
        if v is None or (isinstance(v, list) and len(v) == 1 and v[0] == "*"):
            # Check if we're in production
            env = values.get("environment", "development")
            if env == "production":
                # In production, use specific origins unless explicitly overridden
                return [
                    "https://agent-control-plane.vercel.app",
                    "https://*.vercel.app",
                    "http://localhost:3000",
                    "http://localhost:8000",
                ]
        return v
    
    # ==================== External Services ====================
    
    kubiya_api_base: str = Field(
        default="https://api.kubiya.ai",
        description="Kubiya API base URL",
    )
    
    kubiya_api_key: Optional[str] = Field(
        default=None,
        description="Kubiya API key",
        validation_alias=AliasChoices("KUBIYA_API_KEY", "kubiya_api_key"),
    )

    litellm_api_base: str = Field(
        default="https://llm-proxy.kubiya.ai",
        description="LiteLLM proxy base URL",
    )

    litellm_api_key: Optional[str] = Field(
        default=None,
        description="LiteLLM API key",
        validation_alias=AliasChoices("LITELLM_API_KEY", "litellm_api_key"),
    )
    
    litellm_default_model: str = Field(
        default="kubiya/claude-sonnet-4",
        description="Default LLM model",
    )
    
    litellm_timeout: int = Field(
        default=300,
        description="LiteLLM request timeout in seconds",
    )

    litellm_models_cache_ttl: int = Field(
        default=300,
        description="Cache TTL for LiteLLM models list in seconds (default 5 minutes)",
    )

    # ==================== Context Graph Settings ====================

    context_graph_api_base: str = Field(
        default="https://graph.kubiya.ai",
        description="Context Graph API base URL",
        validation_alias=AliasChoices("CONTEXT_GRAPH_API_BASE", "context_graph_api_base"),
    )

    context_graph_api_timeout: int = Field(
        default=120,  # Increased for semantic search operations
        description="Context Graph API request timeout in seconds",
        validation_alias=AliasChoices("CONTEXT_GRAPH_API_TIMEOUT", "context_graph_api_timeout"),
    )

    # ==================== Logging Settings ====================
    
    log_level: str = Field(
        default="INFO",
        description="Logging level",
    )
    
    log_format: str = Field(
        default="json",
        description="Log format (json or text)",
    )
    
    # ==================== Monitoring Settings ====================
    
    metrics_enabled: bool = Field(
        default=False,
        description="Enable Prometheus metrics",
    )
    
    metrics_port: int = Field(
        default=9090,
        description="Prometheus metrics port",
    )
    
    tracing_enabled: bool = Field(
        default=False,
        description="Enable OpenTelemetry tracing",
    )
    
    otlp_endpoint: Optional[str] = Field(
        default=None,
        description="OpenTelemetry collector endpoint",
    )
    
    sentry_dsn: Optional[str] = Field(
        default=None,
        description="Sentry DSN for error reporting",
        validation_alias=AliasChoices("SENTRY_DSN", "sentry_dsn"),
    )
    
    # ==================== Rate Limiting ====================
    
    rate_limit_enabled: bool = Field(
        default=True,
        description="Enable rate limiting",
    )
    
    rate_limit_requests_per_minute: int = Field(
        default=60,
        description="Default requests per minute limit",
    )
    
    rate_limit_burst_size: int = Field(
        default=10,
        description="Burst size for rate limiting",
    )

    # ==================== Event Bus Settings ====================

    event_bus: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Event bus configuration for multi-provider event publishing",
    )

    model_config = SettingsConfigDict(
        env_file=".env.local",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @classmethod
    def from_yaml_and_env(cls, config_path: Optional[str] = None) -> "APIConfig":
        """
        Load configuration from YAML file and merge with environment variables.

        Priority: Environment variables > YAML file > Defaults

        Args:
            config_path: Optional path to YAML config file

        Returns:
            APIConfig instance with merged configuration

        Example YAML:
            event_bus:
              http:
                enabled: true
                base_url: ${CONTROL_PLANE_URL}
              websocket:
                enabled: true
              redis:
                enabled: true
                redis_url: ${REDIS_URL}
              nats:
                enabled: false
        """
        from control_plane_api.app.config.config_loader import load_config_file

        # Load YAML config (empty dict if no file found)
        yaml_config = load_config_file(config_path)

        # Pydantic will merge YAML config with environment variables
        # Environment variables take precedence
        return cls(**yaml_config)
