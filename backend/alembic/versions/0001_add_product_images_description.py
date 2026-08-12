"""add product images and description columns

Revision ID: 0001
Revises:
Create Date: 2026-08-12
"""
import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    json_type = sa.JSON()
    bind_name = getattr(bind.dialect, "name", "")
    column_args = {"server_default": sa.text("'[]'")} if bind_name == "postgresql" else {}
    op.add_column("products", sa.Column("images", json_type, **column_args))
    op.add_column("products", sa.Column("description", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("products", "description")
    op.drop_column("products", "images")