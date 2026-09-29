from sqlalchemy.orm import Session

from app.models.project import Project
from app.repositories import projects
from app.services.errors import NotAuthorizedError, ProjectNotFoundError


def require_project(
    db: Session, project_id: int, user_id: int, reveal_forbidden: bool = False
) -> Project:
    project = projects.get_any(db, project_id)
    if project is None:
        raise ProjectNotFoundError
    if project.owner_id != user_id:
        if reveal_forbidden:
            raise NotAuthorizedError
        raise ProjectNotFoundError
    return project
