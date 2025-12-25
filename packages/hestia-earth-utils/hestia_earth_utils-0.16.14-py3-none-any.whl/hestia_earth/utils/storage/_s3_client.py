import os

BUCKET = os.getenv("AWS_BUCKET")
BUCKET_GLOSSARY = os.getenv("AWS_BUCKET_GLOSSARY")
_s3_client = None  # noqa: F824


# improves speed for connecting on subsequent calls
def _get_s3_client():
    global _s3_client
    import boto3

    _s3_client = (
        boto3.session.Session().client("s3") if _s3_client is None else _s3_client
    )
    return _s3_client


def _get_bucket(glossary: bool = False) -> str:
    return BUCKET_GLOSSARY if glossary else BUCKET


def _load_from_bucket(bucket: str, key: str):
    from botocore.exceptions import ClientError

    try:
        return _get_s3_client().get_object(Bucket=bucket, Key=key)["Body"].read()
    except ClientError:
        return None


def _exists_in_bucket(bucket: str, key: str):
    from botocore.exceptions import ClientError

    try:
        _get_s3_client().head_object(Bucket=bucket, Key=key)
        return True
    except ClientError:
        return False


def _read_size(bucket: str, key: str):
    try:
        return _get_s3_client().head_object(Bucket=bucket, Key=key).get("ContentLength")
    except Exception:
        return 0


def _read_metadata(bucket_name: str, key: str):
    try:
        return (
            _get_s3_client()
            .head_object(Bucket=bucket_name, Key=key)
            .get("Metadata", {})
        )
    except Exception:
        return {}


def _update_metadata(bucket: str, key: str, data: dict = {}):
    try:
        metadata = _read_metadata(bucket, key)
        metadata.update(data)
        _get_s3_client().copy_object(
            Bucket=bucket,
            Key=key,
            CopySource={"Bucket": bucket, "Key": key},
            Metadata=metadata,
            MetadataDirective="REPLACE",
        )
    except Exception:
        pass


def _last_modified(bucket: str, key: str):
    try:
        return _get_s3_client().head_object(Bucket=bucket, Key=key).get("LastModified")
    except Exception:
        return None


def _upload_to_bucket(bucket: str, key: str, body, content_type: str):
    from botocore.exceptions import ClientError

    try:
        return _get_s3_client().put_object(
            Bucket=bucket, Key=key, Body=body, ContentType=content_type
        )
    except ClientError:
        return None


def _list_bucket_objects(bucket: str, folder: str = ""):
    from botocore.exceptions import ClientError

    try:
        paginator = _get_s3_client().get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=bucket, Prefix=folder)

        contents = []
        for page in pages:
            contents.extend(page.get("Contents", []))
        return contents
    except ClientError:
        return []


def _delete_objects(bucket: str, objects: list):
    from botocore.exceptions import ClientError

    try:
        # delete in batch of 1000 max allowed
        batch_size = 1000
        for i in range(0, len(objects), batch_size):
            batch_objects = objects[i : i + batch_size]
            _get_s3_client().delete_objects(
                Bucket=bucket, Delete={"Objects": batch_objects, "Quiet": True}
            )
    except ClientError:
        return None
