import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from sqlalchemy import distinct, func, select

from caerp.models.third_party import ThirdParty
from caerp.utils.apigouv import call_api_gouv_enterprise, clean_api_string

logger = logging.getLogger(__name__)

API_GOUV_ENTREPRISE_URL = "https://recherche-entreprises.api.gouv.fr/search"


def get_third_parties_from_siren(request, siren: str, _class=ThirdParty) -> list:
    """
    Return list of third party instances that match the given SIRET

    If '_class' is set to 'Customer' or 'Supplier' instead of 'ThirdParty'
    results will be filtered by the given type
    """
    return (
        request.dbsession.execute(
            select(_class)
            .where(_class.siret.like(f"{siren}%"))
            .order_by(_class.registration.asc(), _class.city.asc())
        )
        .scalars()
        .all()
    )


def get_cae_third_parties_sirens(request, _class=ThirdParty) -> list:
    """
    Return a list with all the distinct third parties SIRET used in the CAE

    If '_class' is set to 'Customer' or 'Supplier' instead of 'ThirdParty'
    results will be filtered by the given type
    """
    query = select(distinct(func.substr(_class.siret, 1, 9).label("sirent"))).filter(
        _class.siret != "", _class.siret.is_not(None)
    )
    return request.dbsession.execute(query).scalars().all()


def get_unique_third_party_attribute_by_siren(
    request, siren: str, attribute: str, _class=ThirdParty
) -> Optional[str]:
    """
    Return the unique value of a given attribute for the third party with the given SIREN

    If there are multiple results, we return None

    If '_class' is set to 'Customer' or 'Supplier' instead of 'ThirdParty'
    results will be filtered by the given type
    """
    try:
        return request.dbsession.execute(
            select(distinct(getattr(_class, attribute))).filter(
                _class.siret.like(f"%{siren}")
            )
        ).scalar_one()
    except Exception:
        return None


@dataclass
class CompanyData:
    siren: str
    siret: str
    company_name: str
    address: str
    zip_code: str
    city: str
    city_code: str
    country: str
    country_code: str
    additional_address: Optional[str] = None
    function: Optional[str] = None
    lastname: Optional[str] = None
    firstname: Optional[str] = None


def _get_company_data_from_siege_gouv_data(api_data: dict) -> CompanyData:
    """
    Build company data using siege (headquarters) information from API response
    """
    siege = api_data.get("siege", {})

    # Build address from components
    address_parts = [
        clean_api_string(siege.get("numero_voie", "")),
        clean_api_string(siege.get("type_voie", "")),
        clean_api_string(siege.get("libelle_voie", "")),
    ]
    address = " ".join(part for part in address_parts if part).strip()

    # Get country information
    country = clean_api_string(siege.get("libelle_pays_etranger", ""))
    country_code = clean_api_string(siege.get("code_pays_etranger", ""))

    if not country:
        country = "FRANCE"
        country_code = "99100"

    # Get dirigeant information
    dirigeant_data = _get_dirigeant_from_gouv_data(api_data)

    company_data = CompanyData(
        siren=api_data.get("siren", ""),
        siret=siege.get("siret", ""),
        company_name=clean_api_string(api_data.get("nom_complet", "")),
        address=address,
        additional_address=clean_api_string(siege.get("complement_adresse", "")),
        zip_code=clean_api_string(siege.get("code_postal", "")),
        city=clean_api_string(siege.get("libelle_commune", "")),
        city_code=clean_api_string(siege.get("commune", "")),
        country=country,
        country_code=country_code,
        function=dirigeant_data.get("function", ""),
        lastname=dirigeant_data.get("lastname", ""),
        firstname=dirigeant_data.get("firstname", ""),
    )

    return company_data


def _get_dirigeant_from_gouv_data(api_data: dict) -> dict:
    """
    Extract dirigeant information from API response
    """
    dirigeants = api_data.get("dirigeants", [])
    dirigeants = [
        d for d in dirigeants if d.get("type_dirigeant") == "personne physique"
    ]

    if dirigeants:
        dirigeant = dirigeants[0]
        return {
            "lastname": clean_api_string(dirigeant.get("nom", "")),
            "firstname": clean_api_string(dirigeant.get("prenoms", "")),
            "function": clean_api_string(dirigeant.get("qualite", "")),
        }
    else:
        return {}


def _get_company_data_from_etablissements_gouv_data(
    api_data: dict,
) -> list[CompanyData]:
    """
    Build company_data for each établissement from API response
    """
    results = []

    for etablissement in api_data.get("matching_etablissements", []):
        if etablissement.get("ancien_siege"):
            continue

        name = (
            etablissement.get("nom_commercial")
            if etablissement.get("nom_commercial")
            else api_data.get("nom_complet", "")
        )

        commune = clean_api_string(etablissement.get("libelle_commune", ""))
        code_postal = clean_api_string(etablissement.get("code_postal", ""))
        adresse = clean_api_string(etablissement.get("adresse", ""))
        adresse = adresse.replace(f" {code_postal} {commune}", "")

        country = clean_api_string(etablissement.get("libelle_pays_etranger", ""))
        country_code = clean_api_string(etablissement.get("code_pays_etranger", ""))

        if not country:
            country = "FRANCE"
            country_code = "99100"

        company_data = CompanyData(
            siren=clean_api_string(api_data.get("siren", "")),
            siret=clean_api_string(etablissement.get("siret", "")),
            company_name=clean_api_string(name),
            address=adresse,
            additional_address="",  # Not available in etablissement data
            zip_code=code_postal,
            city=commune,
            city_code=clean_api_string(etablissement.get("commune", "")),
            country=country,
            country_code=country_code,
            function="",  # Not available in etablissement data
            lastname="",  # Not available in etablissement data
            firstname="",  # Not available in etablissement data
        )

        results.append(company_data)

    return results


def _api_result_to_company_data(
    api_result: dict, only_siege: bool = False
) -> List[CompanyData]:
    """
    Convert a result from api.gouv.fr to a dict with company_data
    """
    if not api_result.get("siren"):
        return []

    if only_siege:
        return [_get_company_data_from_siege_gouv_data(api_result)]
    # NB : Ici on exclue les anciens siège de la société
    etablissements = [
        e
        for e in api_result.get("matching_etablissements", [])
        if not e.get("ancien_siege")
    ]

    if etablissements and len(etablissements) > 1:
        # CAS 1 : Plusieurs établissements qui ne sont pas le siège
        data = _get_company_data_from_etablissements_gouv_data(api_result)
        return data
    elif (
        etablissements
        and len(etablissements) == 1
        and not etablissements[0].get("est_siege")
    ):
        # CAS 2 : Un seul établissement qui n'est pas le siège
        # Si on cherche avec le siret par exemple seul un établissement
        # ressort de la recherche
        data = _get_company_data_from_etablissements_gouv_data(api_result)
        return [data[0]] if data else []
    else:
        # Un seul établissement qui est le siège
        # Dans ce cas là les informations du siège sont utilisées car sûrement
        # plus complètes
        company_data = _get_company_data_from_siege_gouv_data(api_result)
        return [company_data]


def find_company_infos(
    request,
    siren: str,
    with_etablissements: bool = True,
    page_number: int = 1,
    only_siege: bool = False,
    filters: Optional[Dict[str, Any]] = None,
) -> list:
    """
    Find company data using the api.gouv.fr
    """
    results = []
    api_response = call_api_gouv_enterprise(
        siren,
        with_etablissements=with_etablissements,
        page_number=page_number,
        filters=filters,
    )
    if api_response is None or api_response.get("total_results") == 0:
        return results
    else:
        for api_result in api_response["results"]:
            if api_result.get("siren"):
                results.extend(
                    _api_result_to_company_data(api_result, only_siege=only_siege)
                )
        return results
