import json
import numpy as np
import pandas as pd
from hestia_earth.schema import SCHEMA_TYPES, NODE_TYPES, EmissionMethodTier
from flatten_json import flatten as flatten_json

from ..tools import list_sum


EXCLUDE_FIELDS = ["@type", "type", "@context"]
EXCLUDE_PRIVATE_FIELDS = [
    "added",
    "addedVersion",
    "updated",
    "updatedVersion",
    "aggregatedVersion",
    "_cache",
]


# assuming column labels always camelCase
def _get_node_type_label(node_type):
    return node_type[0].lower() + node_type[1:]


def _get_node_type_from_label(node_type):
    return node_type[0].upper() + node_type[1:]


def _is_blank_node(data: dict):
    node_type = data.get("@type") or data.get("type")
    return node_type in SCHEMA_TYPES and node_type not in NODE_TYPES


def _with_csv_formatting(dct):
    """
    Use as object_hook when parsing a JSON node: json.loads(node, object_hook=_with_csv_formatting).
    Ensures parsed JSON has field values formatted according to hestia csv conventions.
    """
    if "boundary" in dct:
        dct["boundary"] = json.dumps(dct["boundary"])
    for key, value in dct.items():
        if _is_scalar_list(value):
            dct[key] = ";".join([str(el) for el in value])
    return dct


def _is_scalar_list(value):
    if not isinstance(value, list):
        return False
    all_scalar = True
    for element in value:
        if not np.isscalar(element):
            all_scalar = False
            break
    return all_scalar


def _filter_not_relevant(blank_node: dict):
    return blank_node.get("methodTier") != EmissionMethodTier.NOT_RELEVANT.value


def _filter_emissions_not_relevant(node: dict):
    """
    Ignore all emissions where `methodTier=not relevant` to save space.
    """
    return node | (
        {
            key: list(filter(_filter_not_relevant, node[key]))
            for key in ["emissions", "emissionsResourceUse"]
            if key in node
        }
    )


def _filter_zero_value(blank_node: dict):
    value = blank_node.get("value")
    value = (
        list_sum(blank_node.get("value"), default=-1)
        if isinstance(value, list)
        else value
    )
    return value != 0


def _filter_zero_values(node: dict):
    """
    Ignore all blank nodes where `value=0` to save space.
    """
    return node | (
        {
            key: list(filter(_filter_zero_value, value))
            for key, value in node.items()
            if isinstance(value, list)
            and isinstance(value[0], dict)
            and _is_blank_node(value[0])
        }
    )


def nodes_to_df(nodes: list[dict]):
    nodes_flattened = [
        flatten_json(
            dict([(_get_node_type_label(node.get("@type", node.get("type"))), node)]),
            ".",
        )
        for node in nodes
    ]

    return pd.json_normalize(nodes_flattened)
