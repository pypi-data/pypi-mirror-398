"""
Modèle pour les mentions dans les devis et factures
"""
from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from caerp.models.base import DBBASE, DBSESSION, default_table_args
from caerp.models.options import ConfigurableOption, get_id_foreignkey_col

TASK_MENTION = Table(
    "task_mention_rel",
    DBBASE.metadata,
    Column("task_id", Integer, ForeignKey("task.id", ondelete="cascade")),
    Column("mention_id", Integer, ForeignKey("task_mention.id")),
    UniqueConstraint("task_id", "mention_id"),
    mysql_charset=default_table_args["mysql_charset"],
    mysql_engine=default_table_args["mysql_engine"],
)
MANDATORY_TASK_MENTION = Table(
    "mandatory_task_mention_rel",
    DBBASE.metadata,
    Column("task_id", Integer, ForeignKey("task.id")),
    Column("mention_id", Integer, ForeignKey("task_mention.id")),
    UniqueConstraint("task_id", "mention_id"),
    mysql_charset=default_table_args["mysql_charset"],
    mysql_engine=default_table_args["mysql_engine"],
)


class TaskMention(ConfigurableOption):
    __colanderalchemy_config__ = {
        "title": "Mentions facultatives des devis/factures",
        "description": (
            "Configurer les mentions que les entrepreneurs peuvent faire"
            " figurer dans leurs devis/factures"
        ),
    }
    id = get_id_foreignkey_col("configurable_option.id")
    title = Column(
        String(255),
        default="",
        info={
            "colanderalchemy": {
                "title": "Titre à afficher dans les PDF",
                "description": (
                    "Texte apparaissant sous forme de titre dans la sortie PDF"
                    " (facultatif)"
                ),
            }
        },
    )
    full_text = Column(
        Text(),
        info={
            "colanderalchemy": {
                "title": "Texte à afficher dans les PDF",
                "description": (
                    "Si cette mention a été ajoutée à un devis/facture, ce"
                    " texte apparaitra dans la sortie PDF"
                ),
            }
        },
    )
    help_text = Column(
        String(255),
        info={
            "colanderalchemy": {
                "title": "Texte d'aide à l'utilisation",
                "description": "Aide fournie à l'entrepreneur dans l'interface",
            }
        },
    )

    def __json__(self, request):
        dic = super(TaskMention, self).__json__(request)
        dic.update(
            dict(
                help_text=self.help_text,
            )
        )
        return dic

    @property
    def is_used(self):
        task_query = (
            DBSESSION()
            .query(TASK_MENTION.c.task_id)
            .filter(TASK_MENTION.c.mention_id == self.id)
        )

        mandatory_query = (
            DBSESSION()
            .query(MANDATORY_TASK_MENTION.c.task_id)
            .filter(MANDATORY_TASK_MENTION.c.mention_id == self.id)
        )

        return (
            DBSESSION().query(task_query.exists()).scalar()
            or DBSESSION().query(mandatory_query.exists()).scalar()
        )


COMPANY_TASK_MENTION = Table(
    "company_task_mention_rel",
    DBBASE.metadata,
    Column("task_id", Integer, ForeignKey("task.id", ondelete="cascade")),
    Column("company_task_mention_id", Integer, ForeignKey("company_task_mention.id")),
    UniqueConstraint("task_id", "company_task_mention_id"),
    mysql_charset=default_table_args["mysql_charset"],
    mysql_engine=default_table_args["mysql_engine"],
)


class CompanyTaskMention(ConfigurableOption):
    """
    Mention facultative des devis/factures configurée au niveau de l'enseigne
    """

    id = get_id_foreignkey_col("configurable_option.id")
    title = Column(
        String(255),
        default="",
        info={
            "colanderalchemy": {
                "title": "Titre à afficher dans les PDF",
                "description": (
                    "Texte apparaissant sous forme de titre dans la sortie PDF"
                    " (facultatif)"
                ),
            }
        },
        nullable=True,
    )
    full_text = Column(
        Text(),
        info={
            "colanderalchemy": {
                "title": "Texte à afficher dans les PDF",
                "description": (
                    "Si cette mention a été ajoutée à un devis/facture, ce"
                    " texte apparaitra dans la sortie PDF"
                ),
            }
        },
        nullable=False,
    )
    help_text = Column(
        String(255),
        info={
            "colanderalchemy": {
                "title": "Texte d'aide à l'utilisation",
                "description": "Aide fournie dans l'interface de saisie",
            }
        },
    )
    company_id = Column(
        Integer, ForeignKey("company.id", ondelete="CASCADE"), nullable=False
    )
    company = relationship("Company", back_populates="company_task_mentions")
