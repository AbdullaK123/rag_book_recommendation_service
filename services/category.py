from sqlmodel import Session, select
from typing import List, Optional
from models.models import Category, BookCategoryLink
from schemas.book import CategoryCreate, CategoryUpdate
from utils.decorators.db import db_exception_handler
from utils.decorators.cache import cached, invalidate_cache
from services.base import BaseService
from utils.exceptions.base import ValidationException


class CategoryService(BaseService[Category]):
    def __init__(self):
        super().__init__(Category)
        self.cache_prefix = "category_service"
    
    @db_exception_handler
    @cached(prefix="category_service", ttl=3600)  # 1 hour cache
    async def get_by_name(self, db: Session, name: str) -> Optional[Category]:
        """Get category by name"""
        return db.exec(select(Category).where(Category.name == name)).first()
    
    @db_exception_handler
    @cached(prefix="category_service", ttl=3600)
    async def get_all_categories(self, db: Session, skip: int = 0, limit: int = 100) -> List[Category]:
        """Get all categories with pagination"""
        return db.exec(
            select(Category)
            .offset(skip)
            .limit(limit)
            .order_by(Category.name)
        ).all()
    
    @db_exception_handler
    @invalidate_cache(prefix="category_service")
    async def create_category(self, db: Session, category_in: CategoryCreate) -> Category:
        """Create a new category"""
        # Check if name already exists
        existing_category = await self.get_by_name(db, category_in.name)
        if existing_category:
            raise ValidationException(
                message="Category name already exists",
                details={"field": "name"}
            )
            
        # Create category
        category = Category(**category_in.dict())
        db.add(category)
        db.commit()
        db.refresh(category)
        
        return category
    
    @db_exception_handler
    @invalidate_cache(prefix="category_service")
    async def update_category(self, db: Session, category_id: str, category_in: CategoryUpdate) -> Optional[Category]:
        """Update a category"""
        category = await self.get_by_id(db, category_id)
        if not category:
            return None
            
        # Check name uniqueness if changed
        if category_in.name and category_in.name != category.name:
            existing_category = await self.get_by_name(db, category_in.name)
            if existing_category:
                raise ValidationException(
                    message="Category name already exists",
                    details={"field": "name"}
                )
                
        # Update category attributes
        update_data = category_in.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(category, key, value)
            
        db.add(category)
        db.commit()
        db.refresh(category)
        
        return category
    
    @db_exception_handler
    @cached(prefix="category_service", ttl=3600)
    async def get_category_book_count(self, db: Session, category_id: str) -> int:
        """Get number of books in a category"""
        result = db.exec(
            select(BookCategoryLink)
            .where(BookCategoryLink.category_id == category_id)
        ).all()
        
        return len(result)
    
    @db_exception_handler
    @invalidate_cache(prefix="category_service")
    async def delete_category_if_unused(self, db: Session, category_id: str) -> bool:
        """Delete a category only if it's not used by any book"""
        book_count = await self.get_category_book_count(db, category_id)
        if book_count > 0:
            raise ValidationException(
                message="Cannot delete category that is used by books",
                details={"book_count": book_count}
            )
            
        # Delete category
        return await self.delete(db, category_id)
    
    @db_exception_handler
    @cached(prefix="category_service", ttl=3600)
    async def get_popular_categories(self, db: Session, limit: int = 10) -> List[Category]:
        """Get most popular categories based on book count"""
        # Get all category IDs with their book counts
        category_counts = {}
        
        # Get all book-category links
        links = db.exec(select(BookCategoryLink)).all()
        
        # Count books per category
        for link in links:
            category_counts[link.category_id] = category_counts.get(link.category_id, 0) + 1
            
        # Sort by count descending
        sorted_categories = sorted(
            category_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:limit]
        
        # Get top category objects
        result = []
        for category_id, _ in sorted_categories:
            category = await self.get_by_id(db, category_id)
            if category:
                result.append(category)
                
        return result