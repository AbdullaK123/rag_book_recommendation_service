from sqlmodel import Session, select, col, or_
from typing import List, Optional, Dict, Any
from models.models import Book, Category, BookCategoryLink
from schemas.book import BookCreate, BookUpdate, BookSearchParams
from utils.decorators.db import db_exception_handler
from utils.decorators.cache import cached, invalidate_cache
from services.base import BaseService


class BookService(BaseService[Book]):
    def __init__(self):
        super().__init__(Book)
        self.cache_prefix = "book_service"
    
    @db_exception_handler
    @cached(prefix="book_service", ttl=600)  # 10 minute cache
    async def get_books_with_categories(self, db: Session, skip: int = 0, limit: int = 100) -> List[Book]:
        """Get books with their categories"""
        books = db.exec(
            select(Book)
            .offset(skip)
            .limit(limit)
            .order_by(Book.title)
        ).all()
        
        # Load categories for each book
        for book in books:
            book.categories = db.exec(
                select(Category)
                .join(BookCategoryLink)
                .where(BookCategoryLink.book_id == book.id)
            ).all()
            
        return books
    
    @db_exception_handler
    @cached(prefix="book_service", ttl=600)
    async def get_book_with_categories(self, db: Session, book_id: str) -> Optional[Book]:
        """Get a single book with its categories"""
        book = await self.get_by_id(db, book_id)
        if not book:
            return None
            
        book.categories = db.exec(
            select(Category)
            .join(BookCategoryLink)
            .where(BookCategoryLink.book_id == book_id)
        ).all()
            
        return book
    
    @db_exception_handler
    @cached(prefix="book_service", ttl=300)
    async def search_books(
        self, 
        db: Session, 
        params: BookSearchParams,
        skip: int = 0, 
        limit: int = 10
    ) -> List[Book]:
        """Search books by various criteria"""
        query = select(Book)
        
        # Apply filters based on search parameters
        if params.title:
            query = query.where(col(Book.title).contains(params.title))
        
        if params.author:
            query = query.where(col(Book.author).contains(params.author))
        
        if params.category_id:
            query = query.join(BookCategoryLink).where(
                BookCategoryLink.category_id == params.category_id
            )
        
        if params.language:
            query = query.where(Book.language == params.language)
        
        if params.min_publication_year:
            query = query.where(Book.publication_year >= params.min_publication_year)
        
        if params.max_publication_year:
            query = query.where(Book.publication_year <= params.max_publication_year)
        
        if params.min_page_count:
            query = query.where(Book.page_count >= params.min_page_count)
        
        if params.max_page_count:
            query = query.where(Book.page_count <= params.max_page_count)
        
        if params.min_rating:
            query = query.where(Book.average_rating >= params.min_rating)
            
        # Apply pagination
        query = query.offset(skip).limit(limit).order_by(Book.title)
        
        # Execute query
        books = db.exec(query).all()
        
        # Load categories for each book
        for book in books:
            book.categories = db.exec(
                select(Category)
                .join(BookCategoryLink)
                .where(BookCategoryLink.book_id == book.id)
            ).all()
            
        return books
    
    @db_exception_handler
    @invalidate_cache(prefix="book_service")
    async def create_book(self, db: Session, book_in: BookCreate) -> Book:
        """Create a new book with categories"""
        # Create book
        book_data = book_in.dict(exclude={"category_ids"})
        book = Book(**book_data)
        db.add(book)
        db.commit()
        db.refresh(book)
        
        # Add categories
        if book_in.category_ids:
            for category_id in book_in.category_ids:
                link = BookCategoryLink(book_id=book.id, category_id=category_id)
                db.add(link)
            
            db.commit()
            
        # Load categories
        book.categories = db.exec(
            select(Category)
            .join(BookCategoryLink)
            .where(BookCategoryLink.book_id == book.id)
        ).all()
        
        return book
    
    @db_exception_handler
    @invalidate_cache(prefix="book_service")
    async def update_book(self, db: Session, book_id: str, book_in: BookUpdate) -> Optional[Book]:
        """Update a book and its categories"""
        book = await self.get_by_id(db, book_id)
        if not book:
            return None
            
        # Update book attributes
        update_data = book_in.dict(exclude={"category_ids"}, exclude_unset=True)
        for key, value in update_data.items():
            setattr(book, key, value)
        
        # Update categories if provided
        if book_in.category_ids is not None:
            # Remove existing category links
            db.exec(
                select(BookCategoryLink)
                .where(BookCategoryLink.book_id == book_id)
            ).delete()
            
            # Add new category links
            for category_id in book_in.category_ids:
                link = BookCategoryLink(book_id=book_id, category_id=category_id)
                db.add(link)
        
        db.add(book)
        db.commit()
        db.refresh(book)
        
        # Load categories
        book.categories = db.exec(
            select(Category)
            .join(BookCategoryLink)
            .where(BookCategoryLink.book_id == book.id)
        ).all()
        
        return book
    
    @db_exception_handler
    @cached(prefix="book_service", ttl=3600)  # 1 hour cache for popular books
    async def get_popular_books(self, db: Session, limit: int = 10) -> List[Book]:
        """Get popular books based on ratings"""
        books = db.exec(
            select(Book)
            .where(Book.ratings_count > 0)
            .order_by(col(Book.average_rating).desc(), col(Book.ratings_count).desc())
            .limit(limit)
        ).all()
        
        # Load categories for each book
        for book in books:
            book.categories = db.exec(
                select(Category)
                .join(BookCategoryLink)
                .where(BookCategoryLink.book_id == book.id)
            ).all()
            
        return books
    
    @db_exception_handler
    @cached(prefix="book_service", ttl=3600)
    async def get_books_by_category(self, db: Session, category_id: str, limit: int = 10) -> List[Book]:
        """Get books by category"""
        books = db.exec(
            select(Book)
            .join(BookCategoryLink)
            .where(BookCategoryLink.category_id == category_id)
            .order_by(Book.title)
            .limit(limit)
        ).all()
        
        # Load all categories for each book
        for book in books:
            book.categories = db.exec(
                select(Category)
                .join(BookCategoryLink)
                .where(BookCategoryLink.book_id == book.id)
            ).all()
            
        return books
    
    @db_exception_handler
    @invalidate_cache(prefix="book_service", key_pattern="book_*")
    async def update_book_ratings(self, db: Session, book_id: str) -> Optional[Book]:
        """Update a book's average rating and rating count based on user interactions"""
        from models.models import UserBookInteraction, InteractionType
        
        book = await self.get_by_id(db, book_id)
        if not book:
            return None
        
        # Get all RATE interactions for this book
        ratings = db.exec(
            select(UserBookInteraction)
            .where(
                UserBookInteraction.book_id == book_id,
                UserBookInteraction.interaction_type == InteractionType.RATE,
                UserBookInteraction.rating != None
            )
        ).all()
        
        # Calculate new average
        if ratings:
            total_rating = sum(r.rating for r in ratings if r.rating is not None)
            book.ratings_count = len(ratings)
            book.average_rating = total_rating / book.ratings_count if book.ratings_count > 0 else 0
        else:
            book.ratings_count = 0
            book.average_rating = 0
            
        # Save changes
        db.add(book)
        db.commit()
        db.refresh(book)
        
        return book