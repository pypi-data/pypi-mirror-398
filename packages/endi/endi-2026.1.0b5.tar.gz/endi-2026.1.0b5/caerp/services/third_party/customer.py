from caerp.models.third_party import Customer

from .third_party import get_cae_third_parties_sirens, get_third_parties_from_siren


def get_customers_from_siren(request, siren: str) -> list:
    """
    Return list of customer instances that match the given SIREN
    """
    return get_third_parties_from_siren(request, siren, Customer)


def get_cae_customers_sirens(request) -> list:
    """
    Return a list with all the distinct customers SIREN used in the CAE
    """
    return get_cae_third_parties_sirens(request, Customer)
