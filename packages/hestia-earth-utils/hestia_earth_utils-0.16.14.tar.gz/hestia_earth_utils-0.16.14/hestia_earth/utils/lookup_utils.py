from functools import lru_cache
import json
from hestia_earth.schema import SchemaType

from .lookup import _download_lookup_data, download_lookup, get_table_value
from .api import download_hestia
from .tools import non_empty_list, flatten

_ALLOW_ALL = "all"


@lru_cache()
def _allowed_mapping_data():
    data = _download_lookup_data("allowed-mapping.json")
    data = json.loads(data) if data else {}
    return data


def _is_site(site: dict):
    return site.get("@type", site.get("type")) == "Site" if site else None


def _get_sites(node: dict):
    site = node.get("site", node.get("cycle", {}).get("site"))
    other_sites = node.get("otherSites", node.get("cycle", {}).get("otherSites", []))
    return non_empty_list([site] + other_sites)


def _get_site_types(node: dict):
    sites = [node] if _is_site(node) else _get_sites(node)
    return non_empty_list([site.get("siteType") for site in sites])


def _get_site_measurements(node: dict):
    sites = [node] if _is_site(node) else _get_sites(node)
    return flatten([non_empty_list(site.get("measurements", [])) for site in sites])


def _blank_node_term_values(blank_nodes: list, key: str = "@id"):
    return non_empty_list([v.get("term", {}).get(key) for v in blank_nodes])


@lru_cache()
def _allowed_model_mapping(model: str, term_id: str, column: str):
    mapping = _allowed_mapping_data()
    value = (
        mapping.get(term_id, {}).get(model, {}).get(column)
        if mapping
        else get_table_value(
            download_lookup(
                f"{(download_hestia(term_id) or {}).get('termType')}-model-{column}.csv"
            ),
            "term.id",
            term_id,
            column,
        )
    )
    return (value or _ALLOW_ALL).split(";") if isinstance(value, str) else _ALLOW_ALL


def _is_model_value_allowed(model: str, term_id: str, values: list, lookup_column: str):
    allowed_values = _allowed_model_mapping(model, term_id, lookup_column)
    return any([_ALLOW_ALL in allowed_values, len(values) == 0]) or any(
        [value in allowed_values for value in values]
    )


def is_model_siteType_allowed(model: str, term_id: str, data: dict):
    values = _get_site_types(data)
    return _is_model_value_allowed(model, term_id, values, "siteTypesAllowed")


def is_model_product_id_allowed(model: str, term_id: str, data: dict):
    values = _blank_node_term_values(data.get("products", []))
    return _is_model_value_allowed(model, term_id, values, "productTermIdsAllowed")


def is_model_measurement_id_allowed(model: str, term_id: str, data: dict):
    values = _blank_node_term_values(data.get("measurements", []))
    return _is_model_value_allowed(model, term_id, values, "measurementIdsAllowed")


@lru_cache()
def _allowed_mapping(term_id: str, column: str):
    mapping = _allowed_mapping_data()
    value = (
        mapping.get(term_id, {}).get(column)
        if mapping
        else get_table_value(
            download_lookup(f"{(download_hestia(term_id) or {}).get('termType')}.csv"),
            "term.id",
            term_id,
            column,
        )
    )
    return (value or _ALLOW_ALL).split(";") if isinstance(value, str) else _ALLOW_ALL


def _is_term_value_allowed(term_id: str, values: list, lookup_column: str):
    allowed_values = _allowed_mapping(term_id, lookup_column)
    return any([_ALLOW_ALL in allowed_values, len(values) == 0]) or any(
        [value in allowed_values for value in values]
    )


def is_siteType_allowed(data: dict, term_id: str):
    values = _get_site_types(data)
    return _is_term_value_allowed(term_id, values, "siteTypesAllowed")


def is_site_measurement_id_allowed(data: dict, term_id: str):
    measurements = _get_site_measurements(data)
    values = _blank_node_term_values(measurements, key="@id")
    return _is_term_value_allowed(term_id, values, "siteMeasurementIdsAllowed")


def is_product_termType_allowed(data: dict, term_id: str):
    products = data.get("products", [])
    values = _blank_node_term_values(products, key="termType")
    return _is_term_value_allowed(term_id, values, "productTermTypesAllowed")


def is_product_id_allowed(data: dict, term_id: str):
    products = data.get("products", [])
    values = _blank_node_term_values(products, key="@id")
    return _is_term_value_allowed(term_id, values, "productTermIdsAllowed")


def is_input_termType_allowed(data: dict, term_id: str):
    inputs = data.get("inputs", [])
    values = _blank_node_term_values(inputs, key="termType")
    return _is_term_value_allowed(term_id, values, "inputTermTypesAllowed")


def is_input_id_allowed(data: dict, term_id: str):
    inputs = data.get("inputs", [])
    values = _blank_node_term_values(inputs, key="@id")
    return _is_term_value_allowed(term_id, values, "inputTermIdsAllowed")


def is_practice_termType_allowed(data: dict, term_id: str):
    practices = data.get("practices", [])
    values = _blank_node_term_values(practices, key="termType")
    return _is_term_value_allowed(term_id, values, "practiceTermTypesAllowed")


def is_practice_id_allowed(data: dict, term_id: str):
    practices = data.get("practices", [])
    values = _blank_node_term_values(practices, key="@id")
    return _is_term_value_allowed(term_id, values, "practiceTermIdsAllowed")


def is_transformation_termType_allowed(data: dict, term_id: str):
    is_transformation = (
        data.get("@type", data.get("type")) == SchemaType.TRANSFORMATION.value
    )
    values = non_empty_list([data.get("term", {}).get("termType")])
    return not is_transformation or _is_term_value_allowed(
        term_id, values, "transformationTermTypesAllowed"
    )


def is_transformation_id_allowed(data: dict, term_id: str):
    is_transformation = (
        data.get("@type", data.get("type")) == SchemaType.TRANSFORMATION.value
    )
    values = non_empty_list([data.get("term", {}).get("@id")])
    return not is_transformation or _is_term_value_allowed(
        term_id, values, "transformationTermIdsAllowed"
    )


def is_node_type_allowed(data: dict, term_id: str):
    values = non_empty_list([data.get("@type", data.get("type"))])
    return _is_term_value_allowed(term_id, values, "typesAllowed")


@lru_cache()
def is_in_system_boundary(term_id: str) -> bool:
    """
    Check if the term is included in the HESTIA system boundary.

    Parameters
    ----------
    term_id : str
        The term ID

    Returns
    -------
    bool
        True if the Term is included in the HESTIA system boundary, False otherwise.
    """
    mapping = _allowed_mapping_data()
    column = "inHestiaDefaultSystemBoundary"
    value = (
        mapping.get(term_id, {}).get(column)
        if mapping
        else get_table_value(
            download_lookup(f"{(download_hestia(term_id) or {}).get('termType')}.csv"),
            "term.id",
            term_id,
            column,
        )
    )
    # handle numpy bool from table value
    return not (not value)
