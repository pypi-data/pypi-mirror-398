from ._s3_client import _get_bucket, _load_from_bucket, _exists_in_bucket
from ._azure_client import _get_container, _load_from_container, _exists_in_container
from ._local_client import _get_folder, _load_from_folder, _exists_in_folder


def _load_from_storage(filepath: str, glossary: bool = False):
    if _get_bucket(glossary):
        return _load_from_bucket(_get_bucket(glossary), filepath)
    if _get_container(glossary):
        return _load_from_container(_get_container(glossary), filepath)
    if _get_folder(glossary):
        return _load_from_folder(_get_folder(glossary), filepath)
    raise ImportError


def _exists(filepath: str):
    if _get_bucket():
        return _exists_in_bucket(_get_bucket(), filepath)
    if _get_container():
        return _exists_in_container(_get_container(), filepath)
    if _get_folder():
        return _exists_in_folder(_get_folder(), filepath)
    raise ImportError
