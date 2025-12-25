import os

# import json
# from pytest import mark
# from hestia_earth.schema import TermTermType

from tests.utils import fixtures_path
from hestia_earth.utils.blank_node import (
    get_node_value,
    ArrayTreatment,
    # get_blank_nodes_calculation_status,
)

fixtures_folder = os.path.join(fixtures_path, "blank_node")
calculation_status_folder = os.path.join(fixtures_folder, "calculation_status")


def test_get_node_value():
    assert get_node_value(None) == 0

    blank_node = {"term": {"termType": "crop", "@id": "wheatGrain"}, "value": [10]}
    assert get_node_value(blank_node, "value", default=None) == 10

    blank_node = {"term": {"termType": "crop", "@id": "wheatGrain"}, "value": [0]}
    assert get_node_value(blank_node, "value", default=None) == 0

    blank_node = {"term": {"termType": "crop", "@id": "wheatGrain"}}
    assert get_node_value(blank_node, "value", default=None) is None

    blank_node = {"term": {"termType": "crop", "@id": "wheatGrain"}, "value": [10, 20]}
    assert get_node_value(blank_node, "value", default=None) == 30

    blank_node = {"term": {"termType": "crop", "@id": "wheatGrain"}, "value": True}
    assert get_node_value(blank_node, "value", default=None) is True

    blank_node = {"term": {"termType": "crop", "@id": "wheatGrain"}, "value": 10}
    assert get_node_value(blank_node, "value", default=None) == 10

    blank_node = {"term": {"termType": "crop", "@id": "wheatGrain"}, "value": None}
    assert get_node_value(blank_node, "value", default=None) is None

    blank_node = {"term": {"termType": "crop", "@id": "wheatGrain"}, "value": None}
    assert get_node_value(blank_node, "value", default=0) == 0

    blank_node = {
        "term": {"termType": "crop", "@id": "wheatGrain"},
        "value": [10, None, 20],
    }
    assert (
        get_node_value(blank_node, "value", array_treatment=ArrayTreatment.MEAN) == 15
    )

    blank_node = {
        "term": {"termType": "crop", "@id": "wheatGrain"},
        "value": [10, None, 20],
    }
    assert get_node_value(blank_node, "value", array_treatment=ArrayTreatment.SUM) == 30


# @mark.parametrize(
#     'folder,list_key,termType',
#     [
#         ('cycle', 'emissions', TermTermType.EMISSION),
#     ]
# )
# def test_get_blank_nodes_calculation_status(folder: str, list_key: str, termType: TermTermType):
#     with open(f"{calculation_status_folder}/{folder}/node.jsonld", encoding='utf-8') as f:
#         node = json.load(f)

#     with open(f"{calculation_status_folder}/{folder}/{list_key}-{termType.value}.json", encoding='utf-8') as f:
#         expected = json.load(f)

#     result = get_blank_nodes_calculation_status(node, list_key=list_key, termType=termType)
#     assert result == expected, folder
