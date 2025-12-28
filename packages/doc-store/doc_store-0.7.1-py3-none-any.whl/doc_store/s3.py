import io
import re
import time

import boto3
from boto3.s3.transfer import TransferConfig
from botocore.client import Config
from botocore.exceptions import ClientError
from botocore.response import StreamingBody

from .config import config

__re_s3_path = re.compile("^s3a?://([^/]+)(?:/(.*))?$")


def split_s3_path(path: str) -> tuple[str, str]:
    "split bucket and key from path"
    m = __re_s3_path.match(path)
    if m is None:
        raise ValueError(f"Invalid S3 path: {path}")
    return m.group(1), (m.group(2) or "")


def get_s3_client(path: str):
    bucket, _ = split_s3_path(path)
    bucket_profile = config.s3.buckets.get(bucket, None)
    if not bucket_profile:
        raise ValueError(f"Bucket {bucket} not found in S3 config.")
    profile = config.s3.profiles.get(bucket_profile, None)
    if not profile:
        raise ValueError(f"Profile {bucket_profile} not found in S3 config.")
    return boto3.client(
        "s3",
        aws_access_key_id=profile.aws_access_key_id,
        aws_secret_access_key=profile.aws_secret_access_key,
        endpoint_url=profile.endpoint_url,
        config=Config(
            s3={"addressing_style": profile.addressing_style},
            retries={"max_attempts": 8},
        ),
    )


def is_s3_404_error(e: Exception):
    if not isinstance(e, ClientError):
        return False
    return (
        e.response.get("Error", {}).get("Code") in ["404", "NoSuchKey"]
        or e.response.get("Error", {}).get("Message") == "Not Found"
        or e.response.get("ResponseMetadata", {}).get("HTTPStatusCode") == 404
    )


def head_s3_object(path: str, raise_404=False, client=None) -> dict | None:
    client = client or get_s3_client(path)
    bucket, key = split_s3_path(path)
    try:
        resp = client.head_object(Bucket=bucket, Key=key)
        return resp
    except ClientError as e:
        if not raise_404 and is_s3_404_error(e):
            return None
        raise


def get_s3_object(path: str, client=None, **kwargs) -> dict:
    client = client or get_s3_client(path)
    bucket, key = split_s3_path(path)
    return client.get_object(Bucket=bucket, Key=key, **kwargs)


def read_s3_object_detailed(path: str, client=None) -> tuple[StreamingBody, dict]:
    obj = get_s3_object(path, client=client)
    return obj.pop("Body"), obj


def read_s3_object_bytes_detailed(path: str, size_limit=0, client=None):
    """This method cache all content in memory, avoid large file."""
    retries = 0
    last_e = None
    while True:
        if retries > 5:
            msg = f"Retry exhausted for reading [{path}]"
            raise Exception(msg) from last_e
        try:
            stream, obj = read_s3_object_detailed(path, client=client)
            with stream:
                amt = size_limit if size_limit > 0 else None
                buf = stream.read(amt)
            break
        except ClientError:
            raise
        except Exception as e:
            last_e = e
            retries += 1
            time.sleep(3)
    assert isinstance(buf, bytes)
    return buf, obj


def read_s3_object(path: str, client=None):
    return read_s3_object_detailed(path, client=client)[0]


def read_s3_object_bytes(path: str, size_limit=0, client=None):
    """This method cache all content in memory, avoid large file."""
    return read_s3_object_bytes_detailed(path, size_limit, client=client)[0]


def get_s3_presigned_url(path: str, expires_in=3600, content_type="", as_attachment=False, client=None) -> str:
    client = client or get_s3_client(path)
    bucket, key = split_s3_path(path)
    params = {"Bucket": bucket, "Key": key}
    if content_type:
        params["ResponseContentType"] = content_type
    if as_attachment:
        filename = key.split("/")[-1]
        params["ResponseContentDisposition"] = f'attachment; filename="{filename}"'
    return client.generate_presigned_url(ClientMethod="get_object", Params=params, ExpiresIn=expires_in)


def put_s3_object(path: str, body: bytes = b"", client=None, **kwargs):
    client = client or get_s3_client(path)
    bucket, key = split_s3_path(path)
    return client.put_object(Bucket=bucket, Key=key, Body=body, **kwargs)


def upload_s3_object_bytes(path: str, body: bytes, client=None, **kwargs):
    client = client or get_s3_client(path)
    bucket, key = split_s3_path(path)
    with io.BytesIO(body) as buffer:
        client.upload_fileobj(Fileobj=buffer, Bucket=bucket, Key=key, ExtraArgs=kwargs)


def upload_s3_object_file(path: str, local_file_path: str, client=None):
    client = client or get_s3_client(path)
    config = TransferConfig(
        multipart_threshold=134217728,  # 128MiB
        multipart_chunksize=16777216,  # 16MiB, 156.25GiB maximum
    )
    bucket, key = split_s3_path(path)
    client.upload_file(local_file_path, bucket, key, Config=config)
