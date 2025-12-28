from __future__ import annotations

import os
import tempfile
import zipfile
from typing import List, TypedDict

import pyarrow.parquet as pq
from tqdm.contrib.concurrent import thread_map

from .http import http_download_file, http_download_file_wrapper
from .s3 import s3_to_url


class DatasetParquetMeta(TypedDict):
    parent_dir: str
    name: str
    s3path: str
    type: int  # 0=file, 1=dir


_ENUM_FILE = 0


def _read_parquet_index(file_path: str) -> List[DatasetParquetMeta]:
    table = pq.read_table(file_path)
    return table.to_pylist()  # 每行转 dict


def _safe_rel(part: str) -> str:
    if not part:
        return ""
    drive, tail = os.path.splitdrive(part)
    return tail.lstrip(r"\/")


def dataset_download(index_url: str, local_dir: str, worker: int = 4) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_file = os.path.join(tmpdir, "index.parquet")
        http_download_file(index_url, tmp_file)
        rows = _read_parquet_index(tmp_file)

    host = (index_url.split("//", 1)[-1]).split("/", 1)[0]

    files = [
        (
            os.path.join(
                local_dir,
                _safe_rel(row["parent_dir"]),
                _safe_rel(row["name"]),
            ),
            s3_to_url(row["s3path"], host),
        )
        for row in rows
        if row["type"] == _ENUM_FILE
    ]

    if worker < 1:
        worker = 1

    thread_map(http_download_file_wrapper, files, max_workers=worker)


def zip_dir(dir_path: str, zip_path: str):
    zip_file = zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED)
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            zip_file.write(
                os.path.join(root, file),
                os.path.relpath(os.path.join(root, file), dir_path),
            )

    zip_file.close()
