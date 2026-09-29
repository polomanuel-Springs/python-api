import argparse
import asyncio
from concurrent.futures import ThreadPoolExecutor
from time import sleep

from app.db.session import SessionLocal
from app.models import Task
from app.repositories.projects import get_any


def prepare_thread(number: int) -> str:
    sleep(0.001)  # Simulate a delay before preparing the title.
    return f"Task {number}"


async def prepare_async(number: int) -> str:
    await asyncio.sleep(0.001)  # The same delay without blocking the program.
    return f"Task {number}"


def titles_with_threads(count: int) -> list[str]:
    with ThreadPoolExecutor(max_workers=20) as pool:
        return list(pool.map(prepare_thread, range(1, count + 1)))


async def titles_with_asyncio(count: int) -> list[str]:
    return list(await asyncio.gather(*(prepare_async(n) for n in range(1, count + 1))))


def main(project_id: int, count: int, mode: str) -> None:
    titles = (
        titles_with_threads(count)
        if mode == "threads"
        else asyncio.run(titles_with_asyncio(count))
    )

    with SessionLocal() as db:
        if get_any(db, project_id) is None:
            raise SystemExit("That project does not exist. Create one first.")
        db.add_all([Task(project_id=project_id, title=title) for title in titles])
        db.commit()
    print(f"Inserted {count} tasks using {mode} mode.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create many sample tasks")
    parser.add_argument("--project-id", type=int, required=True)
    parser.add_argument("--count", type=int, default=1000)
    parser.add_argument("--mode", choices=["threads", "async"], default="threads")
    args = parser.parse_args()
    main(args.project_id, args.count, args.mode)
