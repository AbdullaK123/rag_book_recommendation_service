import functools
import logging
import traceback
from typing import Callable, Optional, Dict, Any, Type, Union
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from utils.exceptions.api import (
    APIException, 
    ResourceNotFoundException,
    UnauthorizedException,
    ForbiddenException,
    BadRequestException,
    RateLimitException
)

# Setup logger
logger = logging.getLogger(__name__)

def api_exception_handler(
    func: Optional[Callable] = None,
    include_traceback: bool = False,
    default_status_code: int = 500,
    custom_handlers: Dict[Type[Exception], Callable[[Exception, Request], JSONResponse]] = None
):
    """
    Decorator to handle API exceptions in FastAPI endpoints.
    
    This decorator catches API-related exceptions and converts them
    to appropriate HTTP response formats.
    
    Args:
        func: The function to decorate
        include_traceback: Whether to include traceback in the response (dev environments only)
        default_status_code: Default HTTP status code for unhandled exceptions
        custom_handlers: Optional dictionary mapping exception types to custom handler functions
    
    Returns:
        Decorated function that catches and handles API exceptions
    
    Example:
        @app.get("/users/{user_id}")
        @api_exception_handler
        async def get_user(user_id: int):
            # API operations here
    """
    custom_handlers = custom_handlers or {}
    
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Extract request if present in args or kwargs
            request = next((arg for arg in args if isinstance(arg, Request)), 
                         kwargs.get('request'))
            
            try:
                return await func(*args, **kwargs)
            except APIException as exc:
                # Our custom API exceptions
                log_api_exception(exc, request)
                return create_api_exception_response(exc, include_traceback)
            except HTTPException as exc:
                # FastAPI's HTTPException
                custom_exc = convert_http_exception(exc)
                log_api_exception(custom_exc, request)
                return create_api_exception_response(custom_exc, include_traceback)
            except RequestValidationError as exc:
                # FastAPI's RequestValidationError
                for exc_type, handler in custom_handlers.items():
                    if isinstance(exc, exc_type):
                        return handler(exc, request)
                # Default validation error handling
                custom_exc = BadRequestException(
                    message="Validation error in request data",
                    details={"errors": _format_validation_errors(exc.errors())}
                )
                log_api_exception(custom_exc, request)
                return create_api_exception_response(custom_exc, include_traceback)
            except ValidationError as exc:
                # Pydantic's ValidationError
                custom_exc = BadRequestException(
                    message="Validation error in request data",
                    details={"errors": _format_validation_errors(exc.errors())}
                )
                log_api_exception(custom_exc, request)
                return create_api_exception_response(custom_exc, include_traceback)
            except Exception as exc:
                # Check if we have a custom handler for this exception type
                for exc_type, handler in custom_handlers.items():
                    if isinstance(exc, exc_type):
                        return handler(exc, request)
                
                # For any other exception, we re-raise to let other handlers catch it
                # This allows chaining multiple exception handlers (e.g., DB then API)
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Extract request if present in args or kwargs
            request = next((arg for arg in args if isinstance(arg, Request)), 
                         kwargs.get('request'))
            
            try:
                return func(*args, **kwargs)
            except APIException as exc:
                # Our custom API exceptions
                log_api_exception(exc, request)
                return create_api_exception_response(exc, include_traceback)
            except HTTPException as exc:
                # FastAPI's HTTPException
                custom_exc = convert_http_exception(exc)
                log_api_exception(custom_exc, request)
                return create_api_exception_response(custom_exc, include_traceback)
            except RequestValidationError as exc:
                # FastAPI's RequestValidationError
                for exc_type, handler in custom_handlers.items():
                    if isinstance(exc, exc_type):
                        return handler(exc, request)
                # Default validation error handling
                custom_exc = BadRequestException(
                    message="Validation error in request data",
                    details={"errors": _format_validation_errors(exc.errors())}
                )
                log_api_exception(custom_exc, request)
                return create_api_exception_response(custom_exc, include_traceback)
            except ValidationError as exc:
                # Pydantic's ValidationError
                custom_exc = BadRequestException(
                    message="Validation error in request data",
                    details={"errors": _format_validation_errors(exc.errors())}
                )
                log_api_exception(custom_exc, request)
                return create_api_exception_response(custom_exc, include_traceback)
            except Exception as exc:
                # Check if we have a custom handler for this exception type
                for exc_type, handler in custom_handlers.items():
                    if isinstance(exc, exc_type):
                        return handler(exc, request)
                
                # For any other exception, we re-raise to let other handlers catch it
                # This allows chaining multiple exception handlers (e.g., DB then API)
                raise
        
        # Determine if the function is async or sync
        if callable(getattr(func, "__await__", None)):
            return async_wrapper
        return sync_wrapper
    
    # This allows the decorator to be used with or without arguments
    if func is not None:
        return decorator(func)
    return decorator


def log_api_exception(exc: APIException, request: Optional[Request] = None) -> None:
    """Log API exception with appropriate context"""
    request_info = {}
    if request:
        request_info = {
            "method": request.method,
            "url": str(request.url),
            "client": request.client.host if request.client else "unknown",
            "headers": {k: v for k, v in request.headers.items() if k.lower() not in ('authorization', 'cookie')},
            "path_params": dict(request.path_params) if hasattr(request, 'path_params') else {},
            "query_params": dict(request.query_params) if hasattr(request, 'query_params') else {}
        }
    
    error_data = exc.to_dict()
    error_data["request"] = request_info
    
    # Determine log level based on status code
    log_level = logging.ERROR
    if exc.http_status_code and 400 <= exc.http_status_code < 500:
        # 4xx errors are warnings, not critical errors
        log_level = logging.WARNING
        
    logger.log(log_level, f"API Exception: {exc.__class__.__name__}", 
              extra={"api_error_data": error_data})


def create_api_exception_response(
    exc: APIException, 
    include_traceback: bool = False
) -> JSONResponse:
    """Create a standardized JSONResponse from an API exception"""
    status_code = exc.http_status_code or 500
    
    response_data = {
        "error": exc.__class__.__name__,
        "error_code": exc.error_code,
        "message": exc.message,
    }
    
    if exc.details:
        response_data["details"] = exc.details
    
    if exc.suggestion:
        response_data["suggestion"] = exc.suggestion
    
    if include_traceback and exc.original_exception:
        response_data["traceback"] = traceback.format_exc()
    
    return JSONResponse(
        status_code=status_code,
        content=response_data
    )


def convert_http_exception(exc: HTTPException) -> APIException:
    """Convert FastAPI's HTTPException to our custom APIException"""
    status_code = exc.status_code
    
    # Map status code to appropriate exception type
    if status_code == status.HTTP_404_NOT_FOUND:
        return ResourceNotFoundException(
            resource_type="Resource",
            resource_id="unknown",
            message=exc.detail,
            original_exception=exc
        )
    elif status_code == status.HTTP_401_UNAUTHORIZED:
        return UnauthorizedException(
            message=exc.detail,
            original_exception=exc
        )
    elif status_code == status.HTTP_403_FORBIDDEN:
        return ForbiddenException(
            message=exc.detail,
            original_exception=exc
        )
    elif status_code == status.HTTP_429_TOO_MANY_REQUESTS:
        return RateLimitException(
            message=exc.detail,
            original_exception=exc
        )
    elif 400 <= status_code < 500:
        return BadRequestException(
            message=exc.detail,
            http_status_code=status_code,
            original_exception=exc
        )
    else:
        return APIException(
            message=exc.detail,
            http_status_code=status_code,
            original_exception=exc
        )


def _format_validation_errors(errors: list) -> list:
    """Format validation errors into a more readable structure"""
    formatted_errors = []
    for error in errors:
        formatted_error = {
            "loc": " -> ".join(str(loc) for loc in error["loc"]),
            "msg": error["msg"],
            "type": error["type"]
        }
        formatted_errors.append(formatted_error)
    return formatted_errors


# Custom handler for Pydantic validation errors
def validation_error_handler(exc: Union[ValidationError, RequestValidationError], request: Request) -> JSONResponse:
    """Custom handler for Pydantic and FastAPI validation errors"""
    errors = getattr(exc, "errors", lambda: [])
    if callable(errors):
        error_list = errors()
    else:
        error_list = errors
        
    formatted_errors = _format_validation_errors(error_list)
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "VALIDATION_ERROR",
            "error_code": "VALIDATION_ERROR",
            "message": "The request data failed validation",
            "details": {
                "validation_errors": formatted_errors
            },
            "suggestion": "Please check the request data and ensure it meets the required format"
        }
    )