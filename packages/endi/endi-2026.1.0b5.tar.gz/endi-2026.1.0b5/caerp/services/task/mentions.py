from sqlalchemy import exists, select

from caerp.models.task.mentions import COMPANY_TASK_MENTION, CompanyTaskMention


def get_company_task_mentions(request, company_id):
    """
    Return the list of CompanyTaskMention configured by the current company
    """
    query = (
        select(CompanyTaskMention)
        .filter(
            CompanyTaskMention.company_id == company_id,
            CompanyTaskMention.active.is_(True),
        )
        .order_by(CompanyTaskMention.order)
    )
    return request.dbsession.execute(query).scalars().all()


def company_task_mention_is_used(request, company_task_mention_id):
    """
    Check if the given CompanyTaskMention is used by any task
    """
    query = select(exists(COMPANY_TASK_MENTION)).filter(
        COMPANY_TASK_MENTION.c.company_task_mention_id == company_task_mention_id
    )
    return request.dbsession.execute(query).scalar()
