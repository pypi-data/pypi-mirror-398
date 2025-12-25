"""
Task Planning Pydantic Models
"""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Optional, Literal


class AgentInfo(BaseModel):
    """Lightweight agent info from CLI"""
    id: str
    name: str
    model_id: str
    description: Optional[str] = None
    capabilities: List[str] = Field(default_factory=list, description="Agent capabilities")
    status: str = Field(default="active", description="Agent status")

    @field_validator('description', mode='before')
    @classmethod
    def empty_str_to_none(cls, v):
        """Convert empty string to None for optional fields"""
        if v == '':
            return None
        return v

    @field_validator('model_id', mode='before')
    @classmethod
    def default_model(cls, v):
        """Provide default model if empty"""
        if not v or v == '':
            return 'claude-sonnet-4'
        return v


class TeamInfo(BaseModel):
    """Lightweight team info from CLI"""
    id: str
    name: str
    description: Optional[str] = None
    agent_count: int = Field(default=0, description="Number of agents in team")
    status: str = Field(default="active", description="Team status")

    @field_validator('description', mode='before')
    @classmethod
    def empty_str_to_none(cls, v):
        """Convert empty string to None for optional fields"""
        if v == '':
            return None
        return v


class EnvironmentInfo(BaseModel):
    """Environment info from CLI"""
    id: str
    name: str
    display_name: Optional[str] = Field(default=None, description="Display name for environment")
    status: str = Field(default="active", description="Environment status")


class WorkerQueueInfo(BaseModel):
    """Worker queue info from CLI"""
    id: str
    name: str
    environment_id: str = Field(..., description="Associated environment ID")
    status: str = Field(default="active", description="Worker queue status")
    active_workers: int = Field(default=0, description="Number of active workers (key for queue selection!)")


class TaskPlanRequest(BaseModel):
    """Request to plan a task"""
    description: str = Field(..., description="Task description")
    priority: Literal['low', 'medium', 'high', 'critical'] = Field('medium', description="Task priority")
    project_id: Optional[str] = Field(None, description="Associated project ID")
    agents: List[AgentInfo] = Field(default_factory=list, description="Available agents (outer context from CLI)")
    teams: List[TeamInfo] = Field(default_factory=list, description="Available teams (outer context from CLI)")
    environments: List[EnvironmentInfo] = Field(default_factory=list, description="Available execution environments")
    worker_queues: List[WorkerQueueInfo] = Field(default_factory=list, description="Available worker queues")
    refinement_feedback: Optional[str] = Field(None, description="User feedback for plan refinement")
    conversation_context: Optional[str] = Field(None, description="Conversation history for context")
    previous_plan: Optional[Dict] = Field(None, description="Previous plan for refinement")
    iteration: int = Field(1, description="Planning iteration number")
    planning_strategy: Optional[Literal['claude_code_sdk', 'agno']] = Field('claude_code_sdk', description="Planning strategy to use (claude_code_sdk or agno)")
    quick_mode: bool = Field(default=False, description="Use fast planning for --local mode (Haiku vs Sonnet)")


class ComplexityInfo(BaseModel):
    """Task complexity assessment"""
    story_points: int = Field(..., ge=1, le=21, description="Story points (1-21)")
    confidence: Literal['low', 'medium', 'high'] = Field(..., description="Confidence level")
    reasoning: str = Field(..., description="Reasoning for complexity assessment")


class AnalysisAndSelectionOutput(BaseModel):
    """Combined output from Step 1: Analysis + Resource Selection

    This model combines the old Step 1 (Task Analysis) and Step 2 (Resource Discovery)
    into a single output for the simplified 2-step workflow.
    """

    # Task Analysis (from old Step 1)
    task_summary: str = Field(..., description="Brief summary of the task")
    required_capabilities: List[str] = Field(default_factory=list, description="Required capabilities (e.g., kubernetes, aws, python)")
    task_type: str = Field(..., description="Type of task (e.g., deployment, investigation, automation)")
    complexity_estimate: Literal["simple", "moderate", "complex"] = Field(..., description="Complexity assessment")
    story_points_estimate: int = Field(..., ge=1, le=21, description="Story points (1-21)")
    needs_multi_agent: bool = Field(..., description="Whether task requires multiple agents/team")
    reasoning: str = Field(..., description="Reasoning for analysis and selection")

    # Resource Selection (from old Step 2)
    selected_entity_type: Literal["agent", "team"] = Field(..., description="Selected entity type")
    selected_entity_id: str = Field(..., description="UUID of selected agent or team")
    selected_entity_name: str = Field(..., description="Name of selected agent or team")
    selection_reasoning: str = Field(..., description="Why this agent/team was selected")

    # Selected agent runtime and model info (for preference-based selection)
    selected_agent_runtime: Optional[str] = Field(None, description="Runtime of selected agent ('default' or 'claude_code')")
    selected_agent_model_id: Optional[str] = Field(None, description="Model ID of selected agent (e.g., 'claude-sonnet-4')")

    # Environment Selection
    selected_environment_id: Optional[str] = Field(None, description="UUID of selected environment (if any)")
    selected_environment_name: Optional[str] = Field(None, description="Name of selected environment")
    selected_worker_queue_id: Optional[str] = Field(None, description="UUID of selected worker queue (if any)")
    selected_worker_queue_name: Optional[str] = Field(None, description="Name of selected worker queue")

    # Basic Cost Estimate
    estimated_cost_usd: float = Field(..., description="Estimated cost in USD")
    estimated_time_hours: float = Field(..., description="Estimated execution time in hours")

    # Discovery Data (for Step 2 reference)
    discovered_agents: List[Dict] = Field(default_factory=list, description="Agents discovered during selection")
    discovered_teams: List[Dict] = Field(default_factory=list, description="Teams discovered during selection")


class AgentModelInfo(BaseModel):
    """Information about the model an agent will use"""
    model_id: str  # e.g., "claude-sonnet-4", "gpt-4o"
    estimated_input_tokens: int
    estimated_output_tokens: int
    cost_per_1k_input_tokens: float
    cost_per_1k_output_tokens: float
    total_model_cost: float


class ToolUsageInfo(BaseModel):
    """Expected tool usage for an agent"""
    tool_name: str  # e.g., "aws_s3", "kubectl", "bash"
    estimated_calls: int
    cost_per_call: float
    total_tool_cost: float


class TaskItem(BaseModel):
    """Detailed task breakdown item with dependencies and testing strategy"""
    id: int = Field(..., description="Unique task ID for tracking dependencies")
    title: str = Field(..., description="Short, clear task title")
    description: str = Field(..., description="Brief overview of what needs to be done")
    details: str = Field(..., description="Step-by-step implementation details, code snippets, and specific instructions")
    test_strategy: str = Field(..., description="How to verify this task was completed correctly")
    priority: Literal["high", "medium", "low"] = Field(default="medium", description="Task priority level")
    dependencies: List[int] = Field(default_factory=list, description="List of task IDs that must be completed before this one")
    status: Literal["pending", "in_progress", "done"] = Field(default="pending", description="Current task status")
    subtasks: List["TaskItem"] = Field(default_factory=list, description="Optional nested subtasks")
    # Optional context-driven fields - planner decides what to use based on agent capabilities
    skills_to_use: Optional[List[str]] = Field(default=None, description="Optional: Specific skills from agent's skillset to use (e.g., ['aws_s3', 'kubectl'])")
    env_vars_to_use: Optional[List[str]] = Field(default=None, description="Optional: Environment variables from execution_environment to use (e.g., ['AWS_REGION', 'KUBECONFIG'])")
    secrets_to_use: Optional[List[str]] = Field(default=None, description="Optional: Secrets/credentials from execution_environment to use (e.g., ['AWS_ACCESS_KEY_ID', 'GITHUB_TOKEN'])")
    knowledge_references: Optional[List[str]] = Field(default=None, description="Optional: References to organizational knowledge used for this task")


class TeamBreakdownItem(BaseModel):
    """Breakdown of work for a specific team/agent"""
    team_id: Optional[str] = None
    team_name: str
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None
    responsibilities: List[str]
    estimated_time_hours: float
    model_info: Optional[AgentModelInfo] = None
    expected_tools: List[ToolUsageInfo] = []
    agent_cost: float = 0.0  # Total cost for this agent (model + tools)
    # New: Detailed task breakdown with dependencies (OPTIONAL to reduce generation time)
    tasks: List[TaskItem] = Field(default_factory=list, description="Optional: Ordered list of tasks with dependencies. Can be empty for faster plan generation.")


class RecommendedExecution(BaseModel):
    """AI recommendation for which entity should execute the task"""
    entity_type: Literal['agent', 'team']
    entity_id: str
    entity_name: str
    reasoning: str
    recommended_environment_id: Optional[str] = None
    recommended_environment_name: Optional[str] = None
    recommended_worker_queue_id: Optional[str] = None
    recommended_worker_queue_name: Optional[str] = None
    execution_reasoning: Optional[str] = None


class LLMCostBreakdown(BaseModel):
    """Detailed LLM cost breakdown by model"""
    model_id: str
    estimated_input_tokens: int
    estimated_output_tokens: int
    cost_per_1k_input_tokens: float
    cost_per_1k_output_tokens: float
    total_cost: float


class ToolCostBreakdown(BaseModel):
    """Tool execution cost breakdown"""
    category: str  # e.g., "AWS APIs", "Database Queries", "External APIs"
    tools: List[ToolUsageInfo]
    category_total: float


class RuntimeCostBreakdown(BaseModel):
    """Runtime and compute costs"""
    worker_execution_hours: float
    cost_per_hour: float
    total_cost: float


class CostBreakdownItem(BaseModel):
    """Individual cost breakdown item (legacy, kept for backwards compatibility)"""
    item: str
    cost: float


class HumanResourceCost(BaseModel):
    """Human resource cost breakdown by role"""
    role: str  # e.g., "Senior DevOps Engineer", "Security Engineer"
    hourly_rate: float  # e.g., 150.00
    estimated_hours: float  # e.g., 8.0
    total_cost: float  # e.g., 1200.00


class CostEstimate(BaseModel):
    """Enhanced cost estimation for the task"""
    estimated_cost_usd: float
    # Legacy breakdown (keep for backwards compatibility)
    breakdown: List[CostBreakdownItem] = []
    # New detailed breakdowns
    llm_costs: List[LLMCostBreakdown] = []
    tool_costs: List[ToolCostBreakdown] = []
    runtime_cost: Optional[RuntimeCostBreakdown] = None


class RealizedSavings(BaseModel):
    """Realized savings by using Kubiya orchestration platform"""
    # Without Kubiya (manual execution)
    without_kubiya_cost: float  # Total cost if done manually
    without_kubiya_hours: float  # Total time if done manually
    without_kubiya_resources: List[HumanResourceCost]  # Resource breakdown

    # With Kubiya (AI orchestration)
    with_kubiya_cost: float  # AI execution cost
    with_kubiya_hours: float  # AI execution time

    # Realized Savings
    money_saved: float  # Dollars saved
    time_saved_hours: float  # Hours saved
    time_saved_percentage: int  # Percentage of time saved

    # Summary
    savings_summary: str  # Compelling savings narrative


class TaskPlanResponse(BaseModel):
    """AI-generated task plan"""
    title: str
    summary: str
    complexity: ComplexityInfo
    team_breakdown: List[TeamBreakdownItem]
    recommended_execution: RecommendedExecution
    cost_estimate: CostEstimate
    realized_savings: RealizedSavings
    risks: List[str] = []
    prerequisites: List[str] = []
    success_criteria: List[str] = []
    # Optional fields for when AI needs clarification
    has_questions: bool = False
    questions: Optional[str] = None
    # Engineered prompt for execution - includes full context from plan
    execution_prompt: Optional[str] = Field(
        None,
        description="Detailed, engineered prompt for the executing agent that includes "
                    "original request, summary, responsibilities, prerequisites, "
                    "success criteria, risks, and execution context. Max 2000 words.",
        max_length=10000  # ~2000 words
    )
    # Top-level environment selection fields for convenience (mirrors recommended_execution)
    selected_environment_id: Optional[str] = Field(
        None,
        description="UUID of the selected environment for execution. "
                    "Convenience field - same value as recommended_execution.recommended_environment_id"
    )
    selected_environment_name: Optional[str] = Field(
        None,
        description="Name of the selected environment for execution. "
                    "Convenience field - same value as recommended_execution.recommended_environment_name"
    )
    # Selected agent/team runtime and model info
    selected_agent_runtime: Optional[str] = Field(
        None,
        description="Runtime of the selected agent (e.g., 'default', 'claude_code')"
    )
    selected_agent_model_id: Optional[str] = Field(
        None,
        description="Model ID of the selected agent (e.g., 'claude-sonnet-4', 'gpt-4o')"
    )


# ============================================================================
# Streaming Event Models
# ============================================================================

class StepStartedEvent(BaseModel):
    """Event emitted when a workflow step begins execution"""
    event: Literal["step_started"] = "step_started"
    step: int = Field(..., ge=1, le=4, description="Step number (1-4)")
    step_name: str = Field(..., description="Human-readable step name")
    step_description: str = Field(..., description="What this step does")
    progress: int = Field(..., ge=0, le=100, description="Overall workflow progress percentage")


class StepCompletedEvent(BaseModel):
    """Event emitted when a workflow step completes with its output"""
    event: Literal["step_completed"] = "step_completed"
    step: int = Field(..., ge=1, le=4, description="Step number (1-4)")
    step_name: str = Field(..., description="Human-readable step name")
    output: Dict = Field(..., description="Structured output from this step (TaskAnalysisOutput, etc.)")
    progress: int = Field(..., ge=0, le=100, description="Overall workflow progress percentage")


class ToolCallEvent(BaseModel):
    """Event emitted when a tool begins execution"""
    event: Literal["tool_call"] = "tool_call"
    tool_id: str = Field(..., description="Unique ID for this tool execution")
    tool_name: str = Field(..., description="Name of the tool being called")
    tool_description: Optional[str] = Field(None, description="What the tool does")
    arguments: Dict = Field(default_factory=dict, description="Arguments passed to the tool")
    step: int = Field(..., ge=1, le=4, description="Which workflow step is executing this tool")
    timestamp: str = Field(..., description="ISO 8601 timestamp of tool call")


class ToolResultEvent(BaseModel):
    """Event emitted when a tool completes execution"""
    event: Literal["tool_result"] = "tool_result"
    tool_id: str = Field(..., description="Unique ID matching the tool_call event")
    tool_name: str = Field(..., description="Name of the tool that executed")
    status: Literal["success", "failed"] = Field(..., description="Tool execution status")
    result: Optional[str] = Field(None, description="Tool output (truncated if large)")
    error: Optional[str] = Field(None, description="Error message if status=failed")
    duration: float = Field(..., description="Execution time in seconds")
    step: int = Field(..., ge=1, le=4, description="Which workflow step executed this tool")
    timestamp: str = Field(..., description="ISO 8601 timestamp of completion")


class ValidationErrorEvent(BaseModel):
    """Event emitted when step output validation fails"""
    event: Literal["validation_error"] = "validation_error"
    step: int = Field(..., ge=1, le=4, description="Which workflow step failed validation")
    attempt: int = Field(..., ge=1, description="Retry attempt number (1-based)")
    error: str = Field(..., description="Detailed validation error message explaining what went wrong")
    retrying: bool = Field(..., description="Whether the step will be retried (true) or if this was the final attempt (false)")


# Rebuild models to support forward references (for TaskItem.subtasks)
TaskItem.model_rebuild()
