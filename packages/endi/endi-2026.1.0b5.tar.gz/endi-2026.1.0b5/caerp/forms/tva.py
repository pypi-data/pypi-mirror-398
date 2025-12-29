import colander

from caerp.services.tva import get_product_by_id, get_products, get_tvas


def get_tva_product_validator(request):
    def tva_product_validator_v2(self, node, value):
        """
        Validator checking that tva and product_id matches
        """
        product_id = value.get("product_id")
        if product_id is not None:
            tva_id = value.get("tva_id")
            if tva_id is not None:
                product = get_product_by_id(request, product_id)
                if product.tva_id != tva_id:
                    exc = colander.Invalid(
                        node, "Ce compte produit ne correspond pas à la TVA"
                    )
                    exc["product_id"] = (
                        "Le code produit doit correspondre à la                    "
                        " TVA"
                    )
                    raise exc

    return tva_product_validator_v2


def get_tva_id_product_id_schema(request, internal=False):
    class TvaIdProductIdSchema(colander.Schema):
        tva_id = colander.SchemaNode(
            colander.Integer(),
            title="Taux de TVA",
            validator=colander.OneOf(
                [
                    tva.id
                    for tva in get_tvas(request, attribute_name="id", internal=internal)
                ]
            ),
        )
        product_id = colander.SchemaNode(
            colander.Integer(),
            title="Identifiant du produit",
            validator=colander.OneOf(
                [
                    p.id
                    for p in get_products(
                        request, attribute_name="id", internal=internal
                    )
                ]
            ),
        )
        validator = get_tva_product_validator(request)

    schema = TvaIdProductIdSchema()
    return schema
