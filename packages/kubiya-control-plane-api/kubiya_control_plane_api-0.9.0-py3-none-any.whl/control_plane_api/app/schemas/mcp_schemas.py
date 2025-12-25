"""
Pydantic schemas for MCP (Model Context Protocol) server configurations.

Supports multiple transport types:
- stdio: External process communication via stdin/stdout
- http: HTTP-based communication
- sse: Server-Sent Events communication

All string fields support template syntax for dynamic value resolution.
"""

from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from typing import Dict, List, Literal, Optional, Union, Any
from enum import Enum


class MCPTransportType(str, Enum):
    """MCP server transport types."""
    STDIO = "stdio"
    HTTP = "http"
    SSE = "sse"


class MCPServerStdioConfig(BaseModel):
    """
    Configuration for stdio-based MCP servers.

    Stdio servers run as external processes and communicate via stdin/stdout.
    Commonly used for local tools and CLI-based MCP servers.

    All string fields support template syntax:
    - {{variable}} - Simple variables
    - {{.secret.name}} - Secrets from vault
    - {{.env.VAR}} - Environment variables

    Example:
        {
            "command": "python",
            "args": ["-m", "mcp_server_filesystem"],
            "env": {
                "ALLOWED_PATHS": "{{.env.PROJECT_ROOT}}",
                "API_KEY": "{{.secret.filesystem_key}}"
            }
        }
    """
    command: str = Field(
        ...,
        description="Command to execute (supports templates)",
        min_length=1,
        examples=["python", "node", "npx", "/usr/local/bin/mcp-server"]
    )
    args: List[str] = Field(
        default_factory=list,
        description="Command arguments (each arg supports templates)",
        examples=[
            ["-m", "mcp_server_filesystem"],
            ["@modelcontextprotocol/server-filesystem", "{{.env.ROOT_PATH}}"]
        ]
    )
    env: Dict[str, str] = Field(
        default_factory=dict,
        description="Environment variables (values support templates)",
        examples=[
            {"ALLOWED_PATHS": "/home/user/projects", "DEBUG": "{{.env.DEBUG_MODE}}"}
        ]
    )

    @field_validator('command')
    @classmethod
    def validate_command(cls, v: str) -> str:
        """Validate command is not empty after stripping."""
        if not v.strip():
            raise ValueError("Command cannot be empty or whitespace only")
        return v.strip()

    @field_validator('args')
    @classmethod
    def validate_args(cls, v: List[str]) -> List[str]:
        """Validate args list doesn't contain empty strings."""
        if any(not arg.strip() for arg in v):
            raise ValueError("Arguments cannot contain empty or whitespace-only strings")
        return [arg.strip() for arg in v]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "command": "python",
                "args": ["-m", "mcp_server_filesystem"],
                "env": {
                    "ALLOWED_PATHS": "{{.env.PROJECT_ROOT}}",
                    "LOG_LEVEL": "info"
                }
            }
        }
    )


class MCPServerHTTPConfig(BaseModel):
    """
    Configuration for HTTP/SSE-based MCP servers.

    HTTP servers communicate over network using HTTP protocol or Server-Sent Events.
    Useful for remote MCP servers and cloud-hosted tools.

    All string fields support template syntax:
    - {{variable}} - Simple variables
    - {{.secret.name}} - Secrets from vault
    - {{.env.VAR}} - Environment variables

    Example:
        {
            "type": "sse",
            "url": "https://{{.env.API_HOST}}/mcp/sse",
            "headers": {
                "Authorization": "Bearer {{.secret.api_token}}",
                "X-API-Key": "{{.secret.api_key}}"
            }
        }
    """
    type: Literal["http", "sse"] = Field(
        ...,
        description="Transport type: 'http' for HTTP or 'sse' for Server-Sent Events"
    )
    url: str = Field(
        ...,
        description="Server URL (supports templates)",
        min_length=1,
        examples=[
            "https://api.example.com/mcp",
            "https://{{.env.MCP_HOST}}/sse",
            "http://localhost:{{.env.MCP_PORT}}/mcp"
        ]
    )
    headers: Dict[str, str] = Field(
        default_factory=dict,
        description="HTTP headers (values support templates)",
        examples=[
            {
                "Authorization": "Bearer {{.secret.mcp_token}}",
                "X-API-Key": "{{.secret.api_key}}",
                "Content-Type": "application/json"
            }
        ]
    )

    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL format (basic check, templates make full validation impossible)."""
        v = v.strip()
        if not v:
            raise ValueError("URL cannot be empty")

        # Basic sanity check - should start with http:// or https:// or contain template
        if not (v.startswith(('http://', 'https://')) or '{{' in v):
            raise ValueError("URL must start with http:// or https://, or contain templates")

        return v

    @field_validator('headers')
    @classmethod
    def validate_headers(cls, v: Dict[str, str]) -> Dict[str, str]:
        """Validate headers don't have empty keys or values."""
        for key, value in v.items():
            if not key.strip():
                raise ValueError("Header keys cannot be empty")
            if not value.strip():
                raise ValueError(f"Header value for '{key}' cannot be empty")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "sse",
                "url": "https://api.example.com/mcp/sse",
                "headers": {
                    "Authorization": "Bearer {{.secret.mcp_token}}",
                    "X-Organization": "{{.env.ORG_ID}}"
                }
            }
        }
    )


class MCPServerConfig(BaseModel):
    """
    Unified MCP server configuration supporting multiple transport types.

    This schema uses discriminated union based on the presence of 'command' or 'type' field:
    - If 'command' is present: stdio transport
    - If 'type' is present: HTTP/SSE transport

    The configuration is validated to ensure only one transport type is specified.
    """
    # Fields from stdio config
    command: Optional[str] = Field(
        None,
        description="Command for stdio transport (mutually exclusive with url/type)"
    )
    args: Optional[List[str]] = Field(
        None,
        description="Arguments for stdio transport"
    )
    env: Optional[Dict[str, str]] = Field(
        None,
        description="Environment variables (used by both stdio and HTTP transports)"
    )

    # Fields from HTTP/SSE config
    type: Optional[Literal["http", "sse"]] = Field(
        None,
        description="Transport type for HTTP/SSE (mutually exclusive with command)",
        alias="transport_type"  # Support both 'type' and 'transport_type' for backward compatibility
    )
    url: Optional[str] = Field(
        None,
        description="URL for HTTP/SSE transport (mutually exclusive with command)"
    )
    headers: Optional[Dict[str, str]] = Field(
        None,
        description="HTTP headers for HTTP/SSE transport"
    )

    @model_validator(mode='after')
    def validate_transport_type(self):
        """Validate that exactly one transport type is configured."""
        has_stdio = self.command is not None
        has_http = self.type is not None or self.url is not None

        if not has_stdio and not has_http:
            raise ValueError(
                "MCP server config must specify either 'command' (stdio) or 'type'/'url' (HTTP/SSE)"
            )

        if has_stdio and has_http:
            raise ValueError(
                "MCP server config cannot specify both stdio (command) and HTTP/SSE (type/url) transport"
            )

        # Validate stdio config
        if has_stdio:
            if not self.command.strip():
                raise ValueError("Command cannot be empty for stdio transport")

        # Validate HTTP/SSE config
        if has_http:
            if not self.type:
                raise ValueError("'type' field is required for HTTP/SSE transport")
            if not self.url:
                raise ValueError("'url' field is required for HTTP/SSE transport")
            if not self.url.strip():
                raise ValueError("URL cannot be empty for HTTP/SSE transport")

        return self

    def get_transport_type(self) -> MCPTransportType:
        """Get the transport type of this configuration."""
        if self.command:
            return MCPTransportType.STDIO
        elif self.type == "sse":
            return MCPTransportType.SSE
        elif self.type == "http":
            return MCPTransportType.HTTP
        else:
            raise ValueError("Invalid MCP server configuration")

    def to_stdio_config(self) -> Optional[MCPServerStdioConfig]:
        """Convert to stdio config if applicable."""
        if self.command:
            return MCPServerStdioConfig(
                command=self.command,
                args=self.args or [],
                env=self.env or {}
            )
        return None

    def to_http_config(self) -> Optional[MCPServerHTTPConfig]:
        """Convert to HTTP/SSE config if applicable."""
        if self.type and self.url:
            return MCPServerHTTPConfig(
                type=self.type,
                url=self.url,
                headers=self.headers or {}
            )
        return None

    model_config = ConfigDict(
        populate_by_name=True,  # Allow populating by both field name and alias
        json_schema_extra={
            "examples": [
                {
                    "command": "python",
                    "args": ["-m", "mcp_server_filesystem"],
                    "env": {"ALLOWED_PATHS": "{{.env.PROJECT_ROOT}}"}
                },
                {
                    "type": "sse",
                    "url": "https://api.example.com/mcp",
                    "headers": {"Authorization": "Bearer {{.secret.token}}"}
                },
                {
                    "transport_type": "sse",  # Also supports 'transport_type'
                    "url": "https://api.example.com/mcp",
                    "headers": {"Authorization": "Bearer {{.secret.token}}"}
                }
            ]
        }
    )

# NOTE: MCPServersConfig was removed as it's not used anywhere and had Pydantic v2 compatibility issues.
# MCP servers are stored as Dict[str, Any] in execution_environment.mcp_servers
