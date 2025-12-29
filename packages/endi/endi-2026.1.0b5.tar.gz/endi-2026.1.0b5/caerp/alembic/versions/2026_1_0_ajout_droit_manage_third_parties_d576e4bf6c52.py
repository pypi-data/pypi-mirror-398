"""
2026.1.0 Donne le droit 'manage_third_parties' aux rôles de type 'equipe_appui'
"""
revision = "d576e4bf6c52"
down_revision = "a2b2e2bc0689"


def update_database_structure():
    pass


def migrate_datas():
    from sqlalchemy import select
    from zope.sqlalchemy import mark_changed

    from caerp.models.base import DBSESSION
    from caerp.models.user import Group
    from caerp.models.user.access_right import AccessRight

    session = DBSESSION()

    tp_right = session.execute(
        select(AccessRight).where(AccessRight.name == "global_manage_third_parties")
    ).scalar()

    if not tp_right:
        tp_right = AccessRight(name="global_manage_third_parties")
        session.add(tp_right)
        mark_changed(session)
        session.flush()

    ea_groups = (
        session.execute(select(Group).filter(Group.account_type == "equipe_appui"))
        .scalars()
        .all()
    )
    for ea_group in ea_groups:
        if tp_right not in ea_group.access_rights:
            ea_group.access_rights.append(tp_right)
        session.merge(ea_group)

    mark_changed(session)
    session.flush()


def upgrade():
    update_database_structure()
    migrate_datas()


def downgrade():
    pass
