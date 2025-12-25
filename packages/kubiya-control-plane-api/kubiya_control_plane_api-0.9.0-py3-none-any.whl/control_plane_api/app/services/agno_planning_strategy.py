"""
Agno Planning Strategy

Implementation using Agno framework for task planning with 4-step workflow.
"""

from typing import Dict, Any, AsyncIterator
import structlog
import asyncio

from control_plane_api.app.services.planning_strategy import PlanningStrategy
from control_plane_api.app.models.task_planning import TaskPlanResponse, TaskPlanRequest
from control_plane_api.app.lib.task_planning.planning_workflow import (
    create_planning_workflow,
    run_planning_workflow_stream,
)

logger = structlog.get_logger(__name__)


class AgnoPlanningStrategy(PlanningStrategy):
    """Task planning using Agno framework with robust 4-step workflow"""

    @property
    def name(self) -> str:
        return "agno"

    async def plan_task(self, planning_prompt: str) -> TaskPlanResponse:
        """Generate task plan using Agno 4-step workflow (non-streaming)"""
        logger.info("using_agno_strategy_with_4step_workflow")

        # Create a minimal TaskPlanRequest from the prompt
        # Extract description from prompt (simple parsing)
        description = planning_prompt.split("\n")[0] if planning_prompt else "Task planning request"
        request = TaskPlanRequest(
            description=description,
            priority="medium",
            agents=[],
            teams=[],
            environments=[],
            worker_queues=[],
            quick_mode=False  # Non-streaming endpoint uses normal mode
        )

        # Create the 4-step workflow with DB and org context
        workflow = create_planning_workflow(
            db=self.db,
            organization_id=self.organization_id,
            api_token=self.api_token,
            quick_mode=request.quick_mode,
            outer_context=None  # No outer context for this endpoint
        )

        # Run workflow without streaming (collect events but don't yield them)
        events = []
        def collect_event(event_dict):
            events.append(event_dict)

        # Run the workflow
        result = run_planning_workflow_stream(workflow, request, collect_event)

        # Validate and return
        if isinstance(result, TaskPlanResponse):
            plan = result
        elif isinstance(result, dict):
            from pydantic import ValidationError
            try:
                plan = TaskPlanResponse.model_validate(result)
            except ValidationError as e:
                logger.error("plan_validation_failed", errors=e.errors())
                raise ValueError(f"Invalid TaskPlanResponse structure: {e}")
        else:
            raise ValueError(f"Unexpected response type from Agno workflow: {type(result)}")

        logger.info("agno_4step_plan_generated", title=plan.title)
        return plan

    async def plan_task_stream(self, planning_prompt: str) -> AsyncIterator[Dict[str, Any]]:
        """Generate task plan using Agno 4-step workflow with progress streaming"""
        logger.info("using_agno_strategy_stream_4step_workflow", prompt_length=len(planning_prompt))

        try:
            # Yield initial progress
            yield {
                "event": "progress",
                "data": {
                    "stage": "initializing",
                    "message": "🚀 Initializing 4-step AI planner...",
                    "progress": 10
                }
            }

            # Create a minimal TaskPlanRequest from the prompt
            description = planning_prompt.split("\n")[0] if planning_prompt else "Task planning request"
            request = TaskPlanRequest(
                description=description,
                priority="medium",
                agents=[],
                teams=[],
                environments=[],
                worker_queues=[],
                quick_mode=False  # Non-streaming strategy uses normal mode
            )

            # Create the 4-step workflow with DB and org context
            workflow = create_planning_workflow(
                db=self.db,
                organization_id=self.organization_id,
                api_token=self.api_token,
                quick_mode=request.quick_mode,
                outer_context=None  # No outer context for this strategy
            )

            # Set up event queue for streaming progress updates
            event_queue = asyncio.Queue()
            loop = asyncio.get_event_loop()

            def publish_event(event_dict):
                """Publish event to the queue (thread-safe)"""
                try:
                    loop.call_soon_threadsafe(event_queue.put_nowait, event_dict)
                except Exception as e:
                    logger.error("failed_to_publish_event", error=str(e), event=event_dict)

            workflow_complete = False
            workflow_result = None
            workflow_error = None

            async def run_workflow_async():
                """Run the workflow in a thread pool"""
                nonlocal workflow_complete, workflow_result, workflow_error
                try:
                    result = await asyncio.to_thread(
                        run_planning_workflow_stream,
                        workflow,
                        request,
                        publish_event
                    )
                    workflow_result = result
                except Exception as e:
                    logger.error("workflow_execution_failed", error=str(e), exc_info=True)
                    workflow_error = e
                finally:
                    workflow_complete = True

            # Start workflow task
            workflow_task = asyncio.create_task(run_workflow_async())

            # Stream events from queue as they arrive
            while not workflow_complete:
                try:
                    # Try to get event from queue (with timeout)
                    event = await asyncio.wait_for(event_queue.get(), timeout=2.0)

                    # Yield event to client
                    yield event

                except asyncio.TimeoutError:
                    # No event in queue, check if workflow is done
                    if workflow_task.done():
                        workflow_complete = True
                        break
                    # Otherwise continue waiting
                    continue

            # Drain any remaining events
            while not event_queue.empty():
                try:
                    event = event_queue.get_nowait()
                    yield event
                except asyncio.QueueEmpty:
                    break

            # Check for errors
            if workflow_error:
                yield {
                    "event": "error",
                    "data": {
                        "message": f"Workflow execution failed: {str(workflow_error)}",
                        "error": str(workflow_error)
                    }
                }
                raise workflow_error

            # Validate result
            if isinstance(workflow_result, TaskPlanResponse):
                plan = workflow_result
            elif isinstance(workflow_result, dict):
                from pydantic import ValidationError
                try:
                    plan = TaskPlanResponse.model_validate(workflow_result)
                except ValidationError as e:
                    logger.error("plan_validation_failed", errors=e.errors())
                    yield {
                        "event": "error",
                        "data": {
                            "message": f"Invalid plan structure: {str(e)}",
                            "error": str(e)
                        }
                    }
                    raise
            else:
                error_msg = f"Unexpected result type: {type(workflow_result)}"
                yield {
                    "event": "error",
                    "data": {
                        "message": error_msg,
                        "error": error_msg
                    }
                }
                raise ValueError(error_msg)

            logger.info("agno_4step_plan_generated_stream", title=plan.title)

            # Yield complete event with the plan
            yield {
                "event": "complete",
                "data": {
                    "plan": plan.model_dump(),
                    "progress": 100,
                    "message": "✅ Plan ready!"
                }
            }

        except Exception as e:
            logger.error("agno_streaming_error", error=str(e), exc_info=True)
            yield {
                "event": "error",
                "data": {
                    "message": f"Planning failed: {str(e)}",
                    "error": str(e)
                }
            }
