"""Error handling middleware for consistent error responses."""

import traceback
from typing import Any

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from api.core.exceptions import AppException
from api.core.logging import get_logger

logger = get_logger(__name__)


def create_error_response(
    status_code: int,
    message: str,
    details: dict[str, Any] | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Create standardized error response."""
    error_response: dict[str, Any] = {
        "error": {
            "status_code": status_code,
            "message": message,
            "type": "client_error" if 400 <= status_code < 500 else "server_error",
        }
    }

    if details:
        error_response["error"]["details"] = details

    if request_id:
        error_response["request_id"] = request_id

    return error_response


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle custom application exceptions."""
    request_id = getattr(request.state, "request_id", None) or request.headers.get("X-Request-ID")

    # Log based on error type
    if exc.status_code >= 500:
        logger.error(
            "server_error",
            status_code=exc.status_code,
            message=exc.message,
            path=request.url.path,
            method=request.method,
            request_id=request_id,
            details=exc.details,
        )
    else:
        logger.warning(
            "client_error",
            status_code=exc.status_code,
            message=exc.message,
            path=request.url.path,
            method=request.method,
            request_id=request_id,
        )

    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            status_code=exc.status_code,
            message=exc.message,
            details=exc.details if exc.details else None,
            request_id=request_id,
        ),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors (422)."""
    request_id = getattr(request.state, "request_id", None) or request.headers.get("X-Request-ID")

    errors = exc.errors()
    logger.warning(
        "validation_error",
        path=request.url.path,
        method=request.method,
        errors=errors,
        request_id=request_id,
    )

    # Format validation errors
    validation_details = {
        "validation_errors": [
            {
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            }
            for error in errors
        ]
    }

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=create_error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message="Request validation failed",
            details=validation_details,
            request_id=request_id,
        ),
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Handle SQLAlchemy database errors (500)."""
    request_id = getattr(request.state, "request_id", None) or request.headers.get("X-Request-ID")

    logger.error(
        "database_error",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        request_id=request_id,
        exc_info=True,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Database error occurred",
            request_id=request_id,
        ),
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions (500)."""
    request_id = getattr(request.state, "request_id", None) or request.headers.get("X-Request-ID")

    logger.error(
        "unhandled_exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        traceback=traceback.format_exc(),
        request_id=request_id,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="An unexpected error occurred",
            request_id=request_id,
        ),
    )
