"""Fix scoring: remove Vedleggssjekker, set max_score = percentage weight, drop default_enabled

Revision ID: 009
Revises: 008
Create Date: 2026-04-05
"""
from alembic import op
import sqlalchemy as sa


revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None

# Each agent's max_score now equals its percentage weight (sum = 100)
AGENT_WEIGHTS = {
    'Formalitetssjekker': 3.0,
    'Kildesjekker': 3.0,
    'Figur-, tabell- og ligningssjekker': 2.0,
    'Språksjekker': 2.0,
    'Sammendragssjekker': 2.0,
    'Innholdssjekker': 85.0,
    'Helhetsvurdering': 3.0,
}


def upgrade() -> None:
    conn = op.get_bind()

    # Delete Vedleggssjekker (and its results)
    conn.execute(sa.text("DELETE FROM agent_results WHERE agent_config_id IN (SELECT id FROM agent_configurations WHERE name = 'Vedleggssjekker')"))
    conn.execute(sa.text("DELETE FROM agent_configurations WHERE name = 'Vedleggssjekker'"))

    # Set max_score = percentage weight for each agent
    for name, weight in AGENT_WEIGHTS.items():
        conn.execute(
            sa.text("UPDATE agent_configurations SET max_score = :weight WHERE name = :name"),
            {'weight': weight, 'name': name}
        )

    # Drop default_enabled — all agents always run
    op.drop_column('agent_configurations', 'default_enabled')


def downgrade() -> None:
    conn = op.get_bind()
    op.add_column(
        'agent_configurations',
        sa.Column('default_enabled', sa.Boolean(), nullable=False, server_default='true')
    )
    # Restore original max_scores (from migration 006)
    original = {
        'Formalitetssjekker': 3.0,
        'Kildesjekker': 3.0,
        'Figur-, tabell- og ligningssjekker': 3.0,
        'Språksjekker': 2.0,
        'Sammendragssjekker': 2.0,
        'Innholdssjekker': 85.0,
        'Helhetsvurdering': 1.0,
    }
    for name, score in original.items():
        conn.execute(
            sa.text("UPDATE agent_configurations SET max_score = :score WHERE name = :name"),
            {'score': score, 'name': name}
        )
