import os

_sns_client = None  # noqa: F824


# improves speed for connecting on subsequent calls
def _get_sns_client():
    global _sns_client
    import boto3

    region_name = os.getenv("AWS_REGION")
    _sns_client = (
        boto3.session.Session().client("sns", region_name=region_name)
        if _sns_client is None
        else _sns_client
    )
    return _sns_client
