from sqlmodel import Session, select, SQLModel
from typing import TypeVar, Generic, Type, List, Optional, Any
from utils.decorators.db import db_exception_handler
from utils.decorators.cache import cached
from utils.cache.redis_client import get_redis_client

T = TypeVar('T', bound=SQLModel)

class BaseService(Generic[T]):
    def __init__(self, model: Type[T]):
        self.model = model
        self.cache = get_redis_client()  # Get Redis client for caching
        self.cache_prefix = f"{self.__class__.__name__}"  # Use class name as cache prefix
    
    @db_exception_handler
    @cached(prefix="base_service", ttl=300)  # 5 minute default cache
    async def get_by_id(self, db: Session, id: str) -> Optional[T]:
        """Get a record by ID"""
        return db.exec(select(self.model).where(self.model.id == id)).first()
    
    @db_exception_handler
    @cached(prefix="base_service", ttl=300)
    async def get_all(self, db: Session) -> List[T]:
        """Get all records"""
        return db.exec(select(self.model)).all()
    
    @db_exception_handler
    async def create(self, db: Session, obj_in: SQLModel) -> T:
        """Create a new record"""
        db_obj = self.model.from_orm(obj_in) if not isinstance(obj_in, self.model) else obj_in
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    @db_exception_handler
    async def update(self, db: Session, id: str, obj_in: SQLModel) -> Optional[T]:
        """Update a record"""
        db_obj = await self.get_by_id(db, id)
        if not db_obj:
            return None
            
        obj_data = obj_in.dict(exclude_unset=True)
        for key, value in obj_data.items():
            setattr(db_obj, key, value)
            
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    @db_exception_handler
    async def delete(self, db: Session, id: str) -> bool:
        """Delete a record by ID"""
        db_obj = await self.get_by_id(db, id)
        if db_obj:
            db.delete(db_obj)
            db.commit()
            return True
        return False
    
    @db_exception_handler
    async def exists(self, db: Session, id: str) -> bool:
        """Check if a record exists by ID"""
        result = await self.get_by_id(db, id)
        return result is not None