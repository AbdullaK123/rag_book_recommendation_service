from sqlmodel import Session, select
from typing import List, Optional, Dict, Any
from datetime import datetime
from models.models import UserBookInteraction, InteractionType, Book, User
from schemas.interaction import InteractionCreate, InteractionUpdate
from utils.decorators.db import db_exception_handler
from utils.decorators.cache import cached, invalidate_cache
from services.base import BaseService
from utils.exceptions.base import ValidationException


class InteractionService(BaseService[UserBookInteraction]):
    def __init__(self):
        super().__init__(UserBookInteraction)
        self.cache_prefix = "interaction_service"
    
    @db_exception_handler
    @cached(prefix="interaction_service", ttl=300)
    async def get_user_interactions(self, db: Session, user_id: str, limit: int = 50) -> List[UserBookInteraction]:
        """Get interactions for a specific user"""
        interactions = db.exec(
            select(UserBookInteraction)
            .where(UserBookInteraction.user_id == user_id)
            .order_by(UserBookInteraction.created_at.desc())
            .limit(limit)
        ).all()
        
        # Load related books
        for interaction in interactions:
            interaction.book = db.exec(
                select(Book).where(Book.id == interaction.book_id)
            ).first()
            
        return interactions
    
    @db_exception_handler
    @cached(prefix="interaction_service", ttl=300)
    async def get_book_interactions(self, db: Session, book_id: str, limit: int = 50) -> List[UserBookInteraction]:
        """Get interactions for a specific book"""
        interactions = db.exec(
            select(UserBookInteraction)
            .where(UserBookInteraction.book_id == book_id)
            .order_by(UserBookInteraction.created_at.desc())
            .limit(limit)
        ).all()
        
        # Load related users
        for interaction in interactions:
            interaction.user = db.exec(
                select(User).where(User.id == interaction.user_id)
            ).first()
            
        return interactions
    
    @db_exception_handler
    @cached(prefix="interaction_service", ttl=300)
    async def get_user_book_interaction(
        self, 
        db: Session, 
        user_id: str, 
        book_id: str, 
        interaction_type: Optional[InteractionType] = None
    ) -> Optional[UserBookInteraction]:
        """Get a specific interaction between a user and a book"""
        query = (
            select(UserBookInteraction)
            .where(
                UserBookInteraction.user_id == user_id,
                UserBookInteraction.book_id == book_id
            )
        )
        
        if interaction_type:
            query = query.where(UserBookInteraction.interaction_type == interaction_type)
            
        return db.exec(query.order_by(UserBookInteraction.created_at.desc())).first()
    
    @db_exception_handler
    @invalidate_cache(prefix="interaction_service")
    async def create_interaction(
        self, 
        db: Session, 
        user_id: str, 
        interaction_in: InteractionCreate
    ) -> UserBookInteraction:
        """Create a new interaction between a user and a book"""
        # Validate rating if interaction type is RATE
        if interaction_in.interaction_type == InteractionType.RATE and interaction_in.rating is None:
            raise ValidationException(
                message="Rating is required for RATE interaction type",
                details={"field": "rating"}
            )
            
        # Validate review text if interaction type is REVIEW
        if interaction_in.interaction_type == InteractionType.REVIEW and not interaction_in.review_text:
            raise ValidationException(
                message="Review text is required for REVIEW interaction type",
                details={"field": "review_text"}
            )
            
        # Check if book exists
        book = db.exec(select(Book).where(Book.id == interaction_in.book_id)).first()
        if not book:
            raise ValidationException(
                message="Book not found",
                details={"field": "book_id"}
            )
            
        # Create interaction
        interaction_data = interaction_in.dict()
        interaction = UserBookInteraction(**interaction_data, user_id=user_id)
        db.add(interaction)
        db.commit()
        db.refresh(interaction)
        
        # Update book rating if this is a RATE interaction
        if interaction.interaction_type == InteractionType.RATE:
            book_service = None  # Import this inside method to avoid circular imports
            from services.book import BookService
            book_service = BookService()
            await book_service.update_book_ratings(db, interaction.book_id)
            
        # Load related book
        interaction.book = book
        
        return interaction
    
    @db_exception_handler
    @invalidate_cache(prefix="interaction_service")
    async def update_interaction(
        self, 
        db: Session, 
        interaction_id: str, 
        user_id: str,  # For authorization check
        interaction_in: InteractionUpdate
    ) -> Optional[UserBookInteraction]:
        """Update an existing interaction"""
        # Get existing interaction
        interaction = await self.get_by_id(db, interaction_id)
        if not interaction:
            return None
            
        # Check if user is authorized to update this interaction
        if interaction.user_id != user_id:
            raise ValidationException(
                message="Not authorized to update this interaction",
                details={"field": "user_id"}
            )
            
        # Validate rating if changing to RATE
        if interaction_in.interaction_type == InteractionType.RATE and interaction_in.rating is None:
            raise ValidationException(
                message="Rating is required for RATE interaction type",
                details={"field": "rating"}
            )
            
        # Validate review text if changing to REVIEW
        if interaction_in.interaction_type == InteractionType.REVIEW and not interaction_in.review_text:
            raise ValidationException(
                message="Review text is required for REVIEW interaction type",
                details={"field": "review_text"}
            )
            
        # Update interaction attributes
        update_data = interaction_in.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(interaction, key, value)
            
        interaction.updated_at = datetime.utcnow()
        db.add(interaction)
        db.commit()
        db.refresh(interaction)
        
        # Update book rating if this is a RATE interaction
        if interaction.interaction_type == InteractionType.RATE:
            book_service = None  # Import this inside method to avoid circular imports
            from services.book import BookService
            book_service = BookService()
            await book_service.update_book_ratings(db, interaction.book_id)
            
        # Load related book
        interaction.book = db.exec(
            select(Book).where(Book.id == interaction.book_id)
        ).first()
        
        return interaction
    
    @db_exception_handler
    @invalidate_cache(prefix="interaction_service")
    async def delete_interaction(
        self, 
        db: Session, 
        interaction_id: str, 
        user_id: str  # For authorization check
    ) -> bool:
        """Delete an interaction"""
        # Get existing interaction
        interaction = await self.get_by_id(db, interaction_id)
        if not interaction:
            return False
            
        # Check if user is authorized to delete this interaction
        if interaction.user_id != user_id:
            raise ValidationException(
                message="Not authorized to delete this interaction",
                details={"field": "user_id"}
            )
            
        # Store book_id for rating update
        book_id = interaction.book_id
        was_rating = interaction.interaction_type == InteractionType.RATE
        
        # Delete the interaction
        result = await self.delete(db, interaction_id)
        
        # Update book rating if this was a RATE interaction
        if result and was_rating:
            book_service = None  # Import this inside method to avoid circular imports
            from services.book import BookService
            book_service = BookService()
            await book_service.update_book_ratings(db, book_id)
            
        return result
    
    @db_exception_handler
    @cached(prefix="interaction_service", ttl=3600)  # 1 hour cache
    async def get_user_rated_books(self, db: Session, user_id: str) -> List[Book]:
        """Get all books rated by a user"""
        interactions = db.exec(
            select(UserBookInteraction)
            .where(
                UserBookInteraction.user_id == user_id,
                UserBookInteraction.interaction_type == InteractionType.RATE
            )
        ).all()
        
        book_ids = [interaction.book_id for interaction in interactions]
        books = []
        
        for book_id in book_ids:
            book = db.exec(select(Book).where(Book.id == book_id)).first()
            if book:
                books.append(book)
                
        return books
    
    @db_exception_handler
    @cached(prefix="interaction_service", ttl=3600)  # 1 hour cache
    async def get_user_bookmarked_books(self, db: Session, user_id: str) -> List[Book]:
        """Get all books bookmarked by a user"""
        interactions = db.exec(
            select(UserBookInteraction)
            .where(
                UserBookInteraction.user_id == user_id,
                UserBookInteraction.interaction_type == InteractionType.BOOKMARK
            )
        ).all()
        
        book_ids = [interaction.book_id for interaction in interactions]
        books = []
        
        for book_id in book_ids:
            book = db.exec(select(Book).where(Book.id == book_id)).first()
            if book:
                books.append(book)
                
        return books
    
    @db_exception_handler
    @cached(prefix="interaction_service", ttl=1800)  # 30 minute cache
    async def get_users_who_rated_book(self, db: Session, book_id: str, min_rating: float = 0) -> List[User]:
        """Get all users who rated a book, optionally with a minimum rating"""
        query = (
            select(UserBookInteraction)
            .where(
                UserBookInteraction.book_id == book_id,
                UserBookInteraction.interaction_type == InteractionType.RATE
            )
        )
        
        if min_rating > 0:
            query = query.where(UserBookInteraction.rating >= min_rating)
            
        interactions = db.exec(query).all()
        
        user_ids = [interaction.user_id for interaction in interactions]
        users = []
        
        for user_id in user_ids:
            user = db.exec(select(User).where(User.id == user_id)).first()
            if user:
                users.append(user)
                
        return users