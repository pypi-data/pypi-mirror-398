from collections.abc import Iterable
from typing import Optional, Union, Any
from enum import Enum
from functools import reduce
from statistics import mode, mean
from hestia_earth.schema import TermTermType

from .lookup import download_lookup, get_table_value
from .tools import non_empty_list, non_empty_value, flatten
from .emission import cycle_emissions_in_system_boundary
from .model import filter_list_term_type


def get_lookup_value(blank_node: dict, column: str):
    term = blank_node.get("term", {})
    table_name = f"{term.get('termType')}.csv" if term else None
    value = (
        get_table_value(download_lookup(table_name), "term.id", term.get("@id"), column)
        if table_name
        else None
    )
    return value


def group_by_keys(values: list, group_keys: list = ["term"]):
    def node_value(value):
        return (
            value.get("@id")
            if isinstance(value, dict)
            else list(map(node_value, value)) if isinstance(value, list) else value
        )

    def run(group: dict, node: dict):
        group_key = "-".join(
            flatten(non_empty_list([node_value(node.get(v)) for v in group_keys]))
        )
        group[group_key] = group.get(group_key, []) + [node]
        return group

    return reduce(run, values, {})


class ArrayTreatment(Enum):
    """
    Enum representing different treatments for arrays of values.
    """

    MEAN = "mean"
    MODE = "mode"
    SUM = "sum"
    FIRST = "first"
    LAST = "last"


def _should_run_array_treatment(value):
    return isinstance(value, Iterable) and len(value) > 0


DEFAULT_ARRAY_TREATMENT = ArrayTreatment.MEAN
ARRAY_TREATMENT_TO_REDUCER = {
    ArrayTreatment.MEAN: lambda value: (
        mean(non_empty_list(value)) if _should_run_array_treatment(value) else None
    ),
    ArrayTreatment.MODE: lambda value: (
        mode(non_empty_list(value)) if _should_run_array_treatment(value) else None
    ),
    ArrayTreatment.SUM: lambda value: (
        sum(non_empty_list(value)) if _should_run_array_treatment(value) else None
    ),
    ArrayTreatment.FIRST: lambda value: (
        value[0] if _should_run_array_treatment(value) else None
    ),
    ArrayTreatment.LAST: lambda value: (
        value[-1] if _should_run_array_treatment(value) else None
    ),
}
"""
A dictionary mapping ArrayTreatment enums to corresponding reducer functions.
"""


def _retrieve_array_treatment(
    node: dict,
    is_larger_unit: bool = False,
    default: ArrayTreatment = ArrayTreatment.MEAN,
) -> ArrayTreatment:
    """
    Retrieves the array treatment for a given node.

    Array treatments are used to reduce an array's list of values into
    a single value. The array treatment is retrieved from a lookup on
    the node's term.

    Parameters
    ----------
    node : dict
        The dictionary representing the node.
    is_larger_unit : bool, optional
        Flag indicating whether to use the larger unit lookup, by default `False`.
    default : ArrayTreatment, optional
        Default value to return if the lookup fails, by default `ArrayTreatment.MEAN`.

    Returns
    -------
    ArrayTreatment
        The retrieved array treatment.

    """
    ARRAY_TREATMENT_LOOKUPS = ["arrayTreatmentLargerUnitOfTime", "arrayTreatment"]
    lookup = (
        ARRAY_TREATMENT_LOOKUPS[0] if is_larger_unit else ARRAY_TREATMENT_LOOKUPS[1]
    )

    lookup_value = get_lookup_value(node, lookup)

    return next(
        (treatment for treatment in ArrayTreatment if treatment.value == lookup_value),
        default,
    )


def get_node_value(
    node: dict,
    key: str = "value",
    is_larger_unit: bool = False,
    array_treatment: Optional[ArrayTreatment] = None,
    default_array_treatment: Optional[ArrayTreatment] = ArrayTreatment.MEAN,
    default: Any = 0,
) -> Union[float, bool]:
    """
    Get the value from the dictionary representing the node,
    applying optional array treatment if the value is a list.

    Parameters
    ----------
    node : dict
        The dictionary representing the node.
    key : str
        The key to retrieve the value for. Will use `value` by default.
    is_larger_unit : bool, optional
        A flag indicating whether the unit of time is larger, by default `False`.
    array_treatment : ArrayTreatment, optional
        Override any array treatment set in the term lookup.
    default_array_treatment : ArrayTreatment, optional
        The default treatment to use when the term has none, and `array_treatment` is not set
    default : any
        The default value, if no value is found or it could not be parsed.

    Returns
    -------
    float | bool
        The extracted value from the node.
    """
    value = (node or {}).get(key)

    reducer = (
        ARRAY_TREATMENT_TO_REDUCER[
            (
                array_treatment
                or _retrieve_array_treatment(
                    node, is_larger_unit=is_larger_unit, default=default_array_treatment
                )
            )
        ]
        if isinstance(value, list) and len(value) > 0
        else None
    )

    return (
        reducer(value)
        if reducer
        else (
            value
            if any(
                [
                    isinstance(value, float),
                    isinstance(value, int),
                    isinstance(value, bool),
                ]
            )
            else default if not non_empty_value(value) else value
        )
    )


_BLANK_NODE_GROUPING_KEYS = {TermTermType.EMISSION: ["methodModel"]}


def get_blank_nodes_calculation_status(
    node: dict, list_key: str, termType: TermTermType
):
    """
    Get calculation status for a Node and a list of Blank node.
    Example: get the calculation status for all emissions included in the HESTIA system boundary.

    Parameters
    ----------
    node : dict
        The dictionary representing the node.
    list_key : str
        The key where the blank nodes are contained. Example: `emissions`.
    termType : TermTermType
        The `term.termType` resitrction for blank nodes. Example for `list_key=emissions`: `TermTermType.EMISSION`.

    Returns
    -------
    dict
        A dictionary of `key:value` pairs representing each `term.@id` found in the blank nodes as key,
        and the resulting calculation as value, containing the recalculated `value`, `method` and `methodTier`.
        Note: if a calculation fails for a blank node, the `value` is an empty dictionary.
    """
    all_term_ids = cycle_emissions_in_system_boundary(node, termType=termType)
    blank_nodes = filter_list_term_type(node.get(list_key, []), termType)
    blank_nodes_by_term = group_by_keys(blank_nodes, ["term"])
    blank_nodes_grouping_keys = _BLANK_NODE_GROUPING_KEYS.get(termType) or []

    def blank_node_data(blank_nodes: list):
        value = get_node_value(
            {
                "term": blank_nodes[0].get("term"),
                "value": list(map(get_node_value, blank_nodes)),
            }
        )
        inputs = flatten(map(lambda v: v.get("inputs", []), blank_nodes))
        return {"value": value} | (
            {"inputs": sorted(list(map(lambda v: v.get("@id"), inputs)))}
            if inputs
            else {}
        )

    def map_blank_node(term_id: str):
        values = blank_nodes_by_term.get(term_id, [])
        grouped_blank_nodes = (
            group_by_keys(values, blank_nodes_grouping_keys)
            if blank_nodes_grouping_keys
            else {}
        )
        return (
            {}
            if not values
            else (
                {k: blank_node_data(v) for k, v in grouped_blank_nodes.items()}
                if grouped_blank_nodes
                else blank_node_data([values[0]])
            )
        )

    return {term_id: map_blank_node(term_id) for term_id in all_term_ids}
