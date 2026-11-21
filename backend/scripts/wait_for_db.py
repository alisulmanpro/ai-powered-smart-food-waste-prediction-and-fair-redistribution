"""Block until PostgreSQL accepts connections (used by the container entrypoints)."""

import sys
import time

import psycopg

from app.core.config import settings


def main(timeout_seconds: int = 60) -> None:
    dsn = settings.DATABASE_URL.replace("postgresql+psycopg://", "postgresql://")
    deadline = time.monotonic() + timeout_seconds
    while True:
        try:
            with psycopg.connect(dsn, connect_timeout=3):
                print("Database is ready.")
                return
        except psycopg.OperationalError as exc:
            if time.monotonic() > deadline:
                print(f"Database not reachable after {timeout_seconds}s: {exc}", file=sys.stderr)
                sys.exit(1)
            print("Waiting for database...")
            time.sleep(2)


if __name__ == "__main__":
    main()
