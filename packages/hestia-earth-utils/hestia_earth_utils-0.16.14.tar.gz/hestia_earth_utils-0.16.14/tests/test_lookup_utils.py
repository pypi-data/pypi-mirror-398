from hestia_earth.schema import SiteSiteType

from hestia_earth.utils.lookup_utils import (
    is_model_siteType_allowed,
    is_model_product_id_allowed,
    is_model_measurement_id_allowed,
    is_siteType_allowed,
    # is_site_measurement_id_allowed,  # TODO: test when lookup is added
    is_input_id_allowed,
    is_input_termType_allowed,
    # is_practice_termType_allowed,  # TODO: test when lookup is added
    # is_practice_id_allowed,  # TODO: test when lookup is added
    is_product_id_allowed,
    is_product_termType_allowed,
    is_node_type_allowed,
    # is_transformation_termType_allowed,  # TODO: test when lookup is added
    # is_transformation_id_allowed,  # TODO: test when lookup is added
)


def test_is_model_siteType_allowed():
    model = "pooreNemecek2018"
    term_id = "netPrimaryProduction"

    site = {"siteType": SiteSiteType.POND.value}
    assert is_model_siteType_allowed(model, term_id, {"site": site}) is True

    site = {"siteType": SiteSiteType.CROPLAND.value}
    assert not is_model_siteType_allowed(model, term_id, {"site": site})


def test_is_model_product_id_allowed():
    model = "schmidt2007"
    term_id = "ch4ToAirWasteTreatment"

    node = {"products": [{"term": {"@id": "oilPalmMillEffluentWaste"}}]}
    assert is_model_product_id_allowed(model, term_id, node) is True

    node = {"products": [{"term": {"@id": "wheatGrain"}}]}
    assert not is_model_product_id_allowed(model, term_id, node)


def test_is_model_measurement_id_allowed():
    model = "ipcc2019"
    term_id = "organicCarbonPerHa"

    node = {"measurements": [{"term": {"@id": "mineralSoils"}}]}
    assert is_model_measurement_id_allowed(model, term_id, node) is True

    node = {"measurements": [{"term": {"@id": "organicSoils"}}]}
    assert not is_model_measurement_id_allowed(model, term_id, node)


def test_is_siteType_allowed():
    node = {"@type": "Site", "siteType": "cropland"}
    assert not is_siteType_allowed(node, "pastureGrass")

    node = {"otherSites": [{"@type": "Site", "siteType": "permanent pasture"}]}
    assert is_siteType_allowed(node, "pastureGrass") is True


def test_is_input_id_allowed():
    term_id = "noxToAirExcreta"

    node = {"inputs": [{"term": {"@id": "wheatGrain"}}]}
    assert is_input_id_allowed(node, term_id) is True


def test_is_input_termType_allowed():
    term_id = "noxToAirExcreta"

    node = {"inputs": [{"term": {"termType": "crop"}}]}
    assert not is_input_termType_allowed(node, term_id)

    node = {"inputs": [{"term": {"termType": "excreta"}}]}
    assert is_input_termType_allowed(node, term_id) is True


def test_is_product_id_allowed():
    term_id = "n2OToAirWasteTreatmentDirect"

    node = {"products": [{"term": {"@id": "wheatGrain"}}]}
    assert not is_product_id_allowed(node, term_id)

    node = {"products": [{"term": {"@id": "oilPalmFruit"}}]}
    assert is_product_id_allowed(node, term_id) is True


def test_is_product_termType_allowed():
    term_id = "ch4ToAirAquacultureSystems"

    node = {"products": [{"term": {"termType": "crop"}}]}
    assert not is_product_termType_allowed(node, term_id)

    node = {"products": [{"term": {"termType": "liveAquaticSpecies"}}]}
    assert is_product_termType_allowed(node, term_id) is True


def test_is_node_type_allowed():
    term_id = "ch4ToAirAquacultureSystems"

    assert not is_node_type_allowed({"type": "Site"}, term_id)

    assert is_node_type_allowed({"type": "Cycle"}, term_id) is True
