from sqlalchemy.orm import Session

from app.models import AuditLog


def log_action(
    db: Session,
    user_id: int | None,
    action: str,
    entity: str,
    entity_id: int | None = None,
    details: dict | None = None,
) -> None:
    """Add an audit row to the current transaction (committed together with the change)."""
    db.add(
        AuditLog(
            user_id=user_id, action=action, entity=entity, entity_id=entity_id, details=details
        )
    )
