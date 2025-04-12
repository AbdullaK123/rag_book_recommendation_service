from utils.exceptions.base import BaseServiceException

class DatabaseException(BaseServiceException):
    """Base exception for all database errors"""
    def __init__(self, message, **kwargs):
        kwargs.setdefault('error_code', 'DB_ERROR')
        super().__init__(message, **kwargs)

class ConnectionException(DatabaseException):
    """Exception raised for database connection issues"""
    def __init__(self, message="Database connection failed", **kwargs):
        kwargs.setdefault('error_code', 'DB_CONNECTION_ERROR')
        kwargs.setdefault('suggestion', 'Check database credentials and network connectivity')
        super().__init__(message, **kwargs)

class QueryException(DatabaseException):
    """Exception raised for SQL or query execution errors"""
    def __init__(self, message, query=None, params=None, **kwargs):
        kwargs.setdefault('error_code', 'DB_QUERY_ERROR')
        details = kwargs.get('details', {})
        if query:
            details['query'] = query
        if params:
            details['params'] = params
        kwargs['details'] = details
        super().__init__(message, **kwargs)

class IntegrityException(DatabaseException):
    """Exception raised for data integrity violations"""
    def __init__(self, message, **kwargs):
        kwargs.setdefault('error_code', 'DB_INTEGRITY_ERROR')
        kwargs.setdefault('suggestion', 'Check for duplicate keys or constraint violations')
        super().__init__(message, **kwargs)

class TransactionException(DatabaseException):
    """Exception raised for transaction-related errors"""
    def __init__(self, message, **kwargs):
        kwargs.setdefault('error_code', 'DB_TRANSACTION_ERROR')
        super().__init__(message, **kwargs)