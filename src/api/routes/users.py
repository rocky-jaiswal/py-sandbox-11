"""User API routes with full async support."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.database import get_db
from api.core.exceptions import ConflictError, NotFoundError
from api.core.logging import get_logger
from api.core.security import hash_password
from api.models.user import User
from api.schemas.user import UserCreate, UserListResponse, UserResponse, UserUpdate

logger = get_logger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
)
async def create_user(
    user_data: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Create a new user with validation."""
    logger.info("creating_user", email=user_data.email, username=user_data.username)

    # Check if email already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise ConflictError(f"User with email '{user_data.email}' already exists")

    # Check if username already exists
    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalar_one_or_none():
        raise ConflictError(f"Username '{user_data.username}' is already taken")

    # Hash password and create new user
    hashed_password = hash_password(user_data.password)
    user = User(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    logger.info("user_created", user_id=user.id, username=user.username)
    return user


@router.get(
    "",
    response_model=UserListResponse,
    summary="List all users with pagination",
)
async def list_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
) -> UserListResponse:
    """Get paginated list of users."""
    offset = (page - 1) * page_size

    # Get total count
    count_result = await db.execute(select(User))
    total = len(count_result.scalars().all())

    # Get paginated users
    result = await db.execute(select(User).offset(offset).limit(page_size))
    users = result.scalars().all()

    logger.info("users_listed", total=total, page=page, returned=len(users))

    return UserListResponse(
        users=list(users),
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID",
)
async def get_user(
    user_id: Annotated[int, Path(ge=1)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Get a specific user by ID."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise NotFoundError(f"User with ID {user_id} not found")

    logger.info("user_retrieved", user_id=user.id)
    return user


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update user",
)
async def update_user(
    user_id: Annotated[int, Path(ge=1)],
    user_data: UserUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Update a user's information."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise NotFoundError(f"User with ID {user_id} not found")

    # Update only provided fields
    update_data = user_data.model_dump(exclude_unset=True)

    if "email" in update_data and update_data["email"] != user.email:
        # Check email uniqueness
        result = await db.execute(select(User).where(User.email == update_data["email"]))
        if result.scalar_one_or_none():
            raise ConflictError(f"Email '{update_data['email']}' is already in use")

    if "username" in update_data and update_data["username"] != user.username:
        # Check username uniqueness
        result = await db.execute(select(User).where(User.username == update_data["username"]))
        if result.scalar_one_or_none():
            raise ConflictError(f"Username '{update_data['username']}' is already taken")

    for field, value in update_data.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)

    logger.info("user_updated", user_id=user.id, updated_fields=list(update_data.keys()))
    return user


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user",
)
async def delete_user(
    user_id: Annotated[int, Path(ge=1)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete a user."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise NotFoundError(f"User with ID {user_id} not found")

    await db.delete(user)
    await db.commit()

    logger.info("user_deleted", user_id=user_id)
