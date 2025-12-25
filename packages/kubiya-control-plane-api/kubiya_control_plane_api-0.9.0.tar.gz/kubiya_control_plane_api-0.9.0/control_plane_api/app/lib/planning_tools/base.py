"""
Base classes and utilities for planning tools
"""

from typing import Optional, Dict, Any, List
from agno.tools.toolkit import Toolkit
from sqlalchemy.orm import Session
import structlog
import json

logger = structlog.get_logger()


class BasePlanningTools(Toolkit):
    """
    Base class for all planning tools with common utilities

    Provides:
    - Database session for direct data access
    - Common error handling
    - Response formatting
    - Logging utilities
    """

    def __init__(
        self,
        db: Optional[Session] = None,
        organization_id: Optional[str] = None,
    ):
        """
        Initialize base planning tools

        Args:
            db: Database session for direct data access
            organization_id: Organization context for filtering
        """
        super().__init__(name="base_planning_tools")
        self.db = db
        self.organization_id = organization_id

    def _get_db(self) -> Session:
        """Get database session, creating one if needed"""
        if self.db is None:
            from control_plane_api.app.database import get_db
            # Create a new session
            self.db = next(get_db())
        return self.db

    def _format_list_response(
        self,
        items: List[Dict[str, Any]],
        title: str,
        key_fields: List[str],
    ) -> str:
        """
        Format a list of items as a readable string

        For LLM consumption, we want to preserve as much structured data as possible
        rather than summarizing it.

        Args:
            items: List of items to format
            title: Title for the list
            key_fields: Fields to include in the output

        Returns:
            Formatted string representation with full data
        """
        if not items:
            return f"{title}: None available"

        output = [f"{title} ({len(items)} total):"]
        for idx, item in enumerate(items, 1):
            output.append(f"\n{idx}. {item.get('name', 'Unnamed')} (ID: {item.get('id', 'N/A')})")
            for field in key_fields:
                if field in item and item[field]:
                    value = item[field]
                    # Format nested objects - preserve full data for LLM
                    if isinstance(value, dict):
                        # Keep full JSON for dicts (execution_environment, etc.)
                        value = json.dumps(value, indent=2)
                    elif isinstance(value, list):
                        # For lists, show full data as JSON if items are dicts/objects
                        # This is critical for skills, projects, environments, etc.
                        if value and isinstance(value[0], dict):
                            value = json.dumps(value, indent=2)
                        else:
                            value = json.dumps(value)
                    output.append(f"   - {field}: {value}")

        return "\n".join(output)

    def _format_detail_response(
        self,
        item: Dict[str, Any],
        title: str,
    ) -> str:
        """
        Format a single item as a readable string

        Args:
            item: Item to format
            title: Title for the item

        Returns:
            Formatted string representation
        """
        if not item:
            return f"{title}: Not found"

        output = [f"{title}:"]
        for key, value in item.items():
            if isinstance(value, dict):
                value = json.dumps(value, indent=2)
            elif isinstance(value, list):
                value = f"{len(value)} items: {', '.join([str(v) for v in value[:3]])}{'...' if len(value) > 3 else ''}"
            output.append(f"  {key}: {value}")

        return "\n".join(output)
