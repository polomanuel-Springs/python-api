from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.task import TaskOut


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)


class ProjectOut(BaseModel):
    id: int
    name: str
    owner_id: int
    created_at: datetime
    tasks: list[TaskOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}
