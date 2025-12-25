import os
import json
import pytest
from unittest.mock import Mock, patch, call

from .utils import fixtures_path
from hestia_earth.utils.tools import flatten
from hestia_earth.utils.pipeline import (
    METADATA_PROGRESS_KEY,
    METADATA_STAGE_KEY,
    parse_event,
    get_related_nodes,
    get_related_nodes_data,
    is_calculating,
    set_calculating,
    get_stage,
    to_string,
)

class_path = "hestia_earth.utils.pipeline"
fixtures_folder = os.path.join(fixtures_path, "pipeline")


def test_parse_event_direct():
    with open(os.path.join(fixtures_folder, "direct-invokation.json")) as f:
        event = json.load(f)
    results = parse_event(event)
    assert results == [
        {"bucket": "hestia-data-dev", "key": "recalculated/Cycle/1.jsonld"}
    ]


def test_parse_event_sqs():
    with open(os.path.join(fixtures_folder, "sqs.json")) as f:
        event = json.load(f)
    results = parse_event(event)
    assert results == [
        {
            "bucket": "hestia-data-staging",
            "key": "ImpactAssessment/d3wqcuk_o-vz.jsonld",
            "attributes": {"id": "d3wqcuk_o-vz", "type": "ImpactAssessment"},
        }
    ]


def test_parse_event_sqs_exhausted():
    with open(os.path.join(fixtures_folder, "sqs-exhausted.json")) as f:
        event = json.load(f)
    results = parse_event(event)
    assert results == []


def test_parse_event_sns():
    with open(os.path.join(fixtures_folder, "sns.json")) as f:
        event = json.load(f)
    results = parse_event(event)
    assert results == [
        {
            "bucket": "hestia-data-dev",
            "key": "recalculated/Cycle/1.jsonld",
            "attributes": {"Test": "TestString", "TestBinary": "TestBinary"},
        }
    ]


def test_parse_event_s3():
    with open(os.path.join(fixtures_folder, "s3.json")) as f:
        event = json.load(f)
    results = parse_event(event)
    assert results == [
        {"bucket": "hestia-data-dev", "key": "recalculated/Cycle/1.jsonld"}
    ]


_CACHE = {
    "nested": [
        {"@type": "Site", "@id": "nested-site-1"},
        {"@type": "Cycle", "@id": "nested-cycle-1"},
        {"@type": "ImpactAssessment", "@id": "nested-ia-1"},
    ],
    "related": [
        {"@type": "Site", "@id": "related-site-1"},
        {"@type": "Cycle", "@id": "related-cycle-1"},
        {"@type": "ImpactAssessment", "@id": "related-ia-1"},
    ],
}


@pytest.mark.parametrize(
    "test_name,node_type,related_key,related_type,cache,expected_nodes",
    [
        (
            "nested-with-cache",
            "Site",
            "nested",
            "Cycle",
            _CACHE,
            [{"@type": "Cycle", "@id": "nested-cycle-1"}],
        ),
        (
            "related-with-cache",
            "Site",
            "related",
            "Site",
            _CACHE,
            [{"@type": "Site", "@id": "related-site-1"}],
        ),
        ("related-empty-cache", "Site", "related", "Cycle", {"related": []}, []),
        ("related-no-cache", "Site", "related", "Cycle", None, _CACHE["related"]),
    ],
)
@patch(f"{class_path}.find_related", return_value=_CACHE["related"])
def test_get_related_nodes(
    mock_find_related: Mock,
    test_name: str,
    node_type: str,
    related_key: str,
    related_type: str,
    cache: dict,
    expected_nodes: list,
):
    nodes = get_related_nodes(
        node={"@type": node_type},
        related_key=related_key,
        related_type=related_type,
        cache=cache,
    )
    assert nodes == expected_nodes, test_name


@pytest.mark.parametrize(
    "test_name,node_type,related_key,related_type,cache,expected_nodes",
    [
        (
            "nested-with-cache",
            "Site",
            "nested",
            "Cycle",
            _CACHE,
            [{"@type": "Cycle", "@id": "nested-cycle-1"}],
        ),
        (
            "related-with-cache",
            "Site",
            "related",
            "Site",
            _CACHE,
            [{"@type": "Site", "@id": "related-site-1"}],
        ),
        ("related-no-cache", "Site", "related", "Cycle", None, _CACHE["related"]),
    ],
)
@patch(f"{class_path}.find_related", return_value=_CACHE["related"])
@patch(f"{class_path}._last_modified", return_value="")
@patch(f"{class_path}.is_calculating", return_value=False)
@patch(f"{class_path}.get_stage", return_value=1)
def test_get_related_nodes_data(
    mock_get_stage: Mock,
    mock_is_calculating: Mock,
    mock_last_modified: Mock,
    mock_find_related: Mock,
    test_name: str,
    node_type: str,
    related_key: str,
    related_type: str,
    cache: dict,
    expected_nodes: list,
):
    bucket = "bucket"
    nodes = get_related_nodes_data(
        bucket_name=bucket,
        node={"@type": node_type},
        related_key=related_key,
        related_type=related_type,
        cache=cache,
    )

    assert nodes == [
        node
        | {
            "indexed_at": "",
            "recalculated_at": "",
            "recalculated_stage": 1,
            "is_calculating": False,
        }
        for node in expected_nodes
    ], test_name

    assert mock_get_stage.call_args_list == [
        call("bucket", node) for node in expected_nodes
    ], test_name

    assert mock_is_calculating.call_args_list == [
        call("bucket", node) for node in expected_nodes
    ], test_name

    assert mock_last_modified.call_args_list == flatten(
        [
            [
                call(bucket="bucket", key=f"{node['@type']}/{node['@id']}.jsonld"),
                call(
                    bucket="bucket",
                    key=f"recalculated/{node['@type']}/{node['@id']}.jsonld",
                ),
            ]
            for node in expected_nodes
        ]
    ), test_name


@patch(f"{class_path}._read_metadata")
def test_get_stage(mock_read_metadata: Mock):
    bucket = "bucket"
    node = {"@type": "Cycle", "@id": "cycle"}

    mock_read_metadata.return_value = {METADATA_STAGE_KEY: "1"}
    assert get_stage(bucket, node) == 1

    mock_read_metadata.return_value = {}
    assert get_stage(bucket, node) is None


@patch(f"{class_path}._read_metadata")
def test_is_calculating(mock_read_metadata: Mock):
    bucket = "bucket"
    node = {"@type": "Cycle", "@id": "cycle"}

    mock_read_metadata.return_value = {METADATA_PROGRESS_KEY: "true"}
    assert is_calculating(bucket, node) is True

    mock_read_metadata.return_value = {METADATA_PROGRESS_KEY: "false"}
    assert not is_calculating(bucket, node)


@patch(f"{class_path}._update_metadata")
def test_set_calculating(mock_update_metadata: Mock):
    bucket = "bucket"
    node = {"@type": "Cycle", "@id": "cycle"}
    set_calculating(bucket, node, True)
    assert mock_update_metadata.call_args_list == [
        call("bucket", "Cycle/cycle.jsonld", {METADATA_PROGRESS_KEY: "true"})
    ]


@pytest.mark.parametrize(
    "data,indent,expected",
    [({"@id": 2}, None, '{"@id": 2}'), ({"@id": 2}, 2, '{\n  "@id": 2\n}')],
)
def test_to_string(data: dict, indent, expected: str):
    assert to_string(data, indent=indent) == expected, expected
