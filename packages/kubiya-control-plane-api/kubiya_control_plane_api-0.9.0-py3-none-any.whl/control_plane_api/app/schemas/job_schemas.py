"""
Pydantic schemas for Jobs API.

This module defines request/response schemas for the Jobs CRUD API.
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, Dict, List, Any
from datetime import datetime
from croniter import croniter


class ExecutionEnvironment(BaseModel):
    """Execution environment configuration for jobs"""
    env_vars: Dict[str, str] = Field(default_factory=dict, description="Environment variables (key-value pairs)")
    secrets: List[str] = Field(default_factory=list, description="Secret names from Kubiya vault")
    integration_ids: List[str] = Field(default_factory=list, description="Integration UUIDs for delegated credentials")
    mcp_servers: Dict[str, Dict] = Field(
        default_factory=dict,
        description="MCP (Model Context Protocol) server configurations. Supports stdio, HTTP, and SSE transports."
    )


class JobCreate(BaseModel):
    """Schema for creating a new job"""
    name: str = Field(..., description="Job name", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Job description")
    enabled: bool = Field(True, description="Whether the job is enabled")

    # Trigger configuration
    trigger_type: str = Field(..., description="Trigger type: 'cron', 'webhook', or 'manual'")

    # Cron configuration (required if trigger_type is 'cron')
    cron_schedule: Optional[str] = Field(None, description="Cron expression (e.g., '0 17 * * *' for daily at 5pm)")
    cron_timezone: Optional[str] = Field("UTC", description="Timezone for cron schedule (e.g., 'America/New_York')")

    # Planning and execution configuration
    planning_mode: str = Field(
        default="predefined_agent",
        description="Planning mode: 'on_the_fly', 'predefined_agent', 'predefined_team', or 'predefined_workflow'"
    )

    # Entity to execute (required for predefined modes)
    entity_type: Optional[str] = Field(None, description="Entity type: 'agent', 'team', or 'workflow'")
    entity_id: Optional[str] = Field(None, description="Entity ID (agent_id, team_id, or workflow_id)")

    # Prompt configuration
    prompt_template: str = Field(..., description="Prompt template (can include {{variables}} for dynamic params)")
    system_prompt: Optional[str] = Field(None, description="Optional system prompt")

    # Executor routing configuration
    executor_type: str = Field(
        default="auto",
        description="Executor routing: 'auto', 'specific_queue', or 'environment'"
    )
    worker_queue_name: Optional[str] = Field(None, description="Worker queue name for 'specific_queue' executor type")
    environment_name: Optional[str] = Field(None, description="Environment name for 'environment' executor type")

    # Execution configuration
    config: Dict[str, Any] = Field(default_factory=dict, description="Additional execution config (timeout, retry, etc.)")
    execution_environment: Optional[ExecutionEnvironment] = Field(
        None,
        description="Execution environment: env vars, secrets, integrations"
    )

    @field_validator("trigger_type")
    @classmethod
    def validate_trigger_type(cls, v):
        valid_types = ["cron", "webhook", "manual"]
        if v not in valid_types:
            raise ValueError(f"trigger_type must be one of {valid_types}")
        return v

    @field_validator("planning_mode")
    @classmethod
    def validate_planning_mode(cls, v):
        valid_modes = ["on_the_fly", "predefined_agent", "predefined_team", "predefined_workflow"]
        if v not in valid_modes:
            raise ValueError(f"planning_mode must be one of {valid_modes}")
        return v

    @field_validator("executor_type")
    @classmethod
    def validate_executor_type(cls, v):
        valid_types = ["auto", "specific_queue", "environment"]
        if v not in valid_types:
            raise ValueError(f"executor_type must be one of {valid_types}")
        return v

    @field_validator("cron_schedule")
    @classmethod
    def validate_cron_schedule(cls, v):
        if v is not None:
            # Validate cron expression
            try:
                croniter(v)
            except Exception as e:
                raise ValueError(f"Invalid cron expression: {str(e)}")
        return v

    @model_validator(mode='after')
    def validate_cross_field_dependencies(self):
        # Validate cron_schedule required for cron trigger
        if self.trigger_type == "cron" and not self.cron_schedule:
            raise ValueError("cron_schedule is required when trigger_type is 'cron'")

        # Validate entity_id required for predefined modes
        if self.planning_mode in ["predefined_agent", "predefined_team", "predefined_workflow"] and not self.entity_id:
            raise ValueError(f"entity_id is required when planning_mode is '{self.planning_mode}'")

        # Validate worker_queue_name for specific_queue executor
        if self.executor_type == "specific_queue" and not self.worker_queue_name:
            raise ValueError("worker_queue_name is required when executor_type is 'specific_queue'")

        # Validate environment_name for environment executor
        if self.executor_type == "environment" and not self.environment_name:
            raise ValueError("environment_name is required when executor_type is 'environment'")

        return self


class JobUpdate(BaseModel):
    """Schema for updating an existing job"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    enabled: Optional[bool] = None

    # Trigger configuration
    trigger_type: Optional[str] = None
    cron_schedule: Optional[str] = None
    cron_timezone: Optional[str] = None

    # Planning and execution configuration
    planning_mode: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None

    # Prompt configuration
    prompt_template: Optional[str] = None
    system_prompt: Optional[str] = None

    # Executor routing configuration
    executor_type: Optional[str] = None
    worker_queue_name: Optional[str] = None
    environment_name: Optional[str] = None

    # Execution configuration
    config: Optional[Dict[str, Any]] = None
    execution_environment: Optional[ExecutionEnvironment] = None

    @field_validator("trigger_type")
    @classmethod
    def validate_trigger_type(cls, v):
        if v is not None:
            valid_types = ["cron", "webhook", "manual"]
            if v not in valid_types:
                raise ValueError(f"trigger_type must be one of {valid_types}")
        return v

    @field_validator("planning_mode")
    @classmethod
    def validate_planning_mode(cls, v):
        if v is not None:
            valid_modes = ["on_the_fly", "predefined_agent", "predefined_team", "predefined_workflow"]
            if v not in valid_modes:
                raise ValueError(f"planning_mode must be one of {valid_modes}")
        return v

    @field_validator("executor_type")
    @classmethod
    def validate_executor_type(cls, v):
        if v is not None:
            valid_types = ["auto", "specific_queue", "environment"]
            if v not in valid_types:
                raise ValueError(f"executor_type must be one of {valid_types}")
        return v

    @field_validator("cron_schedule")
    @classmethod
    def validate_cron_schedule(cls, v):
        if v is not None:
            try:
                croniter(v)
            except Exception as e:
                raise ValueError(f"Invalid cron expression: {str(e)}")
        return v


class JobResponse(BaseModel):
    """Schema for job response"""
    id: str
    organization_id: str
    name: str
    description: Optional[str]
    enabled: bool
    status: str

    # Trigger configuration
    trigger_type: str
    cron_schedule: Optional[str]
    cron_timezone: Optional[str]
    webhook_url: Optional[str] = Field(None, description="Full webhook URL (generated from webhook_url_path)")
    webhook_secret: Optional[str] = Field(None, description="Webhook HMAC secret for signature verification")
    temporal_schedule_id: Optional[str]

    # Planning and execution configuration
    planning_mode: str
    entity_type: Optional[str]
    entity_id: Optional[str]
    entity_name: Optional[str]

    # Prompt configuration
    prompt_template: str
    system_prompt: Optional[str]

    # Executor routing configuration
    executor_type: str
    worker_queue_name: Optional[str]
    environment_name: Optional[str]

    # Execution configuration
    config: Dict[str, Any]
    execution_environment: Optional[ExecutionEnvironment]

    # Execution tracking
    last_execution_id: Optional[str]
    last_execution_at: Optional[datetime]
    next_execution_at: Optional[datetime]
    total_executions: int
    successful_executions: int
    failed_executions: int
    execution_history: List[Dict[str, Any]]

    # Audit fields
    created_by: Optional[str]
    updated_by: Optional[str]
    created_by_email: Optional[str] = Field(None, description="Email of the user who created the job (enriched)")
    updated_by_email: Optional[str] = Field(None, description="Email of the user who last updated the job (enriched)")

    # Timestamps
    created_at: datetime
    updated_at: datetime
    last_triggered_at: Optional[datetime]

    class Config:
        from_attributes = True


class JobTriggerRequest(BaseModel):
    """Schema for manually triggering a job"""
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Parameters to substitute in prompt template (e.g., {{param_name}})"
    )
    config_override: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional config overrides for this execution"
    )


class JobTriggerResponse(BaseModel):
    """Schema for job trigger response"""
    job_id: str
    execution_id: str
    workflow_id: str
    status: str
    message: str


class JobExecutionHistoryItem(BaseModel):
    """Schema for a single job execution history item"""
    execution_id: str
    trigger_type: str
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_ms: Optional[int]
    error_message: Optional[str]
    trigger_metadata: Optional[Dict[str, Any]] = None


class JobExecutionHistoryResponse(BaseModel):
    """Schema for job execution history response"""
    job_id: str
    total_count: int
    executions: List[JobExecutionHistoryItem]


class WebhookPayload(BaseModel):
    """Schema for webhook trigger payload"""
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Parameters to substitute in prompt template"
    )
    config_override: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional config overrides for this execution"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional metadata for this webhook trigger"
    )
