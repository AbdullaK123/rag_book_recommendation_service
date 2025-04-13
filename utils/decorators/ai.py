import functools
import logging
import traceback
from typing import Callable, Optional, Dict, Any, Type, Union
from fastapi import Request
from fastapi.responses import JSONResponse
from utils.exceptions.processing import (
    ProcessingException,
    RAGException,
    ContentGenerationException,
    RecommendationException
)
from utils.exceptions.service import (
    ExternalServiceException,
    LLMServiceException,
    WebSearchException
)

# Setup logger
logger = logging.getLogger(__name__)

def ai_exception_handler(
    func: Optional[Callable] = None,
    include_traceback: bool = False,
    default_status_code: int = 500,
    custom_handlers: Dict[Type[Exception], Callable[[Exception, Request], JSONResponse]] = None
):
    """
    Decorator to handle AI and RAG-related exceptions in functions and API endpoints.
    
    This decorator catches AI-processing related exceptions and converts them
    to appropriate response formats based on the context.
    
    Args:
        func: The function to decorate
        include_traceback: Whether to include traceback in the response (dev environments only)
        default_status_code: Default HTTP status code for unhandled exceptions
        custom_handlers: Optional dictionary mapping exception types to custom handler functions
    
    Returns:
        Decorated function that catches and handles AI/RAG exceptions
    
    Example:
        @app.get("/recommendations/{user_id}")
        @ai_exception_handler
        async def get_recommendations(user_id: int):
            # AI/RAG operations here
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
            except ProcessingException as exc:
                log_ai_exception(exc, request)
                return create_ai_exception_response(exc, include_traceback)
            except LLMServiceException as exc:
                log_ai_exception(exc, request)
                return create_ai_exception_response(exc, include_traceback)
            except WebSearchException as exc:
                log_ai_exception(exc, request)
                return create_ai_exception_response(exc, include_traceback)
            except Exception as exc:
                # Check if we have a custom handler for this exception type
                for exc_type, handler in custom_handlers.items():
                    if isinstance(exc, exc_type):
                        return handler(exc, request)
                
                # If no custom handler, wrap in ProcessingException
                wrapped_exc = ProcessingException(
                    message=f"AI processing error: {str(exc)}",
                    original_exception=exc
                )
                log_ai_exception(wrapped_exc, request)
                return create_ai_exception_response(wrapped_exc, include_traceback)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Extract request if present in args or kwargs
            request = next((arg for arg in args if isinstance(arg, Request)), 
                         kwargs.get('request'))
            
            try:
                return func(*args, **kwargs)
            except ProcessingException as exc:
                log_ai_exception(exc, request)
                return create_ai_exception_response(exc, include_traceback)
            except LLMServiceException as exc:
                log_ai_exception(exc, request)
                return create_ai_exception_response(exc, include_traceback)
            except WebSearchException as exc:
                log_ai_exception(exc, request)
                return create_ai_exception_response(exc, include_traceback)
            except Exception as exc:
                # Check if we have a custom handler for this exception type
                for exc_type, handler in custom_handlers.items():
                    if isinstance(exc, exc_type):
                        return handler(exc, request)
                
                # If no custom handler, wrap in ProcessingException
                wrapped_exc = ProcessingException(
                    message=f"AI processing error: {str(exc)}",
                    original_exception=exc
                )
                log_ai_exception(wrapped_exc, request)
                return create_ai_exception_response(wrapped_exc, include_traceback)
        
        # Determine if the function is async or sync
        if callable(getattr(func, "__await__", None)):
            return async_wrapper
        return sync_wrapper
    
    # This allows the decorator to be used with or without arguments
    if func is not None:
        return decorator(func)
    return decorator


def log_ai_exception(exc: Union[ProcessingException, ExternalServiceException], request: Optional[Request] = None) -> None:
    """Log AI exception with appropriate context"""
    request_info = {}
    if request:
        request_info = {
            "method": request.method,
            "url": str(request.url),
            "client": request.client.host if request.client else "unknown",
            "path_params": dict(request.path_params) if hasattr(request, 'path_params') else {},
            "query_params": dict(request.query_params) if hasattr(request, 'query_params') else {}
        }
    
    error_data = exc.to_dict()
    error_data["request"] = request_info
    
    # Add RAG-specific details if available
    if isinstance(exc, RAGException) and hasattr(exc, 'stage'):
        error_data['rag_stage'] = exc.stage
    
    # Add content generation details if available
    if isinstance(exc, ContentGenerationException) and hasattr(exc, 'content_type'):
        error_data['content_type'] = exc.content_type
    
    # Add LLM service details if available
    if isinstance(exc, LLMServiceException) and hasattr(exc, 'model'):
        error_data['llm_model'] = exc.model
    
    # Add recommendation details if available
    if isinstance(exc, RecommendationException) and hasattr(exc, 'user_id'):
        error_data['recommendation_user_id'] = exc.user_id
    
    # Determine log level based on severity
    log_level = logging.ERROR
    if isinstance(exc, (RAGException, LLMServiceException)) and exc.http_status_code and exc.http_status_code < 500:
        log_level = logging.WARNING
    
    logger.log(log_level, f"AI Exception: {exc.__class__.__name__}", 
               extra={"ai_error_data": error_data})


def create_ai_exception_response(
    exc: Union[ProcessingException, ExternalServiceException], 
    include_traceback: bool = False
) -> Union[JSONResponse, Dict[str, Any]]:
    """
    Create a standardized response from an AI exception.
    
    Args:
        exc: The exception that was raised
        include_traceback: Whether to include traceback in the response
        
    Returns:
        JSONResponse if in an API context, Dict if in a LangChain/RAG context
    """
    status_code = getattr(exc, 'http_status_code', 500)
    
    # Determine if we're in an API context based on status_code type
    is_api_context = isinstance(status_code, int)
    
    response_data = {
        "error": exc.__class__.__name__,
        "error_code": exc.error_code or "AI_PROCESSING_ERROR",
        "message": exc.message
    }
    
    if hasattr(exc, 'details') and exc.details:
        response_data["details"] = exc.details
    
    if hasattr(exc, 'suggestion') and exc.suggestion:
        response_data["suggestion"] = exc.suggestion
        
    # Add more specific fields based on exception type
    if isinstance(exc, RAGException) and hasattr(exc, 'stage'):
        response_data["stage"] = exc.stage
        
    if isinstance(exc, ContentGenerationException) and hasattr(exc, 'content_type'):
        response_data["content_type"] = exc.content_type
        
    if isinstance(exc, LLMServiceException) and hasattr(exc, 'model'):
        response_data["model"] = exc.model
    
    if include_traceback and exc.original_exception:
        response_data["traceback"] = traceback.format_exc()
    
    # Return appropriate response type
    if is_api_context:
        return JSONResponse(
            status_code=status_code,
            content=response_data
        )
    else:
        # For non-API contexts (e.g., LangChain callbacks)
        response_data["status_code"] = status_code
        return {"error": response_data}


# Custom handler for OpenAI errors (can be expanded with providers)
def openai_error_handler(exc: Exception, request: Request) -> JSONResponse:
    """Custom handler for OpenAI-specific errors"""
    # Check for different OpenAI error types
    error_type = type(exc).__name__
    
    if "RateLimitError" in error_type:
        # Handle rate limiting
        wrapped_exc = LLMServiceException(
            message="OpenAI rate limit exceeded, please try again later",
            error_code="OPENAI_RATE_LIMIT",
            http_status_code=429,
            suggestion="Try again later or reduce the frequency of requests",
            original_exception=exc
        )
    elif "InvalidRequestError" in error_type:
        # Handle invalid requests
        wrapped_exc = LLMServiceException(
            message=f"Invalid request to OpenAI API: {str(exc)}",
            error_code="OPENAI_INVALID_REQUEST",
            http_status_code=400,
            original_exception=exc
        )
    elif "AuthenticationError" in error_type:
        # Handle authentication issues
        wrapped_exc = LLMServiceException(
            message="OpenAI API authentication failed",
            error_code="OPENAI_AUTH_ERROR",
            http_status_code=401,
            suggestion="Check your API key configuration",
            original_exception=exc
        )
    else:
        # Generic OpenAI error
        wrapped_exc = LLMServiceException(
            message=f"OpenAI API error: {str(exc)}",
            error_code="OPENAI_API_ERROR",
            original_exception=exc
        )
    
    log_ai_exception(wrapped_exc, request)
    return create_ai_exception_response(wrapped_exc)


# Initialize logging
def init_ai_logging():
    """Initialize the AI exception logger"""
    from utils.logging.ai import setup_ai_logging
    return setup_ai_logging()