from fastapi.testclient import TestClient

from app.services import tasks as task_service


def authorized(client: TestClient, email: str = "one@example.com") -> dict[str, str]:
    registered = client.post(
        "/auth/register", json={"email": email, "password": "Password123!"}
    )
    assert registered.status_code == 201
    token = client.post(
        "/auth/login", json={"email": email, "password": "Password123!"}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def create_project(client: TestClient, headers: dict[str, str]) -> int:
    response = client.post("/projects", json={"name": "University"}, headers=headers)
    assert response.status_code == 201
    return response.json()["id"]


def create_task(
    client: TestClient, headers: dict[str, str], project_id: int, **values
) -> int:
    response = client.post(
        f"/projects/{project_id}/tasks",
        json={"title": "Study", **values},
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_health_and_auth(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/docs").status_code == 200
    assert (
        client.post(
            "/auth/register", json={"email": "bad", "password": "short"}
        ).status_code
        == 422
    )
    headers = authorized(client)
    assert (
        client.post(
            "/auth/register",
            json={"email": "one@example.com", "password": "Password123!"},
        ).status_code
        == 409
    )
    assert (
        client.post(
            "/auth/login", json={"email": "one@example.com", "password": "wrong"}
        ).status_code
        == 401
    )
    assert client.get("/projects").status_code == 401
    assert client.get("/projects", headers=headers).json() == []


def test_project_create_list_update_get_delete(client: TestClient) -> None:
    headers = authorized(client)
    project_id = create_project(client, headers)
    assert client.get("/projects", headers=headers).json()[0]["name"] == "University"
    assert client.get(f"/projects/{project_id}", headers=headers).json()["tasks"] == []
    changed = client.patch(
        f"/projects/{project_id}", json={"name": "Work"}, headers=headers
    )
    assert changed.json()["name"] == "Work"
    assert client.delete(f"/projects/{project_id}", headers=headers).status_code == 204
    assert client.get(f"/projects/{project_id}", headers=headers).status_code == 404


def test_project_failure_paths(client: TestClient) -> None:
    headers = authorized(client)
    assert (
        client.post("/projects", json={"name": ""}, headers=headers).status_code == 422
    )
    assert client.get("/projects?limit=0", headers=headers).status_code == 422
    assert (
        client.patch(
            "/projects/999", json={"name": "Other"}, headers=headers
        ).status_code
        == 404
    )
    assert client.delete("/projects/999", headers=headers).status_code == 404
    project_id = create_project(client, headers)
    other_headers = authorized(client, "other@example.com")
    assert (
        client.get(f"/projects/{project_id}", headers=other_headers).status_code == 404
    )


def test_tasks_crud_filters_pagination_and_summary(client: TestClient) -> None:
    headers = authorized(client)
    project_id = create_project(client, headers)
    first = create_task(
        client, headers, project_id, priority="high", due_date="2030-01-01"
    )
    create_task(client, headers, project_id, status="done", priority="low")
    filtered = client.get(
        f"/projects/{project_id}/tasks?status=todo&priority=high&sort_by_due_date=true&limit=1&offset=0",
        headers=headers,
    )
    assert [task["id"] for task in filtered.json()] == [first]
    page_two = client.get(
        f"/projects/{project_id}/tasks?limit=1&offset=1", headers=headers
    )
    assert len(page_two.json()) == 1
    summary = client.get("/tasks/summary", headers=headers)
    assert summary.status_code == 200
    assert summary.json() == {"todo": 1, "in_progress": 0, "done": 1, "total": 2}
    changed = client.patch(
        f"/tasks/{first}", json={"status": "in_progress"}, headers=headers
    )
    assert changed.json()["status"] == "in_progress"
    assert client.delete(f"/tasks/{first}", headers=headers).status_code == 204
    assert (
        client.patch(
            f"/tasks/{first}", json={"title": "Other"}, headers=headers
        ).status_code
        == 404
    )


def test_task_failure_paths_and_ownership(client: TestClient) -> None:
    headers = authorized(client)
    project_id = create_project(client, headers)
    task_id = create_task(client, headers, project_id)
    other_headers = authorized(client, "other@example.com")
    assert (
        client.get(f"/projects/{project_id}/tasks", headers=other_headers).status_code
        == 404
    )
    assert (
        client.post(
            f"/projects/{project_id}/tasks",
            json={"title": "Unauthorized task"},
            headers=other_headers,
        ).status_code
        == 403
    )
    assert (
        client.post(
            f"/projects/{project_id}/tasks", json={"title": ""}, headers=headers
        ).status_code
        == 422
    )
    assert (
        client.get(f"/projects/{project_id}/tasks?limit=0", headers=headers).status_code
        == 422
    )
    assert (
        client.patch(
            f"/tasks/{task_id}", json={"title": "X"}, headers=other_headers
        ).status_code
        == 404
    )
    assert (
        client.patch(
            f"/tasks/{task_id}", json={"status": "unknown"}, headers=headers
        ).status_code
        == 422
    )
    assert client.delete(f"/tasks/{task_id}", headers=other_headers).status_code == 404
    assert (
        client.post(f"/tasks/{task_id}/remind", headers=other_headers).status_code
        == 404
    )
    assert client.get("/tasks/summary").status_code == 401


def test_tasks_sort_by_due_date(client: TestClient) -> None:
    headers = authorized(client)
    project_id = create_project(client, headers)
    later = create_task(client, headers, project_id, due_date="2030-01-01")
    earlier = create_task(client, headers, project_id, due_date="2028-01-01")
    response = client.get(
        f"/projects/{project_id}/tasks?sort_by_due_date=true", headers=headers
    )
    assert [item["id"] for item in response.json()] == [earlier, later]


def test_reminder_uses_background_job(client: TestClient, monkeypatch) -> None:
    headers = authorized(client)
    task_id = create_task(client, headers, create_project(client, headers))
    calls: list[tuple[int, int]] = []
    monkeypatch.setattr(
        task_service, "send_reminder", lambda task, user: calls.append((task, user))
    )
    response = client.post(f"/tasks/{task_id}/remind", headers=headers)
    assert response.status_code == 202
    assert calls and calls[0][0] == task_id
