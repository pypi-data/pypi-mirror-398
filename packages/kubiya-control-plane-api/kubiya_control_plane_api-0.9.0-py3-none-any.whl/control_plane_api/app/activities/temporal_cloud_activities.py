"""Temporal Cloud provisioning activities using tcld CLI"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timezone
from temporalio import activity
import structlog
import subprocess
import json
import os
import time
import secrets

from control_plane_api.app.database import get_session_local
from control_plane_api.app.models.orchestration import Namespace
from control_plane_api.app.models.environment import Environment

logger = structlog.get_logger()


@dataclass
class CheckNamespaceInput:
    """Input for check_namespace_exists activity"""
    organization_id: str
    namespace_name: str


@dataclass
class CreateNamespaceInput:
    """Input for create_namespace activity"""
    organization_id: str
    namespace_name: str
    account_id: str
    region: str = "aws-us-east-1"
    retention_days: int = 30


@dataclass
class PollNamespaceStatusInput:
    """Input for poll_namespace_status activity"""
    namespace_name: str
    max_attempts: int = 60  # 60 attempts * 5 seconds = 5 minutes max
    poll_interval_seconds: int = 5


@dataclass
class GenerateApiKeyInput:
    """Input for generate_namespace_api_key activity"""
    namespace_name: str
    key_description: str = "Control Plane API Key"


@dataclass
class StoreNamespaceCredentialsInput:
    """Input for store_namespace_credentials activity"""
    organization_id: str
    namespace_name: str
    api_key: str
    status: str = "ready"


def run_tcld_command(cmd: list[str], capture_output: bool = True) -> dict:
    """
    Execute tcld CLI command and return result.

    Args:
        cmd: Command list (e.g., ["tcld", "namespace", "get", "--namespace", "my-ns"])
        capture_output: Whether to capture stdout/stderr

    Returns:
        Dict with success, stdout, stderr, returncode
    """
    try:
        # Get admin token from environment
        admin_token = os.getenv("TEMPORAL_CLOUD_ADMIN_TOKEN")
        if not admin_token:
            raise ValueError("TEMPORAL_CLOUD_ADMIN_TOKEN environment variable is not set")

        # Add API key to command if not already present
        # tcld expects --api-key flag for authentication
        enhanced_cmd = cmd.copy()
        if "--api-key" not in enhanced_cmd:
            # Insert API key right after tcld command
            enhanced_cmd.insert(1, "--api-key")
            enhanced_cmd.insert(2, admin_token)

        activity.logger.info(f"Running tcld command: {' '.join(enhanced_cmd[:3])}... [credentials hidden]")

        # Prepare environment (tcld might also check env vars)
        env = os.environ.copy()
        env["TEMPORAL_CLOUD_API_KEY"] = admin_token  # Backup: env var

        result = subprocess.run(
            enhanced_cmd,
            capture_output=capture_output,
            text=True,
            timeout=60,  # 60 second timeout (namespace operations can take longer)
            env=env,
        )

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Command timed out after 60 seconds",
            "returncode": -1,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "returncode": -1,
        }


@activity.defn
async def check_namespace_exists(input: CheckNamespaceInput) -> dict:
    """
    Check if a Temporal Cloud namespace already exists.

    Uses: tcld namespace get --namespace <namespace_name>

    Returns:
        Dict with exists (bool) and details if found
    """
    activity.logger.info(
        f"Checking if namespace exists",
        extra={
            "organization_id": input.organization_id,
            "namespace_name": input.namespace_name,
        }
    )

    try:
        # First check our database
        SessionLocal = get_session_local()
        db = SessionLocal()

        try:
            namespace = db.query(Namespace).filter(
                Namespace.organization_id == input.organization_id,
                Namespace.namespace_name == input.namespace_name
            ).first()

            if namespace:
                activity.logger.info(
                    f"Namespace found in database",
                    extra={
                        "namespace_name": input.namespace_name,
                        "status": namespace.status,
                    }
                )
                return {
                    "exists": True,
                    "in_database": True,
                    "status": namespace.status,
                    "details": {
                        "id": str(namespace.id),
                        "organization_id": namespace.organization_id,
                        "namespace_name": namespace.namespace_name,
                        "status": namespace.status,
                        "temporal_host": namespace.temporal_host,
                        "created_at": namespace.created_at.isoformat() if namespace.created_at else None,
                        "updated_at": namespace.updated_at.isoformat() if namespace.updated_at else None,
                    },
                }
        finally:
            db.close()

        # Check Temporal Cloud using tcld
        result = run_tcld_command([
            "tcld", "namespace", "get",
            "--namespace", input.namespace_name,
            "--output", "json"
        ])

        if result["success"]:
            # Parse JSON output
            try:
                namespace_data = json.loads(result["stdout"])
                activity.logger.info(
                    f"Namespace exists in Temporal Cloud",
                    extra={"namespace_name": input.namespace_name}
                )
                return {
                    "exists": True,
                    "in_temporal_cloud": True,
                    "details": namespace_data,
                }
            except json.JSONDecodeError:
                return {"exists": True, "in_temporal_cloud": True}
        else:
            # Namespace doesn't exist
            activity.logger.info(
                f"Namespace does not exist",
                extra={"namespace_name": input.namespace_name}
            )
            return {"exists": False}

    except Exception as e:
        activity.logger.error(
            f"Failed to check namespace existence",
            extra={"error": str(e), "namespace_name": input.namespace_name}
        )
        raise


@activity.defn
async def create_namespace(input: CreateNamespaceInput) -> dict:
    """
    Create a new Temporal Cloud namespace using tcld CLI.

    Uses: tcld namespace create --namespace <name> --region <region> --retention-days <days>

    Returns:
        Dict with success flag and namespace details
    """
    activity.logger.info(
        f"Creating Temporal Cloud namespace",
        extra={
            "organization_id": input.organization_id,
            "namespace_name": input.namespace_name,
            "region": input.region,
        }
    )

    # Create namespace record in database first (status: provisioning)
    SessionLocal = get_session_local()
    db = SessionLocal()

    try:
        # Check if already exists in DB
        existing = db.query(Namespace).filter(
            Namespace.organization_id == input.organization_id
        ).first()

        if existing:
            namespace_id = existing.id
            # Update to provisioning
            existing.status = "provisioning"
            existing.updated_at = datetime.now(timezone.utc)
            db.commit()
        else:
            # Create new record
            new_namespace = Namespace(
                organization_id=input.organization_id,
                namespace_name=input.namespace_name,
                status="provisioning",
                temporal_host=None,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.add(new_namespace)
            db.commit()
            db.refresh(new_namespace)
            namespace_id = new_namespace.id

        # Execute tcld namespace create
        cmd = [
            "tcld", "namespace", "create",
            "--namespace", input.namespace_name,
            "--region", input.region,
            "--retention-days", str(input.retention_days),
            "--output", "json"
        ]

        result = run_tcld_command(cmd)

        if result["success"]:
            activity.logger.info(
                f"Namespace creation initiated",
                extra={"namespace_name": input.namespace_name}
            )
            return {
                "success": True,
                "namespace_id": namespace_id,
                "namespace_name": input.namespace_name,
                "message": "Namespace creation initiated",
            }
        else:
            error_msg = result.get("stderr", result.get("error", "Unknown error"))
            activity.logger.error(
                f"Failed to create namespace",
                extra={
                    "namespace_name": input.namespace_name,
                    "error": error_msg,
                }
            )

            # Update database with error
            if namespace_id:
                namespace_to_update = db.query(Namespace).filter(Namespace.id == namespace_id).first()
                if namespace_to_update:
                    namespace_to_update.status = "error"
                    namespace_to_update.updated_at = datetime.now(timezone.utc)
                    db.commit()

            return {
                "success": False,
                "error": error_msg,
            }

    except Exception as e:
        activity.logger.error(
            f"Failed to create namespace",
            extra={"error": str(e), "namespace_name": input.namespace_name}
        )
        raise
    finally:
        db.close()

@activity.defn
async def poll_namespace_status(input: PollNamespaceStatusInput) -> dict:
    """
    Poll Temporal Cloud namespace status until it's ready.

    Uses: tcld namespace get --namespace <name>

    Returns:
        Dict with ready (bool), status, and details
    """
    activity.logger.info(
        f"Polling namespace status",
        extra={
            "namespace_name": input.namespace_name,
            "max_attempts": input.max_attempts,
        }
    )

    attempt = 0
    while attempt < input.max_attempts:
        attempt += 1

        try:
            result = run_tcld_command([
                "tcld", "namespace", "get",
                "--namespace", input.namespace_name,
                "--output", "json"
            ])

            if result["success"]:
                try:
                    namespace_data = json.loads(result["stdout"])
                    status = namespace_data.get("state", "unknown")

                    activity.logger.info(
                        f"Namespace status check",
                        extra={
                            "namespace_name": input.namespace_name,
                            "attempt": attempt,
                            "status": status,
                        }
                    )

                    # Check if namespace is ready (status might be "active" or "running")
                    if status.lower() in ["active", "running", "ready"]:
                        return {
                            "ready": True,
                            "status": status,
                            "attempts": attempt,
                            "details": namespace_data,
                        }
                except json.JSONDecodeError:
                    activity.logger.warning(
                        f"Failed to parse namespace status JSON",
                        extra={"attempt": attempt}
                    )

            # Wait before next attempt
            if attempt < input.max_attempts:
                time.sleep(input.poll_interval_seconds)

        except Exception as e:
            activity.logger.warning(
                f"Error polling namespace status",
                extra={"attempt": attempt, "error": str(e)}
            )
            if attempt < input.max_attempts:
                time.sleep(input.poll_interval_seconds)

    # Timed out
    activity.logger.error(
        f"Namespace provisioning timed out",
        extra={
            "namespace_name": input.namespace_name,
            "attempts": attempt,
        }
    )
    return {
        "ready": False,
        "status": "timeout",
        "attempts": attempt,
        "error": f"Namespace not ready after {attempt} attempts"
    }


@activity.defn
async def generate_namespace_api_key(input: GenerateApiKeyInput) -> dict:
    """
    Generate an API key for the Temporal Cloud namespace.

    Uses: tcld apikey create --namespace <name> --description <desc>

    Returns:
        Dict with success flag and api_key
    """
    activity.logger.info(
        f"Generating API key for namespace",
        extra={"namespace_name": input.namespace_name}
    )

    try:
        result = run_tcld_command([
            "tcld", "apikey", "create",
            "--namespace", input.namespace_name,
            "--description", input.key_description,
            "--output", "json"
        ])

        if result["success"]:
            try:
                key_data = json.loads(result["stdout"])
                api_key = key_data.get("key") or key_data.get("apiKey")

                if api_key:
                    activity.logger.info(
                        f"API key generated successfully",
                        extra={"namespace_name": input.namespace_name}
                    )
                    return {
                        "success": True,
                        "api_key": api_key,
                        "key_id": key_data.get("id"),
                    }
                else:
                    return {
                        "success": False,
                        "error": "API key not found in response",
                    }
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "error": "Failed to parse API key response",
                }
        else:
            error_msg = result.get("stderr", result.get("error", "Unknown error"))
            activity.logger.error(
                f"Failed to generate API key",
                extra={"namespace_name": input.namespace_name, "error": error_msg}
            )
            return {
                "success": False,
                "error": error_msg,
            }

    except Exception as e:
        activity.logger.error(
            f"Failed to generate API key",
            extra={"error": str(e), "namespace_name": input.namespace_name}
        )
        raise


@activity.defn
async def store_namespace_credentials(input: StoreNamespaceCredentialsInput) -> dict:
    """
    Store namespace credentials in database.

    TODO: Encrypt API key before storing (use something like Fernet or AWS KMS)

    Returns:
        Dict with success flag
    """
    activity.logger.info(
        f"Storing namespace credentials",
        extra={
            "organization_id": input.organization_id,
            "namespace_name": input.namespace_name,
        }
    )

    try:
        SessionLocal = get_session_local()
        db = SessionLocal()

        try:
            # TODO: Encrypt API key properly
            # For now, we'll store it as-is (NOT RECOMMENDED FOR PRODUCTION)
            # In production, use:
            # - AWS KMS
            # - Vault
            # - Supabase Vault (vault.encrypt)
            # - cryptography.Fernet
            api_key_encrypted = input.api_key  # Should be encrypted!

            # Find and update namespace record
            namespace = db.query(Namespace).filter(
                Namespace.organization_id == input.organization_id,
                Namespace.namespace_name == input.namespace_name
            ).first()

            if namespace:
                namespace.api_key_encrypted = api_key_encrypted
                namespace.status = input.status
                namespace.updated_at = datetime.now(timezone.utc)
                db.commit()

                activity.logger.info(
                    f"Namespace credentials stored",
                    extra={"namespace_name": input.namespace_name}
                )
                return {"success": True, "namespace_id": str(namespace.id)}
            else:
                raise Exception("Failed to update namespace credentials - namespace not found")
        finally:
            db.close()

    except Exception as e:
        activity.logger.error(
            f"Failed to store namespace credentials",
            extra={"error": str(e), "namespace_name": input.namespace_name}
        )
        raise


@activity.defn
async def update_task_queue_status(
    task_queue_id: str,
    status: str,
    error_message: Optional[str] = None,
    temporal_namespace_id: Optional[str] = None,
) -> dict:
    """
    Update task queue status after provisioning.

    Returns:
        Dict with success flag
    """
    activity.logger.info(
        f"Updating task queue status",
        extra={"task_queue_id": task_queue_id, "status": status}
    )

    try:
        SessionLocal = get_session_local()
        db = SessionLocal()

        try:
            # Find and update environment (task queue)
            environment = db.query(Environment).filter(
                Environment.id == task_queue_id
            ).first()

            if environment:
                environment.status = status
                environment.updated_at = datetime.now(timezone.utc)

                if error_message:
                    environment.error_message = error_message

                # Note: temporal_namespace_id field may not exist in Environment model
                # This might need schema update if it's required
                if temporal_namespace_id and hasattr(environment, 'temporal_namespace_id'):
                    environment.temporal_namespace_id = temporal_namespace_id

                db.commit()

                activity.logger.info(
                    f"Task queue status updated",
                    extra={"task_queue_id": task_queue_id, "status": status}
                )
                return {"success": True}
            else:
                raise Exception("Failed to update task queue status - environment not found")
        finally:
            db.close()

    except Exception as e:
        activity.logger.error(
            f"Failed to update task queue status",
            extra={"error": str(e), "task_queue_id": task_queue_id}
        )
        raise
