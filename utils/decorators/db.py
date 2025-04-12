import functools
import logging
import traceback
from typing import Callable, Optional, Dict, Any, Type, Union
from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError, NoResultFound
from utils.exceptions.db import (
    DatabaseException,
    ConnectionException,
    QueryException,
    IntegrityException,
    TransactionException
)

# Setup logger
logger = logging.getLogger(__name__)

def db_exception_handler(
    func: Optional[Callable] = None,
    include_traceback: bool = False
):
    """
    Decorator to handle database exceptions in FastAPI, LangChain, and LangGraph components.
    
    This decorator catches SQLAlchemy and custom database exceptions and converts them
    to appropriate response formats based on the context.
    
    Args:
        func: The function to decorate
        include_traceback: Whether to include traceback in the response (dev environments only)
    
    Returns:
        Decorated function that catches and handles database exceptions
    
    Example:
        @app.get("/users/{user_id}")
        @db_exception_handler
        async def get_user(user_id: int):
            # Database operations here
            
        @db_exception_handler(include_traceback=True)  # For development environment
        def fetch_books():
            # Database operations here
    """
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Extract request if present in args or kwargs
            request = next((arg for arg in args if isinstance(arg, Request)), 
                         kwargs.get('request'))
            
            try:
                return await func(*args, **kwargs)
            except DatabaseException as exc:
                # Our custom database exceptions already have proper context
                log_db_exception(exc, request)
                return handle_db_exception(exc, request, include_traceback)
            except NoResultFound as exc:
                # Handle SQLAlchemy NoResultFound exception
                custom_exc = QueryException(
                    message="Resource not found in database",
                    original_exception=exc
                )
                log_db_exception(custom_exc, request)
                return handle_db_exception(custom_exc, request, include_traceback)
            except IntegrityError as exc:
                # Handle SQLAlchemy IntegrityError
                custom_exc = IntegrityException(
                    message="Database integrity error: possible duplicate or constraint violation",
                    original_exception=exc
                )
                log_db_exception(custom_exc, request)
                return handle_db_exception(custom_exc, request, include_traceback)
            except OperationalError as exc:
                # Handle SQLAlchemy OperationalError (connection issues)
                custom_exc = ConnectionException(
                    message="Database connection error",
                    original_exception=exc
                )
                log_db_exception(custom_exc, request)
                return handle_db_exception(custom_exc, request, include_traceback)
            except SQLAlchemyError as exc:
                # Handle any other SQLAlchemy errors
                custom_exc = QueryException(
                    message=f"Database error: {str(exc)}",
                    original_exception=exc
                )
                log_db_exception(custom_exc, request)
                return handle_db_exception(custom_exc, request, include_traceback)
            except Exception as exc:
                # For any other exception, check if it's db-related by name
                if any(term in str(exc.__class__.__name__).lower() 
                       for term in ['db', 'sql', 'database', 'query']):
                    custom_exc = DatabaseException(
                        message=f"Database error: {str(exc)}",
                        original_exception=exc
                    )
                    log_db_exception(custom_exc, request)
                    return handle_db_exception(custom_exc, request, include_traceback)
                # Re-raise non-database exceptions for other handlers
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Extract request if present in args or kwargs
            request = next((arg for arg in args if isinstance(arg, Request)), 
                         kwargs.get('request'))
            
            try:
                return func(*args, **kwargs)
            except DatabaseException as exc:
                # Our custom database exceptions already have proper context
                log_db_exception(exc, request)
                return handle_db_exception(exc, request, include_traceback)
            except NoResultFound as exc:
                # Handle SQLAlchemy NoResultFound exception
                custom_exc = QueryException(
                    message="Resource not found in database",
                    original_exception=exc
                )
                log_db_exception(custom_exc, request)
                return handle_db_exception(custom_exc, request, include_traceback)
            except IntegrityError as exc:
                # Handle SQLAlchemy IntegrityError
                custom_exc = IntegrityException(
                    message="Database integrity error: possible duplicate or constraint violation",
                    original_exception=exc
                )
                log_db_exception(custom_exc, request)
                return handle_db_exception(custom_exc, request, include_traceback)
            except OperationalError as exc:
                # Handle SQLAlchemy OperationalError (connection issues)
                custom_exc = ConnectionException(
                    message="Database connection error",
                    original_exception=exc
                )
                log_db_exception(custom_exc, request)
                return handle_db_exception(custom_exc, request, include_traceback)
            except SQLAlchemyError as exc:
                # Handle any other SQLAlchemy errors
                custom_exc = QueryException(
                    message=f"Database error: {str(exc)}",
                    original_exception=exc
                )
                log_db_exception(custom_exc, request)
                return handle_db_exception(custom_exc, request, include_traceback)
            except Exception as exc:
                # For any other exception, check if it's db-related by name
                if any(term in str(exc.__class__.__name__).lower() 
                       for term in ['db', 'sql', 'database', 'query']):
                    custom_exc = DatabaseException(
                        message=f"Database error: {str(exc)}",
                        original_exception=exc
                    )
                    log_db_exception(custom_exc, request)
                    return handle_db_exception(custom_exc, request, include_traceback)
                # Re-raise non-database exceptions for other handlers
                raise
        
        # Determine if the function is async or sync
        if callable(getattr(func, "__await__", None)):
            return async_wrapper
        return sync_wrapper
    
    # This allows the decorator to be used with or without arguments
    if func is not None:
        return decorator(func)
    return decorator


def log_db_exception(exc: DatabaseException, request: Optional[Request] = None) -> None:
    """Log database exception with appropriate context"""
    request_info = {}
    if request:
        request_info = {
            "method": request.method,
            "url": str(request.url),
            "client": request.client.host if request.client else "unknown",
        }
    
    error_data = exc.to_dict()
    error_data["request"] = request_info
    
    # Add SQLAlchemy specific details if available
    if exc.original_exception and isinstance(exc.original_exception, SQLAlchemyError):
        original = exc.original_exception
        if hasattr(original, 'statement'):
            error_data['sql_statement'] = str(original.statement)
        if hasattr(original, 'params'):
            error_data['sql_params'] = str(original.params)
    
    logger.error(f"Database Exception: {exc.__class__.__name__}", 
                 extra={"db_error_data": error_data})


def handle_db_exception(
    exc: DatabaseException, 
    request: Optional[Request] = None,
    include_traceback: bool = False
) -> Union[JSONResponse, Dict[str, Any]]:
    """
    Handle database exception based on context
    
    Returns:
        - JSONResponse if request is provided (FastAPI context)
        - Dict with error info if no request (LangChain/LangGraph context)
    """
    # Determine status code based on exception type
    status_code = 500
    if isinstance(exc, ConnectionException):
        status_code = 503  # Service Unavailable
    elif isinstance(exc, IntegrityException):
        status_code = 409  # Conflict
    elif isinstance(exc, QueryException) and "not found" in exc.message.lower():
        status_code = 404  # Not Found
    
    # Create response data
    response_data = {
        "error": exc.__class__.__name__,
        "error_code": exc.error_code or "DB_ERROR",
        "message": exc.message,
    }
    
    if exc.details:
        response_data["details"] = exc.details
    
    if exc.suggestion:
        response_data["suggestion"] = exc.suggestion
    
    if include_traceback and exc.original_exception:
        response_data["traceback"] = traceback.format_exc()
    
    # Return appropriate response based on context
    if request and isinstance(request, Request):
        # We're in a FastAPI context
        return JSONResponse(
            status_code=status_code,
            content=response_data
        )
    else:
        # We're in a LangChain/LangGraph context
        response_data["status_code"] = status_code
        return {"error": response_data}