"""Custom exception classes for proper error handling."""

from typing import Any


class AppException(Exception):
    """Base exception for all application errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


# 4xx Client Errors
class BadRequestError(AppException):
    """400 Bad Request - Client sent invalid data."""

    def __init__(self, message: str = "Bad request", details: dict[str, Any] | None = None) -> None:
        super().__init__(message=message, status_code=400, details=details)


class UnauthorizedError(AppException):
    """401 Unauthorized - Authentication required."""

    def __init__(
        self, message: str = "Unauthorized", details: dict[str, Any] | None = None
    ) -> None:
        super().__init__(message=message, status_code=401, details=details)


class ForbiddenError(AppException):
    """403 Forbidden - Client lacks permissions."""

    def __init__(self, message: str = "Forbidden", details: dict[str, Any] | None = None) -> None:
        super().__init__(message=message, status_code=403, details=details)


class NotFoundError(AppException):
    """404 Not Found - Resource does not exist."""

    def __init__(
        self, message: str = "Resource not found", details: dict[str, Any] | None = None
    ) -> None:
        super().__init__(message=message, status_code=404, details=details)


class ConflictError(AppException):
    """409 Conflict - Resource already exists or state conflict."""

    def __init__(self, message: str = "Conflict", details: dict[str, Any] | None = None) -> None:
        super().__init__(message=message, status_code=409, details=details)


class UnprocessableEntityError(AppException):
    """422 Unprocessable Entity - Semantic validation errors."""

    def __init__(
        self, message: str = "Unprocessable entity", details: dict[str, Any] | None = None
    ) -> None:
        super().__init__(message=message, status_code=422, details=details)


# 5xx Server Errors
class InternalServerError(AppException):
    """500 Internal Server Error - Unexpected server error."""

    def __init__(
        self, message: str = "Internal server error", details: dict[str, Any] | None = None
    ) -> None:
        super().__init__(message=message, status_code=500, details=details)


class ServiceUnavailableError(AppException):
    """503 Service Unavailable - Temporary service unavailability."""

    def __init__(
        self, message: str = "Service unavailable", details: dict[str, Any] | None = None
    ) -> None:
        super().__init__(message=message, status_code=503, details=details)


class DatabaseError(InternalServerError):
    """Database operation error - Always 5xx."""

    def __init__(
        self, message: str = "Database error occurred", details: dict[str, Any] | None = None
    ) -> None:
        super().__init__(message=message, details=details)
