from sqlalchemy import (
    Column,
    String,
)
from sqlalchemy.ext.declarative import declared_attr

from caerp.utils.strings import format_civilite


class PostalAddressMixin:
    """
    Common fields and operations for a postal address
    """

    @declared_attr
    def address(cls):
        return Column(
            "address",
            String(255),
            info={"colanderalchemy": {"title": "Adresse"}},
            default="",
        )

    @declared_attr
    def additional_address(cls):
        return Column(
            "additional_address",
            String(255),
            info={"colanderalchemy": {"title": "Complément d'adresse"}},
            default="",
        )

    @declared_attr
    def zip_code(cls):
        return Column(
            "zip_code",
            String(20),
            info={"colanderalchemy": {"title": "Code postal"}},
            default="",
        )

    @declared_attr
    def city(cls):
        return Column(
            "city",
            String(255),
            info={"colanderalchemy": {"title": "Ville"}},
            default="",
        )

    @declared_attr
    def city_code(cls):
        return Column(
            "city_code",
            String(8),
            info={
                "colanderalchemy": {
                    "title": "Code INSEE",
                    "description": "Code INSEE de la commune (renseigné automatiquement d’après les informations ci-dessus)",
                }
            },
            default="",
        )

    @declared_attr
    def country(cls):
        return Column(
            "country",
            String(150),
            info={"colanderalchemy": {"title": "Pays"}},
            default="FRANCE",
        )

    @declared_attr
    def country_code(cls):
        return Column(
            "country_code",
            String(8),
            info={"colanderalchemy": {"title": "Code INSEE du Pays"}},
            default="99100",  # France
        )

    def get_postal_address(self):
        """
        Return text formatted postal address

        Format :
            {address}
            {additional_address}
            {zip_code} {city}
            {country}
        """
        postal_address = ""
        if self.address:
            postal_address += "{0}\n".format(self.address)
        if self.additional_address:
            postal_address += "{0}\n".format(self.additional_address)
        postal_address += "{0} {1}".format(self.zip_code, self.city)
        country = self.country
        if country is not None and country.lower() != "france":
            postal_address += "\n{0}".format(country)
        return postal_address


class ContactMixin:
    """
    Common fields for a contact (name and coordinates)
    """

    @declared_attr
    def civilite(cls):
        return Column(
            "civilite",
            String(10),
            info={"colanderalchemy": {"title": "Civilité"}},
            default="",
        )

    @declared_attr
    def lastname(cls):
        return Column(
            "lastname",
            String(255),
            info={"colanderalchemy": {"title": "Nom"}},
            default="",
        )

    @declared_attr
    def firstname(cls):
        return Column(
            "firstname",
            String(255),
            info={"colanderalchemy": {"title": "Prénom"}},
            default="",
        )

    @declared_attr
    def function(cls):
        return Column(
            "function",
            String(255),
            info={"colanderalchemy": {"title": "Fonction"}},
            default="",
        )

    @declared_attr
    def email(cls):
        return Column(
            "email",
            String(255),
            info={"colanderalchemy": {"title": "Adresse e-mail"}},
            default="",
        )

    @declared_attr
    def mobile(cls):
        return Column(
            "mobile",
            String(20),
            info={"colanderalchemy": {"title": "Téléphone portable"}},
            default="",
        )

    @declared_attr
    def phone(cls):
        return Column(
            "phone",
            String(50),
            info={"colanderalchemy": {"title": "Téléphone fixe"}},
            default="",
        )

    def get_contact_label(self):
        """
        Return text formatted contact label

        Format :
            {civilite_abr} {lastname} {firstname}
        """
        label = ""
        if self.lastname:
            label = self.lastname
            if self.civilite:
                label = "{0} {1}".format(format_civilite(self.civilite), label)
            if self.firstname:
                label += " {0}".format(self.firstname)
        return label
