"""
2026.1.0 Refonte de la gestion de la TVA des lignes des devis et factures
"""
revision = "918f6b253918"
down_revision = "6e3073ee9e2a"

import sqlalchemy as sa
from alembic import op

from caerp.alembic.utils import drop_column
from caerp.models.tva import Tva


def upgrade():
    from zope.sqlalchemy import mark_changed

    from caerp.models.base import DBSESSION

    session = DBSESSION()
    op.add_column("discount", sa.Column("tva_id", sa.Integer(), nullable=False))
    op.add_column("task_line", sa.Column("tva_id", sa.Integer(), nullable=False))

    # Migrate tva
    # Ensure tva exists before migrating
    for value in session.execute(
        sa.text(
            "select distinct(tva) from task_line where tva not in (select value from tva) "
            "UNION "
            "select distinct(tva) from discount where tva not in (select value from tva)"
        )
    ).scalars():
        tva = Tva(value=value, name=f"TVA {value/100} %", active=False, default=False)
        session.add(tva)
    mark_changed(session)
    session.flush()

    session.execute(
        sa.text(
            "update task_line set tva_id = (SELECT id FROM tva WHERE value = task_line.tva)"
        )
    )
    session.execute(
        sa.text(
            "update discount set tva_id = (SELECT id FROM tva WHERE value = discount.tva)"
        )
    )

    op.create_foreign_key(
        op.f("fk_discount_tva_id"), "discount", "tva", ["tva_id"], ["id"]
    )
    op.create_foreign_key(
        op.f("fk_task_line_tva_id"), "task_line", "tva", ["tva_id"], ["id"]
    )
    op.drop_column("discount", "tva")
    op.drop_column("task_line", "tva")
    drop_column("groups", "primary")


def downgrade():
    pass
