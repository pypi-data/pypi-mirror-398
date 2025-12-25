import copy
import json
import re
import numpy as np
import pandas as pd
from hestia_earth.schema import UNIQUENESS_FIELDS, Term, NODE_TYPES
from hestia_earth.schema.utils.sort import get_sort_key, SORT_CONFIG

# __package__ = "hestia_earth.utils" # required to run interactively in vscode
from ..api import find_term_ids_by_names
from ._shared import (
    EXCLUDE_FIELDS,
    EXCLUDE_PRIVATE_FIELDS,
    _with_csv_formatting,
    _filter_emissions_not_relevant,
    _get_node_type_label,
    _get_node_type_from_label,
    nodes_to_df,
)


# We only want to pivot array items containing blank nodes
# Assume these are all fields with uniqueness fields not of type Node
def _get_blank_node_uniqueness_fields():
    filtered_uniqueness_fields = copy.deepcopy(UNIQUENESS_FIELDS)
    for node_type, array_fields in UNIQUENESS_FIELDS.items():
        for array_field in array_fields.keys():
            if SORT_CONFIG[node_type][array_field]["type"] in NODE_TYPES:
                del filtered_uniqueness_fields[node_type][array_field]
            # include `impactAssessment.@id` since it is not part of original uniqueness
            if "impactAssessment.id" in array_fields[array_field]:
                filtered_uniqueness_fields[node_type][array_field].append(
                    "impactAssessment.@id"
                )
    return filtered_uniqueness_fields


BLANK_NODE_UNIQUENESS_FIELDS = _get_blank_node_uniqueness_fields()


def _get_names(df):
    names = []
    for node_type, array_fields in BLANK_NODE_UNIQUENESS_FIELDS.items():
        nt_label = _get_node_type_label(node_type)
        for array_field, uniqueness_fields in array_fields.items():
            regex = rf"^{nt_label}\.{array_field}\.\d+"
            field_cols = df.filter(regex=regex).copy()
            deep_cols = [col for col in field_cols.columns if _get_deep_col(col)]
            if len(deep_cols):
                deep_df = field_cols[deep_cols].rename(columns=_get_deep_col)
                deep_df.columns = pd.MultiIndex.from_tuples(deep_df.columns)
                for _original_prefix, term in deep_df.T.groupby(level=0):
                    deep_names = _get_names(term.T.droplevel(0, axis=1))
                    names.extend(deep_names)
            for field in [f for f in uniqueness_fields if ".@id" in f]:
                name_field = field.replace(".@id", ".name")
                regex = rf"^{nt_label}\.{array_field}\.\d+\.{name_field}$"
                names_for_field = field_cols.filter(regex=regex).to_numpy().flatten()
                names.extend(names_for_field)
    valid_names = [name for name in set(names) if pd.notna(name)]
    return valid_names


def _get_name_id_dict(df):
    names = _get_names(df)
    return find_term_ids_by_names(sorted(names))


def _sort_keys(index):
    return [get_sort_key(col) for col in index]


def _sort_inplace(df):
    df.sort_index(axis=1, inplace=True, key=_sort_keys)


def _get_term_field(col_header):
    return ".".join(col_header.split(".")[3:])


def _get_term_index(col_header):
    return f"term.{col_header.split('.')[2]}"


def _group_by_term(termT, name_id_dict, uniqueness_fields):
    term = termT.T
    term.columns = map(_get_term_field, term.columns)

    # fill in any missing ids prior to grouping by id
    replace_fields = {
        f: f.replace(".@id", ".name") for f in uniqueness_fields if ".@id" in f
    }
    for idField, nameField in replace_fields.items():
        term[idField] = term.apply(
            lambda row: row.get(
                idField,
                name_id_dict.get(row.get(nameField, "default_id_value"), np.nan),
            ),
            axis=1,
        )
        term.drop(nameField, axis=1, inplace=True, errors="ignore")
    return term.T


def _format_col_field(field):
    return field.split(".")[0]


def _pivot_by_term(row_tuple, columns, fields_to_include):
    row = {k: v for k, v in zip(columns, row_tuple)}
    value_col_fields = []
    series = {}
    for col, append_to_value_col in fields_to_include.items():
        if pd.notna(row[col]):
            if append_to_value_col:
                value_col_fields.append(col)
            else:
                series[f"{row['term.@id']}.{col}"] = row[col]
    value_col_fields.sort()
    value_col_prefix = f"{row['term.@id']}{'+' if len(value_col_fields) else ''}"
    value_col_suffix = "+".join(
        [f"{_format_col_field(col)}[{row[col]}]" for col in value_col_fields]
    )
    value_col = f"{value_col_prefix}{value_col_suffix}.value"
    series[value_col] = row.get("value", np.nan)
    return series


def _is_not_term_field(col):
    deepest_field = col.split(".")[-1]
    is_name = (
        deepest_field == "name"
    )  # keep .name fields that are not being pivoted (because not a uniqueArrayItem)
    return is_name or deepest_field not in Term().fields


def _pivot_by_term_id_group(terms, uniqueness_fields):
    fields_to_include = {}
    for col in terms.columns:
        if col in uniqueness_fields:
            single_value = (
                terms[col].eq(terms[col].iloc[0]).all() or terms[col].isna().all()
            )
            append_to_value_col = (
                # depthUpper and depthLower are exceptions which go into value col no matter what
                col == "depthUpper"
                or col == "depthLower"
                or not single_value
            )
            fields_to_include[col] = append_to_value_col
        elif col != "value" and _is_not_term_field(col):
            fields_to_include[col] = False
    del fields_to_include["term.@id"]
    # print('terms->', terms, '\n')
    pivoted_arr = [
        _pivot_by_term(row_tuple, terms.columns, fields_to_include)
        for row_tuple in zip(*[terms[col] for col in terms])
    ]
    pivoted = pd.DataFrame.from_records(pivoted_arr, index=terms.index)
    # pivoted = terms.apply(_pivot_by_term, axis=1, fields_to_include=fields_to_include)
    # print('pivoted->', pivoted, '\n')
    return pivoted


def _pivot_row(row, uniqueness_fields):
    # unstack to group sets of values for each id, then stack to restore row
    # unstacking looks like this:
    #          term.@id dates	            startDate	value
    # term.0	gwp100	01-02-22;02-02-22	01-01-22	10;12
    # term.1	gwp100	01-02-22;02-02-22	02-01-22	20;30
    # term.2	someId	bla                 bla         1.0

    pivoted = (
        row.unstack()
        .groupby("term.@id", group_keys=False)
        .apply(_pivot_by_term_id_group, uniqueness_fields=uniqueness_fields)
    )
    return pivoted.stack(dropna=False)


def _get_deep_col(col):
    parent_type_label, field, idx, *rest = col.split(".")
    deep_col = ".".join(rest)
    match = re.search(r"\.\d+\.", deep_col)
    if match:
        node_type = (
            SORT_CONFIG.get(_get_node_type_from_label(parent_type_label))
            .get(field)
            .get("type")
        )
        original_prefix = ".".join([parent_type_label, field, idx])
        raised_deep_col = f"{_get_node_type_label(node_type)}.{deep_col}"
        return (original_prefix, raised_deep_col)
    else:
        return None


def _restore_deep_col_prefix(original_prefix):
    def do_restore(deep_col):
        original_suffix = deep_col.split(".")[1:]
        return f'{original_prefix}.{".".join(original_suffix)}'

    return do_restore


def _do_pivot(df_in, name_id_dict):
    for node_type, array_fields in BLANK_NODE_UNIQUENESS_FIELDS.items():
        nt_label = _get_node_type_label(node_type)
        for field in array_fields:
            regex = rf"^{nt_label}\.{field}\.\d+"
            uniqueness_fields = array_fields[field]
            field_cols = df_in.filter(regex=regex).copy()
            if field_cols.empty:
                continue
            deep_cols = [col for col in field_cols.columns if _get_deep_col(col)]
            if len(deep_cols):
                deep_df = field_cols[deep_cols].rename(columns=_get_deep_col)
                field_cols.drop(deep_cols, axis=1, inplace=True)
                deep_df.columns = pd.MultiIndex.from_tuples(deep_df.columns)
                for original_prefix, term in deep_df.T.groupby(level=0):
                    deep_pivoted = _do_pivot(term.T.droplevel(0, axis=1), name_id_dict)
                    deep_pivoted.rename(
                        columns=_restore_deep_col_prefix(original_prefix), inplace=True
                    )
                    field_cols = field_cols.merge(
                        deep_pivoted, left_index=True, right_index=True, how="outer"
                    )

            field_cols.dropna(axis=0, how="all", inplace=True)

            with_grouped_cols = (
                field_cols.T.groupby(_get_term_index, group_keys=True)
                .apply(
                    _group_by_term,
                    name_id_dict=name_id_dict,
                    uniqueness_fields=uniqueness_fields,
                )
                .T
            )

            pivoted_terms = with_grouped_cols.apply(
                _pivot_row, axis=1, uniqueness_fields=uniqueness_fields
            )

            # merge any duplicated columns caused by shuffled term positions
            # this operation coincidentally sorts the columns alphabetically
            pivoted_terms = (
                pivoted_terms.T.groupby(
                    level=pivoted_terms.columns.nlevels - 1, group_keys=False
                )
                .apply(lambda term: term.bfill().iloc[0, :])
                .T
            )

            pivoted_terms.columns = map(
                lambda col: f"{nt_label}.{field}.{col}", pivoted_terms.columns
            )
            df_in.drop(df_in.filter(regex=regex).columns, axis=1, inplace=True)
            df_in = df_in.merge(
                pivoted_terms, left_index=True, right_index=True, how="outer"
            )
    return df_in


def _format_and_pivot(df_in):
    df_in.replace("-", np.nan, inplace=True)
    df_in.dropna(how="all", axis=1, inplace=True)
    df_in.drop(columns="-", errors="ignore", inplace=True)
    name_id_dict = _get_name_id_dict(df_in)

    df_out = _do_pivot(df_in.copy(), name_id_dict)

    _sort_inplace(df_out)
    df_out = df_out.astype("object")
    df_out.fillna("-", inplace=True)
    return df_out


def pivot_nodes(nodes: list[dict]):
    """
    Pivot array of nodes in dict format (e.g under the 'nodes' key of a .hestia file)
    The nodes json should first be parsed using _with_csv_formatting for output as csv.
    """
    df_in = nodes_to_df(list(map(_filter_emissions_not_relevant, nodes)))

    regex = rf".*\.({'|'.join(EXCLUDE_FIELDS + EXCLUDE_PRIVATE_FIELDS)})$"
    df_in.drop(df_in.filter(regex=regex).columns, axis=1, inplace=True)
    df_out = _format_and_pivot(df_in)
    return df_out


def pivot_hestia_file(hestia_file: str):
    """
    Parse a .hestia file and pivot the nodes within.

    Parameters
    ----------
    hestia_file : str
        A .hestia file as string

    Returns
    -------
    pandas.DataFrame
        Pandas dataframe with pivoted array terms
    """
    parsed = json.loads(hestia_file, object_hook=_with_csv_formatting)
    nodes = parsed.get("nodes", [parsed])
    return pivot_nodes(nodes)


def pivot_csv(filepath):
    """
    Pivot terms belonging to array fields of nodes, indexing their value directly with
    the term ID and any distinguishing uniqueness fields in the following format:
    node.arrayField.termId+uniquenessField1[value]+uniquenessField2etc[value]

    Parameters
    ----------
    filepath : str
        Path to the CSV to be formatted.

    Returns
    -------
    pandas.DataFrame
        Pandas dataframe with pivoted array terms
    """
    df_in = pd.read_csv(filepath, index_col=None, dtype=object)
    df_out = _format_and_pivot(df_in)
    return df_out
