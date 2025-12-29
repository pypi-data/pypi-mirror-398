from typing import List, Optional

from caerp.models.task.task import TaskLineGroup


def tasklinegroup_on_before_commit(
    request,
    task_line_groups: List[TaskLineGroup],
    action: str,
    attributes: Optional[dict] = None,
):
    """
    Handle actions before commit

    :param obj request: Pyramid request
    :param obj task_line: A TaskLineGroup instance
    :param str action: A str (add/update/delete)
    :param dict attributes: The attributes that were recently modified
    (default None)
    """
    should_sync = False
    task = task_line_groups[0].task
    invoice_with_estimation = False
    if task and getattr(task, "estimation_id", None):
        invoice_with_estimation = True

    for group in task_line_groups:
        if action in ("add", "delete"):
            should_sync = True

        if action == "add" and invoice_with_estimation:
            # Cas du chargement depuis le catalogue
            for line in group.lines:
                line.modified = True

        elif action == "delete":
            if task and group in task.line_groups:
                task.line_groups.remove(group)

    if should_sync and task:
        task.cache_totals(request)
    return task_line_groups
