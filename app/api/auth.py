from fastapi import APIRouter, status

from app.api.deps import DbSession
from app.schemas.auth import LoginRequest, TokenOut, UserCreate, UserOut
from app.services import auth

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, db: DbSession):
    return auth.register(db, data)


@router.post("/login", response_model=TokenOut)
def login(data: LoginRequest, db: DbSession) -> TokenOut:
    return TokenOut(access_token=auth.login(db, data))
