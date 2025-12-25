"""
Integration Templates Router

API endpoints for managing and using integration templates.
Templates provide pre-configured integration definitions for common providers.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/integration-templates", tags=["integration-templates"])


# Integration Templates for Common Providers
INTEGRATION_TEMPLATES = {
    "postgres": {
        "name": "PostgreSQL Database",
        "integration_type": "postgres",
        "description": "PostgreSQL database connection with SSL support",
        "icon": "PostgreSQL",
        "category": "database",
        "config": {
            "env_vars": {
                "DB_HOST": "localhost",
                "DB_PORT": "5432",
                "DB_NAME": "postgres",
                "DB_USER": "postgres"
            },
            "secrets": ["DB_PASSWORD"],
            "files": [
                {
                    "path": "~/.postgresql/client.crt",
                    "secret_ref": "POSTGRES_CLIENT_CERT",
                    "mode": "0600",
                    "description": "PostgreSQL client certificate"
                },
                {
                    "path": "~/.postgresql/client.key",
                    "secret_ref": "POSTGRES_CLIENT_KEY",
                    "mode": "0600",
                    "description": "PostgreSQL client key"
                }
            ],
            "context_prompt": "PostgreSQL relational database. Use parameterized queries to prevent SQL injection. Connection pooling is recommended for better performance.",
            "connection_test": {
                "enabled": True,
                "command": "pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER",
                "timeout": 5
            }
        },
        "tags": ["database", "postgres", "sql", "relational"]
    },
    "mysql": {
        "name": "MySQL Database",
        "integration_type": "mysql",
        "description": "MySQL relational database connection",
        "icon": "MySQL",
        "category": "database",
        "config": {
            "env_vars": {
                "MYSQL_HOST": "localhost",
                "MYSQL_PORT": "3306",
                "MYSQL_DATABASE": "mysql",
                "MYSQL_USER": "root"
            },
            "secrets": ["MYSQL_PASSWORD"],
            "files": [
                {
                    "path": "~/.my.cnf",
                    "content": "[client]\nhost=${MYSQL_HOST}\nport=${MYSQL_PORT}\nuser=${MYSQL_USER}\npassword=${MYSQL_PASSWORD}",
                    "mode": "0600",
                    "description": "MySQL client configuration"
                }
            ],
            "context_prompt": "MySQL relational database. Use transactions for data consistency. Avoid SELECT * in production queries.",
            "connection_test": {
                "enabled": True,
                "command": "mysqladmin -h $MYSQL_HOST -P $MYSQL_PORT -u $MYSQL_USER ping",
                "timeout": 5
            }
        },
        "tags": ["database", "mysql", "sql", "relational"]
    },
    "mongodb": {
        "name": "MongoDB Database",
        "integration_type": "mongodb",
        "description": "MongoDB NoSQL document database",
        "icon": "MongoDB",
        "category": "database",
        "config": {
            "env_vars": {
                "MONGO_HOST": "localhost",
                "MONGO_PORT": "27017",
                "MONGO_DATABASE": "admin"
            },
            "secrets": ["MONGO_CONNECTION_STRING"],
            "context_prompt": "MongoDB NoSQL database. Use connection pooling for better performance. Always use indexes for query optimization.",
            "connection_test": {
                "enabled": True,
                "command": "mongosh $MONGO_CONNECTION_STRING --eval 'db.runCommand({ping: 1})'",
                "timeout": 5
            }
        },
        "tags": ["database", "mongodb", "nosql", "document"]
    },
    "redis": {
        "name": "Redis Cache",
        "integration_type": "redis",
        "description": "Redis in-memory data store and cache",
        "icon": "Redis",
        "category": "cache",
        "config": {
            "env_vars": {
                "REDIS_HOST": "localhost",
                "REDIS_PORT": "6379",
                "REDIS_DB": "0"
            },
            "secrets": ["REDIS_PASSWORD"],
            "context_prompt": "Redis in-memory cache. All keys have TTL. Use for session storage, caching, and rate limiting. Data is not persistent by default.",
            "connection_test": {
                "enabled": True,
                "command": "redis-cli -h $REDIS_HOST -p $REDIS_PORT -a $REDIS_PASSWORD ping",
                "timeout": 5
            }
        },
        "tags": ["cache", "redis", "in-memory", "key-value"]
    },
    "elasticsearch": {
        "name": "Elasticsearch Cluster",
        "integration_type": "elasticsearch",
        "description": "Elasticsearch search and analytics engine",
        "icon": "Elasticsearch",
        "category": "search",
        "config": {
            "env_vars": {
                "ES_HOST": "localhost",
                "ES_PORT": "9200",
                "ES_SCHEME": "https"
            },
            "secrets": ["ES_USERNAME", "ES_PASSWORD", "ES_API_KEY"],
            "files": [
                {
                    "path": "~/.elasticsearch/ca.crt",
                    "secret_ref": "ES_CA_CERT",
                    "mode": "0644",
                    "description": "Elasticsearch CA certificate"
                }
            ],
            "context_prompt": "Elasticsearch for full-text search and analytics. Use bulk API for large datasets. Optimize mappings for your use case.",
            "connection_test": {
                "enabled": True,
                "command": "curl -k $ES_SCHEME://$ES_HOST:$ES_PORT/_cluster/health",
                "timeout": 10
            }
        },
        "tags": ["search", "elasticsearch", "analytics", "full-text"]
    },
    "rabbitmq": {
        "name": "RabbitMQ Message Broker",
        "integration_type": "rabbitmq",
        "description": "RabbitMQ message queue and broker",
        "icon": "RabbitMQ",
        "category": "messaging",
        "config": {
            "env_vars": {
                "RABBITMQ_HOST": "localhost",
                "RABBITMQ_PORT": "5672",
                "RABBITMQ_VHOST": "/"
            },
            "secrets": ["RABBITMQ_USER", "RABBITMQ_PASSWORD"],
            "context_prompt": "RabbitMQ message broker. Use acknowledgments for reliable message processing. Configure dead letter queues for failed messages.",
            "connection_test": {
                "enabled": True,
                "command": "rabbitmqctl status",
                "timeout": 5
            }
        },
        "tags": ["messaging", "rabbitmq", "queue", "amqp"]
    },
    "kafka": {
        "name": "Apache Kafka",
        "integration_type": "kafka",
        "description": "Apache Kafka distributed streaming platform",
        "icon": "Kafka",
        "category": "messaging",
        "config": {
            "env_vars": {
                "KAFKA_BOOTSTRAP_SERVERS": "localhost:9092",
                "KAFKA_GROUP_ID": "default"
            },
            "secrets": ["KAFKA_SASL_USERNAME", "KAFKA_SASL_PASSWORD"],
            "context_prompt": "Apache Kafka streaming platform. Use consumer groups for scalability. Configure retention policies appropriately.",
            "connection_test": {
                "enabled": True,
                "command": "kafka-broker-api-versions --bootstrap-server $KAFKA_BOOTSTRAP_SERVERS",
                "timeout": 10
            }
        },
        "tags": ["messaging", "kafka", "streaming", "event-driven"]
    },
    "api": {
        "name": "Custom REST API",
        "integration_type": "api",
        "description": "Generic REST API integration",
        "icon": "API",
        "category": "api",
        "config": {
            "env_vars": {
                "API_BASE_URL": "https://api.example.com",
                "API_VERSION": "v1",
                "API_TIMEOUT": "30"
            },
            "secrets": ["API_KEY", "API_SECRET"],
            "context_prompt": "REST API integration. Always check rate limits. Use exponential backoff for retries. Handle errors gracefully.",
        },
        "tags": ["api", "rest", "http", "web-service"]
    },
    "sftp": {
        "name": "SFTP Server",
        "integration_type": "sftp",
        "description": "SFTP file transfer server",
        "icon": "SFTP",
        "category": "file-transfer",
        "config": {
            "env_vars": {
                "SFTP_HOST": "sftp.example.com",
                "SFTP_PORT": "22",
                "SFTP_USER": "user"
            },
            "secrets": ["SFTP_PASSWORD"],
            "files": [
                {
                    "path": "~/.ssh/sftp_key",
                    "secret_ref": "SFTP_PRIVATE_KEY",
                    "mode": "0600",
                    "description": "SFTP private key for authentication"
                }
            ],
            "context_prompt": "SFTP server for secure file transfers. Always verify file integrity after upload. Use batch operations when possible.",
        },
        "tags": ["file-transfer", "sftp", "ssh", "secure"]
    },
    "s3": {
        "name": "AWS S3 Storage",
        "integration_type": "s3",
        "description": "AWS S3 object storage",
        "icon": "S3",
        "category": "storage",
        "config": {
            "env_vars": {
                "S3_BUCKET": "my-bucket",
                "S3_REGION": "us-east-1",
                "S3_ENDPOINT": ""
            },
            "secrets": ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
            "context_prompt": "AWS S3 object storage. Use multipart upload for large files. Consider lifecycle policies for cost optimization.",
            "connection_test": {
                "enabled": True,
                "command": "aws s3 ls s3://$S3_BUCKET --region $S3_REGION",
                "timeout": 10
            }
        },
        "tags": ["storage", "s3", "aws", "object-storage"]
    }
}


# Pydantic Models
class IntegrationTemplateResponse(BaseModel):
    """Integration template response"""
    template_id: str
    name: str
    integration_type: str
    description: str
    icon: Optional[str] = None
    category: str
    config: Dict[str, Any]
    tags: List[str]

    class Config:
        json_schema_extra = {
            "example": {
                "template_id": "postgres",
                "name": "PostgreSQL Database",
                "integration_type": "postgres",
                "description": "PostgreSQL database connection with SSL support",
                "icon": "PostgreSQL",
                "category": "database",
                "config": {
                    "env_vars": {"DB_HOST": "localhost"},
                    "secrets": ["DB_PASSWORD"]
                },
                "tags": ["database", "postgres", "sql"]
            }
        }


class IntegrationTemplateSummary(BaseModel):
    """Brief template summary for listing"""
    template_id: str
    name: str
    integration_type: str
    description: str
    icon: Optional[str] = None
    category: str
    tags: List[str]


# API Endpoints

@router.get(
    "",
    response_model=List[IntegrationTemplateSummary],
    summary="List Integration Templates",
    description="""
    List all pre-configured integration templates.

    **Available Categories:**
    - database (PostgreSQL, MySQL, MongoDB, Elasticsearch)
    - cache (Redis)
    - messaging (RabbitMQ, Kafka)
    - storage (S3, SFTP)
    - api (Generic REST API)

    **Filtering:**
    - `category`: Filter by category name
    - `tag`: Filter by single tag
    - `search`: Search in name and description

    **Usage:**
    Templates provide pre-configured integration definitions that can be
    customized when creating a custom integration instance.

    **Example:**
    ```
    GET /api/v1/integration-templates?category=database
    GET /api/v1/integration-templates?tag=sql
    GET /api/v1/integration-templates?search=postgres
    ```
    """,
    responses={
        200: {
            "description": "List of integration templates",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "template_id": "postgres",
                            "name": "PostgreSQL Database",
                            "integration_type": "postgres",
                            "description": "PostgreSQL database with SSL support",
                            "icon": "PostgreSQL",
                            "category": "database",
                            "tags": ["database", "postgres", "sql", "relational"]
                        }
                    ]
                }
            }
        }
    }
)
async def list_integration_templates(
    category: Optional[str] = Query(None, description="Filter by category (database, cache, messaging, storage, api)"),
    tag: Optional[str] = Query(None, description="Filter by tag (e.g., sql, nosql, messaging)"),
    search: Optional[str] = Query(None, description="Search in template name and description"),
):
    """List all available pre-configured integration templates."""
    templates = []

    for template_id, template_data in INTEGRATION_TEMPLATES.items():
        # Apply filters
        if category and template_data.get("category") != category:
            continue

        if tag and tag not in template_data.get("tags", []):
            continue

        if search:
            search_lower = search.lower()
            if (search_lower not in template_data.get("name", "").lower() and
                search_lower not in template_data.get("description", "").lower()):
                continue

        templates.append(IntegrationTemplateSummary(
            template_id=template_id,
            name=template_data["name"],
            integration_type=template_data["integration_type"],
            description=template_data["description"],
            icon=template_data.get("icon"),
            category=template_data.get("category", "other"),
            tags=template_data.get("tags", [])
        ))

    logger.info(
        "integration_templates_listed",
        count=len(templates),
        filters={"category": category, "tag": tag, "search": search}
    )

    return templates


@router.get(
    "/{template_id}",
    response_model=IntegrationTemplateResponse,
    summary="Get Integration Template",
    description="""
    Retrieve complete configuration for a specific integration template.

    **Returns:**
    - Full template configuration
    - Environment variable definitions
    - Required secrets list
    - File configurations (with examples)
    - Context prompt for AI agents
    - Connection test command (if applicable)
    - Tags and metadata

    **Available Templates:**
    - postgres, mysql, mongodb, elasticsearch
    - redis
    - rabbitmq, kafka
    - s3, sftp
    - api (generic)

    **Usage:**
    Use this endpoint to get the template configuration before creating
    a custom integration instance. Customize the returned config as needed.

    **Example:**
    ```
    GET /api/v1/integration-templates/postgres
    ```
    """,
    responses={
        200: {"description": "Template details with full configuration"},
        404: {"description": "Template not found"}
    }
)
async def get_integration_template(template_id: str):
    """Retrieve detailed configuration for a specific integration template."""
    if template_id not in INTEGRATION_TEMPLATES:
        raise HTTPException(
            status_code=404,
            detail=f"Integration template '{template_id}' not found"
        )

    template_data = INTEGRATION_TEMPLATES[template_id]

    logger.info(
        "integration_template_fetched",
        template_id=template_id,
        template_name=template_data["name"]
    )

    return IntegrationTemplateResponse(
        template_id=template_id,
        name=template_data["name"],
        integration_type=template_data["integration_type"],
        description=template_data["description"],
        icon=template_data.get("icon"),
        category=template_data.get("category", "other"),
        config=template_data["config"],
        tags=template_data.get("tags", [])
    )


@router.get("/categories/list", response_model=List[str])
async def list_template_categories():
    """
    List all available template categories.

    Returns a list of unique categories across all templates.
    """
    categories = set()
    for template_data in INTEGRATION_TEMPLATES.values():
        categories.add(template_data.get("category", "other"))

    return sorted(list(categories))


@router.get("/tags/list", response_model=List[str])
async def list_template_tags():
    """
    List all available template tags.

    Returns a list of unique tags across all templates.
    """
    tags = set()
    for template_data in INTEGRATION_TEMPLATES.values():
        tags.update(template_data.get("tags", []))

    return sorted(list(tags))
