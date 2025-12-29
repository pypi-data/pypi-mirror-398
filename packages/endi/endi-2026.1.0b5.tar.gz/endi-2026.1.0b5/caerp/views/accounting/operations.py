import logging

import colander
from pyramid.httpexceptions import HTTPFound
from sqlalchemy.orm import load_only

from caerp.celery.tasks.accounting_api import synchronize_accounting_from_quadraod
from caerp.celery.tasks.accounting_measure_compute import compile_measures_task
from caerp.celery.tasks.utils import check_alive
from caerp.consts.permissions import PERMISSIONS
from caerp.forms.accounting import get_operation_list_schema, get_upload_list_schema
from caerp.models.accounting.operations import (
    AccountingOperation,
    AccountingOperationUpload,
)
from caerp.utils.widgets import Link, POSTButton, ViewLink
from caerp.views import BaseListView, DeleteView
from caerp.views.accounting.routes import (
    UPLOAD_ITEM_INCOME_STATEMENT_ROUTE,
    UPLOAD_ITEM_ROUTE,
    UPLOAD_ITEM_TREASURY_ROUTE,
    UPLOAD_ROUTE,
)

logger = logging.getLogger(__name__)


class UploadListView(BaseListView):
    title = "Remontées comptables"
    add_template_vars = ("stream_main_actions", "stream_actions")
    schema = get_upload_list_schema()
    sort_columns = {
        "date": AccountingOperationUpload.date,
        "filename": AccountingOperationUpload.filename,
        "created_at": AccountingOperationUpload.created_at,
    }
    default_sort = "created_at"
    default_direction = "desc"

    def _has_operations(self, item):
        """
        Return true if the given item has operations attached to it

        :param obj item: a AccountingOperationUpload instance
        """
        return (
            self.request.dbsession.query(AccountingOperation.id)
            .filter_by(upload_id=item.id)
            .count()
            > 0
        )

    def stream_main_actions(self):
        if self.request.registry.settings.get("caerp.accounting_sync_operator", None):
            yield POSTButton(
                self.request.route_path(
                    UPLOAD_ROUTE,
                    _query={"action": "synchronize"},
                ),
                "Lancer une remontée comptable manuellement",
                title="Lancer maintenant une remontée des données comptables pour "
                "les exercices en cours",
                icon="exchange",
                confirm="Vous êtes sur le point de lancer une tâche de fond qui va "
                "remonter vos écritures comptables dans l'application.\n\nCela peut "
                "prendre jusqu'à 1h. Vous recevrez un mail à la fin du traitement."
                "\n\nContinuer ?",
            )

    def stream_actions(self, item):
        """
        Compile the action description for the given item
        """
        if self._has_operations(item):
            yield Link(
                self.request.route_path(
                    UPLOAD_ITEM_ROUTE,
                    id=item.id,
                ),
                "Voir le détail",
                title="Voir le détail des écritures importées",
                icon="arrow-right",
            )
            if item.is_upload_valid:
                if item.filetype == item.SYNCHRONIZED_ACCOUNTING:
                    yield POSTButton(
                        self.request.route_path(
                            UPLOAD_ITEM_ROUTE,
                            id=item.id,
                            _query={"action": "compile", "grid_type": "treasury"},
                        ),
                        "(Re)-Générer les états de trésorerie",
                        title="Génère les états de trésorerie depuis les "
                        "{}".format(item.filename.lower()),
                        icon="calculator",
                    )
                    yield POSTButton(
                        self.request.route_path(
                            UPLOAD_ITEM_ROUTE,
                            id=item.id,
                            _query={
                                "action": "compile",
                                "grid_type": "income_statement",
                            },
                        ),
                        "(Re)-Générer les comptes de résultat",
                        title="Génère les comptes de résultat depuis les "
                        "{}".format(item.filename.lower()),
                        icon="calculator",
                    )
                    yield POSTButton(
                        self.request.route_path(
                            UPLOAD_ITEM_ROUTE,
                            id=item.id,
                            _query={
                                "action": "compile",
                                "grid_type": "balance_sheet",
                            },
                        ),
                        "(Re)-Générer les bilans",
                        title="Génère les bilans depuis les "
                        "{}".format(item.filename.lower()),
                        icon="calculator",
                    )
                else:
                    yield POSTButton(
                        self.request.route_path(
                            UPLOAD_ITEM_ROUTE, id=item.id, _query={"action": "compile"}
                        ),
                        "Recalculer les indicateurs",
                        title="Recalculer les indicateurs générés depuis ce "
                        "fichier (ex : vous avez changé la configuration des"
                        " indicateurs)",
                        icon="calculator",
                    )
        yield POSTButton(
            self.request.route_path(
                UPLOAD_ITEM_ROUTE, id=item.id, _query={"action": "delete"}
            ),
            "Supprimer",
            title="Supprimer les écritures téléversées ainsi que les "
            "indicateurs rattachés",
            icon="trash-alt",
            confirm="Supprimer ce téléversement "
            "entraînera la suppression : \n- Des indicateurs générés"
            " depuis ce fichier\n"
            "- Des écritures enregistrées provenant de ce fichier\n"
            "Continuez ?",
            css="negative",
        )

    def query(self):
        return AccountingOperationUpload.query().options(
            load_only(
                AccountingOperationUpload.id,
                AccountingOperationUpload.created_at,
                AccountingOperationUpload.date,
                AccountingOperationUpload.filename,
                AccountingOperationUpload.filetype,
                AccountingOperationUpload.is_upload_valid,
            )
        )

    def filter_date(self, query, appstruct):
        """
        Filter by date period
        """
        period_appstruct = appstruct.get("period", {})
        if period_appstruct not in (None, colander.null):
            start_date = appstruct.get("start_date")
            if start_date not in (None, colander.null):
                query = query.filter(AccountingOperationUpload.date >= start_date)

            end_date = appstruct.get("end_date")
            if end_date not in (None, colander.null):
                query = query.filter(AccountingOperationUpload.date >= end_date)
        return query

    def filter_filetype(self, query, appstruct):
        """
        Filter uploads by filetype
        """
        filetype = appstruct.get("filetype", None)
        if filetype not in ("all", None, colander.null):
            query = query.filter(AccountingOperationUpload.filetype == filetype)

        return query


class DeleteUploadView(DeleteView):
    """
    AccountingOperationUpload delete view
    """

    delete_msg = "Les données ont bien été supprimées"
    redirect_route = "/accounting/operation_uploads"


class OperationListTools:
    """
    Tools for list operations
    """

    schema = get_operation_list_schema()
    sort_columns = {
        "analytical_account": AccountingOperation.analytical_account,
        "general_account": AccountingOperation.general_account,
        "date": AccountingOperation.date,
    }
    default_sort = "date"
    default_direction = "desc"

    def sort_by_date(self, query, appstruct):
        return query.order_by(AccountingOperation.date.desc()).order_by(
            AccountingOperation.analytical_account.asc()
        )

    def query(self):
        query = AccountingOperation.query().options(
            load_only(
                AccountingOperation.id,
                AccountingOperation.analytical_account,
                AccountingOperation.general_account,
                AccountingOperation.company_id,
                AccountingOperation.label,
                AccountingOperation.debit,
                AccountingOperation.credit,
                AccountingOperation.balance,
            )
        )
        return query.filter_by(upload_id=self.context.id)

    def filter_analytical_account(self, query, appstruct):
        account = appstruct.get("analytical_account")
        if account not in ("", colander.null, None):
            logger.debug("    + Filtering by analytical_account")
            query = query.filter_by(analytical_account=account)
        return query

    def filter_general_account(self, query, appstruct):
        account = appstruct.get("general_account")
        if account not in ("", colander.null, None):
            logger.debug("    + Filtering by general_account")
            query = query.filter(
                AccountingOperation.general_account.like(account + "%")
            )
        return query

    def filter_search(self, query, appstruct):
        search = appstruct.get("search")
        if search not in ("", colander.null, None):
            query = query.filter(AccountingOperation.label.like("%" + search + "%"))
        return query

    def filter_include_associated(self, query, appstruct):
        include = appstruct.get("include_associated")
        if not include:
            query = query.filter_by(company_id=None)
        return query

    def filter_company_id(self, query, appstruct):
        cid = appstruct.get("company_id")
        if cid not in ("", None, colander.null):
            query = query.filter_by(company_id=cid)
        return query


class OperationListView(
    OperationListTools,
    BaseListView,
):
    """
    Return the list of operations of a given upload (the view's context)
    """

    add_template_vars = (
        "stream_regenerate_actions",
        "stream_view_actions",
        "stream_export_actions",
        "stream_delete_actions",
    )

    @property
    def title(self):
        return "Liste des écritures extraites du fichier {0}".format(
            self.context.filename
        )

    def populate_actionmenu(self, appstruct):
        self.request.actionmenu.add(
            ViewLink(
                "Liste des fichiers téléversés",
                path="/accounting/operation_uploads",
            )
        )

    def _get_item_url(self, **kwargs):
        return self.request.route_path(
            UPLOAD_ITEM_ROUTE, id=self.context.id, _query=kwargs
        )

    def stream_regenerate_actions(self):
        """
        Stream the action buttons
        """
        yield POSTButton(
            self._get_item_url(action="compile", grid_type="treasury"),
            "(Re)-Générer les états de trésorerie",
            icon="calculator",
        )
        yield POSTButton(
            self._get_item_url(action="compile", grid_type="income_statement"),
            "(Re)-Générer les comptes de résultat",
            icon="calculator",
        )
        yield POSTButton(
            self._get_item_url(action="compile", grid_type="balance_sheet"),
            "(Re)-Générer les bilans",
            icon="calculator",
        )

    def stream_view_actions(self):
        yield Link(
            self.request.route_path(UPLOAD_ITEM_TREASURY_ROUTE, id=self.context.id),
            "Voir les états de trésorerie",
            title="Voir les états de trésorerie générés depuis ces " "écritures",
            icon="eye",
            css="btn icon",
        )
        yield Link(
            self.request.route_path(
                UPLOAD_ITEM_INCOME_STATEMENT_ROUTE, id=self.context.id
            ),
            "Voir les comptes de résultat",
            title="Voir les comptes de résultat générés depuis ces " "écritures",
            icon="eye",
            css="btn icon",
        )

    def stream_export_actions(self):
        args = self.request.GET.copy()

        yield Link(
            self.request.route_path(
                "operations.{extension}",
                extension="csv",
                id=self.context.id,
                _query=args,
            ),
            label="Exporter au format CSV",
            title="Exporter les éléments de la liste au format CSV",
            icon="file-csv",
        )
        yield Link(
            self.request.route_path(
                "operations.{extension}",
                extension="xls",
                id=self.context.id,
                _query=args,
            ),
            label="Exporter au format Excel",
            title="Exporter les éléments de la liste au format Excel (xlsx)",
            icon="file-excel",
        )
        yield Link(
            self.request.route_path(
                "operations.{extension}",
                extension="ods",
                id=self.context.id,
                _query=args,
            ),
            label="Exporter au format ODS",
            title="Exporter les éléments de la liste au format ODS",
            icon="file-spreadsheet",
        )

    def stream_delete_actions(self):
        yield POSTButton(
            self._get_item_url(action="delete"),
            label="Supprimer",
            title="Supprimer ces écritures",
            confirm="Êtes-vous sûr de vouloir supprimer ces écritures, "
            "cela supprimera également tous les indicateurs générés "
            "depuis celles-ci. \nContinuer ?",
            css="btn icon negative",
            icon="trash-alt",
        )


def synchronize_accounting_view(context, request):
    """
    Manually launch accounting synchronization
    """
    sync_operator = request.registry.settings.get(
        "caerp.accounting_sync_operator", None
    )
    if sync_operator:
        service_ok, msg = check_alive()
        if not service_ok:
            request.session.flash(msg, "error")
        else:
            logger.info(f"Synchronizing accounting operations from '{sync_operator}'")
            celery_job = None
            if sync_operator == "quadraod":
                celery_job = synchronize_accounting_from_quadraod.apply_async()
            if celery_job:
                logger.info(
                    "The celery task {0} has been delayed, see celery logs for "
                    "details".format(celery_job.id)
                )
                request.session.flash("La remontée comptable a bien démarré !")
            else:
                request.session.flash(
                    "Opérateur de synchronisation comptable non reconnu : {}".format(
                        sync_operator
                    ),
                    "error",
                )
    else:
        request.session.flash("Erreur : Aucune remontée comptable configurée", "error")
    return HTTPFound(request.referrer)


def compile_measures_view(context, request):
    """
    Handle compilation of measures

    :param obj context: The AccountingOperationUpload instance
    :param obj request: The pyramid request object
    """
    # FIXME: transformer en classe et refacto avec AsyncJobMixin ?
    service_ok, msg = check_alive()
    if not service_ok:
        request.session.flash(msg, "error")
        return HTTPFound(request.referrer)
    logger.debug("Compiling measures for upload {0}".format(context.id))

    celery_job = compile_measures_task.delay(context.id, request.GET.get("grid_type"))

    logger.info(
        "The Celery Task {0} has been delayed, see celery logs for "
        "details".format(celery_job.id)
    )
    request.session.flash("Les indicateurs sont en cours de génération")
    return HTTPFound(request.referrer)


def includeme(config):
    config.add_view(
        UploadListView,
        route_name=UPLOAD_ROUTE,
        renderer="/accounting/operation_uploads.mako",
        permission=PERMISSIONS["global.generate_accounting_measures"],
    )

    config.add_view(
        DeleteUploadView,
        route_name=UPLOAD_ITEM_ROUTE,
        request_param="action=delete",
        permission=PERMISSIONS["global.config_accounting"],
        request_method="POST",
        require_csrf=True,
    )

    config.add_view(
        OperationListView,
        route_name=UPLOAD_ITEM_ROUTE,
        renderer="/accounting/operations.mako",
        permission=PERMISSIONS["global.generate_accounting_measures"],
    )
    config.add_view(
        synchronize_accounting_view,
        route_name=UPLOAD_ROUTE,
        request_param="action=synchronize",
        permission=PERMISSIONS["global.generate_accounting_measures"],
        request_method="POST",
        require_csrf=True,
    )
    config.add_view(
        compile_measures_view,
        route_name=UPLOAD_ITEM_ROUTE,
        request_param="action=compile",
        permission=PERMISSIONS["global.generate_accounting_measures"],
        request_method="POST",
        require_csrf=True,
    )
    config.add_admin_menu(
        parent="accounting",
        order=7,
        href=UPLOAD_ROUTE,
        label="Remontée comptable",
        permission=PERMISSIONS["global.generate_accounting_measures"],
    )
