from sqlalchemy import func, select


def get_next_order(request, model_class):
    query = select(func.max(model_class.order)).where(model_class.active == True)
    result = request.dbsession.execute(query).scalar()
    if result is not None:
        return result + 1
    else:
        return 0
