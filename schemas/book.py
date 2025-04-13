from typing import Optional, List, Set
from sqlmodel import SQLModel, Field


class CategoryBase(SQLModel):
    """Base schema for category data"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class CategoryCreate(CategoryBase):
    """Schema for creating a new category"""
    pass
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Science Fiction",
                "description": "Fiction dealing with imaginative content such as futuristic settings"
            }
        }


class CategoryUpdate(SQLModel):
    """Schema for updating a category"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None


class CategoryRead(CategoryBase):
    """Schema for category responses"""
    id: int


class BookBase(SQLModel):
    """Base schema for book data"""
    title: str = Field(..., min_length=1, max_length=200)
    author: str = Field(..., min_length=1, max_length=100)
    isbn: Optional[str] = Field(None, regex=r'^(\d{10}|\d{13})$')
    description: Optional[str] = None
    publication_year: Optional[int] = Field(None, ge=0, le=2100)
    publisher: Optional[str] = None
    language: Optional[str] = None
    page_count: Optional[int] = Field(None, gt=0)
    cover_image_url: Optional[str] = None


class BookCreate(BookBase):
    """Schema for creating a new book"""
    category_ids: List[int] = Field(default_factory=list)
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Dune",
                "author": "Frank Herbert",
                "isbn": "9780441172719",
                "description": "Set in the distant future amidst a feudal interstellar society",
                "publication_year": 1965,
                "publisher": "Chilton Books",
                "language": "English",
                "page_count": 412,
                "cover_image_url": "https://example.com/covers/dune.jpg",
                "category_ids": [1, 3]
            }
        }


class BookUpdate(SQLModel):
    """Schema for updating a book"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    author: Optional[str] = Field(None, min_length=1, max_length=100)
    isbn: Optional[str] = Field(None, regex=r'^(\d{10}|\d{13})$')
    description: Optional[str] = None
    publication_year: Optional[int] = Field(None, ge=0, le=2100)
    publisher: Optional[str] = None
    language: Optional[str] = None
    page_count: Optional[int] = Field(None, gt=0)
    cover_image_url: Optional[str] = None
    category_ids: Optional[List[int]] = None


class BookSearchParams(SQLModel):
    """Query parameters for searching books"""
    title: Optional[str] = None
    author: Optional[str] = None
    category_id: Optional[int] = None
    language: Optional[str] = None
    min_publication_year: Optional[int] = Field(None, ge=0, le=2100)
    max_publication_year: Optional[int] = Field(None, ge=0, le=2100)
    min_page_count: Optional[int] = Field(None, gt=0)
    max_page_count: Optional[int] = Field(None, gt=0)
    min_rating: Optional[float] = Field(None, ge=0, le=5)


class BookWithCategories(BookBase):
    """Schema for book responses with categories"""
    id: int
    average_rating: float = 0.0
    ratings_count: int = 0
    categories: List[CategoryRead] = Field(default_factory=list)


class BooksListResponse(SQLModel):
    """Schema for returning a list of books"""
    books: List[BookWithCategories]
    total: int