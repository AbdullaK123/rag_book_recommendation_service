import logging
from typing import Optional, Any, Dict, Union
import redis
from redis.asyncio import Redis as AsyncRedis
from redis.exceptions import RedisError
from utils.config import settings
from utils.exceptions.caching import RedisConnectionException

logger = logging.getLogger(__name__)


def create_redis_client(use_async: bool = False) -> Union[redis.Redis, AsyncRedis]:
    """
    Create and return a Redis client instance.
    
    Args:
        use_async: Whether to return an asyncio Redis client
    
    Returns:
        A Redis client instance
        
    Raises:
        RedisConnectionException: If Redis connection fails
    """
    try:
        connection_params = {
            "host": settings.redis.REDIS_HOST,
            "port": settings.redis.REDIS_PORT,
            "db": settings.redis.REDIS_DB,
            "password": settings.redis.REDIS_PASSWORD if settings.redis.REDIS_PASSWORD else None,
            "ssl": settings.redis.REDIS_USE_SSL,
            "decode_responses": False,  # We want bytes back for flexibility
            "socket_timeout": 5,  # 5 second timeout
            "socket_connect_timeout": 5,
            "retry_on_timeout": True
        }
        
        # Remove None values
        connection_params = {k: v for k, v in connection_params.items() if v is not None}
        
        if use_async:
            # Create asyncio Redis client
            client = AsyncRedis(**connection_params)
            logger.info("Async Redis client created")
        else:
            # Create synchronous Redis client
            client = redis.Redis(**connection_params)
            logger.info("Synchronous Redis client created")
        
        return client
    except RedisError as e:
        logger.error(f"Failed to create Redis client: {str(e)}")
        raise RedisConnectionException(
            message=f"Failed to connect to Redis: {str(e)}",
            original_exception=e
        )


class RedisClient:
    """Class for managing Redis connections and providing cache operations."""
    
    def __init__(self, use_async: bool = False):
        """Initialize Redis client."""
        self.client = None
        self.use_async = use_async
        self.initialize()
    
    def initialize(self) -> None:
        """Initialize Redis connection."""
        try:
            self.client = create_redis_client(self.use_async)
        except RedisConnectionException as e:
            logger.error(f"Redis initialization failed: {str(e)}")
            self.client = None
    
    def get_client(self) -> Optional[Union[redis.Redis, AsyncRedis]]:
        """Get the Redis client instance."""
        return self.client
    
    async def ping_async(self) -> bool:
        """Check if Redis connection is alive (async)."""
        if not self.client or not self.use_async:
            return False
        
        try:
            return await self.client.ping()
        except RedisError as e:
            logger.error(f"Redis ping failed: {str(e)}")
            return False
    
    def ping(self) -> bool:
        """Check if Redis connection is alive (sync)."""
        if not self.client or self.use_async:
            return False
        
        try:
            return self.client.ping()
        except RedisError as e:
            logger.error(f"Redis ping failed: {str(e)}")
            return False


# Global instances for convenience
sync_redis = RedisClient(use_async=False)
async_redis = RedisClient(use_async=True)


def get_redis_client(use_async: bool = False) -> Optional[Union[redis.Redis, AsyncRedis]]:
    """Get Redis client instance based on async preference."""
    if use_async:
        return async_redis.get_client()
    return sync_redis.get_client()