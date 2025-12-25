"""Add show_walkthrough to USER and drop email_domain constraint on ORGANIZATION

Revision ID: 009
Revises: 008
Create Date: 2025-12-10 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None

def upgrade():
   # Convert column to timezone-aware timestamp
    op.alter_column(
        "SESSION",
        "last_seen",
        type_=sa.DateTime(timezone=True),
        existing_type=sa.DateTime(timezone=False),
        existing_nullable=False,
    )

    op.alter_column(
        "SESSION",
        "last_seen",
        server_default=sa.text("CURRENT_TIMESTAMP"),
        existing_type=sa.DateTime(timezone=True)
    )

    op.alter_column(
        "SESSION",
        "expires_at",
        type_=sa.DateTime(timezone=True),
        existing_type=sa.DateTime(timezone=False),
        existing_nullable=False,
    )

def downgrade():
    # Revert type back to non-tz timestamp
    op.alter_column(
        "SESSION",
        "last_seen",
        type_=sa.DateTime(timezone=False),
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=False,
    )

    # Remove default
    op.alter_column(
        "SESSION",
        "last_seen",
        server_default=None,
        existing_type=sa.DateTime()
    )

    op.alter_column(
        "SESSION",
        "expires_at",
        type_=sa.DateTime(timezone=False),
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=False,
    )