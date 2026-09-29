import asyncio
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, DbSession
from app.models.task import Priority, TaskStatus
from app.repositories import tasks
from app.repositories.tasks import PaginationParams
from app.schemas.task import TaskCreate, TaskOut, TaskSummary, TaskUpdate
from app.services import tasks as task_service
from app.services.projects import require_project

router = APIRouter(tags=["tasks"])


@router.get("/projects/{project_id}/tasks", response_model=list[TaskOut])
def list_tasks(
    project_id: int,
    db: DbSession,
    user: CurrentUser,
    status_filter: Annotated[TaskStatus | None, Query(alias="status")] = None,
    priority: Priority | None = None,
    sort_by_due_date: bool = False,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    require_project(db, project_id, user.id)
    return tasks.list_for_project(
        db,
        project_id,
        PaginationParams(limit=limit, offset=offset),
        status_filter,
        priority,
        sort_by_due_date,
    )


@router.post(
    "/projects/{project_id}/tasks",
    response_model=TaskOut,
    status_code=status.HTTP_201_CREATED,
)
def create_task(project_id: int, data: TaskCreate, db: DbSession, user: CurrentUser):
    return task_service.create_task(db, project_id, user.id, data.model_dump())


def count_in_new_session(bind: object, user_id: int, task_status: TaskStatus) -> int:
    with Session(bind=bind) as session:  # type: ignore[arg-type]
        return tasks.count_for_user(session, user_id, task_status)


@router.get("/tasks/summary", response_model=TaskSummary)
async def task_summary(db: DbSession, user: CurrentUser) -> TaskSummary:
    bind = db.get_bind()
    statuses = list(TaskStatus)
    # Each count uses its own session; sessions are not shared between threads.
    counts = await asyncio.gather(
        *(
            asyncio.to_thread(count_in_new_session, bind, user.id, item)
            for item in statuses
        )
    )
    by_status = dict(zip(statuses, counts, strict=True))
    return TaskSummary(
        todo=by_status[TaskStatus.TODO],
        in_progress=by_status[TaskStatus.IN_PROGRESS],
        done=by_status[TaskStatus.DONE],
        total=sum(counts),
    )


@router.patch("/tasks/{task_id}", response_model=TaskOut)
def update_task(task_id: int, data: TaskUpdate, db: DbSession, user: CurrentUser):
    task = task_service.require_task(db, task_id, user.id)
    return tasks.update(db, task, data.model_dump(exclude_unset=True))


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: DbSession, user: CurrentUser) -> Response:
    tasks.delete(db, task_service.require_task(db, task_id, user.id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/tasks/{task_id}/remind", status_code=status.HTTP_202_ACCEPTED)
def remind_task(
    task_id: int, background_tasks: BackgroundTasks, db: DbSession, user: CurrentUser
) -> dict[str, str]:
    task = task_service.require_task(db, task_id, user.id)
    background_tasks.add_task(task_service.send_reminder, task.id, user.id)
    return {"message": "Reminder scheduled."}
