from utils.exceptions.base import BaseServiceException


class CacheException(BaseServiceException):
    """Base exception for caching issues"""
    def __init__(self, message, cache_key=None, **kwargs):
        details = kwargs.get('details', {})
        if cache_key:
            details['cache_key'] = cache_key
        kwargs['details'] = details
        kwargs.setdefault('error_code', 'CACHE_ERROR')
        super().__init__(message, **kwargs)

class RedisConnectionException(CacheException):
    """Exception raised for Redis connection failures"""
    def __init__(self, message="Redis connection failed", **kwargs):
        kwargs.setdefault('error_code', 'REDIS_CONNECTION_ERROR')
        kwargs.setdefault('suggestion', 'Check Redis connection settings and availability')
        super().__init__(message, **kwargs)

class CacheSerializationException(CacheException):
    """Exception raised for serialization/deserialization errors"""
    def __init__(self, message, operation=None, **kwargs):
        details = kwargs.get('details', {})
        if operation:
            details['operation'] = operation  # 'serialize' or 'deserialize'
        kwargs['details'] = details
        kwargs.setdefault('error_code', 'CACHE_SERIALIZATION_ERROR')
        super().__init__(message, **kwargs)