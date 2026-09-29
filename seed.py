import argparse

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import Priority, Project, Task, TaskStatus, User
from app.repositories import users


def seed(email: str, password: str) -> None:
    with SessionLocal() as db:
        if users.get_by_email(db, email) is not None:
            print("This user already exists; no data was added.")
            return
        user = User(email=email, hashed_password=hash_password(password))
        project = Project(name="Demo project", owner=user)
        project.tasks = [
            Task(
                title="Prepare presentation",
                status=TaskStatus.TODO,
                priority=Priority.HIGH,
            ),
            Task(
                title="Review API",
                status=TaskStatus.IN_PROGRESS,
                priority=Priority.MEDIUM,
            ),
        ]
        db.add(user)
        db.commit()
        print(f"Data created for {email}. Project: {project.name}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Insert sample data")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    arguments = parser.parse_args()
    seed(arguments.email.lower(), arguments.password)
