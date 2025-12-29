from typing import List, Optional

from caerp.models.price_study.discount import PriceStudyDiscount
from caerp.models.task.task import DiscountLine


def price_study_discount_sync_with_task(
    request, discount: PriceStudyDiscount
) -> List[DiscountLine]:
    from caerp.models.task import DiscountLine

    result = []
    for tva, ht in discount.ht_by_tva().items():
        discount_line = DiscountLine(
            task=discount.price_study.task,
            tva=tva,
            amount=ht,
            description=discount.description,
        )
        request.dbsession.add(discount_line)
        request.dbsession.flush()
        result.append(discount_line)
    return result


def price_study_discount_on_before_commit(
    request,
    discount: PriceStudyDiscount,
    action: str,
    attributes: Optional[dict] = None,
):
    from .price_study import price_study_sync_amounts, price_study_sync_with_task

    price_study = discount.price_study
    sync = False
    if action == "delete":
        if discount in price_study.discounts:
            price_study.discounts.remove(discount)
        sync = True
    elif action == "add":
        sync = True
    elif action == "update":
        keys = ["tva_id", "amount", "percentage"]
        if attributes:
            for key in keys:
                if key in attributes:
                    sync = True
                    break
        else:
            sync = True

    if sync and price_study is not None:
        price_study_sync_amounts(request, price_study)
        price_study_sync_with_task(request, price_study)
