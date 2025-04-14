import functools
import json
import logging
import time
import inspect
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union, cast
import hashlib
from redis.asyncio import Redis as AsyncRedis
from redis import Redis

from utils.exceptions.caching import CacheException, CacheSerializationException

logger = logging.getLogger(__name__)


def generate_cache_key(
    prefix: str,
    func_name: str,
    args: Tuple,
    kwargs: Dict[str, Any]
) -> str:
    """
    Generate a consistent cache key based on function name and arguments.
    
    Args:
        prefix: Prefix for the cache key (usually service name)
        func_name: Name of the function being cached
        args: Positional arguments to the function
        kwargs: Keyword arguments to the function
        
    Returns:
        A string cache key
    """
    # Convert args to a list of strings
    args_str = [str(arg) for arg in args]
    
    # Convert kwargs to a sorted list of key-value pairs
    kwargs_str = [f"{k}:{v}" for k, v in sorted(kwargs.items())]
    
    # Combine all components
    key_components = [prefix, func_name] + args_str + kwargs_str
    
    # Join with colons and create hash for potentially large keys
    key_base = ":".join(key_components)
    
    # Use hash for potentially large keys
    if len(key_base) > 200:
        hash_obj = hashlib.md5(key_base.encode())
        return f"{prefix}:{func_name}:hash:{hash_obj.hexdigest()}"
    
    return key_base


def serialize_cache_data(data: Any) -> str:
    """
    Serialize data for caching.
    
    Args:
        data: The data to serialize
        
    Returns:
        JSON string representation of the data
        
    Raises:
        CacheSerializationException: If serialization fails
    """
    try:
        return json.dumps(data)
    except (TypeError, ValueError, OverflowError) as e:
        raise CacheSerializationException(
            message=f"Failed to serialize data for cache: {str(e)}",
            operation="serialize",
            original_exception=e
        )


def deserialize_cache_data(data_str: str) -> Any:
    """
    Deserialize data from cache.
    
    Args:
        data_str: The serialized data string
        
    Returns:
        Deserialized data
        
    Raises:
        CacheSerializationException: If deserialization fails
    """
    try:
        return json.loads(data_str)
    except (json.JSONDecodeError, TypeError) as e:
        raise CacheSerializationException(
            message=f"Failed to deserialize data from cache: {str(e)}",
            operation="deserialize",
            original_exception=e
        )


def cached(
    prefix: str,
    ttl: int = 300,  # Default TTL: 5 minutes
    key_builder: Optional[Callable] = None
):
    """
    Decorator for caching function results in Redis.
    
    Args:
        prefix: Prefix for the cache key
        ttl: Time to live in seconds
        key_builder: Optional custom function to generate cache keys
        
    Returns:
        Decorated function
    
    Example:
        @cached("user_service", ttl=3600)
        async def get_user(self, user_id: int) -> User:
            # Function implementation
    """
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(self, *args, **kwargs):
            # Skip caching if cache client is not available
            if not hasattr(self, "cache") or self.cache is None:
                return await func(self, *args, **kwargs)
                
            cache_client = self.cache
            if not isinstance(cache_client, (Redis, AsyncRedis)):
                return await func(self, *args, **kwargs)
            
            # Generate cache key
            if key_builder:
                cache_key = key_builder(self, *args, **kwargs)
            else:
                cache_key = generate_cache_key(prefix, func.__name__, args, kwargs)
            
            # Try to get from cache
            try:
                cached_data = await cache_client.get(cache_key)
                if cached_data:
                    logger.debug(f"Cache hit for key: {cache_key}")
                    return deserialize_cache_data(cached_data.decode())
                
                logger.debug(f"Cache miss for key: {cache_key}")
                # Execute function and cache result
                result = await func(self, *args, **kwargs)
                
                # Only cache non-None results
                if result is not None:
                    serialized_result = serialize_cache_data(result)
                    await cache_client.setex(cache_key, ttl, serialized_result)
                
                return result
            except CacheException:
                # Log and continue with function execution on cache error
                logger.warning(f"Cache error for key: {cache_key}, executing function directly")
                return await func(self, *args, **kwargs)
            except Exception as e:
                logger.error(f"Unexpected error in cached decorator: {str(e)}")
                return await func(self, *args, **kwargs)
        
        @functools.wraps(func)
        def sync_wrapper(self, *args, **kwargs):
            # Skip caching if cache client is not available
            if not hasattr(self, "cache") or self.cache is None:
                return func(self, *args, **kwargs)
                
            cache_client = self.cache
            if not isinstance(cache_client, Redis):
                return func(self, *args, **kwargs)
            
            # Generate cache key
            if key_builder:
                cache_key = key_builder(self, *args, **kwargs)
            else:
                cache_key = generate_cache_key(prefix, func.__name__, args, kwargs)
            
            # Try to get from cache
            try:
                cached_data = cache_client.get(cache_key)
                if cached_data:
                    logger.debug(f"Cache hit for key: {cache_key}")
                    return deserialize_cache_data(cached_data.decode())
                
                logger.debug(f"Cache miss for key: {cache_key}")
                # Execute function and cache result
                result = func(self, *args, **kwargs)
                
                # Only cache non-None results
                if result is not None:
                    serialized_result = serialize_cache_data(result)
                    cache_client.setex(cache_key, ttl, serialized_result)
                
                return result
            except CacheException:
                # Log and continue with function execution on cache error
                logger.warning(f"Cache error for key: {cache_key}, executing function directly")
                return func(self, *args, **kwargs)
            except Exception as e:
                logger.error(f"Unexpected error in cached decorator: {str(e)}")
                return func(self, *args, **kwargs)
        
        # Determine if the function is async or sync
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def invalidate_cache(
    prefix: str,
    key_pattern: Optional[str] = None,
    key_builder: Optional[Callable] = None
):
    """
    Decorator to invalidate cache entries after a function is executed.
    
    Args:
        prefix: Prefix for the cache key
        key_pattern: Optional pattern for cache keys to invalidate (can include *)
        key_builder: Optional custom function to generate the exact cache key or list of keys
        
    Returns:
        Decorated function
    
    Example:
        @invalidate_cache("user_service", "user:*")
        async def update_user(self, user_id: int, user_data: UserUpdate) -> User:
            # Function implementation
    """
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(self, *args, **kwargs):
            # Execute function first
            result = await func(self, *args, **kwargs)
            
            # Skip invalidation if cache client is not available
            if not hasattr(self, "cache") or self.cache is None:
                return result
                
            cache_client = self.cache
            if not isinstance(cache_client, (Redis, AsyncRedis)):
                return result
            
            try:
                # Determine keys to invalidate
                if key_builder:
                    # Custom key builder can return a single key or list of keys
                    keys_to_invalidate = key_builder(self, *args, **kwargs, result=result)
                    if isinstance(keys_to_invalidate, str):
                        keys_to_invalidate = [keys_to_invalidate]
                    
                    for key in keys_to_invalidate:
                        await cache_client.delete(key)
                        logger.debug(f"Invalidated cache key: {key}")
                
                elif key_pattern:
                    # If pattern includes wildcard, use scan and delete
                    if '*' in key_pattern:
                        pattern = f"{prefix}:{key_pattern}"
                        cursor = 0
                        while True:
                            cursor, keys = await cache_client.scan(cursor, match=pattern, count=100)
                            if keys:
                                for key in keys:
                                    await cache_client.delete(key)
                                    logger.debug(f"Invalidated cache key: {key.decode()}")
                            if cursor == 0:
                                break
                    else:
                        # If no wildcard, direct delete
                        full_key = f"{prefix}:{key_pattern}"
                        await cache_client.delete(full_key)
                        logger.debug(f"Invalidated cache key: {full_key}")
                else:
                    # Default: invalidate function-specific cache with same args
                    cache_key = generate_cache_key(prefix, func.__name__, args, kwargs)
                    await cache_client.delete(cache_key)
                    logger.debug(f"Invalidated cache key: {cache_key}")
            except Exception as e:
                logger.error(f"Error invalidating cache: {str(e)}")
            
            return result
        
        @functools.wraps(func)
        def sync_wrapper(self, *args, **kwargs):
            # Execute function first
            result = func(self, *args, **kwargs)
            
            # Skip invalidation if cache client is not available
            if not hasattr(self, "cache") or self.cache is None:
                return result
                
            cache_client = self.cache
            if not isinstance(cache_client, Redis):
                return result
            
            try:
                # Determine keys to invalidate
                if key_builder:
                    # Custom key builder can return a single key or list of keys
                    keys_to_invalidate = key_builder(self, *args, **kwargs, result=result)
                    if isinstance(keys_to_invalidate, str):
                        keys_to_invalidate = [keys_to_invalidate]
                    
                    for key in keys_to_invalidate:
                        cache_client.delete(key)
                        logger.debug(f"Invalidated cache key: {key}")
                
                elif key_pattern:
                    # If pattern includes wildcard, use scan and delete
                    if '*' in key_pattern:
                        pattern = f"{prefix}:{key_pattern}"
                        cursor = 0
                        while True:
                            cursor, keys = cache_client.scan(cursor, match=pattern, count=100)
                            if keys:
                                for key in keys:
                                    cache_client.delete(key)
                                    logger.debug(f"Invalidated cache key: {key.decode()}")
                            if cursor == 0:
                                break
                    else:
                        # If no wildcard, direct delete
                        full_key = f"{prefix}:{key_pattern}"
                        cache_client.delete(full_key)
                        logger.debug(f"Invalidated cache key: {full_key}")
                else:
                    # Default: invalidate function-specific cache with same args
                    cache_key = generate_cache_key(prefix, func.__name__, args, kwargs)
                    cache_client.delete(cache_key)
                    logger.debug(f"Invalidated cache key: {cache_key}")
            except Exception as e:
                logger.error(f"Error invalidating cache: {str(e)}")
            
            return result
        
        # Determine if the function is async or sync
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator