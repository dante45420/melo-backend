"""subscription delivery text + web pricing on plan; drop addon web types

Revision ID: e4f5g6h7i8j0
Revises: c3d4e5f6789a

"""
from alembic import op
import sqlalchemy as sa


revision = "e4f5g6h7i8j0"
down_revision = "c3d4e5f6789a"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"
    false_default = sa.text("false") if is_pg else sa.text("0")

    op.add_column(
        "client_subscriptions",
        sa.Column("web_enabled", sa.Boolean(), server_default=false_default, nullable=False),
    )

    op.add_column("subscriptions", sa.Column("delivery_contents", sa.Text(), nullable=True))
    op.add_column(
        "subscriptions",
        sa.Column("web_active", sa.Boolean(), server_default=false_default, nullable=False),
    )
    op.add_column("subscriptions", sa.Column("web_creation_price", sa.Integer(), nullable=True))
    op.add_column("subscriptions", sa.Column("web_maintenance_monthly", sa.Integer(), nullable=True))

    true_lit, false_lit = ("true", "false") if is_pg else ("1", "0")
    updates = [
        (
            "basico",
            "2 posts + 3 historias/semana · 1 entrega semanal",
            true_lit,
            149900,
            29900,
        ),
        (
            "pro",
            "4 posts (1 reel) + 7 historias/semana · 1 entrega semanal",
            true_lit,
            119900,
            24900,
        ),
        (
            "full",
            "5 posts (2 reels) + 14 historias/semana · 1 entrega semanal",
            true_lit,
            89900,
            19900,
        ),
    ]
    for slug, contents, w_lit, wc, wm in updates:
        esc = contents.replace("'", "''")
        op.execute(
            sa.text(
                f"""
                UPDATE subscriptions SET
                    delivery_contents = '{esc}',
                    web_active = {w_lit},
                    web_creation_price = {wc},
                    web_maintenance_monthly = {wm}
                WHERE slug = '{slug}' AND type = 'plan'
                """
            )
        )

    op.execute(
        sa.text(
            """
            UPDATE payments SET client_subscription_id = NULL
            WHERE client_subscription_id IN (
                SELECT cs.id FROM client_subscriptions cs
                INNER JOIN subscriptions s ON s.id = cs.subscription_id
                WHERE s.type IN ('web_design', 'web_maintenance')
            )
            """
        )
    )

    we = true_lit
    op.execute(
        sa.text(
            f"""
            UPDATE client_subscriptions SET web_enabled = {we}
            WHERE id IN (
                SELECT cs_plan.id FROM client_subscriptions cs_plan
                INNER JOIN subscriptions sp ON sp.id = cs_plan.subscription_id AND sp.type = 'plan'
                WHERE EXISTS (
                    SELECT 1 FROM client_subscriptions cs_w
                    INNER JOIN subscriptions sw ON sw.id = cs_w.subscription_id
                    WHERE cs_w.client_id = cs_plan.client_id
                    AND sw.type IN ('web_design', 'web_maintenance')
                    AND cs_w.status = 'active'
                )
                AND cs_plan.status = 'active'
            )
            """
        )
    )

    op.execute(
        sa.text(
            """
            DELETE FROM client_subscriptions WHERE subscription_id IN (
                SELECT id FROM subscriptions WHERE type IN ('web_design', 'web_maintenance')
            )
            """
        )
    )
    op.execute(
        sa.text(
            "DELETE FROM subscriptions WHERE type IN ('web_design', 'web_maintenance')"
        )
    )

    with op.batch_alter_table("subscriptions") as batch_op:
        batch_op.drop_column("is_addon")


def downgrade():
    op.add_column(
        "subscriptions",
        sa.Column("is_addon", sa.Boolean(), server_default=sa.text("0"), nullable=True),
    )
    op.execute(sa.text("UPDATE subscriptions SET is_addon = 0"))

    with op.batch_alter_table("subscriptions") as batch_op:
        batch_op.drop_column("web_maintenance_monthly")
        batch_op.drop_column("web_creation_price")
        batch_op.drop_column("web_active")
        batch_op.drop_column("delivery_contents")

    with op.batch_alter_table("client_subscriptions") as batch_op:
        batch_op.drop_column("web_enabled")
