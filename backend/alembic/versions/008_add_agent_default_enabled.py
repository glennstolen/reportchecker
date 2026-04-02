"""Add default_enabled field to agent_configurations

Revision ID: 008
Revises: 007
Create Date: 2026-04-02
"""
from alembic import op
import sqlalchemy as sa


revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add default_enabled column
    op.add_column(
        'agent_configurations',
        sa.Column('default_enabled', sa.Boolean(), nullable=False, server_default='true')
    )

    # Set Vedleggssjekker to default_enabled=False
    op.execute("""
        UPDATE agent_configurations
        SET default_enabled = false
        WHERE name = 'Vedleggssjekker'
    """)


def downgrade() -> None:
    op.drop_column('agent_configurations', 'default_enabled')
