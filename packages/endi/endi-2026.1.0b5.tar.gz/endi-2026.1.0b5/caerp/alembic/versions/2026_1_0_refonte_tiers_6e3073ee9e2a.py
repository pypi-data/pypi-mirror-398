"""
2026.1.0 Refonte des tiers
"""
revision = "6e3073ee9e2a"
down_revision = "2bfe694e37ca"

import logging
import re

from sqlalchemy import Column, DateTime, String, or_, select
from zope.sqlalchemy import mark_changed

from caerp.alembic import utils
from caerp.models.base import DBSESSION

logger = logging.getLogger(__name__)


def clean_registration_number(value):
    if not isinstance(value, str):
        return value
    value = value.strip()
    value = value.upper()
    value = value.replace("SIRET", "").replace("SIREN", "").replace("N°", "")
    # on ne garde que les caractères alphanumériques
    value = "".join([char for char in value if char.isalnum()])
    return value


def is_siren(value):
    from stdnum.fr import siren

    return siren.is_valid(value)


def is_siret(value):
    from stdnum.fr import siret

    return siret.is_valid(value)


def is_tva_intracomm(value):
    return re.compile("^FR[0-9]{11}$").match(value)


def is_long_tva_intracomm(value):
    # For SIRET and not SIREN in TVA Intracomm
    return re.compile("^FR[0-9]{16}$").match(value)


def is_rcs(value):
    return re.compile("^RCS[a-zA-Z]*[A|B]?[0-9]{9}$").match(value) or re.compile(
        "^[0-9]{9}RCS[a-zA-Z]*[A|B]?$"
    ).match(value)


def format_siren(value):
    if is_siren(value):
        return "{} {} {}".format(value[:3], value[3:6], value[-3:])
    return value


def update_database_structure():
    logger.info("Mise à jour de la table 'third_party'")
    # On garde les colonnes par sécurité pour l'instant
    # utils.drop_column("third_party", "code")
    # utils.drop_column("third_party", "fax")
    utils.add_column(
        "third_party",
        Column("internal_name", String(255), nullable=False, default=""),
    )
    utils.add_column(
        "third_party",
        Column("siret", String(15), nullable=False, default="", index=True),
    )
    utils.add_column(
        "third_party",
        Column("api_last_update", DateTime(), nullable=True),
    )


def set_siret_from_other_fields(field_value, third_party, fieldname):
    if not field_value:
        return
    if is_tva_intracomm(field_value):
        third_party.siret = field_value[-9:]
        if third_party.tva_intracomm == "":
            third_party.tva_intracomm = field_value
    elif is_long_tva_intracomm(field_value):
        third_party.siret = field_value[-14:]
        if third_party.tva_intracomm == "":
            third_party.tva_intracomm = field_value
    elif is_rcs(field_value):
        field_value = re.sub(r"\D", "", field_value)
        third_party.siret = field_value[-9:]
    elif is_siret(field_value) or is_siren(field_value):
        third_party.siret = field_value
        setattr(third_party, fieldname, "")
    elif len(field_value) >= 14 and is_siret(field_value[:14]):
        third_party.siret = field_value[:14]
    elif len(field_value) >= 9 and is_siren(field_value[:9]):
        third_party.siren = field_value[:9]


def migrate_datas():
    """
    Try to populate SIREN field for all third party companies (customers and suppliers)
    based on actual 'registration' and 'tva_intracomm' fields
    """
    from caerp.models.third_party import ThirdParty

    session = DBSESSION()
    third_parties = (
        session.execute(
            select(ThirdParty).filter(
                or_(ThirdParty.registration != "", ThirdParty.tva_intracomm != "")
            )
        )
        .scalars()
        .all()
    )
    logger.info(
        f"Récupération du SIREN depuis les infos existantes pour {len(third_parties)} "
        "entreprises"
    )
    for third_party in third_parties:
        third_party.siret = ""
        reg = clean_registration_number(third_party.registration)
        tva_intracomm = clean_registration_number(third_party.tva_intracomm)
        set_siret_from_other_fields(reg, third_party, "registration")
        set_siret_from_other_fields(tva_intracomm, third_party, "tva_intracomm")
        if (
            third_party.siret != ""
            and not is_siret(third_party.siret)
            and not is_siren(third_party.siret)
        ):
            logger.debug(f"SIREN/SIRET invalide ({third_party.siret})")
            third_party.siret = ""
        if third_party.siret == "":
            logger.debug(
                "> #{} Impossible de déduidre le SIREN de {} -- ( REG:'{}' / TVA:'{}' "
                "=> SIREN:'{}' / REG:'{}' / TVA:'{}' )".format(
                    third_party.id,
                    third_party.company_name,
                    reg,
                    tva_intracomm,
                    format_siren(third_party.siret),
                    third_party.registration,
                    third_party.tva_intracomm,
                )
            )
        session.merge(third_party)

    mark_changed(session)
    session.flush()


def upgrade():
    update_database_structure()
    migrate_datas()


def downgrade():
    utils.drop_column("third_party", "api_last_update")
    utils.drop_column("third_party", "siret")
    utils.drop_column("third_party", "internal_name")
    # utils.add_column("third_party", Column("fax", String(15), default=""))
    # utils.add_column("third_party", Column("code", String(15), default=""))
