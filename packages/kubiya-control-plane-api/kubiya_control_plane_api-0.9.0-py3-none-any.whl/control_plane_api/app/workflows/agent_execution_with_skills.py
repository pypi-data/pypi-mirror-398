"""
Agent Execution Workflow with Skill Support.

This workflow demonstrates how to execute an agent with skills resolved
from the Control Plane API.
"""

from datetime import timedelta
from dataclasses import dataclass
from temporalio import workflow
from temporalio.common import RetryPolicy
import structlog

# Import activities
from control_plane_api.app.activities.agent_activities import (
    execute_agent_llm,
    update_execution_status,
)
from control_plane_api.app.activities.skill_activities import (
    resolve_agent_skills,
    instantiate_agent_skills,
)

logger = structlog.get_logger()


@dataclass
class AgentExecutionInput:
    """Input for agent execution workflow"""
    execution_id: str
    organization_id: str
    agent_id: str
    prompt: str
    system_prompt: str | None = None
    control_plane_url: str = "https://agent-control-plane.vercel.app"
    api_key: str = None  # Kubiya API key for authentication


@dataclass
class AgentExecutionResult:
    """Result of agent execution workflow"""
    execution_id: str
    response: str
    usage: dict
    status: str
    skills_used: list[str] | None = None


@workflow.defn
class AgentExecutionWithToolSetsWorkflow:
    """
    Orchestrates agent execution with skill resolution.

    Flow:
    1. Fetch agent configuration from Control Plane
    2. Resolve skills from Control Plane (with inheritance)
    3. Instantiate agno tool instances
    4. Create agent with tools
    5. Execute agent
    6. Return results
    """

    @workflow.run
    async def run(self, input: AgentExecutionInput) -> AgentExecutionResult:
        """
        Execute agent workflow with skills.

        Args:
            input: AgentExecutionInput with agent_id, prompt, etc.

        Returns:
            AgentExecutionResult with response and metadata
        """
        workflow.logger.info(
            "agent_execution_workflow_started",
            execution_id=input.execution_id,
            agent_id=input.agent_id,
            organization_id=input.organization_id
        )

        # 1. Update execution status to 'running'
        await workflow.execute_activity(
            update_execution_status,
            args=[input.execution_id, "running"],
            start_to_close_timeout=timedelta(seconds=10)
        )

        try:
            # 2. Resolve skills from Control Plane
            # The Control Plane handles inheritance: Environment → Team → Agent
            skill_definitions = await workflow.execute_activity(
                resolve_agent_skills,
                args=[
                    input.agent_id,
                    input.control_plane_url,
                    input.api_key
                ],
                start_to_close_timeout=timedelta(seconds=30)
            )

            workflow.logger.info(
                "skills_resolved",
                execution_id=input.execution_id,
                skill_count=len(skill_definitions),
                skill_types=[t.get("type") for t in skill_definitions]
            )

            # 3. Instantiate agno tool instances
            agent_tools = await workflow.execute_activity(
                instantiate_agent_skills,
                args=[skill_definitions],
                start_to_close_timeout=timedelta(seconds=10)
            )

            workflow.logger.info(
                "tools_instantiated",
                execution_id=input.execution_id,
                tool_count=len(agent_tools)
            )

            # 4. Execute agent with LLM
            # Pass tools to the execution activity
            llm_result = await workflow.execute_activity(
                execute_agent_llm,
                args=[
                    input.agent_id,
                    input.prompt,
                    input.system_prompt,
                    agent_tools,  # Pass instantiated tools
                    input.control_plane_url,
                    input.api_key
                ],
                start_to_close_timeout=timedelta(minutes=10),
                retry_policy=RetryPolicy(
                    maximum_attempts=3,
                    initial_interval=timedelta(seconds=1),
                    backoff_coefficient=2.0
                )
            )

            # 5. Update execution status to 'completed'
            await workflow.execute_activity(
                update_execution_status,
                args=[input.execution_id, "completed", llm_result],
                start_to_close_timeout=timedelta(seconds=30)
            )

            workflow.logger.info(
                "agent_execution_workflow_completed",
                execution_id=input.execution_id,
                agent_id=input.agent_id
            )

            return AgentExecutionResult(
                execution_id=input.execution_id,
                response=llm_result.get("response", ""),
                usage=llm_result.get("usage", {}),
                status="completed",
                skills_used=[t.get("name") for t in skill_definitions]
            )

        except Exception as e:
            workflow.logger.error(
                "agent_execution_workflow_failed",
                execution_id=input.execution_id,
                error=str(e)
            )

            # Update execution status to 'failed'
            await workflow.execute_activity(
                update_execution_status,
                args=[input.execution_id, "failed", {"error": str(e)}],
                start_to_close_timeout=timedelta(seconds=30)
            )

            raise


# Example usage in Control Plane API:
"""
from temporalio.client import Client
from control_plane_api.app.workflows.agent_execution_with_skills import (
    AgentExecutionWithToolSetsWorkflow,
    AgentExecutionInput
)

# In your agent execution endpoint:
@router.post("/api/v1/agents/{agent_id}/execute")
async def execute_agent(
    agent_id: str,
    request: AgentExecutionRequest,
    organization: dict = Depends(get_current_organization),
):
    # Get Temporal client
    temporal_client = await get_temporal_client()

    # Create execution record
    execution_id = str(uuid.uuid4())

    # Submit workflow to Temporal
    workflow_handle = await temporal_client.start_workflow(
        AgentExecutionWithToolSetsWorkflow.run,
        AgentExecutionInput(
            execution_id=execution_id,
            organization_id=organization["id"],
            agent_id=agent_id,
            prompt=request.prompt,
            system_prompt=request.system_prompt,
            control_plane_url=settings.CONTROL_PLANE_URL,
            api_key=organization["api_key"]  # Or get from auth
        ),
        id=f"agent-exec-{execution_id}",
        task_queue=request.worker_queue_id,  # Route to specific worker queue
        execution_timeout=timedelta(hours=1)
    )

    return AgentExecutionResponse(
        execution_id=execution_id,
        workflow_id=workflow_handle.id,
        status="pending",
        message="Agent execution submitted successfully"
    )
"""
