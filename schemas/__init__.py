from schemas.base import (
    ResponseSchema,
    PaginatedResponseSchema,
    ErrorSchema,
    PaginationParams
)

from schemas.user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserPasswordUpdate,
    UserRead,
    UsersListResponse
)

from schemas.book import (
    CategoryBase,
    CategoryCreate,
    CategoryUpdate,
    CategoryRead,
    BookBase,
    BookCreate,
    BookUpdate,
    BookSearchParams,
    BookWithCategories,
    BooksListResponse
)

from schemas.interaction import (
    InteractionCreate,
    InteractionUpdate,
    UserPreferenceBase,
    UserPreferenceCreate,
    UserPreferenceUpdate,
    UserPreferenceRead,
    InteractionRead,
    InteractionWithBook,
    InteractionWithUser,
    InteractionListResponse
)

from schemas.recommendation import (
    RecommendationSource,
    RecommendationCreate,
    RecommendationUpdate,
    RecommendationRead,
    RecommendationWithBook,
    RecommendationListResponse,
    RecommendationBatchRequest,
    RecommendationFeedbackRequest
)

from schemas.auth import (
    LoginRequest,
    LoginResponse,
    SessionData,
    LogoutRequest,
    PasswordResetRequest,
    PasswordResetConfirm
)

# For convenient imports
__all__ = [
    # Base schemas
    "ResponseSchema", "PaginatedResponseSchema",
    "ErrorSchema", "PaginationParams",
    
    # User schemas
    "UserBase", "UserCreate", "UserUpdate", "UserPasswordUpdate",
    "UserRead", "UsersListResponse",
    
    # Book and Category schemas
    "CategoryBase", "CategoryCreate", "CategoryUpdate", "CategoryRead",
    "BookBase", "BookCreate", "BookUpdate", "BookSearchParams",
    "BookWithCategories", "BooksListResponse",
    
    # Interaction and Preference schemas
    "InteractionCreate", "InteractionUpdate",
    "UserPreferenceBase", "UserPreferenceCreate", "UserPreferenceUpdate",
    "UserPreferenceRead", "InteractionRead",
    "InteractionWithBook", "InteractionWithUser",
    "InteractionListResponse",
    
    # Recommendation schemas
    "RecommendationSource", "RecommendationCreate", "RecommendationUpdate",
    "RecommendationRead", "RecommendationWithBook",
    "RecommendationListResponse", "RecommendationBatchRequest",
    "RecommendationFeedbackRequest",
    
    # Auth schemas
    "LoginRequest", "LoginResponse", "SessionData", "LogoutRequest",
    "PasswordResetRequest", "PasswordResetConfirm"
]