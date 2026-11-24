"""Test setup: a separate `<db>_test` database on the same Postgres server.

Every test runs inside a transaction that is rolled back, so tests stay isolated.
"""

from collections.abc import Generator

import psycopg
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

import app.models  # noqa: F401
from app.core.config import settings
from app.core.security import create_verification_token, hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import User, UserRole


def _test_url() -> str:
    if settings.TEST_DATABASE_URL:
        return settings.TEST_DATABASE_URL
    url = make_url(settings.DATABASE_URL)
    return url.set(database=f"{url.database}_test").render_as_string(hide_password=False)


def _ensure_database(url_str: str) -> None:
    url = make_url(url_str)
    admin_dsn = url.set(drivername="postgresql", database="postgres").render_as_string(
        hide_password=False
    )
    with psycopg.connect(admin_dsn, autocommit=True) as conn:
        exists = conn.execute("SELECT 1 FROM pg_database WHERE datname = %s", (url.database,))
        if exists.fetchone() is None:
            conn.execute(f'CREATE DATABASE "{url.database}"')


@pytest.fixture(scope="session")
def engine():
    url = _test_url()
    _ensure_database(url)
    eng = create_engine(url)
    Base.metadata.drop_all(eng)
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture()
def db(engine) -> Generator[Session, None, None]:
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db: Session) -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------- helpers ----------

PASSWORD = "password123"


def make_user(db: Session, email: str, role: UserRole, name: str = "Test User") -> User:
    user = User(
        name=name,
        email=email,
        password_hash=hash_password(PASSWORD),
        role=role,
        email_verified=True,  # direct DB creation bypasses the email round-trip
    )
    db.add(user)
    db.commit()
    return user


def verify_email_for(client: TestClient, user_id: int) -> None:
    """Confirm a freshly registered user without sending a real email."""
    token = create_verification_token(user_id)
    resp = client.post("/api/v1/auth/verify-email", json={"token": token})
    assert resp.status_code == 200, resp.text


def auth_headers(client: TestClient, email: str, password: str = PASSWORD) -> dict[str, str]:
    resp = client.post("/api/v1/auth/login", data={"username": email, "password": password})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture()
def admin_headers(client: TestClient, db: Session) -> dict[str, str]:
    make_user(db, "admin@example.com", UserRole.admin, "Admin")
    return auth_headers(client, "admin@example.com")
