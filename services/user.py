from sqlmodel import Session, select
from typing import List, Optional, Dict, Any
import json
from datetime import datetime
from models.models import User, UserPreference
from schemas.user import UserCreate, UserUpdate, UserPasswordUpdate
from utils.decorators.db import db_exception_handler
from utils.decorators.cache import cached, invalidate_cache
from services.base import BaseService
from utils.exceptions.base import ValidationException


class UserService(BaseService[User]):
    def __init__(self):
        super().__init__(User)
        self.cache_prefix = "user_service"
    
    @db_exception_handler
    @cached(prefix="user_service", ttl=300)
    async def get_by_username(self, db: Session, username: str) -> Optional[User]:
        """Get user by username"""
        return db.exec(select(User).where(User.username == username)).first()
    
    @db_exception_handler
    @cached(prefix="user_service", ttl=300)
    async def get_by_email(self, db: Session, email: str) -> Optional[User]:
        """Get user by email"""
        return db.exec(select(User).where(User.email == email)).first()
    
    @db_exception_handler
    @invalidate_cache(prefix="user_service")
    async def create_user(self, db: Session, user_in: UserCreate, hashed_password: str) -> User:
        """Create a new user"""
        # Check if username or email already exists
        existing_user = await self.get_by_username(db, user_in.username)
        if existing_user:
            raise ValidationException(
                message="Username already exists",
                details={"field": "username"}
            )
            
        existing_email = await self.get_by_email(db, user_in.email)
        if existing_email:
            raise ValidationException(
                message="Email already exists",
                details={"field": "email"}
            )
            
        # Create user
        user_data = user_in.dict(exclude={"password"})
        user = User(**user_data, hashed_password=hashed_password)
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Create default empty preferences
        preferences = UserPreference(user_id=user.id)
        db.add(preferences)
        db.commit()
        
        return user
    
    @db_exception_handler
    @invalidate_cache(prefix="user_service")
    async def update_user(self, db: Session, user_id: str, user_in: UserUpdate) -> Optional[User]:
        """Update user"""
        user = await self.get_by_id(db, user_id)
        if not user:
            return None
            
        # Check username uniqueness if changed
        if user_in.username and user_in.username != user.username:
            existing_user = await self.get_by_username(db, user_in.username)
            if existing_user:
                raise ValidationException(
                    message="Username already exists",
                    details={"field": "username"}
                )
                
        # Check email uniqueness if changed
        if user_in.email and user_in.email != user.email:
            existing_email = await self.get_by_email(db, user_in.email)
            if existing_email:
                raise ValidationException(
                    message="Email already exists",
                    details={"field": "email"}
                )
        
        # Update user attributes
        update_data = user_in.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(user, key, value)
            
        user.updated_at = datetime.utcnow()
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user
    
    @db_exception_handler
    @invalidate_cache(prefix="user_service")
    async def update_password(
        self, 
        db: Session, 
        user_id: str, 
        current_password_hash: str,
        new_password_hash: str
    ) -> Optional[User]:
        """Update user password"""
        user = await self.get_by_id(db, user_id)
        if not user:
            return None
            
        # Verify current password
        if user.hashed_password != current_password_hash:
            raise ValidationException(
                message="Current password is incorrect",
                details={"field": "current_password"}
            )
            
        # Update password
        user.hashed_password = new_password_hash
        user.updated_at = datetime.utcnow()
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user
    
    @db_exception_handler
    @invalidate_cache(prefix="user_service")
    async def deactivate_user(self, db: Session, user_id: str) -> Optional[User]:
        """Deactivate a user account"""
        user = await self.get_by_id(db, user_id)
        if not user:
            return None
            
        user.is_active = False
        user.updated_at = datetime.utcnow()
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user
    
    @db_exception_handler
    @invalidate_cache(prefix="user_service")
    async def reactivate_user(self, db: Session, user_id: str) -> Optional[User]:
        """Reactivate a user account"""
        user = await self.get_by_id(db, user_id)
        if not user:
            return None
            
        user.is_active = True
        user.updated_at = datetime.utcnow()
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user
    
    @db_exception_handler
    @cached(prefix="user_service", ttl=600)
    async def get_user_preferences(self, db: Session, user_id: str) -> Optional[UserPreference]:
        """Get a user's preferences"""
        preferences = db.exec(
            select(UserPreference).where(UserPreference.user_id == user_id)
        ).first()
        
        return preferences
    
    @db_exception_handler
    @invalidate_cache(prefix="user_service")
    async def update_user_preferences(
        self, 
        db: Session, 
        user_id: str, 
        category_preferences: Optional[Dict[str, float]] = None,
        preferences_data: Optional[Dict[str, Any]] = None
    ) -> Optional[UserPreference]:
        """Update a user's preferences"""
        # Get current preferences
        preferences = await self.get_user_preferences(db, user_id)
        if not preferences:
            # Create if not exists
            preferences = UserPreference(user_id=user_id)
            
        # Update category preferences if provided
        if category_preferences is not None:
            preferences.set_category_preferences(category_preferences)
            
        # Update other preferences if provided
        if preferences_data:
            for key, value in preferences_data.items():
                if key == 'custom_preferences':
                    # Handle custom preferences separately
                    current_custom = preferences.get_custom_preferences()
                    current_custom.update(value)
                    preferences.set_custom_preferences(current_custom)
                elif hasattr(preferences, key):
                    setattr(preferences, key, value)
                    
        preferences.updated_at = datetime.utcnow()
        db.add(preferences)
        db.commit()
        db.refresh(preferences)
        
        return preferences