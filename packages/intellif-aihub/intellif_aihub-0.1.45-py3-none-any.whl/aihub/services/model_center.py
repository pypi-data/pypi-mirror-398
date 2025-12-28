# !/usr/bin/env python
# -*- coding:utf-8 -*-
"""模型中心服务模块

当前封装的能力：
- 分页查询模型列表
- 获取单个模型详情
- 新建模型
- 编辑模型
- 删除模型
- 上传模型
- 下载模型
- 查询模型 DB 信息
"""

from __future__ import annotations

import io
import os
import time

import httpx
import minio
from loguru import logger
from pydantic import ValidationError
from typer.models import OptionInfo

from .tag_resource_management import TagResourceManagementService
from ..exceptions import APIError, convert_errors
from ..models.tag_resource_management import ModelTag
from ..models.artifact import StsResp
from ..models.common import APIWrapper
from ..models.model_center import (
    ListModelsRequest,
    ListModelsResponse,
    ModelCardDetail,
    CreateModelRequest,
    CreateModelResponse,
    EditModelRequest,
    ModelDb,
    InferService,
    DataFormat,
    TaskType,
    Framework,
    Licence,
    Language,
    CreateModelEvalTaskRequest,
    CreateModelEvalTaskResponse,
    GetModelTasksRequest,
    GetModelTasksResponse,
)
from ..utils.di import SimpleS3Client, DataUploader
from ..utils.s3 import parse_s3_path_strict, download_dir_from_s3_to_local

_BASE = "/model-center/api/v1"
MODEL_STATUS_INIT = "init"
MODEL_STATUS_UPLOADING = "uploading"
MODEL_STATUS_READY = "ready"
MODEL_STATUS_FAILED = "failed"


class ModelCenterService:
    """模型中心业务封装"""

    def __init__(self, http: httpx.Client):
        self._model = _Model(http)
        self._http = http

    def list_models(self, payload: ListModelsRequest) -> ListModelsResponse:
        """分页查询模型列表

        Args:
            payload: 查询参数（分页、名称过滤等）

        Returns:
            ListModelsResponse: 包含分页信息与模型数据
        """
        return self._model.list(payload)

    def get_model(self, model_id: int) -> ModelCardDetail:
        """获取模型详情

        Args:
            model_id: 模型 ID

        Returns:
            ModelCardDetail: 模型详情（含 README、模型树、基模型等）
        """
        return self._model.get(model_id)

    def create_model(self, payload: CreateModelRequest) -> int:
        """创建模型 ,兼容性接口将在未来版本移除，请使用 Create

        Args:
            payload: 创建模型所需字段

        Returns:
            int: 后端生成的模型 ID
        """
        return self._model.create(payload)

    def create(
        self,
        name: str,
        description: str = "",
        is_public: bool = True,
        data_format: DataFormat | None = None,
        task_type: TaskType | None = None,
        framework: Framework | None = None,
        licence: Licence | None = None,
        language: Language | None = None,
    ) -> int:
        """创建模型

        Args:
            is_public:  是否公开
            name: 模型名称
            description: 模型描述
            data_format: 数据格式
            task_type: 任务类型
            framework: 框架
            licence: 许可证
            language: 语言

        Returns:
            int: 后端生成的模型 ID
        """
        # 获取所有模型标签
        tag_service = TagResourceManagementService(self._http)
        model_tags = tag_service.select_model_tags()

        # 定义枚举参数与 category key 的映射
        tag_mapping = {
            "model.data_format": data_format.value if data_format else None,
            "model.task_type": task_type.value if task_type else None,
            "model.framework": framework.value if framework else None,
            "model.licence": licence.value if licence else None,
            "model.language": language.value if language else None,
        }

        # 匹配 tag ID
        tag_ids = []
        for model_tag in model_tags:
            category_key = model_tag.category.key
            target_value = tag_mapping.get(category_key)
            if target_value is not None:
                for tag in model_tag.tags:
                    if tag.value == target_value:
                        tag_ids.append(tag.id)
                        break

        # 构建请求并创建模型
        payload = CreateModelRequest(
            name=name,
            description=description,
            tags=",".join(str(tid) for tid in tag_ids) if tag_ids else None,
            is_public=is_public,
        )
        return self._model.create(payload)

    def edit_model(self, model_id: int, payload: EditModelRequest) -> None:
        """编辑模型信息

        Args:
            model_id: 模型ID
            payload: 编辑模型信息
        """
        self._model.edit(model_id, payload)

    def delete_model(self, model_id: int) -> None:
        """删除模型

        Args:
            model_id: 目标模型 ID
        """
        self._model.delete(model_id)

    def get_model_db(self, id: int | None = None, name: str | None = None) -> ModelDb:
        """通过 id 或 name 查询模型 DB 信息

        Args:
            id: 模型id
            name: 模型名称

        Returns:
            ModelDb: 模型在DB中的信息
        """
        return self._model.get_model_db(id=id, name=name)

    def upload(
        self,
        model_name: str | None = None,
        local_dir: str | None = None,
        model_id: int | None = None,
        timeout_seconds: int = 3600,
    ) -> None:
        """上传模型

        Args:
            local_dir: 本地模型目录
            model_id: 模型 id
            model_name: 模型名称
            timeout_seconds: 超时时间
        """
        return self._model.upload(
            local_dir=local_dir,
            model_id=model_id,
            model_name=model_name,
            timeout_seconds=timeout_seconds,
        )

    def download(
        self,
        model_name: str | None = None,
        local_dir: str | None = None,
        model_id: int | None = None,
    ) -> None:
        """下载模型

        Args:
            local_dir: 要下载到的本地目录
            model_id: 模型id
            model_name: 模型名称
        """
        return self._model.download(local_dir=local_dir, model_id=model_id, model_name=model_name)

    def get_infer_service_by_id(self, service_id: int) -> InferService:
        """通过id获取推理服务信息

        Args:
            service_id: 推理服务id
        Returns:
            InferService
        """
        return self._model.get_infer_service(service_id)

    def create_eval_task(
        self,
        model_id: int,
        payload: CreateModelEvalTaskRequest,
    ) -> int:
        """创建模型评测任务

        Args:
            model_id: 模型ID
            payload: 评测任务参数

        Returns:
            int: 任务ID
        """
        return self._model.create_eval_task(model_id, payload)

    def get_model_tasks(
        self,
        model_id: int,
        payload: GetModelTasksRequest | None = None,
    ) -> GetModelTasksResponse:
        """获取模型任务列表

        Args:
            model_id: 模型ID
            payload: 分页参数（可选）

        Returns:
            GetModelTasksResponse: 任务列表
        """
        if payload is None:
            payload = GetModelTasksRequest()
        return self._model.get_model_tasks(model_id, payload)

    @property
    def model(self) -> _Model:
        return self._model


class _Model:

    def __init__(self, http: httpx.Client):
        self._http = http

    def list(self, payload: ListModelsRequest) -> ListModelsResponse:
        try:
            resp = self._http.get(f"{_BASE}/models", params=payload.model_dump(by_alias=True, exclude_none=True))
            wrapper = APIWrapper[ListModelsResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def get(self, model_id: int) -> ModelCardDetail:
        try:
            resp = self._http.get(f"{_BASE}/models/{model_id}")
            wrapper = APIWrapper[ModelCardDetail].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def create(self, form: CreateModelRequest) -> int:
        files = {
            "name": (None, form.name),
            "is_public": (None, "true" if bool(form.is_public) else "false"),
        }
        if form.description is not None:
            files["description"] = (None, form.description)
        if form.tags is not None:
            files["tags"] = (None, form.tags)

        if form.readme_content:
            md_text = (
                form.readme_content
                if (form.readme_content and form.readme_content.strip())
                else f"# {form.name}\n\nAutogenerated at {int(time.time())}\n"
            )
            files["readme_file"] = ("README.md", io.BytesIO(md_text.encode("utf-8")), "text/markdown")

        try:
            resp = self._http.post(f"{_BASE}/models", files=files)
            wrapper = APIWrapper[CreateModelResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data.id
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def edit(self, model_id: int, payload: EditModelRequest) -> None:
        try:
            resp = self._http.put(
                f"{_BASE}/models/{model_id}", json=payload.model_dump(by_alias=True, exclude_none=True)
            )
            wrapper = APIWrapper[dict].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def delete(self, model_id: int) -> None:
        try:
            resp = self._http.delete(f"{_BASE}/models/{model_id}")
            wrapper = APIWrapper[dict].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def get_model_db(self, *, id: int | None = None, name: str | None = None) -> ModelDb:
        if id is None and (name is None or name == ""):
            raise ValueError("id or name is required")

        params = {"id": id} if id is not None else {"name": name}
        try:
            resp = self._http.get(f"{_BASE}/models/db", params=params)
            if resp.status_code != 200:
                logger.error(f"http code {resp.status_code}: {resp.text}")
                raise APIError(f"http code {resp.status_code}: {resp.text}", status=resp.status_code)
            wrapper = APIWrapper[ModelDb].model_validate(resp.json())
            if wrapper.code != 0:
                logger.error(f"backend code {wrapper.code}: {wrapper.msg}")
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def _get_sts(self) -> StsResp:
        try:
            resp = self._http.get(f"{_BASE}/models/get-sts")
            wrapper = APIWrapper[StsResp].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def upload(
        self,
        *,
        local_dir: str,
        model_id: int | None = None,
        model_name: str | None = None,
        timeout_seconds: int = 3600,
    ) -> None:
        if (model_id is None) and (not model_name):
            raise ValueError("id or name is required")
        if not local_dir or not os.path.exists(local_dir):
            raise ValueError(f"local_dir not exists: {local_dir}")

        # 1. get db info
        db_info = self.get_model_db(id=model_id, name=model_name)
        resolved_id = db_info.id
        s3_target = db_info.object_storage_path
        s3_csv_path = db_info.csv_file_path
        s3_status_path = db_info.task_status_s3_path

        # 2. upload file to s3
        sts = self._get_sts()
        s3_client = SimpleS3Client(
            sts.endpoint, sts.access_key_id, sts.secret_access_key, session_token=sts.session_token
        )
        uploader = DataUploader(
            task_id=resolved_id,
            local_path=local_dir,
            s3_target=s3_target,
            csv_path=s3_csv_path,
            status_path=s3_status_path,
            num_workers=40,
        )
        stats = uploader.run(s3_client)

        # 3. invoke model center upload interface
        payload = {
            "model_id": resolved_id,
            "object_cnt": stats.uploaded_count,
            "data_size": stats.uploaded_size,
        }
        try:
            resp = self._http.post(f"{_BASE}/models/upload", json=payload)
            wrapper = APIWrapper[dict].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

        logger.info(f"模型上传本地处理完成，model_id={resolved_id}，等待服务端处理，3s 后开始轮询状态…")
        time.sleep(3)

        start_ts = time.time()
        poll_interval = 10
        while True:
            db_cur = self.get_model_db(id=resolved_id)
            status = (db_cur.status or "").lower()

            if status == MODEL_STATUS_READY:
                logger.info(f"模型处理成功：model_id={resolved_id}, status=ready")
                return

            if status == MODEL_STATUS_FAILED:
                logger.error(f"模型处理失败：model_id={resolved_id}, status=failed")
                raise APIError(f"模型处理失败：model_id={resolved_id}, status=failed")

            elapsed = time.time() - start_ts
            if elapsed > timeout_seconds:
                logger.error(f"等待模型就绪超时：model_id={resolved_id}, waited={int(elapsed)}s")
                raise TimeoutError(f"等待模型就绪超时：model_id={resolved_id}, waited={int(elapsed)}s")

            logger.info(f"[Model Upload] id={resolved_id} 已等待 {int(elapsed)}s，当前 status={status}，继续轮询…")
            time.sleep(poll_interval)

    def download(self, *, local_dir: str, model_id: int | None = None, model_name: str | None = None) -> None:
        if (model_id is None) and (not model_name):
            raise ValueError("id or name is required")
        if not local_dir:
            raise ValueError("local_dir is required")

        db_info = self.get_model_db(id=model_id, name=model_name)

        # 判断是否允许下载
        status = (db_info.status or "").lower()
        if status != "ready":
            raise APIError(f"model is not ready for download (current status: {db_info.status})")
        if not (db_info.parquet_index_path or "").strip():
            raise APIError("parquet index path is required and cannot be empty")

        s3_dir_path = db_info.object_storage_path
        if not s3_dir_path or not s3_dir_path.startswith("s3://"):
            raise APIError(f"invalid object_storage_path: {s3_dir_path}")

        sts = self._get_sts()
        s3_client = minio.Minio(
            endpoint=sts.endpoint,
            access_key=sts.access_key_id,
            secret_key=sts.secret_access_key,
            session_token=sts.session_token,
            secure=False,
        )

        bucket, object_name = parse_s3_path_strict(s3_dir_path)
        if not bucket or not object_name:
            raise APIError(f"invalid s3 path: {s3_dir_path}")

        os.makedirs(local_dir, exist_ok=True)
        download_dir_from_s3_to_local(s3_client, bucket, object_name, local_dir)

    def get_infer_service(self, service_id: int) -> InferService:
        try:
            resp = self._http.get(f"{_BASE}/infer-services/{service_id}")
            wrapper = APIWrapper[InferService].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def create_eval_task(self, model_id: int, payload: CreateModelEvalTaskRequest) -> int:
        """创建模型评测任务

        Args:
            model_id: 模型ID
            payload: 评测任务参数

        Returns:
            int: 任务ID
        """
        try:
            resp = self._http.post(
                f"{_BASE}/models/{model_id}/eval_task",
                json=payload.model_dump(by_alias=True, exclude_none=True),
            )
            wrapper = APIWrapper[CreateModelEvalTaskResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data.id
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def get_model_tasks(self, model_id: int, payload: GetModelTasksRequest) -> GetModelTasksResponse:
        """获取模型任务列表

        Args:
            model_id: 模型ID
            payload: 分页参数

        Returns:
            GetModelTasksResponse: 任务列表
        """
        try:
            resp = self._http.get(
                f"{_BASE}/models/{model_id}/tasks",
                params=payload.model_dump(by_alias=True, exclude_none=True),
            )
            wrapper = APIWrapper[GetModelTasksResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e
