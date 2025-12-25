from functools import reduce
from typing import Any
import requests
from io import StringIO
import pandas as pd

from .storage import _load_from_storage
from .request import request_url, web_url

_GLOSSARY_FOLDER = "glossary/lookups"
_memory = {}


def _memory_wrapper(key: str, func):
    global _memory  # noqa: F824
    _memory[key] = _memory[key] if key in _memory else func()
    return _memory[key]


def _read_csv(value: str) -> pd.DataFrame:
    return pd.read_csv(value, na_values=["-", ""])


def _read_csv_from_string(data: str) -> pd.DataFrame:
    return _read_csv(StringIO(data))


def is_missing_value(value):
    return pd.isna(value) or value is None or value == "" or value == "-"


def load_lookup(filepath: str, keep_in_memory: bool = False):
    """
    Import local lookup table as csv file into a `numpy.recarray`.

    Parameters
    ----------
    filepath : str
        The path of csv file on the local file system.
    keep_in_memory: bool
        Set to True if you want to store the file in memory for later use.

    Returns
    -------
    numpy.recarray
        The `numpy.recarray` converted from the csv content.
    """

    def load():
        return _read_csv(filepath)

    return _memory_wrapper(filepath, load) if keep_in_memory else load()


def _download_lookup_data(filename: str):
    filepath = f"{_GLOSSARY_FOLDER}/{filename}"

    def fallback():
        url = request_url(f"{web_url()}/{filepath}")
        data = requests.get(url).content.decode("utf-8")
        return data if data and "<html" not in data else None

    try:
        data = _load_from_storage(filepath, glossary=True)
        return data.decode("utf-8") if data else None
    except ImportError:
        return fallback()


def download_lookup(filename: str, keep_in_memory: bool = True):
    """
    Download lookup table from HESTIA as csv into a `numpy.recarray`.

    Parameters
    ----------
    filename : str
        The name on the file on the HESTIA lookup repository.
    keep_in_memory: bool
        Set to False if you do NOT want to store the file in memory for later use.
    build_index : bool
        Set to False to skip trying to build an index.

    Returns
    -------
    numpy.recarray
        The `numpy.recarray` converted from the csv content.
    """

    def load():
        data = _download_lookup_data(filename)
        return _read_csv_from_string(data) if data else None

    try:
        return _memory_wrapper(filename, load) if keep_in_memory else load()
    except Exception:
        return None


def column_name(key: str):
    """
    Deprecated. Columns are no longer renamed.
    """
    return key


def _parse_value(value: str):
    """Automatically converts the value to float or bool if possible"""
    try:
        return (
            True
            if str(value).lower() == "true"
            else False if str(value).lower() == "false" else float(value)
        )
    except Exception:
        return value


def _get_single_table_value(df: pd.DataFrame, col_match: str, col_match_with, col_val):
    filtered_df = df[df[col_match] == col_match_with]
    return None if filtered_df.empty else filtered_df[col_val].iloc[0]


def get_table_value(
    lookup: pd.DataFrame,
    col_match: str,
    col_match_with: str,
    col_val: Any,
    default_value="",
):
    """
    Get a value matched by one or more columns from a `numpy.recarray`.

    Parameters
    ----------
    lookup : DataFrame
        The value returned by the `download_lookup` function.
    col_match : str
        Which `column` should be used to find data in. This will restrict the rows to search for.
        Can be a single `str` or a list of `str`. If a list is used, must be the same length as `col_match_with`.
    col_match_with: str
        Which column `value` should be used to find data in. This will restrict the rows to search for.
    col_val: str
        The column which contains the value to look for.
    default_value : Any
        A value to return when none if found in the data.

    Returns
    -------
    str
        The value found or `None` if no match.
    """
    try:
        value = _get_single_table_value(lookup, col_match, col_match_with, col_val)
        return default_value if is_missing_value(value) else _parse_value(value)
    except Exception:
        return None


def find_term_ids_by(lookup: pd.DataFrame, col_match: str, col_match_with: str):
    """
    Find `term.id` values where a column matches a specific value.

    Parameters
    ----------
    lookup : DataFrame
        The value returned by the `download_lookup` function.
    col_match : str
        Which `column` should be used to find data in. This will restrict the rows to search for.
        Can be a single `str` or a list of `str`. If a list is used, must be the same length as `col_match_with`.
    col_match_with: str
        Which column `value` should be used to find data in. This will restrict the rows to search for.

    Returns
    -------
    list[str]
        The list of `term.id` that matched the expected column value.
    """
    filtered_df = lookup[lookup[col_match] == col_match_with]
    term_ids = (
        filtered_df["term.id"].unique().tolist()
        if "term.id" in filtered_df.columns
        else []
    )
    return list(map(str, term_ids))


def extract_grouped_data(data: str, key: str) -> str:
    """
    Extract value from a grouped data in a lookup table.

    Example:
    - with data: `Average_price_per_tonne:106950.5556;1991:-;1992:-`
    - get the value for `Average_price_per_tonne` = `106950.5556`

    Parameters
    ----------
    data
        The data to parse. Must be a string in the format `<key1>:<value>;<key2>:<value>`
    key
        The key to extract the data. If not present, `None` will be returned.

    Returns
    -------
    str
        The value found or `None` if no match.
    """
    grouped_data = (
        reduce(
            lambda prev, curr: {**prev, **{curr.split(":")[0]: curr.split(":")[1]}},
            data.split(";"),
            {},
        )
        if data is not None and isinstance(data, str) and len(data) > 1
        else {}
    )
    value = grouped_data.get(key)
    return None if is_missing_value(value) else _parse_value(value)


def extract_grouped_data_closest_date(data: str, year: int) -> str:
    """
    Extract date value from a grouped data in a lookup table.

    Example:
    - with data: `2000:-;2001:0.1;2002:0;2003:0;2004:0;2005:0`
    - get the value for `2001` = `0.1`

    Parameters
    ----------
    data
        The data to parse. Must be a string in the format `<key1>:<value>;<key2>:<value>`
    year
        The year to extract the data. If not present, the closest date data will be returned.

    Returns
    -------
    str
        The closest value found.
    """
    data_by_date = (
        reduce(
            lambda prev, curr: (
                {**prev, **{curr.split(":")[0]: curr.split(":")[1]}}
                if len(curr) > 0 and not is_missing_value(curr.split(":")[1])
                else prev
            ),
            data.split(";"),
            {},
        )
        if data is not None and isinstance(data, str) and len(data) > 1
        else {}
    )
    dist_years = list(data_by_date.keys())
    closest_year = (
        min(dist_years, key=lambda x: abs(int(x) - year))
        if len(dist_years) > 0
        else None
    )
    return (
        None if closest_year is None else _parse_value(data_by_date.get(closest_year))
    )


def lookup_term_ids(lookup: pd.DataFrame):
    """
    Get the `term.id` values from a lookup.

    Parameters
    ----------
    lookup : DataFrame
        The value returned by the `download_lookup` function.

    Returns
    -------
    list[str]
        The `term.id` values from the lookup.
    """
    return (
        list(map(str, lookup["term.id"].tolist()))
        if "term.id" in lookup.columns
        else []
    )


def lookup_columns(lookup: pd.DataFrame):
    """
    Get the columns from a lookup.

    Parameters
    ----------
    lookup : DataFrame
        The value returned by the `download_lookup` function.

    Returns
    -------
    list[str]
        The columns from the lookup.
    """
    return list(lookup.columns)
