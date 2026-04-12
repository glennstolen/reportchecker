"""Add is_active to users and make name nullable

Revision ID: 002
Revises: 001
Create Date: 2026-04-12
"""
import os
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Make name nullable (not required for magic-link auth)
    op.alter_column("users", "name", nullable=True)

    # Add is_active column
    op.add_column(
        "users",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
    )

    # Seed admin user from ADMIN_EMAIL env var (idempotent)
    admin_email = os.environ.get("ADMIN_EMAIL", "")
    if admin_email:
        conn = op.get_bind()
        existing = conn.execute(
            sa.text("SELECT id FROM users WHERE email = :email"),
            {"email": admin_email},
        ).fetchone()
        if not existing:
            conn.execute(
                sa.text(
                    "INSERT INTO users (email, is_active) VALUES (:email, true)"
                ),
                {"email": admin_email},
            )
            print(f"Admin-bruker opprettet: {admin_email}")


def downgrade() -> None:
    op.drop_column("users", "is_active")
    op.alter_column("users", "name", nullable=False)
