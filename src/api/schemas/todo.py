"""Pydantic schemas for Todo validation."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class TodoPriority(str, Enum):
    """Todo priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TodoBase(BaseModel):
    """Base todo schema with common fields."""

    title: str = Field(..., min_length=1, max_length=255, description="Todo title")
    description: str | None = Field(None, description="Optional todo description")
    priority: TodoPriority = Field(default=TodoPriority.MEDIUM, description="Priority level")


class TodoCreate(TodoBase):
    """Schema for creating a new todo."""

    pass


class TodoUpdate(BaseModel):
    """Schema for updating a todo (all fields optional)."""

    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    is_completed: bool | None = None
    priority: TodoPriority | None = None


class TodoResponse(TodoBase):
    """Schema for todo responses."""

    id: int
    is_completed: bool
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TodoListResponse(BaseModel):
    """Schema for paginated todo list."""

    todos: list[TodoResponse]
    total: int
    page: int
    page_size: int
