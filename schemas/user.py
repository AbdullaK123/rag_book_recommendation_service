from typing import Optional, List
from sqlmodel import SQLModel, Field
from pydantic import EmailStr, validator


class UserBase(SQLModel):
    """Base schema for user data"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = None
    bio: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a new user"""
    password: str = Field(..., min_length=8, description="User password")
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "johndoe",
                "email": "john.doe@example.com",
                "full_name": "John Doe",
                "bio": "Book enthusiast and sci-fi lover",
                "password": "SecurePassword123"
            }
        }


class UserUpdate(SQLModel):
    """Schema for updating a user"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    bio: Optional[str] = None
    is_active: Optional[bool] = None


class UserPasswordUpdate(SQLModel):
    """Schema for updating a user's password"""
    current_password: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v


class UserRead(UserBase):
    """Schema for user responses, excluding sensitive data"""
    id: int
    is_active: bool = True
    is_admin: bool = False


class UsersListResponse(SQLModel):
    """Schema for returning a list of users"""
    users: List[UserRead]
    total: int