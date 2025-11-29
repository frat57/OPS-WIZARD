"""create fraud_logs table

Revision ID: 0003_create_fraudlogs
Revises: 0002_create_core_tables
Create Date: 2025-11-29 16:50:00
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0003_create_fraudlogs'
down_revision = '0002_create_core_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'fraud_logs',
        sa.Column('id', sa.Text(), primary_key=True, nullable=False),
        sa.Column('transaction_id', sa.Text(), nullable=True),
        sa.Column('risk_score', sa.Float(), nullable=False),
        sa.Column('ai_reason', sa.Text(), nullable=True),
        sa.Column('suggested_action', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()')),
    )


def downgrade() -> None:
    op.drop_table('fraud_logs')
