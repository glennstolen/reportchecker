"""Initial migration

Revision ID: 001
Revises:
Create Date: 2024-01-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), nullable=True, server_default='lecturer'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_users_id', 'users', ['id'])
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # Reports table
    op.create_table(
        'reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('content_text', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('UPLOADED', 'PROCESSING', 'READY', 'ERROR', name='reportstatus'), nullable=True, server_default='UPLOADED'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_reports_id', 'reports', ['id'])

    # Agent configurations table
    op.create_table(
        'agent_configurations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('criteria', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('max_score', sa.Float(), nullable=True, server_default='10.0'),
        sa.Column('prompt_template', sa.Text(), nullable=True),
        sa.Column('is_template', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_agent_configurations_id', 'agent_configurations', ['id'])

    # Evaluations table
    op.create_table(
        'evaluations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('report_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'RUNNING', 'COMPLETED', 'ERROR', name='evaluationstatus'), nullable=True, server_default='PENDING'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_score', sa.Float(), nullable=True),
        sa.Column('max_possible_score', sa.Float(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['report_id'], ['reports.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_evaluations_id', 'evaluations', ['id'])

    # Agent results table
    op.create_table(
        'agent_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('evaluation_id', sa.Integer(), nullable=False),
        sa.Column('agent_config_id', sa.Integer(), nullable=False),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('max_score', sa.Float(), nullable=True),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'RUNNING', 'COMPLETED', 'ERROR', name='evaluationstatus', create_type=False), nullable=True, server_default='PENDING'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['evaluation_id'], ['evaluations.id']),
        sa.ForeignKeyConstraint(['agent_config_id'], ['agent_configurations.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_agent_results_id', 'agent_results', ['id'])


def downgrade() -> None:
    op.drop_table('agent_results')
    op.drop_table('evaluations')
    op.drop_table('agent_configurations')
    op.drop_table('reports')
    op.drop_table('users')
    op.execute('DROP TYPE IF EXISTS evaluationstatus')
    op.execute('DROP TYPE IF EXISTS reportstatus')
