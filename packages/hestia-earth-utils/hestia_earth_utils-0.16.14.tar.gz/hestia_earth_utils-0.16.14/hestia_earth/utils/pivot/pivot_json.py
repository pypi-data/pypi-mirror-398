import json
from hestia_earth.schema import UNIQUENESS_FIELDS, Term, NODE_TYPES
from hestia_earth.schema.utils.sort import SORT_CONFIG
from flatten_json import flatten, unflatten_list
from collections import defaultdict
from copy import deepcopy

from hestia_earth.utils.pipeline import _node_type
from ._shared import (
    EXCLUDE_FIELDS,
    EXCLUDE_PRIVATE_FIELDS,
    _with_csv_formatting,
    _filter_emissions_not_relevant,
    _filter_zero_values,
)

pivot_exclude_fields = Term().fields
pivot_exclude_fields.update(
    {k: "" for k in EXCLUDE_FIELDS} | {k: "" for k in EXCLUDE_PRIVATE_FIELDS}
)

term_exclude_fields = Term().fields
del term_exclude_fields["name"]
term_exclude_fields.update({k: "" for k in EXCLUDE_PRIVATE_FIELDS})

include_all_unique_keys = ["emissions", "emissionsResourceUse"]

# Treat properties uniqueness fields as special case for now
PROPERTIES_VIRTUAL_UNIQUENESS_FIELD = "propertyValues"
ADAPTED_UNIQUENESS_FIELDS = deepcopy(UNIQUENESS_FIELDS)
for node_type, array_fields in UNIQUENESS_FIELDS.items():
    for array_field, uniqueness_fields in array_fields.items():
        if (
            "properties.term.@id" in uniqueness_fields
            and "properties.value" in uniqueness_fields
        ):
            uniqueness_fields.append(PROPERTIES_VIRTUAL_UNIQUENESS_FIELD)
            ADAPTED_UNIQUENESS_FIELDS[node_type][array_field] = [
                f
                for f in uniqueness_fields
                if f not in ("properties.term.@id", "properties.value")
            ]
        # include `impactAssessment.@id` since it is not part of original uniqueness
        if "impactAssessment.id" in array_fields[array_field]:
            ADAPTED_UNIQUENESS_FIELDS[node_type][array_field].append(
                "impactAssessment.@id"
            )


def _combine_node_ids(nodes: list):
    return {"@id": ";".join([node.get("@id", node.get("id")) for node in nodes])}


def _base_pivoted_value(key: str, value, is_top_level: bool):
    # handle list of Nodes
    return (
        (
            _combine_node_ids(value)
            if isinstance(value[0], dict) and value[0].get("@type") in NODE_TYPES
            else (
                json.dumps(value, separators=(",", ":"))
                if any([is_top_level, key in ["distribution"]])
                else value
            )
        )
        if isinstance(value, list)
        else value
    )


def _do_pivot(node, parent_node_type=None, parent_field=None, level=0):  # noqa: C901
    # print('\ninput node', level, node, '\n')
    node_type = _node_type(node)
    if node_type not in ADAPTED_UNIQUENESS_FIELDS:
        return node
    pivoted_node = {
        field: _base_pivoted_value(field, value, level == 0)
        for field, value in node.items()
        if all(
            [
                field not in ADAPTED_UNIQUENESS_FIELDS[node_type],
                node_type != "Term" or field not in term_exclude_fields,
                field not in EXCLUDE_PRIVATE_FIELDS,
            ]
        )
    }

    fields_to_pivot = [
        (field, uniqueness_fields)
        for field, uniqueness_fields in ADAPTED_UNIQUENESS_FIELDS[node_type].items()
        if field in node
    ]

    # print('\n', level, 'fields_to_pivot', fields_to_pivot)
    for field, uniqueness_fields in fields_to_pivot:
        include_all_unique_fields = field in include_all_unique_keys
        # print('\nbefore processing node field', level, field, node[field], '\n')
        # Compress lists of 'Node' nodes to dict with single @id key.
        # The compressed field matches uniqueness fields like cycle.emissions.inputs.@id.
        if node[field] and SORT_CONFIG[node_type][field]["type"] in NODE_TYPES:
            pivoted_node[field] = _combine_node_ids(node[field])
            # print('\nafter processing node field', level, field, pivoted_node[field], '\n')
            continue
        else:
            node[field] = [
                _do_pivot(
                    term,
                    parent_node_type=node_type,
                    parent_field=field,
                    level=level + 1,
                )
                for term in node[field]
            ]
        # print('\nafter processing node field', level, field, node[field], '\n')

        pivoted_field = defaultdict(dict)
        # by_idx
        # [{
        #   term.@id: gwp100,
        #   any.term.field: value
        #   value: 10
        # }, etc.]
        by_idx = [flatten(term, ".") for term in node[field] if term]
        if not by_idx:
            continue
        # by_term_id
        # {
        #   gwp100: {
        #       indexes: [1, 4, etc.]
        #       combined_fields { field: last_traversed_value }
        #   }
        # }
        # print('\n\nby_idx', level, field, by_idx, '\n')
        by_term_id = defaultdict(lambda: {"indexes": [], "combined_fields": {}})
        # build list of property id:value pairs when required
        properties = []
        is_properties_special_case = (
            parent_node_type
            and field == "properties"
            and PROPERTIES_VIRTUAL_UNIQUENESS_FIELD
            in ADAPTED_UNIQUENESS_FIELDS[parent_node_type][parent_field]
        )
        for idx, term in enumerate(by_idx):
            id_key = "term.@id"
            id = term[id_key]
            if is_properties_special_case:
                properties.append(f'{id}[{term.get("value")}]')
            by_term_id[id]["indexes"].append(idx)
            combined_fields = {
                k: v
                for k, v in term.items()
                if k not in by_term_id[id]["combined_fields"]
            }
            by_term_id[id]["combined_fields"].update(combined_fields)
        # print('by_term_id', level, field, by_term_id, '\n')

        for term_id, term_data in by_term_id.items():
            indexes = term_data["indexes"]
            del term_data["combined_fields"][id_key]
            # print('combined_fields', field, term_id, term_data['combined_fields'], '\n')
            fields_to_include = {
                k: include_all_unique_fields
                or any(
                    by_idx[idx].get(k) != by_idx[indexes[0]].get(k) for idx in indexes
                )
                for k in term_data["combined_fields"].keys()
                if k in uniqueness_fields
                or (k != "value" and k.split(".")[-1] not in pivot_exclude_fields)
            }
            # print('fields_to_include', level, field, term_id, fields_to_include, '\n')
            for idx in indexes:
                term = by_idx[idx]
                distingishing_field_fields = [
                    field
                    for field, not_unanimous in fields_to_include.items()
                    if field in uniqueness_fields
                    and (
                        # depthUpper and depthLower are exceptions which go into value col no matter what
                        field == "depthUpper"
                        or field == "depthLower"
                        or not_unanimous
                    )
                ]
                # print('distingishing_field_fields', level, field, term_id, distingishing_field_fields, '\n')
                # print('unanimous_fields', level, field, term_id, unanimous_fields, '\n')
                unanimous_fields = (
                    {}
                    if include_all_unique_fields
                    else {
                        field: term_data["combined_fields"][field]
                        for field, not_unanimous in fields_to_include.items()
                        if field not in distingishing_field_fields
                        and not not_unanimous
                        and field is not PROPERTIES_VIRTUAL_UNIQUENESS_FIELD
                    }
                )
                differentiated_fields = {
                    field: term[field]
                    for field, not_unanimous in fields_to_include.items()
                    if field not in distingishing_field_fields
                    and (include_all_unique_fields or not_unanimous)
                    and field in term
                }
                # print('differentiated_fields', level, field, term_id, differentiated_fields, '\n')

                if unanimous_fields:
                    pivoted_field[term_id].update(unflatten_list(unanimous_fields, "."))
                distingishing_field_fields.sort()
                value_field_suffix = "".join(
                    [
                        f"+{term_field.split('.')[0]}[{term.get(term_field)}]"
                        for term_field in distingishing_field_fields
                        if term.get(term_field)
                    ]
                )
                distingishing_field = f"{term_id}{value_field_suffix}"
                if "value" in term:
                    pivoted_field[distingishing_field]["value"] = term.get("value")
                else:
                    pivoted_field[distingishing_field] = pivoted_field[
                        distingishing_field
                    ]
                if differentiated_fields:
                    pivoted_field[distingishing_field].update(
                        unflatten_list(differentiated_fields, ".")
                    )
        pivoted_node[field] = pivoted_field
        if is_properties_special_case:
            pivoted_node[PROPERTIES_VIRTUAL_UNIQUENESS_FIELD] = ";".join(properties)
    return pivoted_node


def pivot_node(
    node: dict,
    include_emissions_not_relevant: bool = False,
    include_zero_values: bool = True,
):
    """
    Pivot single node in dict format parsed with object_hook=_with_csv_formatting
    """
    node = (
        node if include_emissions_not_relevant else _filter_emissions_not_relevant(node)
    )
    node = node if include_zero_values else _filter_zero_values(node)
    return _do_pivot(node)


def pivot_json_node(
    json_node: str,
    include_emissions_not_relevant: bool = False,
    include_zero_values: bool = True,
):
    """
    Pivot single schema-compliant unparsed json string node
    """
    node = json.loads(json_node, object_hook=_with_csv_formatting)
    return pivot_node(
        node,
        include_emissions_not_relevant=include_emissions_not_relevant,
        include_zero_values=include_zero_values,
    )


def pivot_hestia_file(hestia_file: str):
    """
    Pivot json array of schema-compliant nodes on 'nodes' key of unparsed json string
    """
    parsed = json.loads(hestia_file, object_hook=_with_csv_formatting)
    return pivot_nodes(parsed.get("nodes", []))


def pivot_nodes(
    nodes: list[dict],
    include_emissions_not_relevant: bool = False,
    include_zero_values: bool = True,
):
    """
    Pivot multiple nodes in dict format parsed with object_hook=_with_csv_formatting
    """
    return [
        pivot_node(
            node,
            include_emissions_not_relevant=include_emissions_not_relevant,
            include_zero_values=include_zero_values,
        )
        for node in nodes
    ]
