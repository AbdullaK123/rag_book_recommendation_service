from enum import Enum
from typing import Optional
from sqlmodel import Field, SQLModel, Relationship
from models.base import TimestampMixin
from models.user import User
from models.book import Book


class InteractionType(str, Enum):
    """Enum for types of interactions a user can have with a book."""
    VIEW = "view"  # User viewed book details
    LIKE = "like"  # User liked the book
    DISLIKE = "dislike"  # User disliked the book
    BOOKMARK = "bookmark"  # User bookmarked the book for later
    RATE = "rate"  # User rated the book
    REVIEW = "review"  # User reviewed the book
    RECOMMEND = "recommend"  # Book was recommended to user


class UserBookInteraction(SQLModel, TimestampMixin, table=True):
    """Model to track user interactions with books."""
    __tablename__ = "user_book_interactions"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    book_id: int = Field(foreign_key="books.id", index=True)
    interaction_type: InteractionType
    rating: Optional[float] = None  # 1-5 star rating
    review_text: Optional[str] = None
    
    # Relationships
    user: "User" = Relationship(back_populates="interactions")
    book: "Book" = Relationship(back_populates="interactions")