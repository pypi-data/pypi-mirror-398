from typing import List, Optional

from caerp.models.task.task import DiscountLine


def discountline_on_before_commit(
    request,
    discountlines: List[DiscountLine],
    action: str,
    attributes: Optional[dict] = None,
):
    """
    Handle actions before commit

    :param obj request: Pyramid request
    :param str action: A str (add/update/delete)
    :param dict attributes: The attributes that were recently modified
    (default None)
    """
    should_sync = False
    task = discountlines[0].task
    invoice_with_estimation = False
    if task and getattr(task, "estimation_id", None):
        invoice_with_estimation = True

    for line in discountlines:
        if action in ("add", "update") and invoice_with_estimation:
            line.modified = True

        if action == "add":
            should_sync = True
        elif action == "update":
            if attributes:
                for field in ("amount", "tva"):
                    if field in attributes:
                        should_sync = True
            else:
                should_sync = True

        elif action == "delete":
            if task and line in task.discounts:
                task.discounts.remove(line)
            should_sync = True

    if should_sync and task:
        task.cache_totals(request)
    return discountlines
