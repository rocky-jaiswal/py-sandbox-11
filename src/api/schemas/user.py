"""Pydantic schemas for User validation."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserBase(BaseModel):
    """Base user schema with common fields."""

    email: EmailStr = Field(..., description="User email address")
    username: str = Field(..., min_length=3, max_length=100, description="Unique username")
    full_name: str = Field(..., min_length=1, max_length=255, description="User's full name")

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        """Validate username is alphanumeric with underscores."""
        if not v.replace("_", "").isalnum():
            raise ValueError("Username must be alphanumeric (underscores allowed)")
        return v


class UserCreate(UserBase):
    """Schema for creating a new user."""

    password: str = Field(..., min_length=8, max_length=100, description="User password")


class UserUpdate(BaseModel):
    """Schema for updating a user (all fields optional)."""

    email: EmailStr | None = None
    username: str | None = Field(None, min_length=3, max_length=100)
    full_name: str | None = Field(None, min_length=1, max_length=255)
    is_active: bool | None = None

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v: str | None) -> str | None:
        """Validate username is alphanumeric with underscores."""
        if v is not None and not v.replace("_", "").isalnum():
            raise ValueError("Username must be alphanumeric (underscores allowed)")
        return v


class UserResponse(UserBase):
    """Schema for user responses."""

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    """Schema for paginated user list."""

    users: list[UserResponse]
    total: int
    page: int
    page_size: int
