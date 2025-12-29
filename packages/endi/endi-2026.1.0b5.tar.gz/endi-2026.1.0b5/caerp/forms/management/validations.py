import datetime

import colander
import deform

from caerp import forms
from caerp.forms.company import company_filter_node_factory
from caerp.forms.lists import BaseListsSchema
from caerp.forms.user import validator_filter_node_factory
from caerp.models.node import Node


def get_list_schema():
    schema = BaseListsSchema().clone()
    del schema["search"]
    del schema["page"]
    del schema["items_per_page"]

    # Mois
    month_node = forms.month_select_node(name="month", title="Mois")
    schema.insert(0, month_node)

    # Année
    def get_year_options(kw):
        years = []
        current_year = datetime.date.today().year
        for year in range(current_year - 10, current_year + 1):
            years.append(year)
        return years

    year_node = forms.year_select_node(
        name="year", query_func=get_year_options, title="Année"
    )
    schema.insert(1, year_node)

    # Validateur
    schema.insert(
        2,
        validator_filter_node_factory(name="user_id", title="Validateur"),
    )

    # Enseigne
    schema.insert(
        3,
        company_filter_node_factory(name="company_id"),
    )

    # Type
    type_options = [("all", "Tous")]
    for type in [
        "estimation",
        "invoice",
        "cancelinvoice",
        "expensesheet",
        "supplier_order",
        "supplier_invoice",
    ]:
        type_options.append((type, Node.NODE_LABELS[type]))
    type_node = colander.SchemaNode(
        colander.String(),
        name="type",
        title="Type",
        widget=deform.widget.SelectWidget(values=type_options),
        default="all",
        missing="all",
    )
    schema.insert(4, type_node)

    # Résultat
    result_options = [("all", "Tous"), ("valid", "Validé"), ("invalid", "Invalidé")]
    result_node = colander.SchemaNode(
        colander.String(),
        name="result",
        title="Résultat",
        widget=deform.widget.SelectWidget(values=result_options),
        default="all",
        missing="all",
    )
    schema.insert(5, result_node)

    return schema
