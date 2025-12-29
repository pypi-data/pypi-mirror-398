# -*- coding: utf-8 -*-
import logging
from typing import List

from pyramid_mailer.message import Attachment

from caerp.celery.models import check_if_mail_sent, store_sent_mail
from caerp.exception import MailAlreadySent, UndeliveredMail
from caerp.models.third_party import Customer
from caerp.models.user import User, UserDatas
from caerp.utils.mail import send_mail

logger = logging.getLogger(__name__)


# BULLETINS DE SALAIRE ################################################################


SALARYSHEET_MAIL_MESSAGE = """Bonjour,
Vous trouverez ci-joint votre bulletin de salaire.
"""

SALARYSHEET_MAIL_SUBJECT = "Votre bulletin de salaire"


def send_salary_sheet(
    request,
    email,
    company_id,
    filename,
    filepath,
    force=False,
    message=None,
    subject=None,
):
    """
    Send a salarysheet to the given company's e-mail

    :param obj request: A pyramid request object
    :param str company_mail: The mail to send it to
    :param int company_id: The id of the associated company
    :param str filepath: The path to the filename
    :param bool force: Whether to force sending this file again
    :param str message: The mail message
    :param str subject: The mail subject
    :returns: A MailHistory instance
    :TypeError UndeliveredMail: When the company has no mail
    :TypeError MailAlreadySent: if the file has
        already been sent and no force option was passed
    """
    filebuf = open(filepath, "rb")
    filedatas = filebuf.read()

    if not force and check_if_mail_sent(filedatas, company_id):
        logger.warning("Mail already sent : mail already sent")
        raise MailAlreadySent("Mail already sent")

    filebuf.seek(0)

    if email is None:
        logger.warning(
            "Undelivered email : no mail provided for company {0}".format(company_id)
        )
        raise UndeliveredMail("no mail provided for company {0}".format(company_id))
    else:
        logger.info("Sending the file %s" % filepath)
        logger.info("Sending it to %s" % email)
        attachment = Attachment(filename, "application/pdf", filebuf)

        subject = subject or SALARYSHEET_MAIL_SUBJECT
        message = message or SALARYSHEET_MAIL_MESSAGE

        send_mail(
            request,
            email,
            message,
            subject,
            attachment,
        )
        return store_sent_mail(filepath, filedatas, company_id)


# FACTURATION INTERNE #################################################################


INTERNAL_ORDER_CUSTOMER_MAIL_OBJECT = """Nouvelle commande founisseur générée \
dans votre espace"""

INTERNAL_ORDER_CUSTOMER_MAIL_TMPL = """
Bonjour {customer},

L'enseigne {supplier} vous a transmis un devis 'interne'.

Une commande fournisseur contenant le devis est accessible dans votre espace
dans la section "Commande fournisseur".
"""

INTERNAL_ORDER_SUPPLIER_MAIL_OBJECT = "Votre devis a été transmis à votre \
client"
INTERNAL_ORDER_SUPPLIER_MAIL_TMPL = """
Bonjour {supplier},

Votre devis 'interne' a été transmis à l'enseigne {customer}.

Une commande fournisseur contenant le devis est accessible dans son espace dans
la section "Commande fournisseur".
"""


def send_customer_new_order_mail(request, order):
    """
    Send an email to an internal customer
    """
    customer = order.company
    supplier = order.supplier
    message = INTERNAL_ORDER_CUSTOMER_MAIL_TMPL.format(
        customer=customer.name, supplier=supplier.label
    )
    if customer.email:
        recipients = [customer.email]
        send_mail(request, recipients, message, INTERNAL_ORDER_CUSTOMER_MAIL_OBJECT)
    else:
        logger.error("Company {} has no email set".format(customer.id))


def send_supplier_new_order_mail(request, order):
    """
    Send an email to an internal supplier
    """
    customer = order.company
    supplier = order.supplier
    message = INTERNAL_ORDER_SUPPLIER_MAIL_TMPL.format(
        customer=customer.name, supplier=supplier.label
    )
    if supplier:
        recipients = [supplier.email]
        send_mail(request, recipients, message, INTERNAL_ORDER_SUPPLIER_MAIL_OBJECT)
    else:
        logger.error("Company {} has no email set".format(supplier.id))


INTERNAL_INVOICE_CUSTOMER_MAIL_OBJECT = """Nouvelle facture founisseur \
générée dans votre espace"""

INTERNAL_INVOICE_CUSTOMER_MAIL_TMPL = """
Bonjour {customer},

L'enseigne {supplier} vous a transmis une facture 'interne'.

Une facture fournisseur contenant la facture est accessible dans votre espace
dans la section "Facture fournisseur".
"""

INTERNAL_INVOICE_SUPPLIER_MAIL_OBJECT = "Votre facture a été transmis à votre \
client"
INTERNAL_INVOICE_SUPPLIER_MAIL_TMPL = """
Bonjour {supplier},

Votre facture 'interne' a été transmis à l'enseigne {customer}.

Une facture fournisseur contenant la facture est accessible dans son espace
dans la section "Facture fournisseur".
"""


def send_customer_new_invoice_mail(request, supplier_invoice):
    """
    Send an email to an internal customer
    """
    customer = supplier_invoice.company
    supplier = supplier_invoice.supplier
    message = INTERNAL_INVOICE_CUSTOMER_MAIL_TMPL.format(
        customer=customer.name, supplier=supplier.label
    )
    if customer.email:
        recipients = [customer.email]
        send_mail(request, recipients, message, INTERNAL_INVOICE_CUSTOMER_MAIL_OBJECT)
    else:
        logger.error("Company {} has no email set".format(customer.id))


def send_supplier_new_invoice_mail(request, supplier_invoice):
    """
    Send an email to an internal supplier
    """
    customer = supplier_invoice.company
    supplier = supplier_invoice.supplier
    message = INTERNAL_INVOICE_SUPPLIER_MAIL_TMPL.format(
        customer=customer.name, supplier=supplier.label
    )
    if supplier:
        recipients = [supplier.email]
        send_mail(request, recipients, message, INTERNAL_INVOICE_SUPPLIER_MAIL_OBJECT)
    else:
        logger.error("Company {} has no email set".format(supplier.id))


# RGPD ################################################################################


RGPD_SUPPORT_MESSAGE = (
    "Compte tenu du nombre important de données à anonymiser "
    "vous pouvez demander à votre support technique de vous assister."
)
RGPD_SUPPORT_MESSAGE_HIGH = (
    "Compte tenu du nombre très important de données à anonymiser "
    "il n'est pas possible d'afficher le détail ici. Vous devez "
    "demander à votre support technique d'intervenir."
)

RGPD_USERDATA_EMAIL_SUBJECT = "[RGPD] Il y a des fiches de gestion sociale à nettoyer"
RGPD_USERDATA_EMAIL_BODY = """Bonjour,

Vous recevez cet e-mail en tant que responsable RGPD.

Les {number} fiches de gestion sociale suivantes ne semblent pas avoir été utilisées \
    depuis plus de {days} jours et devraient être anonymisées.

{additional_message}


{email_body}
"""


def _get_userdata_link(request, userdata_entry):
    from caerp.views.userdatas.routes import USER_USERDATAS_URL

    settings = request.registry.settings
    instance_name = settings.get("caerp.instance_name")
    view_path = USER_USERDATAS_URL.format(id=userdata_entry.user_id)
    return f"https://{instance_name}/{view_path}"


def send_rgpd_userdata_notification(
    request, recipients, userdata_entries: List[UserDatas], days: int
):
    """
    Send an email to the RGPD team notifying about userdata entries that should be
    cleaned up.

    :param recipients: List of email addresses to send the notification to.
    :param userdata_entries: List of Userdata instances that should be cleaned up.
    :param days: Number of days after which userdata entries should be considered old.
    """
    subject = RGPD_USERDATA_EMAIL_SUBJECT.format(number=len(userdata_entries))
    links = ""
    additional_message = ""
    if len(userdata_entries) > 75:
        additional_message = RGPD_SUPPORT_MESSAGE_HIGH
    else:
        if len(userdata_entries) > 25:
            additional_message = RGPD_SUPPORT_MESSAGE
        for entry in userdata_entries:
            entry_url = _get_userdata_link(request, entry)
            links += (
                f"- {entry.coordonnees_lastname} {entry.coordonnees_firstname} : "
                f"{entry_url}\n"
            )
    body = RGPD_USERDATA_EMAIL_BODY.format(
        number=len(userdata_entries),
        days=days,
        email_body=links,
        additional_message=additional_message,
    )
    send_mail(request, recipients, body, subject)


RGPD_USER_ACCOUNT_EMAIL_SUBJECT = "[RGPD] Il y a des comptes utilisateurs à désactiver"
RGPD_USER_ACCOUNT_EMAIL_BODY = """Bonjour,

Vous recevez cet e-mail en tant que responsable RGPD.

Les {number} comptes utilisateurs suivants sont toujours actifs mais n'ont pas été \
    utilisés depuis plus de {days} jours. Ils devraient peut-être être désactivés.

{additional_message}


{email_body}
"""


def _get_user_account_link(request, user: User):
    from caerp.views.user.routes import USER_LOGIN_URL

    settings = request.registry.settings
    instance_name = settings.get("caerp.instance_name")
    view_path = USER_LOGIN_URL.format(id=user.id)
    return f"https://{instance_name}/{view_path}"


def send_unused_login_notification(
    request, recipients, user_entries: List[User], days: int
):
    """
    Send an email to the RGPD team notifying about unused active accounts

    :param recipients: List of email addresses to send the notification to.
    :param userdata_entries: List of Userdata instances that should be cleaned up.
    :param days: Number of days after which userdata entries should be considered old.
    """
    subject = RGPD_USER_ACCOUNT_EMAIL_SUBJECT.format(number=len(user_entries))
    links = ""
    additional_message = ""
    if len(user_entries) > 75:
        additional_message = RGPD_SUPPORT_MESSAGE_HIGH
    else:
        if len(user_entries) > 25:
            additional_message = RGPD_SUPPORT_MESSAGE
        for entry in user_entries:
            entry_url = _get_user_account_link(request, entry)
            links += f"- {entry.lastname} {entry.firstname} : " f"{entry_url}\n"
    body = RGPD_USER_ACCOUNT_EMAIL_BODY.format(
        number=len(user_entries),
        days=days,
        email_body=links,
        additional_message=additional_message,
    )
    send_mail(request, recipients, body, subject)


RGPD_CUSTOMER_EMAIL_SUBJECT = "[RGPD] Il y a des fiches clients à nettoyer"
RGPD_CUSTOMER_EMAIL_BODY = """Bonjour,

Vous recevez cet e-mail en tant que responsable RGPD.

Les {number} comptes client (particulier) suivants sont toujours actifs mais n'ont pas \
été utilisés depuis plus de {days} jours. Ils devraient être anonymisés.

{additional_message}


{email_body}
"""


def _get_customer_link(request, customer: Customer):
    from caerp.views.third_party.customer.routes import CUSTOMER_ITEM_ROUTE

    settings = request.registry.settings
    instance_name = settings.get("caerp.instance_name")
    view_path = CUSTOMER_ITEM_ROUTE.format(id=customer.id)
    return f"https://{instance_name}{view_path}"


def send_rgpd_customer_notification(
    request, recipients, customers: List[Customer], days: int
):
    """
    Send an email to the RGPD team notifying about unused individual customer accounts

    :param recipients: List of email addresses to send the notification to.
    :param customers: List of Customer instances that should be cleaned up.
    :param days: Number of days after which customer entries should be considered old.
    """
    subject = RGPD_CUSTOMER_EMAIL_SUBJECT.format(number=len(customers))
    links = ""
    additional_message = ""
    if len(customers) > 75:
        additional_message = RGPD_SUPPORT_MESSAGE_HIGH
    else:
        if len(customers) > 25:
            additional_message = RGPD_SUPPORT_MESSAGE
        for entry in customers:
            entry_url = _get_customer_link(request, entry)
            links += f"- {entry.lastname} {entry.firstname} : " f"{entry_url}\n"
    body = RGPD_CUSTOMER_EMAIL_BODY.format(
        number=len(customers),
        days=days,
        email_body=links,
        additional_message=additional_message,
    )
    send_mail(request, recipients, body, subject)
