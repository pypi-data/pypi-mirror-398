from typing import Union, List, Any
from hestia_earth.schema import TermTermType, NodeType

from .tools import get_dict_key

_LINKED_NODE_KEYS = {
    NodeType.SOURCE.value: ["name"],
    NodeType.TERM.value: ["name", "termType", "units"],
}


def linked_node(node: dict):
    """
    Return a minimal version of the node.

    Parameters
    ----------
    node: dict
        The Node, like a `Cycle` or a `Source` or a `Term`.

    Returns
    -------
    dict
        The node with only: `@type`, `@id`, `name`, `termType` and `units` fields.
    """
    node_type = node.get("@type", "")
    keys = ["@type", "@id"] + _LINKED_NODE_KEYS.get(node_type, [])
    return {key: node[key] for key in keys if key in node}


def find_term_match(
    values: list, term_id: str, default_val: Any = {}, match_params: dict = {}
):
    """
    Return the element in a list which matches the `Term` with the given `@id`.

    Parameters
    ----------
    values : list
        The list in which to search for. Example: `cycle['inputs']`.
    term_id : str
        The `@id` of the `Term`. Example: `sandContent`
    default_val : any
        The returned value if no match was found.
    match_params : dict
        Extra parameters used to match the specific term. Example: using a `site.@id`, or a `methodModel.@id`, etc.

    Returns
    -------
    dict
        The matching object.
    """

    def is_match(value: dict):
        return all(
            [value.get("term", {}).get("@id") == term_id]
            + [get_dict_key(value, k) == v for k, v in match_params.items()]
        )

    return next((v for v in values if is_match(v)), default_val)


def filter_list_term_type(
    values: list, term_type: Union[TermTermType, str, List[TermTermType], List[str]]
) -> list:
    """
    Filters the values by filtering by the `term.termType` property.

    Parameters
    ----------
    values : list
        The list to filter. Example: `cycle['inputs']`.
    term_type : TermTermType or List[TermTermType]
        The `termType` of the `Term`, or a list of `termType`. Example: `TermTermType.CROP`

    Returns
    -------
    list
        The filtered list.
    """
    term_types = [t for t in term_type] if isinstance(term_type, list) else [term_type]
    term_types = [(t if isinstance(t, str) else t.value) for t in term_types]
    return list(
        filter(lambda i: i.get("term", {}).get("termType") in term_types, values)
    )


def find_primary_product(cycle: dict) -> dict:
    """
    Return the `Product` of a `Cycle` which is set to `primary`, `None` if none present.

    Parameters
    ----------
    cycle : dict
        The JSON-LD of the `Cycle`.

    Returns
    -------
    dict
        The primary `Product`.
    """
    products = cycle.get("products", [])
    return (
        next((p for p in products if p.get("primary", False)), products[0])
        if len(products) > 0
        else None
    )


def _convert_m3_to_kg(value: float, **kwargs):
    return value * kwargs.get("density")


def _convert_m3_to_l(value: float, **kwargs):
    return value * 1000


def _convert_kg_to_m3(value: float, **kwargs):
    return value / kwargs.get("density")


def _convert_kg_to_l(value: float, **kwargs):
    return value / kwargs.get("density") * 1000


def _convert_liter_to_kg(value: float, **kwargs):
    return value * kwargs.get("density") / 1000


def _convert_liter_to_m3(value: float, **kwargs):
    return value / 1000


def _convert_mj_to_kwh(value: float, **kwargs):
    return value / 3.6


def _convert_kwh_to_mj(value: float, **kwargs):
    return value * 3.6


CONVERTERS = {
    "m3": {"kg": _convert_m3_to_kg, "L": _convert_m3_to_l},
    "kg": {"m3": _convert_kg_to_m3, "L": _convert_kg_to_l},
    "L": {"kg": _convert_liter_to_kg, "m3": _convert_liter_to_m3},
    "kWh": {"MJ": _convert_kwh_to_mj},
    "MJ": {"kWh": _convert_mj_to_kwh},
}


def convert_value(value: float, from_unit: str, to_unit: str, **kwargs: dict) -> float:
    """
    Converts a value of unit into a different unit.
    Depending on the destination unit, additional arguments might be provided by name, see the list of parameters.

    Parameters
    ----------
    value
        The value to convert, usually a float or an integer.
    from_unit
        The unit the value is specified in.
    to_unit
        The unit the converted value should be.
    density
        Optional. When converting from a 2d unit to 3d or the opposite, a density is required.

    Returns
    -------
    float
        The converted value in the destination unit.
    """
    return CONVERTERS[from_unit][to_unit](value, **kwargs)
