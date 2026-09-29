import logging

from sqlalchemy.orm import Session

from app.models.task import Task
from app.repositories import tasks
from app.services.errors import TaskNotFoundError
from app.services.projects import require_project

logger = logging.getLogger(__name__)


def create_task(
    db: Session, project_id: int, user_id: int, values: dict[str, object]
) -> Task:
    require_project(db, project_id, user_id, reveal_forbidden=True)
    task = tasks.create(db, project_id, values)
    logger.info("task_created task_id=%s project_id=%s", task.id, project_id)
    return task


def require_task(db: Session, task_id: int, user_id: int) -> Task:
    task = tasks.get_any(db, task_id)
    if task is None or task.project.owner_id != user_id:
        raise TaskNotFoundError
    return task


def send_reminder(task_id: int, user_id: int) -> None:
    """Log the reminder without sending an email."""
    logger.info("reminder_sent task_id=%s user_id=%s", task_id, user_id)
