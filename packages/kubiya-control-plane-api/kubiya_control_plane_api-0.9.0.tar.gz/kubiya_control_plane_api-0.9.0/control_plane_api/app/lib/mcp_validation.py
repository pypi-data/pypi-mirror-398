"""
MCP configuration validation helpers.

Validates MCP server configurations and template syntax.
"""

import structlog
from typing import Dict, List, Any, Optional
from pydantic import ValidationError

from control_plane_api.app.schemas.mcp_schemas import MCPServerConfig
from control_plane_api.app.lib.templating import extract_all_variables, TemplateValidator, TemplateContext, get_default_engine

logger = structlog.get_logger()


class MCPValidationError(Exception):
    """Raised when MCP configuration validation fails."""
    pass


def validate_mcp_server_config(
    mcp_servers: Dict[str, Any],
    available_secrets: Optional[List[str]] = None,
    available_env_vars: Optional[List[str]] = None,
    strict: bool = False
) -> Dict[str, Any]:
    """
    Validate MCP server configuration.

    Validates:
    1. MCP server configuration schema (Pydantic validation)
    2. Template syntax in all string fields
    3. Referenced secrets exist (if available_secrets provided)
    4. Referenced env vars exist (if available_env_vars provided)

    Args:
        mcp_servers: Dict of MCP server configurations
        available_secrets: List of available secret names for validation
        available_env_vars: List of available env var names for validation
        strict: If True, raise error for missing secrets/env vars

    Returns:
        Dict with validation results:
        {
            "valid": bool,
            "errors": List[str],
            "warnings": List[str],
            "required_secrets": List[str],
            "required_env_vars": List[str]
        }

    Raises:
        MCPValidationError: If strict=True and validation fails
    """
    errors = []
    warnings = []
    all_required_secrets = set()
    all_required_env_vars = set()

    if not mcp_servers:
        return {
            "valid": True,
            "errors": [],
            "warnings": [],
            "required_secrets": [],
            "required_env_vars": []
        }

    # Validate each server configuration
    for server_name, server_config in mcp_servers.items():
        try:
            # Validate using Pydantic schema
            validated_config = MCPServerConfig(**server_config)

            # Extract template variables
            variables = extract_all_variables(server_config)
            required_secrets = variables.get("secrets", [])
            required_env_vars = variables.get("env_vars", [])

            all_required_secrets.update(required_secrets)
            all_required_env_vars.update(required_env_vars)

            # Check if required secrets are available
            if available_secrets is not None:
                missing_secrets = [s for s in required_secrets if s not in available_secrets]
                if missing_secrets:
                    error_msg = f"Server '{server_name}': Missing secrets: {', '.join(missing_secrets)}"
                    if strict:
                        errors.append(error_msg)
                    else:
                        warnings.append(error_msg)

            # Check if required env vars are available
            if available_env_vars is not None:
                missing_env_vars = [v for v in required_env_vars if v not in available_env_vars]
                if missing_env_vars:
                    error_msg = f"Server '{server_name}': Missing environment variables: {', '.join(missing_env_vars)}"
                    if strict:
                        errors.append(error_msg)
                    else:
                        warnings.append(error_msg)

            logger.debug(
                "mcp_server_validated",
                server_name=server_name,
                transport_type=validated_config.get_transport_type().value,
                required_secrets_count=len(required_secrets),
                required_env_vars_count=len(required_env_vars)
            )

        except ValidationError as e:
            error_msg = f"Server '{server_name}': Invalid configuration: {str(e)}"
            errors.append(error_msg)
            logger.warning("mcp_server_validation_error", server_name=server_name, error=str(e))

        except Exception as e:
            error_msg = f"Server '{server_name}': Validation error: {str(e)}"
            errors.append(error_msg)
            logger.error("mcp_server_validation_exception", server_name=server_name, error=str(e))

    result = {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "required_secrets": sorted(list(all_required_secrets)),
        "required_env_vars": sorted(list(all_required_env_vars))
    }

    if strict and not result["valid"]:
        error_summary = "; ".join(errors)
        raise MCPValidationError(f"MCP configuration validation failed: {error_summary}")

    return result


def validate_execution_environment_mcp(
    execution_environment: Dict[str, Any],
    strict: bool = False
) -> Dict[str, Any]:
    """
    Validate MCP servers in an execution environment configuration.

    Args:
        execution_environment: Execution environment dict with mcp_servers
        strict: If True, raise error on validation failure

    Returns:
        Validation result dict

    Raises:
        MCPValidationError: If strict=True and validation fails
    """
    mcp_servers = execution_environment.get("mcp_servers", {})
    available_secrets = execution_environment.get("secrets", [])
    available_env_vars = list(execution_environment.get("env_vars", {}).keys())

    return validate_mcp_server_config(
        mcp_servers,
        available_secrets=available_secrets,
        available_env_vars=available_env_vars,
        strict=strict
    )
