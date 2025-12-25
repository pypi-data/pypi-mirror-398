import json
from functools import lru_cache
from typing import Union
from hestia_earth.schema import TermTermType

from .storage import _load_from_storage
from .api import download_hestia


@lru_cache()
def _load_term_file(term_type: str):
    try:
        filepath = f"glossary/{term_type}.json"
        nodes = json.loads(_load_from_storage(filepath, glossary=True))
        return {node.get("@id"): node for node in nodes}
    except Exception:
        return {}


def download_term(term: Union[str, dict], termType: Union[str, TermTermType] = None):
    """
    Download a Term, using the glossary file if available, or default to the standard download.
    """
    term_id = term.get("@id", term.get("id")) if isinstance(term, dict) else term
    term_type = (
        (termType if isinstance(termType, str) else termType.value)
        if termType
        else (term.get("termType") if isinstance(term, dict) else None)
    )
    cached_nodes = _load_term_file(term_type) if term_type else {}
    return cached_nodes.get(term_id) or download_hestia(term_id)
