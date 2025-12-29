from typing import List, Optional

from caerp.models.price_study.work import PriceStudyWork
from caerp.models.price_study.work_item import PriceStudyWorkItem


def price_study_work_item_from_sale_product(
    request, catalog_sale_product
) -> PriceStudyWorkItem:
    """
    Load a price study work item from a catalog product
    """
    instance = PriceStudyWorkItem()
    instance.work_unit_quantity = 1

    instance.supplier_ht = getattr(catalog_sale_product, "supplier_ht", None)

    for field in (
        "ht",
        "description",
        "unity",
        "mode",
    ):
        setattr(instance, field, getattr(catalog_sale_product, field, None))

    instance.work_unit_ht = catalog_sale_product.ht
    instance.base_sale_product = catalog_sale_product

    return instance


def price_study_work_item_from_work_item(
    request, price_study_work: PriceStudyWork, catalog_work_item
) -> PriceStudyWorkItem:
    """
    Load a price study work item from a catalog one
    """
    instance = PriceStudyWorkItem()
    instance.price_study_work = price_study_work

    for field in (
        "description",
        "supplier_ht",
        "ht",
        "unity",
        "total_ht",
        "mode",
        "base_sale_product_id",
    ):
        setattr(instance, field, getattr(catalog_work_item, field, None))

    instance.work_unit_quantity = catalog_work_item.quantity
    instance.total_quantity = catalog_work_item.quantity
    instance.work_unit_ht = catalog_work_item.total_ht
    return instance


def price_study_work_item_sync_amounts(
    request, work_item: PriceStudyWorkItem, work: Optional[PriceStudyWork] = None
):
    """
    Sync the work_item's cached values

    :param obj work: The PriceStudyWork to be synced in case of ascending syncing
    """
    work_item.ht = work_item.unit_ht()
    work_item.work_unit_ht = work_item.compute_work_unit_ht()
    work_item.total_ht = work_item.compute_total_ht()
    request.dbsession.merge(work_item)

    # On update le work que si ce n'est pas lui qui a fait la demande
    # initiale
    from .product import price_study_product_sync_amounts

    if work is None and work_item.price_study_work:
        price_study_product_sync_amounts(request, work_item.price_study_work)
    return True


def price_study_work_item_sync_quantities(
    request, work_item: PriceStudyWorkItem, work: Optional[PriceStudyWork] = None
):
    # Quantities are synced only if the quantity is inherited
    work_unit_quantity = work_item.work_unit_quantity
    if work_item.quantity_inherited:
        work_quantity = 1
        work = work or work_item.price_study_work
        if work:
            work_quantity = work.quantity
        work_item.total_quantity = work_unit_quantity * work_quantity
    else:
        work_item.total_quantity = work_unit_quantity
    request.dbsession.merge(work_item)
    return True


def price_study_work_item_on_before_commit(
    request,
    work_items: List[PriceStudyWorkItem],
    action: str,
    attributes: Optional[dict] = None,
):
    """
    :param list work_items: Les work_items sont liés au même PriceStudyWork

    :param str action: 'add'/'update'/'delete'
    """
    from .price_study import price_study_sync_with_task
    from .product import price_study_product_sync_amounts

    price_study = None
    work = work_items[0].price_study_work
    invoice_has_estimation = False
    if work:
        price_study = work.price_study
        invoice_has_estimation = (
            getattr(price_study.task, "estimation_id", None) is not None
        )

    need_sync_amounts = False
    for work_item in work_items:
        if action == "delete":
            need_sync_amounts = True
            if work and work_item in work.items:
                work.items.remove(work_item)
            if invoice_has_estimation:
                work.modified = True

        elif action == "add":
            if invoice_has_estimation:
                work_item.modified = True
            need_sync_amounts = True
        else:
            if attributes:
                for key in (
                    "mode",
                    "supplier_ht",
                    "ht",
                    "_margin_rate",
                    "work_unit_quantity",
                    "quantity_inherited",
                    "work_unit_ht",
                ):
                    if key in attributes:
                        need_sync_amounts = True
                        if invoice_has_estimation:
                            work_item.modified = True
                        break
            else:
                if invoice_has_estimation:
                    work_item.modified = True
                work_item.modified = True
                need_sync_amounts = True

        if need_sync_amounts:
            price_study_work_item_sync_quantities(request, work_item)
            price_study_work_item_sync_amounts(request, work_item)

    if need_sync_amounts:
        if work:
            price_study_product_sync_amounts(request, work)
            if price_study:
                price_study_sync_with_task(request, price_study)
