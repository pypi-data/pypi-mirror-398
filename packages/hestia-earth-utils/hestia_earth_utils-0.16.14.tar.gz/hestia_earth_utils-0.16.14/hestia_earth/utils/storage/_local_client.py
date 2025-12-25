import os


def _get_folder(glossary: bool = False) -> str:
    return (
        os.getenv("DOWNLOAD_FOLDER_GLOSSARY")
        if glossary
        else os.getenv("DOWNLOAD_FOLDER")
    )


def _load_from_folder(folder: str, key: str):
    try:
        with open(os.path.join(folder, key)) as f:
            return f.read().encode("utf-8")
    except Exception:
        # in case the file does not exist, should simply return None
        return None


def _exists_in_folder(folder: str, key: str):
    return os.path.exists(os.path.join(folder, key))
