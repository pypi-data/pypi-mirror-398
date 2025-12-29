"""5.0 Revision merge

Revision ID: e7e675528508
Revises: ('ad33637b0b1a', '9a0a4f30ee28')
Create Date: 2019-06-24 10:37:30.998174

"""

# revision identifiers, used by Alembic.
revision = "e7e675528508"
down_revision = ("ad33637b0b1a", "9a0a4f30ee28")

import sqlalchemy as sa
from alembic import op


def update_database_structure():
    pass


def migrate_datas():
    from caerp.models.base import DBSESSION

    session = DBSESSION()
    from alembic.context import get_bind

    conn = get_bind()


def upgrade():
    update_database_structure()
    migrate_datas()


def downgrade():
    pass
