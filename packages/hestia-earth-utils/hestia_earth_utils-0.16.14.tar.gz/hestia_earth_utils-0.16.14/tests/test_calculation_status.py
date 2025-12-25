# import os
# import json

# from tests.utils import fixtures_path
# from hestia_earth.utils.calculation_status import _emissions_with_status, get_nodes_calculations_status_dataframe

# fixtures_folder = os.path.join(fixtures_path, 'calculation_status')


# def test_emissions_with_status():
#     with open(os.path.join(fixtures_folder, 'nodes.json')) as f:
#         nodes = json.load(f)

#     result = _emissions_with_status(nodes[0])
#     assert result == {
#         'emissions-total': 193,
#         'emissions-complete': 56,
#         'emissions-incomplete': 1,
#         'emissions-missing': 136,
#         'emissions': result['emissions']  # ignore
#     }

#     result = _emissions_with_status(nodes[1])
#     assert result == {
#         'emissions-total': 193,
#         'emissions-complete': 0,
#         'emissions-incomplete': 13,
#         'emissions-missing': 180,
#         'emissions': result['emissions']  # ignore
#     }


# def test_get_nodes_calculations_status_dataframe():
#     with open(os.path.join(fixtures_folder, 'nodes.json')) as f:
#         nodes = json.load(f)

#     expected = open(os.path.join(fixtures_folder, 'result.csv'), 'r').read()

#     df = get_nodes_calculations_status_dataframe(nodes, file_format='csv')
#     assert df.to_csv(None, index=None) == expected
