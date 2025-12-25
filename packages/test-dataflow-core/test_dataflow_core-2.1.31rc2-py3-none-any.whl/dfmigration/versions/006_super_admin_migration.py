"""Add active column to organization table

Revision ID: 006
Revises: 005
Create Date: 2025-11-18 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None

def upgrade():
    # Add active column to ORGANIZATION table
    op.add_column('ORGANIZATION', sa.Column('active', sa.Boolean(), nullable=False, server_default=sa.text('true')))
    
    # Create index on active column for efficient filtering
    op.create_index('idx_organization_active', 'ORGANIZATION', ['active'])

def downgrade():
    # Drop index
    op.drop_index('idx_organization_active', 'ORGANIZATION')
    
    # Remove active column from ORGANIZATION table
    op.drop_column('ORGANIZATION', 'active')