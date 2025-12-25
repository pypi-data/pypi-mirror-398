from hestia_earth.schema import TermTermType

from hestia_earth.utils.model import (
    find_term_match,
    find_primary_product,
    filter_list_term_type,
    convert_value,
    linked_node,
)


def test_find_term_match():
    values = [
        {"term": {"@id": "my term"}, "methodModel": {"@id": "model-1"}},
        {"term": {"@id": "another id"}},
        {"term": {"@id": "my term"}, "methodModel": {"@id": "model-2"}},
    ]
    assert find_term_match(values, "my term") == values[0]
    assert (
        find_term_match(values, "my term", match_params={"methodModel.@id": "model-2"})
        == values[2]
    )


def test_find_primary_product():
    primary = {"@type": "Product", "primary": True}
    cycle = {"products": [primary, {"@type": "Product"}]}
    assert find_primary_product(cycle) == primary


def test_filter_list_term_type():
    values = [
        {"term": {"termType": TermTermType.CROP.value}},
        {"term": {"termType": TermTermType.FUEL.value}},
    ]
    assert len(filter_list_term_type(values, TermTermType.CROP)) == 1
    assert (
        len(filter_list_term_type(values, [TermTermType.CROP, TermTermType.FUEL])) == 2
    )


def test_convert_value():
    assert convert_value(1, "m3", "kg", density=553) == 553
    assert convert_value(1, "m3", "L") == 1000
    assert convert_value(553, "kg", "m3", density=553) == 1
    assert convert_value(553, "kg", "L", density=553) == 1000
    assert convert_value(1000, "L", "m3") == 1
    assert round(convert_value(100, "MJ", "kWh")) == 28
    assert convert_value(10, "kWh", "MJ") == 36


def test_linked_node():
    node = {"@type": "Term", "@id": "term-id", "value": 10, "name": "term"}
    assert linked_node(node) == {"@type": "Term", "@id": "term-id", "name": "term"}

    node["@type"] = "Cycle"
    assert linked_node(node) == {"@type": "Cycle", "@id": "term-id"}
