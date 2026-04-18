"""Add candidate_registry table

Revision ID: 002
Revises: 001
Create Date: 2026-04-18
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'candidate_registry',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name_normalized', sa.String(500), nullable=False),
        sa.Column('candidate_number', sa.String(6), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('name_normalized'),
        sa.UniqueConstraint('candidate_number'),
    )
    op.create_index('ix_candidate_registry_name_normalized', 'candidate_registry', ['name_normalized'])


def downgrade() -> None:
    op.drop_index('ix_candidate_registry_name_normalized', 'candidate_registry')
    op.drop_table('candidate_registry')
