"""Add kandidater, oppgave, innleveringsdato to reports

Revision ID: 004
Revises: 003
Create Date: 2026-03-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('reports', sa.Column('kandidater', sa.JSON(), nullable=True))
    op.add_column('reports', sa.Column('oppgave', sa.String(255), nullable=True))
    op.add_column('reports', sa.Column('innleveringsdato', sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column('reports', 'innleveringsdato')
    op.drop_column('reports', 'oppgave')
    op.drop_column('reports', 'kandidater')
