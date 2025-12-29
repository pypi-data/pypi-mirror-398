"""
2026.1.0 Ajout d'un booléen 'modified' sur les lignes des devis et factures
"""
revision = "a2b2e2bc0689"
down_revision = "918f6b253918"

import sqlalchemy as sa
from alembic import op


def update_database_structure():
    op.add_column(
        "base_price_study_product", sa.Column("modified", sa.Boolean(), nullable=True)
    )
    op.add_column("discount", sa.Column("modified", sa.Boolean(), nullable=True))
    op.add_column(
        "price_study_work_item", sa.Column("modified", sa.Boolean(), nullable=True)
    )
    op.add_column(
        "price_study_discount", sa.Column("modified", sa.Boolean(), nullable=True)
    )
    op.add_column("task_line", sa.Column("modified", sa.Boolean(), nullable=True))


def migrate_datas():
    from alembic.context import get_bind
    from zope.sqlalchemy import mark_changed

    from caerp.models.base import DBSESSION

    session = DBSESSION()
    conn = get_bind()

    mark_changed(session)
    session.flush()


def upgrade():
    update_database_structure()
    migrate_datas()


def downgrade():
    pass
