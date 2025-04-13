
from datetime import datetime
from typing import Optional, Dict, Any
from sqlmodel import Field, SQLModel, Relationship, JSON
from models.base import TimestampMixin


class BookRecommendation(SQLModel, TimestampMixin, table=True):
    """Model to store book recommendations for users."""
    __tablename__ = "book_recommendations"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    book_id: int = Field(foreign_key="books.id", index=True)
    
    # Recommendation metadata
    score: float  # Recommendation confidence score (0-1)
    reason: Optional[str] = None  # Human-readable explanation for recommendation
    is_viewed: bool = Field(default=False)  # Whether user has seen this recommendation
    is_dismissed: bool = Field(default=False)  # Whether user has dismissed this recommendation
    
    # Method used to generate this recommendation
    recommendation_source: str = Field(index=True)  # e.g., "collaborative", "content-based", "rag", "hybrid"
    
    # Metadata about the recommendation process
    metadata: Dict[str, Any] = Field(default={}, sa_column=JSON)
    
    # When the recommendation was viewed by the user
    viewed_at: Optional[datetime] = None