from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import structlog

from control_plane_api.app.config import settings
from control_plane_api.app.routers import agents, teams, workflows, health, executions, presence, runners, workers, projects, models, models_v2, task_queues, worker_queues, environment_context, team_context, context_manager, skills, skills_definitions, environments, runtimes, secrets, integrations, custom_integrations, integration_templates, execution_environment, policies, task_planning, jobs, analytics, context_graph, templates, enforcer, auth, storage, client_config
from control_plane_api.app.routers import agents_v2  # New multi-tenant agent router

# Configure structured logging
import logging

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(
        getattr(logging, settings.log_level.upper(), logging.INFO)
    ),
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info(
        "agent_control_plane_starting",
        version=settings.api_version,
        environment=settings.environment
    )
    # No database initialization needed for serverless
    # Supabase client is initialized on-demand

    # Initialize event bus if configured
    event_bus_manager = None
    if hasattr(settings, 'event_bus') and settings.event_bus:
        try:
            from control_plane_api.app.lib.event_bus.manager import EventBusManager, EventBusManagerConfig

            manager_config = EventBusManagerConfig(**settings.event_bus)
            event_bus_manager = EventBusManager(manager_config)
            await event_bus_manager.initialize()

            # Store in app state for access by routes
            app.state.event_bus = event_bus_manager

            logger.info(
                "event_bus_initialized",
                providers=event_bus_manager.get_provider_names(),
                count=len(event_bus_manager.providers)
            )
        except ImportError as e:
            logger.warning(
                "event_bus_dependencies_missing",
                error=str(e),
                message="Install event bus dependencies with: pip install kubiya-control-plane-api[event-bus]"
            )
        except Exception as e:
            logger.error(
                "event_bus_initialization_failed",
                error=str(e),
                message="Event bus will not be available"
            )

    yield

    # Shutdown event bus
    if event_bus_manager:
        try:
            await event_bus_manager.shutdown()
            logger.info("event_bus_shutdown")
        except Exception as e:
            logger.error("event_bus_shutdown_failed", error=str(e))

    logger.info("agent_control_plane_shutting_down")


# Create FastAPI application
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="""
## Kubiya Agent Control Plane API

Complete API for managing AI agents, skills, integrations, and workflows.

### Features
- 🤖 **Agent Management** - Create and manage AI agents with custom skills
- 🔌 **Integrations** - Connect to databases, APIs, and services
- 🛠️ **Tool Sets** - Manage agent capabilities and tools
- 📊 **Workflows** - Orchestrate complex automation flows
- 🔐 **Security** - Secrets management and access control
- 📈 **Analytics** - Monitor agent performance and usage

### Getting Started
1. Obtain your API token from the Kubiya dashboard
2. Click "Authorize" button and enter your token
3. Explore the API endpoints organized by category
4. Try the interactive examples with "Try it out"

### Support
- [Documentation](https://docs.kubiya.ai)
- [API Reference](https://docs.kubiya.ai/api)
- [Support Portal](https://support.kubiya.ai)
    """,
    lifespan=lifespan,
    # Disable lifespan for Vercel (will be "off" via Mangum)
    openapi_url="/api/openapi.json" if settings.environment != "production" else None,
    docs_url="/api/docs" if settings.environment != "production" else None,
    redoc_url=None,  # Using custom ReDoc page instead
    # Configure OpenAPI security scheme for Swagger UI
    swagger_ui_parameters={
        "persistAuthorization": True,  # Remember auth token across page refreshes
        "deepLinking": True,  # Enable deep linking for sharing specific endpoint URLs
        "displayOperationId": False,  # Hide operation IDs for cleaner UI
        "defaultModelsExpandDepth": 1,  # Collapse models by default
        "defaultModelExpandDepth": 1,  # Show only first level of model properties
        "displayRequestDuration": True,  # Show request duration in UI
        "filter": True,  # Enable search/filter functionality
        "showExtensions": True,  # Show vendor extensions
        "showCommonExtensions": True,  # Show common extensions
        "syntaxHighlight.theme": "monokai",  # Better syntax highlighting theme
        "docExpansion": "list",  # Show tags/operations but collapse details (none/list/full)
    },
    contact={
        "name": "Kubiya Support",
        "url": "https://support.kubiya.ai",
        "email": "support@kubiya.ai"
    },
    license_info={
        "name": "Proprietary",
        "url": "https://kubiya.ai/terms"
    },
)

# Configure security scheme for OpenAPI/Swagger
from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=settings.api_title,
        version=settings.api_version,
        description=settings.api_description,
        routes=app.routes,
    )

    # Add security scheme for Bearer token
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter your Kubiya API token (format: Bearer <token>)",
        }
    }

    # Apply security globally to all endpoints
    openapi_schema["security"] = [{"BearerAuth": []}]

    # Add tags metadata for better organization in Swagger UI
    openapi_schema["tags"] = [
        {
            "name": "health",
            "description": "🏥 **Health & Status** - Check API health and availability"
        },
        {
            "name": "authentication",
            "description": "🔐 **Authentication** - Token validation and auth management"
        },
        {
            "name": "agents",
            "description": "🤖 **Agents** - Create and manage AI agents with custom capabilities"
        },
        {
            "name": "skills",
            "description": "🛠️ **Tool Sets** - Manage agent skills and tool configurations"
        },
        {
            "name": "integrations",
            "description": "🔌 **Integrations** - Connect to external services (Kubiya managed)"
        },
        {
            "name": "custom-integrations",
            "description": "⚙️ **Custom Integrations** - User-defined integration instances with env vars, secrets, and files"
        },
        {
            "name": "integration-templates",
            "description": "📦 **Integration Templates** - Pre-configured templates for common services (PostgreSQL, Redis, MongoDB, etc.)"
        },
        {
            "name": "secrets",
            "description": "🔑 **Secrets** - Secure credential storage and retrieval"
        },
        {
            "name": "teams",
            "description": "👥 **Teams** - Team management and collaboration"
        },
        {
            "name": "workflows",
            "description": "📊 **Workflows** - Multi-step automation and orchestration"
        },
        {
            "name": "executions",
            "description": "▶️ **Executions** - Track and monitor workflow runs"
        },
        {
            "name": "jobs",
            "description": "⏰ **Jobs** - Scheduled and webhook-triggered tasks"
        },
        {
            "name": "policies",
            "description": "🛡️ **Policies** - Access control and security policies"
        },
        {
            "name": "analytics",
            "description": "📈 **Analytics** - Usage metrics and performance monitoring"
        },
        {
            "name": "projects",
            "description": "📁 **Projects** - Project organization and management"
        },
        {
            "name": "environments",
            "description": "🌍 **Environments** - Environment configuration (dev, staging, prod)"
        },
        {
            "name": "models",
            "description": "🧠 **Models** - LLM model configuration and management"
        },
        {
            "name": "runtimes",
            "description": "⚡ **Runtimes** - Agent execution runtime environments"
        },
        {
            "name": "workers",
            "description": "👷 **Workers** - Worker registration and heartbeat monitoring"
        },
        {
            "name": "storage",
            "description": "💾 **Storage** - File storage and cloud integration"
        },
        {
            "name": "context-graph",
            "description": "🕸️ **Context Graph** - Knowledge graph and context management"
        },
        {
            "name": "templates",
            "description": "📝 **Templates** - Reusable configuration templates"
        },
    ]

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers (all routes under /api/v1)
# NOTE: tags parameter is omitted to use tags defined in each router, preventing duplicates in Swagger UI
app.include_router(health.router, prefix="/api")
app.include_router(auth.router)  # Auth validation for delegated auth from other services
app.include_router(client_config.router, prefix="/api/v1")  # Client configuration for service discovery
app.include_router(models_v2.router, prefix="/api/v1/models")  # LLM models CRUD (database-backed)
app.include_router(runtimes.router, prefix="/api/v1")  # Agent runtime types
app.include_router(secrets.router, prefix="/api/v1")  # Kubiya secrets proxy
app.include_router(integrations.router, prefix="/api/v1")  # Kubiya integrations proxy
app.include_router(custom_integrations.router, prefix="/api/v1")  # Custom user-defined integrations
app.include_router(integration_templates.router, prefix="/api/v1")  # Pre-configured integration templates
app.include_router(context_graph.router, prefix="/api/v1")  # Context Graph API proxy
app.include_router(templates.router, prefix="/api/v1")  # Template compilation and validation
app.include_router(execution_environment.router, prefix="/api/v1")  # Resolved execution environment for workers
app.include_router(projects.router, prefix="/api/v1/projects")  # Multi-project management
app.include_router(environments.router, prefix="/api/v1/environments")  # Environment management
app.include_router(task_queues.router, prefix="/api/v1/task-queues")  # Legacy endpoint (use /environments)
app.include_router(worker_queues.router, prefix="/api/v1")  # Worker queue management per environment
app.include_router(environment_context.router, prefix="/api/v1")  # Environment context management
app.include_router(team_context.router, prefix="/api/v1")  # Team context management
app.include_router(context_manager.router, prefix="/api/v1")  # Unified context management
app.include_router(skills_definitions.router, prefix="/api/v1/skills")  # Skill definitions and templates (must be before skills.router)
app.include_router(skills.router, prefix="/api/v1/skills")  # Tool sets management
app.include_router(enforcer.router, prefix="/api/v1")  # OPA Watchdog enforcer proxy
app.include_router(policies.router, prefix="/api/v1/policies")  # Policy management and enforcement
app.include_router(task_planning.router, prefix="/api/v1")  # AI-powered task planning
app.include_router(agents_v2.router, prefix="/api/v1/agents")  # Use new multi-tenant router
app.include_router(runners.router, prefix="/api/v1/runners")  # Proxy to Kubiya API
app.include_router(workers.router, prefix="/api/v1/workers")  # Worker registration and heartbeats
app.include_router(teams.router, prefix="/api/v1/teams")
app.include_router(workflows.router, prefix="/api/v1/workflows")
app.include_router(executions.router, prefix="/api/v1/executions")
app.include_router(presence.router, prefix="/api/v1/presence")
app.include_router(jobs.router, prefix="/api/v1/jobs")  # Scheduled and webhook-triggered jobs
app.include_router(analytics.router, prefix="/api/v1/analytics")  # Execution metrics and reporting
app.include_router(storage.router, prefix="/api/v1/storage")  # Remote filesystem and cloud storage


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint - Beautiful landing page with service status"""
    from fastapi.responses import HTMLResponse
    from pathlib import Path

    template_path = Path(__file__).parent / "templates" / "index.html"

    if template_path.exists():
        html_content = template_path.read_text()
        # Replace template variables
        html_content = html_content.replace("{{ version }}", settings.api_version)
        return HTMLResponse(content=html_content)

    # Fallback to JSON if template not found
    return {
        "message": "Welcome to Agent Control Plane",
        "version": settings.api_version,
        "environment": settings.environment,
        "docs": "/api/docs" if settings.environment != "production" else None,
    }


@app.get("/api/spec", include_in_schema=False)
async def openapi_viewer():
    """OpenAPI JSON viewer with search and formatting"""
    from fastapi.responses import HTMLResponse
    from pathlib import Path

    template_path = Path(__file__).parent / "templates" / "openapi-viewer.html"

    if template_path.exists():
        html_content = template_path.read_text()
        return HTMLResponse(content=html_content)

    # Fallback to raw JSON
    from fastapi.responses import JSONResponse
    return JSONResponse(content=app.openapi())


@app.get("/api")
async def api_root():
    """API root endpoint"""
    return {
        "message": "Agent Control Plane API",
        "version": settings.api_version,
        "endpoints": {
            "projects": "/api/v1/projects",
            "task_queues": "/api/v1/task-queues",
            "agents": "/api/v1/agents",
            "teams": "/api/v1/teams",
            "skills": "/api/v1/skills",
            "policies": "/api/v1/policies",
            "workflows": "/api/v1/workflows",
            "executions": "/api/v1/executions",
            "presence": "/api/v1/presence",
            "runners": "/api/v1/runners",
            "workers": "/api/v1/workers",
            "models": "/api/v1/models",
            "runtimes": "/api/v1/runtimes",
            "secrets": "/api/v1/secrets",
            "integrations": "/api/v1/integrations",
            "context_graph": "/api/v1/context-graph",
            "health": "/api/health",
        }
    }
