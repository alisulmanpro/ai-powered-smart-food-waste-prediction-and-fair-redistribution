from fastapi import APIRouter
from sqlalchemy import text

from app.api.deps import DbSession

router = APIRouter(tags=["health"])


@router.get("/health")
def health(db: DbSession) -> dict:
    """Checks the API and the database connection."""
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "ok"}
