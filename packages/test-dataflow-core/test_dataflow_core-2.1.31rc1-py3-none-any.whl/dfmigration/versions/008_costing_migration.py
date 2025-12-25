"""Add soft delete and update constraints

Revision ID: 008
Revises: 007
Create Date: 2025-12-03 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import DateTime, Index, UniqueConstraint

# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None

def upgrade():
    #ORGANIATION table changes
    op.add_column(
        "ORGANIZATION",
        sa.Column("subscription_id", sa.Integer(), sa.ForeignKey("SUBSCRIPTION.id"), nullable=True)
    )

    op.add_column(
        "ORGANIZATION",
        sa.Column("stripe_customer_id", sa.String(), nullable=True)
    )

    op.add_column(
        "ORGANIZATION",
        sa.Column("credits_balance", sa.Numeric(10, 2), nullable=False, server_default="0")
    )


    # CONNECTION table changes
    # Add deleted_at column
    op.add_column('CONNECTION', sa.Column('deleted_at', DateTime(timezone=True), nullable=True))
    
    # Drop old unique constraint
    op.drop_constraint('uq_active_conn_with_runtime_slug', 'CONNECTION', type_='unique')
    
    # Create new unique index with postgresql_where clause
    op.execute("""
        CREATE UNIQUE INDEX uq_active_connection_slug 
        ON "CONNECTION" (conn_id, created_by, org_id, runtime, slug) 
        WHERE deleted_at IS NULL
    """)
    
    # ENVIRONMENT table changes
    # Add deleted_at column
    op.add_column('ENVIRONMENT', sa.Column('deleted_at', DateTime, nullable=True))

    op.drop_constraint(
        "_env_short_name_org_uc",
        "ENVIRONMENT",
        type_="unique",
        if_exists=True  # Alembic supports this in modern versions
    )

    
    # Create unique index for active environments
    op.execute("""
        CREATE UNIQUE INDEX uq_active_env_short_name 
        ON "ENVIRONMENT" (created_by, org_id, short_name) 
        WHERE deleted_at IS NULL
    """)
    
    # ORGANIZATION_USER table changes
    # Drop existing foreign key constraint
    op.drop_constraint('ORGANIZATION_USER_active_server_id_fkey', 'ORGANIZATION_USER', type_='foreignkey')
    
    # Add new foreign key constraint pointing to SERVER_CONFIG
    op.create_foreign_key(
        'ORGANIZATION_USER_active_server_id_fkey',
        'ORGANIZATION_USER',
        'SERVER_CONFIG',
        ['active_server_id'],
        ['id'],
        ondelete='SET NULL'
    )

    op.add_column(
        "ORGANIZATION_USER",
        sa.Column("used_cost", sa.JSON(), nullable=True)
    )
    
    # ROLE_SERVER table changes
    # Drop existing unique constraint
    op.drop_constraint('_role_server_uc', 'ROLE_SERVER', type_='unique')
    
    # Drop old foreign key and column
    op.drop_constraint('ROLE_SERVER_custom_server_id_fkey', 'ROLE_SERVER', type_='foreignkey')
    
    # Add new server_id column with foreign key
    # Step 1: Add new column as nullable
    op.add_column(
        "ROLE_SERVER",
        sa.Column("server_id", sa.Integer(), nullable=True)
    )
    # Step 2: Delete ALL invalid rows (custom_server_id > 3)
    op.execute("""
        DELETE FROM "ROLE_SERVER"
        WHERE custom_server_id > (SELECT MAX(id) FROM "SERVER_CONFIG");
    """)
    # Step 3: Copy remaining valid values
    op.execute("""
        UPDATE "ROLE_SERVER"
        SET server_id = custom_server_id;
    """)
    # Step 4: Make NOT NULL
    op.alter_column(
        "ROLE_SERVER",
        "server_id",
        nullable=False
    )
    op.drop_column('ROLE_SERVER', 'custom_server_id')

    op.create_foreign_key(
        'role_server_server_id_fkey',
        'ROLE_SERVER',
        'SERVER_CONFIG',
        ['server_id'],
        ['id'],
        ondelete='CASCADE'
    )
    
    # Create new unique constraint
    op.create_unique_constraint('_role_server_uc', 'ROLE_SERVER', ['role_id', 'server_id'])
    
    # VARIABLE table changes
    # Add deleted_at column
    op.add_column('VARIABLE', sa.Column('deleted_at', DateTime, nullable=True))
    
    # Drop old unique constraint
    op.drop_constraint('unique_key', 'VARIABLE', type_='unique')
    
    # Create new unique index with postgresql_where clause
    op.execute("""
        CREATE UNIQUE INDEX uq_active_secret_key 
        ON "VARIABLE" (key, created_by, org_id, runtime, slug) 
        WHERE deleted_at IS NULL
    """)

    # Convert column to timestamptz, interpreting old values as UTC
    op.alter_column(
        "VARIABLE",
        "created_at",
        type_=sa.TIMESTAMP(timezone=True),
        postgresql_using="created_at AT TIME ZONE 'UTC'"
    )

    op.alter_column(
        "VARIABLE",
        "updated_at",
        type_=sa.TIMESTAMP(timezone=True),
        postgresql_using="updated_at AT TIME ZONE 'UTC'"
    )

    # add new org credit column in dataflow_settings
    op.add_column(
        "DATAFLOW_SETTING",
        sa.Column("new_org_credits", sa.Integer(), nullable=False, server_default="100")
    )


def downgrade():
    # Reverse VARIABLE changes
    op.drop_index('uq_active_secret_key', 'VARIABLE')
    op.create_unique_constraint('unique_key', 'VARIABLE', ['key', 'org_id', 'runtime', 'slug', 'created_by'])
    op.drop_column('VARIABLE', 'deleted_at')
    
    # Reverse ROLE_SERVER changes
    op.drop_constraint('_role_server_uc', 'ROLE_SERVER', type_='unique')
    op.drop_constraint('role_server_server_id_fkey', 'ROLE_SERVER', type_='foreignkey')
    # 1. Re-add old column (nullable)
    op.add_column(
        "ROLE_SERVER",
        sa.Column("custom_server_id", sa.Integer(), nullable=True)
    )
    # 2. Copy values back from server_id
    op.execute("""
        UPDATE "ROLE_SERVER"
        SET custom_server_id = server_id;
    """)
    # 3. Make custom_server_id NOT NULL (only if needed)
    op.alter_column(
        "ROLE_SERVER",
        "custom_server_id",
        nullable=False
    )
    # 4. Drop new server_id column
    op.drop_column("ROLE_SERVER", "server_id")
    
    # Add back custom_server_id column with foreign key
    op.add_column('ROLE_SERVER', sa.Column('custom_server_id', sa.Integer(), nullable=False))
    op.create_foreign_key(
        'role_server_custom_server_id_fkey',
        'ROLE_SERVER',
        'CUSTOM_SERVER',
        ['custom_server_id'],
        ['id'],
        ondelete='CASCADE'
    )
    op.create_unique_constraint('_role_server_uc', 'ROLE_SERVER', ['role_id', 'custom_server_id'])

    # Reverse ORGANIZATION_USER changes
    op.drop_constraint('organization_user_active_server_id_fkey', 'ORGANIZATION_USER', type_='foreignkey')
    op.create_foreign_key(
        'organization_user_active_server_id_fkey',
        'ORGANIZATION_USER',
        'CUSTOM_SERVER',
        ['active_server_id'],
        ['id'],
        ondelete='SET NULL'
    )
    
    # Reverse ENVIRONMENT changes
    op.drop_index('uq_active_env_short_name', 'ENVIRONMENT')
    op.drop_column('ENVIRONMENT', 'deleted_at')
    
    # Reverse CONNECTION changes
    op.drop_index('uq_active_connection_slug', 'CONNECTION')
    op.create_unique_constraint(
        'uq_active_conn_with_runtime_slug',
        'CONNECTION',
        ['conn_id', 'org_id', 'runtime', 'slug', 'is_active', 'created_by']
    )
    op.drop_column('CONNECTION', 'deleted_at')

    # Reverse: convert timestamptz back to timestamp without timezone
    # (values will be stored as naive UTC timestamps)
    op.alter_column(
        "VARIABLE",
        "created_at",
        type_=sa.TIMESTAMP(timezone=False),
        postgresql_using="created_at"
    )