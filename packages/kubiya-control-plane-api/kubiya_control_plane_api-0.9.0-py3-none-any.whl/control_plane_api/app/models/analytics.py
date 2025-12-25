"""
Analytics models for comprehensive execution tracking and reporting.

This module provides production-grade analytics tables to track:
- Per-turn LLM metrics (tokens, duration, cost)
- Tool execution details (success/failure, timing)
- Task completion tracking
- Organization-level reporting
"""

from sqlalchemy import Column, String, DateTime, Integer, Float, Boolean, Text, JSON, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func, text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from control_plane_api.app.database import Base


class ExecutionTurn(Base):
    """
    Tracks each LLM interaction turn within an execution.

    This provides granular metrics for each agent reasoning step,
    enabling detailed performance analysis and cost tracking.
    """

    __tablename__ = "execution_turns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)

    # Organization and execution context
    organization_id = Column(String, nullable=False, index=True)
    execution_id = Column(UUID(as_uuid=True), ForeignKey("executions.id", ondelete="CASCADE"), nullable=False, index=True)

    # Turn identification
    turn_number = Column(Integer, nullable=False)  # Sequential turn number in conversation
    turn_id = Column(String, nullable=True)  # Runtime-specific turn identifier

    # Model information
    model = Column(String, nullable=False)  # e.g., "claude-sonnet-4", "gpt-4"
    model_provider = Column(String, nullable=True)  # e.g., "anthropic", "openai"

    # Timing metrics
    started_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_ms = Column(Integer, nullable=True)  # Duration in milliseconds

    # Token usage metrics
    input_tokens = Column(Integer, nullable=True, server_default=text('0'))
    output_tokens = Column(Integer, nullable=True, server_default=text('0'))
    cache_read_tokens = Column(Integer, nullable=True, server_default=text('0'))  # Cached tokens (Anthropic)
    cache_creation_tokens = Column(Integer, nullable=True, server_default=text('0'))  # Cache creation tokens
    total_tokens = Column(Integer, nullable=True, server_default=text('0'))

    # Cost metrics (in USD)
    input_cost = Column(Float, nullable=True, server_default=text('0'))
    output_cost = Column(Float, nullable=True, server_default=text('0'))
    cache_read_cost = Column(Float, nullable=True, server_default=text('0'))
    cache_creation_cost = Column(Float, nullable=True, server_default=text('0'))
    total_cost = Column(Float, nullable=True, server_default=text('0'))

    # Agentic Engineering Minutes (AEM) metrics
    runtime_minutes = Column(Float, nullable=True, server_default=text('0'))  # duration_ms / 60000
    model_weight = Column(Float, nullable=True, server_default=text('1'))  # Model family weight (opus=2.0, sonnet=1.0, haiku=0.5)
    tool_calls_weight = Column(Float, nullable=True, server_default=text('1'))  # Tool complexity weight
    aem_value = Column(Float, nullable=True, server_default=text('0'))  # Calculated: runtime_minutes × model_weight × tool_calls_weight
    aem_cost = Column(Float, nullable=True, server_default=text('0'))  # AEM × price per AEM ($0.15/min default)

    # Turn result
    finish_reason = Column(String, nullable=True)  # "stop", "length", "tool_use", "error"
    response_preview = Column(Text, nullable=True)  # First 500 chars of response

    # Tool usage in this turn
    tools_called_count = Column(Integer, server_default=text('0'), nullable=False)
    tools_called_names = Column(JSON, server_default=text("'[]'::json"), nullable=False)  # List of tool names called

    # Error tracking
    error_message = Column(Text, nullable=True)

    # Additional metrics (JSON for flexibility)
    metrics = Column(JSON, server_default=text("'{}'::json"), nullable=False)  # Custom metrics, latencies, etc.

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Indexes for fast querying
    __table_args__ = (
        Index('ix_execution_turns_org_execution', 'organization_id', 'execution_id'),
        Index('ix_execution_turns_org_model', 'organization_id', 'model'),
        Index('ix_execution_turns_org_created', 'organization_id', 'created_at'),
        Index('ix_execution_turns_org_cost', 'organization_id', 'total_cost'),
    )

    def __repr__(self):
        return f"<ExecutionTurn {self.id} turn={self.turn_number} model={self.model} tokens={self.total_tokens} cost=${self.total_cost}>"


class ExecutionToolCall(Base):
    """
    Tracks individual tool/function calls within an execution.

    This enables detailed tool usage analytics, error tracking,
    and performance monitoring at the tool level.
    """

    __tablename__ = "execution_tool_calls"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)

    # Organization and execution context
    organization_id = Column(String, nullable=False, index=True)
    execution_id = Column(UUID(as_uuid=True), ForeignKey("executions.id", ondelete="CASCADE"), nullable=False, index=True)
    turn_id = Column(UUID(as_uuid=True), ForeignKey("execution_turns.id", ondelete="CASCADE"), nullable=True, index=True)

    # Tool identification
    tool_name = Column(String, nullable=False, index=True)  # e.g., "Read", "Bash", "WebFetch"
    tool_use_id = Column(String, nullable=True)  # Runtime-specific tool call ID

    # Timing
    started_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_ms = Column(Integer, nullable=True)  # Duration in milliseconds

    # Tool execution details
    tool_input = Column(JSON, nullable=True)  # Tool parameters
    tool_output = Column(Text, nullable=True)  # Tool result (truncated if large)
    tool_output_size = Column(Integer, nullable=True)  # Size in bytes

    # Status
    success = Column(Boolean, nullable=False, server_default=text('true'))
    error_message = Column(Text, nullable=True)
    error_type = Column(String, nullable=True)  # e.g., "TimeoutError", "PermissionError"

    # Additional metadata
    metadata_ = Column("metadata", JSON, server_default=text("'{}'::json"), nullable=False)  # Custom metrics, context, etc.

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Indexes for fast querying
    __table_args__ = (
        Index('ix_execution_tool_calls_org_execution', 'organization_id', 'execution_id'),
        Index('ix_execution_tool_calls_org_tool', 'organization_id', 'tool_name'),
        Index('ix_execution_tool_calls_org_success', 'organization_id', 'success'),
        Index('ix_execution_tool_calls_org_created', 'organization_id', 'created_at'),
    )

    def __repr__(self):
        status = "✓" if self.success else "✗"
        return f"<ExecutionToolCall {status} {self.tool_name} duration={self.duration_ms}ms>"


class ExecutionTask(Base):
    """
    Tracks high-level tasks/subtasks within an execution.

    Some runtimes (like Claude Code) break work into tasks with status tracking.
    This table captures that information for progress monitoring and analytics.
    """

    __tablename__ = "execution_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)

    # Organization and execution context
    organization_id = Column(String, nullable=False, index=True)
    execution_id = Column(UUID(as_uuid=True), ForeignKey("executions.id", ondelete="CASCADE"), nullable=False, index=True)

    # Task identification
    task_number = Column(Integer, nullable=True)  # Sequential task number
    task_id = Column(String, nullable=True)  # Runtime-specific task ID

    # Task details
    task_description = Column(Text, nullable=False)  # What is the task
    task_type = Column(String, nullable=True)  # e.g., "coding", "analysis", "research"

    # Status tracking
    status = Column(String, nullable=False, server_default=text("'pending'::character varying"))  # pending, in_progress, completed, failed

    # Timing
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_ms = Column(Integer, nullable=True)

    # Result
    result = Column(Text, nullable=True)  # Task outcome/result
    error_message = Column(Text, nullable=True)

    # Additional metadata
    custom_metadata = Column(JSON, server_default=text("'{}'::json"), nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Indexes
    __table_args__ = (
        Index('ix_execution_tasks_org_execution', 'organization_id', 'execution_id'),
        Index('ix_execution_tasks_org_status', 'organization_id', 'status'),
    )

    def __repr__(self):
        return f"<ExecutionTask {self.id} status={self.status} desc={self.task_description[:50]}>"
