"""
Integration Resolution Service

Handles resolution of custom integrations to execution environment configuration.
Includes secret resolution, file preparation, and context building.
"""
from typing import Dict, Any, List, Optional
import httpx
import structlog

from control_plane_api.app.config import settings

logger = structlog.get_logger(__name__)


class IntegrationResolutionService:
    """
    Service for resolving custom integrations to execution environment.

    Handles:
    - Environment variable extraction
    - Secret resolution from vault
    - File content preparation
    - Context prompt building
    """

    def __init__(self, kubiya_token: str, org_id: str):
        """
        Initialize the resolution service.

        Args:
            kubiya_token: Kubiya API token for secret resolution
            org_id: Organization ID
        """
        self.kubiya_token = kubiya_token
        self.org_id = org_id
        self.kubiya_api_base = settings.KUBIYA_API_BASE

    async def resolve_secret(self, secret_name: str) -> str:
        """
        Resolve a secret name to its actual value from Kubiya API.

        Args:
            secret_name: Name of the secret to resolve

        Returns:
            Secret value as string

        Raises:
            ValueError: If secret resolution fails
        """
        headers = {
            "Authorization": f"UserKey {self.kubiya_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Kubiya-Client": "agent-control-plane",
            "X-Organization-ID": self.org_id,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.kubiya_api_base}/api/v2/secrets/get_value/{secret_name}",
                headers=headers,
            )

            if response.status_code == 200:
                logger.debug(
                    "secret_resolved",
                    secret_name=secret_name[:20],
                    org_id=self.org_id[:8]
                )
                return response.text
            else:
                logger.error(
                    "secret_resolution_failed",
                    secret_name=secret_name[:20],
                    status=response.status_code,
                    org_id=self.org_id[:8]
                )
                raise ValueError(
                    f"Failed to resolve secret '{secret_name}': {response.text[:200]}"
                )

    async def resolve_integration_config(
        self,
        config: Dict[str, Any],
        integration_name: str = "custom"
    ) -> Dict[str, Any]:
        """
        Resolve custom integration configuration to execution environment.

        Args:
            config: Integration configuration dict
            integration_name: Name of the integration (for logging)

        Returns:
            Dictionary with:
            - env_vars: Resolved environment variables
            - files: Prepared file configurations
            - context_prompt: Context guidance for agent
        """
        resolved_env_vars = {}
        files_to_create = []

        # Extract direct environment variables
        env_vars = config.get("env_vars", {})
        resolved_env_vars.update(env_vars)

        # Resolve secrets to environment variables
        secrets = config.get("secrets", [])
        for secret_name in secrets:
            try:
                secret_value = await self.resolve_secret(secret_name)
                resolved_env_vars[secret_name] = secret_value
                logger.debug(
                    "integration_secret_resolved",
                    integration_name=integration_name,
                    secret_name=secret_name[:20]
                )
            except Exception as e:
                logger.error(
                    "integration_secret_resolution_error",
                    integration_name=integration_name,
                    secret_name=secret_name[:20],
                    error=str(e)
                )
                # Continue with other secrets even if one fails

        # Prepare files
        files_config = config.get("files", [])
        for file_config in files_config:
            file_path = file_config.get("path")
            content = file_config.get("content")
            secret_ref = file_config.get("secret_ref")
            mode = file_config.get("mode", "0644")

            if not file_path:
                logger.warning(
                    "integration_file_missing_path",
                    integration_name=integration_name
                )
                continue

            # Resolve content from secret if needed
            if secret_ref and not content:
                try:
                    content = await self.resolve_secret(secret_ref)
                    logger.debug(
                        "integration_file_secret_resolved",
                        integration_name=integration_name,
                        file_path=file_path,
                        secret_ref=secret_ref[:20]
                    )
                except Exception as e:
                    logger.error(
                        "integration_file_secret_error",
                        integration_name=integration_name,
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
            else:
                logger.warning(
                    "integration_file_no_content",
                    integration_name=integration_name,
                    file_path=file_path
                )

        context_prompt = config.get("context_prompt")

        logger.info(
            "integration_config_resolved",
            integration_name=integration_name,
            env_var_count=len(resolved_env_vars),
            file_count=len(files_to_create),
            has_context=bool(context_prompt)
        )

        return {
            "env_vars": resolved_env_vars,
            "files": files_to_create,
            "context_prompt": context_prompt
        }

    @staticmethod
    def build_integration_context(
        resolved_integrations: List[Dict[str, Any]]
    ) -> str:
        """
        Build integration context information for injection into system prompt.

        Args:
            resolved_integrations: List of resolved integration metadata with:
                - integration_type: Type of integration
                - name: Integration name
                - env_vars: List of environment variable names
                - custom_context: Optional custom context prompt

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
                context_parts.append(
                    f"- Available environment variables: {', '.join(env_vars)}"
                )

            # Add custom context if provided
            if custom_context:
                context_parts.append(f"- {custom_context}")

            # Add integration-specific guidance
            context_parts.extend(
                IntegrationResolutionService._get_integration_guidance(integration_type)
            )

        return "\n".join(context_parts)

    @staticmethod
    def _get_integration_guidance(integration_type: str) -> List[str]:
        """
        Get default guidance for known integration types.

        Args:
            integration_type: Type of integration

        Returns:
            List of guidance strings
        """
        guidance_map = {
            "postgres": [
                "- PostgreSQL database. Use parameterized queries to prevent SQL injection.",
                "- Connection pooling is recommended for better performance."
            ],
            "mysql": [
                "- MySQL database. Use transactions for data consistency.",
                "- Avoid SELECT * in production queries."
            ],
            "mongodb": [
                "- MongoDB NoSQL database. Use connection pooling.",
                "- Always use indexes for query optimization."
            ],
            "redis": [
                "- Redis in-memory cache. All keys have TTL.",
                "- Use for session storage, caching, and rate limiting."
            ],
            "elasticsearch": [
                "- Elasticsearch for full-text search and analytics.",
                "- Use bulk API for large datasets."
            ],
            "api": [
                "- REST API integration. Always check rate limits.",
                "- Use exponential backoff for retries."
            ]
        }

        return guidance_map.get(integration_type, [])

    async def resolve_multiple_integrations(
        self,
        integrations_config: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Resolve multiple custom integrations.

        Args:
            integrations_config: List of integration configs, each with:
                - name: Integration name
                - integration_type: Integration type
                - config: Integration configuration dict

        Returns:
            Combined resolution result with:
            - env_vars: Merged environment variables from all integrations
            - files: Combined files from all integrations
            - resolved_integrations: Metadata for context building
        """
        all_env_vars = {}
        all_files = []
        resolved_integrations = []

        for integ_data in integrations_config:
            name = integ_data.get("name", "unknown")
            integration_type = integ_data.get("integration_type", "unknown")
            config = integ_data.get("config", {})

            try:
                result = await self.resolve_integration_config(config, name)

                # Merge env vars (later integrations override earlier ones)
                all_env_vars.update(result["env_vars"])

                # Append files
                all_files.extend(result["files"])

                # Track for context
                resolved_integrations.append({
                    "integration_type": integration_type,
                    "name": name,
                    "env_vars": list(result["env_vars"].keys()),
                    "custom_context": result.get("context_prompt")
                })

            except Exception as e:
                logger.error(
                    "integration_resolution_failed",
                    integration_name=name,
                    error=str(e)
                )
                # Continue with other integrations

        logger.info(
            "multiple_integrations_resolved",
            count=len(integrations_config),
            successful=len(resolved_integrations),
            total_env_vars=len(all_env_vars),
            total_files=len(all_files)
        )

        return {
            "env_vars": all_env_vars,
            "files": all_files,
            "resolved_integrations": resolved_integrations
        }
