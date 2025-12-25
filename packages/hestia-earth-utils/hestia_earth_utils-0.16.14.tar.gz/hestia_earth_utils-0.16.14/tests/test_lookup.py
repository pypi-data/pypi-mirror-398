import pytest
import pandas as pd

from .utils import fixtures_path
from hestia_earth.utils.lookup import (
    load_lookup,
    get_table_value,
    find_term_ids_by,
    download_lookup,
    extract_grouped_data,
    extract_grouped_data_closest_date,
    _get_single_table_value,
    lookup_term_ids,
    lookup_columns,
)


def test_load_lookup_type():
    lookup = load_lookup(f"{fixtures_path}/lookup.csv")
    assert isinstance(lookup, pd.DataFrame)


@pytest.mark.parametrize(
    "col_match,col_match_with,col_val,expected",
    [
        ("Col1", "val10", "Col3", "val30"),
        ("Col1", "val10", "Col5", None),
        ("Col1", "val10", "Col4", ""),
    ],
)
def test_get_table_value(col_match, col_match_with, col_val, expected):
    lookup = load_lookup(f"{fixtures_path}/lookup.csv")
    assert get_table_value(lookup, col_match, col_match_with, col_val) == expected


def test_get_table_value_no_lookup():
    assert not get_table_value(None, "Col10", "val10", "Col3")


def test_get_table_value_default_value():
    lookup = load_lookup(f"{fixtures_path}/lookup.csv")
    assert get_table_value(lookup, "Col2", "val22", "Col1") == ""

    lookup = download_lookup("crop.csv")
    assert (
        get_table_value(lookup, "term.id", "genericCropSeed", "Plantation_density")
        == ""
    )
    assert (
        get_table_value(
            lookup, "term.id", "fixedNitrogen", "Combustion_Factor_crop_residue"
        )
        == ""
    )


def test_find_term_ids_by():
    lookup = download_lookup("crop.csv")
    assert "wheatGrain" in find_term_ids_by(
        lookup, "cropGroupingFAO", "Temporary crops"
    )


def test_handle_missing_float_value():
    filename = "measurement.csv"
    lookup = download_lookup(filename)
    assert get_table_value(lookup, "term.id", "rainfallPeriod", "maximum") == ""


def test_handle_missing_lookup_value():
    filename = "region-crop-cropGroupingFaostatProduction-price.csv"
    lookup = download_lookup(filename)
    assert get_table_value(lookup, "term.id", "GADM-CYP", "Sugar crops nes") is None


def test_extract_grouped_data_no_data():
    assert not extract_grouped_data("", "2000")
    assert not extract_grouped_data("-", "2000")


def test_extract_grouped_data():
    data = "Average_price_per_tonne:106950.5556;1991:-;1992:-"
    assert extract_grouped_data(data, "Average_price_per_tonne") == 106950.5556
    assert extract_grouped_data(data, "2010") is None


def test_extract_grouped_data_lookup():
    filename = "region-crop-cropGroupingFaostatProduction-price.csv"
    lookup = download_lookup(filename)
    data = get_table_value(lookup, "term.id", "GADM-NPL", "Chick peas, dry")
    assert extract_grouped_data(data, "2000") is None
    assert extract_grouped_data(data, "2012") is not None

    filename = "region-animalProduct-animalProductGroupingFAO-price.csv"
    lookup = download_lookup(filename)
    data = get_table_value(
        lookup, "term.id", "GADM-NPL", "Eggs from other birds in shell, fresh, n.e.c."
    )
    assert extract_grouped_data(data, "2000") is None
    assert extract_grouped_data(data, "2012") is not None


def test_get_single_table_value_float_values():
    filename = "ecoClimateZone.csv"
    lookup = download_lookup(filename)
    column = "STEHFEST_BOUWMAN_2006_N2O-N_FACTOR"
    assert _get_single_table_value(lookup, "ecoClimateZone", 11, column) == -0.3022


def test_extract_grouped_data_closest_date_no_data():
    assert not extract_grouped_data_closest_date("", 2000)
    assert not extract_grouped_data_closest_date("-", 2000)


def test_extract_grouped_data_closest_date():
    data = "2000:-;2001:0.1;2002:0.2;2003:0.3;2004:0.4;2005:0.5"
    assert extract_grouped_data_closest_date(data, 2000) == 0.1
    assert extract_grouped_data_closest_date(data, 2001) == 0.1
    assert extract_grouped_data_closest_date(data, 2020) == 0.5


def test_lookup_term_ids():
    assert "wheatGrain" in lookup_term_ids(download_lookup("crop.csv"))


def test_lookup_columns():
    assert "term.id" in lookup_columns(download_lookup("crop.csv"))


def test_get_data_advanced():
    lookup = download_lookup("liveAnimal.csv")
    value = get_table_value(
        lookup, "term.id", "sheepRam", "ratioCPregnancyNetEnergyPregnancyIpcc2019"
    )
    assert value == ""


def test_grouping_with_comma():
    lookup = download_lookup("animalProduct.csv")
    term_id = "meatChickenReadyToCookWeight"
    value = get_table_value(lookup, "term.id", term_id, "animalProductGroupingFAO")
    assert value == "Meat of chickens, fresh or chilled"
