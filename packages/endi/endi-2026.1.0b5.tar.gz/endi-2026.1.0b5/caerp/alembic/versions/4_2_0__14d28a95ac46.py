"""4.2.0 empty message

Revision ID: 14d28a95ac46
Revises: 7aed0aafcbd
Create Date: 2018-12-06 18:02:31.442653

"""

# revision identifiers, used by Alembic.
revision = "14d28a95ac46"
down_revision = "7aed0aafcbd"

import sqlalchemy as sa
from alembic import op

from caerp.alembic.utils import column_exists


def update_database_structure():
    if column_exists("accounts", "session_datas"):
        op.alter_column(
            "accounts", "session_datas", new_column_name="user_prefs", type_=sa.Text
        )


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
