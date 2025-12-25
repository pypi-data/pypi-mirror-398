"""
Execution Environment Router - Resolve execution environment for agents/teams

This router provides workers with resolved execution environment configuration:
- Fetches agent/team execution_environment from database
- Resolves secret names to actual values from Kubiya API
- Resolves integration IDs to actual tokens from Kubiya API
- Maps integration tokens to specific env var names (GH_TOKEN, JIRA_TOKEN, etc.)
- Returns complete env var dict ready for worker to inject into execution
"""

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, Any, Optional
import structlog
from sqlalchemy.orm import Session

from control_plane_api.app.middleware.auth import get_current_organization
from control_plane_api.app.database import get_db
from control_plane_api.app.models import Environment, AgentEnvironment, TeamEnvironment
from control_plane_api.app.lib.sqlalchemy_utils import model_to_dict
from control_plane_api.app.lib.kubiya_client import KUBIYA_API_BASE
from control_plane_api.app.lib.templating import TemplateContext, resolve_templates

logger = structlog.get_logger()

router = APIRouter(prefix="/execution-environment", tags=["execution-environment"])


# Integration type to environment variable name mapping
INTEGRATION_ENV_VAR_MAP = {
    "github": "GH_TOKEN",
    "github_app": "GITHUB_TOKEN",
    "jira": "JIRA_TOKEN",
    "slack": "SLACK_TOKEN",
    "aws": "AWS_ACCESS_KEY_ID",  # Note: AWS might need multiple vars
    "aws-serviceaccount": "AWS_ROLE_ARN",
    "kubernetes": "KUBECONFIG",
}


async def resolve_secret_value(
    secret_name: str,
    token: str,
    org_id: str,
) -> str:
    """
    Resolve a secret name to its actual value from Kubiya API.

    Args:
        secret_name: Name of the secret to resolve
        token: Kubiya API token
        org_id: Organization ID

    Returns:
        Secret value as string
    """
    headers = {
        "Authorization": f"UserKey {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Kubiya-Client": "agent-control-plane",
        "X-Organization-ID": org_id,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{KUBIYA_API_BASE}/api/v2/secrets/get_value/{secret_name}",
            headers=headers,
        )

        if response.status_code == 200:
            return response.text
        else:
            logger.warning(
                "secret_resolution_failed",
                secret_name=secret_name[:20],
                status=response.status_code,
            )
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to resolve secret '{secret_name}': {response.text[:200]}",
            )


async def resolve_integration_token(
    integration_id: str,
    integration_type: str,
    token: str,
    org_id: str,
) -> Dict[str, str]:
    """
    Resolve an integration ID to its actual token from Kubiya API.

    Args:
        integration_id: Integration UUID
        integration_type: Type of integration (github, jira, etc.)
        token: Kubiya API token
        org_id: Organization ID

    Returns:
        Dict with env_var_name and token value
    """
    headers = {
        "Authorization": f"UserKey {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Kubiya-Client": "agent-control-plane",
        "X-Organization-ID": org_id,
    }

    # Build token URL based on integration type
    integration_type_lower = integration_type.lower()

    if integration_type_lower == "github":
        token_url = f"{KUBIYA_API_BASE}/api/v1/integration/github/token/{integration_id}"
    elif integration_type_lower == "github_app":
        token_url = f"{KUBIYA_API_BASE}/api/v1/integration/github_app/token/{integration_id}"
    elif integration_type_lower == "jira":
        token_url = f"{KUBIYA_API_BASE}/api/v1/integration/jira/token/{integration_id}"
    else:
        logger.warning(
            "unsupported_integration_type",
            integration_type=integration_type,
            integration_id=integration_id[:8],
        )
        # For unsupported types, skip
        return {}

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(token_url, headers=headers)

        if response.status_code == 200:
            # Try to parse as JSON first
            try:
                token_data = response.json()
                token_value = token_data.get("token", response.text)
            except:
                # If not JSON, use plain text
                token_value = response.text

            # Map to env var name
            env_var_name = INTEGRATION_ENV_VAR_MAP.get(integration_type_lower, f"{integration_type.upper()}_TOKEN")

            return {env_var_name: token_value}
        else:
            logger.warning(
                "integration_token_resolution_failed",
                integration_id=integration_id[:8],
                integration_type=integration_type,
                status=response.status_code,
            )
            # Don't fail the entire request for one integration
            return {}


async def resolve_environment_configs(
    environment_ids: list[str],
    org_id: str,
    db: Session,
) -> Dict[str, Any]:
    """
    Resolve execution environment configs from a list of environment IDs.
    Merges configs from all environments.

    Args:
        environment_ids: List of environment IDs
        org_id: Organization ID
        db: Database session

    Returns:
        Merged execution environment dict with env_vars, secrets, integration_ids, mcp_servers
    """
    if not environment_ids:
        return {"env_vars": {}, "secrets": [], "integration_ids": [], "mcp_servers": {}}

    # Fetch all environments
    environments = (
        db.query(Environment)
        .filter(
            Environment.id.in_(environment_ids),
            Environment.organization_id == org_id
        )
        .all()
    )

    # Merge all environment configs
    merged_env_vars = {}
    merged_secrets = set()
    merged_integration_ids = set()
    merged_mcp_servers = {}

    for env in environments:
        env_config = env.execution_environment or {}

        # Merge env vars (later environments override earlier ones)
        merged_env_vars.update(env_config.get("env_vars", {}))

        # Collect secrets (union)
        merged_secrets.update(env_config.get("secrets", []))

        # Collect integration IDs (union)
        merged_integration_ids.update(env_config.get("integration_ids", []))

        # Merge MCP servers (later environments override earlier ones)
        merged_mcp_servers.update(env_config.get("mcp_servers", {}))

    return {
        "env_vars": merged_env_vars,
        "secrets": list(merged_secrets),
        "integration_ids": list(merged_integration_ids),
        "mcp_servers": merged_mcp_servers,
    }


def apply_template_resolution(
    config: Dict[str, Any],
    resolved_secrets: Dict[str, str],
    resolved_env_vars: Dict[str, str],
) -> Dict[str, Any]:
    """
    Apply template resolution to a configuration object.

    Resolves all templates in the config using resolved secrets and env vars.
    Templates are resolved recursively in all string fields, including:
    - system_prompt
    - description
    - mcp_servers (all fields)
    - runtime_config (all fields)
    - Any other text-based fields

    Args:
        config: Configuration dict with potential templates
        resolved_secrets: Map of secret names to resolved values
        resolved_env_vars: Map of env var names to values

    Returns:
        Configuration with all templates resolved
    """
    try:
        # Build template context
        context = TemplateContext(
            variables={},  # Simple variables not used in execution environment
            secrets=resolved_secrets,
            env_vars=resolved_env_vars
        )

        # Apply template resolution recursively to entire config
        resolved_config = resolve_templates(config, context, skip_on_error=True)

        logger.info(
            "template_resolution_applied",
            config_keys=list(config.keys()),
            secrets_count=len(resolved_secrets),
            env_vars_count=len(resolved_env_vars)
        )

        return resolved_config

    except Exception as e:
        logger.error(
            "template_resolution_failed",
            error=str(e),
            config_keys=list(config.keys())
        )
        # Return original config on error to avoid breaking execution
        return config


@router.get("/agents/{agent_id}/resolved")
async def get_agent_execution_environment(
    agent_id: str,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    """
    Get resolved execution environment for an agent.

    This endpoint:
    1. Fetches agent's execution_environment and environment_ids from database
    2. Fetches and merges execution configs from all associated environments
    3. Merges agent's own execution_environment (agent config overrides environment)
    4. Resolves all secret names to actual values
    5. Resolves all integration IDs to actual tokens
    6. Maps integration tokens to specific env var names
    7. Returns merged env var dict

    Inheritance order (later overrides earlier):
    - Environment 1 execution_environment
    - Environment 2 execution_environment
    - ...
    - Agent execution_environment

    Returns:
        Dict of environment variables ready to inject into agent execution
    """
    try:
        token = request.state.kubiya_token
        org_id = organization["id"]

        # Import Agent model locally to avoid circular dependency
        from control_plane_api.app.models import Agent

        # Fetch agent with execution environment
        agent = (
            db.query(Agent)
            .filter(Agent.id == agent_id, Agent.organization_id == org_id)
            .first()
        )

        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

        # Get environment associations from join table
        env_associations = (
            db.query(AgentEnvironment)
            .filter(AgentEnvironment.agent_id == agent_id)
            .all()
        )
        environment_ids = [str(assoc.environment_id) for assoc in env_associations]
        env_config = await resolve_environment_configs(environment_ids, org_id, db)

        # Get agent-level config
        agent_config = agent.execution_environment or {}

        # Merge: environment config + agent config (agent overrides environment)
        execution_environment = {
            "env_vars": {**env_config.get("env_vars", {}), **agent_config.get("env_vars", {})},
            "secrets": list(set(env_config.get("secrets", []) + agent_config.get("secrets", []))),
            "integration_ids": list(set(env_config.get("integration_ids", []) + agent_config.get("integration_ids", []))),
        }

        # Start with custom env vars
        resolved_env_vars = dict(execution_environment.get("env_vars", {}))

        # Resolve secrets
        secrets = execution_environment.get("secrets", [])
        for secret_name in secrets:
            try:
                secret_value = await resolve_secret_value(secret_name, token, org_id)
                resolved_env_vars[secret_name] = secret_value
                logger.info(
                    "secret_resolved",
                    agent_id=agent_id[:8],
                    secret_name=secret_name[:20],
                )
            except Exception as e:
                logger.error(
                    "secret_resolution_error",
                    agent_id=agent_id[:8],
                    secret_name=secret_name[:20],
                    error=str(e),
                )
                # Continue with other secrets even if one fails

        # Resolve integrations
        integration_ids = execution_environment.get("integration_ids", [])
        if integration_ids:
            # First, fetch integration details to get types
            headers = {
                "Authorization": f"UserKey {token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-Kubiya-Client": "agent-control-plane",
                "X-Organization-ID": org_id,
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{KUBIYA_API_BASE}/api/v2/integrations?full=true",
                    headers=headers,
                )

                if response.status_code == 200:
                    all_integrations = response.json()

                    for integration_id in integration_ids:
                        # Find integration by UUID
                        integration = next(
                            (i for i in all_integrations if i.get("uuid") == integration_id),
                            None
                        )

                        if integration:
                            integration_type = integration.get("integration_type", "")
                            try:
                                token_env_vars = await resolve_integration_token(
                                    integration_id,
                                    integration_type,
                                    token,
                                    org_id,
                                )
                                resolved_env_vars.update(token_env_vars)
                                logger.info(
                                    "integration_resolved",
                                    agent_id=agent_id[:8],
                                    integration_id=integration_id[:8],
                                    integration_type=integration_type,
                                    env_vars=list(token_env_vars.keys()),
                                )
                            except Exception as e:
                                logger.error(
                                    "integration_resolution_error",
                                    agent_id=agent_id[:8],
                                    integration_id=integration_id[:8],
                                    error=str(e),
                                )
                        else:
                            logger.warning(
                                "integration_not_found",
                                agent_id=agent_id[:8],
                                integration_id=integration_id[:8],
                            )

        logger.info(
            "execution_environment_resolved",
            agent_id=agent_id[:8],
            env_var_count=len(resolved_env_vars),
            env_var_keys=list(resolved_env_vars.keys()),
        )

        return resolved_env_vars

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "execution_environment_resolution_error",
            agent_id=agent_id[:8],
            error=str(e),
            error_type=type(e).__name__,
        )
        raise HTTPException(status_code=500, detail=f"Failed to resolve execution environment: {str(e)}")


@router.get("/teams/{team_id}/resolved")
async def get_team_execution_environment(
    team_id: str,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    """
    Get resolved execution environment for a team.

    This endpoint:
    1. Fetches team's execution_environment and environment_ids from database
    2. Fetches and merges execution configs from all associated environments
    3. Merges team's own execution_environment (team config overrides environment)
    4. Resolves all secret names to actual values
    5. Resolves all integration IDs to actual tokens
    6. Maps integration tokens to specific env var names
    7. Returns merged env var dict

    Inheritance order (later overrides earlier):
    - Environment 1 execution_environment
    - Environment 2 execution_environment
    - ...
    - Team execution_environment

    Returns:
        Dict of environment variables ready to inject into team execution
    """
    try:
        token = request.state.kubiya_token
        org_id = organization["id"]

        # Import Team model locally to avoid circular dependency
        from control_plane_api.app.models import Team

        # Fetch team with environment associations
        team = (
            db.query(Team)
            .filter(Team.id == team_id, Team.organization_id == org_id)
            .first()
        )

        if not team:
            raise HTTPException(status_code=404, detail=f"Team {team_id} not found")

        # Get environment-level configs first
        environment_ids = team.environment_ids or []
        env_config = await resolve_environment_configs(environment_ids, org_id, db)

        # Get team-level config
        team_config = team.execution_environment or {}

        # Merge: environment config + team config (team overrides environment)
        execution_environment = {
            "env_vars": {**env_config.get("env_vars", {}), **team_config.get("env_vars", {})},
            "secrets": list(set(env_config.get("secrets", []) + team_config.get("secrets", []))),
            "integration_ids": list(set(env_config.get("integration_ids", []) + team_config.get("integration_ids", []))),
        }

        # Start with custom env vars
        resolved_env_vars = dict(execution_environment.get("env_vars", {}))

        # Resolve secrets
        secrets = execution_environment.get("secrets", [])
        for secret_name in secrets:
            try:
                secret_value = await resolve_secret_value(secret_name, token, org_id)
                resolved_env_vars[secret_name] = secret_value
                logger.info(
                    "secret_resolved",
                    team_id=team_id[:8],
                    secret_name=secret_name[:20],
                )
            except Exception as e:
                logger.error(
                    "secret_resolution_error",
                    team_id=team_id[:8],
                    secret_name=secret_name[:20],
                    error=str(e),
                )
                # Continue with other secrets even if one fails

        # Resolve integrations
        integration_ids = execution_environment.get("integration_ids", [])
        if integration_ids:
            # First, fetch integration details to get types
            headers = {
                "Authorization": f"UserKey {token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-Kubiya-Client": "agent-control-plane",
                "X-Organization-ID": org_id,
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{KUBIYA_API_BASE}/api/v2/integrations?full=true",
                    headers=headers,
                )

                if response.status_code == 200:
                    all_integrations = response.json()

                    for integration_id in integration_ids:
                        # Find integration by UUID
                        integration = next(
                            (i for i in all_integrations if i.get("uuid") == integration_id),
                            None
                        )

                        if integration:
                            integration_type = integration.get("integration_type", "")
                            try:
                                token_env_vars = await resolve_integration_token(
                                    integration_id,
                                    integration_type,
                                    token,
                                    org_id,
                                )
                                resolved_env_vars.update(token_env_vars)
                                logger.info(
                                    "integration_resolved",
                                    team_id=team_id[:8],
                                    integration_id=integration_id[:8],
                                    integration_type=integration_type,
                                    env_vars=list(token_env_vars.keys()),
                                )
                            except Exception as e:
                                logger.error(
                                    "integration_resolution_error",
                                    team_id=team_id[:8],
                                    integration_id=integration_id[:8],
                                    error=str(e),
                                )
                        else:
                            logger.warning(
                                "integration_not_found",
                                team_id=team_id[:8],
                                integration_id=integration_id[:8],
                            )

        logger.info(
            "execution_environment_resolved",
            team_id=team_id[:8],
            env_var_count=len(resolved_env_vars),
            env_var_keys=list(resolved_env_vars.keys()),
        )

        return resolved_env_vars

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "execution_environment_resolution_error",
            team_id=team_id[:8],
            error=str(e),
            error_type=type(e).__name__,
        )
        raise HTTPException(status_code=500, detail=f"Failed to resolve execution environment: {str(e)}")


async def resolve_agent_execution_environment_internal(
    agent_id: str,
    org_id: str,
    db: Session,
    token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Internal function to resolve execution environment (can be called directly).

    This bypasses HTTP/auth and can be called from other endpoints directly.
    Token is optional - when None, secrets and integrations won't be resolved from Kubiya API.
    """
    try:
        # Import Agent model locally to avoid circular dependency
        from control_plane_api.app.models import Agent

        # Fetch agent with configuration fields
        agent = (
            db.query(Agent)
            .filter(Agent.id == agent_id, Agent.organization_id == org_id)
            .first()
        )

        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

        # Get environment associations from join table
        env_associations = (
            db.query(AgentEnvironment)
            .filter(AgentEnvironment.agent_id == agent_id)
            .all()
        )
        environment_ids = [str(assoc.environment_id) for assoc in env_associations]
        env_config = await resolve_environment_configs(environment_ids, org_id, db)

        # Get agent-level config
        agent_exec_env = agent.execution_environment or {}

        # Get system_prompt from configuration, description from agent column
        agent_configuration = agent.configuration or {}

        # Merge: environment config + agent config (agent overrides environment)
        execution_environment = {
            "env_vars": {**env_config.get("env_vars", {}), **agent_exec_env.get("env_vars", {})},
            "secrets": list(set(env_config.get("secrets", []) + agent_exec_env.get("secrets", []))),
            "integration_ids": list(set(env_config.get("integration_ids", []) + agent_exec_env.get("integration_ids", []))),
            "mcp_servers": {**env_config.get("mcp_servers", {}), **agent_exec_env.get("mcp_servers", {})},
        }

        # Start with custom env vars
        resolved_env_vars = dict(execution_environment.get("env_vars", {}))
        resolved_secrets = {}

        # Resolve secrets (only if token is provided)
        secrets = execution_environment.get("secrets", [])
        if token:
            for secret_name in secrets:
                try:
                    secret_value = await resolve_secret_value(secret_name, token, org_id)
                    resolved_env_vars[secret_name] = secret_value
                    resolved_secrets[secret_name] = secret_value  # Store for template context
                    logger.debug("secret_resolved", agent_id=agent_id[:8], secret_name=secret_name[:20])
                except Exception as e:
                    logger.error("secret_resolution_error", agent_id=agent_id[:8], secret_name=secret_name[:20], error=str(e))

        # Resolve integrations (only if token is provided)
        integration_ids = execution_environment.get("integration_ids", [])
        if integration_ids and token:
            headers = {
                "Authorization": f"UserKey {token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-Kubiya-Client": "agent-control-plane",
                "X-Organization-ID": org_id,
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{KUBIYA_API_BASE}/api/v2/integrations?full=true", headers=headers)

                if response.status_code == 200:
                    all_integrations = response.json()

                    for integration_id in integration_ids:
                        integration = next((i for i in all_integrations if i.get("uuid") == integration_id), None)

                        if integration:
                            integration_type = integration.get("integration_type", "")
                            try:
                                token_env_vars = await resolve_integration_token(integration_id, integration_type, token, org_id)
                                resolved_env_vars.update(token_env_vars)
                                logger.debug("integration_resolved", agent_id=agent_id[:8], integration_id=integration_id[:8])
                            except Exception as e:
                                logger.error("integration_resolution_error", agent_id=agent_id[:8], integration_id=integration_id[:8], error=str(e))

        # Build complete config to resolve templates
        complete_config = {
            "system_prompt": agent_configuration.get("system_prompt"),
            "description": agent.description,  # From agents table column
            "configuration": agent_configuration,
            "mcp_servers": execution_environment.get("mcp_servers", {}),
            "env_vars": execution_environment.get("env_vars", {}),
        }

        # Apply template resolution to ENTIRE config
        resolved_config = apply_template_resolution(
            complete_config,
            resolved_secrets,
            resolved_env_vars
        )

        mcp_servers_resolved = resolved_config.get("mcp_servers", {})

        logger.info(
            "full_execution_environment_resolved",
            agent_id=agent_id[:8],
            env_var_count=len(resolved_env_vars),
            mcp_server_count=len(mcp_servers_resolved),
            mcp_server_names=list(mcp_servers_resolved.keys()),
            secrets_count=len(resolved_secrets)
        )

        # Debug log each MCP server after resolution
        for server_name, server_config in mcp_servers_resolved.items():
            logger.debug(
                "mcp_server_after_template_resolution",
                server_name=server_name,
                config=server_config,
            )

        return {
            "env_vars": resolved_env_vars,
            "mcp_servers": mcp_servers_resolved,
            "system_prompt": resolved_config.get("system_prompt"),
            "description": resolved_config.get("description"),
            "configuration": resolved_config.get("configuration", {}),
            "secrets_resolved": resolved_secrets,  # For debugging/logging only
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("full_execution_environment_resolution_error", agent_id=agent_id[:8], error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to resolve full execution environment: {str(e)}")


@router.get("/agents/{agent_id}/resolved/full")
async def get_agent_execution_environment_full(
    agent_id: str,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get FULL resolved execution environment for an agent with template resolution.

    This endpoint extends the basic /resolved endpoint by:
    1. Returning the complete execution environment (not just env vars)
    2. Including MCP servers with templates resolved
    3. Resolving templates in ALL text fields (system_prompt, description, etc.)
    4. Providing resolved secrets dict (for template context)

    Returns:
        Complete execution environment dict with:
        - env_vars: Resolved environment variables
        - mcp_servers: MCP server configs with templates resolved
        - secrets_resolved: Map of secret names to values (for templates)
        - raw_config: Original config before template resolution
    """
    from control_plane_api.app.controllers.execution_environment_controller import (
        resolve_agent_execution_environment,
        ExecutionEnvironmentResolutionError,
    )
    import os

    try:
        org_id = organization["id"]

        # Determine which token to use for Kubiya API calls
        # If authenticated with UserKey (API key), use that token
        # If authenticated with Bearer (JWT), fall back to environment KUBIYA_API_KEY
        auth_type = getattr(request.state, "kubiya_auth_type", "Bearer")
        if auth_type == "UserKey":
            # User authenticated with API key - use it directly
            kubiya_api_key = request.state.kubiya_token
        else:
            # User authenticated with JWT - use environment API key for Kubiya API calls
            kubiya_api_key = os.environ.get("KUBIYA_API_KEY")

        return await resolve_agent_execution_environment(agent_id, org_id, db, kubiya_api_key)
    except ExecutionEnvironmentResolutionError as e:
        raise HTTPException(status_code=404 if "not found" in str(e).lower() else 500, detail=str(e))


@router.get("/teams/{team_id}/resolved/full")
async def get_team_execution_environment_full(
    team_id: str,
    request: Request,
    organization: dict = Depends(get_current_organization),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get FULL resolved execution environment for a team with template resolution.

    Similar to agent endpoint but for teams.
    """
    from control_plane_api.app.controllers.execution_environment_controller import (
        resolve_team_execution_environment,
        ExecutionEnvironmentResolutionError,
    )
    import os

    try:
        org_id = organization["id"]

        # Determine which token to use for Kubiya API calls
        auth_type = getattr(request.state, "kubiya_auth_type", "Bearer")
        if auth_type == "UserKey":
            kubiya_api_key = request.state.kubiya_token
        else:
            kubiya_api_key = os.environ.get("KUBIYA_API_KEY")

        return await resolve_team_execution_environment(team_id, org_id, db, kubiya_api_key)
    except ExecutionEnvironmentResolutionError as e:
        raise HTTPException(status_code=404 if "not found" in str(e).lower() else 500, detail=str(e))
