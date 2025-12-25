from pydantic_settings import BaseSettings
from pydantic import model_validator
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 7777
    API_TITLE: str = "Agent Control Plane"
    API_VERSION: str = "0.1.0"
    API_DESCRIPTION: str = "Multi-tenant agent orchestration with Temporal workflows"

    # Supabase Settings (replaces DATABASE_URL for serverless)
    SUPABASE_URL: str = ""  # Required: Set via environment variable
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_SERVICE_KEY: str = ""  # Required: Set via environment variable for admin operations

    # Legacy Database URL (kept for backward compatibility)
    DATABASE_URL: Optional[str] = None

    @model_validator(mode='after')
    def set_database_url_fallback(self):
        """Set DATABASE_URL from SUPABASE_POSTGRES_URL if not already set (for Vercel compatibility)"""
        if not self.DATABASE_URL:
            # Check for Vercel's SUPABASE_POSTGRES_URL or other variants
            supabase_db_url = (
                os.environ.get("SUPABASE_POSTGRES_URL") or
                os.environ.get("SUPABASE_POSTGRES_PRISMA_URL") or
                os.environ.get("SUPABASE_DB_URL")
            )
            if supabase_db_url:
                # Fix URL format for SQLAlchemy 2.0+ (postgres:// -> postgresql://)
                if supabase_db_url.startswith("postgres://"):
                    supabase_db_url = supabase_db_url.replace("postgres://", "postgresql://", 1)
                # Remove invalid Supabase pooler parameters that SQLAlchemy doesn't understand
                supabase_db_url = supabase_db_url.replace("&supa=base-pooler.x", "")
                self.DATABASE_URL = supabase_db_url
        
        # Also fix DATABASE_URL if it was already set with old postgres:// scheme
        if self.DATABASE_URL and self.DATABASE_URL.startswith("postgres://"):
            self.DATABASE_URL = self.DATABASE_URL.replace("postgres://", "postgresql://", 1)
        
        # Remove invalid Supabase pooler parameters from DATABASE_URL
        if self.DATABASE_URL:
            self.DATABASE_URL = self.DATABASE_URL.replace("&supa=base-pooler.x", "")
        
        return self

    # Redis Settings (from Composer)
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_HOST: Optional[str] = None
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0

    # Temporal Settings
    TEMPORAL_HOST: str = "localhost:7233"
    TEMPORAL_NAMESPACE: str = "default"
    TEMPORAL_CLIENT_CERT_PATH: Optional[str] = None
    TEMPORAL_CLIENT_KEY_PATH: Optional[str] = None

    # Security Settings
    SECRET_KEY: str = "change-this-secret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Logging
    LOG_LEVEL: str = "info"

    # CORS
    CORS_ORIGINS: list[str] = ["*"]

    # LiteLLM Settings
    LITELLM_API_BASE: str = "https://llm-proxy.kubiya.ai"
    LITELLM_API_KEY: str = ""  # Required: Set via environment variable
    LITELLM_DEFAULT_MODEL: str = "kubiya/claude-sonnet-4"
    LITELLM_TIMEOUT: int = 300
    LITELLM_MODELS_CACHE_TTL: int = 300  # Cache TTL in seconds (default: 5 minutes)

    # Kubiya API Settings
    KUBIYA_API_BASE: str = "https://api.kubiya.ai"

    # Context Graph API Settings
    CONTEXT_GRAPH_API_BASE: str = "https://context-graph-api.dev.kubiya.ai"
    CONTEXT_GRAPH_API_TIMEOUT: int = 30

    # Environment
    ENVIRONMENT: str = "development"  # development, staging, production

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Allow extra environment variables (for worker-specific vars)


settings = Settings()
