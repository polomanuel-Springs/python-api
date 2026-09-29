from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import read_access_token
from app.db.session import get_db
from app.models.user import User
from app.repositories.users import get_by_id

DbSession = Annotated[Session, Depends(get_db)]
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: DbSession,
) -> User:
    user_id = read_access_token(credentials.credentials) if credentials else None
    user = get_by_id(db, user_id) if user_id is not None else None
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
