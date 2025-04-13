from typing import Optional
from sqlmodel import SQLModel, Field
from pydantic import validator


class LoginRequest(SQLModel):
    """Schema for user login"""
    username: str
    password: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "johndoe",
                "password": "SecurePassword123"
            }
        }


class LoginResponse(SQLModel):
    """Schema for login response"""
    session_id: str
    user_id: int
    username: str
    is_admin: bool


class SessionData(SQLModel):
    """Schema for session data stored in Redis"""
    user_id: int
    username: str
    is_admin: bool = False
    created_at: int  # Unix timestamp
    expires_at: int  # Unix timestamp


class LogoutRequest(SQLModel):
    """Schema for logout request"""
    session_id: str


class PasswordResetRequest(SQLModel):
    """Schema for requesting a password reset"""
    email: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }


class PasswordResetConfirm(SQLModel):
    """Schema for confirming a password reset"""
    token: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "token": "reset-token-from-email",
                "new_password": "NewSecurePassword123",
                "confirm_password": "NewSecurePassword123"
            }
        }