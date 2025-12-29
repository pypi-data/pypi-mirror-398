from typing import Optional

import colander

from caerp.models.task.task import Task
from caerp.services.tva import get_task_default_product, get_task_default_tva


def _get_context_task(context) -> Optional[Task]:
    """
    Renvoie la Task associée au contexte
    """
    result = None
    if hasattr(context, "get_task"):
        result = context.get_task()
    return result


@colander.deferred
def deferred_default_tva_id(node, kw):
    """
    Collect the default tva id
    """
    request = kw["request"]
    task = _get_context_task(request.context)

    tva = get_task_default_tva(request, task)
    if tva is not None:
        return tva.id
    else:
        return None


@colander.deferred
def deferred_default_product_id(node, kw):
    """
    Collect the default product id
    """
    request = kw["request"]

    task = _get_context_task(request.context)
    product = get_task_default_product(request, task)
    if product is not None:
        return product.id
    else:
        return None
