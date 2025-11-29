"""create core tables for fraud workflow

Revision ID: 0002_create_core_tables
Revises: 0001_create_events_table
Create Date: 2025-11-29 00:00:00
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0002_create_core_tables'
down_revision = '0001_create_events_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # users
    op.create_table(
        'users',
        sa.Column('id', sa.Text(), primary_key=True, nullable=False),
        sa.Column('email', sa.Text(), nullable=True, unique=True),
        sa.Column('name', sa.Text(), nullable=True),
        sa.Column('role', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=True),
    )

    # transactions
    op.create_table(
        'transactions',
        sa.Column('id', sa.Text(), primary_key=True, nullable=False),
        sa.Column('user_id', sa.Text(), nullable=True),
        sa.Column('amount', sa.Numeric(18, 4), nullable=True),
        sa.Column('currency', sa.Text(), nullable=True),
        sa.Column('status', sa.Text(), nullable=True),
        sa.Column('raw_payload', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()')),
    )
    op.create_index('ix_transactions_user_id', 'transactions', ['user_id'])

    # alerts
    op.create_table(
        'alerts',
        sa.Column('id', sa.Text(), primary_key=True, nullable=False),
        sa.Column('transaction_id', sa.Text(), nullable=True),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('reasoning', sa.Text(), nullable=True),
        sa.Column('suggested_action', sa.Text(), nullable=True),
        sa.Column('explanation', sa.JSON(), nullable=True),
        sa.Column('status', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()')),
    )
    op.create_index('ix_alerts_transaction_id', 'alerts', ['transaction_id'])
    op.create_index('ix_alerts_status', 'alerts', ['status'])

    # investigations
    op.create_table(
        'investigations',
        sa.Column('id', sa.Text(), primary_key=True, nullable=False),
        sa.Column('alert_id', sa.Text(), nullable=False),
        sa.Column('assigned_to', sa.Text(), nullable=True),
        sa.Column('status', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()')),
        sa.Column('closed_at', sa.TIMESTAMP(timezone=True), nullable=True),
    )

    op.create_index('ix_investigations_assigned_to', 'investigations', ['assigned_to'])
    op.create_index('ix_investigations_status', 'investigations', ['status'])

    # decisions
    op.create_table(
        'decisions',
        sa.Column('id', sa.Text(), primary_key=True, nullable=False),
        sa.Column('investigation_id', sa.Text(), nullable=False),
        sa.Column('actor', sa.Text(), nullable=True),
        sa.Column('action_taken', sa.Text(), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()')),
    )

    # integrations
    op.create_table(
        'integrations',
        sa.Column('id', sa.Text(), primary_key=True, nullable=False),
        sa.Column('name', sa.Text(), nullable=True),
        sa.Column('type', sa.Text(), nullable=True),
        sa.Column('config', sa.JSON(), nullable=True),
        sa.Column('enabled', sa.Boolean(), server_default=sa.text('true')),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()')),
    )

    # audit_logs
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Text(), primary_key=True, nullable=False),
        sa.Column('entity_type', sa.Text(), nullable=True),
        sa.Column('entity_id', sa.Text(), nullable=True),
        sa.Column('actor', sa.Text(), nullable=True),
        sa.Column('operation', sa.Text(), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()')),
    )


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('integrations')
    op.drop_table('decisions')
    op.drop_table('investigations')
    op.drop_index('ix_alerts_status', table_name='alerts')
    op.drop_index('ix_alerts_transaction_id', table_name='alerts')
    op.drop_table('alerts')
    op.drop_index('ix_transactions_user_id', table_name='transactions')
    op.drop_table('transactions')
    op.drop_table('users')
