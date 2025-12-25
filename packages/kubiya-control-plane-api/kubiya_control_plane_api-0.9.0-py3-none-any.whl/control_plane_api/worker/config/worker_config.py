"""
Worker-specific configuration.

This module contains settings specific to Temporal workers.
"""

from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import Optional


class WorkerConfig(BaseSettings):
    """Configuration for Temporal workers."""
    
    # ==================== Control Plane Connection ====================
    
    control_plane_url: str = Field(
        ...,
        description="Control Plane API URL (required)",
    )
    
    kubiya_api_key: str = Field(
        ...,
        description="Kubiya API key for authentication (required)",
    )
    
    # ==================== Worker Identity ====================
    
    queue_id: str = Field(
        ...,
        description="Worker queue ID (required)",
    )
    
    worker_id: Optional[str] = Field(
        default=None,
        description="Worker ID (auto-generated if not provided)",
    )
    
    worker_hostname: Optional[str] = Field(
        default=None,
        description="Worker hostname (auto-detected if not provided)",
    )
    
    # ==================== Worker Settings ====================
    
    heartbeat_interval: int = Field(
        default=30,
        description="Heartbeat interval in seconds",
    )
    
    max_concurrent_activities: int = Field(
        default=10,
        description="Maximum concurrent activities",
    )
    
    max_concurrent_workflows: int = Field(
        default=10,
        description="Maximum concurrent workflow tasks",
    )
    
    graceful_shutdown_timeout: int = Field(
        default=30,
        description="Graceful shutdown timeout in seconds",
    )
    
    # ==================== Temporal Settings (from Control Plane) ====================
    
    temporal_host: Optional[str] = Field(
        default=None,
        description="Temporal server host:port (provided by Control Plane)",
    )
    
    temporal_namespace: Optional[str] = Field(
        default=None,
        description="Temporal namespace (provided by Control Plane)",
    )
    
    temporal_api_key: Optional[str] = Field(
        default=None,
        description="Temporal API key (provided by Control Plane)",
    )
    
    temporal_tls_enabled: bool = Field(
        default=True,
        description="Enable TLS for Temporal connection",
    )
    
    # ==================== LiteLLM Settings (from Control Plane) ====================
    
    litellm_api_base: Optional[str] = Field(
        default=None,
        description="LiteLLM proxy base URL (provided by Control Plane)",
    )
    
    litellm_api_key: Optional[str] = Field(
        default=None,
        description="LiteLLM API key (provided by Control Plane)",
    )
    
    litellm_timeout: int = Field(
        default=300,
        description="LiteLLM request timeout in seconds",
    )
    
    litellm_max_retries: int = Field(
        default=3,
        description="Maximum retries for LiteLLM requests",
    )
    
    # ==================== Runtime Settings ====================
    
    default_runtime: str = Field(
        default="agno",
        description="Default agent runtime (agno, claude_code, openai)",
    )
    
    enable_streaming: bool = Field(
        default=True,
        description="Enable streaming responses",
    )
    
    # ==================== Resource Limits ====================
    
    max_memory_mb: Optional[int] = Field(
        default=None,
        description="Maximum memory usage in MB (if set)",
    )
    
    max_cpu_percent: Optional[float] = Field(
        default=None,
        description="Maximum CPU usage percentage (if set)",
    )
    
    # ==================== Logging Settings ====================

    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
        env="KUBIYA_CLI_LOG_LEVEL",
    )

    log_format: str = Field(
        default="pretty",
        description="Log format (pretty, json, text)",
        env="KUBIYA_LOG_FORMAT",
    )

    log_to_file: bool = Field(
        default=False,
        description="Enable logging to file",
    )

    log_file_path: str = Field(
        default="worker.log",
        description="Log file path",
    )

    # ==================== Development Settings ====================

    debug: bool = Field(
        default=False,
        description="Enable debug mode (sets KUBIYA_CLI_LOG_LEVEL=DEBUG)",
        env="DEBUG",
    )
    
    reload: bool = Field(
        default=False,
        description="Enable auto-reload on code changes",
    )
    
    # ==================== Docker Settings ====================
    
    docker_enabled: bool = Field(
        default=True,
        description="Enable Docker tool execution",
    )
    
    docker_socket_path: str = Field(
        default="/var/run/docker.sock",
        description="Docker socket path",
    )
    
    docker_network: Optional[str] = Field(
        default=None,
        description="Docker network for tool containers",
    )
    
    # ==================== Monitoring Settings ====================
    
    metrics_enabled: bool = Field(
        default=False,
        description="Enable Prometheus metrics",
    )
    
    metrics_port: int = Field(
        default=9091,
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
    
    # ==================== Security Settings ====================
    
    enable_sandbox: bool = Field(
        default=True,
        description="Enable execution sandboxing",
    )
    
    allowed_commands: Optional[str] = Field(
        default=None,
        description="Comma-separated list of allowed shell commands",
    )
    
    blocked_commands: str = Field(
        default="rm -rf,sudo,su,chmod,chown,mount,umount,iptables",
        description="Comma-separated list of blocked shell commands",
    )
    
    @validator("blocked_commands", "allowed_commands")
    def parse_command_list(cls, v):
        """Parse comma-separated command list."""
        if v:
            return [cmd.strip() for cmd in v.split(",") if cmd.strip()]
        return []
    
    class Config:
        """Pydantic config."""
        env_file = ".env.worker"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
        # Environment variable prefix
        env_prefix = ""
        
        # Allow these environment variables
        fields = {
            "control_plane_url": {"env": ["CONTROL_PLANE_URL", "control_plane_url"]},
            "kubiya_api_key": {"env": ["KUBIYA_API_KEY", "kubiya_api_key"]},
            "queue_id": {"env": ["QUEUE_ID", "queue_id"]},
            "worker_id": {"env": ["WORKER_ID", "worker_id"]},
            "heartbeat_interval": {"env": ["HEARTBEAT_INTERVAL", "heartbeat_interval"]},
        }
    
    def update_from_control_plane(self, control_plane_config: dict) -> None:
        """
        Update configuration with values from Control Plane.
        
        This is called after worker registration to update settings
        with values provided by the Control Plane.
        
        Args:
            control_plane_config: Configuration from Control Plane /start endpoint
        """
        if "temporal_host" in control_plane_config:
            self.temporal_host = control_plane_config["temporal_host"]
        
        if "temporal_namespace" in control_plane_config:
            self.temporal_namespace = control_plane_config["temporal_namespace"]
        
        if "temporal_api_key" in control_plane_config:
            self.temporal_api_key = control_plane_config["temporal_api_key"]
        
        if "litellm_api_url" in control_plane_config:
            self.litellm_api_base = control_plane_config["litellm_api_url"]
        
        if "litellm_api_key" in control_plane_config:
            self.litellm_api_key = control_plane_config["litellm_api_key"]
        
        if "worker_id" in control_plane_config:
            self.worker_id = control_plane_config["worker_id"]
