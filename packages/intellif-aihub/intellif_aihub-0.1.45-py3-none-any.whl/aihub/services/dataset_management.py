# !/usr/bin/env python
# -*- coding:utf-8 -*-
"""数据集管理服务模块

本模块围绕 **“数据集生命周期管理”** 提供以下能力：

- **创建数据集及其版本**（支持本地上传和服务器现有文件两种方式）
- **上传文件到对象存储**（大文件自动分片）
- **查询数据集／数据集版本详情**
- **列表查询和搜索数据集**（支持分页和筛选）
- **列表查询数据集版本**（支持按数据集ID筛选和分页）
- **按版本名称或ID下载数据集文件**
"""

from __future__ import annotations

import mimetypes
import os
import pathlib
import time
import uuid
from pathlib import Path

import httpx
from loguru import logger
from minio import Minio
from pydantic import ValidationError

from ..exceptions import APIError, convert_errors
from ..models.artifact import StsResp
from ..models.common import APIWrapper
from ..models.dataset_management import (
    CreateDatasetRequest,
    CreateDatasetResponse,
    DatasetDetail,
    CreateDatasetVersionRequest,
    CreateDatasetVersionResponse,
    UploadDatasetVersionRequest,
    DatasetVersionDetail,
    UploadDatasetVersionResponse,
    FileUploadData,
    ListDatasetReq,
    ListDatasetResp,
    ListDatasetVersionReq,
    ListDatasetVersionResp,
    CreateDatasetVersionByDataIngestReqV2,
    UploadType,
)
from ..models.dataset_management import DatasetVersionStatus
from ..utils.di import SimpleS3Client, DataUploader
from ..utils.download import dataset_download
from ..utils.s3 import upload_dir_to_s3

_BASE = "/dataset-mng/api/v2"


class DatasetManagementService:
    """数据集管理服务，用于数据集的上传、下载"""

    def __init__(self, http: httpx.Client):
        self._dataset = _Dataset(http)
        self._dataset_version = _DatasetVersion(http)
        self._upload = _Upload(http)

    # 直接把常用方法抛到一级，调用体验简单
    def create_dataset(self, payload: CreateDatasetRequest) -> int:
        """创建数据集

        Args:
            payload (CreateDatasetRequest): 创建数据集所需信息，如名称、描述、可见性等

        Returns:
            int: 新建数据集的 ``dataset_id``
        """
        return self._dataset.create(payload)

    def get_dataset(self, dataset_id: int) -> DatasetDetail:
        """获取数据集详情

        Args:
            dataset_id (int): 数据集 ID

        Returns:
            DatasetDetail: 数据集完整信息（含所有版本元数据）
        """
        return self._dataset.get(dataset_id)

    def create_dataset_version(self, payload: CreateDatasetVersionRequest) -> int:
        """创建数据集版本

        Args:
            payload (CreateDatasetVersionRequest): 版本元信息

        Returns:
            int: 新建版本的 ``version_id``。
        """
        return self._dataset_version.create(payload)

    def upload_dataset_version(self, payload: UploadDatasetVersionRequest) -> int:
        """上传数据集版本

        Args:
            payload (UploadDatasetVersionRequest): 上传请求，需包含本地文件已上传后的 OSS 路径等信息

        Returns:
            int: 新建版本的 ``version_id``
        """
        return self._dataset_version.upload(payload)

    def get_dataset_version(self, version_id: int) -> DatasetVersionDetail:
        """获取数据集版本详情

        Args:
            version_id (int): 数据集版本 ID

        Returns:
            DatasetVersionDetail: 版本详细信息
        """
        return self._dataset_version.get(version_id)

    def get_dataset_version_by_name(self, version_name: str) -> DatasetVersionDetail:
        """通过 “数据集名/版本号” 获取版本详情

        Args:
            version_name (str): 形如 ``<dataset_name>/V<version>`` 的唯一标识

        Returns:
            DatasetVersionDetail: 版本详细信息
        """
        return self._dataset_version.get_by_name(version_name)

    def upload_file(self, file_path: str) -> FileUploadData:
        """上传本地文件到对象存储

        Args:
            file_path (str): 本地文件绝对路径

        Returns:
            FileUploadData: 上传结果（包含 OSS 路径、下载 URL 等）
        """
        return self._upload.upload_file(file_path)

    # 如果想要访问子对象，也保留属性
    @property
    def dataset(self) -> _Dataset:
        return self._dataset

    def _get_sts(self) -> StsResp:
        return self.dataset_version.get_sts()

    @property
    def dataset_version(self) -> _DatasetVersion:
        return self._dataset_version

    def upload_by_data_ingest(
        self,
        req: CreateDatasetVersionByDataIngestReqV2,
    ) -> CreateDatasetVersionResponse:
        return self.dataset_version.upload_by_data_ingest(req)

    def create_dataset_and_version(
        self,
        *,
        dataset_name: str,
        dataset_description: str = "",
        is_local_upload: bool,
        local_file_path: str | None = None,
        server_file_path: str | None = None,
        version_description: str = "",
        user_upload_data_path: str | None = None,
        timeout: int = 1_800,
    ) -> tuple[int, int, str]:
        """创建数据集及其版本，并等待版本状态变为 *Success*。

        根据参数创建数据集，并根据上传类型（本地或服务器路径）创建对应的数据集版本。

        Args:
            dataset_name: 数据集名称。
            dataset_description: 数据集描述，默认为空。
            is_local_upload: 是否为本地上传。若为 True，需提供 local_file_path；
                             否则需提供 server_file_path。
            local_file_path: 本地文件路径，当 is_local_upload=True 时必须提供。
            server_file_path: 服务器已有文件路径，当 is_local_upload=False 时必须提供。
            version_description: 版本描述，默认为空。
            timeout: 最大等待秒数（默认1800s）。超过后仍未成功则引发 ``TimeoutError``。
            user_upload_data_path: 用户本体数据的存储地址

        Returns:
           tuple[int, int, str]: 一个三元组，包含：[数据集 ID,数据集版本 ID, 数据集版本标签（格式为 <dataset_name>/V<version_number>)]

        Raises:
            ValueError: 当参数不满足要求时
            APIError: 当后端返回错误时
            TimeoutError: 当等待超时时
        """
        # 参数校验
        self._validate_create_params(is_local_upload, local_file_path, server_file_path)

        # 创建数据集
        dataset_id = self._create_dataset(dataset_name, dataset_description)
        logger.info(f"创建数据集成功，名称为 {dataset_name} ,开始准备创建版本、上传数据")

        # 创建数据集版本
        version_id = self._create_dataset_version(
            dataset_id=dataset_id,
            is_local_upload=is_local_upload,
            local_file_path=local_file_path,
            server_file_path=server_file_path,
            version_description=version_description,
            user_upload_data_path=user_upload_data_path,
        )

        # 获取版本标签
        version_tag = self._get_version_tag(dataset_id, version_id)
        logger.info(f"数据集版本创建成功，名称为 {version_tag}，开始轮询状态…")

        # 轮询等待版本状态变为成功
        self._wait_for_version_success(version_id, timeout)

        return dataset_id, version_id, version_tag

    def _validate_create_params(
        self, is_local_upload: bool, local_file_path: str | None, server_file_path: str | None
    ) -> None:
        """验证创建数据集和版本所需的参数"""
        if is_local_upload:
            if not local_file_path:
                raise ValueError("is_local_upload=True 时必须提供 local_file_path")
        else:
            if not server_file_path:
                raise ValueError("is_local_upload=False 时必须提供 server_file_path")

    def _create_dataset(self, dataset_name: str, dataset_description: str) -> int:
        """创建数据集"""
        return self._dataset.create(
            CreateDatasetRequest(
                name=dataset_name,
                description=dataset_description,
                tags=[],
                cover_img=None,
                create_by=None,
                is_private=None,
                access_user_ids=None,
            )
        )

    def _create_dataset_version(
        self,
        dataset_id: int,
        is_local_upload: bool,
        local_file_path: str | None,
        server_file_path: str | None,
        version_description: str,
        user_upload_data_path: str | None,
    ) -> int:
        """根据上传类型创建数据集版本"""
        if is_local_upload:
            return self._create_local_dataset_version(
                dataset_id, local_file_path, version_description, user_upload_data_path
            )
        else:
            return self._create_server_dataset_version(dataset_id, server_file_path, version_description)

    def _create_local_dataset_version(
        self, dataset_id: int, local_file_path: str | None, version_description: str, user_upload_data_path: str | None
    ) -> int:
        """创建本地文件数据集版本"""
        if pathlib.Path(local_file_path).is_dir():
            return self._create_local_dir_dataset_version(dataset_id, local_file_path, user_upload_data_path)
        elif pathlib.Path(local_file_path).is_file():
            return self._create_local_file_dataset_version(dataset_id, local_file_path, version_description)
        else:
            raise ValueError(f"本地路径既不是文件也不是目录: {local_file_path}")

    def _create_local_dir_dataset_version(
        self, dataset_id: int, local_file_path: str, user_upload_data_path: str
    ) -> int:
        """处理本地目录上传"""
        sts = self._get_sts()
        s3_client = SimpleS3Client(
            sts.endpoint, sts.access_key_id, sts.secret_access_key, session_token=sts.session_token
        )
        uid = uuid.uuid4().hex
        s3_target = f"s3://{sts.bucket}/dataset_workspace/{dataset_id}/{uid}"
        s3_csv_path = f"s3://{sts.bucket}/dataset_workspace/{dataset_id}/{uid}.csv"
        s3_status_path = f"s3://{sts.bucket}/dataset_workspace/{dataset_id}/{uid}.json"

        # 创建上传器并执行
        uploader = DataUploader(
            task_id=dataset_id,
            local_path=str(local_file_path),
            s3_target=s3_target,
            csv_path=s3_csv_path,
            status_path=s3_status_path,
            num_workers=40,
        )

        upload_stats = uploader.run(s3_client)
        req = CreateDatasetVersionByDataIngestReqV2(
            description=f"sdk 上传",
            dataset_id=dataset_id,
            s3_object_sheet=s3_csv_path,
            object_cnt=upload_stats.uploaded_count,
            data_size=upload_stats.uploaded_size,
            user_upload_data_path=user_upload_data_path,
            s3_target_path=s3_target,
        )
        return self.upload_by_data_ingest(req).id

    def _create_local_file_dataset_version(
        self, dataset_id: int, local_file_path: str, version_description: str
    ) -> int:
        """处理本地文件上传"""
        upload_data = self._upload.upload_file(local_file_path)
        upload_path = upload_data.path
        logger.info(f"文件上传成功：{local_file_path}")
        return self._dataset_version.upload(
            UploadDatasetVersionRequest(
                upload_path=upload_path,
                upload_type=UploadType.LOCAL,  # 本地上传类型
                dataset_id=dataset_id,
                description=version_description,
                parent_version_id=0,
            )
        )

    def _create_server_dataset_version(
        self, dataset_id: int, server_file_path: str | None, version_description: str
    ) -> int:
        """创建服务器文件数据集版本"""
        return self._dataset_version.upload(
            UploadDatasetVersionRequest(
                upload_path=server_file_path,
                upload_type=UploadType.SERVER_PATH,  # 服务器文件上传类型
                dataset_id=dataset_id,
                description=version_description,
                parent_version_id=0,
            )
        )

    def _get_version_tag(self, dataset_id: int, version_id: int) -> str:
        """获取版本标签"""
        detail = self._dataset.get(dataset_id)
        ver_num = next(
            (v.version for v in detail.versions if v.id == version_id),
            None,
        )
        if ver_num is None:
            ver_num = 1

        return f"{detail.name}/V{ver_num}"

    def _wait_for_version_success(self, version_id: int, timeout: int) -> None:
        """轮询等待版本状态变为成功"""
        start_ts = time.time()
        poll_interval = 10

        while True:
            ver_detail = self._dataset_version.get(version_id)
            status = ver_detail.status

            if status == DatasetVersionStatus.Success:
                logger.info("版本状态已成功")
                break

            if status == DatasetVersionStatus.Fail:
                raise APIError(f"版本构建失败：{ver_detail.message}")

            elapsed = time.time() - start_ts
            if elapsed > timeout:
                raise TimeoutError(f"等待版本成功超时（{timeout}s），当前状态：{status}")

            logger.debug(f"已等待 {elapsed:.0f}s，继续轮询…")
            time.sleep(poll_interval)

    def run_download(self, dataset_version_name: str, local_dir: str, worker: int = 4) -> None:
        """根据数据集版本名称下载对应的数据集文件。

        Args:
            dataset_version_name (str): 数据集版本名称。
            local_dir (str): 下载文件保存的本地目录路径。
            worker (int): 并发下载使用的线程数，默认为 4。

        Raises:
            APIError: 如果获取到的版本信息中没有 parquet_index_path，即无法进行下载时抛出异常。

        Returns:
            None
        """
        detail = self._dataset_version.get_by_name(dataset_version_name)
        if not detail.parquet_index_path:
            raise APIError("parquet_index_path 为空")
        dataset_download(detail.parquet_index_path, local_dir, worker)

    def list_datasets(
        self,
        *,
        page_size: int = 20,
        page_num: int = 1,
        name: str | None = None,
        tags: str | None = None,
        create_by: int | None = None,
        scope: str = "all",
    ) -> ListDatasetResp:
        """列表查询数据集

        Args:
            page_size: 每页大小，默认20
            page_num: 页码，从1开始，默认1
            name: 数据集名称筛选，可选
            tags: 标签筛选，可选
            create_by: 创建人筛选，可选
            scope: 范围筛选：created|shared|all，默认all

        Returns:
            ListDatasetResp: 数据集列表响应，包含分页信息和数据集列表
        """
        payload = ListDatasetReq(
            page_size=page_size, page_num=page_num, name=name, tags=tags, create_by=create_by, scope=scope
        )
        return self._dataset.list_datasets(payload)

    def list_dataset_versions(
        self,
        *,
        page_size: int = 10000000,
        page_num: int = 1,
        dataset_id: int | None = None,
        dataset_version_ids: str | None = None,
    ) -> ListDatasetVersionResp:
        """列表查询数据集版本

        Args:
            page_size: 每页大小，默认10000000
            page_num: 页码，从1开始，默认1
            dataset_id: 数据集ID筛选，可选
            dataset_version_ids: 数据集版本ID列表，逗号分隔，可选

        Returns:
            ListDatasetVersionResp: 数据集版本列表响应，包含分页信息和数据集版本列表
        """
        payload = ListDatasetVersionReq(
            page_size=page_size, page_num=page_num, dataset_id=dataset_id, dataset_version_ids=dataset_version_ids
        )
        return self._dataset_version.list_dataset_versions(payload)

    def upload_data(self, local_path: str) -> str:

        sts = self._get_sts()

        s3_client = Minio(
            endpoint=sts.endpoint,
            access_key=sts.access_key_id,
            secret_key=sts.secret_access_key,
            session_token=sts.session_token,
            secure=False,
        )
        s3_prefix = f"user_data/{uuid.uuid4().hex}"
        if Path(local_path).is_file():
            s3_key = f"{s3_prefix}/{Path(local_path).name}"
            s3_client.fput_object(bucket_name=sts.bucket, object_name=s3_prefix, file_path=local_path)
            return f"s3://{sts.bucket}/{s3_key}"
        else:
            upload_dir_to_s3(s3_client, local_path, sts.bucket, s3_prefix)
            return f"s3://{sts.bucket}/{s3_prefix}"


class _Dataset:
    def __init__(self, http: httpx.Client):
        self._http = http

    def create(self, payload: CreateDatasetRequest) -> int:
        try:
            resp = self._http.post(
                f"{_BASE}/datasets",
                json=payload.model_dump(by_alias=True, exclude_none=True),
            )
            if resp.status_code != 200:
                logger.error(f"http code {resp.status_code}: {resp.text}")
                raise APIError(f"http code {resp.status_code}: {resp.text}")
            wrapper = APIWrapper[CreateDatasetResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg} in  create dataset")
            return wrapper.data.id
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise ValueError

    def get(self, dataset_id: int) -> DatasetDetail:
        try:
            resp = self._http.get(f"{_BASE}/datasets/{dataset_id}")
            if resp.status_code != 200:
                raise APIError(f"backend code {resp.status_code}: {resp.text}")
            wrapper = APIWrapper[DatasetDetail].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise ValueError

    def list_datasets(self, payload: ListDatasetReq) -> ListDatasetResp:
        """列表查询数据集"""
        params = payload.model_dump(by_alias=True, exclude_none=True)
        resp = self._http.get(f"{_BASE}/datasets", params=params)
        if resp.status_code != 200:
            logger.error(f"http code {resp.status_code}: {resp.text}")
            raise APIError(f"backend code {resp.status_code}: {resp.text}", status=resp.status_code)
        try:
            wrapper = APIWrapper[ListDatasetResp].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise ValueError


class _DatasetVersion:
    def __init__(self, http: httpx.Client):
        self._http = http

    def create(self, payload: CreateDatasetVersionRequest) -> int:
        resp = self._http.post(
            f"{_BASE}/dataset-versions",
            json=payload.model_dump(by_alias=True, exclude_none=True),
        )
        if resp.status_code != 200:
            logger.error(f"http code {resp.status_code}: {resp.text}")
            raise APIError(f"backend code {resp.status_code}: {resp.text}", status=resp.status_code)
        try:
            wrapper = APIWrapper[CreateDatasetVersionResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data.id
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise ValueError

    def upload(self, payload: UploadDatasetVersionRequest) -> int:
        resp = self._http.post(
            f"{_BASE}/dataset-versions-upload",
            json=payload.model_dump(by_alias=True, exclude_none=True),
        )
        if resp.status_code != 200:
            logger.error(f"http code {resp.status_code}: {resp.text}")
            raise APIError(f"backend code {resp.status_code}: {resp.text}", status=resp.status_code)
        try:
            wrapper = APIWrapper[UploadDatasetVersionResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data.id
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise ValueError

    def get(self, version_id: int) -> DatasetVersionDetail:
        resp = self._http.get(f"{_BASE}/dataset-versions/{version_id}")
        if resp.status_code != 200:
            logger.error(f"http code {resp.status_code}: {resp.text}")
            raise APIError(f"backend code {resp.status_code}: {resp.text}", status=resp.status_code)
        try:
            wrapper = APIWrapper[DatasetVersionDetail].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise ValueError

    def get_by_name(self, version_name: str) -> DatasetVersionDetail:
        resp = self._http.get(f"{_BASE}/dataset-versions-detail", params={"name": version_name})
        if resp.status_code != 200:
            logger.error(f"http code {resp.status_code}: {resp.text}")
            raise APIError(f"backend code {resp.status_code}: {resp.text}", status=resp.status_code)
        try:
            wrapper = APIWrapper[DatasetVersionDetail].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise ValueError

    def list_dataset_versions(self, payload: ListDatasetVersionReq) -> ListDatasetVersionResp:
        """列表查询数据集版本"""
        params = payload.model_dump(by_alias=True, exclude_none=True)
        resp = self._http.get(f"{_BASE}/dataset-versions", params=params)
        if resp.status_code != 200:
            logger.error(f"http code {resp.status_code}: {resp.text}")
            raise APIError(f"backend code {resp.status_code}: {resp.text}", status=resp.status_code)
        try:
            wrapper = APIWrapper[ListDatasetVersionResp].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise ValueError

    def get_sts(self) -> StsResp:
        """获取STS临时凭证

        获取用于访问S3存储的临时凭证。

        Returns:
            StsResp: STS临时凭证信息

        Raises:
            APIError: 当API调用失败时抛出
        """
        resp = self._http.get(f"{_BASE}/dataset-versions/get-sts")
        if resp.status_code != 200:
            logger.error(f"http code {resp.status_code}: {resp.text}")
            raise APIError(f"backend code {resp.status_code}: {resp.text}", status=resp.status_code)
        try:
            wrapper = APIWrapper[StsResp].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise ValueError

    def upload_by_data_ingest(self, req: CreateDatasetVersionByDataIngestReqV2) -> CreateDatasetVersionResponse:
        """上传数据集版本（数据集导入）
        Args:
            req

        """
        resp = self._http.post(
            f"{_BASE}/dataset-versions/data-ingest",
            json=req.model_dump(),
        )
        if resp.status_code != 200:
            logger.error(f"http code {resp.status_code}: {resp.text}")
            raise APIError(f"backend code {resp.status_code}: {resp.text}", status=resp.status_code)
        try:
            wrapper = APIWrapper[CreateDatasetVersionResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise ValueError


class _Upload:
    def __init__(self, http: httpx.Client):
        self._http = http

    def upload_file(self, file_path: str) -> FileUploadData:
        if not os.path.isfile(file_path):
            raise FileNotFoundError(file_path)

        file_name = pathlib.Path(file_path).name
        mime_type = mimetypes.guess_type(file_name)[0] or "application/octet-stream"

        with open(file_path, "rb") as fp:
            resp = self._http.post(
                f"/dataset-mng/api/v1/uploads",
                files={"file": (file_name, fp, mime_type)},
                timeout=None,
            )

        try:
            wrapper = APIWrapper[FileUploadData].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise ValueError
