"""
Custom Integration Service

Business logic for managing and resolving custom integrations.
Provides a clean, testable interface for integration operations.
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import structlog

from control_plane_api.app.models.custom_integration import (
    CustomIntegration,
    CustomIntegrationStatus
)

logger = structlog.get_logger(__name__)


class CustomIntegrationService:
    """
    Service for managing custom integrations.

    Provides methods for:
    - CRUD operations
    - Filtering and search
    - Integration resolution
    - Validation
    """

    def __init__(self, db: Session):
        """
        Initialize the service.

        Args:
            db: Database session
        """
        self.db = db

    def list_integrations(
        self,
        org_id: str,
        integration_type: Optional[str] = None,
        status: Optional[CustomIntegrationStatus] = None,
        tags: Optional[List[str]] = None,
        include_deleted: bool = False
    ) -> List[CustomIntegration]:
        """
        List custom integrations with optional filtering.

        Args:
            org_id: Organization ID
            integration_type: Filter by integration type
            status: Filter by status
            tags: Filter by tags (AND logic - must have all)
            include_deleted: Include deleted integrations

        Returns:
            List of custom integrations
        """
        query = self.db.query(CustomIntegration).filter(
            CustomIntegration.organization_id == org_id
        )

        if integration_type:
            query = query.filter(CustomIntegration.integration_type == integration_type)

        if status:
            query = query.filter(CustomIntegration.status == status)
        elif not include_deleted:
            # By default, exclude deleted integrations
            query = query.filter(CustomIntegration.status != CustomIntegrationStatus.DELETED)

        if tags:
            # Filter integrations that have ALL specified tags
            for tag in tags:
                query = query.filter(CustomIntegration.tags.contains([tag]))

        integrations = query.order_by(CustomIntegration.created_at.desc()).all()

        logger.debug(
            "custom_integrations_listed",
            org_id=org_id,
            count=len(integrations),
            filters={
                "type": integration_type,
                "status": status,
                "tags": tags
            }
        )

        return integrations

    def get_integration(
        self,
        integration_id: str,
        org_id: str
    ) -> Optional[CustomIntegration]:
        """
        Get a specific custom integration by ID.

        Args:
            integration_id: Integration ID
            org_id: Organization ID

        Returns:
            CustomIntegration or None if not found
        """
        integration = self.db.query(CustomIntegration).filter(
            CustomIntegration.id == integration_id,
            CustomIntegration.organization_id == org_id
        ).first()

        if integration:
            logger.debug(
                "custom_integration_fetched",
                integration_id=integration_id[:8],
                integration_name=integration.name
            )

        return integration

    def create_integration(
        self,
        org_id: str,
        name: str,
        integration_type: str,
        config: Dict[str, Any],
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        created_by: Optional[str] = None
    ) -> CustomIntegration:
        """
        Create a new custom integration.

        Args:
            org_id: Organization ID
            name: Integration name
            integration_type: Type of integration
            config: Integration configuration
            description: Optional description
            tags: Optional tags
            created_by: Optional user ID

        Returns:
            Created CustomIntegration

        Raises:
            ValueError: If integration with name already exists
        """
        # Check for duplicate name
        existing = self.db.query(CustomIntegration).filter(
            CustomIntegration.organization_id == org_id,
            CustomIntegration.name == name,
            CustomIntegration.status != CustomIntegrationStatus.DELETED
        ).first()

        if existing:
            raise ValueError(f"Custom integration with name '{name}' already exists")

        # Validate config structure
        self._validate_config(config)

        integration = CustomIntegration(
            organization_id=org_id,
            name=name,
            integration_type=integration_type,
            description=description,
            config=config,
            tags=tags or [],
            status=CustomIntegrationStatus.ACTIVE,
            created_by=created_by
        )

        self.db.add(integration)
        self.db.commit()
        self.db.refresh(integration)

        logger.info(
            "custom_integration_created",
            integration_id=str(integration.id)[:8],
            integration_name=integration.name,
            integration_type=integration.integration_type,
            org_id=org_id
        )

        return integration

    def update_integration(
        self,
        integration_id: str,
        org_id: str,
        name: Optional[str] = None,
        integration_type: Optional[str] = None,
        description: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        status: Optional[CustomIntegrationStatus] = None,
        tags: Optional[List[str]] = None
    ) -> CustomIntegration:
        """
        Update an existing custom integration.

        Args:
            integration_id: Integration ID
            org_id: Organization ID
            name: Optional new name
            integration_type: Optional new type
            description: Optional new description
            config: Optional new config
            status: Optional new status
            tags: Optional new tags

        Returns:
            Updated CustomIntegration

        Raises:
            ValueError: If integration not found or name conflict
        """
        integration = self.get_integration(integration_id, org_id)
        if not integration:
            raise ValueError(f"Custom integration {integration_id} not found")

        # Check name uniqueness if changing name
        if name and name != integration.name:
            existing = self.db.query(CustomIntegration).filter(
                CustomIntegration.organization_id == org_id,
                CustomIntegration.name == name,
                CustomIntegration.id != integration_id,
                CustomIntegration.status != CustomIntegrationStatus.DELETED
            ).first()
            if existing:
                raise ValueError(f"Custom integration with name '{name}' already exists")
            integration.name = name

        if integration_type is not None:
            integration.integration_type = integration_type

        if description is not None:
            integration.description = description

        if config is not None:
            self._validate_config(config)
            integration.config = config

        if status is not None:
            integration.status = status

        if tags is not None:
            integration.tags = tags

        self.db.commit()
        self.db.refresh(integration)

        logger.info(
            "custom_integration_updated",
            integration_id=integration_id[:8],
            integration_name=integration.name,
            org_id=org_id
        )

        return integration

    def delete_integration(
        self,
        integration_id: str,
        org_id: str,
        hard_delete: bool = False
    ) -> bool:
        """
        Delete a custom integration.

        Args:
            integration_id: Integration ID
            org_id: Organization ID
            hard_delete: If True, permanently delete. If False, soft delete.

        Returns:
            True if deleted

        Raises:
            ValueError: If integration not found
        """
        integration = self.get_integration(integration_id, org_id)
        if not integration:
            raise ValueError(f"Custom integration {integration_id} not found")

        if hard_delete:
            self.db.delete(integration)
            logger.info(
                "custom_integration_hard_deleted",
                integration_id=integration_id[:8],
                integration_name=integration.name,
                org_id=org_id
            )
        else:
            integration.status = CustomIntegrationStatus.DELETED
            logger.info(
                "custom_integration_soft_deleted",
                integration_id=integration_id[:8],
                integration_name=integration.name,
                org_id=org_id
            )

        self.db.commit()
        return True

    def _validate_config(self, config: Dict[str, Any]) -> None:
        """
        Validate integration configuration structure.

        Args:
            config: Configuration dict

        Raises:
            ValueError: If config is invalid
        """
        if not isinstance(config, dict):
            raise ValueError("Config must be a dictionary")

        # Validate env_vars if present
        if "env_vars" in config and not isinstance(config["env_vars"], dict):
            raise ValueError("config.env_vars must be a dictionary")

        # Validate secrets if present
        if "secrets" in config and not isinstance(config["secrets"], list):
            raise ValueError("config.secrets must be a list")

        # Validate files if present
        if "files" in config:
            if not isinstance(config["files"], list):
                raise ValueError("config.files must be a list")

            for file_config in config["files"]:
                if not isinstance(file_config, dict):
                    raise ValueError("Each file in config.files must be a dictionary")
                if "path" not in file_config:
                    raise ValueError("Each file must have a 'path' field")

        # Validate context_prompt if present
        if "context_prompt" in config and not isinstance(config["context_prompt"], str):
            raise ValueError("config.context_prompt must be a string")

    def search_integrations(
        self,
        org_id: str,
        search_term: str,
        limit: int = 20
    ) -> List[CustomIntegration]:
        """
        Search integrations by name or description.

        Args:
            org_id: Organization ID
            search_term: Search term
            limit: Maximum number of results

        Returns:
            List of matching integrations
        """
        search_pattern = f"%{search_term}%"

        integrations = self.db.query(CustomIntegration).filter(
            CustomIntegration.organization_id == org_id,
            CustomIntegration.status != CustomIntegrationStatus.DELETED,
            (
                CustomIntegration.name.ilike(search_pattern) |
                CustomIntegration.description.ilike(search_pattern)
            )
        ).limit(limit).all()

        logger.debug(
            "custom_integrations_searched",
            org_id=org_id,
            search_term=search_term,
            results=len(integrations)
        )

        return integrations

    def get_integration_stats(self, org_id: str) -> Dict[str, Any]:
        """
        Get statistics about custom integrations for an organization.

        Args:
            org_id: Organization ID

        Returns:
            Dictionary with stats
        """
        total = self.db.query(CustomIntegration).filter(
            CustomIntegration.organization_id == org_id,
            CustomIntegration.status != CustomIntegrationStatus.DELETED
        ).count()

        active = self.db.query(CustomIntegration).filter(
            CustomIntegration.organization_id == org_id,
            CustomIntegration.status == CustomIntegrationStatus.ACTIVE
        ).count()

        inactive = self.db.query(CustomIntegration).filter(
            CustomIntegration.organization_id == org_id,
            CustomIntegration.status == CustomIntegrationStatus.INACTIVE
        ).count()

        # Get type distribution
        type_counts = {}
        integrations = self.list_integrations(org_id)
        for integration in integrations:
            type_counts[integration.integration_type] = type_counts.get(integration.integration_type, 0) + 1

        return {
            "total": total,
            "active": active,
            "inactive": inactive,
            "by_type": type_counts
        }
