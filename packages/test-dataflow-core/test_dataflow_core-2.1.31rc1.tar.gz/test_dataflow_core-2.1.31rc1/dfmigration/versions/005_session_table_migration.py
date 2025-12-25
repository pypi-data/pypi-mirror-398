"""Add session lifecycle management columns and cleanup job

Revision ID: 005
Revises: 004
Create Date: 2025-11-13 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None

def upgrade():
    # Add new columns to SESSION table
    op.add_column('SESSION', sa.Column('last_seen', sa.DateTime(timezone=False), nullable=False, server_default=sa.text("(CURRENT_TIMESTAMP AT TIME ZONE 'UTC')")))
    op.add_column('SESSION', sa.Column('expires_at', sa.DateTime(timezone=False), nullable=False, server_default=sa.text("((CURRENT_TIMESTAMP AT TIME ZONE 'UTC') + INTERVAL '7 days')")))
    op.add_column('SESSION', sa.Column('revoked', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    
    # Create index on expires_at for efficient cleanup queries
    op.create_index('idx_session_expires_at', 'SESSION', ['expires_at'])
    op.create_index('idx_session_revoked', 'SESSION', ['revoked'])
    
    # Modify USER table password column to be nullable
    op.alter_column('USER', 'password', nullable=True)
    op.alter_column('ORGANIZATION_ONBOARDING', 'admin_designation', nullable=True)

    # Add 'expired' value to existing onboardingstatus enum
    op.execute("ALTER TYPE onboardingstatus ADD VALUE IF NOT EXISTS 'expired';")
    op.execute("ALTER TYPE onboarding_status ADD VALUE IF NOT EXISTS 'expired';")
    op.execute("ALTER TYPE baserolefield ADD VALUE IF NOT EXISTS 'ops';")
    op.execute("ALTER TYPE onboardingstatus ADD VALUE IF NOT EXISTS 'partial';")

def downgrade():
    
    # Revert USER table password column to not nullable
    op.alter_column('USER', 'password', nullable=False)
    
    # Drop indexes
    op.drop_index('idx_session_revoked', 'SESSION')
    op.drop_index('idx_session_expires_at', 'SESSION')
    
    # Remove columns from SESSION table
    op.drop_column('SESSION', 'revoked')
    op.drop_column('SESSION', 'expires_at')
    op.drop_column('SESSION', 'last_seen')
    
    # Note: Cannot remove enum value 'expired' in PostgreSQL, it would remain in the enum type
