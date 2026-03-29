"""Add prompt_used and raw_response to agent_results

Revision ID: 003
Revises: 002
Create Date: 2026-03-29

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('agent_results', sa.Column('prompt_used', sa.Text(), nullable=True))
    op.add_column('agent_results', sa.Column('raw_response', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('agent_results', 'raw_response')
    op.drop_column('agent_results', 'prompt_used')
