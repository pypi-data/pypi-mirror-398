from numpy import array
from pytest import mark
from hestia_earth.schema import MeasurementStatsDefinition

from hestia_earth.utils.descriptive_stats import calc_descriptive_stats

EXPECTED_FLATTENED = {
    "value": [5],
    "sd": [2.581989],
    "min": [1],
    "max": [9],
    "statsDefinition": "simulated",
    "observations": [9],
}

EXPECTED_COLUMNWISE = {
    "value": [4, 5, 6],
    "sd": [2.44949, 2.44949, 2.44949],
    "min": [1, 2, 3],
    "max": [7, 8, 9],
    "statsDefinition": "simulated",
    "observations": [3, 3, 3],
}

EXPECTED_ROWWISE = {
    "value": [2, 5, 8],
    "sd": [0.816497, 0.816497, 0.816497],
    "min": [1, 4, 7],
    "max": [3, 6, 9],
    "statsDefinition": "simulated",
    "observations": [3, 3, 3],
}


@mark.parametrize(
    "axis, expected",
    [(None, EXPECTED_FLATTENED), (0, EXPECTED_COLUMNWISE), (1, EXPECTED_ROWWISE)],
    ids=["flattened", "columnwise", "rowwise"],
)
@mark.parametrize(
    "stats_definition",
    [MeasurementStatsDefinition.SIMULATED, "simulated"],
    ids=["Enum", "str"],
)
def test_calc_descriptive_stats(stats_definition, axis, expected):
    ARR = array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])

    result = calc_descriptive_stats(ARR, stats_definition, axis=axis)
    assert result == expected
