import datetime
import logging
from dataclasses import asdict
from typing import List

from stdnum.fr.siren import is_valid as is_valid_siren
from stdnum.fr.siret import is_valid as is_valid_siret

from caerp.models.third_party.third_party import ThirdParty
from caerp.services.third_party.third_party import (
    CompanyData,
    find_company_infos,
    get_third_parties_from_siren,
)

logger = logging.getLogger(__name__)


def update_third_party_accounting(request, siren, compte_cg, compte_tiers):
    """
    Update all third_parties with the given SIREN
    with the given accounting informations
    """
    for supplier in get_third_parties_from_siren(request, siren):
        if compte_cg is not None:
            supplier.compte_cg = compte_cg
        if compte_tiers is not None:
            supplier.compte_tiers = compte_tiers
        request.dbsession.merge(supplier)


def _update_third_party_from_company_data(
    request, third_party: ThirdParty, company_data: CompanyData
):
    mandatory_values = ["company_name", "siret"]
    for key in mandatory_values:
        setattr(third_party, key, getattr(company_data, key))

    for key, value in asdict(company_data).items():
        third_party_value = getattr(third_party, key, None)
        if value and not third_party_value:
            setattr(third_party, key, value)
    third_party.api_last_update = datetime.datetime.now()
    request.dbsession.merge(third_party)


def update_third_parties_from_siren_api(request, siren: str):
    """
    Update all third parties with the given SIREN with data from the government's API

    If the SIREN give no result or more than 1 result on the API nothing is modified
    """
    logger.debug(f"Updating third parties with SIREN {siren} from government's API...")
    # Collect distinct sirets
    siret_dict = {}
    for third_party in get_third_parties_from_siren(request, siren):
        siret_dict.setdefault(
            (third_party.siret, third_party.zip_code, third_party.city_code), []
        ).append(third_party)

    for (siret, zip_code, city_code), third_parties in siret_dict.items():
        if is_valid_siret(siret):
            logger.debug("SIRET valide")
            data = find_company_infos(request, siret, with_etablissements=True)
            if len(data) == 1:
                for third_party in third_parties:
                    _update_third_party_from_company_data(request, third_party, data[0])
            else:
                logger.error(f"> Résultats multiples pour le SIREN/SIRET {siret}")
        elif is_valid_siren(siret):
            logger.debug("SIREN valide mais pas un SIRET")
            filters = {}
            if zip_code:
                filters["code_postal"] = zip_code
            if city_code:
                filters["code_commune"] = city_code
            logger.debug(f"Filters : {filters}")
            data = find_company_infos(
                request, siret, with_etablissements=True, filters=filters
            )
            if len(data) == 1:
                for third_party in third_parties:
                    _update_third_party_from_company_data(request, third_party, data[0])
            else:
                logger.error(f"> Résultats multiples pour le SIREN/SIRET {siret}")
                continue

        else:
            logger.error(f"> SIREN/SIRET {siret} invalide")
            continue

    request.dbsession.flush()
