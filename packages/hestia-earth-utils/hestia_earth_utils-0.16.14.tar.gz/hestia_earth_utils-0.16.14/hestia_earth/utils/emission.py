from typing import List
from hestia_earth.schema import TermTermType

from .lookup import download_lookup, lookup_term_ids
from .lookup_utils import (
    is_in_system_boundary,
    is_siteType_allowed,
    is_site_measurement_id_allowed,
    is_product_termType_allowed,
    is_product_id_allowed,
    is_input_termType_allowed,
    is_input_id_allowed,
    is_practice_termType_allowed,
    is_practice_id_allowed,
    is_transformation_termType_allowed,
    is_transformation_id_allowed,
)


def emissions_in_system_boundary(
    termType: TermTermType = TermTermType.EMISSION,
) -> List[str]:
    """
    Get all emissions included in HESTIA system boundary.

    Returns
    -------
    List[str]
        List of emission IDs
    """
    lookup = download_lookup(f"{termType.value}.csv")
    # find all emissions in system boundary
    return list(filter(is_in_system_boundary, lookup_term_ids(lookup)))


def cycle_emission_is_in_system_boundary(cycle: dict):
    def filter_term(term_id: str):
        return is_in_system_boundary(term_id) and all(
            map(
                lambda check: check(cycle, term_id),
                [
                    is_siteType_allowed,
                    is_site_measurement_id_allowed,
                    is_product_termType_allowed,
                    is_product_id_allowed,
                    is_input_termType_allowed,
                    is_input_id_allowed,
                    is_practice_termType_allowed,
                    is_practice_id_allowed,
                    is_transformation_termType_allowed,
                    is_transformation_id_allowed,
                ],
            )
        )

    return filter_term


def cycle_emissions_in_system_boundary(
    cycle: dict, termType: TermTermType = TermTermType.EMISSION
):
    """
    Get all emissions relevant for the Cycle, included in HESTIA system boundary.

    Returns
    -------
    List[str]
        List of emission IDs
    """
    lookup = download_lookup(f"{termType.value}.csv")
    # find all emissions in system boundary
    return list(
        filter(cycle_emission_is_in_system_boundary(cycle), lookup_term_ids(lookup))
    )
