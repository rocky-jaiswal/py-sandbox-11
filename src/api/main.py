"""Main FastAPI application with async support."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC
from typing import Annotated, Any

from fastapi import Depends, FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.config import get_settings
from api.core.database import close_db, get_db, init_db
from api.core.exceptions import AppException
from api.core.logging import configure_logging, get_logger
from api.middleware.error_handler import (
    app_exception_handler,
    generic_exception_handler,
    sqlalchemy_exception_handler,
    validation_exception_handler,
)
from api.routes import auth, todos, users

# Configure logging first
configure_logging()
logger = get_logger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info(
        "application_starting",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )

    # Initialize database tables
    try:
        await init_db()
        logger.info("database_initialized")
    except Exception as e:
        logger.error("database_initialization_failed", error=str(e))
        raise

    yield

    # Shutdown
    logger.info("application_shutting_down")
    await close_db()
    logger.info("database_connections_closed")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Pure Async REST API with request validation, logging, and error handling",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)


# Register exception handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)


# Health check endpoint (under v1)
@app.get("/v1/health", status_code=status.HTTP_200_OK, tags=["health"])
async def health_check(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """Health check endpoint with database connectivity check."""
    from datetime import datetime

    from sqlalchemy import text

    health_status = {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.environment,
        "timestamp": datetime.now(UTC).isoformat(),
    }

    # Check database connectivity
    try:
        result = await db.execute(text("SELECT NOW() as current_time"))
        db_time = result.scalar_one()
        health_status["database"] = {
            "status": "connected",
            "current_time": db_time.isoformat() if db_time else None,
        }
    except Exception as e:
        logger.error("database_health_check_failed", error=str(e))
        health_status["database"] = {
            "status": "disconnected",
            "error": str(e),
        }
        health_status["status"] = "unhealthy"

    return health_status


# Register routers under v1 prefix
app.include_router(auth.router, prefix="/v1")
app.include_router(users.router, prefix="/v1")
app.include_router(todos.router, prefix="/v1")


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests with response time and structured data."""
    import time
    import uuid

    # Generate unique request ID
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    # Start timer
    start_time = time.perf_counter()

    # Extract request details
    client_host = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent", "unknown")

    # Log incoming request
    logger.info(
        "http_request_start",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        query_params=str(request.query_params) if request.query_params else None,
        client_ip=client_host,
        user_agent=user_agent,
        http_version=request.scope.get("http_version"),
    )

    # Process request
    try:
        response = await call_next(request)

        # Calculate response time
        process_time = time.perf_counter() - start_time
        response_time_ms = round(process_time * 1000, 2)

        # Add custom headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(response_time_ms)

        # Log completed request with full details
        logger.info(
            "http_request_complete",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            response_time_ms=response_time_ms,
            client_ip=client_host,
            success=200 <= response.status_code < 400,
        )

        return response

    except Exception as e:
        # Log failed request
        process_time = time.perf_counter() - start_time
        response_time_ms = round(process_time * 1000, 2)

        logger.error(
            "http_request_failed",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            response_time_ms=response_time_ms,
            error=str(e),
            error_type=type(e).__name__,
            client_ip=client_host,
        )
        raise


def run() -> None:
    """Run the application using uvicorn."""
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_config=None,  # Use our structlog configuration
    )


if __name__ == "__main__":
    run()
