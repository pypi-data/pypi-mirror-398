"""NATS credentials manager for generating temporary worker credentials."""

import os
import json
from datetime import datetime, timedelta, timezone
from typing import Optional
from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger(__name__)


class WorkerCredentials(BaseModel):
    """NATS credentials for a worker."""

    jwt: str = Field(..., description="User JWT token")
    seed: str = Field(..., description="NKey seed (private key)")
    public_key: str = Field(..., description="NKey public key")
    subject_prefix: str = Field(..., description="Subject prefix for publishing")
    expires_at: datetime = Field(..., description="Credential expiration time")


class NATSCredentialsManager:
    """Generate temporary NATS credentials for workers."""

    def __init__(
        self,
        operator_jwt: str,
        operator_seed: str,
        account_public_key: Optional[str] = None,
    ):
        """
        Initialize NATS credentials manager.

        Args:
            operator_jwt: Operator JWT (not used for signing, just for reference)
            operator_seed: Operator seed for signing JWTs
            account_public_key: Optional account public key (extracted from operator JWT if not provided)
        """
        try:
            import nkeys
            import jwt as jwt_lib
        except ImportError:
            raise ImportError(
                "nkeys and PyJWT are required for NATS credentials. "
                "Install with: pip install nkeys pyjwt"
            )

        self.operator_jwt = operator_jwt
        self.operator_seed = operator_seed
        self.account_public_key = account_public_key

        # Create signing key from operator seed
        try:
            self.signing_key = nkeys.from_seed(operator_seed.encode())
            logger.info(
                "nats_credentials_manager_initialized",
                operator_key=self.signing_key.public_key.decode()[:10] + "...",
            )
        except Exception as e:
            logger.error("nats_signing_key_init_failed", error=str(e))
            raise

    def create_worker_credentials(
        self,
        worker_id: str,
        organization_id: str,
        ttl_hours: int = 24,
    ) -> WorkerCredentials:
        """
        Create temporary NATS user credentials (JWT + seed) for worker.

        Permissions:
        - Publish: events.{organization_id}.{worker_id}.>
        - Subscribe: None (workers only publish)

        Args:
            worker_id: Worker UUID
            organization_id: Organization ID
            ttl_hours: Credential time-to-live in hours

        Returns:
            WorkerCredentials with JWT and seed

        Raises:
            Exception: If credential generation fails
        """
        try:
            import nkeys
            import jwt as jwt_lib

            # Generate user nkey
            user_key = nkeys.create_user()
            user_seed = user_key.seed.decode()
            user_public_key = user_key.public_key.decode()

            # Calculate expiration
            now = datetime.now(timezone.utc)
            expires_at = now + timedelta(hours=ttl_hours)

            # Subject prefix for this worker
            subject_prefix = f"events.{organization_id}.{worker_id}"

            # Create user JWT claims
            # Reference: https://docs.nats.io/running-a-nats-service/configuration/securing_nats/jwt
            claims = {
                "jti": f"worker-{worker_id}",  # JWT ID
                "iat": int(now.timestamp()),  # Issued at
                "iss": self.signing_key.public_key.decode(),  # Issuer (operator key)
                "sub": user_public_key,  # Subject (user public key)
                "exp": int(expires_at.timestamp()),  # Expiration
                "nats": {
                    "pub": {
                        # Allow publishing to worker-specific subjects
                        "allow": [f"{subject_prefix}.>"]
                    },
                    "sub": {
                        # Workers don't subscribe
                        "allow": []
                    },
                    "subs": -1,  # Unlimited subscriptions (not used)
                    "data": -1,  # Unlimited data
                    "payload": -1,  # Unlimited payload size
                    "type": "user",
                    "version": 2,
                },
            }

            # Sign JWT with operator key using Ed25519
            # nkeys uses Ed25519, so we sign manually
            signing_input = self._encode_jwt_parts(claims)
            signature = self.signing_key.sign(signing_input)

            # Build complete JWT
            import base64

            jwt_parts = [
                base64.urlsafe_b64encode(
                    json.dumps({"typ": "JWT", "alg": "ed25519-nkey"}).encode()
                )
                .decode()
                .rstrip("="),
                base64.urlsafe_b64encode(json.dumps(claims).encode())
                .decode()
                .rstrip("="),
                base64.urlsafe_b64encode(signature).decode().rstrip("="),
            ]

            user_jwt = ".".join(jwt_parts)

            logger.info(
                "nats_worker_credentials_created",
                worker_id=worker_id[:8],
                organization_id=organization_id,
                subject_prefix=subject_prefix,
                expires_at=expires_at.isoformat(),
                ttl_hours=ttl_hours,
            )

            return WorkerCredentials(
                jwt=user_jwt,
                seed=user_seed,
                public_key=user_public_key,
                subject_prefix=subject_prefix,
                expires_at=expires_at,
            )

        except ImportError as e:
            logger.error("nats_credentials_dependency_missing", error=str(e))
            raise

        except Exception as e:
            logger.error(
                "nats_worker_credentials_creation_failed",
                error=str(e),
                worker_id=worker_id[:8],
                organization_id=organization_id,
            )
            raise

    def _encode_jwt_parts(self, claims: dict) -> bytes:
        """
        Encode JWT header and payload for signing.

        Args:
            claims: JWT claims

        Returns:
            Signing input (header.payload as bytes)
        """
        import base64
        import json

        header = {"typ": "JWT", "alg": "ed25519-nkey"}

        header_b64 = (
            base64.urlsafe_b64encode(json.dumps(header).encode())
            .decode()
            .rstrip("=")
        )
        payload_b64 = (
            base64.urlsafe_b64encode(json.dumps(claims).encode())
            .decode()
            .rstrip("=")
        )

        signing_input = f"{header_b64}.{payload_b64}"
        return signing_input.encode()

    def save_credentials_file(
        self, credentials: WorkerCredentials, file_path: str
    ) -> None:
        """
        Save credentials to .creds file format.

        The .creds file format contains both the JWT and seed in a specific format
        that NATS clients can read.

        Args:
            credentials: Worker credentials
            file_path: Path to save .creds file

        Raises:
            Exception: If file write fails
        """
        try:
            # Standard NATS .creds file format
            creds_content = f"""-----BEGIN NATS USER JWT-----
{credentials.jwt}
------END NATS USER JWT------

************************* IMPORTANT *************************
NKEY Seed printed below can be used to sign and prove identity.
NKEYs are sensitive and should be treated as secrets.

-----BEGIN USER NKEY SEED-----
{credentials.seed}
------END USER NKEY SEED------

*************************************************************
"""

            # Write file
            with open(file_path, "w") as f:
                f.write(creds_content)

            # Secure file permissions (owner read/write only)
            os.chmod(file_path, 0o600)

            logger.info(
                "nats_credentials_file_saved",
                file_path=file_path,
                permissions="0600",
            )

        except Exception as e:
            logger.error(
                "nats_credentials_file_save_failed",
                error=str(e),
                file_path=file_path,
            )
            raise

    @staticmethod
    def get_credentials_string(credentials: WorkerCredentials) -> str:
        """
        Get credentials as a string (for passing to workers without file).

        Args:
            credentials: Worker credentials

        Returns:
            Credentials in .creds file format as string
        """
        return f"""-----BEGIN NATS USER JWT-----
{credentials.jwt}
------END NATS USER JWT------

************************* IMPORTANT *************************
NKEY Seed printed below can be used to sign and prove identity.
NKEYs are sensitive and should be treated as secrets.

-----BEGIN USER NKEY SEED-----
{credentials.seed}
------END USER NKEY SEED------

*************************************************************
"""
