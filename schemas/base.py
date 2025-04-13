from datetime import datetime
from typing import Optional, Any, Dict, List, Generic, TypeVar
from sqlmodel import SQLModel, Field

# Define type variables for generic schemas
T = TypeVar('T')


class ResponseSchema(SQLModel, Generic[T]):
    """Standard response wrapper for single items"""
    success: bool = True
    message: Optional[str] = None
    data: Optional[T] = None
    error: Optional[str] = None


class PaginatedResponseSchema(SQLModel, Generic[T]):
    """Standard response wrapper for paginated results"""
    success: bool = True
    message: Optional[str] = None
    data: Optional[List[T]] = None
    error: Optional[str] = None
    
    # Pagination metadata
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool


class ErrorSchema(SQLModel):
    """Standard error response"""
    success: bool = False
    error: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    suggestion: Optional[str] = None


class PaginationParams(SQLModel):
    """Query parameters for pagination"""
    page: int = Field(1, gt=0, description="Page number (1-indexed)")
    page_size: int = Field(10, gt=0, le=100, description="Number of items per page")
    sort_by: Optional[str] = None
    sort_order: Optional[str] = Field(None, pattern="^(asc|desc)$")