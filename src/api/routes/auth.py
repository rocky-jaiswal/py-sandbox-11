"""Authentication routes for login and registration."""

from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.auth import CurrentUser
from api.core.database import get_db
from api.core.exceptions import ConflictError, UnauthorizedError
from api.core.logging import get_logger
from api.core.security import get_jwt_manager, hash_password, verify_password
from api.models.user import User
from api.schemas.auth import LoginRequest, TokenResponse
from api.schemas.user import UserCreate, UserResponse

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Register a new user."""
    logger.info("registering_user", username=user_data.username)

    # Check if email already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise ConflictError(f"User with email '{user_data.email}' already exists")

    # Check if username already exists
    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalar_one_or_none():
        raise ConflictError(f"Username '{user_data.username}' is already taken")

    # Hash password and create user
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

    logger.info("user_registered", user_id=user.id, username=user.username)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Authenticate user and return JWT token."""
    logger.info("login_attempt", username=login_data.username)

    # Find user by username or email
    result = await db.execute(
        select(User).where(
            (User.username == login_data.username) | (User.email == login_data.username)
        )
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(login_data.password, user.hashed_password):
        logger.warning("login_failed", username=login_data.username)
        raise UnauthorizedError("Incorrect username or password")

    if not user.is_active:
        logger.warning("inactive_user_login_attempt", user_id=user.id)
        raise UnauthorizedError("User account is inactive")

    # Generate JWT token
    jwt_manager = get_jwt_manager()
    access_token_expires = timedelta(hours=24)
    access_token = jwt_manager.create_access_token(
        subject=str(user.id), expires_delta=access_token_expires
    )

    logger.info("login_successful", user_id=user.id, username=user.username)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=int(access_token_expires.total_seconds()),
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: CurrentUser) -> User:
    """Get current authenticated user information."""
    return current_user
