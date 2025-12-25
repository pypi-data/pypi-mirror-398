# import os
# import json

# from tests.utils import fixtures_path
# from hestia_earth.utils.cycle import get_cycle_emissions_calculation_status


# def test_get_cycle_emissions_calculation_status():
#     folder = os.path.join(fixtures_path, 'blank_node', 'calculation_status', 'cycle')

#     with open(f"{folder}/node.jsonld", encoding='utf-8') as f:
#         cycle = json.load(f)

#     with open(f"{folder}/emissions-emission-with-missing-inputs.json", encoding='utf-8') as f:
#         expected = json.load(f)

#     result = get_cycle_emissions_calculation_status(cycle)
#     assert result == expected
