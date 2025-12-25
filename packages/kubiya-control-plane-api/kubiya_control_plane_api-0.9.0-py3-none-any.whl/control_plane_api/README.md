# Kubiya Control Plane API

A multi-tenant AI agent orchestration and management platform built with FastAPI, Temporal, and PostgreSQL.

## Features

- **Multi-tenant Architecture**: Manage multiple projects, teams, and agents
- **Workflow Orchestration**: Temporal-based workflow execution
- **Flexible Agent Runtime**: Support for multiple agent types and skills
- **Policy Enforcement**: OPA-based policy engine for agent governance
- **Tool Call Enforcement**: Non-blocking validation of tool executions against policies
- **Event Bus System**: Pluggable multi-provider event streaming (HTTP, Redis, WebSocket, NATS)
- **Scalable Workers**: Distributed worker architecture for agent execution
- **Context Management**: Environment and team-specific context handling
- **LLM Integration**: Support for multiple LLM providers via LiteLLM
- **Comprehensive APIs**: RESTful APIs for all platform features

### Tool Call Enforcement

The platform includes **end-to-end tool call enforcement** that validates agent tool executions against OPA policies:

- **Non-blocking enforcement**: Policy violations are injected into tool outputs without failing workflows
- **Fail-open strategy**: Graceful degradation on timeout or error prevents blocking workflows
- **Automatic risk assessment**: Tools classified as critical/high/medium/low risk
- **Full context enrichment**: User, organization, team, and environment data included in policy evaluation
- **5 example policies**: Role-based access, production safeguards, bash validation, business hours, MCP allowlist

See the [Tool Enforcement Guide](../docs/TOOL_ENFORCEMENT.md) for detailed documentation.

### Event Bus System

The platform includes a **production-grade event bus abstraction** for real-time event streaming:

- **Multi-provider support**: HTTP, Redis, WebSocket, NATS
- **Parallel publishing**: Events sent to all providers simultaneously
- **Graceful degradation**: Continues if one provider fails
- **Optional dependencies**: Lightweight base package with optional providers
- **Comprehensive logging**: Structured JSON logs at every step
- **Health monitoring**: Per-provider and overall system health checks
- **Backwards compatible**: Falls back to direct Redis if not configured

**Quick Start:**

```bash
# Base package (HTTP, Redis, WebSocket)
pip install kubiya-control-plane-api

# With YAML config support
pip install kubiya-control-plane-api[yaml]

# With NATS provider
pip install kubiya-control-plane-api[nats]

# All event bus features
pip install kubiya-control-plane-api[event-bus]
```

**Configuration Example:**

```yaml
# config.yaml
event_bus:
  http:
    enabled: true
    base_url: http://localhost:8000
  redis:
    enabled: true
    redis_url: redis://localhost:6379
```

See the [Event Bus README](app/lib/event_bus/README.md) for detailed documentation.

## Installation

### Using pip

```bash
pip install kubiya-control_plane_api
```

### From source

```bash
git clone https://github.com/kubiyabot/agent-control-plane.git
cd agent-control-plane/control_plane_api
pip install -e .
```

### With development dependencies

```bash
pip install kubiya-control_plane_api[dev]
```

## Quick Start

### 1. Set up environment variables

Create a `.env` file or set the following environment variables:

```bash
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/control_plane

# Supabase (for serverless deployments)
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-key

# Temporal Configuration
TEMPORAL_HOST=localhost:7233
TEMPORAL_NAMESPACE=default

# API Configuration
API_TITLE="Agent Control Plane"
API_VERSION="1.0.0"
ENVIRONMENT=development
LOG_LEVEL=info

# Security
SECRET_KEY=your-secret-key-here

# Optional: Kubiya Integration
KUBIYA_API_KEY=your-kubiya-api-key
KUBIYA_API_URL=https://api.kubiya.ai

# Optional: Event Bus Configuration (or use YAML config)
EVENT_BUS_HTTP_ENABLED=true
EVENT_BUS_HTTP_BASE_URL=http://localhost:8000
EVENT_BUS_REDIS_ENABLED=true
```

**Alternatively, use YAML configuration** (recommended):

Create `config.yaml` or set `KUBIYA_CONFIG_FILE=/path/to/config.yaml`:

```yaml
event_bus:
  http:
    enabled: true
    base_url: http://localhost:8000
    batching_enabled: true
  redis:
    enabled: true
    redis_url: redis://localhost:6379
```

### 2. Run database migrations

```bash
alembic upgrade head
```

### 3. Start the API server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 7777 --reload
```

The API will be available at `http://localhost:7777`

### 4. Access the API documentation

Open your browser and navigate to:
- Swagger UI: `http://localhost:7777/api/docs`
- ReDoc: `http://localhost:7777/api/redoc`

### 5. Start a worker (optional)

To process agent execution workflows:

```bash
python worker.py
```

## Package Structure

```
app/
├── activities/          # Temporal activities
├── lib/                # Client libraries and utilities
│   ├── event_bus/      # Event bus abstraction (multi-provider)
│   │   ├── base.py     # Provider interface
│   │   ├── manager.py  # Manager orchestrator
│   │   └── providers/  # HTTP, Redis, WebSocket, NATS providers
│   ├── redis_client.py # Redis connection
│   └── temporal_client.py # Temporal connection
├── middleware/         # FastAPI middleware (auth, etc.)
├── models/             # SQLAlchemy models
├── policies/           # OPA policy files (.rego)
├── routers/            # FastAPI route handlers
├── services/           # Business logic services
├── skills/             # Agent skills
├── workflows/          # Temporal workflows
├── config.py           # Configuration management
├── database.py         # Database connection
└── main.py             # FastAPI application entry point
```

## API Endpoints

### Core Resources

- **Projects**: `/api/v1/projects` - Multi-project management
- **Environments**: `/api/v1/environments` - Environment configuration
- **Agents**: `/api/v1/agents` - Agent management
- **Teams**: `/api/v1/teams` - Team management
- **Workflows**: `/api/v1/workflows` - Workflow definitions
- **Executions**: `/api/v1/executions` - Execution tracking
- **Workers**: `/api/v1/workers` - Worker registration and management

### Skills and Policies

- **Skills**: `/api/v1/skills` - Tool sets and definitions
- **Policies**: `/api/v1/policies` - Policy management and enforcement

### Integration

- **Secrets**: `/api/v1/secrets` - Secrets management (proxies to Kubiya)
- **Integrations**: `/api/v1/integrations` - Third-party integrations
- **Models**: `/api/v1/models` - LLM model configuration

### Utilities

- **Health**: `/api/health` - Health check endpoint
- **Event Bus Health**: `/api/health/event-bus` - Event bus provider health
- **Task Planning**: `/api/v1/task-planning` - AI-powered task planning

## Configuration

The application uses Pydantic Settings for configuration management. All settings can be configured via environment variables or a `.env` file.

### Key Configuration Options

- `DATABASE_URL`: PostgreSQL connection string
- `SUPABASE_URL`, `SUPABASE_KEY`: Supabase configuration for serverless
- `TEMPORAL_HOST`: Temporal server address
- `KUBIYA_API_KEY`: Kubiya platform API key
- `SECRET_KEY`: Secret key for JWT token signing
- `LOG_LEVEL`: Logging level (debug, info, warning, error)
- `ENVIRONMENT`: Deployment environment (development, staging, production)

## Development

### Install development dependencies

```bash
pip install -e ".[dev]"
```

### Run tests

```bash
# All tests
pytest

# Unit tests only
pytest -m unit

# Integration tests
pytest -m integration

# With coverage
pytest --cov=app --cov-report=html
```

### Code formatting

```bash
# Format code with black
black .

# Lint with ruff
ruff check .
```

### Database migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Deployment

### Docker

```bash
docker build -t control_plane_api .
docker run -p 7777:7777 --env-file .env control_plane_api
```

### Vercel (Serverless)

The API is configured for Vercel deployment with `vercel.json` and the Mangum adapter.

```bash
vercel deploy
```

## Architecture

### Workflow Orchestration

The platform uses Temporal for reliable workflow execution:
- Durable execution with automatic retries
- Activity-based task decomposition
- Support for long-running workflows
- Built-in observability and monitoring

### Multi-tenancy

- **Projects**: Top-level isolation boundary
- **Environments**: Isolated execution contexts within projects
- **Teams**: Collaborative agent groups
- **Agents**: Individual agent instances

### Worker Architecture

Workers pull tasks from environment-specific queues and execute agent workflows using Temporal.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

GNU Affero General Public License v3.0 (AGPL-3.0) - see LICENSE file for details

## Support

For issues and questions:
- GitHub Issues: https://github.com/kubiyabot/agent-control-plane/issues
- Email: support@kubiya.ai

## Links

- [Documentation](https://github.com/kubiyabot/agent-control-plane/blob/main/README.md)
- [GitHub Repository](https://github.com/kubiyabot/agent-control-plane)
- [Kubiya Platform](https://kubiya.ai)

