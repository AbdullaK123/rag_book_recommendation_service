from typing import List, Optional
from sqlmodel import Field, SQLModel, Relationship
from models.base import TimestampMixin
from models.preference import UserPreference
from models.interaction import UserBookInteraction

class User(SQLModel, TimestampMixin, table=True):
    """User model representing a user of the application."""
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str
    full_name: Optional[str] = None
    bio: Optional[str] = None
    is_active: bool = Field(default=True)
    is_admin: bool = Field(default=False)
    
    # Relationships
    preferences: "UserPreference" = Relationship(back_populates="user")
    interactions: List["UserBookInteraction"] = Relationship(back_populates="user")