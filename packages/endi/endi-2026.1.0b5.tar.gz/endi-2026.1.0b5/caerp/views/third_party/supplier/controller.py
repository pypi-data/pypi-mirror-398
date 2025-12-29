from colanderalchemy import SQLAlchemySchemaNode

from caerp.forms.third_party.supplier import (
    get_company_supplier_schema,
    get_internal_supplier_schema,
)

from ..controller import ThirdPartyAddEditController


class SupplierAddEditController(ThirdPartyAddEditController):
    def get_company_schema(self) -> SQLAlchemySchemaNode:
        return get_company_supplier_schema()

    def get_internal_schema(self) -> SQLAlchemySchemaNode:
        return get_internal_supplier_schema(edit=self.edit)

    def get_default_type(self) -> str:
        return "company"
