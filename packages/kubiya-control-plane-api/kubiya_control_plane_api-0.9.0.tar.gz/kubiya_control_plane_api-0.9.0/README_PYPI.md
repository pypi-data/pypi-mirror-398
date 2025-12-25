# Kubiya Control Plane API

A multi-tenant AI agent orchestration and management platform built with FastAPI, Temporal, and PostgreSQL.

## Features

- **Multi-tenant Architecture**: Manage multiple projects, teams, and agents
- **Workflow Orchestration**: Temporal-based workflow execution
- **Flexible Agent Runtime**: Support for multiple agent types and skills
- **Policy Enforcement**: OPA-based policy engine for agent governance
- **Scalable Workers**: Distributed worker architecture for agent execution
- **Context Management**: Environment and team-specific context handling
- **LLM Integration**: Support for multiple LLM providers via LiteLLM
- **Comprehensive APIs**: RESTful APIs for all platform features

## Installation

### Using pip

```bash
pip install kubiya-control-plane-api
```

### With optional dependencies

```bash
# For API server
pip install kubiya-control-plane-api[api]

# For worker runtime
pip install kubiya-control-plane-api[worker]

# For development
pip install kubiya-control-plane-api[dev]

# All dependencies
pip install kubiya-control-plane-api[all]
```

### From source

```bash
git clone https://github.com/kubiyabot/agent-control-plane.git
cd agent-control-plane
pip install -e .
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
```

### 2. Run database migrations

```bash
alembic upgrade head
```

### 3. Start the API server

```bash
uvicorn control_plane_api.app.main:app --host 0.0.0.0 --port 7777 --reload
```

The API will be available at `http://localhost:7777`

### 4. Access the API documentation

Open your browser and navigate to:
- Swagger UI: `http://localhost:7777/api/docs`
- ReDoc: `http://localhost:7777/api/redoc`

### 5. Start a worker

To process agent execution workflows:

```bash
kubiya-control-plane-worker
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
pytest --cov=control_plane_api --cov-report=html
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
