"""
Agent Communication Tools - Enable agents to call other agents or teams.

Provides hierarchical agent execution capabilities with security safeguards.
"""
import asyncio
import os
import time
import uuid
from typing import Any, Dict, List, Optional, Union, Literal
from datetime import datetime
import httpx
import structlog

logger = structlog.get_logger()


class AgentCommunicationTools:
    """
    Tools for agent-to-agent and agent-to-team communication.

    Enables hierarchical agent execution with:
    - Parent-child execution tracking
    - Execution depth control
    - Circular call prevention
    - Real-time status monitoring
    """

    def __init__(
        self,
        allowed_operations: List[str] = None,
        allowed_agents: Union[List[str], str] = None,
        allowed_teams: Union[List[str], str] = None,
        max_execution_depth: int = 2,
        timeout: int = 300,
        wait_for_completion: bool = True,
        inherit_context: bool = True,
        max_concurrent_calls: int = 3,
        allow_session_continuation: bool = True,
        streaming_enabled: bool = True,
        parent_execution_id: Optional[str] = None,
        execution_depth: int = 0,
        control_plane_base_url: str = None,
        kubiya_api_key: str = None,
        organization_id: Optional[str] = None,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize Agent Communication Tools.

        Args:
            allowed_operations: List of allowed tool operations
            allowed_agents: List of agent IDs that can be called, or '*' for all
            allowed_teams: List of team IDs that can be called, or '*' for all
            max_execution_depth: Maximum nesting depth for child executions
            timeout: Maximum wait time for child execution in seconds
            wait_for_completion: Whether to wait for child execution to complete
            inherit_context: Whether to pass parent execution context to child
            max_concurrent_calls: Maximum number of concurrent child executions
            allow_session_continuation: Allow following up on existing sessions
            streaming_enabled: Stream child execution events to parent
            parent_execution_id: ID of parent execution (for tracking)
            execution_depth: Current depth in execution tree
            control_plane_base_url: Control Plane API base URL
            kubiya_api_key: Kubiya API key for authentication
            organization_id: Organization ID for context
            user_id: User ID for context
            user_email: User email for context
            **kwargs: Additional configuration
        """
        self.allowed_operations = allowed_operations or ["get_execution_status"]
        self.allowed_agents = allowed_agents or []
        self.allowed_teams = allowed_teams or []
        self.max_execution_depth = max_execution_depth
        self.timeout = timeout
        self.wait_for_completion = wait_for_completion
        self.inherit_context = inherit_context
        self.max_concurrent_calls = max_concurrent_calls
        self.allow_session_continuation = allow_session_continuation
        self.streaming_enabled = streaming_enabled
        self.parent_execution_id = parent_execution_id
        self.execution_depth = execution_depth
        self.organization_id = organization_id
        self.user_id = user_id
        self.user_email = user_email

        # Get control plane URL from environment or parameter
        self.control_plane_base_url = (
            control_plane_base_url or
            os.environ.get("CONTROL_PLANE_BASE_URL") or
            os.environ.get("CONTROL_PLANE_URL", "http://localhost:8000")
        ).rstrip("/")

        self.kubiya_api_key = kubiya_api_key or os.environ.get("KUBIYA_API_KEY")
        if not self.kubiya_api_key:
            raise ValueError("KUBIYA_API_KEY is required for Agent Communication tools")

        # Semaphore for concurrent execution limit
        self._semaphore = asyncio.Semaphore(max_concurrent_calls)

        # HTTP client for API calls
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(timeout, connect=5.0))

        logger.info(
            "agent_communication_tools_initialized",
            allowed_operations=self.allowed_operations,
            allowed_agents=self.allowed_agents if self.allowed_agents != "*" else "all",
            allowed_teams=self.allowed_teams if self.allowed_teams != "*" else "all",
            max_execution_depth=max_execution_depth,
            execution_depth=execution_depth,
            parent_execution_id=parent_execution_id,
        )

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        return {
            "Authorization": f"UserKey {self.kubiya_api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _check_operation_allowed(self, operation: str) -> bool:
        """Check if an operation is allowed."""
        return operation in self.allowed_operations

    def _check_allowed_entity(self, entity_type: str, entity_id: str) -> bool:
        """
        Check if entity is allowed to be called.

        Args:
            entity_type: "agent" or "team"
            entity_id: Agent or team ID

        Returns:
            True if allowed, False otherwise
        """
        allowed_list = self.allowed_agents if entity_type == "agent" else self.allowed_teams

        # Wildcard = all allowed
        if allowed_list == "*":
            return True

        # Check explicit whitelist
        if isinstance(allowed_list, list):
            return entity_id in allowed_list

        return False

    def _check_execution_depth(self, child_depth: int) -> None:
        """
        Check if execution depth is within limits.

        Args:
            child_depth: Depth of child execution

        Raises:
            RuntimeError: If depth exceeds max_execution_depth
        """
        if child_depth > self.max_execution_depth:
            raise RuntimeError(
                f"Execution depth limit exceeded: {child_depth} > {self.max_execution_depth}. "
                f"Cannot create deeper child executions."
            )

    async def _get_execution_chain(self, execution_id: str) -> List[Dict[str, Any]]:
        """
        Build execution chain from root to current execution.

        Args:
            execution_id: Execution ID to start from

        Returns:
            List of execution info dicts with execution_id, entity_type, entity_id
        """
        chain = []
        current_id = execution_id
        max_depth = 20  # Prevent infinite loops

        while current_id and len(chain) < max_depth:
            try:
                url = f"{self.control_plane_base_url}/api/v1/executions/{current_id}"
                response = await self._client.get(url, headers=self._get_headers())

                if response.status_code != 200:
                    logger.warning(
                        "failed_to_fetch_execution_in_chain",
                        execution_id=current_id,
                        status_code=response.status_code
                    )
                    break

                execution = response.json()
                chain.append({
                    "execution_id": current_id,
                    "entity_type": execution.get("entity_type"),
                    "entity_id": execution.get("entity_id"),
                })

                # Get parent execution ID
                current_id = execution.get("parent_execution_id")

            except Exception as e:
                logger.error(
                    "error_building_execution_chain",
                    execution_id=current_id,
                    error=str(e)
                )
                break

        return chain

    def _is_circular_call(self, chain: List[Dict[str, Any]], target_entity_id: str) -> bool:
        """
        Check if target_entity_id appears in execution chain (circular call).

        Args:
            chain: Execution chain from _get_execution_chain
            target_entity_id: Agent or team ID to check

        Returns:
            True if circular call detected, False otherwise
        """
        return any(e.get("entity_id") == target_entity_id for e in chain)

    async def _check_circular_execution(self, target_entity_id: str) -> None:
        """
        Check if calling target_entity_id would create a circular execution.

        Args:
            target_entity_id: Agent or team ID to check

        Raises:
            RuntimeError: If circular call detected
        """
        if not self.parent_execution_id:
            # No parent, so no cycle possible
            return

        # Build execution chain
        chain = await self._get_execution_chain(self.parent_execution_id)

        # Check for circular call
        if self._is_circular_call(chain, target_entity_id):
            chain_str = " -> ".join([e["entity_id"] for e in chain])
            raise RuntimeError(
                f"Circular execution detected: {target_entity_id} already appears in execution chain. "
                f"Chain: {chain_str} -> {target_entity_id}"
            )

    def _build_child_context(self) -> Dict[str, Any]:
        """
        Build context to pass to child execution.

        Returns:
            Dict with parent context information
        """
        context = {
            "parent_execution_id": self.parent_execution_id,
            "execution_depth": self.execution_depth + 1,
        }

        if self.inherit_context:
            # Add user context
            if self.user_id:
                context["user_id"] = self.user_id
            if self.user_email:
                context["user_email"] = self.user_email
            if self.organization_id:
                context["organization_id"] = self.organization_id

        return context

    async def _wait_for_execution(
        self,
        execution_id: str,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Poll execution status until complete or timeout.

        Args:
            execution_id: Execution ID to wait for
            timeout: Timeout in seconds (defaults to self.timeout)

        Returns:
            Dict with execution result
        """
        timeout = timeout or self.timeout
        start_time = time.time()
        poll_interval = 2  # seconds

        while True:
            elapsed = time.time() - start_time

            if elapsed >= timeout:
                logger.warning(
                    "execution_timeout",
                    execution_id=execution_id,
                    timeout=timeout
                )
                return {
                    "execution_id": execution_id,
                    "status": "timeout",
                    "error": f"Execution exceeded timeout of {timeout}s",
                    "duration_ms": int(elapsed * 1000),
                }

            # Fetch execution status
            try:
                status_result = await self.get_execution_status(
                    execution_id=execution_id,
                    include_events=False,
                    include_session=False
                )

                status = status_result.get("status")

                # Check if completed
                if status in ["completed", "failed", "cancelled"]:
                    return status_result

                # Still running or waiting for input, continue polling
                await asyncio.sleep(poll_interval)

            except Exception as e:
                logger.error(
                    "error_polling_execution_status",
                    execution_id=execution_id,
                    error=str(e)
                )
                return {
                    "execution_id": execution_id,
                    "status": "error",
                    "error": f"Failed to poll execution status: {str(e)}",
                }

    async def _stream_child_events(
        self,
        child_execution_id: str,
        parent_execution_id: str
    ) -> None:
        """
        Stream child execution events to parent execution (background task).

        Args:
            child_execution_id: Child execution ID
            parent_execution_id: Parent execution ID to stream events to
        """
        # TODO: Implement event streaming from child to parent
        # This would require subscribing to child execution events via WebSocket or SSE
        # and republishing them to the parent execution
        logger.info(
            "event_streaming_placeholder",
            child_execution_id=child_execution_id,
            parent_execution_id=parent_execution_id,
            message="Event streaming not yet implemented"
        )

    async def execute_agent(
        self,
        agent_id: str,
        prompt: str,
        wait_for_completion: Optional[bool] = None,
        timeout: Optional[int] = None,
        inherit_context: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Execute another agent with a specific prompt.

        Creates a new child execution and optionally waits for completion.

        Args:
            agent_id: The ID of the agent to execute
            prompt: The prompt/instruction to send to the agent
            wait_for_completion: Whether to wait for the agent to finish (defaults to config)
            timeout: Maximum wait time in seconds (defaults to config)
            inherit_context: Whether to pass parent execution context (defaults to config)

        Returns:
            Dict containing:
            - execution_id: ID of the child execution
            - status: Current execution status
            - result: Final result if wait_for_completion=True
            - events: List of execution events

        Raises:
            ValueError: If agent_id not in allowed_agents or operation not allowed
            RuntimeError: If max_execution_depth exceeded or circular execution detected
        """
        # Check operation allowed
        if not self._check_operation_allowed("execute_agent"):
            raise ValueError(
                "Operation 'execute_agent' not allowed. "
                f"Allowed operations: {self.allowed_operations}"
            )

        # Check agent allowed
        if not self._check_allowed_entity("agent", agent_id):
            raise ValueError(
                f"Agent '{agent_id}' not in allowed agents list. "
                f"Allowed agents: {self.allowed_agents}"
            )

        # Use defaults if not specified
        wait = wait_for_completion if wait_for_completion is not None else self.wait_for_completion
        timeout_val = timeout if timeout is not None else self.timeout
        inherit = inherit_context if inherit_context is not None else self.inherit_context

        # Check execution depth
        child_depth = self.execution_depth + 1
        self._check_execution_depth(child_depth)

        # Check circular execution
        await self._check_circular_execution(agent_id)

        # Acquire semaphore for concurrent execution limit
        async with self._semaphore:
            # Create child execution
            execution_id = str(uuid.uuid4())

            logger.info(
                "creating_child_agent_execution",
                parent_execution_id=self.parent_execution_id,
                child_execution_id=execution_id,
                agent_id=agent_id,
                execution_depth=child_depth,
                wait_for_completion=wait
            )

            try:
                # Build child context
                child_context = self._build_child_context() if inherit else {}

                # Create execution via Control Plane API
                url = f"{self.control_plane_base_url}/api/v1/executions"
                payload = {
                    "execution_id": execution_id,
                    "entity_type": "agent",
                    "entity_id": agent_id,
                    "prompt": prompt,
                    "parent_execution_id": self.parent_execution_id,
                    "execution_depth": child_depth,
                    "context": child_context,
                }

                if self.organization_id:
                    payload["organization_id"] = self.organization_id

                response = await self._client.post(
                    url,
                    headers=self._get_headers(),
                    json=payload
                )

                if response.status_code not in [200, 201, 202]:
                    error_msg = f"Failed to create execution: {response.status_code} {response.text}"
                    logger.error(
                        "create_execution_failed",
                        execution_id=execution_id,
                        agent_id=agent_id,
                        status_code=response.status_code,
                        error=response.text[:500]
                    )
                    return {
                        "execution_id": execution_id,
                        "status": "failed",
                        "error": error_msg,
                    }

                # Start event streaming if enabled (background task)
                if self.streaming_enabled and self.parent_execution_id:
                    asyncio.create_task(
                        self._stream_child_events(execution_id, self.parent_execution_id)
                    )

                # Wait for completion if requested
                if wait:
                    result = await self._wait_for_execution(execution_id, timeout_val)
                    logger.info(
                        "child_agent_execution_completed",
                        execution_id=execution_id,
                        agent_id=agent_id,
                        status=result.get("status")
                    )
                    return result
                else:
                    # Return immediately with execution ID
                    return {
                        "execution_id": execution_id,
                        "status": "running",
                        "entity_type": "agent",
                        "entity_id": agent_id,
                        "parent_execution_id": self.parent_execution_id,
                        "execution_depth": child_depth,
                        "message": "Execution started asynchronously. Use get_execution_status() to check progress.",
                    }

            except Exception as e:
                logger.error(
                    "execute_agent_error",
                    execution_id=execution_id,
                    agent_id=agent_id,
                    error=str(e)
                )
                return {
                    "execution_id": execution_id,
                    "status": "failed",
                    "error": f"Failed to execute agent: {str(e)}",
                }

    async def execute_team(
        self,
        team_id: str,
        prompt: str,
        wait_for_completion: Optional[bool] = None,
        timeout: Optional[int] = None,
        inherit_context: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Execute a team with a specific prompt.

        Creates a new child team execution with multi-agent collaboration.

        Args:
            team_id: The ID of the team to execute
            prompt: The prompt/instruction to send to the team
            wait_for_completion: Whether to wait for team to finish
            timeout: Maximum wait time in seconds
            inherit_context: Whether to pass parent execution context

        Returns:
            Dict containing:
            - execution_id: ID of the child execution
            - status: Current execution status
            - result: Final result if wait_for_completion=True
            - team_members: List of agents in the team
            - events: List of execution events

        Raises:
            ValueError: If team_id not in allowed_teams or operation not allowed
            RuntimeError: If max_execution_depth exceeded or circular execution detected
        """
        # Check operation allowed
        if not self._check_operation_allowed("execute_team"):
            raise ValueError(
                "Operation 'execute_team' not allowed. "
                f"Allowed operations: {self.allowed_operations}"
            )

        # Check team allowed
        if not self._check_allowed_entity("team", team_id):
            raise ValueError(
                f"Team '{team_id}' not in allowed teams list. "
                f"Allowed teams: {self.allowed_teams}"
            )

        # Use defaults if not specified
        wait = wait_for_completion if wait_for_completion is not None else self.wait_for_completion
        timeout_val = timeout if timeout is not None else self.timeout
        inherit = inherit_context if inherit_context is not None else self.inherit_context

        # Check execution depth
        child_depth = self.execution_depth + 1
        self._check_execution_depth(child_depth)

        # Check circular execution
        await self._check_circular_execution(team_id)

        # Acquire semaphore for concurrent execution limit
        async with self._semaphore:
            # Create child execution
            execution_id = str(uuid.uuid4())

            logger.info(
                "creating_child_team_execution",
                parent_execution_id=self.parent_execution_id,
                child_execution_id=execution_id,
                team_id=team_id,
                execution_depth=child_depth,
                wait_for_completion=wait
            )

            try:
                # Build child context
                child_context = self._build_child_context() if inherit else {}

                # Create execution via Control Plane API
                url = f"{self.control_plane_base_url}/api/v1/executions"
                payload = {
                    "execution_id": execution_id,
                    "entity_type": "team",
                    "entity_id": team_id,
                    "prompt": prompt,
                    "parent_execution_id": self.parent_execution_id,
                    "execution_depth": child_depth,
                    "context": child_context,
                }

                if self.organization_id:
                    payload["organization_id"] = self.organization_id

                response = await self._client.post(
                    url,
                    headers=self._get_headers(),
                    json=payload
                )

                if response.status_code not in [200, 201, 202]:
                    error_msg = f"Failed to create execution: {response.status_code} {response.text}"
                    logger.error(
                        "create_execution_failed",
                        execution_id=execution_id,
                        team_id=team_id,
                        status_code=response.status_code,
                        error=response.text[:500]
                    )
                    return {
                        "execution_id": execution_id,
                        "status": "failed",
                        "error": error_msg,
                    }

                # Start event streaming if enabled (background task)
                if self.streaming_enabled and self.parent_execution_id:
                    asyncio.create_task(
                        self._stream_child_events(execution_id, self.parent_execution_id)
                    )

                # Wait for completion if requested
                if wait:
                    result = await self._wait_for_execution(execution_id, timeout_val)
                    logger.info(
                        "child_team_execution_completed",
                        execution_id=execution_id,
                        team_id=team_id,
                        status=result.get("status")
                    )
                    return result
                else:
                    # Return immediately with execution ID
                    return {
                        "execution_id": execution_id,
                        "status": "running",
                        "entity_type": "team",
                        "entity_id": team_id,
                        "parent_execution_id": self.parent_execution_id,
                        "execution_depth": child_depth,
                        "message": "Execution started asynchronously. Use get_execution_status() to check progress.",
                    }

            except Exception as e:
                logger.error(
                    "execute_team_error",
                    execution_id=execution_id,
                    team_id=team_id,
                    error=str(e)
                )
                return {
                    "execution_id": execution_id,
                    "status": "failed",
                    "error": f"Failed to execute team: {str(e)}",
                }

    async def followup_execution(
        self,
        execution_id: str,
        followup_prompt: str,
        wait_for_completion: Optional[bool] = None,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Send a followup prompt to an existing execution (continue conversation).

        Only available if allow_session_continuation=True.

        Args:
            execution_id: The ID of the execution to follow up on
            followup_prompt: Additional prompt/instruction to add to conversation
            wait_for_completion: Whether to wait for response
            timeout: Maximum wait time in seconds

        Returns:
            Dict containing:
            - execution_id: Same execution ID
            - status: Current execution status
            - result: Response to followup
            - message_count: Total messages in session

        Raises:
            RuntimeError: If allow_session_continuation=False
            ValueError: If execution_id not found or not accessible or operation not allowed
        """
        # Check operation allowed
        if not self._check_operation_allowed("followup_execution"):
            raise ValueError(
                "Operation 'followup_execution' not allowed. "
                f"Allowed operations: {self.allowed_operations}"
            )

        # Check if session continuation is allowed
        if not self.allow_session_continuation:
            raise RuntimeError(
                "Session continuation is not allowed. "
                "Set allow_session_continuation=True to enable this operation."
            )

        # Use defaults if not specified
        wait = wait_for_completion if wait_for_completion is not None else self.wait_for_completion
        timeout_val = timeout if timeout is not None else self.timeout

        logger.info(
            "following_up_execution",
            execution_id=execution_id,
            wait_for_completion=wait
        )

        try:
            # Send followup via Control Plane API
            url = f"{self.control_plane_base_url}/api/v1/executions/{execution_id}/followup"
            payload = {
                "prompt": followup_prompt,
            }

            response = await self._client.post(
                url,
                headers=self._get_headers(),
                json=payload
            )

            if response.status_code not in [200, 201, 202]:
                error_msg = f"Failed to send followup: {response.status_code} {response.text}"
                logger.error(
                    "followup_execution_failed",
                    execution_id=execution_id,
                    status_code=response.status_code,
                    error=response.text[:500]
                )
                return {
                    "execution_id": execution_id,
                    "status": "failed",
                    "error": error_msg,
                }

            # Wait for completion if requested
            if wait:
                result = await self._wait_for_execution(execution_id, timeout_val)
                logger.info(
                    "followup_execution_completed",
                    execution_id=execution_id,
                    status=result.get("status")
                )
                return result
            else:
                return {
                    "execution_id": execution_id,
                    "status": "running",
                    "message": "Followup sent successfully. Use get_execution_status() to check progress.",
                }

        except Exception as e:
            logger.error(
                "followup_execution_error",
                execution_id=execution_id,
                error=str(e)
            )
            return {
                "execution_id": execution_id,
                "status": "failed",
                "error": f"Failed to send followup: {str(e)}",
            }

    async def get_execution_status(
        self,
        execution_id: str,
        include_events: bool = False,
        include_session: bool = False,
    ) -> Dict[str, Any]:
        """
        Get the current status of an execution.

        Available for all variants (monitoring-only to full orchestration).

        Args:
            execution_id: The ID of the execution to check
            include_events: Whether to include full event history
            include_session: Whether to include conversation history

        Returns:
            Dict containing:
            - execution_id: Execution ID
            - status: Current status (pending, running, completed, failed)
            - entity_type: "agent" or "team"
            - entity_id: Agent or team ID
            - created_at: Start timestamp
            - completed_at: End timestamp (if completed)
            - duration_ms: Execution duration
            - result: Final result (if completed)
            - error: Error message (if failed)
            - events: Event history (if include_events=True)
            - session: Conversation history (if include_session=True)

        Raises:
            ValueError: If operation not allowed
        """
        # Check operation allowed
        if not self._check_operation_allowed("get_execution_status"):
            raise ValueError(
                "Operation 'get_execution_status' not allowed. "
                f"Allowed operations: {self.allowed_operations}"
            )

        logger.debug(
            "fetching_execution_status",
            execution_id=execution_id,
            include_events=include_events,
            include_session=include_session
        )

        try:
            # Fetch execution from Control Plane API
            url = f"{self.control_plane_base_url}/api/v1/executions/{execution_id}"
            params = {}
            if include_events:
                params["include_events"] = "true"
            if include_session:
                params["include_session"] = "true"

            response = await self._client.get(
                url,
                headers=self._get_headers(),
                params=params
            )

            if response.status_code == 404:
                return {
                    "execution_id": execution_id,
                    "status": "not_found",
                    "error": f"Execution '{execution_id}' not found",
                }

            if response.status_code != 200:
                error_msg = f"Failed to fetch execution: {response.status_code} {response.text}"
                logger.error(
                    "fetch_execution_failed",
                    execution_id=execution_id,
                    status_code=response.status_code,
                    error=response.text[:500]
                )
                return {
                    "execution_id": execution_id,
                    "status": "error",
                    "error": error_msg,
                }

            execution_data = response.json()

            # Format response
            result = {
                "execution_id": execution_id,
                "status": execution_data.get("status", "unknown"),
                "entity_type": execution_data.get("entity_type"),
                "entity_id": execution_data.get("entity_id"),
                "created_at": execution_data.get("created_at"),
                "completed_at": execution_data.get("completed_at"),
                "duration_ms": execution_data.get("duration_ms"),
                "parent_execution_id": execution_data.get("parent_execution_id"),
                "execution_depth": execution_data.get("execution_depth", 0),
            }

            # Add result if completed
            if execution_data.get("result"):
                result["result"] = execution_data["result"]

            # Add error if failed
            if execution_data.get("error"):
                result["error"] = execution_data["error"]

            # Add events if requested
            if include_events and execution_data.get("events"):
                result["events"] = execution_data["events"]

            # Add session if requested
            if include_session and execution_data.get("session"):
                result["session"] = execution_data["session"]

            return result

        except Exception as e:
            logger.error(
                "get_execution_status_error",
                execution_id=execution_id,
                error=str(e)
            )
            return {
                "execution_id": execution_id,
                "status": "error",
                "error": f"Failed to get execution status: {str(e)}",
            }

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - cleanup."""
        await self._client.aclose()
