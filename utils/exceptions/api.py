from utils.exceptions.base import BaseServiceException

class APIException(BaseServiceException):
    """Base exception for API-related errors"""
    def __init__(self, message, **kwargs):
        kwargs.setdefault('error_code', 'API_ERROR')
        kwargs.setdefault('http_status_code', 500)
        super().__init__(message, **kwargs)

class ResourceNotFoundException(APIException):
    """Exception raised when a requested resource doesn't exist"""
    def __init__(self, resource_type, resource_id, **kwargs):
        message = f"{resource_type} with ID {resource_id} not found"
        kwargs.setdefault('error_code', 'RESOURCE_NOT_FOUND')
        kwargs.setdefault('http_status_code', 404)
        kwargs.setdefault('details', {'resource_type': resource_type, 'resource_id': resource_id})
        super().__init__(message, **kwargs)

class UnauthorizedException(APIException):
    """Exception raised when authentication is required but not provided"""
    def __init__(self, message="Authentication required", **kwargs):
        kwargs.setdefault('error_code', 'UNAUTHORIZED')
        kwargs.setdefault('http_status_code', 401)
        kwargs.setdefault('suggestion', 'Please provide valid authentication credentials')
        super().__init__(message, **kwargs)

class ForbiddenException(APIException):
    """Exception raised when authentication is valid but lacks permission"""
    def __init__(self, message="Insufficient permissions", **kwargs):
        kwargs.setdefault('error_code', 'FORBIDDEN')
        kwargs.setdefault('http_status_code', 403)
        kwargs.setdefault('suggestion', 'Contact administrator for required permissions')
        super().__init__(message, **kwargs)

class BadRequestException(APIException):
    """Exception raised for malformed requests"""
    def __init__(self, message, **kwargs):
        kwargs.setdefault('error_code', 'BAD_REQUEST')
        kwargs.setdefault('http_status_code', 400)
        super().__init__(message, **kwargs)

class RateLimitException(APIException):
    """Exception raised when API rate limits are exceeded"""
    def __init__(self, message="Rate limit exceeded", **kwargs):
        kwargs.setdefault('error_code', 'RATE_LIMIT_EXCEEDED')
        kwargs.setdefault('http_status_code', 429)
        kwargs.setdefault('suggestion', 'Please reduce request frequency or contact support to increase limits')
        super().__init__(message, **kwargs)