from unittest.mock import patch
import os
import requests
import json
from hestia_earth.schema import SchemaType
import pytest

from .utils import fixtures_path
from hestia_earth.utils.request import api_url
from hestia_earth.utils.api import (
    search,
    find_related,
    download_hestia,
    node_exists,
    find_node,
    find_node_exact,
    find_term_ids_by_names,
)


fake_related_response = {"results": [[{"@id": "related_id"}]]}
fake_download_response = {"@id": "id", "@type": "type"}


class FakeFindRelatedSuccess:
    def json():
        return fake_related_response


class FakeFindRelatedError:
    def json():
        return {}


class FakeFindRelatedException:
    def json():
        raise requests.exceptions.RequestException("error")


class FakeDownloadSuccess:
    def json():
        return fake_download_response


class FakeDownloadError:
    def json():
        raise requests.exceptions.RequestException("error")


class FakeNodeExistSuccess:
    def json():
        return fake_download_response


class FakeNodeExistError:
    def json():
        return {"message": "not-found", "details": {}}


class FakeElasticSearchEmptyResult:
    def json():
        return {"results": []}


@patch("requests.get", return_value=FakeFindRelatedSuccess)
def test_find_related_success(mock_get):
    res = find_related(SchemaType.CYCLE, "id", SchemaType.SOURCE)
    assert res == fake_related_response.get("results")
    mock_get.assert_called_once_with(
        f"{api_url()}/cycles/id/sources?limit=100",
        headers={"Content-Type": "application/json"},
    )


@patch("requests.get", return_value=FakeFindRelatedError)
def test_find_related_error(*args):
    res = find_related(SchemaType.CYCLE, "id", SchemaType.SOURCE)
    assert not res


@patch("requests.get", return_value=FakeFindRelatedException)
def test_find_related_exception(*args):
    res = find_related(SchemaType.CYCLE, "id", SchemaType.SOURCE)
    assert not res


@patch(
    "requests.get", return_value=FakeDownloadError
)  # make sure fallback is not enabled
def test_download_hestia_local_file(*args):
    id = "sandContent"
    with open(f"{fixtures_path}/Term/{id}.jsonld", encoding="utf-8") as f:
        expected = json.load(f)
    os.environ["DOWNLOAD_FOLDER"] = fixtures_path
    res = download_hestia(id, SchemaType.TERM)
    assert res == expected
    del os.environ["DOWNLOAD_FOLDER"]


@patch("requests.get", return_value=FakeDownloadSuccess)
def test_download_hestia_success(mock_get):
    res = download_hestia("id", SchemaType.SOURCE)
    assert res == fake_download_response
    mock_get.assert_called_once_with(
        f"{api_url()}/sources/id", headers={"Content-Type": "application/json"}
    )


@patch("requests.get", return_value=FakeDownloadError)
def test_download_hestia_error(*args):
    res = download_hestia("id", SchemaType.SOURCE)
    assert not res


@patch(
    "requests.get", return_value=FakeNodeExistError
)  # make sure fallback is not enabled
def test_node_exists_local_file(*args):
    os.environ["DOWNLOAD_FOLDER"] = fixtures_path
    id = "sandContent"
    assert node_exists(id, SchemaType.TERM)
    del os.environ["DOWNLOAD_FOLDER"]


@patch("requests.get", return_value=FakeNodeExistSuccess)
def test_node_exists_true(*args):
    assert node_exists("id", SchemaType.SOURCE)


@patch("requests.get", return_value=FakeNodeExistError)
def test_node_exists_false(*args):
    assert not node_exists("id", SchemaType.SOURCE)


def test_search():
    name = "Wheat"
    res = search(query={"bool": {"must": [{"match": {"name": name}}]}}, limit=2)
    assert res[0].get("name").startswith(name)


def test_find_node():
    name = "Wheat"
    res = find_node(SchemaType.TERM, {"name": name}, 2)
    assert res[0].get("name").startswith(name)


def test_find_node_exact():
    name = "Wheat"
    res = find_node_exact(SchemaType.TERM, {"name": name})
    assert not res

    name = "Wheat, grain"
    res = find_node_exact(SchemaType.TERM, {"name": name})
    assert res.get("name") == name


def test_find_term_ids_by_names():
    names = ["Harris Termite Powder", "Wheat, grain", "Urea (kg N)"]
    res = find_term_ids_by_names(names, 2)
    assert res == {
        "Wheat, grain": "wheatGrain",
        "Harris Termite Powder": "harrisTermitePowder",
        "Urea (kg N)": "ureaKgN",
    }


@patch("requests.post", return_value=FakeElasticSearchEmptyResult)
def test_find_term_ids_by_names_error(mock):
    names = ["id_not_found_name"]
    with pytest.raises(Exception, match=names[0]):
        find_term_ids_by_names(names)
