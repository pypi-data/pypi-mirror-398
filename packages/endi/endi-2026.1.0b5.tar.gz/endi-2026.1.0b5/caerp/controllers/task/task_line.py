import logging
from typing import List, Optional

from caerp.models.task.task import TaskLine

logger = logging.getLogger(__name__)


def taskline_on_before_commit(
    request, tasklines: List[TaskLine], action: str, attributes: Optional[dict] = None
):
    """
    Handle actions before commit

    :param obj request: Pyramid request
    :param str action: A str (add/update/delete)
    :param dict attributes: The attributes that were modified (default None)
    """
    should_sync = False
    task = tasklines[0].task
    invoice_with_estimation = False
    if task and getattr(task, "estimation_id", None):
        invoice_with_estimation = True

    for line in tasklines:
        if action in ("add", "update") and invoice_with_estimation:
            line.modified = True

        if action == "add":
            should_sync = True

        elif action == "update":
            if attributes:
                for field in ("cost", "mode", "tva_id", "quantity"):
                    if field in attributes:
                        should_sync = True
            else:
                should_sync = True
        elif action == "delete":
            group = line.group
            if group and line in group.lines:
                group.lines.remove(line)
            should_sync = True

    if should_sync and task:
        task.cache_totals(request)
    return tasklines
