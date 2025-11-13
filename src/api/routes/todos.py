"""Protected Todo API routes - users can only CRUD their own todos."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.auth import CurrentUser
from api.core.database import get_db
from api.core.exceptions import ForbiddenError, NotFoundError
from api.core.logging import get_logger
from api.models.todo import Todo
from api.schemas.todo import TodoCreate, TodoListResponse, TodoResponse, TodoUpdate

logger = get_logger(__name__)

router = APIRouter(prefix="/todos", tags=["todos"])


@router.post(
    "",
    response_model=TodoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new todo",
)
async def create_todo(
    todo_data: TodoCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Todo:
    """Create a new todo for the authenticated user."""
    logger.info(
        "creating_todo",
        user_id=current_user.id,
        title=todo_data.title,
    )

    todo = Todo(
        title=todo_data.title,
        description=todo_data.description,
        priority=todo_data.priority.value,
        user_id=current_user.id,
    )

    db.add(todo)
    await db.commit()
    await db.refresh(todo)

    logger.info("todo_created", todo_id=todo.id, user_id=current_user.id)
    return todo


@router.get(
    "",
    response_model=TodoListResponse,
    summary="List all todos for current user",
)
async def list_todos(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
    completed: Annotated[bool | None, Query()] = None,
) -> TodoListResponse:
    """Get paginated list of todos for the authenticated user."""
    offset = (page - 1) * page_size

    # Build query
    query = select(Todo).where(Todo.user_id == current_user.id)

    # Filter by completion status if specified
    if completed is not None:
        query = query.where(Todo.is_completed == completed)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # Get paginated todos
    query = query.offset(offset).limit(page_size).order_by(Todo.created_at.desc())
    result = await db.execute(query)
    todos = result.scalars().all()

    logger.info(
        "todos_listed",
        user_id=current_user.id,
        total=total,
        page=page,
        returned=len(todos),
    )

    return TodoListResponse(
        todos=list(todos),
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{todo_id}",
    response_model=TodoResponse,
    summary="Get todo by ID",
)
async def get_todo(
    todo_id: Annotated[int, Path(ge=1)],
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Todo:
    """Get a specific todo by ID (only if owned by current user)."""
    result = await db.execute(select(Todo).where(Todo.id == todo_id))
    todo = result.scalar_one_or_none()

    if not todo:
        raise NotFoundError(f"Todo with ID {todo_id} not found")

    # Ensure todo belongs to current user
    if todo.user_id != current_user.id:
        raise ForbiddenError("You don't have permission to access this todo")

    logger.info("todo_retrieved", todo_id=todo.id, user_id=current_user.id)
    return todo


@router.patch(
    "/{todo_id}",
    response_model=TodoResponse,
    summary="Update todo",
)
async def update_todo(
    todo_id: Annotated[int, Path(ge=1)],
    todo_data: TodoUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Todo:
    """Update a todo (only if owned by current user)."""
    result = await db.execute(select(Todo).where(Todo.id == todo_id))
    todo = result.scalar_one_or_none()

    if not todo:
        raise NotFoundError(f"Todo with ID {todo_id} not found")

    # Ensure todo belongs to current user
    if todo.user_id != current_user.id:
        raise ForbiddenError("You don't have permission to modify this todo")

    # Update only provided fields
    update_data = todo_data.model_dump(exclude_unset=True)
    if "priority" in update_data and update_data["priority"] is not None:
        update_data["priority"] = update_data["priority"].value

    for field, value in update_data.items():
        setattr(todo, field, value)

    await db.commit()
    await db.refresh(todo)

    logger.info(
        "todo_updated",
        todo_id=todo.id,
        user_id=current_user.id,
        updated_fields=list(update_data.keys()),
    )
    return todo


@router.delete(
    "/{todo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete todo",
)
async def delete_todo(
    todo_id: Annotated[int, Path(ge=1)],
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete a todo (only if owned by current user)."""
    result = await db.execute(select(Todo).where(Todo.id == todo_id))
    todo = result.scalar_one_or_none()

    if not todo:
        raise NotFoundError(f"Todo with ID {todo_id} not found")

    # Ensure todo belongs to current user
    if todo.user_id != current_user.id:
        raise ForbiddenError("You don't have permission to delete this todo")

    await db.delete(todo)
    await db.commit()

    logger.info("todo_deleted", todo_id=todo_id, user_id=current_user.id)
