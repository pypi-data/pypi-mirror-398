import pandas as pd

from .cycle import get_cycle_emissions_calculation_status


def _emissions_color(row):
    color = (
        "red"
        if row["emissions-missing"] > 0
        else "yellow" if row["emissions-incomplete"] > 0 else "lightgreen"
    )
    return [f"background-color: {color}"] * len(row)


def _emissions_with_status(cycle: dict):
    emissions = get_cycle_emissions_calculation_status(cycle)
    all_emissions = emissions.keys()
    # an emission is missing if there is no value (ignore `missingInputs`)
    missing_emissions = set(
        [
            k
            for k, v in emissions.items()
            if len((set(v.keys()) - set(["missingInputs"]))) == 0
        ]
    )
    # an emission is incomplete if it has missing inputs
    incomplete_emissions = set(
        [
            k
            for k, v in emissions.items()
            if all([len(v.get("missingInputs", [])) > 0, k not in missing_emissions])
        ]
    )
    complete_emissions = set(
        [
            k
            for k, v in emissions.items()
            if all(
                [
                    len(v.get("missingInputs", [])) == 0,
                    len((set(v.keys()) - set(["missingInputs"]))) > 0,
                ]
            )
        ]
    )
    return {
        "emissions-total": len(all_emissions),
        "emissions-complete": len(complete_emissions),
        "emissions-incomplete": len(incomplete_emissions),
        "emissions-missing": len(missing_emissions),
        "emissions": emissions,
    }


def _handle_lists(df: pd.DataFrame, columns: list):
    for col in columns:
        df[col] = df[col].apply(lambda v: ";".join(v) if isinstance(v, list) else v)
    return df


def get_nodes_calculations_status_dataframe(nodes: list, file_format: str = "excel"):
    cycles_status = [
        {"id": cycle.get("@id") or cycle.get("id")} | _emissions_with_status(cycle)
        for cycle in nodes
        if (cycle.get("@type") or cycle.get("type")) == "Cycle"
    ]
    df = pd.json_normalize(cycles_status, errors="ignore")
    # convert list of inputs to semi-column strings
    list_columns = [
        col
        for col in df.columns
        if col.endswith(".inputs") or col.endswith(".missingInputs")
    ]
    df = _handle_lists(df, list_columns)
    return df.style.apply(_emissions_color, axis=1) if file_format == "excel" else df
