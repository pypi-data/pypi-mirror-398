"""add environment job table

Revision ID: 010
Revises: 009
Create Date: 2025-12-13

"""
from alembic import op

import sqlalchemy as sa
# revision identifiers, used by Alembic.
revision = '010'
down_revision = '009' 
branch_labels = None
depends_on = None


def upgrade():
    # Create ENVIRONMENT_JOB table
    op.create_table(
        'ENVIRONMENT_JOB',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('env_id', sa.Integer(), nullable=False),
        sa.Column('job_name', sa.String(), nullable=False),
        sa.Column('operation_type', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['env_id'], ['ENVIRONMENT.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for better query performance
    op.create_index('ix_environment_job_job_name', 'ENVIRONMENT_JOB', ['job_name'], unique=True)
    op.create_index('ix_environment_job_env_id', 'ENVIRONMENT_JOB', ['env_id'], unique=False)


def downgrade():
    # Drop indexes
    op.drop_index('ix_environment_job_env_id', table_name='ENVIRONMENT_JOB')
    op.drop_index('ix_environment_job_job_name', table_name='ENVIRONMENT_JOB')
    
    # Drop table
    op.drop_table('ENVIRONMENT_JOB')
