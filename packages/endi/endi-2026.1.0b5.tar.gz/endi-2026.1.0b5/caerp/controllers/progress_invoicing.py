from caerp.models.progress_invoicing.invoicing import (
    ProgressInvoicingChapter,
    ProgressInvoicingPlan,
    ProgressInvoicingWork,
)


def _bulk_edit_chapter_percentage(
    request, context: ProgressInvoicingChapter, percentage: int
):
    """
    Bulk edit the percentage of the given context
    """
    for product in context.products:
        product.percentage = percentage - product.already_invoiced
        if isinstance(product, ProgressInvoicingWork):
            product.locked = True
            product.status.locked = True
            request.dbsession.merge(product.status)

        request.dbsession.merge(product)


def bulk_edit_chapter_percentage(
    request, context: ProgressInvoicingChapter, percentage: int
):
    """
    Bulk edit the percentage of the given context
    """
    _bulk_edit_chapter_percentage(request, context, percentage)
    context.plan.sync_with_task()


def bulk_edit_progress_invoicing_plan_percentage(
    request, context: ProgressInvoicingPlan, percentage: int
):
    """
    Bulk edit the percentage of the given context
    """
    for chapter in context.chapters:
        _bulk_edit_chapter_percentage(request, chapter, percentage)
    context.sync_with_task()
