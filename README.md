# Pure Async REST API with JWT Auth

A fully asynchronous REST API built with FastAPI, SQLAlchemy 2.0+, and PostgreSQL. Features JWT authentication (RS256), protected routes, database migrations, clean architecture, comprehensive error handling, and structured logging.

## Features

- **Pure Async** - Fully asynchronous from API to database operations
- **JWT Authentication** - RS256 (asymmetric) JWT tokens with secure authentication
- **Protected Routes** - User-scoped authorization for todo management
- **Database Migrations** - Alembic for version-controlled schema changes
- **Request Validation** - Pydantic v2 schemas with comprehensive validation
- **Error Handling** - Proper 4xx (client errors) vs 5xx (server errors) distinction
- **Structured Logging** - JSON/console logging with structlog, response time tracking, and request IDs
- **Database ORM** - Async SQLAlchemy 2.0+ with asyncpg driver for PostgreSQL
- **Clean Architecture** - Modular design with separation of concerns
- **Password Hashing** - Bcrypt for secure password storage

## Tech Stack

- **FastAPI** - Modern async web framework
- **SQLAlchemy 2.0+** - Async ORM with full type hints
- **Alembic** - Database migration tool
- **asyncpg** - High-performance async PostgreSQL driver
- **PyJWT** - RS256 JWT token generation and validation
- **Pydantic v2** - Data validation using Python type hints
- **passlib** - Password hashing with bcrypt
- **structlog** - Structured logging
- **uvicorn** - ASGI server

## Project Structure

```
src/api/
├── core/                  # Core configuration and utilities
│   ├── config.py          # Environment configuration
│   ├── database.py        # Async database setup
│   ├── logging.py         # Structured logging
│   ├── security.py        # JWT and password hashing
│   ├── auth.py            # Authentication dependencies
│   └── exceptions.py      # Custom exception classes
├── middleware/            # Custom middleware
│   └── error_handler.py   # Error handling middleware
├── models/                # SQLAlchemy models
│   ├── user.py            # User model with auth
│   └── todo.py            # Todo model (one-to-many with User)
├── routes/                # API route handlers
│   ├── auth.py            # Login/register endpoints
│   ├── users.py           # User CRUD
│   └── todos.py           # Protected todo CRUD
├── schemas/               # Pydantic validation schemas
│   ├── auth.py            # Auth request/response schemas
│   ├── user.py            # User schemas
│   └── todo.py            # Todo schemas
└── main.py                # Application entry point

migrations/                # Alembic database migrations
scripts/                   # Utility scripts
keys/                      # RSA keys for JWT (gitignored)
```

## Setup

### Prerequisites

- Python 3.12+
- PostgreSQL 12+
- Docker (optional, for running PostgreSQL)
- uv (recommended) or pip

### Installation

1. Clone the repository and navigate to the project directory

2. Create and activate virtual environment:

```bash
uv venv
source .venv/bin/activate  # or .venv/bin/activate.fish for fish shell
```

3.Install dependencies:

```bash
uv sync
```

4.Generate RSA keys for JWT authentication:

```bash
uv run python scripts/generate_keys.py
```

This creates:

- `keys/private_key.pem` - Private key for signing tokens (never commit!)
- `keys/public_key.pem` - Public key for verifying tokens

5.Start PostgreSQL (using Docker):

```bash
docker compose up -d
```

Or use your own PostgreSQL instance and configure the connection in `.env`

6.Configure environment variables:

```bash
cp .env.example .env
# Edit .env with your database credentials if needed
```

7.Run database migrations:

```bash
uv run alembic upgrade head
```

## Running the Application

### Development mode (with auto-reload)

```bash
uv run uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Access the API

- API: <http://localhost:8000>
- Interactive docs (Swagger): <http://localhost:8000/docs>
- Alternative docs (ReDoc): <http://localhost:8000/redoc>
- Health check: <http://localhost:8000/v1/health>

## API Endpoints

All endpoints are versioned under the `/v1` prefix.

### Health (`/v1/health`)

- `GET /v1/health` - Health check with database connectivity test

### Authentication (`/v1/auth`)

- `POST /v1/auth/register` - Register a new user
- `POST /v1/auth/login` - Login and get JWT token
- `GET /v1/auth/me` - Get current user info (protected)

### Users API (`/v1/users`)

- `POST /v1/users` - Create a new user
- `GET /v1/users` - List users (paginated)
- `GET /v1/users/{user_id}` - Get user by ID
- `PATCH /v1/users/{user_id}` - Update user
- `DELETE /v1/users/{user_id}` - Delete user

### Todos API (`/v1/todos`) - 🔒 Protected

All todo endpoints require JWT authentication. Users can only access their own todos.

- `POST /v1/todos` - Create a new todo
- `GET /v1/todos` - List todos (paginated, with optional `completed` filter)
- `GET /v1/todos/{todo_id}` - Get todo by ID
- `PATCH /v1/todos/{todo_id}` - Update todo
- `DELETE /v1/todos/{todo_id}` - Delete todo

## Usage Examples

### 1. Check API health

```bash
curl http://localhost:8000/v1/health
```

Response:

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "environment": "development",
  "timestamp": "2025-01-15T10:30:00.000000+00:00",
  "database": {
    "status": "connected",
    "current_time": "2025-01-15T10:30:00.123456+00:00"
  }
}
```

### 2. Register a new user

```bash
curl -X POST http://localhost:8000/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "username": "john_doe",
    "full_name": "John Doe",
    "password": "securepass123"
  }'
```

### 3. Login and get JWT token

```bash
curl -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "securepass123"
  }'
```

Response:

```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

### 4. Create a todo (protected)

```bash
curl -X POST http://localhost:8000/v1/todos \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "title": "Learn FastAPI",
    "description": "Build an async REST API",
    "priority": "high"
  }'
```

### 5. List your todos (protected)

```bash
curl http://localhost:8000/v1/todos \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Database Migrations

### Create a new migration

```bash
uv run alembic revision --autogenerate -m "Description of changes"
```

### Apply migrations

```bash
uv run alembic upgrade head
```

### Rollback migrations

```bash
uv run alembic downgrade -1  # Rollback one migration
uv run alembic downgrade base  # Rollback all migrations
```

### View migration history

```bash
uv run alembic history
```

## Error Handling

The API provides consistent error responses with proper HTTP status codes:

**Client Errors (4xx):**

- 400 - Bad Request
- 401 - Unauthorized (invalid or expired token)
- 403 - Forbidden (insufficient permissions)
- 404 - Not Found
- 409 - Conflict (duplicate email/username)
- 422 - Unprocessable Entity (validation errors)

**Server Errors (5xx):**

- 500 - Internal Server Error
- 503 - Service Unavailable

Example error response:

```json
{
  "error": {
    "status_code": 401,
    "message": "Invalid authentication token",
    "type": "client_error"
  }
}
```

## Security

### JWT Authentication

- **Algorithm**: RS256 (asymmetric encryption)
- **Token Lifetime**: 24 hours (configurable)
- **Private Key**: Used for signing tokens (keep secure!)
- **Public Key**: Used for verifying tokens

### Password Security

- Passwords are hashed using **bcrypt**
- Minimum password length: 8 characters
- Passwords are never stored in plain text or logged

### Authorization

- Todo endpoints are protected with JWT authentication
- Users can only access their own todos
- 403 Forbidden returned when accessing another user's resources

## Testing

### Run all tests

```bash
uv run pytest
```

### Run integration tests with testcontainers

```bash
uv run pytest tests/integration/ -v
```

### Run specific test file

```bash
uv run pytest tests/test_api.py -v
```

## Configuration

All configuration is managed through environment variables (see [.env.example](.env.example)):

**Application:**

- `APP_NAME` - Application name
- `DEBUG` - Enable debug mode and API docs
- `ENVIRONMENT` - Environment (development/production)

**Server:**

- `HOST` - Server host (default: 0.0.0.0)
- `PORT` - Server port (default: 8000)

**Database:**

- `DATABASE_URL` - PostgreSQL connection string
- `DB_POOL_SIZE` - Connection pool size
- `DB_ECHO` - Log SQL queries

**Logging:**

- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)
- `LOG_JSON` - Output logs as JSON for production (true/false)

See [LOGGING.md](LOGGING.md) for detailed logging documentation including:

- Structured log format and fields
- Request tracing with unique IDs
- Response time tracking
- Integration with ELK, Datadog, CloudWatch
- Query examples for log analysis

## Development

### Code Quality

Format and lint code:

```bash
uv run ruff check src/
uv run ruff format src/
```

Type checking:

```bash
uv run mypy src/
```

### Project Principles

Following clean code and functional programming principles:

- **Single Responsibility** - Each module has one clear purpose
- **Dependency Injection** - FastAPI's `Depends()` for loose coupling
- **Type Safety** - Full type hints with mypy strict mode
- **Separation of Concerns** - Models, schemas, routes, and business logic separated
- **Immutability** - Prefer immutable data structures and pure functions
- **DRY** - Reusable components (database sessions, logging, error handling)
- **Security First** - JWT auth, password hashing, input validation

## Production Deployment

### Environment Variables

- Set `DEBUG=false` to disable API docs
- Set `LOG_JSON=true` for structured logging
- Set `ENVIRONMENT=production`
- Use strong, unique database credentials

### Security Checklist

- [ ] Keep `private_key.pem` secure and never commit to version control
- [ ] Use environment-specific RSA keys for different environments
- [ ] Enable HTTPS/TLS in production
- [ ] Set secure CORS policies
- [ ] Use strong database passwords
- [ ] Regularly rotate JWT signing keys
- [ ] Monitor and rate-limit authentication attempts

## License

This project is provided as a template for building production-ready async REST APIs.
