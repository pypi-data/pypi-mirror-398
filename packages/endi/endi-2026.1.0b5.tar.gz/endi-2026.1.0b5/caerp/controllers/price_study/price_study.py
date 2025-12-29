from caerp.models.price_study.price_study import PriceStudy
from caerp.models.price_study.work import PriceStudyWork


def price_study_sync_with_task(request, price_study: PriceStudy):
    """
    Sync price_study elements with the associated Task
    """
    from .chapter import price_study_chapter_sync_with_task
    from .discount import price_study_discount_sync_with_task

    task = price_study.task
    for chapter in price_study.chapters:
        price_study_chapter_sync_with_task(request, chapter)

    all_discounts = list(task.discounts)
    for discount in all_discounts:
        request.dbsession.delete(discount)
        task.discounts.remove(discount)

    for discount in price_study.discounts:
        price_study_discount_sync_with_task(request, discount)

    task.cache_totals(request)


def price_study_on_before_commit(request, price_study, state, changes=None):
    from .product import price_study_product_sync_amounts

    if changes and "general_overhead" in changes:
        for product in price_study.products:
            if isinstance(product, PriceStudyWork) or product.mode == "supplier_ht":
                price_study_product_sync_amounts(request, product, propagate=False)
        price_study_sync_amounts(request, price_study)
        price_study_sync_with_task(request, price_study)


def price_study_sync_amounts(request, price_study, sync_down=False):
    """
    Compute cached amount attributes
    :param bool sync_down: Should we sync all children in the hierarchy
    """
    from .product import price_study_product_sync_amounts

    if hasattr(price_study, "_amount_cache"):
        delattr(price_study, "_amount_cache")
    if sync_down:
        for chapter in price_study.chapters:
            for product in chapter.products:
                price_study_product_sync_amounts(request, product, propagate=False)
    price_study.ht = price_study.total_ht()
    request.dbsession.merge(price_study)
