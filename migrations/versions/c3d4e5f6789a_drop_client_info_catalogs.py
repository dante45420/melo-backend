"""drop client_infos and catalog tables; notes on clients

Revision ID: c3d4e5f6789a
Revises: a1b2c3d4e5f6
Create Date: 2026-03-19

En instalaciones nuevas, initial_schema ya incluye posts_* y notes en clients
y no crea client_infos; esta migración solo añade columnas si faltan y elimina
tablas legacy si existen.
"""
from alembic import op
import sqlalchemy as sa


revision = "c3d4e5f6789a"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = {c["name"] for c in insp.get_columns("clients")}

    if "posts_liked" not in cols:
        op.add_column("clients", sa.Column("posts_liked", sa.Text(), nullable=True))
    if "posts_disliked" not in cols:
        op.add_column("clients", sa.Column("posts_disliked", sa.Text(), nullable=True))
    if "notes" not in cols:
        op.add_column("clients", sa.Column("notes", sa.Text(), nullable=True))

    if insp.has_table("client_infos"):
        if bind.dialect.name == "postgresql":
            op.execute(
                sa.text(
                    """
                    UPDATE clients c SET
                        posts_liked = COALESCE(c.posts_liked, ci.posts_liked),
                        posts_disliked = COALESCE(c.posts_disliked, ci.posts_disliked),
                        notes = COALESCE(c.notes, ci.notes)
                    FROM client_infos ci
                    WHERE ci.client_id = c.id
                    """
                )
            )
        else:
            op.execute(
                sa.text(
                    """
                    UPDATE clients SET
                        posts_liked = COALESCE(posts_liked, (SELECT posts_liked FROM client_infos WHERE client_infos.client_id = clients.id)),
                        posts_disliked = COALESCE(posts_disliked, (SELECT posts_disliked FROM client_infos WHERE client_infos.client_id = clients.id)),
                        notes = COALESCE(notes, (SELECT notes FROM client_infos WHERE client_infos.client_id = clients.id))
                    WHERE id IN (SELECT client_id FROM client_infos)
                    """
                )
            )
        op.drop_table("client_infos")

    for t in ("previous_results", "value_propositions", "company_infos"):
        if insp.has_table(t):
            op.drop_table(t)


def downgrade():
    op.create_table(
        "company_infos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "value_propositions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "previous_results",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "client_infos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("value_proposition_id", sa.Integer(), nullable=True),
        sa.Column("company_info_id", sa.Integer(), nullable=True),
        sa.Column("previous_results_id", sa.Integer(), nullable=True),
        sa.Column("posts_liked", sa.Text(), nullable=True),
        sa.Column("posts_disliked", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.ForeignKeyConstraint(["company_info_id"], ["company_infos.id"]),
        sa.ForeignKeyConstraint(["previous_results_id"], ["previous_results.id"]),
        sa.ForeignKeyConstraint(["value_proposition_id"], ["value_propositions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("client_id"),
    )
    op.execute(
        sa.text(
            """
            INSERT INTO client_infos (client_id, posts_liked, posts_disliked, notes)
            SELECT id, posts_liked, posts_disliked, notes FROM clients
            WHERE posts_liked IS NOT NULL OR posts_disliked IS NOT NULL OR notes IS NOT NULL
            """
        )
    )
    op.drop_column("clients", "notes")
    op.drop_column("clients", "posts_disliked")
    op.drop_column("clients", "posts_liked")
