from hestia_earth.utils.request import join_args, request_url


def test_join_args():
    assert join_args(["arg1", "", "arg3"]) == "arg1&arg3"


def test_request_url():
    assert request_url("base", id="id", empty="") == "base?id=id"
