from typing import List, Optional, Union

from caerp.models.price_study.chapter import PriceStudyChapter
from caerp.models.price_study.product import PriceStudyProduct
from caerp.models.price_study.work import PriceStudyWork
from caerp.models.task.task import TaskLine

from .base import _base_price_study_product_from_sale_product, _ensure_tva
from .work_item import price_study_work_item_from_work_item


def price_study_product_from_sale_product(request, sale_product) -> PriceStudyProduct:
    instance: PriceStudyProduct = _base_price_study_product_from_sale_product(
        request, PriceStudyProduct, sale_product
    )  # type: ignore
    instance.supplier_ht = getattr(sale_product, "supplier_ht", None)
    instance.mode = getattr(sale_product, "mode", "ht")
    instance.base_sale_product = sale_product
    return instance


def price_study_work_from_sale_product(request, sale_product) -> PriceStudyWork:
    instance: PriceStudyWork = _base_price_study_product_from_sale_product(
        request, PriceStudyWork, sale_product
    )  # type: ignore
    if sale_product.title:
        instance.title = sale_product.title

    for item in sale_product.items:
        price_study_work_item_from_work_item(request, instance, item)
    return instance


def _price_study_product_sync_task_line_attributes(
    product: Union[PriceStudyProduct, PriceStudyWork], line: TaskLine
):
    """
    Sync the price study attributes to the task line
    """
    line.description = product.description

    line.quantity = product.quantity
    line.cost = product.ht
    line.unity = product.unity
    if product.tva:
        line.tva = product.tva
    line.product = product.product
    line.order = product.order
    return line


def _price_study_work_sync_task_line_attributes(
    work: PriceStudyWork, line: TaskLine
) -> TaskLine:
    line = _price_study_product_sync_task_line_attributes(work, line)
    line.description = "<strong>{}</strong>".format(work.title)
    if work.description:
        line.description += work.description
    # Fix #3348 : https://framagit.org/caerp/caerp/-/issues/3348
    # on utilise une quantité de 1
    line.quantity = 1
    line.cost = work.total_ht
    return line


def price_study_product_sync_task_line_attributes(
    product: Union[PriceStudyProduct, PriceStudyWork], line: TaskLine
) -> TaskLine:
    if isinstance(product, PriceStudyProduct):
        return _price_study_product_sync_task_line_attributes(product, line)
    elif isinstance(product, PriceStudyWork):
        return _price_study_work_sync_task_line_attributes(product, line)
    else:
        raise ValueError("Invalid product type")


def price_study_product_sync_with_task(
    request,
    product: Union[PriceStudyProduct, PriceStudyWork],
    chapter: PriceStudyChapter,
) -> TaskLine:
    """
    Ensure a TaskLine is created for the given product and set the attributes
    """
    _ensure_tva(request, product)
    if product.task_line is None:
        from caerp.models.task import TaskLine

        line = TaskLine()
        line.group = chapter.task_line_group
        line = price_study_product_sync_task_line_attributes(product, line)

        product.task_line = line
        request.dbsession.add(line)
        request.dbsession.merge(product)
        request.dbsession.flush()
    else:
        line = product.task_line
        line = price_study_product_sync_task_line_attributes(product, line)
        request.dbsession.merge(line)
        request.dbsession.flush()
    return line


def _price_study_base_product_on_delete(
    request, product: Union[PriceStudyProduct, PriceStudyWork]
) -> None:
    """
    _base_product_on_delete is called when a product is deleted.

    :param request: Description
    :param product: Description
    """
    from .price_study import price_study_sync_amounts, price_study_sync_with_task

    chapter = product.chapter
    if chapter:
        if product in chapter.products:
            chapter.products.remove(product)

        price_study = chapter.price_study
        if price_study:
            price_study_sync_amounts(request, price_study)
            price_study_sync_with_task(request, price_study)


def _price_study_work_on_before_commit(
    request,
    products: List[PriceStudyWork],
    action: str,
    attributes: Optional[dict] = None,
):
    from .price_study import price_study_sync_with_task

    price_study = None
    price_study = products[0].price_study
    need_sync_amounts = False
    invoice_has_estimation = False
    if price_study:
        invoice_has_estimation = (
            getattr(price_study.task, "estimation_id", None) is not None
        )

    for work in products:
        if action == "delete":
            _price_study_base_product_on_delete(request, work)
        elif action == "add":
            if invoice_has_estimation:
                work.modified = True
            _ensure_tva(request, work)
            need_sync_amounts = True
        else:
            # update
            if attributes:
                # On update les totaux uniquement si certains attributs ont été
                # modifiés
                for key in (
                    "quantity",
                    "margin_rate",
                    "tva_id",
                    "product_id",
                    "tva",
                    "unity",
                ):
                    if key in attributes:
                        need_sync_amounts = True
                        if invoice_has_estimation:
                            work.modified = True
                        break

                if not need_sync_amounts:
                    price_study_product_sync_with_task(request, work, work.chapter)
            else:
                if invoice_has_estimation:
                    work.modified = True
                need_sync_amounts = True

            if attributes and ("tva_id" in attributes or "tva" in attributes):
                _ensure_tva(request, work)

        if need_sync_amounts:
            price_study_work_sync_quantities(request, work)
            _price_study_work_sync_amounts(request, work)

    if need_sync_amounts and price_study:
        price_study_sync_with_task(request, price_study)


def _price_study_product_on_before_commit(
    request,
    products: List[PriceStudyProduct],
    action: str,
    attributes: Optional[dict] = None,
):
    """
    Docstring for product_on_before_commit

    :param action: Description
    :param attributes: Description
    """
    from .price_study import price_study_sync_with_task

    price_study = products[0].price_study
    invoice_has_estimation = False
    if price_study:
        invoice_has_estimation = (
            getattr(price_study.task, "estimation_id", None) is not None
        )

    for product in products:
        if action == "delete":
            need_sync_amounts = False
            _price_study_base_product_on_delete(request, product)

        elif action == "add":
            if invoice_has_estimation:
                product.modified = True
            _ensure_tva(request, product)
            need_sync_amounts = True

        elif action == "update":

            need_sync_amounts = False
            if attributes is not None:
                if "tva_id" in attributes or "tva" in attributes:
                    _ensure_tva(request, product)
                for key in (
                    "supplier_ht",
                    "ht",
                    "mode",
                    "margin_rate",
                    "quantity",
                    "mode",
                    "tva_id",
                    "tva",
                ):
                    if key in attributes:
                        if invoice_has_estimation:
                            product.modified = True
                        need_sync_amounts = True
                        break
                if not need_sync_amounts:
                    price_study_product_sync_with_task(request, product, None)
            else:
                if invoice_has_estimation:
                    product.modified = True
                need_sync_amounts = True

        if need_sync_amounts:
            price_study_product_sync_amounts(request, product)

    if need_sync_amounts and price_study:
        price_study_sync_with_task(request, price_study)


def price_study_product_on_before_commit(
    request,
    products: Union[List[PriceStudyProduct], List[PriceStudyWork]],
    action: str,
    attributes: Optional[dict] = None,
):
    if isinstance(products[0], PriceStudyProduct):
        _price_study_product_on_before_commit(request, products, action, attributes)
    else:
        _price_study_work_on_before_commit(request, products, action, attributes)


def _price_study_work_sync_amounts(request, work: PriceStudyWork, propagate=True):
    """
    Set all amounts on this work entry

    :param bool propagate: Should we propagate the syncing up ?
    """

    if not propagate:
        # On synchronise les enfants
        price_study_work_sync_quantities(request, work)

    work.ht = work.unit_ht()
    work.total_ht = work.compute_total_ht()
    request.dbsession.merge(work)

    return work


def price_study_work_sync_quantities(request, work: PriceStudyWork):
    """
    Sync all work items quantities and update amounts
    """
    from .work_item import (
        price_study_work_item_sync_amounts,
        price_study_work_item_sync_quantities,
    )

    for item in work.items:
        price_study_work_item_sync_quantities(request, item, work)
        price_study_work_item_sync_amounts(request, item, work)
    return work


def _price_study_product_sync_amounts(request, product):
    """
    Synchronize the amounts for the given product
    and fire the information up if propagate is True
    """
    product.ht = product.unit_ht()
    product.total_ht = product.compute_total_ht()
    request.dbsession.merge(product)
    return product


def price_study_product_sync_amounts(
    request,
    product: Union[PriceStudyProduct, PriceStudyWork],
    propagate=True,
):
    """
    Synchronize the amounts for the given product
    """

    if isinstance(product, PriceStudyProduct):
        _price_study_product_sync_amounts(request, product)
    else:
        _price_study_work_sync_amounts(request, product, propagate=propagate)

    if propagate:
        from .price_study import price_study_sync_amounts

        price_study_sync_amounts(request, product.chapter.price_study)
