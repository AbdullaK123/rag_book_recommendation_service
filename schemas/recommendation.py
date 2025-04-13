from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum
from sqlmodel import SQLModel, Field
from pydantic import validator
from schemas.book import BookWithCategories


class RecommendationSource(str, Enum):
    """Enum for recommendation source types"""
    COLLABORATIVE = "collaborative"
    CONTENT_BASED = "content_based"
    RAG = "rag"  # Retrieval-Augmented Generation
    HYBRID = "hybrid"
    POPULAR = "popular"  # Popular among all users
    SIMILAR = "similar"  # Similar to previously read books
    PERSONALIZED = "personalized"  # Based on user preferences


class RecommendationCreate(SQLModel):
    """Schema for creating a new recommendation"""
    user_id: int
    book_id: int
    score: float = Field(..., ge=0, le=1, description="Recommendation confidence score (0-1)")
    reason: Optional[str] = None
    recommendation_source: RecommendationSource
    recommendation_metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 1,
                "book_id": 5,
                "score": 0.87,
                "reason": "Based on your interest in science fiction and previous ratings",
                "recommendation_source": "hybrid",
                "recommendation_metadata": {
                    "similarity_score": 0.78,
                    "collaborative_score": 0.92,
                    "matching_categories": [1, 3]
                }
            }
        }


class RecommendationUpdate(SQLModel):
    """Schema for updating a recommendation"""
    score: Optional[float] = Field(None, ge=0, le=1)
    reason: Optional[str] = None
    is_viewed: Optional[bool] = None
    is_dismissed: Optional[bool] = None
    recommendation_source: Optional[RecommendationSource] = None
    recommendation_metadata: Optional[Dict[str, Any]] = None


class RecommendationRead(SQLModel):
    """Schema for recommendation responses"""
    id: int
    user_id: int
    book_id: int
    score: float
    reason: Optional[str] = None
    is_viewed: bool
    is_dismissed: bool
    recommendation_source: str
    recommendation_metadata: Optional[Dict[str, Any]] = None
    viewed_at: Optional[datetime] = None


class RecommendationWithBook(RecommendationRead):
    """Schema for recommendation responses with embedded book data"""
    book: BookWithCategories


class RecommendationListResponse(SQLModel):
    """Schema for returning a list of recommendations"""
    recommendations: List[RecommendationWithBook]
    total: int


class RecommendationBatchRequest(SQLModel):
    """Schema for requesting a batch of new recommendations"""
    count: int = Field(5, ge=1, le=20, description="Number of recommendations to generate")
    include_viewed: bool = False
    include_dismissed: bool = False
    category_filters: Optional[List[int]] = None
    min_score: Optional[float] = Field(None, ge=0, le=1)
    source_filters: Optional[List[RecommendationSource]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "count": 5,
                "include_viewed": False,
                "include_dismissed": False,
                "category_filters": [1, 3],
                "min_score": 0.7,
                "source_filters": ["rag", "hybrid"]
            }
        }


class RecommendationFeedbackRequest(SQLModel):
    """Schema for providing feedback on a recommendation"""
    is_helpful: bool
    feedback_text: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "is_helpful": True,
                "feedback_text": "This was a great recommendation, thank you!"
            }
        }