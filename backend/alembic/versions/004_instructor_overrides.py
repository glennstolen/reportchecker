"""Add instructor override fields

Revision ID: 004
Revises: 003
Create Date: 2026-04-19
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('agent_results', sa.Column('instructor_score', sa.Float(), nullable=True))
    op.add_column('agent_results', sa.Column('instructor_comment', sa.Text(), nullable=True))
    op.add_column('evaluations', sa.Column('instructor_total_score', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('evaluations', 'instructor_total_score')
    op.drop_column('agent_results', 'instructor_comment')
    op.drop_column('agent_results', 'instructor_score')
