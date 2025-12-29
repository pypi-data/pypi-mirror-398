import os

from caerp.views import API_ROUTE, caerp_add_route

# /api/v1/price_studies/id
# /api/v1/price_studies/id/chapters
# /api/v1/price_studies/id/chapters/id
# /api/v1/price_studies/id/chapters/id/products
# /api/v1/price_studies/id/chapters/id/products/id
# /api/v1/price_studies/id/chapters/id/products/id/work_item
# /api/v1/price_studies/id/chapters/id/products/id/work_item/id


PRICE_STUDY_API_ROUTE = os.path.join(API_ROUTE, "price_studies")
PRICE_STUDY_ITEM_API_ROUTE = os.path.join(PRICE_STUDY_API_ROUTE, "{id}")

CHAPTER_API_ROUTE = os.path.join(PRICE_STUDY_ITEM_API_ROUTE, "chapters")
CHAPTER_ITEM_API_ROUTE = os.path.join(CHAPTER_API_ROUTE, "{cid}")
CHAPTER_ITEM_BULK_EDIT_API_ROUTE = os.path.join(CHAPTER_ITEM_API_ROUTE, "bulk_edit")

PRODUCT_API_ROUTE = os.path.join(CHAPTER_ITEM_API_ROUTE, "products")
PRODUCT_ITEM_API_ROUTE = os.path.join(PRODUCT_API_ROUTE, "{pid}")

DISCOUNT_API_ROUTE = os.path.join(PRICE_STUDY_ITEM_API_ROUTE, "discounts")
DISCOUNT_ITEM_API_ROUTE = os.path.join(DISCOUNT_API_ROUTE, "{pid}")

WORK_ITEMS_API_ROUTE = os.path.join(PRODUCT_ITEM_API_ROUTE, "work_items")
WORK_ITEMS_ITEM_API_ROUTE = os.path.join(WORK_ITEMS_API_ROUTE, "{wid}")


def includeme(config):
    for route in (
        PRICE_STUDY_ITEM_API_ROUTE,
        CHAPTER_API_ROUTE,
        DISCOUNT_API_ROUTE,
    ):
        caerp_add_route(
            config,
            route,
            traverse="/price_studies/{id}",
        )
    for route in (
        CHAPTER_ITEM_API_ROUTE,
        PRODUCT_API_ROUTE,
        CHAPTER_ITEM_BULK_EDIT_API_ROUTE,
    ):
        caerp_add_route(
            config,
            route,
            traverse="/price_study_chapters/{cid}",
        )
    caerp_add_route(
        config,
        PRODUCT_ITEM_API_ROUTE,
        traverse="/base_price_study_products/{pid}",
    )
    caerp_add_route(
        config,
        DISCOUNT_ITEM_API_ROUTE,
        traverse="/price_study_discounts/{pid}",
    )
    caerp_add_route(
        config,
        WORK_ITEMS_API_ROUTE,
        traverse="/base_price_study_products/{pid}",
    )
    caerp_add_route(
        config,
        WORK_ITEMS_ITEM_API_ROUTE,
        traverse="/price_study_work_items/{wid}",
    )
