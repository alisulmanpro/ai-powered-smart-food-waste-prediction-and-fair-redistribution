"""add email_verified to users

Revision ID: f7e2a9c41d08
Revises: 6ce14b325bc6
Create Date: 2026-11-24 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'f7e2a9c41d08'
down_revision: Union[str, None] = '6ce14b325bc6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='false'),
    )
    # Accounts created before email verification existed are grandfathered in
    # so existing users are not locked out; new registrations must verify.
    op.execute("UPDATE users SET email_verified = true")


def downgrade() -> None:
    op.drop_column('users', 'email_verified')
