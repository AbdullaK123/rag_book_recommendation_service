from datetime import datetime
from enum import Enum
from typing import List, Optional
import json
from sqlmodel import Field, Relationship, SQLModel
import uuid

def generate_uuid():
    return str(uuid.uuid4())


# ========== Base Models ==========

class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps to models."""
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: Optional[datetime] = Field(default=None, sa_column_kwargs={"onupdate": datetime.utcnow})


# ========== Link Tables ==========

class BookCategoryLink(SQLModel, table=True):
    """Link table for many-to-many relationship between books and categories."""
    __tablename__ = "book_category_links"

    book_id: str = Field(foreign_key="books.id", primary_key=True)
    category_id: str = Field(foreign_key="categories.id", primary_key=True)


# ========== Enums ==========

class InteractionType(str, Enum):
    """Enum for types of interactions a user can have with a book."""
    VIEW = "view"  # User viewed book details
    LIKE = "like"  # User liked the book
    DISLIKE = "dislike"  # User disliked the book
    BOOKMARK = "bookmark"  # User bookmarked the book for later
    RATE = "rate"  # User rated the book
    REVIEW = "review"  # User reviewed the book
    RECOMMEND = "recommend"  # Book was recommended to user


# ========== Main Models ==========

class User(SQLModel, TimestampMixin, table=True):
    """User model representing a user of the application."""
    __tablename__ = "users"

    id: Optional[str] = Field(default_factory=generate_uuid, primary_key=True)
    username: str = Field(index=True, unique=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str
    full_name: Optional[str] = None
    bio: Optional[str] = None
    is_active: bool = Field(default=True)
    is_admin: bool = Field(default=False)
    
    # Relationships
    preferences: Optional["UserPreference"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"uselist": False}
    )
    interactions: List["UserBookInteraction"] = Relationship(back_populates="user")


class Book(SQLModel, TimestampMixin, table=True):
    """Book model representing a book in the system."""
    __tablename__ = "books"

    id: Optional[str] = Field(default_factory=generate_uuid, primary_key=True)
    title: str = Field(index=True)
    author: str = Field(index=True)
    isbn: Optional[str] = Field(default=None, unique=True, index=True)
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
    categories: List["Category"] = Relationship(
        back_populates="books", 
        link_model=BookCategoryLink
    )
    interactions: List["UserBookInteraction"] = Relationship(back_populates="book")
    recommendations: List["BookRecommendation"] = Relationship(back_populates="book")


class Category(SQLModel, TimestampMixin, table=True):
    """Category model representing book genres and categories."""
    __tablename__ = "categories"

    id: Optional[str] = Field(default_factory=generate_uuid, primary_key=True)
    name: str = Field(index=True, unique=True)
    description: Optional[str] = None
    
    # Relationships
    books: List[Book] = Relationship(
        back_populates="categories", 
        link_model=BookCategoryLink
    )


class UserPreference(SQLModel, TimestampMixin, table=True):
    """Model to store user preferences for recommendations."""
    __tablename__ = "user_preferences"

    id: Optional[str] = Field(default_factory=generate_uuid, primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True, unique=True)
    
    # Category preferences (serialized dict with category_id -> weight)
    category_preferences: Optional[str] = None
    
    # Reading preferences
    preferred_language: Optional[str] = None
    min_page_count: Optional[int] = None
    max_page_count: Optional[int] = None
    min_publication_year: Optional[int] = None
    max_publication_year: Optional[int] = None
    min_rating: Optional[float] = None
    
    # Custom preferences stored as serialized JSON string
    custom_preferences: Optional[str] = Field(default="{}")
    
    # Relationship
    user: User = Relationship(back_populates="preferences")
    
    def get_category_preferences(self):
        """Deserialize category preferences from string to dict."""
        if not self.category_preferences:
            return {}
        return json.loads(self.category_preferences)
    
    def set_category_preferences(self, preferences):
        """Serialize category preferences from dict to string."""
        self.category_preferences = json.dumps(preferences)
        
    def get_custom_preferences(self):
        """Deserialize custom preferences from string to dict."""
        if not self.custom_preferences:
            return {}
        return json.loads(self.custom_preferences)
    
    def set_custom_preferences(self, preferences):
        """Serialize custom preferences from dict to string."""
        self.custom_preferences = json.dumps(preferences)


class UserBookInteraction(SQLModel, TimestampMixin, table=True):
    """Model to track user interactions with books."""
    __tablename__ = "user_book_interactions"

    id: Optional[str] = Field(default_factory=generate_uuid, primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    book_id: str = Field(foreign_key="books.id", index=True)
    interaction_type: InteractionType
    rating: Optional[float] = None  # 1-5 star rating
    review_text: Optional[str] = None
    
    # Relationships
    user: User = Relationship(back_populates="interactions")
    book: Book = Relationship(back_populates="interactions")


class BookRecommendation(SQLModel, TimestampMixin, table=True):
    """Model to store book recommendations for users."""
    __tablename__ = "book_recommendations"

    id: Optional[str] = Field(default_factory=generate_uuid, primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    book_id: str = Field(foreign_key="books.id", index=True)
    
    # Recommendation metadata
    score: float  # Recommendation confidence score (0-1)
    reason: Optional[str] = None  # Human-readable explanation for recommendation
    is_viewed: bool = Field(default=False)  # Whether user has seen this recommendation
    is_dismissed: bool = Field(default=False)  # Whether user has dismissed this recommendation
    
    # Method used to generate this recommendation
    recommendation_source: str = Field(index=True)  # e.g., "collaborative", "content-based", "rag", "hybrid"
    
    # Metadata about the recommendation process (stored as serialized JSON)
    recommendation_metadata: Optional[str] = Field(default="{}")
    
    # When the recommendation was viewed by the user
    viewed_at: Optional[datetime] = None
    
    # Relationships
    user: User = Relationship()
    book: Book = Relationship(back_populates="recommendations")
    
    def get_metadata(self):
        """Deserialize metadata from string to dict."""
        if not self.metadata:
            return {}
        return json.loads(self.metadata)
    
    def set_metadata(self, metadata):
        """Serialize metadata from dict to string."""
        self.metadata = json.dumps(metadata)