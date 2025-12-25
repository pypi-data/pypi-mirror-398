from collections.abc import Iterable
from enum import Enum
from numpy import around
from numpy.typing import NDArray
from typing import Optional, Union


def calc_descriptive_stats(
    arr: NDArray,
    stats_definition: Union[Enum, str],
    axis: Optional[int] = None,
    decimals: int = 6,
) -> dict:
    """
    Calculate the descriptive stats for an array row-wise, round them to specified number of decimal places and return
    them formatted for a HESTIA node.

    Parameters
    ----------
    arr : NDArray
    stats_definition : Enum | str
    axis : int | None
    decimals : int

    Returns
    -------
    float
        The precision of the sample mean estimated by the Monte Carlo model as a floating point value with the same
        units as the estimated mean.
    """
    value = around(arr.mean(axis=axis), decimals)
    sd = around(arr.std(axis=axis), decimals)
    min_ = around(arr.min(axis=axis), decimals)
    max_ = around(arr.max(axis=axis), decimals)

    observations = (
        [arr.shape[0]] * arr.shape[1]
        if axis == 0
        else [arr.shape[1]] * arr.shape[0] if axis == 1 else [arr.size]
    )

    return {
        "value": list(value) if isinstance(value, Iterable) else [value],
        "sd": list(sd) if isinstance(sd, Iterable) else [sd],
        "min": list(min_) if isinstance(min_, Iterable) else [min_],
        "max": list(max_) if isinstance(max_, Iterable) else [max_],
        "statsDefinition": (
            stats_definition.value
            if isinstance(stats_definition, Enum)
            else stats_definition
        ),
        "observations": observations,
    }
