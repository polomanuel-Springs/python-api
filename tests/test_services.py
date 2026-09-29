import pytest

from app.models import Project, User
from app.schemas.auth import UserCreate
from app.services.auth import register
from app.services.errors import EmailAlreadyRegisteredError, NotAuthorizedError
from app.services.projects import require_project


def test_registration_rejects_duplicate_email(db_session) -> None:
    data = UserCreate(email="one@example.com", password="Password123!")
    register(db_session, data)
    with pytest.raises(EmailAlreadyRegisteredError):
        register(db_session, data)


def test_foreign_project_raises_not_authorized(db_session) -> None:
    first = User(email="first@example.com", hashed_password="sample")
    second = User(email="second@example.com", hashed_password="sample")
    project = Project(name="Private", owner=first)
    db_session.add_all([first, second, project])
    db_session.commit()
    with pytest.raises(NotAuthorizedError):
        require_project(db_session, project.id, second.id, reveal_forbidden=True)
