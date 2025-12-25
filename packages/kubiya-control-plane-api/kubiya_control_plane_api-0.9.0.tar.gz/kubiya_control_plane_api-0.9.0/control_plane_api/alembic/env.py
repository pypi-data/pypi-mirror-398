from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Import application settings and models
import sys
from pathlib import Path

# Add parent directory to path so control_plane_api is importable
# env.py location: /app/control_plane_api/alembic/env.py
# We need: /app (which is parent.parent.parent)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from control_plane_api.app.config import settings
from control_plane_api.app.database import Base

from control_plane_api.app.models.project import Project, ProjectStatus
from control_plane_api.app.models.agent import Agent, AgentStatus, RuntimeType as AgentRuntimeType
from control_plane_api.app.models.team import Team, TeamStatus, RuntimeType as TeamRuntimeType
from control_plane_api.app.models.session import Session
from control_plane_api.app.models.execution import Execution, ExecutionStatus, ExecutionType, ExecutionTriggerSource
from control_plane_api.app.models.environment import Environment, EnvironmentStatus
from control_plane_api.app.models.associations import AgentEnvironment, TeamEnvironment, ExecutionParticipant, ParticipantRole
from control_plane_api.app.models.job import Job, JobExecution, JobStatus, JobTriggerType, ExecutorType, PlanningMode
from control_plane_api.app.models.skill import Skill, SkillAssociation, SlashCommand, SlashCommandExecution, SkillType, SkillEntityType, SlashCommandStatus
from control_plane_api.app.models.worker import Worker, WorkerHeartbeat, WorkerQueue, OrchestrationServer, OrchestrationServerHealth, WorkerStatus, WorkerRegistrationStatus, QueueStatus, ServerHealthStatus
from control_plane_api.app.models.orchestration import Namespace
from control_plane_api.app.models.context import AgentContext, EnvironmentContext, ProjectContext, TeamContext, ContextResource
from control_plane_api.app.models.analytics import ExecutionTurn, ExecutionToolCall, ExecutionTask
from control_plane_api.app.models.project_management import Profile, ProjectAgent, ProjectTeam
from control_plane_api.app.models.llm_model import LLMModel
from control_plane_api.app.models.presence import UserPresence
from control_plane_api.app.models.workflow import Workflow
from control_plane_api.app.models.system_tables import (PolicyAssociation)
# NOTE: auth_user is NOT imported because auth.users is an external table managed by Supabase
# The foreign key from profiles uses use_alter=True to handle the reference
from control_plane_api.app.models.workspace import Workspace
from control_plane_api.app.models.user_profile import UserProfile

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Override sqlalchemy.url with our DATABASE_URL from settings
if settings.database_url:
    # Escape % characters for ConfigParser (% -> %%)
    escaped_url = settings.database_url.replace("%", "%%")
    config.set_main_option("sqlalchemy.url", escaped_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
