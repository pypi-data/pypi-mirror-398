"""3.2.1 : fix payment 3

Revision ID: 18504ec02955
Revises: 658e0f23ee2
Create Date: 2016-04-26 18:35:37.775710

"""

# revision identifiers, used by Alembic.
revision = "18504ec02955"
down_revision = "658e0f23ee2"

import sqlalchemy as sa
from alembic import op


def upgrade():
    from datetime import date

    from sqlalchemy import Date, cast

    from caerp.models.base import DBSESSION as db
    from caerp.models.task.invoice import Payment

    for payment in (
        db().query(Payment).filter(cast(Payment.created_at, Date) == date.today())
    ):
        try:
            payment.remittance_amount = float(payment.remittance_amount) / 100000.0
            db().merge(payment)
        except:
            print(
                ("Erreur payment : %s (%s)" % (payment.id, payment.remittance_amount))
            )

    from zope.sqlalchemy import mark_changed

    mark_changed(db())


def downgrade():
    pass
