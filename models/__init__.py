from models.base import TimestampMixin
from models.user import User
from models.book import Book
from models.category import Category, BookCategoryLink
from models.interaction import UserBookInteraction, InteractionType
from models.preference import UserPreference
from models.recommendation import BookRecommendation

# Export all models for easy imports
__all__ = [
    "TimestampMixin",
    "User",
    "Book",
    "Category",
    "BookCategoryLink",
    "UserBookInteraction",
    "InteractionType",
    "UserPreference",
    "BookRecommendation",
]