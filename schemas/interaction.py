from typing import Optional, Dict, List, Any
from enum import Enum
import json
from sqlmodel import SQLModel, Field
from pydantic import validator
from models.models import InteractionType  # Import enum from models
from schemas.book import BookWithCategories
from schemas.user import UserRead


class InteractionCreate(SQLModel):
    """Schema for creating a new user-book interaction"""
    book_id: int
    interaction_type: InteractionType
    rating: Optional[float] = Field(None, ge=1, le=5, description="Rating value (1-5)")
    review_text: Optional[str] = None
    
    @validator('rating')
    def rating_required_for_rate(cls, v, values):
        if values.get('interaction_type') == InteractionType.RATE and v is None:
            raise ValueError('Rating is required for RATE interaction type')
        return v
    
    @validator('review_text')
    def review_required_for_review(cls, v, values):
        if values.get('interaction_type') == InteractionType.REVIEW and not v:
            raise ValueError('Review text is required for REVIEW interaction type')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "book_id": 1,
                "interaction_type": "rate",
                "rating": 4.5,
                "review_text": "This book was excellent, I highly recommend it."
            }
        }


class InteractionUpdate(SQLModel):
    """Schema for updating a user-book interaction"""
    interaction_type: Optional[InteractionType] = None
    rating: Optional[float] = Field(None, ge=1, le=5)
    review_text: Optional[str] = None


class UserPreferenceBase(SQLModel):
    """Base schema for user preference data"""
    category_preferences: Optional[Dict[str, float]] = Field(
        None, 
        description="Category preferences as {category_id: weight} pairs"
    )
    preferred_language: Optional[str] = None
    min_page_count: Optional[int] = Field(None, gt=0)
    max_page_count: Optional[int] = None
    min_publication_year: Optional[int] = Field(None, ge=0, le=2100)
    max_publication_year: Optional[int] = None
    min_rating: Optional[float] = Field(None, ge=0, le=5)
    custom_preferences: Optional[Dict[str, Any]] = None


class UserPreferenceCreate(UserPreferenceBase):
    """Schema for creating user preferences"""
    class Config:
        json_schema_extra = {
            "example": {
                "category_preferences": {"1": 0.8, "3": 0.6, "5": 0.3},
                "preferred_language": "English",
                "min_page_count": 200,
                "max_page_count": 500,
                "min_publication_year": 2000,
                "max_publication_year": 2023,
                "min_rating": 3.5,
                "custom_preferences": {"themes": ["dystopian", "space"], "avoid_authors": ["Author X"]}
            }
        }


class UserPreferenceUpdate(UserPreferenceBase):
    """Schema for updating user preferences"""
    pass


class UserPreferenceRead(UserPreferenceBase):
    """Schema for user preference responses"""
    id: int
    user_id: int


class InteractionRead(SQLModel):
    """Schema for interaction responses"""
    id: int
    user_id: int
    book_id: int
    interaction_type: InteractionType
    rating: Optional[float] = None
    review_text: Optional[str] = None


class InteractionWithBook(InteractionRead):
    """Schema for interaction responses with embedded book data"""
    book: BookWithCategories


class InteractionWithUser(InteractionRead):
    """Schema for interaction responses with embedded user data"""
    user: UserRead


class InteractionListResponse(SQLModel):
    """Schema for returning a list of interactions"""
    interactions: List[InteractionRead]
    total: int