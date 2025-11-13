"""Authentication dependencies for FastAPI."""

from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.database import get_db
from api.core.exceptions import UnauthorizedError
from api.core.logging import get_logger
from api.core.security import get_jwt_manager
from api.models.user import User

logger = get_logger(__name__)

security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Get current authenticated user from JWT token.

    Args:
        credentials: HTTP bearer token credentials
        db: Database session

    Returns:
        Authenticated user

    Raises:
        UnauthorizedError: If token is invalid or user not found
    """
    token = credentials.credentials

    try:
        jwt_manager = get_jwt_manager()
        payload = jwt_manager.decode_token(token)
        user_id: str | None = payload.get("sub")

        if user_id is None:
            raise UnauthorizedError("Invalid authentication token")

    except jwt.ExpiredSignatureError:
        logger.warning("expired_token_attempt")
        raise UnauthorizedError("Token has expired")
    except jwt.InvalidTokenError as e:
        logger.warning("invalid_token_attempt", error=str(e))
        raise UnauthorizedError("Invalid authentication token")

    # Fetch user from database
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if user is None:
        raise UnauthorizedError("User not found")

    if not user.is_active:
        raise UnauthorizedError("User account is inactive")

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Get current active user (additional layer for future extensibility)."""
    return current_user


# Type alias for easier use in route dependencies
CurrentUser = Annotated[User, Depends(get_current_active_user)]
