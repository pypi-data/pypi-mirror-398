from hestia_earth.schema import SiteSiteType, TermTermType

from hestia_earth.utils.emission import (
    cycle_emissions_in_system_boundary,
    emissions_in_system_boundary,
)

class_path = "hestia_earth.utils.emission"


def test_cycle_emissions_in_system_boundary_cropland():
    cycle = {"site": {}}

    cycle["products"] = [
        {"term": {"@id": "wheatGrain", "termType": TermTermType.CROP.value}}
    ]
    cycle["site"]["siteType"] = SiteSiteType.CROPLAND.value
    term_ids = cycle_emissions_in_system_boundary(cycle)
    assert len(term_ids) > 50

    cycle["products"] = [
        {"term": {"@id": "ricePlantFlooded", "termType": TermTermType.CROP.value}}
    ]
    cycle["site"]["siteType"] = SiteSiteType.CROPLAND.value
    term_ids = cycle_emissions_in_system_boundary(cycle)
    assert len(term_ids) > 50

    # with inputs restriction, we should have less emissions
    cycle["inputs"] = [{"term": {"termType": "crop"}}]
    cycle["site"]["siteType"] = SiteSiteType.CROPLAND.value
    assert len(cycle_emissions_in_system_boundary(cycle)) < len(term_ids)


def test_cycle_emissions_in_system_boundary_animal_housing():
    cycle = {"site": {}}
    cycle["products"] = [
        {
            "term": {
                "@id": "meatBeefCattleLiveweight",
                "termType": TermTermType.ANIMALPRODUCT.value,
            }
        }
    ]
    cycle["site"]["siteType"] = SiteSiteType.ANIMAL_HOUSING.value
    term_ids = cycle_emissions_in_system_boundary(cycle)
    assert len(term_ids) > 20


def test_emissions_in_system_boundary():
    term_ids = emissions_in_system_boundary()
    assert len(term_ids) > 50
