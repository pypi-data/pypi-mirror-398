from typing import Type, Union

from caerp.models.price_study.product import PriceStudyProduct
from caerp.models.price_study.work import PriceStudyWork
from caerp.services.tva import get_task_default_tva_and_product


def _ensure_tva(request, product: Union[PriceStudyProduct, PriceStudyWork]):
    """
    Ensure product's tva and product match
    """
    if product.tva is None:
        task = product.price_study.task
        if task:
            tva, _product = get_task_default_tva_and_product(request, task)
            product.tva = tva
            product.product = _product
        else:
            tva, _product = get_task_default_tva_and_product(request)
            product.tva = tva
            product.product = _product
    elif product.product is not None and product.product.tva_id != product.tva_id:
        product.product_id = None


def _base_price_study_product_from_sale_product(
    request,
    factory: Union[Type[PriceStudyProduct], Type[PriceStudyWork]],
    sale_product,
):
    instance = factory(quantity=1)
    for field in (
        "ht",
        "description",
        "unity",
    ):
        setattr(instance, field, getattr(sale_product, field, None))

    if sale_product.company:
        margin_rate = sale_product.company.margin_rate
        if sale_product.company.use_margin_rate_in_catalog and sale_product.margin_rate:
            margin_rate = sale_product.margin_rate

        instance.margin_rate = margin_rate

    return instance
