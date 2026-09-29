from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from app.api.deps import CurrentUser, DbSession
from app.repositories import projects
from app.schemas.project import ProjectCreate, ProjectOut, ProjectUpdate
from app.services.projects import require_project

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectOut])
def list_projects(
    db: DbSession,
    user: CurrentUser,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    return projects.list_for_user(db, user.id, limit, offset)


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(data: ProjectCreate, db: DbSession, user: CurrentUser):
    return projects.create(db, user.id, data.name)


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: int, db: DbSession, user: CurrentUser):
    return require_project(db, project_id, user.id)


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: int, data: ProjectUpdate, db: DbSession, user: CurrentUser
):
    project = require_project(db, project_id, user.id)
    if data.name is None:
        return project
    return projects.update(db, project, data.name)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, db: DbSession, user: CurrentUser) -> Response:
    projects.delete(db, require_project(db, project_id, user.id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
