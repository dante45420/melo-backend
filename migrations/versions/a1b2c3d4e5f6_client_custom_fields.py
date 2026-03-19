"""client custom field definitions and values

Revision ID: a1b2c3d4e5f6
Revises: 1425395b0278
Create Date: 2026-03-19

"""
from alembic import op
import sqlalchemy as sa


revision = "a1b2c3d4e5f6"
down_revision = "1425395b0278"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "client_field_definitions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(length=300), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "client_field_values",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("field_definition_id", sa.Integer(), nullable=False),
        sa.Column("value", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["field_definition_id"], ["client_field_definitions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("client_id", "field_definition_id", name="uq_client_field_value_pair"),
    )


def downgrade():
    op.drop_table("client_field_values")
    op.drop_table("client_field_definitions")
