from hestia_earth.schema import TermTermType

from .tools import flatten
from .blank_node import get_blank_nodes_calculation_status


def _extend_missing_inputs(value: dict, input_ids: set):
    included_inputs = set(flatten([v.get("inputs", []) for v in value.values()]))
    missing_inputs = input_ids - included_inputs
    return {"missingInputs": sorted(list(missing_inputs))} if missing_inputs else {}


def get_cycle_emissions_calculation_status(cycle: dict):
    """
    Get calculation status for Cycle emissions included in the HESTIA system boundary.

    Parameters
    ----------
    cycle : dict
        The dictionary representing the Cycle.

    Returns
    -------
    dict
        A dictionary of `key:value` pairs representing each emission in the system boundary,
        and the resulting calculation as value, containing the recalculated `value`, `method` and `methodTier`.
        Note: if a calculation fails for an emission, the `value` is an empty dictionary.
    """
    status = get_blank_nodes_calculation_status(
        cycle, "emissions", TermTermType.EMISSION
    )
    input_ids = set([v.get("term", {}).get("@id") for v in cycle.get("inputs", [])])
    return {
        k: v | (_extend_missing_inputs(v, input_ids) if "InputsProduction" in k else {})
        for k, v in status.items()
    }
