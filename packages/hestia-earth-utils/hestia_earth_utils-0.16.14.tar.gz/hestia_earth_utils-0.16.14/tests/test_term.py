import json
from unittest.mock import patch

from hestia_earth.utils.term import download_term

class_path = "hestia_earth.utils.term"
term = {"@type": "Term", "@id": "seed"}
termType = "seed"


@patch(f"{class_path}._load_from_storage", return_value=json.dumps([term]))
def test_download_term_from_glossary(*args):
    assert download_term(term, termType) == term


@patch(f"{class_path}.download_hestia", return_value=term)
@patch(f"{class_path}._load_term_file", return_value={})
def test_download_term_from_api(*args):
    assert download_term(term, termType) == term
