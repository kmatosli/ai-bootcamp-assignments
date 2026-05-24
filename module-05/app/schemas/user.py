"""
schemas/user.py

Pydantic schemas for User.
Password never appears in any response schema.
"""
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.common import RoleEnum


class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    role: RoleEnum = RoleEnum.analyst

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Amennai Beyeen",
                "email": "abeyeen@rhenman.com",
                "password": "securepassword123",
                "role": "analyst",
            }
        }
    }


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "name": "Amennai Beyeen",
                "email": "abeyeen@rhenman.com",
                "role": "analyst",
                "is_active": True,
                "created_at": "2026-05-21T10:00:00Z",
            }
        },
    }


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
            }
        }
    }


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)
