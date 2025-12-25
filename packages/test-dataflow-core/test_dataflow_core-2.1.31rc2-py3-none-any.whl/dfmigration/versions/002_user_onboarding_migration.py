"""Add system enhancements - enums, columns, and settings table

Revision ID: 002
Revises: 001
Create Date: 2025-11-08 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None

def upgrade():
    # Add enum values
    op.execute("ALTER TYPE baserolefield ADD VALUE IF NOT EXISTS 'ops'")
    op.execute("ALTER TYPE onboardingstatus ADD VALUE IF NOT EXISTS 'partial'")
    
    
    # Add column to USER table
    op.add_column('USER', sa.Column('is_super_admin', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    
    # Add columns to ORGANIZATION table
    op.add_column('ORGANIZATION', sa.Column('allow_auto_user_onboarding', sa.Boolean(), nullable=False, server_default=sa.text('true')))
    
    # Add columns to ORGANIZATION_ONBOARDING table
    op.add_column('ORGANIZATION_ONBOARDING', sa.Column('organization_website', sa.String(), nullable=True))
    op.add_column('ORGANIZATION_ONBOARDING', sa.Column('admin_phone', sa.String(255), nullable=True))
    
    # Modify admin_password column to allow NULL
    op.alter_column('ORGANIZATION_ONBOARDING', 'admin_password', nullable=True)
    
    # Create DATAFLOW_SETTING table
    op.create_table(
        'DATAFLOW_SETTING',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('allow_auto_org_onboarding', sa.Boolean(), nullable=False, server_default=sa.text('true'))
    )
    
    # Insert default row
    op.execute(
        "INSERT INTO \"DATAFLOW_SETTING\" (allow_auto_org_onboarding) "
        "SELECT TRUE WHERE NOT EXISTS (SELECT 1 FROM \"DATAFLOW_SETTING\")"
    )

def downgrade():
    # Drop DATAFLOW_SETTING table
    op.drop_table('DATAFLOW_SETTING')
    
    # Remove columns from ORGANIZATION_ONBOARDING
    op.alter_column('ORGANIZATION_ONBOARDING', 'admin_password', nullable=False)
    op.drop_column('ORGANIZATION_ONBOARDING', 'admin_phone')
    op.drop_column('ORGANIZATION_ONBOARDING', 'organization_website')
    
    # Remove columns from ORGANIZATION
    op.drop_column('ORGANIZATION', 'allow_auto_user_onboarding')
    
    # Remove column from USER
    op.drop_column('USER', 'is_super_admin')
    
    # Note: Cannot easily remove enum values in PostgreSQL
    # They would need to be handled manually if required