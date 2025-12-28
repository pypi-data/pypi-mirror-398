from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from loguru import logger
from minio import Minio


def s3_to_url(s3_path: str, host: str) -> str:
    key = s3_path.replace("s3://", "").lstrip("/")
    return f"http://{host.rstrip('/')}/{key}"


def S3_path_to_info(s3_path) -> tuple[str | Any, str | Any] | None:
    if not s3_path.startswith("s3://"):
        return None

    pattern = r"s3://(?P<bucket>\w+)/(?P<objectname>.+)"

    match = re.match(pattern, s3_path)

    if match:
        bucket = match.group("bucket")
        objectname = match.group("objectname")
        return bucket, objectname
    return None


def local_path_to_s3_key(work_dir: str, local_path: str) -> str:
    work_dir = Path(work_dir)
    local_path = Path(local_path)
    s3_key = str(local_path.relative_to(work_dir))
    return s3_key


def upload_dir_to_s3(s3_client: Minio, local_dir: str, bucket: str, object_prefix: str) -> None:
    logger.info(
        f"Uploading directory {local_dir} to S3 bucket {bucket} with prefix {object_prefix}"
    )

    for root, dirs, files in os.walk(local_dir):
        for file in files:
            local_path = Path(root) / file
            s3_key = local_path_to_s3_key(local_dir, str(local_path))
            s3_client.fput_object(
                bucket, os.path.join(object_prefix, s3_key), str(local_path)
            )

    logger.info(
        f"Uploaded directory {local_dir} to S3 bucket {bucket} with prefix {object_prefix}"
    )
    return


def download_dir_from_s3(s3_client: Minio, bucket: str, object_prefix: str, local_dir: str) -> None:
    logger.info(
        f"Downloading directory from S3 bucket {bucket} with prefix {object_prefix} to {local_dir}"
    )
    objs = s3_client.list_objects(bucket, object_prefix, recursive=True)

    for obj in objs:
        file_name = Path(obj.object_name).relative_to(object_prefix)
        s3_client.fget_object(
            bucket, obj.object_name, os.path.join(local_dir, file_name)
        )

    logger.info(
        f"Downloaded directory from S3 bucket {bucket} with prefix {object_prefix} to {local_dir}"
    )
    return


def parse_s3_path_strict(s3_path: str) -> tuple[str, str]:
    if not isinstance(s3_path, str) or not s3_path.startswith("s3://"):
        raise ValueError(f"invalid s3 path: {s3_path}")
    without_scheme = s3_path[5:]
    parts = without_scheme.split("/", 1)
    bucket = parts[0].strip()
    if not bucket:
        raise ValueError(f"invalid s3 path (empty bucket): {s3_path}")
    key = parts[1] if len(parts) > 1 else ""
    return bucket, key


def download_dir_from_s3_to_local(s3_client: Minio, bucket: str, object_prefix: str, local_dir: str) -> None:
    logger.info(f"Downloading directory from S3 bucket {bucket} with prefix {object_prefix} to {local_dir}")

    norm_prefix = object_prefix.replace("\\", "/").lstrip("/")
    if norm_prefix and not norm_prefix.endswith("/"):
        norm_prefix = norm_prefix + "/"

    prefixes = [object_prefix]
    norm_for_list = object_prefix.replace("\\", "/")
    if norm_for_list != object_prefix:
        prefixes.append(norm_for_list)

    seen = set()
    for pfx in prefixes:
        for obj in s3_client.list_objects(bucket, pfx, recursive=True):
            key = obj.object_name
            if key in seen:
                continue
            seen.add(key)

            norm_key = key.replace("\\", "/")
            if norm_key.endswith("/"):
                continue

            if norm_prefix and not norm_key.startswith(norm_prefix):
                continue

            rel = norm_key[len(norm_prefix):] if norm_prefix else norm_key
            dest_path = os.path.join(local_dir, *rel.split("/"))
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            s3_client.fget_object(bucket, key, dest_path)

    logger.info(f"Downloaded directory from S3 bucket {bucket} with prefix {object_prefix} to {local_dir}")
