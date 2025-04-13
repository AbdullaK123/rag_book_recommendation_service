from typing import List, Optional, Dict, Any
import json
from sqlmodel import Field, SQLModel, Relationship, JSON
from models.base import TimestampMixin
from models.user import User


class UserPreference(SQLModel, TimestampMixin, table=True):
    """Model to store user preferences for recommendations."""
    __tablename__ = "user_preferences"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True, unique=True)
    
    # Category preferences (serialized dict with category_id -> weight)
    category_preferences: Optional[str] = None
    
    # Reading preferences
    preferred_language: Optional[str] = None
    min_page_count: Optional[int] = None
    max_page_count: Optional[int] = None
    min_publication_year: Optional[int] = None
    max_publication_year: Optional[int] = None
    min_rating: Optional[float] = None
    
    # Custom preferences stored as JSON
    custom_preferences: Dict[str, Any] = Field(default={}, sa_column=JSON)
    
    # Relationship
    user: "User" = Relationship(back_populates="preferences")
    
    def get_category_preferences(self) -> Dict[int, float]:
        """Deserialize category preferences from string to dict."""
        if not self.category_preferences:
            return {}
        return json.loads(self.category_preferences)
    
    def set_category_preferences(self, preferences: Dict[int, float]) -> None:
        """Serialize category preferences from dict to string."""
        self.category_preferences = json.dumps(preferences)