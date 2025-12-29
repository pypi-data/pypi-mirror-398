"""
2025.5.6 Ajout de accounting_operation_upload.is_upload_valid
"""

revision = "2bfe694e37ca"
down_revision = "3fc875364294"

import sqlalchemy as sa
from alembic import op


def update_database_structure():
    op.add_column(
        "accounting_operation_upload",
        sa.Column("is_upload_valid", sa.Boolean(), nullable=False, default=True),
    )


def migrate_datas():
    from alembic.context import get_bind
    from zope.sqlalchemy import mark_changed

    from caerp.models.base import DBSESSION

    session = DBSESSION()
    conn = get_bind()
    conn.execute("update accounting_operation_upload set is_upload_valid=1")
    mark_changed(session)
    session.flush()


def upgrade():
    update_database_structure()
    migrate_datas()


def downgrade():
    op.drop_column("accounting_operation_upload", "is_upload_valid")
