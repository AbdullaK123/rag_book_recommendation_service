from models.models import (
    TimestampMixin,
    User,
    Book,
    Category,
    BookCategoryLink,
    UserBookInteraction,
    InteractionType,
    UserPreference,
    BookRecommendation,
)

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