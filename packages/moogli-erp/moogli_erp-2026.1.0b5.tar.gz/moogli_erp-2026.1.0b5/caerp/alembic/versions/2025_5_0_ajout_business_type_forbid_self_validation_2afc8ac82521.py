"""
2025.5.0 Ajout de business_type.forbid_self_validation
"""

revision = "2afc8ac82521"
down_revision = "1fcb2b2e231e"

import sqlalchemy as sa
from alembic import op


def update_database_structure():
    op.add_column(
        "business_type",
        sa.Column("forbid_self_validation", sa.Boolean(), nullable=False),
    )


def upgrade():
    update_database_structure()


def downgrade():
    op.drop_column("business_type", "forbid_self_validation")
