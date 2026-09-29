from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.project import Project


def get_any(db: Session, project_id: int) -> Project | None:
    return db.scalar(
        select(Project)
        .options(selectinload(Project.tasks))
        .where(Project.id == project_id)
    )


def list_for_user(db: Session, user_id: int, limit: int, offset: int) -> list[Project]:
    query = (
        select(Project)
        .options(selectinload(Project.tasks))
        .where(Project.owner_id == user_id)
        .order_by(Project.id)
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(query).all())


def create(db: Session, user_id: int, name: str) -> Project:
    project = Project(owner_id=user_id, name=name)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def update(db: Session, project: Project, name: str) -> Project:
    project.name = name
    db.commit()
    db.refresh(project)
    return project


def delete(db: Session, project: Project) -> None:
    db.delete(project)
    db.commit()
