"""
Environment Context Tools - Fetch environment and infrastructure information
"""

from typing import Optional
from sqlalchemy.orm import Session
from control_plane_api.app.lib.planning_tools.base import BasePlanningTools
from control_plane_api.app.lib.supabase import get_supabase


class EnvironmentsContextTools(BasePlanningTools):
    """
    Tools for fetching environment and infrastructure context

    Provides methods to:
    - List available execution environments
    - Get worker queue information
    - Check resource availability
    - Query runtime configurations
    """

    def __init__(self, db: Optional[Session] = None, organization_id: Optional[str] = None):
        super().__init__(db=db, organization_id=organization_id)
        self.name = "environment_context_tools"

    async def list_environments(self, limit: int = 50) -> str:
        """
        List all available execution environments

        Args:
            limit: Maximum number of environments to return

        Returns:
            Formatted string with environment information including:
            - Environment name and ID
            - Status (active/inactive)
            - Available resources
            - Configuration details
        """
        try:
            # Use Supabase for environments
            client = get_supabase()

            query = client.table("environments").select("*")
            if self.organization_id:
                query = query.eq("organization_id", self.organization_id)

            result = query.limit(limit).execute()
            environments = result.data or []

            return self._format_list_response(
                items=environments,
                title="Available Environments",
                key_fields=["status", "type", "region"],
            )

        except Exception as e:
            return f"Error listing environments: {str(e)}"

    async def get_environment_details(self, environment_id: str) -> str:
        """
        Get detailed information about a specific environment

        Args:
            environment_id: ID of the environment to fetch

        Returns:
            Detailed environment information including:
            - Full configuration
            - Resource limits
            - Network settings
            - Security policies
        """
        try:
            response = await self._make_request("GET", f"/environments/{environment_id}")

            return self._format_detail_response(
                item=response,
                title=f"Environment Details: {response.get('name', 'Unknown')}",
            )

        except Exception as e:
            return f"Error fetching environment {environment_id}: {str(e)}"

    async def list_worker_queues(self, environment_id: Optional[str] = None) -> str:
        """
        List available worker queues for task execution

        Args:
            environment_id: Optional environment ID to filter queues

        Returns:
            List of worker queues with:
            - Queue name and ID
            - Active worker count
            - Queue status
            - Processing capacity
        """
        try:
            if environment_id:
                endpoint = f"/environments/{environment_id}/worker-queues"
            else:
                endpoint = "/worker-queues"

            params = {}
            if self.organization_id:
                params["organization_id"] = self.organization_id

            response = await self._make_request("GET", endpoint, params=params)

            queues = response if isinstance(response, list) else response.get("queues", [])

            return self._format_list_response(
                items=queues,
                title="Available Worker Queues",
                key_fields=["status", "active_workers", "pending_tasks", "environment_id"],
            )

        except Exception as e:
            return f"Error listing worker queues: {str(e)}"

    async def get_worker_queue_details(self, queue_id: str) -> str:
        """
        Get detailed information about a specific worker queue

        Args:
            queue_id: ID of the worker queue

        Returns:
            Detailed queue information including:
            - Worker capacity and utilization
            - Queue statistics
            - Configuration
        """
        try:
            response = await self._make_request("GET", f"/worker-queues/{queue_id}")

            return self._format_detail_response(
                item=response,
                title=f"Worker Queue Details: {response.get('name', 'Unknown')}",
            )

        except Exception as e:
            return f"Error fetching worker queue {queue_id}: {str(e)}"

    async def check_resource_availability(self, environment_id: str) -> str:
        """
        Check resource availability in a specific environment

        Args:
            environment_id: ID of the environment to check

        Returns:
            Resource availability status including:
            - CPU/Memory availability
            - Active workers
            - Queue capacity
        """
        try:
            # Get environment details
            env_response = await self._make_request("GET", f"/environments/{environment_id}")

            # Get worker queues for this environment
            queues_response = await self._make_request(
                "GET",
                f"/environments/{environment_id}/worker-queues"
            )

            queues = queues_response if isinstance(queues_response, list) else queues_response.get("queues", [])

            total_workers = sum(q.get("active_workers", 0) for q in queues)
            total_pending = sum(q.get("pending_tasks", 0) for q in queues)

            output = [
                f"Resource Availability for Environment: {env_response.get('name', 'Unknown')}",
                f"  Status: {env_response.get('status', 'unknown')}",
                f"  Worker Queues: {len(queues)}",
                f"  Total Active Workers: {total_workers}",
                f"  Total Pending Tasks: {total_pending}",
                "",
                "Queue Details:",
            ]

            for queue in queues:
                output.append(
                    f"  - {queue.get('name')}: "
                    f"{queue.get('active_workers', 0)} workers, "
                    f"{queue.get('pending_tasks', 0)} pending"
                )

            return "\n".join(output)

        except Exception as e:
            return f"Error checking resource availability: {str(e)}"

    async def list_runtime_configurations(self) -> str:
        """
        List available runtime configurations

        Returns:
            Available runtime configurations including:
            - Runtime types (docker, k8s, etc.)
            - Resource templates
            - Default configurations
        """
        try:
            response = await self._make_request("GET", "/runtimes")

            runtimes = response if isinstance(response, list) else response.get("runtimes", [])

            return self._format_list_response(
                items=runtimes,
                title="Available Runtime Configurations",
                key_fields=["type", "version", "resource_limits"],
            )

        except Exception as e:
            return f"Error listing runtime configurations: {str(e)}"
