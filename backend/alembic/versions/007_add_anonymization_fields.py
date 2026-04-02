"""Add anonymization fields to reports

Revision ID: 007
Revises: 006
Create Date: 2026-04-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '007'
down_revision: Union[str, None] = '006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('reports', sa.Column('anonymized_file_path', sa.String(500), nullable=True))
    op.add_column('reports', sa.Column('mapping_file_path', sa.String(500), nullable=True))
    op.add_column('reports', sa.Column('candidate_mappings', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('reports', 'candidate_mappings')
    op.drop_column('reports', 'mapping_file_path')
    op.drop_column('reports', 'anonymized_file_path')
