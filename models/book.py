
from typing import List, Optional
from sqlmodel import Field, SQLModel, Relationship
from models.base import TimestampMixin
from models.category import BookCategoryLink, Category
from models.interaction import UserBookInteraction


class Book(SQLModel, TimestampMixin, table=True):
    """Book model representing a book in the system."""
    __tablename__ = "books"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    author: str = Field(index=True)
    isbn: Optional[str] = Field(unique=True, index=True)
    description: Optional[str] = None
    publication_year: Optional[int] = None
    publisher: Optional[str] = None
    language: Optional[str] = None
    page_count: Optional[int] = None
    average_rating: Optional[float] = Field(default=0.0)
    ratings_count: int = Field(default=0)
    cover_image_url: Optional[str] = None
    
    # Vector embedding for similarity search
    embedding: Optional[str] = None  # Will store serialized embedding vector
    
    # Relationships
    categories: List["Category"] = Relationship(back_populates="books", link_model=BookCategoryLink)
    interactions: List["UserBookInteraction"] = Relationship(back_populates="book")