from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.project import Project
from app.models.task import Priority, Task, TaskStatus


@dataclass(frozen=True)
class PaginationParams:
    limit: int = 20
    offset: int = 0


def get_any(db: Session, task_id: int) -> Task | None:
    return db.scalar(
        select(Task).options(selectinload(Task.project)).where(Task.id == task_id)
    )


def list_for_project(
    db: Session,
    project_id: int,
    pagination: PaginationParams,
    status: TaskStatus | None = None,
    priority: Priority | None = None,
    sort_by_due_date: bool = False,
) -> list[Task]:
    query = select(Task).where(Task.project_id == project_id)
    if status is not None:
        query = query.where(Task.status == status)
    if priority is not None:
        query = query.where(Task.priority == priority)
    order = Task.due_date.asc().nullslast() if sort_by_due_date else Task.id.asc()
    return list(
        db.scalars(
            query.order_by(order).limit(pagination.limit).offset(pagination.offset)
        ).all()
    )


def list_for_user(db: Session, user_id: int) -> list[Task]:
    """Get tasks from all projects owned by one user."""
    query = (
        select(Task)
        .join(Project)
        .options(selectinload(Task.project))
        .where(Project.owner_id == user_id)
        .order_by(Task.id)
    )
    return list(db.scalars(query).all())


def count_for_user(db: Session, user_id: int, status: TaskStatus) -> int:
    query = (
        select(func.count(Task.id))
        .join(Project)
        .where(Project.owner_id == user_id, Task.status == status)
    )
    return int(db.scalar(query) or 0)


def create(db: Session, project_id: int, values: dict[str, object]) -> Task:
    task = Task(project_id=project_id, **values)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def update(db: Session, task: Task, values: dict[str, object]) -> Task:
    for field, value in values.items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


def delete(db: Session, task: Task) -> None:
    db.delete(task)
    db.commit()
