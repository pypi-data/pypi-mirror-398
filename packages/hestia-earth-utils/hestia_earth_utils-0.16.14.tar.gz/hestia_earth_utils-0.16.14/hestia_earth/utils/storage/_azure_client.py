import os

CONN_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
CONTAINER = os.getenv("AZURE_STORAGE_CONTAINER")
CONTAINER_GLOSSARY = os.getenv("AZURE_STORAGE_CONTAINER_GLOSSARY")
_blob_service = None  # noqa: F824


# improves speed for connecting on subsequent calls
def _get_blob_service_client():
    global _blob_service
    from azure.storage.blob import BlobServiceClient

    _blob_service = (
        BlobServiceClient.from_connection_string(CONN_STRING)
        if _blob_service is None
        else _blob_service
    )
    return _blob_service


def _get_container(glossary: bool = False) -> str:
    return CONTAINER_GLOSSARY if glossary else CONTAINER


def _load_from_container(container: str, key: str):
    from azure.core.exceptions import ResourceNotFoundError

    try:
        blob_client = _get_blob_service_client().get_blob_client(
            container=container, blob=key
        )
        return blob_client.download_blob().readall()
    except ResourceNotFoundError:
        return None


def _exists_in_container(container: str, key: str):
    from azure.core.exceptions import ResourceNotFoundError

    try:
        blob_client = _get_blob_service_client().get_blob_client(
            container=container, blob=key
        )
        return blob_client.exists()
    except ResourceNotFoundError:
        return False
