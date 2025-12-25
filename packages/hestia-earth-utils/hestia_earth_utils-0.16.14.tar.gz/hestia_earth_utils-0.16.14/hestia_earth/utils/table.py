from functools import reduce
import numpy as np
import pandas as pd
from hestia_earth.schema import NodeType

# __package__ = "hestia_earth.utils" # required to run interactively in vscode
from .tools import flatten


def _replace_ids(df):
    # in columns, first letter is always lower case
    node_types = [e.value[0].lower() + e.value[1:] for e in NodeType]
    # add extra subvalues
    subvalues = ["source", "defaultSource", "site", "organisation", "cycle"]
    node_types = node_types + flatten(
        [v + "." + value for v in node_types] for value in subvalues
    )
    columns = reduce(
        lambda prev, curr: {**prev, curr + ".@id": curr + ".id"}, node_types, {}
    )
    return df.rename(columns=columns)


def _clean_term_columns(df):
    columns = ["name", "termType", "units"]
    cols = [c for c in df.columns if all([not c.endswith("." + v) for v in columns])]
    return df[cols]


def _replace_nan_values(df, col: str, columns: list):
    for index, row in df.iterrows():
        try:
            value = row[col]
            if np.isnan(value):
                for empty_col in columns:
                    df.loc[index, empty_col] = np.nan
        except TypeError:
            continue
    return df


def _empty_impact_na_values(df):
    impacts_columns = [c for c in df.columns if ".impacts."]
    impacts_values_columns = [c for c in impacts_columns if c.endswith(".value")]
    for col in impacts_values_columns:
        col_prefix = col.replace(".value", "")
        same_col = [c for c in impacts_columns if c.startswith(col_prefix) and c != col]
        _replace_nan_values(df, col, same_col)
    return df


def format_for_upload(filepath: str):
    """
    Format downloaded file for upload on HESTIA platform.
    Will replace all instances of `@id` to `id`, and drop the columns ending by `name`, `termType` or `units`.

    Parameters
    ----------
    filepath : str
        Path to the CSV to be formatted.

    Returns
    -------
    pandas.DataFrame
        Formatted pandas dataframe
    """
    df = pd.read_csv(filepath, index_col=None, na_values="")

    # replace @id with id for top-level Node
    df = _replace_ids(df)

    # drop all term columns that are not needed
    df = _clean_term_columns(df)

    # empty values for impacts which value are empty
    df = _empty_impact_na_values(df)

    return df
