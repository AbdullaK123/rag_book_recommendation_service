from typing import List, Optional
from sqlmodel import Field, SQLModel, Relationship
from models.base import TimestampMixin
from models.book import Book


class Category(SQLModel, TimestampMixin, table=True):
    """Category model representing book genres and categories."""
    __tablename__ = "categories"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    description: Optional[str] = None
    
    # Relationships
    books: List["Book"] = Relationship(back_populates="categories", link_model="BookCategoryLink")


class BookCategoryLink(SQLModel, table=True):
    """Link table for many-to-many relationship between books and categories."""
    __tablename__ = "book_category_links"

    book_id: Optional[int] = Field(
        default=None, foreign_key="books.id", primary_key=True
    )
    category_id: Optional[int] = Field(
        default=None, foreign_key="categories.id", primary_key=True
    )