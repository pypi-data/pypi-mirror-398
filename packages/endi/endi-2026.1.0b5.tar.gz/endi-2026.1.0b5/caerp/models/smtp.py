from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, relationship

from caerp.models.base import DBBASE, default_table_args
from caerp.models.base.mixins import TimeStampedMixin

from caerp.models.base import DBBASE, default_table_args
from caerp.models.base.mixins import TimeStampedMixin


class SmtpSettings(DBBASE, TimeStampedMixin):
    """
    Model storing SMTP settings
    :param smtp_host: SMTP host
    :param smtp_port: SMTP port
    :param smtp_user: SMTP user
    :param smtp_password: SMTP password
    :param smtp_ssl: Use SSL for SMTP connection
    :param smtp_tls: Use TLS for SMTP connection
    :param sender_email: Sender email address
    """

    __tablename__ = "smtp_settings"
    __table_args__ = default_table_args

    id: Mapped[int] = Column(
        Integer,
        primary_key=True,
        info={"colanderalchemy": {"exclude": True}},
    )
    smtp_host: Mapped[str] = Column(
        String(255),
        nullable=False,
        info={"colanderalchemy": {"title": "Adresse du serveur smtp"}},
    )
    smtp_port: Mapped[int] = Column(
        Integer,
        nullable=False,
        info={"colanderalchemy": {"title": "Port d'accès au serveur smtp"}},
    )
    smtp_user: Mapped[str] = Column(
        String(255),
        nullable=False,
        info={
            "colanderalchemy": {"title": "Nom d'utilisateur (généralement l’e-mail)"}
        },
    )
    smtp_password_salt: Mapped[str] = Column(
        String(255),
        nullable=False,
        info={"colanderalchemy": {"exclude": True}},
    )
    smtp_password_hash: Mapped[str] = Column(
        String(255),
        nullable=False,
        info={"colanderalchemy": {"exclude": True}},
    )

    smtp_ssl: Mapped[bool] = Column(
        Boolean,
        default=False,
        info={"colanderalchemy": {"title": "Activer SSL"}},
    )
    smtp_tls: Mapped[bool] = Column(
        Boolean,
        default=False,
        info={"colanderalchemy": {"title": "Activer Start/TLS"}},
    )
    sender_email: Mapped[str] = Column(String(255), nullable=False)
    company_id: Mapped[int] = Column(
        Integer, ForeignKey("company.id", ondelete="CASCADE"), nullable=True
    )

    def __repr__(self):
        return (
            f"<SmtpSettings({self.id}, {self.sender_email} "
            f"{self.smtp_host}:{self.smtp_port} "
            f"ssl: {self.smtp_ssl} tls: {self.smtp_tls} username: "
            f"{self.smtp_user} company_id: {self.company_id})>"
        )


class NodeSmtpHistory(DBBASE, TimeStampedMixin):
    """
    Model storing SMTP history of sending Node data by email

    :param smtp_settings_id: SMTP settings id
    :param status: Status of the mail sending attempt

    :param node_id: The node id
    :param subject: Subject of the mail
    :param body: Error body if the SMTP connection failed
    :param recipient: Recipient email address
    :param sender label: Sender label
    """

    __tablename__ = "node_smtp_history"
    __table_args__ = default_table_args
    id: Mapped[int] = Column(Integer, primary_key=True)
    smtp_settings: Mapped[str] = Column(String(255), nullable=False)
    status = Column(String(255), nullable=False)
    node_id = Column(ForeignKey("node.id", ondelete="CASCADE"), nullable=False)
    subject = Column(String(255), nullable=False)
    body = Column(Text(), nullable=True)
    error = Column(Text(), nullable=True)
    recipient = Column(String(255), nullable=False)
    reply_to = Column(String(255), nullable=True)
    copy_to = Column(String(255), nullable=True)
    sender_label = Column(String(255), nullable=True)

    node = relationship(
        "Node",
        primaryjoin="NodeSmtpHistory.node_id==Node.id",
        back_populates="smtp_history",
        info={"colanderalchemy": {"exclude": True}},
    )
    SUCCESS_STATUS = "success"
    ERROR_STATUS = "error"
