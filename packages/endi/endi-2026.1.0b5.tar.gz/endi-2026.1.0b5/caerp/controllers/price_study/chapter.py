from typing import List, Optional

from caerp.models.price_study.chapter import PriceStudyChapter


def price_study_chapter_sync_with_task(request, chapter, sync_products=True):
    from .product import price_study_product_sync_with_task

    task = chapter.price_study.task
    if chapter.task_line_group_id is None:
        from caerp.models.task import TaskLineGroup

        group = TaskLineGroup(task=task)
        request.dbsession.add(group)
        chapter.task_line_group = group
        request.dbsession.merge(chapter)
    else:
        group = chapter.task_line_group
    if task:
        # On s'assure que la valeur est définie
        group.task_id = task.id
    group.title = chapter.title
    group.description = chapter.description
    group.order = chapter.order
    group.display_details = chapter.display_details

    request.dbsession.merge(group)
    request.dbsession.flush()
    if sync_products:
        for product in chapter.products:
            price_study_product_sync_with_task(request, product, chapter)
    return group


def price_study_chapter_on_before_commit(
    request,
    chapters: List[PriceStudyChapter],
    action: str,
    attributes: Optional[dict] = None,
):
    from .price_study import price_study_sync_amounts, price_study_sync_with_task

    price_study = chapters[0].price_study

    for chapter in chapters:
        # Cas du chargement depuis le catalogue
        if (
            action == "add"
            and price_study
            and price_study.task
            and getattr(price_study.task, "estimation_id", None)
        ):
            for product in chapter.products:
                product.modified = True

        if action == "delete":
            if chapter in price_study.chapters:
                price_study.chapters.remove(chapter)
            price_study_sync_amounts(request, price_study)
            price_study_sync_with_task(request, price_study)

        elif action in ("update", "add"):
            if action == "add":
                for product in chapter.products:
                    product.modified = True
            # Ordre / titre / description
            price_study_chapter_sync_with_task(request, chapter, sync_products=True)
