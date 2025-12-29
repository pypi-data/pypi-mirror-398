"""3.4 : add_user_vehicle

Revision ID: 6a8b2495102
Revises: 22721b810d30
Create Date: 2017-09-06 15:36:29.303641

"""

# revision identifiers, used by Alembic.
revision = "6a8b2495102"
down_revision = "22721b810d30"

import sqlalchemy as sa
from alembic import op


def update_database_structure():
    op.add_column("accounts", sa.Column("vehicle", sa.String(50), nullable=True))


def migrate_datas():
    from caerp.models.base import DBSESSION

    session = DBSESSION()
    from alembic.context import get_bind

    conn = get_bind()


def upgrade():
    update_database_structure()
    migrate_datas()


def downgrade():
    op.drop_column("accounts", "vehicle")
