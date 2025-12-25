import requests
import os
import json
from functools import cache
from hestia_earth.schema import SchemaType, NESTED_SEARCHABLE_KEYS

from .storage import _load_from_storage, _exists
from .request import request_url, api_url, api_access_token


def _match_key_value(key: str, value):
    first_key = key.split(".")[0]
    query = {"match": {key: value}}
    return (
        {"nested": {"path": first_key, "query": query}}
        if first_key in NESTED_SEARCHABLE_KEYS
        else query
    )


def _retry_request_error(func, retry_max: int = 5):
    err = None

    for _ in range(retry_max):
        try:
            return func()
        except json.decoder.JSONDecodeError as e:
            err = e
            continue

    raise err


def _safe_get_request(url: str, res_error=None):
    def exec():
        try:
            headers = {"Content-Type": "application/json"}
            access_token = api_access_token()
            if access_token:
                headers["X-Access-Token"] = access_token
            return requests.get(url, headers=headers).json()
        except requests.exceptions.RequestException:
            return res_error

    return _retry_request_error(exec)


def _safe_post_request(url: str, body: dict, res_error={}):
    def exec():
        try:
            headers = {"Content-Type": "application/json"}
            access_token = api_access_token()
            if access_token:
                headers["X-Access-Token"] = access_token
            return requests.post(url, json.dumps(body), headers=headers).json()
        except requests.exceptions.RequestException:
            return res_error

    return _retry_request_error(exec)


def _parse_node_type(node_type: SchemaType):
    return node_type if isinstance(node_type, str) else node_type.value


def node_type_to_url(node_type: SchemaType):
    return f"{_parse_node_type(node_type)}s".lower()


def node_to_path(node_type: SchemaType, node_id: str, data_state=None):
    jsonld_path = os.path.join(_parse_node_type(node_type), f"{node_id}.jsonld")
    return (
        jsonld_path
        if data_state is None or data_state == "original" or len(data_state) == 0
        else os.path.join(data_state, jsonld_path)
    )


def find_related(
    node_type: SchemaType,
    id: str,
    related_type: SchemaType,
    limit=100,
    offset=0,
    relationship=None,
):
    """
    Return the list of related Nodes by going through a "relationship".
    You can navigate the HESTIA Graph Database using this method.

    Parameters
    ----------
    node_type
        The `@type` of the Node to start from. Example: use `SchemaType.Cycle` to find nodes related to a `Cycle`.
    id
        The `@id` of the Node to start from.
    related_type
        The other Node to which the relation should go to. Example: use `SchemaType.Source` to find `Source` related to
        `Cycle`.
    limit
        The limit of relationships to return. Asking for large number might result in timeouts.
    offset
        Use with limit to paginate through the results.
    relationship
        The relationship used to connect both Node. See the API for more information.
    """
    url = request_url(
        f"{api_url()}/{node_type_to_url(node_type)}/{id}/{node_type_to_url(related_type)}",
        limit=limit,
        offset=offset,
        relationship=relationship,
    )
    response = _safe_get_request(url)
    # handle errors
    return response.get("results", []) if isinstance(response, dict) else response


def _exec_download_hestia(
    node_id: str, node_type=SchemaType.TERM, data_state="", mode=""
) -> dict:
    def fallback():
        url = request_url(
            f"{api_url()}/{node_type_to_url(node_type)}/{node_id}",
            dataState=data_state,
            mode=mode,
        )
        return _safe_get_request(url)

    try:
        jsonld_path = node_to_path(node_type, node_id, data_state)
        data = _load_from_storage(jsonld_path)
        return json.loads(data) if data else None
    except ImportError:
        return fallback()


_exec_download_hestia_cached = cache(_exec_download_hestia)


def download_hestia(
    node_id: str, node_type=SchemaType.TERM, data_state="", mode=""
) -> dict:
    """
    Download a Node from the HESTIA Database.

    Parameters
    ----------
    node_id
        The `@id` of the Node.
    node_type
        The `@type` of the Node.
    data_state
        Optional - the `dataState` of the Node.
        By default, `original` version will be returned.
        Use `recalculated` to download the recalculated version instead (if available).
    mode
        Optional - use `csv` to download as a CSV file, `zip` to download as a ZIP file. Defaults to `JSON`.

    Returns
    -------
    JSON
        The `JSON` content of the Node.
    """
    # cache all requests to `Term` by default, as the values are not likely to change during a single execution
    download_func = (
        _exec_download_hestia_cached
        if _parse_node_type(node_type) == "Term"
        else _exec_download_hestia
    )
    return download_func(node_id, node_type, data_state, mode)


def node_exists(node_id: str, node_type=SchemaType.TERM) -> bool:
    """
    Checks if a node exists on the HESTIA Database.

    Parameters
    ----------
    node_id
        The `@id` of the Node.
    node_type
        The `@type` of the Node.

    Returns
    -------
    bool
        True if the node exists, False otherwise.
    """

    def fallback():
        url = request_url(f"{api_url()}/{node_type_to_url(node_type)}/{node_id}")
        result = _safe_get_request(url)
        return result is not None and "@id" in result

    try:
        return _exists(node_to_path(node_type, node_id))
    except ImportError:
        return fallback()


def search(
    query: dict, fields=["@type", "@id", "name"], limit=10, offset=0, sort=None
) -> list:
    """
    Executes a raw search on the HESTIA Platform.

    Parameters
    ----------
    query
        The search engine is using ElasticSearch engine version 7:
        https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html.
        All options can be used here.
    fields
        The list of fields to return. Example: ['@type', '@id']. Defaults to `['@type', '@id', 'name']`.
    limit
        Optional - limit the number of results to return. Defaults to `10`.
    offset
        Optional - use with limit to paginate the results. Defaults to `0`.
    sort : dict
        Sorting options. Please refer to the ElasticSearch version 7 documentation for use.

    Returns
    -------
    List[JSON]
        List of Nodes (as JSON) found.
    """
    return _safe_post_request(
        f"{api_url()}/search",
        {
            "query": query,
            "limit": limit,
            "offset": offset,
            "fields": fields,
            **({"sort": sort} if sort is not None else {}),
        },
    ).get("results", [])


def find_node(node_type: SchemaType, args: dict, limit=10) -> list:
    """
    Finds nodes on the HESTIA Platform.

    Parameters
    ----------
    node_type
        The `@type` of the Node.
    args
        Dictionary of key/value to exec search on. Example: use `{'bibliography.title': 'My biblio'}` on a
        `SchemaType.Source` to find all `Source`s having a `bibliography` with `title` == `My biblio`
    limit
        Optional - limit the number of results to return. Defaults to `10`.

    Returns
    -------
    List[JSON]
        List of Nodes (as JSON) found.
    """
    query_args = list(
        map(lambda key: _match_key_value(key, args.get(key)), args.keys())
    )
    must = [{"match": {"@type": node_type.value}}]
    must.extend(query_args)
    return search(query={"bool": {"must": must}}, limit=limit)


def find_node_exact(node_type: SchemaType, args: dict) -> dict:
    """
    Finds a single Node on the HESTIA Platform.

    Parameters
    ----------
    node_type
        The `@type` of the Node.
    args
        Dictionary of key/value to exec search on. Example: use `{'bibliography.title': 'My biblio'}` on a
        `SchemaType.Source` to find all `Source`s having a `bibliography` with `title` == `My biblio`

    Returns
    -------
    JSON
        JSON of the node if found, else `None`.
    """
    query_args = list(
        map(lambda key: _match_key_value(f"{key}.keyword", args.get(key)), args.keys())
    )
    must = [{"match": {"@type": node_type.value}}]
    must.extend(query_args)
    results = search(query={"bool": {"must": must}}, limit=2)
    # do not return a duplicate
    return results[0] if len(results) == 1 else None


# should support up to 65,000 terms, but limit to 1000 just in case
# https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-terms-query.html#terms-top-level-params
def find_term_ids_by_names(names, batch_size=1000):
    unique_names_set = set(names)
    unique_names = list(unique_names_set)
    unique_names_count = len(unique_names)
    result = {}
    for i in range(0, unique_names_count, batch_size):
        query = {
            "constant_score": {
                "filter": {
                    "bool": {
                        "must": [
                            {
                                "terms": {
                                    "name.keyword": unique_names[i : i + batch_size],
                                }
                            },
                            {"term": {"@type.keyword": "Term"}},
                        ]
                    }
                }
            }
        }
        results = search(query=query, limit=batch_size, fields=["@id", "name"])
        for term in results:
            result[term.get("name")] = term.get("@id")
    missing_names = unique_names_set - set(result.keys())
    if len(missing_names):
        raise Exception(f"Failed to find ids for names: {'; '.join(missing_names)}")
    return result
