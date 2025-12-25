"""Redis client for caching authentication tokens and user data.

Supports two modes:
1. Upstash REST API (serverless-friendly) - uses KV_REST_API_URL/TOKEN or UPSTASH_* env vars
2. Standard Redis (TCP connection) - uses REDIS_URL env var (e.g., redis://localhost:6379)
"""

import os
import json
from typing import Optional, Any
import httpx
import structlog

logger = structlog.get_logger()

# Redis configuration cache
_redis_client: Optional[Any] = None
_redis_client_type: Optional[str] = None  # "upstash" or "standard"


class UpstashRedisClient:
    """Upstash Redis client using direct HTTP REST API calls (serverless-friendly)."""

    def __init__(self, url: str, token: str):
        self.url = url.rstrip('/')
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        # Use a shared async client for connection reuse and better performance
        # This avoids creating a new connection for every Redis operation
        self._client: Optional[httpx.AsyncClient] = None

    def _get_client(self) -> httpx.AsyncClient:
        """Get or create the shared HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(5.0, connect=2.0),
                limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def get(self, key: str) -> Optional[str]:
        """Get value from Redis."""
        try:
            client = self._get_client()
            response = await client.post(
                f"{self.url}/get/{key}",
                headers=self.headers
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("result")

            logger.warning("redis_get_failed", status=response.status_code, key=key[:20])
            return None

        except Exception as e:
            logger.warning("redis_get_error", error=str(e), key=key[:20])
            return None

    async def mget(self, keys: list[str]) -> dict[str, Optional[str]]:
        """
        Get multiple values from Redis in a single request using pipeline.

        Args:
            keys: List of Redis keys to fetch

        Returns:
            Dict mapping keys to their values (None if key doesn't exist)
        """
        if not keys:
            return {}

        try:
            # Build pipeline commands for MGET
            commands = [["GET", key] for key in keys]

            client = self._get_client()
            response = await client.post(
                f"{self.url}/pipeline",
                headers=self.headers,
                json=commands
            )

            if response.status_code == 200:
                results = response.json()
                # Map keys to their results
                return {
                    key: results[i].get("result") if i < len(results) else None
                    for i, key in enumerate(keys)
                }

            logger.warning("redis_mget_failed", status=response.status_code, key_count=len(keys))
            return {key: None for key in keys}

        except Exception as e:
            logger.warning("redis_mget_error", error=str(e), key_count=len(keys))
            return {key: None for key in keys}

    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """Set value in Redis with optional expiry (seconds)."""
        try:
            # Build command
            if ex:
                command = ["SET", key, value, "EX", str(ex)]
            else:
                command = ["SET", key, value]

            client = self._get_client()
            response = await client.post(
                f"{self.url}/pipeline",
                headers=self.headers,
                json=[command]
            )

            if response.status_code == 200:
                return True

            logger.warning("redis_set_failed", status=response.status_code, key=key[:20])
            return False

        except Exception as e:
            logger.warning("redis_set_error", error=str(e), key=key[:20])
            return False

    async def setex(self, key: str, seconds: int, value: str) -> bool:
        """Set value in Redis with expiry (seconds). Alias for set with ex parameter."""
        return await self.set(key, value, ex=seconds)

    async def delete(self, key: str) -> bool:
        """Delete a key from Redis."""
        try:
            command = ["DEL", key]

            client = self._get_client()
            response = await client.post(
                f"{self.url}/pipeline",
                headers=self.headers,
                json=[command]
            )

            if response.status_code == 200:
                return True

            logger.warning("redis_delete_failed", status=response.status_code, key=key[:20])
            return False

        except Exception as e:
            logger.warning("redis_delete_error", error=str(e), key=key[:20])
            return False

    async def hset(self, key: str, mapping: dict) -> bool:
        """Set hash fields in Redis."""
        try:
            # Convert dict to list of field-value pairs
            fields = []
            for k, v in mapping.items():
                fields.extend([k, str(v)])

            command = ["HSET", key] + fields

            client = self._get_client()
            response = await client.post(
                f"{self.url}/pipeline",
                headers=self.headers,
                json=[command]
            )

            if response.status_code == 200:
                return True

            logger.warning("redis_hset_failed", status=response.status_code, key=key[:20])
            return False

        except Exception as e:
            logger.warning("redis_hset_error", error=str(e), key=key[:20])
            return False

    async def hgetall(self, key: str) -> Optional[dict]:
        """Get all hash fields from Redis."""
        try:
            client = self._get_client()
            response = await client.post(
                f"{self.url}/pipeline",
                headers=self.headers,
                json=[["HGETALL", key]]
            )

            if response.status_code == 200:
                result = response.json()
                if result and isinstance(result, list) and len(result) > 0:
                    data = result[0].get("result", [])
                    # Convert list to dict [k1, v1, k2, v2] -> {k1: v1, k2: v2}
                    return {data[i]: data[i+1] for i in range(0, len(data), 2)} if data else {}

            return None

        except Exception as e:
            logger.warning("redis_hgetall_error", error=str(e), key=key[:20])
            return None

    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiry on a key."""
        try:
            client = self._get_client()
            response = await client.post(
                f"{self.url}/pipeline",
                headers=self.headers,
                json=[["EXPIRE", key, str(seconds)]]
            )

            return response.status_code == 200

        except Exception as e:
            logger.warning("redis_expire_error", error=str(e), key=key[:20])
            return False

    async def sadd(self, key: str, *members: str) -> bool:
        """Add members to a set."""
        try:
            command = ["SADD", key] + list(members)

            client = self._get_client()
            response = await client.post(
                f"{self.url}/pipeline",
                headers=self.headers,
                json=[command]
            )

            return response.status_code == 200

        except Exception as e:
            logger.warning("redis_sadd_error", error=str(e), key=key[:20])
            return False

    async def scard(self, key: str) -> int:
        """Get count of set members."""
        try:
            client = self._get_client()
            response = await client.post(
                f"{self.url}/pipeline",
                headers=self.headers,
                json=[["SCARD", key]]
            )

            if response.status_code == 200:
                result = response.json()
                if result and isinstance(result, list):
                    return result[0].get("result", 0)

            return 0

        except Exception as e:
            logger.warning("redis_scard_error", error=str(e), key=key[:20])
            return 0

    async def lpush(self, key: str, *values: str) -> bool:
        """Push values to start of list."""
        try:
            command = ["LPUSH", key] + list(values)

            client = self._get_client()
            response = await client.post(
                f"{self.url}/pipeline",
                headers=self.headers,
                json=[command]
            )

            return response.status_code == 200

        except Exception as e:
            logger.warning("redis_lpush_error", error=str(e), key=key[:20])
            return False

    async def ltrim(self, key: str, start: int, stop: int) -> bool:
        """Trim list to specified range."""
        try:
            client = self._get_client()
            response = await client.post(
                f"{self.url}/pipeline",
                headers=self.headers,
                json=[["LTRIM", key, str(start), str(stop)]]
            )

            return response.status_code == 200

        except Exception as e:
            logger.warning("redis_ltrim_error", error=str(e), key=key[:20])
            return False

    async def lrange(self, key: str, start: int, stop: int) -> list:
        """Get range of list elements."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    f"{self.url}/pipeline",
                    headers=self.headers,
                    json=[["LRANGE", key, str(start), str(stop)]]
                )

                if response.status_code == 200:
                    result = response.json()
                    if result and isinstance(result, list):
                        return result[0].get("result", [])

                return []

        except Exception as e:
            logger.warning("redis_lrange_error", error=str(e), key=key[:20])
            return []

    async def llen(self, key: str) -> int:
        """Get length of list."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    f"{self.url}/pipeline",
                    headers=self.headers,
                    json=[["LLEN", key]]
                )

                if response.status_code == 200:
                    result = response.json()
                    if result and isinstance(result, list):
                        return result[0].get("result", 0)

                return 0

        except Exception as e:
            logger.warning("redis_llen_error", error=str(e), key=key[:20])
            return 0

    async def publish(self, channel: str, message: str) -> bool:
        """Publish message to Redis pub/sub channel."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    f"{self.url}/pipeline",
                    headers=self.headers,
                    json=[["PUBLISH", channel, message]]
                )

                if response.status_code == 200:
                    return True

                logger.warning("redis_publish_failed", status=response.status_code, channel=channel[:20])
                return False

        except Exception as e:
            logger.warning("redis_publish_error", error=str(e), channel=channel[:20])
            return False

    async def ttl(self, key: str) -> int:
        """Get TTL of a key in seconds."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    f"{self.url}/pipeline",
                    headers=self.headers,
                    json=[["TTL", key]]
                )

                if response.status_code == 200:
                    result = response.json()
                    if result and isinstance(result, list):
                        return result[0].get("result", -2)

                return -2

        except Exception as e:
            logger.warning("redis_ttl_error", error=str(e), key=key[:20])
            return -2

    async def ping(self) -> bool:
        """Ping Redis to check connection."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    f"{self.url}/pipeline",
                    headers=self.headers,
                    json=[["PING"]]
                )

                if response.status_code == 200:
                    result = response.json()
                    if result and isinstance(result, list):
                        return result[0].get("result") == "PONG"

                return False

        except Exception as e:
            logger.warning("redis_ping_error", error=str(e))
            return False


class StandardRedisClient:
    """Standard Redis client using redis-py with async support.

    This client provides the same interface as UpstashRedisClient but uses
    standard Redis protocol (TCP connection) instead of REST API.
    """

    def __init__(self, url: str):
        """Initialize standard Redis client.

        Args:
            url: Redis URL (e.g., redis://localhost:6379, redis://:password@host:port/db)
        """
        try:
            import redis.asyncio as aioredis
        except ImportError:
            raise ImportError(
                "redis package is required for standard Redis connections. "
                "Install it with: pip install redis"
            )

        self.url = url
        self._redis = aioredis.from_url(
            url,
            encoding="utf-8",
            decode_responses=True,
            socket_timeout=5.0,
            socket_connect_timeout=5.0,
        )

    async def get(self, key: str) -> Optional[str]:
        """Get value from Redis."""
        try:
            return await self._redis.get(key)
        except Exception as e:
            logger.warning("redis_get_error", error=str(e), key=key[:20])
            return None

    async def mget(self, keys: list[str]) -> dict[str, Optional[str]]:
        """Get multiple values from Redis."""
        if not keys:
            return {}

        try:
            values = await self._redis.mget(keys)
            return {key: value for key, value in zip(keys, values)}
        except Exception as e:
            logger.warning("redis_mget_error", error=str(e), key_count=len(keys))
            return {key: None for key in keys}

    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """Set value in Redis with optional expiry (seconds)."""
        try:
            result = await self._redis.set(key, value, ex=ex)
            return bool(result)
        except Exception as e:
            logger.warning("redis_set_error", error=str(e), key=key[:20])
            return False

    async def setex(self, key: str, seconds: int, value: str) -> bool:
        """Set value in Redis with expiry (seconds)."""
        return await self.set(key, value, ex=seconds)

    async def delete(self, key: str) -> bool:
        """Delete a key from Redis."""
        try:
            result = await self._redis.delete(key)
            return result > 0
        except Exception as e:
            logger.warning("redis_delete_error", error=str(e), key=key[:20])
            return False

    async def hset(self, key: str, mapping: dict) -> bool:
        """Set hash fields in Redis."""
        try:
            await self._redis.hset(key, mapping=mapping)
            return True
        except Exception as e:
            logger.warning("redis_hset_error", error=str(e), key=key[:20])
            return False

    async def hgetall(self, key: str) -> Optional[dict]:
        """Get all hash fields from Redis."""
        try:
            result = await self._redis.hgetall(key)
            return result if result else {}
        except Exception as e:
            logger.warning("redis_hgetall_error", error=str(e), key=key[:20])
            return None

    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiry on a key."""
        try:
            return await self._redis.expire(key, seconds)
        except Exception as e:
            logger.warning("redis_expire_error", error=str(e), key=key[:20])
            return False

    async def sadd(self, key: str, *members: str) -> bool:
        """Add members to a set."""
        try:
            await self._redis.sadd(key, *members)
            return True
        except Exception as e:
            logger.warning("redis_sadd_error", error=str(e), key=key[:20])
            return False

    async def scard(self, key: str) -> int:
        """Get count of set members."""
        try:
            return await self._redis.scard(key) or 0
        except Exception as e:
            logger.warning("redis_scard_error", error=str(e), key=key[:20])
            return 0

    async def lpush(self, key: str, *values: str) -> bool:
        """Push values to start of list."""
        try:
            await self._redis.lpush(key, *values)
            return True
        except Exception as e:
            logger.warning("redis_lpush_error", error=str(e), key=key[:20])
            return False

    async def ltrim(self, key: str, start: int, stop: int) -> bool:
        """Trim list to specified range."""
        try:
            await self._redis.ltrim(key, start, stop)
            return True
        except Exception as e:
            logger.warning("redis_ltrim_error", error=str(e), key=key[:20])
            return False

    async def lrange(self, key: str, start: int, stop: int) -> list:
        """Get range of list elements."""
        try:
            return await self._redis.lrange(key, start, stop) or []
        except Exception as e:
            logger.warning("redis_lrange_error", error=str(e), key=key[:20])
            return []

    async def llen(self, key: str) -> int:
        """Get length of list."""
        try:
            return await self._redis.llen(key) or 0
        except Exception as e:
            logger.warning("redis_llen_error", error=str(e), key=key[:20])
            return 0

    async def publish(self, channel: str, message: str) -> bool:
        """Publish message to Redis pub/sub channel."""
        try:
            await self._redis.publish(channel, message)
            return True
        except Exception as e:
            logger.warning("redis_publish_error", error=str(e), channel=channel[:20])
            return False

    async def ttl(self, key: str) -> int:
        """Get TTL of a key in seconds."""
        try:
            return await self._redis.ttl(key)
        except Exception as e:
            logger.warning("redis_ttl_error", error=str(e), key=key[:20])
            return -2

    async def ping(self) -> bool:
        """Ping Redis to check connection."""
        try:
            return await self._redis.ping()
        except Exception as e:
            logger.warning("redis_ping_error", error=str(e))
            return False


# Type alias for either Redis client
RedisClient = UpstashRedisClient | StandardRedisClient


def _normalize_redis_url(url: str) -> str:
    """
    Normalize a Redis URL to include the redis:// scheme if missing.

    Handles various URL formats:
    - redis://host:port -> redis://host:port (no change)
    - rediss://host:port -> rediss://host:port (no change)
    - host:port -> redis://host:port (add scheme)
    - host:port/db -> redis://host:port/db (add scheme)
    - :password@host:port -> redis://:password@host:port (add scheme)

    Args:
        url: Redis URL, possibly without scheme

    Returns:
        Normalized Redis URL with scheme
    """
    if not url:
        return url

    url = url.strip()

    # Already has scheme
    if url.startswith(("redis://", "rediss://")):
        return url

    # Check if URL looks like a Redis connection string (has host:port pattern)
    # Patterns: "host:port", "host:port/db", ":password@host:port"
    if ":" in url:
        # Default to redis:// scheme (non-TLS)
        # If the URL has a password marker at the start, add scheme correctly
        if url.startswith(":"):
            # Format: :password@host:port
            return f"redis://{url}"
        else:
            # Format: host:port or host:port/db
            return f"redis://{url}"

    return url


def get_redis_client() -> Optional[RedisClient]:
    """
    Get or create Redis client.

    Supports two modes (checked in order):
    1. Standard Redis URL (REDIS_URL) - e.g., redis://localhost:6379
    2. Upstash REST API (KV_REST_API_URL + KV_REST_API_TOKEN)

    Returns:
        Redis client instance or None if not configured
    """
    global _redis_client, _redis_client_type

    # Return cached client if available
    if _redis_client is not None:
        return _redis_client

    # Priority 1: Check for standard Redis URL
    redis_url = os.getenv("REDIS_URL")

    # Normalize URL format (add redis:// scheme if missing)
    if redis_url:
        original_url = redis_url
        redis_url = _normalize_redis_url(redis_url)
        if redis_url != original_url:
            logger.info(
                "redis_url_normalized",
                original=original_url[:30] + "..." if len(original_url) > 30 else original_url,
                normalized=redis_url[:30] + "..." if len(redis_url) > 30 else redis_url,
            )

    if redis_url and redis_url.startswith(("redis://", "rediss://")):
        try:
            _redis_client = StandardRedisClient(url=redis_url)
            _redis_client_type = "standard"
            # Mask password in log
            log_url = redis_url
            if "@" in redis_url:
                # redis://:password@host:port -> redis://***@host:port
                parts = redis_url.split("@")
                log_url = parts[0].rsplit(":", 1)[0] + ":***@" + parts[1]
            logger.info("redis_client_created", type="standard", url=log_url[:50])
            return _redis_client
        except ImportError as e:
            logger.warning(
                "redis_standard_client_unavailable",
                error=str(e),
                message="Falling back to Upstash REST API if configured"
            )
        except Exception as e:
            logger.error("redis_standard_client_init_failed", error=str(e))

    # Priority 2: Check for Upstash REST API
    upstash_url = (
        os.getenv("KV_REST_API_URL") or
        os.getenv("UPSTASH_REDIS_REST_URL") or
        os.getenv("UPSTASH_REDIS_URL")
    )

    upstash_token = (
        os.getenv("KV_REST_API_TOKEN") or
        os.getenv("UPSTASH_REDIS_REST_TOKEN") or
        os.getenv("UPSTASH_REDIS_TOKEN")
    )

    if upstash_url and upstash_token:
        try:
            _redis_client = UpstashRedisClient(url=upstash_url, token=upstash_token)
            _redis_client_type = "upstash"
            logger.info("redis_client_created", type="upstash", url=upstash_url[:30] + "...")
            return _redis_client
        except Exception as e:
            logger.error("redis_upstash_client_init_failed", error=str(e))
            return None

    # No Redis configured
    logger.warning(
        "redis_not_configured",
        message="No Redis configuration found, caching disabled",
        checked_vars=["REDIS_URL", "KV_REST_API_URL", "KV_REST_API_TOKEN", "UPSTASH_*"]
    )
    return None


# Worker-specific caching functions

async def cache_worker_heartbeat(
    worker_id: str,
    queue_id: str,
    organization_id: str,
    status: str,
    last_heartbeat: str,
    tasks_processed: int,
    system_info: Optional[dict] = None,
    ttl: int = 60
) -> bool:
    """
    Cache worker heartbeat data in Redis.

    Args:
        worker_id: Worker UUID
        queue_id: Queue UUID
        organization_id: Organization ID
        status: Worker status
        last_heartbeat: ISO timestamp
        tasks_processed: Task count
        system_info: Optional system metrics
        ttl: Cache TTL in seconds

    Returns:
        True if cached successfully
    """
    client = get_redis_client()
    if not client:
        return False

    try:
        data = {
            "worker_id": worker_id,
            "queue_id": queue_id,
            "organization_id": organization_id,
            "status": status,
            "last_heartbeat": last_heartbeat,
            "tasks_processed": tasks_processed,
        }

        if system_info:
            data["system_info"] = json.dumps(system_info)

        # Cache worker status
        await client.hset(f"worker:{worker_id}:status", data)
        await client.expire(f"worker:{worker_id}:status", ttl)

        # Add to queue workers set
        await client.sadd(f"queue:{queue_id}:workers", worker_id)
        await client.expire(f"queue:{queue_id}:workers", ttl)

        logger.debug("worker_heartbeat_cached", worker_id=worker_id[:8])
        return True

    except Exception as e:
        logger.error("cache_worker_heartbeat_failed", error=str(e), worker_id=worker_id[:8])
        return False


async def cache_worker_logs(worker_id: str, logs: list, ttl: int = 300) -> bool:
    """Cache worker logs in Redis."""
    client = get_redis_client()
    if not client or not logs:
        return False

    try:
        # Add logs to list
        await client.lpush(f"worker:{worker_id}:logs", *logs)
        # Keep only last 100 logs
        await client.ltrim(f"worker:{worker_id}:logs", 0, 99)
        # Set expiry
        await client.expire(f"worker:{worker_id}:logs", ttl)

        logger.debug("worker_logs_cached", worker_id=worker_id[:8], count=len(logs))
        return True

    except Exception as e:
        logger.error("cache_worker_logs_failed", error=str(e), worker_id=worker_id[:8])
        return False


async def get_queue_worker_count_cached(queue_id: str) -> Optional[int]:
    """Get active worker count for queue from cache."""
    client = get_redis_client()
    if not client:
        return None

    try:
        count = await client.scard(f"queue:{queue_id}:workers")
        return count
    except Exception as e:
        logger.error("get_queue_worker_count_failed", error=str(e), queue_id=queue_id[:8])
        return None
