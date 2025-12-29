import logging

import colander
from pyramid.httpexceptions import HTTPForbidden

from caerp.consts.permissions import PERMISSIONS
from caerp.controllers.progress_invoicing import (
    bulk_edit_chapter_percentage,
    bulk_edit_progress_invoicing_plan_percentage,
)
from caerp.forms.progress_invoicing import (
    get_edit_product_schema,
    get_edit_work_schema,
    get_edit_workitem_schema,
    get_percentage_schema,
)
from caerp.models.progress_invoicing import (
    ProgressInvoicingBaseProduct,
    ProgressInvoicingChapter,
    ProgressInvoicingPlan,
    ProgressInvoicingWork,
    ProgressInvoicingWorkItem,
)
from caerp.utils.rest.apiv1 import RestError
from caerp.views import BaseRestView

from .routes import (
    BULK_EDIT_CHAPTER_API_ROUTE,
    BULK_EDIT_PLAN_API_ROUTE,
    CHAPTER_API_ROUTE,
    CHAPTER_ITEM_API_ROUTE,
    PLAN_ITEM_API_ROUTE,
    PRODUCT_API_ROUTE,
    PRODUCT_ITEM_API_ROUTE,
    WORK_ITEMS_API_ROUTE,
    WORK_ITEMS_ITEM_API_ROUTE,
)

logger = logging.getLogger(__name__)


class ProgressInvoicingPlanRestView(BaseRestView):
    # Pas de requête pour récupérer tous les plans
    route = None
    item_route = PLAN_ITEM_API_ROUTE

    def get(self):
        return {"id": self.context.id}

    def post(self):
        return HTTPForbidden()

    def put(self):
        return HTTPForbidden()

    def delete(self):
        return HTTPForbidden()

    def bulk_edit_percentage_endpoint(self):
        post_data = self.get_posted_data()
        try:
            schema = get_percentage_schema(self.request, self.context)
            schema = schema.bind(request=self.request)
            validated_data = schema.deserialize(post_data)
        except colander.Invalid as err:
            logger.exception("  - Erreur")
            logger.exception(post_data)
            raise RestError(err.asdict(), 400)

        percentage = validated_data["percentage"]
        bulk_edit_progress_invoicing_plan_percentage(
            self.request, self.context, percentage
        )
        return self.get()


class ProgressInvoicingChapterRestView(BaseRestView):
    route = CHAPTER_API_ROUTE
    item_route = CHAPTER_ITEM_API_ROUTE

    def collection_get(self):
        return self.context.chapters

    def put(self):
        return HTTPForbidden()

    def post(self):
        return HTTPForbidden()

    def delete(self):
        return HTTPForbidden()

    def bulk_edit_percentage_endpoint(self):
        post_data = self.get_posted_data()
        try:
            schema = get_percentage_schema(self.request, self.context)
            schema = schema.bind(request=self.request)

            validated_data = schema.deserialize(post_data)
        except colander.Invalid as err:
            logger.exception("  - Erreur")
            logger.exception(post_data)
            raise RestError(err.asdict(), 400)

        percentage = validated_data["percentage"]
        bulk_edit_chapter_percentage(self.request, self.context, percentage)
        return self.get()


class ProgressInvoicingProductRestView(BaseRestView):
    route = PRODUCT_API_ROUTE
    item_route = PRODUCT_ITEM_API_ROUTE

    def collection_get(self):
        return self.context.products

    def get_schema(self, submitted):
        if isinstance(self.context, ProgressInvoicingWork):
            return get_edit_work_schema()
        else:
            return get_edit_product_schema()

    def after_flush(self, entry, edit, attributes):
        entry.on_before_commit(self.request, "update", attributes)
        return super().after_flush(entry, edit, attributes)

    def post(self):
        return HTTPForbidden()

    def delete(self):
        return HTTPForbidden()


class ProgressInvoicingWorkItemRestView(BaseRestView):
    route = WORK_ITEMS_API_ROUTE
    item_route = WORK_ITEMS_ITEM_API_ROUTE
    schema = get_edit_workitem_schema()

    def collection_get(self):
        if isinstance(self.context, ProgressInvoicingWork):
            return self.context.items
        return []

    def pre_format(self, datas, edit=False):
        if "percentage" in datas:
            datas["_percentage"] = datas["percentage"]
        return super().pre_format(datas, edit)

    def after_flush(self, entry, edit, attributes):
        entry.on_before_commit(self.request, "update", attributes)
        return super().after_flush(entry, edit, attributes)

    def post(self):
        return HTTPForbidden()

    def delete(self):
        return HTTPForbidden()


def includeme(config):
    for view, collection_context, context in (
        (ProgressInvoicingPlanRestView, None, ProgressInvoicingPlan),
        (
            ProgressInvoicingChapterRestView,
            ProgressInvoicingPlan,
            ProgressInvoicingChapter,
        ),
        (
            ProgressInvoicingProductRestView,
            ProgressInvoicingChapter,
            ProgressInvoicingBaseProduct,
        ),
        (
            ProgressInvoicingWorkItemRestView,
            ProgressInvoicingWork,
            ProgressInvoicingWorkItem,
        ),
    ):
        config.add_rest_service(
            view,
            view.item_route,
            collection_route_name=view.route,
            collection_context=collection_context,
            context=context,
            collection_view_rights=PERMISSIONS["company.view"],
            view_rights=PERMISSIONS["company.view"],
            add_rights=PERMISSIONS["context.edit_progress_invoicing_plan"],
            edit_rights=PERMISSIONS["context.edit_progress_invoicing_plan"],
            delete_rights=PERMISSIONS["context.edit_progress_invoicing_plan"],
        )

    config.add_view(
        ProgressInvoicingPlanRestView,
        attr="bulk_edit_percentage_endpoint",
        route_name=BULK_EDIT_PLAN_API_ROUTE,
        permission=PERMISSIONS["context.edit_progress_invoicing_plan"],
        renderer="json",
        request_method="POST",
        context=ProgressInvoicingPlan,
        require_csrf=True,
    )

    config.add_view(
        ProgressInvoicingChapterRestView,
        attr="bulk_edit_percentage_endpoint",
        route_name=BULK_EDIT_CHAPTER_API_ROUTE,
        permission=PERMISSIONS["context.edit_progress_invoicing_plan"],
        renderer="json",
        request_method="POST",
        context=ProgressInvoicingChapter,
        require_csrf=True,
    )
