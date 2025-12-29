import logging
from typing import Any, Dict, Optional

import requests

API_GOUV_ENTREPRISE_URL = "https://recherche-entreprises.api.gouv.fr/search"

logger = logging.getLogger(__name__)


def _build_query_params(
    search: str,
    page_number: int = 1,
    with_etablissements: bool = False,
    filters: Optional[Dict[str, Any]] = None,
) -> dict:
    optional_infos = "siege"
    if with_etablissements:
        optional_infos += ",matching_etablissements,dirigeants"
    query_params = {
        "q": search,
        "page": page_number,
        "per_page": 25,
        "minimal": True,
        "include": optional_infos,
        "limite_matching_etablissements": 100,
    }
    if filters is not None:
        query_params.update(filters)
    return query_params


def clean_api_string(str) -> str:
    """
    Clean strings received by government's API
    Handle "Non difusible" companies
    """
    if str is None or str == "null" or str == "undefined":
        return ""
    return str.replace("[ND]", "").replace("[NON-DIFFUSIBLE]", "").strip()


def call_api_gouv_enterprise(
    siren_or_siret: str,
    with_etablissements: bool = False,
    page_number: int = 1,
    filters: Optional[Dict[str, Any]] = None,
) -> Optional[dict]:
    """
    Appel l'api de recherche d'entreprises sirene

    :param siren_or_siret: le siren ou le siret de l'entreprise (ou son nom)
    :param with_etablissements: True pour inclure les informations sur les établissements et les dirigeants
    :param page_number: la page de résultats à récupérer (par défaut 1)
    :param filters: les filtres à appliquer à la recherche

    filtres

        Voir
        https://www.data.gouv.fr/dataservices/api-recherche-dentreprises/
        pour une liste exhaustive des filtres

    """
    query_params = _build_query_params(
        siren_or_siret, page_number, with_etablissements=True, filters=filters
    )
    query_url = API_GOUV_ENTREPRISE_URL
    try:
        logger.info(f">  Send request : GET {query_url}, params={query_params}")
        response = requests.get(query_url, params=query_params)
    except requests.ConnectionError as e:
        logger.error(f"Unable to connect to {query_url}")
        logger.error(e)
    except requests.HTTPError as e:
        logger.error(e)
    else:
        logger.info(f"< Received HTTP {response.status_code} from {query_url}")
        if response.status_code == 429:
            logger.error("Too many requests, try again later")
        elif response.status_code == 200:
            json_response = response.json()
            logger.debug("  Response content :")
            logger.debug(json_response)
            return json_response
        else:
            logger.error("Unable to get data from API (check status code)")
    return None
