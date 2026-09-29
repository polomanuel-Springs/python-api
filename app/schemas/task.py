from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.task import Priority, TaskStatus


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    status: TaskStatus = TaskStatus.TODO
    priority: Priority = Priority.MEDIUM
    due_date: date | None = None


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    status: TaskStatus | None = None
    priority: Priority | None = None
    due_date: date | None = None


class TaskOut(BaseModel):
    id: int
    title: str
    description: str | None
    status: TaskStatus
    priority: Priority
    due_date: date | None
    project_id: int
    created_at: datetime
    is_overdue: bool

    model_config = {"from_attributes": True}


class TaskSummary(BaseModel):
    todo: int
    in_progress: int
    done: int
    total: int
