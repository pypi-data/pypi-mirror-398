# !/usr/bin/env python
# -*-coding:utf-8 -*-
"""制品管理服务模块

封装 **Artifact‑Management** 相关接口，核心能力包括：

- **创建制品** – 支持单文件或目录一次性打包上传
- **上传制品** – 自动分片、断点续传，兼容大文件
- **制品查询** – 按 *Run ID* / 路径精准过滤
- **制品下载** – 支持文件级与目录级批量下载

制品类型覆盖 *数据集、模型、指标、日志、检查点、图像、预测结果* 等
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

import httpx
import minio
from loguru import logger
from pydantic import ValidationError

from ..exceptions import APIError, convert_errors
from ..models.artifact import (
    CreateArtifactsReq,
    CreateArtifactsResponseData,
    ArtifactResp,
    InfinityPageSize,
    ArtifactRespData,
    ArtifactType,
    StsResp,
)
from ..models.common import APIWrapper
from ..utils.s3 import S3_path_to_info, upload_dir_to_s3, download_dir_from_s3

# 制品管理API的基础路径
_Base = "/artifact-management/api/v1"


class ArtifactService:
    """制品管理服务类，该类提供了制品管理相关的功能，包括创建制品、上传制品、获取制品信息等。


    Methods:
        get_by_run_id: 使用run_id获取制品
        create_artifact: 创建一个制品文件
        create_artifacts: 从目录创建一个制品
        download_artifacts: 下载制品

    """

    def __init__(self, http: httpx.Client):
        """初始化制品管理服务

        Args:
            http: HTTP客户端实例
        """
        self._http = http
        self._Artifact = _Artifact(http)
        self.sts = None
        self.s3_client = None

    @property
    def _artifact(self) -> _Artifact:
        """获取内部制品管理实例

        Returns:
            _Artifact: 内部制品管理实例
        """
        return self._Artifact

    def _create(self, payload: CreateArtifactsReq) -> CreateArtifactsResponseData:
        """创建制品（内部方法）

        Args:
            payload: 创建制品请求参数

        Returns:
            CreateArtifactsResponseData: 创建制品响应数据
        """
        return self._artifact.create(payload)

    def _upload_done(self, artifact_id: int) -> None:
        """标记制品上传完成

        Args:
            artifact_id: 制品ID
        """
        return self._artifact.upload_done(artifact_id)

    def _get_sts(self) -> StsResp:
        """获取STS临时凭证

        Returns:
            StsResp: STS临时凭证信息
        """
        return self._artifact.get_sts()

    def get_by_run_id(self, run_id: str, artifact_path: Optional[str] = None) -> List[ArtifactResp]:
        """根据运行ID获取制品列表

        Args:
            run_id: 运行ID
            artifact_path: 制品路径，如果指定则只返回匹配的制品

        Returns:
            List[ArtifactResp]: 制品列表

        Raises:
            APIError: 当API调用失败时抛出
        """
        return self._artifact.get_by_run_id(run_id, artifact_path)

    def create_artifact(
        self,
        local_path: str,
        artifact_path: Optional[str] = None,
        run_id: Optional[str] = None,
        artifact_type: ArtifactType = ArtifactType.other,
    ) -> None:
        """创建单个文件制品并上传

        该方法用于将本地文件上传为制品。过程包括：
        1. 获取STS临时凭证
        2. 创建S3客户端
        3. 检查本地文件是否存在
        4. 创建制品记录
        5. 上传文件到S3
        6. 标记上传完成

        Args:
            local_path (str): 本地文件路径
            artifact_path (str): 制品路径，如果为None则使用本地文件名
            run_id (str): 运行ID，关联制品与特定运行
            artifact_type (ArtifactType): 制品类型，默认为other

        Raises:
            ValueError: 当本地文件不存在时抛出
            APIError: 当API调用失败时抛出
        """
        logger.info(f"log artifact: {artifact_path},local path: {local_path} ")
        if self.s3_client is None:
            self.sts = self._get_sts()
            self.s3_client = minio.Minio(
                endpoint=self.sts.endpoint,
                access_key=self.sts.access_key_id,
                secret_key=self.sts.secret_access_key,
                session_token=self.sts.session_token,
                secure=False,
            )

        # 检查文件是否存在
        if not os.path.exists(local_path):
            raise ValueError(f"File {local_path} does not exist")
        req = CreateArtifactsReq(
            entity_id=run_id,
            entity_type=artifact_type,
            src_path=artifact_path,
            is_dir=False,
        )
        resp = self._create(req)
        bucket, object_name = S3_path_to_info(resp.s3_path)

        self.s3_client.fput_object(bucket, object_name, local_path)
        self._upload_done(resp.id)
        logger.info(f"log artifact done: {artifact_path}")
        return

    def create_artifacts(
        self,
        local_dir: str,
        artifact_path: Optional[str] = None,
        run_id: Optional[str] = None,
        artifact_type: ArtifactType = ArtifactType.other,
    ) -> None:
        """创建目录制品并上传

        该方法用于将本地目录上传为制品。过程包括：
        1. 获取STS临时凭证
        2. 创建S3客户端
        3. 检查本地目录是否存在
        4. 创建制品记录
        5. 上传目录内容到S3
        6. 标记上传完成

        Args:
            local_dir (str): 本地目录路径
            artifact_path (str): 制品路径，如果为None则使用本地目录名
            run_id (str): 运行ID，关联制品与特定运行
            artifact_type (ArtifactType): 制品类型，默认为other

        Raises:
            ValueError: 当本地目录不存在时抛出
            APIError: 当API调用失败时抛出
        """
        if self.s3_client is None:
            self.sts = self._get_sts()
            self.s3_client = minio.Minio(
                endpoint=self.sts.endpoint,
                access_key=self.sts.access_key_id,
                secret_key=self.sts.secret_access_key,
                session_token=self.sts.session_token,
                secure=False,
            )

        logger.info(f"log artifact: {artifact_path},local path: {local_dir} ")
        if not os.path.exists(local_dir):
            raise ValueError(f"File {local_dir} does not exist")
        req = CreateArtifactsReq(
            entity_id=run_id,
            entity_type=artifact_type,
            src_path=artifact_path,
            is_dir=True,
        )
        resp = self._create(req)
        bucket, object_name = S3_path_to_info(resp.s3_path)
        upload_dir_to_s3(self.s3_client, local_dir, bucket, object_name)
        self._upload_done(resp.id)
        logger.info(f"log artifact done: {artifact_path}")
        return

    def download_artifacts(self, run_id: str, artifact_path: Optional[str], local_dir: str) -> None:
        """下载制品

        Args:
            run_id: 运行ID
            artifact_path: 制品路径
            local_dir: 本地目录路径

        Raises:
            APIError: 当API调用失败时抛出
        """
        if self.s3_client is None:
            self.sts = self._get_sts()
            self.s3_client = minio.Minio(
                endpoint=self.sts.endpoint,
                access_key=self.sts.access_key_id,
                secret_key=self.sts.secret_access_key,
                session_token=self.sts.session_token,
                secure=False,
            )
        artifacts = self.get_by_run_id(run_id, artifact_path)

        for artifact_item in artifacts:
            bucket, object_name = S3_path_to_info(artifact_item.s3_path)
            if artifact_item.is_dir:
                download_dir_from_s3(self.s3_client, bucket, object_name, local_dir)
            else:
                self.s3_client.fget_object(bucket, object_name, str(Path(local_dir) / artifact_item.src_path))

        logger.info(f"download artifact done: {artifact_path}")
        return


class _Artifact:
    """内部制品管理类

    该类提供了与制品管理API交互的底层方法。
    通常不直接使用该类，而是通过ArtifactService类访问其功能。
    """

    def __init__(self, http: httpx.Client):
        """初始化内部制品管理类

        Args:
            http: HTTP客户端实例
        """
        self._http = http

    def create(self, payload: CreateArtifactsReq) -> CreateArtifactsResponseData:
        """创建制品记录

        Args:
            payload: 创建制品请求参数

        Returns:
            CreateArtifactsResponseData: 创建制品响应数据

        Raises:
            APIError: 当API调用失败时抛出
        """
        try:
            resp = self._http.post(f"{_Base}/artifacts", json=payload.model_dump())
            wrapper = APIWrapper[CreateArtifactsResponseData].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def upload_done(self, artifact_id: int) -> None:
        """标记制品上传完成

        在制品文件上传到S3后，需要调用此方法标记上传完成。

        Args:
            artifact_id: 制品ID

        Raises:
            APIError: 当API调用失败时抛出
        """
        try:
            resp = self._http.post(f"{_Base}/artifacts/{artifact_id}/uploaded")
            wrapper = APIWrapper.model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def get_by_run_id(self, run_id: str, artifact_path: Optional[str]) -> List[ArtifactResp]:
        """根据运行ID获取制品列表

        Args:
            run_id: 运行ID
            artifact_path: 制品路径，如果指定则只返回匹配的制品

        Returns:
            List[ArtifactResp]: 制品列表

        Raises:
            APIError: 当API调用失败时抛出
        """
        try:
            resp = self._http.get(f"{_Base}/artifacts?entity_id={run_id}&page_num=1&page_size={InfinityPageSize}")
            wrapper = APIWrapper[ArtifactRespData].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            if artifact_path:
                return [artifact for artifact in wrapper.data.data if artifact.src_path == artifact_path]
            else:
                return wrapper.data.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def get_sts(self) -> StsResp:
        """获取STS临时凭证

        获取用于访问S3存储的临时凭证。

        Returns:
            StsResp: STS临时凭证信息

        Raises:
            APIError: 当API调用失败时抛出
        """
        try:
            resp = self._http.get(f"{_Base}/artifacts/get-sts")
            logger.info(f"get sts: {resp.text}")
            wrapper = APIWrapper[StsResp].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e
