from typing import Optional

from caerp.models.task.task import PostTTCLine


def post_ttc_line_on_before_commit(
    request, post_ttc_line: PostTTCLine, action: str, attributes: Optional[dict] = None
):
    """
    Handle actions before commit

    :param obj request: Pyramid request
    :param obj post_ttc_line: A PostTTCLine instance
    :param str state: A str (add/update/delete)
    :param dict attributes: The attributes that were recently modified (default None)
    """
    task = post_ttc_line.task

    if action == "delete":
        if task and post_ttc_line in task.post_ttc_lines:
            task.post_ttc_lines.remove(post_ttc_line)

    return post_ttc_line
