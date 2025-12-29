"""3.2.1 : fix_payment_2

Revision ID: 658e0f23ee2
Revises: 3017103d60c0
Create Date: 2016-04-26 18:20:10.010347

"""

# revision identifiers, used by Alembic.
revision = "658e0f23ee2"
down_revision = "3017103d60c0"

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
            payment.amount = payment.amount / 1000
            db().merge(payment)
        except:
            print(("Erreur payment : %s (%s)" % payment.id, payment.amount))

    from zope.sqlalchemy import mark_changed

    mark_changed(db())


def downgrade():
    pass
