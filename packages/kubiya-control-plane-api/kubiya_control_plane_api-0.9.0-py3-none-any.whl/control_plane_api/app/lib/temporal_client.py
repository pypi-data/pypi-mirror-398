"""Temporal client for Agent Control Plane API"""

import os
from pathlib import Path
from typing import Optional
import structlog
from temporalio.client import Client, TLSConfig

logger = structlog.get_logger()

_temporal_client: Optional[Client] = None


async def get_temporal_client() -> Client:
    """
    Get or create Temporal client singleton.

    DEPRECATED: This uses shared admin credentials from env vars.
    For org-specific credentials, use get_temporal_client_for_org() instead.

    Supports mTLS authentication for Temporal Cloud.
    This client is used by the API to submit workflows.

    Returns:
        Temporal client instance
    """
    global _temporal_client

    if _temporal_client is not None:
        return _temporal_client

    # Get Temporal configuration with defaults matching worker_queues.py
    temporal_host = os.environ.get("TEMPORAL_HOST", "us-east-1.aws.api.temporal.io:7233")
    temporal_namespace = os.environ.get("TEMPORAL_NAMESPACE", "agent-control-plane.lpagu")
    # Check for API key in multiple possible env var names
    temporal_api_key = (
        os.environ.get("TEMPORAL_API_KEY") or
        os.environ.get("TEMPORAL_CLOUD_ADMIN_TOKEN")
    )
    # Strip whitespace and newlines from all env vars (common issue with env vars)
    if temporal_host:
        temporal_host = temporal_host.strip()
    if temporal_namespace:
        temporal_namespace = temporal_namespace.strip()
    if temporal_api_key:
        temporal_api_key = temporal_api_key.strip()
    temporal_cert_path = os.environ.get("TEMPORAL_CLIENT_CERT_PATH")
    temporal_key_path = os.environ.get("TEMPORAL_CLIENT_KEY_PATH")

    try:
        # Check if connecting to Temporal Cloud
        is_cloud = "tmprl.cloud" in temporal_host or "api.temporal.io" in temporal_host

        if is_cloud:
            # Check authentication method: API Key or mTLS
            if temporal_api_key:
                # API Key authentication
                logger.info("temporal_auth_method", method="api_key")

                # Connect with TLS and API key
                _temporal_client = await Client.connect(
                    temporal_host,
                    namespace=temporal_namespace,
                    tls=TLSConfig(),  # TLS without client cert
                    rpc_metadata={"authorization": f"Bearer {temporal_api_key}"}
                )
            elif temporal_cert_path:
                # mTLS authentication
                logger.info("temporal_auth_method", method="mtls")

                # Load client certificate
                cert_path = Path(temporal_cert_path)
                if not cert_path.exists():
                    raise FileNotFoundError(
                        f"Temporal client certificate not found at {cert_path}"
                    )

                with open(cert_path, "rb") as f:
                    cert_content = f.read()

                # Check if private key is in same file or separate
                if b"BEGIN PRIVATE KEY" in cert_content or b"BEGIN RSA PRIVATE KEY" in cert_content:
                    # Key is in the same file
                    client_cert = cert_content
                    client_key = cert_content
                else:
                    # Key must be in separate file
                    if not temporal_key_path:
                        raise ValueError(
                            "Private key not found in certificate file and no separate key path configured. "
                            "Please provide TEMPORAL_CLIENT_KEY_PATH environment variable."
                        )
                    key_path = Path(temporal_key_path)
                    with open(key_path, "rb") as f:
                        client_key = f.read()
                    client_cert = cert_content

                # Create TLS config for mTLS
                tls_config = TLSConfig(
                    client_cert=client_cert,
                    client_private_key=client_key,
                )

                # Connect to Temporal Cloud with mTLS
                _temporal_client = await Client.connect(
                    temporal_host,
                    namespace=temporal_namespace,
                    tls=tls_config,
                )
            else:
                raise ValueError(
                    "For Temporal Cloud connection, either TEMPORAL_API_KEY or TEMPORAL_CLIENT_CERT_PATH must be provided"
                )
        else:
            # Local Temporal server (no authentication required)
            _temporal_client = await Client.connect(
                temporal_host,
                namespace=temporal_namespace,
            )

        logger.info(
            "temporal_client_connected",
            host=temporal_host,
            namespace=temporal_namespace,
        )

        return _temporal_client

    except Exception as e:
        logger.error("temporal_client_connection_failed", error=str(e))
        raise


async def get_temporal_client_for_org(
    namespace: str,
    api_key: str,
    host: Optional[str] = None,
) -> Client:
    """
    Create Temporal client for specific organization.

    This creates a new client instance with org-specific credentials.
    Should be used for all workflow operations to ensure proper multi-tenant isolation.

    Args:
        namespace: Temporal namespace (e.g., "kubiya-ai.lpagu")
        api_key: Temporal API key for the namespace (empty for local Temporal)
        host: Temporal host (optional, uses TEMPORAL_HOST env var if not provided)

    Returns:
        Temporal client instance configured for the organization

    Raises:
        Exception: If connection fails

    Example:
        client = await get_temporal_client_for_org(
            namespace="kubiya-ai.lpagu",
            api_key="temporal-api-key-123",
            host="us-east-1.aws.api.temporal.io:7233"
        )
    """
    if not host:
        host = os.environ.get("TEMPORAL_HOST", "us-east-1.aws.api.temporal.io:7233")

    # Strip whitespace
    host = host.strip()
    namespace = namespace.strip()
    api_key = api_key.strip() if api_key else ""

    try:
        # Check if connecting to Temporal Cloud
        is_cloud = "tmprl.cloud" in host or "api.temporal.io" in host

        if is_cloud:
            if not api_key:
                raise ValueError("API key is required for Temporal Cloud")

            logger.info(
                "creating_temporal_client_for_org",
                namespace=namespace,
                host=host,
                auth_method="api_key"
            )

            # Connect with TLS and API key
            client = await Client.connect(
                host,
                namespace=namespace,
                tls=TLSConfig(),
                rpc_metadata={"authorization": f"Bearer {api_key}"}
            )
        else:
            # Local Temporal server
            logger.info(
                "creating_temporal_client_for_org",
                namespace=namespace,
                host=host,
                auth_method="none"
            )

            client = await Client.connect(
                host,
                namespace=namespace,
            )

        logger.info(
            "temporal_client_created_for_org",
            namespace=namespace,
            host=host,
        )

        return client

    except Exception as e:
        logger.error(
            "temporal_client_creation_failed",
            error=str(e),
            namespace=namespace,
            host=host
        )
        raise


async def close_temporal_client() -> None:
    """Close the Temporal client connection"""
    global _temporal_client

    if _temporal_client is not None:
        await _temporal_client.close()
        _temporal_client = None
        logger.info("temporal_client_closed")
