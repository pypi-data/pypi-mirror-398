from colander import Schema
from colanderalchemy import SQLAlchemySchemaNode
from typing import Dict

from caerp.models.third_party import ThirdParty
from caerp.models.config import Config
from caerp.utils.controller import BaseAddEditController
from caerp.utils.compat import Iterable


class ThirdPartyAddEditController(BaseAddEditController):
    """
    Base controller for add/edit a third party

    Must be override by each third party types
    """

    def get_individual_schema(self) -> SQLAlchemySchemaNode:
        return None

    def get_company_schema(self) -> SQLAlchemySchemaNode:
        return None

    def get_internal_schema(self) -> SQLAlchemySchemaNode:
        return None

    def _internal_active(self) -> bool:
        return Config.get_value("internal_invoicing_active", default=True, type_=bool)

    def get_third_party_type(self, submitted: dict) -> str:
        if self.edit:
            third_party_type = self.context.type
        else:
            third_party_type = submitted.get("type", "company")
            # On s'assure qu'on ne peut pas ajouter des tiers internes
            # si l'option est désactivée
            if third_party_type == "internal" and not self._internal_active():
                third_party_type = "company"
        return third_party_type

    def get_schema(self, submitted: dict) -> Schema:
        if "schema" not in self._cache:
            third_party_type = self.get_third_party_type(submitted)
            method = f"get_{third_party_type}_schema"
            self._cache["schema"] = getattr(self, method)()
        return self._cache["schema"]

    def get_schemas(self) -> Dict[str, Schema]:
        """
        Return available Colander Schemas for third parties

        :return: Liste des schémas colander
        :rtype: Dict[str, Schema]
        """
        schemas = {}
        individual_schema = self.get_individual_schema()
        if individual_schema:
            schemas["individual"] = individual_schema.bind(request=self.request)
        company_schema = self.get_company_schema()
        if company_schema:
            schemas["company"] = company_schema.bind(request=self.request)
        if self._internal_active():
            internal_schema = self.get_internal_schema()
            if internal_schema:
                schemas["internal"] = internal_schema.bind(request=self.request)
        return schemas

    def after_add_edit(
        self, third_party: ThirdParty, edit: bool, attributes: dict
    ) -> ThirdParty:
        """
        Post formatting Hook

        :param third_party: Current third_party (added/edited)
        :type third_party: third_party

        :param edit: Is it an edit form ?
        :type edit: bool

        :param attributes: Validated attributes sent to this view
        :type attributes: dict

        :return: The modified third_party
        :rtype: ThirdParty
        """
        if not edit:
            third_party.company = self.context
            third_party.type = self.get_third_party_type(attributes)
        return third_party

    def get_available_types(self) -> Iterable[Dict]:
        """
        Return available types for third parties creation
        """
        types = [
            {"value": "individual", "label": "Personne physique"},
            {"value": "company", "label": "Personne morale"},
        ]
        if self._internal_active():
            types.append({"value": "internal", "label": "Enseigne de la CAE"})
        return types

    def get_default_type(self) -> str:
        """
        Return the third_party type to provide by default

        :return: The name of the type
        :rtype: str
        """
        return "individual"
