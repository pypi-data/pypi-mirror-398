"""
Execution Environment Controller - Centralized logic for resolving execution environments

This controller provides reusable logic for resolving execution environments for agents/teams.
It can be called from:
- API routes (for HTTP requests)
- Workers (for direct execution)
- Other internal services

The controller handles:
- Fetching execution environment configs from database
- Resolving secret names to actual values from Kubiya API
- Resolving integration IDs to actual tokens from Kubiya API
- Merging configs from environments + agent/team
- Template resolution in config fields
"""

import httpx
import os
import tempfile
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
import structlog

from control_plane_api.app.models import (
    Agent,
    Team,
    Environment,
    AgentEnvironment,
    TeamEnvironment,
)
from control_plane_api.app.models.custom_integration import CustomIntegration
from control_plane_api.app.lib.kubiya_client import KUBIYA_API_BASE
from control_plane_api.app.lib.templating import TemplateContext, resolve_templates

logger = structlog.get_logger(__name__)


# Integration type to environment variable name mapping
# Each integration can map to multiple env vars (e.g., AWS needs key + secret)
INTEGRATION_ENV_VAR_MAP = {
    "github": ["GH_TOKEN", "GITHUB_TOKEN"],
    "github_app": ["GITHUB_TOKEN"],
    "jira": ["JIRA_TOKEN"],
    "slack": ["SLACK_TOKEN", "SLACK_BOT_TOKEN"],
    "aws": ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN", "AWS_REGION"],
    "aws-serviceaccount": ["AWS_ROLE_ARN", "AWS_REGION"],
    "kubernetes": ["KUBECONFIG"],
    "gcp": ["GCP_SERVICE_ACCOUNT_KEY", "GOOGLE_APPLICATION_CREDENTIALS"],
    "azure": ["AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET", "AZURE_TENANT_ID"],
    "datadog": ["DD_API_KEY", "DD_APP_KEY", "DD_SITE"],
    "pagerduty": ["PD_TOKEN"],
    "gitlab": ["GITLAB_TOKEN"],
    "bitbucket": ["BITBUCKET_TOKEN"],
    "linear": ["LINEAR_API_KEY"],
    "notion": ["NOTION_API_KEY"],
    "openai": ["OPENAI_API_KEY"],
    "anthropic": ["ANTHROPIC_API_KEY"],
}


class ExecutionEnvironmentResolutionError(Exception):
    """Raised when execution environment resolution fails"""
    pass


def create_aws_credentials_file(
    access_key_id: str,
    secret_access_key: str,
    session_token: Optional[str] = None,
    region: Optional[str] = None,
    profile: str = "default",
) -> Tuple[str, str]:
    """
    Create AWS credentials and config files for use with AWS SDKs/CLI.

    Args:
        access_key_id: AWS access key ID
        secret_access_key: AWS secret access key
        session_token: Optional session token for temporary credentials
        region: Optional AWS region
        profile: Profile name (default: "default")

    Returns:
        Tuple of (credentials_file_path, config_file_path)
    """
    # Create temp directory for AWS config
    temp_dir = tempfile.mkdtemp(prefix="aws_")

    # Create credentials file
    credentials_path = os.path.join(temp_dir, "credentials")
    credentials_content = f"""[{profile}]
aws_access_key_id = {access_key_id}
aws_secret_access_key = {secret_access_key}
"""
    if session_token:
        credentials_content += f"aws_session_token = {session_token}\n"

    with open(credentials_path, "w") as f:
        f.write(credentials_content)

    # Create config file
    config_path = os.path.join(temp_dir, "config")
    config_content = f"""[{profile}]
"""
    if region:
        config_content += f"region = {region}\n"
    else:
        config_content += "region = us-east-1\n"

    with open(config_path, "w") as f:
        f.write(config_content)

    logger.debug(
        "aws_credentials_files_created",
        credentials_path=credentials_path,
        config_path=config_path,
        profile=profile,
    )

    return credentials_path, config_path


def create_kubeconfig_file(kubeconfig_content: str) -> str:
    """
    Create a kubeconfig file from content.

    Args:
        kubeconfig_content: YAML content of kubeconfig

    Returns:
        Path to kubeconfig file
    """
    temp_dir = tempfile.mkdtemp(prefix="kube_")
    kubeconfig_path = os.path.join(temp_dir, "config")

    with open(kubeconfig_path, "w") as f:
        f.write(kubeconfig_content)

    logger.debug("kubeconfig_file_created", kubeconfig_path=kubeconfig_path)

    return kubeconfig_path


async def resolve_custom_integration(
    custom_integration_id: str,
    org_id: str,
    db: Session,
    kubiya_token: str,
) -> Dict[str, Any]:
    """
    Resolve a custom integration to environment variables and files.

    Args:
        custom_integration_id: Custom integration UUID
        org_id: Organization ID
        db: Database session
        kubiya_token: Kubiya API token for secrets resolution

    Returns:
        Dict with:
        - env_vars: Dict of environment variables
        - files: List of files to create
        - context_prompt: Optional contextual prompt
    """
    # Fetch custom integration from database
    custom_int = db.query(CustomIntegration).filter(
        CustomIntegration.id == custom_integration_id,
        CustomIntegration.organization_id == org_id
    ).first()

    if not custom_int:
        logger.warning(
            "custom_integration_not_found",
            integration_id=custom_integration_id[:8],
            org_id=org_id
        )
        return {"env_vars": {}, "files": [], "context_prompt": None}

    config = custom_int.config or {}
    resolved_env_vars = {}
    files_to_create = []

    # Add direct env vars
    env_vars = config.get("env_vars", {})
    resolved_env_vars.update(env_vars)

    # Resolve secrets
    secrets = config.get("secrets", [])
    for secret_name in secrets:
        try:
            secret_value = await resolve_secret_value(secret_name, kubiya_token, org_id)
            resolved_env_vars[secret_name] = secret_value
            logger.debug(
                "custom_integration_secret_resolved",
                integration_id=custom_integration_id[:8],
                secret_name=secret_name[:20]
            )
        except Exception as e:
            logger.error(
                "custom_integration_secret_resolution_error",
                integration_id=custom_integration_id[:8],
                secret_name=secret_name[:20],
                error=str(e)
            )

    # Prepare files
    files_config = config.get("files", [])
    for file_config in files_config:
        file_path = file_config.get("path")
        content = file_config.get("content")
        secret_ref = file_config.get("secret_ref")
        mode = file_config.get("mode", "0644")

        if not file_path:
            continue

        # Resolve content from secret if needed
        if secret_ref and not content:
            try:
                content = await resolve_secret_value(secret_ref, kubiya_token, org_id)
                logger.debug(
                    "custom_integration_file_secret_resolved",
                    integration_id=custom_integration_id[:8],
                    file_path=file_path,
                    secret_ref=secret_ref[:20]
                )
            except Exception as e:
                logger.error(
                    "custom_integration_file_secret_error",
                    integration_id=custom_integration_id[:8],
                    file_path=file_path,
                    error=str(e)
                )
                continue

        if content:
            files_to_create.append({
                "path": file_path,
                "content": content,
                "mode": mode,
                "description": file_config.get("description")
            })

    context_prompt = config.get("context_prompt")

    logger.info(
        "custom_integration_resolved",
        integration_id=custom_integration_id[:8],
        integration_name=custom_int.name,
        env_var_count=len(resolved_env_vars),
        file_count=len(files_to_create),
        has_context=bool(context_prompt)
    )

    return {
        "env_vars": resolved_env_vars,
        "files": files_to_create,
        "context_prompt": context_prompt,
        "name": custom_int.name,
        "integration_type": custom_int.integration_type
    }


def build_integration_context(
    resolved_integrations: List[Dict[str, Any]],
) -> str:
    """
    Build integration context information for injection into system prompt.

    This provides the agent with awareness of available integrations and their
    configuration without exposing credentials.

    Args:
        resolved_integrations: List of resolved integration metadata

    Returns:
        Markdown-formatted context string for system prompt
    """
    if not resolved_integrations:
        return ""

    context_parts = ["## Available Integrations\n"]
    context_parts.append("The following integrations are configured and available for use:\n")

    for integration in resolved_integrations:
        integration_type = integration.get("integration_type", "unknown")
        integration_name = integration.get("name", integration_type)
        env_vars = integration.get("env_vars", [])
        custom_context = integration.get("custom_context")

        context_parts.append(f"\n### {integration_name} ({integration_type})")

        if env_vars:
            context_parts.append(f"- Available environment variables: {', '.join(env_vars)}")

        # Add custom context if provided
        if custom_context:
            context_parts.append(f"- {custom_context}")

        # Add integration-specific guidance
        if integration_type in ["aws", "aws-serviceaccount"]:
            context_parts.append("- AWS SDK and CLI are pre-configured with credentials")
            context_parts.append("- Use environment variables or ~/.aws/credentials file")
        elif integration_type == "kubernetes":
            context_parts.append("- Kubernetes kubectl is pre-configured")
            context_parts.append("- Use KUBECONFIG environment variable or ~/.kube/config")
        elif integration_type in ["github", "github_app"]:
            context_parts.append("- GitHub API access is available via GH_TOKEN or GITHUB_TOKEN")
        elif integration_type == "jira":
            context_parts.append("- Jira API access is available via JIRA_TOKEN")
        elif integration_type == "slack":
            context_parts.append("- Slack API access is available via SLACK_TOKEN")

    return "\n".join(context_parts)


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

    Raises:
        ExecutionEnvironmentResolutionError: If secret resolution fails
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
            raise ExecutionEnvironmentResolutionError(
                f"Failed to resolve secret '{secret_name}': {response.text[:200]}"
            )


async def resolve_integration_token(
    integration_id: str,
    integration_type: str,
    token: str,
    org_id: str,
) -> Dict[str, str]:
    """
    Resolve an integration ID to its credentials from Kubiya API.

    Args:
        integration_id: Integration UUID
        integration_type: Type of integration (github, jira, aws, etc.)
        token: Kubiya API token
        org_id: Organization ID

    Returns:
        Dict with environment variable names mapped to their values.
        May return multiple env vars for integrations like AWS (key + secret).
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

    # Map integration type to API endpoint
    # NOTE: Kubiya API currently supports github, github_app, jira via /token endpoint
    # For other types, we try the generic /creds endpoint used by SDK

    if integration_type_lower == "github":
        token_url = f"{KUBIYA_API_BASE}/api/v1/integration/github/token/{integration_id}"
    elif integration_type_lower == "github_app":
        token_url = f"{KUBIYA_API_BASE}/api/v1/integration/github_app/token/{integration_id}"
    elif integration_type_lower == "jira":
        token_url = f"{KUBIYA_API_BASE}/api/v1/integration/jira/token/{integration_id}"
    elif integration_type_lower == "slack":
        token_url = f"{KUBIYA_API_BASE}/api/v1/integration/slack/token/{integration_id}"
    else:
        # Use SDK-style generic endpoint: /api/v1/integrations/{vendor}/creds/{id}
        # This supports AWS, Kubernetes, Azure, and other integrations
        # Special integrations (jira, github_app) use "0" as ID per SDK convention
        SPECIAL_INTEGRATIONS = {"jira", "github_app"}
        actual_id = "0" if integration_type_lower in SPECIAL_INTEGRATIONS else integration_id
        token_url = f"{KUBIYA_API_BASE}/api/v1/integrations/{integration_type_lower}/creds/{actual_id}"
        logger.debug(
            "using_sdk_creds_endpoint",
            integration_type=integration_type,
            integration_id=integration_id[:8],
            actual_id=actual_id if actual_id == "0" else actual_id[:8],
        )

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(token_url, headers=headers)

        if response.status_code == 200:
            try:
                # Try to parse as JSON first
                credential_data = response.json()

                # Handle different response formats based on integration type
                if integration_type_lower in ["aws", "aws-serviceaccount"]:
                    # AWS returns structured credentials
                    env_vars = {}
                    if "access_key_id" in credential_data:
                        env_vars["AWS_ACCESS_KEY_ID"] = credential_data["access_key_id"]
                    if "secret_access_key" in credential_data:
                        env_vars["AWS_SECRET_ACCESS_KEY"] = credential_data["secret_access_key"]
                    if "session_token" in credential_data:
                        env_vars["AWS_SESSION_TOKEN"] = credential_data["session_token"]
                    if "region" in credential_data:
                        env_vars["AWS_REGION"] = credential_data["region"]
                    if "role_arn" in credential_data:
                        env_vars["AWS_ROLE_ARN"] = credential_data["role_arn"]
                    return env_vars

                elif integration_type_lower == "kubernetes":
                    # Kubernetes returns kubeconfig content
                    kubeconfig_content = credential_data.get("kubeconfig", response.text)
                    return {"KUBECONFIG_CONTENT": kubeconfig_content}

                elif integration_type_lower == "azure":
                    # Azure returns structured credentials
                    env_vars = {}
                    if "client_id" in credential_data:
                        env_vars["AZURE_CLIENT_ID"] = credential_data["client_id"]
                    if "client_secret" in credential_data:
                        env_vars["AZURE_CLIENT_SECRET"] = credential_data["client_secret"]
                    if "tenant_id" in credential_data:
                        env_vars["AZURE_TENANT_ID"] = credential_data["tenant_id"]
                    return env_vars

                else:
                    # Generic token-based integration
                    token_value = credential_data.get("token", response.text)

                    # Map to standard env var names
                    env_var_names = INTEGRATION_ENV_VAR_MAP.get(
                        integration_type_lower, [f"{integration_type.upper()}_TOKEN"]
                    )

                    # Return token for first (primary) env var name
                    return {env_var_names[0]: token_value}

            except Exception as e:
                logger.debug(
                    "credential_json_parse_failed",
                    integration_id=integration_id[:8],
                    error=str(e),
                    note="Falling back to plain text"
                )
                # If not JSON, use plain text
                token_value = response.text.strip()
                env_var_names = INTEGRATION_ENV_VAR_MAP.get(
                    integration_type_lower, [f"{integration_type.upper()}_TOKEN"]
                )
                return {env_var_names[0]: token_value}
        else:
            logger.warning(
                "integration_token_resolution_failed",
                integration_id=integration_id[:8],
                integration_type=integration_type,
                status=response.status_code,
                response_preview=response.text[:200],
            )
            # Don't fail the entire request for one integration
            return {}


async def resolve_environment_configs(
    environment_ids: List[str],
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
        return {
            "env_vars": {},
            "secrets": [],
            "integration_ids": [],
            "mcp_servers": {},
        }

    # Fetch all environments
    environments = (
        db.query(Environment)
        .filter(Environment.id.in_(environment_ids), Environment.organization_id == org_id)
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
    Templates are resolved recursively in all string fields.

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
            variables={},
            secrets=resolved_secrets,
            env_vars=resolved_env_vars,
        )

        # Apply template resolution recursively to entire config
        resolved_config = resolve_templates(config, context, skip_on_error=True)

        logger.debug(
            "template_resolution_applied",
            config_keys=list(config.keys()),
            secrets_count=len(resolved_secrets),
            env_vars_count=len(resolved_env_vars),
        )

        return resolved_config

    except Exception as e:
        logger.error(
            "template_resolution_failed",
            error=str(e),
            config_keys=list(config.keys()),
        )
        # Return original config on error to avoid breaking execution
        return config


async def resolve_agent_execution_environment(
    agent_id: str,
    org_id: str,
    db: Session,
    kubiya_token: str = None,
) -> Dict[str, Any]:
    """
    Resolve complete execution environment for an agent.

    This is the main controller function that:
    1. Fetches agent config and associated environments from database
    2. Merges environment configs (env vars, secrets, integrations, MCP servers)
    3. Resolves secret names to actual values from Kubiya API
    4. Resolves integration IDs to actual tokens from Kubiya API
    5. Applies template resolution to all config fields
    6. Returns complete resolved execution environment

    Args:
        agent_id: Agent UUID
        org_id: Organization ID
        db: Database session
        kubiya_token: Kubiya API token for secret/integration resolution (optional, uses env var if not provided)

    Returns:
        Dict with:
        - env_vars: Resolved environment variables (dict)
        - mcp_servers: MCP server configs with templates resolved (dict)
        - system_prompt: Resolved system prompt (str)
        - description: Resolved description (str)
        - configuration: Resolved agent configuration (dict)

    Raises:
        ExecutionEnvironmentResolutionError: If agent not found or resolution fails
    """
    try:
        # Use environment KUBIYA_API_KEY if token not provided
        # This is needed because the JWT bearer token from requests doesn't work with Kubiya secrets API
        import os
        if not kubiya_token:
            kubiya_token = os.environ.get("KUBIYA_API_KEY")
            if not kubiya_token:
                logger.warning(
                    "kubiya_api_key_not_available",
                    agent_id=agent_id[:8],
                    note="Secrets and integrations will not be resolved"
                )
                # Continue without secret resolution
        # Fetch agent with configuration fields
        agent = (
            db.query(Agent)
            .filter(Agent.id == agent_id, Agent.organization_id == org_id)
            .first()
        )

        if not agent:
            raise ExecutionEnvironmentResolutionError(
                f"Agent {agent_id} not found in organization {org_id}"
            )

        # Get environment associations from join table
        env_associations = (
            db.query(AgentEnvironment)
            .filter(AgentEnvironment.agent_id == agent_id)
            .all()
        )
        environment_ids = [str(assoc.environment_id) for assoc in env_associations]

        # Fetch environment names for dataset scoping
        environment_names = []
        if environment_ids:
            environments = (
                db.query(Environment)
                .filter(Environment.id.in_(environment_ids))
                .all()
            )
            environment_names = [env.name for env in environments]

        # Resolve and merge environment configs
        env_config = await resolve_environment_configs(environment_ids, org_id, db)

        # Get agent-level config
        agent_exec_env = agent.execution_environment or {}
        agent_configuration = agent.configuration or {}

        # Merge: environment config + agent config (agent overrides environment)
        execution_environment = {
            "env_vars": {
                **env_config.get("env_vars", {}),
                **agent_exec_env.get("env_vars", {}),
            },
            "secrets": list(
                set(env_config.get("secrets", []) + agent_exec_env.get("secrets", []))
            ),
            "integration_ids": list(
                set(
                    env_config.get("integration_ids", [])
                    + agent_exec_env.get("integration_ids", [])
                )
            ),
            "custom_integration_ids": list(
                set(
                    env_config.get("custom_integration_ids", [])
                    + agent_exec_env.get("custom_integration_ids", [])
                )
            ),
            "mcp_servers": {
                **env_config.get("mcp_servers", {}),
                **agent_exec_env.get("mcp_servers", {}),
            },
        }

        # Start with custom env vars
        resolved_env_vars = dict(execution_environment.get("env_vars", {}))
        resolved_secrets = {}
        resolved_integrations = []  # Track resolved integrations for context

        # Add KUBIYA_API_KEY to resolved_env_vars for template resolution
        # This allows MCP server configs to use {{KUBIYA_API_KEY}} templates
        import os
        kubiya_api_key_from_env = os.environ.get("KUBIYA_API_KEY")
        if kubiya_api_key_from_env:
            resolved_env_vars["KUBIYA_API_KEY"] = kubiya_api_key_from_env

        # Resolve secrets
        secrets = execution_environment.get("secrets", [])
        for secret_name in secrets:
            try:
                secret_value = await resolve_secret_value(
                    secret_name, kubiya_token, org_id
                )
                resolved_env_vars[secret_name] = secret_value
                resolved_secrets[secret_name] = secret_value
                logger.debug(
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
            headers = {
                "Authorization": f"UserKey {kubiya_token}",
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
                        integration = next(
                            (
                                i
                                for i in all_integrations
                                if i.get("uuid") == integration_id
                            ),
                            None,
                        )

                        if integration:
                            integration_type = integration.get("integration_type", "")
                            integration_name = integration.get("name", integration_type)
                            try:
                                token_env_vars = await resolve_integration_token(
                                    integration_id,
                                    integration_type,
                                    kubiya_token,
                                    org_id,
                                )

                                # Handle AWS credentials file creation
                                if integration_type in ["aws", "aws-serviceaccount"] and token_env_vars:
                                    if "AWS_ACCESS_KEY_ID" in token_env_vars and "AWS_SECRET_ACCESS_KEY" in token_env_vars:
                                        try:
                                            creds_path, config_path = create_aws_credentials_file(
                                                access_key_id=token_env_vars["AWS_ACCESS_KEY_ID"],
                                                secret_access_key=token_env_vars["AWS_SECRET_ACCESS_KEY"],
                                                session_token=token_env_vars.get("AWS_SESSION_TOKEN"),
                                                region=token_env_vars.get("AWS_REGION"),
                                            )
                                            # Set AWS file locations
                                            resolved_env_vars["AWS_SHARED_CREDENTIALS_FILE"] = creds_path
                                            resolved_env_vars["AWS_CONFIG_FILE"] = config_path
                                        except Exception as e:
                                            logger.warning(
                                                "aws_credentials_file_creation_failed",
                                                error=str(e),
                                            )

                                # Handle Kubernetes kubeconfig file creation
                                elif integration_type == "kubernetes" and "KUBECONFIG_CONTENT" in token_env_vars:
                                    try:
                                        kubeconfig_path = create_kubeconfig_file(
                                            token_env_vars["KUBECONFIG_CONTENT"]
                                        )
                                        resolved_env_vars["KUBECONFIG"] = kubeconfig_path
                                        # Remove content from env vars, keep only path
                                        del token_env_vars["KUBECONFIG_CONTENT"]
                                    except Exception as e:
                                        logger.warning(
                                            "kubeconfig_file_creation_failed",
                                            error=str(e),
                                        )

                                # Add all resolved env vars
                                resolved_env_vars.update(token_env_vars)

                                # Track integration for context
                                resolved_integrations.append({
                                    "integration_type": integration_type,
                                    "name": integration_name,
                                    "env_vars": list(token_env_vars.keys()),
                                })

                                logger.debug(
                                    "integration_resolved",
                                    agent_id=agent_id[:8],
                                    integration_id=integration_id[:8],
                                    integration_type=integration_type,
                                    env_var_count=len(token_env_vars),
                                )
                            except Exception as e:
                                logger.error(
                                    "integration_resolution_error",
                                    agent_id=agent_id[:8],
                                    integration_id=integration_id[:8],
                                    error=str(e),
                                )

        # Resolve custom integrations
        custom_integration_ids = execution_environment.get("custom_integration_ids", [])
        custom_integration_files = []  # Track files to be created

        for custom_integration_id in custom_integration_ids:
            try:
                result = await resolve_custom_integration(
                    custom_integration_id=custom_integration_id,
                    org_id=org_id,
                    db=db,
                    kubiya_token=kubiya_token,
                )

                # Add resolved env vars
                resolved_env_vars.update(result["env_vars"])

                # Track files to be created
                custom_integration_files.extend(result["files"])

                # Track integration for context
                resolved_integrations.append({
                    "integration_type": result.get("integration_type", "custom"),
                    "name": result.get("name", "Custom Integration"),
                    "env_vars": list(result["env_vars"].keys()),
                    "custom_context": result.get("context_prompt"),
                })

                logger.debug(
                    "custom_integration_resolved",
                    agent_id=agent_id[:8],
                    custom_integration_id=custom_integration_id[:8],
                    env_var_count=len(result["env_vars"]),
                    file_count=len(result["files"]),
                )
            except Exception as e:
                logger.error(
                    "custom_integration_resolution_error",
                    agent_id=agent_id[:8],
                    custom_integration_id=custom_integration_id[:8],
                    error=str(e),
                )
                # Continue with other custom integrations even if one fails

        # Build complete config to resolve templates
        complete_config = {
            "system_prompt": agent_configuration.get("system_prompt"),
            "description": agent.description,
            "configuration": agent_configuration,
            "mcp_servers": execution_environment.get("mcp_servers", {}),
            "env_vars": execution_environment.get("env_vars", {}),
        }

        # Apply template resolution to ENTIRE config
        resolved_config = apply_template_resolution(
            complete_config, resolved_secrets, resolved_env_vars
        )

        mcp_servers_resolved = resolved_config.get("mcp_servers", {})

        # Build integration context and inject into system prompt
        integration_context = build_integration_context(resolved_integrations)
        system_prompt = resolved_config.get("system_prompt", "")

        if integration_context and system_prompt:
            # Append integration context to system prompt
            system_prompt = f"{system_prompt}\n\n{integration_context}"

        # Add memory and context graph guidance to system prompt
        memory_guidance = """

## Memory & Context Graph Tools

You have built-in persistent memory and organizational context awareness:

**Memory Tools** (use proactively):
- **store_memory(content, metadata)**: Store important facts, decisions, preferences, or context
- **recall_memory(query, limit)**: Retrieve stored memories using semantic search

**Context Graph** (discover organizational data):
- **search_nodes(label, property_name, property_value)**: Find resources by type and properties
- **search_by_text(property_name, search_text)**: Text search across the graph
- **get_node(node_id)**: Get detailed information about a specific resource

**Best Practices**:
- Store user preferences, task decisions, and important context as you learn them
- Use recall_memory at the start of tasks to check for relevant past context
- Search the graph to discover infrastructure, services, and relationships
- Add descriptive metadata when storing memories for better retrieval"""

        if system_prompt:
            system_prompt = f"{system_prompt}\n{memory_guidance}"
        else:
            system_prompt = memory_guidance.strip()

        # Get context graph API URL from settings for memory tools
        from control_plane_api.app.config import settings
        graph_api_url = settings.context_graph_api_base
        dataset_name = environment_names[0] if environment_names else "default"

        # Inject memory dataset name into env vars
        # Worker skills will fetch graph URL from control plane's /api/v1/client/config endpoint
        resolved_env_vars["MEMORY_DATASET_NAME"] = dataset_name

        logger.info(
            "agent_execution_environment_resolved",
            agent_id=agent_id[:8],
            env_var_count=len(resolved_env_vars),
            mcp_server_count=len(mcp_servers_resolved),
            mcp_server_names=list(mcp_servers_resolved.keys()),
            secrets_count=len(resolved_secrets),
            integrations_count=len(resolved_integrations),
            custom_integration_files_count=len(custom_integration_files),
            graph_api_url=graph_api_url,
            dataset_name=dataset_name,
        )

        return {
            "env_vars": resolved_env_vars,
            "mcp_servers": mcp_servers_resolved,
            "system_prompt": system_prompt,
            "description": resolved_config.get("description"),
            "configuration": resolved_config.get("configuration", {}),
            "files": custom_integration_files,
            # Context graph configuration for memory tools
            "graph_api_url": graph_api_url,
            "dataset_name": dataset_name,
        }

    except ExecutionEnvironmentResolutionError:
        raise
    except Exception as e:
        logger.error(
            "agent_execution_environment_resolution_error",
            agent_id=agent_id[:8],
            error=str(e),
            exc_info=True,
        )
        raise ExecutionEnvironmentResolutionError(
            f"Failed to resolve execution environment for agent {agent_id}: {str(e)}"
        )


async def resolve_team_execution_environment(
    team_id: str,
    org_id: str,
    db: Session,
    kubiya_token: str = None,
) -> Dict[str, Any]:
    """
    Resolve complete execution environment for a team.

    Similar to resolve_agent_execution_environment but for teams.

    Args:
        team_id: Team UUID
        org_id: Organization ID
        db: Database session
        kubiya_token: Kubiya API token for secret/integration resolution (optional, uses env var if not provided)

    Returns:
        Dict with resolved execution environment

    Raises:
        ExecutionEnvironmentResolutionError: If team not found or resolution fails
    """
    try:
        # Use environment KUBIYA_API_KEY if token not provided
        import os
        if not kubiya_token:
            kubiya_token = os.environ.get("KUBIYA_API_KEY")
            if not kubiya_token:
                logger.warning(
                    "kubiya_api_key_not_available",
                    team_id=team_id[:8],
                    note="Secrets and integrations will not be resolved"
                )
        # Fetch team with configuration fields
        team = (
            db.query(Team)
            .filter(Team.id == team_id, Team.organization_id == org_id)
            .first()
        )

        if not team:
            raise ExecutionEnvironmentResolutionError(
                f"Team {team_id} not found in organization {org_id}"
            )

        # Get environment-level configs
        environment_ids = team.environment_ids or []

        # Fetch environment names for dataset scoping
        environment_names = []
        if environment_ids:
            environments = (
                db.query(Environment)
                .filter(Environment.id.in_(environment_ids))
                .all()
            )
            environment_names = [env.name for env in environments]

        env_config = await resolve_environment_configs(environment_ids, org_id, db)

        # Get team-level config
        team_exec_env = team.execution_environment or {}

        # Merge: environment config + team config (team overrides environment)
        execution_environment = {
            "env_vars": {
                **env_config.get("env_vars", {}),
                **team_exec_env.get("env_vars", {}),
            },
            "secrets": list(
                set(env_config.get("secrets", []) + team_exec_env.get("secrets", []))
            ),
            "integration_ids": list(
                set(
                    env_config.get("integration_ids", [])
                    + team_exec_env.get("integration_ids", [])
                )
            ),
            "mcp_servers": {
                **env_config.get("mcp_servers", {}),
                **team_exec_env.get("mcp_servers", {}),
            },
        }

        # Start with custom env vars
        resolved_env_vars = dict(execution_environment.get("env_vars", {}))
        resolved_secrets = {}
        resolved_integrations = []  # Track resolved integrations for context

        # Add KUBIYA_API_KEY to resolved_env_vars for template resolution
        # This allows MCP server configs to use {{KUBIYA_API_KEY}} templates
        kubiya_api_key_from_env = os.environ.get("KUBIYA_API_KEY")
        if kubiya_api_key_from_env:
            resolved_env_vars["KUBIYA_API_KEY"] = kubiya_api_key_from_env

        # Resolve secrets
        secrets = execution_environment.get("secrets", [])
        for secret_name in secrets:
            try:
                secret_value = await resolve_secret_value(
                    secret_name, kubiya_token, org_id
                )
                resolved_env_vars[secret_name] = secret_value
                resolved_secrets[secret_name] = secret_value
                logger.debug(
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

        # Resolve integrations
        integration_ids = execution_environment.get("integration_ids", [])
        if integration_ids:
            headers = {
                "Authorization": f"UserKey {kubiya_token}",
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
                        integration = next(
                            (
                                i
                                for i in all_integrations
                                if i.get("uuid") == integration_id
                            ),
                            None,
                        )

                        if integration:
                            integration_type = integration.get("integration_type", "")
                            integration_name = integration.get("name", integration_type)
                            try:
                                token_env_vars = await resolve_integration_token(
                                    integration_id,
                                    integration_type,
                                    kubiya_token,
                                    org_id,
                                )

                                # Handle AWS credentials file creation
                                if integration_type in ["aws", "aws-serviceaccount"] and token_env_vars:
                                    if "AWS_ACCESS_KEY_ID" in token_env_vars and "AWS_SECRET_ACCESS_KEY" in token_env_vars:
                                        try:
                                            creds_path, config_path = create_aws_credentials_file(
                                                access_key_id=token_env_vars["AWS_ACCESS_KEY_ID"],
                                                secret_access_key=token_env_vars["AWS_SECRET_ACCESS_KEY"],
                                                session_token=token_env_vars.get("AWS_SESSION_TOKEN"),
                                                region=token_env_vars.get("AWS_REGION"),
                                            )
                                            resolved_env_vars["AWS_SHARED_CREDENTIALS_FILE"] = creds_path
                                            resolved_env_vars["AWS_CONFIG_FILE"] = config_path
                                        except Exception as e:
                                            logger.warning(
                                                "aws_credentials_file_creation_failed",
                                                error=str(e),
                                            )

                                # Handle Kubernetes kubeconfig file creation
                                elif integration_type == "kubernetes" and "KUBECONFIG_CONTENT" in token_env_vars:
                                    try:
                                        kubeconfig_path = create_kubeconfig_file(
                                            token_env_vars["KUBECONFIG_CONTENT"]
                                        )
                                        resolved_env_vars["KUBECONFIG"] = kubeconfig_path
                                        del token_env_vars["KUBECONFIG_CONTENT"]
                                    except Exception as e:
                                        logger.warning(
                                            "kubeconfig_file_creation_failed",
                                            error=str(e),
                                        )

                                resolved_env_vars.update(token_env_vars)

                                # Track integration for context
                                resolved_integrations.append({
                                    "integration_type": integration_type,
                                    "name": integration_name,
                                    "env_vars": list(token_env_vars.keys()),
                                })

                                logger.debug(
                                    "integration_resolved",
                                    team_id=team_id[:8],
                                    integration_id=integration_id[:8],
                                    integration_type=integration_type,
                                    env_var_count=len(token_env_vars),
                                )
                            except Exception as e:
                                logger.error(
                                    "integration_resolution_error",
                                    team_id=team_id[:8],
                                    integration_id=integration_id[:8],
                                    error=str(e),
                                )

        # Build complete config to resolve templates
        complete_config = {
            "instructions": (
                team.configuration.get("instructions") if team.configuration else None
            ),
            "description": team.description,
            "configuration": team.configuration or {},
            "mcp_servers": execution_environment.get("mcp_servers", {}),
            "env_vars": execution_environment.get("env_vars", {}),
        }

        # Apply template resolution to ENTIRE config
        resolved_config = apply_template_resolution(
            complete_config, resolved_secrets, resolved_env_vars
        )

        # Build integration context and inject into instructions
        integration_context = build_integration_context(resolved_integrations)
        instructions = resolved_config.get("instructions", "")

        if integration_context and instructions:
            # Append integration context to instructions
            instructions = f"{instructions}\n\n{integration_context}"

        # Add memory and context graph guidance to instructions
        memory_guidance = """

## Memory & Context Graph Tools

You have built-in persistent memory and organizational context awareness:

**Memory Tools** (use proactively):
- **store_memory(content, metadata)**: Store important facts, decisions, preferences, or context
- **recall_memory(query, limit)**: Retrieve stored memories using semantic search

**Context Graph** (discover organizational data):
- **search_nodes(label, property_name, property_value)**: Find resources by type and properties
- **search_by_text(property_name, search_text)**: Text search across the graph
- **get_node(node_id)**: Get detailed information about a specific resource

**Best Practices**:
- Store user preferences, task decisions, and important context as you learn them
- Use recall_memory at the start of tasks to check for relevant past context
- Search the graph to discover infrastructure, services, and relationships
- Add descriptive metadata when storing memories for better retrieval"""

        if instructions:
            instructions = f"{instructions}\n{memory_guidance}"
        else:
            instructions = memory_guidance.strip()

        # Get context graph API URL from settings for memory tools
        from control_plane_api.app.config import settings
        graph_api_url = settings.context_graph_api_base
        dataset_name = environment_names[0] if environment_names else "default"

        # Inject memory dataset name into env vars
        # Worker skills will fetch graph URL from control plane's /api/v1/client/config endpoint
        resolved_env_vars["MEMORY_DATASET_NAME"] = dataset_name

        logger.info(
            "team_execution_environment_resolved",
            team_id=team_id[:8],
            env_var_count=len(resolved_env_vars),
            mcp_server_count=len(resolved_config.get("mcp_servers", {})),
            secrets_count=len(resolved_secrets),
            integrations_count=len(resolved_integrations),
            graph_api_url=graph_api_url,
            dataset_name=dataset_name,
        )

        return {
            "env_vars": resolved_env_vars,
            "mcp_servers": resolved_config.get("mcp_servers", {}),
            "instructions": instructions,
            "description": resolved_config.get("description"),
            "configuration": resolved_config.get("configuration", {}),
            # Context graph configuration for memory tools
            "graph_api_url": graph_api_url,
            "dataset_name": dataset_name,
        }

    except ExecutionEnvironmentResolutionError:
        raise
    except Exception as e:
        logger.error(
            "team_execution_environment_resolution_error",
            team_id=team_id[:8],
            error=str(e),
            exc_info=True,
        )
        raise ExecutionEnvironmentResolutionError(
            f"Failed to resolve execution environment for team {team_id}: {str(e)}"
        )
