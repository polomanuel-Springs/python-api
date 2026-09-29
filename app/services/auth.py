import logging

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories import users
from app.schemas.auth import LoginRequest, UserCreate
from app.services.errors import EmailAlreadyRegisteredError, InvalidCredentialsError

logger = logging.getLogger(__name__)


def register(db: Session, data: UserCreate) -> User:
    email = data.email.lower()
    if users.get_by_email(db, email) is not None:
        raise EmailAlreadyRegisteredError
    try:
        user = users.create(db, email, hash_password(data.password))
    except IntegrityError as error:
        db.rollback()
        raise EmailAlreadyRegisteredError from error
    logger.info("user_registered user_id=%s", user.id)
    return user


def login(db: Session, data: LoginRequest) -> str:
    user = users.get_by_email(db, data.email.lower())
    if user is None or not verify_password(data.password, user.hashed_password):
        raise InvalidCredentialsError
    return create_access_token(user.id)
