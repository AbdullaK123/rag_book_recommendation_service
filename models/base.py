from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps to models."""
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: Optional[datetime] = Field(default=None, sa_column_kwargs={"onupdate": datetime.utcnow})