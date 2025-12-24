# !/usr/bin/env python
# -*- coding:utf-8 -*-
"""模型部署服务模块

当前封装的能力：
- 创建部署
- 查询部署列表
- 查询部署详情
- 删除部署
- 启动部署
- 强制启动部署
- 停止部署
- 终止部署
- 触发部署
- 查询部署Pods
- 查询部署日志
"""

from __future__ import annotations

import httpx
from loguru import logger
from pydantic import ValidationError

from ..exceptions import APIError, convert_errors
from ..models.common import APIWrapper
from ..models.model_deployment import (
    DeploymentCreateRequest,
    DeploymentCreateResponse,
    DeploymentListRequest,
    DeploymentListResponse,
    DeploymentDetail,
    DeploymentPodsResponse,
    DeploymentLogRequest,
    DeploymentLogResponse,
)

_BASE = "/mldp/api/v1"


class ModelDeploymentService:
    """模型部署业务封装"""

    def __init__(self, http: httpx.Client):
        self._deployment = _Deployment(http)
        self._http = http

    def list_deployments(self, payload: DeploymentListRequest) -> DeploymentListResponse:
        """分页查询部署列表

        Args:
            payload: 查询参数（分页、名称过滤、状态等）

        Returns:
            DeploymentListResponse: 包含分页信息与部署数据
        """
        return self._deployment.list(payload)

    def get_deployment(self, deployment_id: int) -> DeploymentDetail:
        """获取部署详情

        Args:
            deployment_id: 部署ID

        Returns:
            DeploymentDetail: 部署详情
        """
        return self._deployment.get(deployment_id)

    def create_deployment(self, payload: DeploymentCreateRequest) -> int:
        """创建部署

        Args:
            payload: 创建部署所需字段

        Returns:
            int: 后端生成的部署ID
        """
        return self._deployment.create(payload)

    def delete_deployment(self, deployment_id: int) -> None:
        """删除部署

        Args:
            deployment_id: 目标部署ID
        """
        self._deployment.delete(deployment_id)

    def start_deployment(self, deployment_id: int) -> None:
        """启动部署

        Args:
            deployment_id: 部署ID
        """
        self._deployment.start(deployment_id)



    def stop_deployment(self, deployment_id: int) -> None:
        """停止部署

        Args:
            deployment_id: 部署ID
        """
        self._deployment.stop(deployment_id)




    def get_deployment_pods(self, deployment_id: int) -> DeploymentPodsResponse:
        """查询部署的Pods

        Args:
            deployment_id: 部署ID

        Returns:
            DeploymentPodsResponse: Pod列表
        """
        return self._deployment.get_pods(deployment_id)

    def get_deployment_logs(
        self, deployment_id: int, pod_name: str | None = None, page_size: int = 20
    ) -> DeploymentLogResponse:
        """查询部署日志

        Args:
            deployment_id: 部署ID
            pod_name: Pod名称（可选）
            page_size: 每页数量

        Returns:
            DeploymentLogResponse: 日志内容
        """
        payload = DeploymentLogRequest(pod_name=pod_name, page_size=page_size)
        return self._deployment.get_logs(deployment_id, payload)

    @property
    def deployment(self) -> _Deployment:
        return self._deployment


class _Deployment:
    def __init__(self, http: httpx.Client):
        self._http = http

    def list(self, payload: DeploymentListRequest) -> DeploymentListResponse:
        try:
            resp = self._http.get(f"{_BASE}/deployment", params=payload.model_dump(by_alias=True, exclude_none=True))
            wrapper = APIWrapper[DeploymentListResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def get(self, deployment_id: int) -> DeploymentDetail:
        try:
            resp = self._http.get(f"{_BASE}/deployment/{deployment_id}")
            wrapper = APIWrapper[DeploymentDetail].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def create(self, payload: DeploymentCreateRequest) -> int:
        try:
            resp = self._http.post(f"{_BASE}/deployment", json=payload.model_dump(by_alias=True, exclude_none=True))
            wrapper = APIWrapper[DeploymentCreateResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data.id
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def delete(self, deployment_id: int) -> None:
        try:
            resp = self._http.delete(f"{_BASE}/deployment/{deployment_id}")
            wrapper = APIWrapper[dict].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def start(self, deployment_id: int) -> None:
        try:
            resp = self._http.post(f"{_BASE}/deployment/{deployment_id}/start")
            wrapper = APIWrapper[dict].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e



    def stop(self, deployment_id: int) -> None:
        try:
            resp = self._http.post(f"{_BASE}/deployment/{deployment_id}/stop")
            wrapper = APIWrapper[dict].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e





    def get_pods(self, deployment_id: int) -> DeploymentPodsResponse:
        try:
            resp = self._http.get(f"{_BASE}/deployment/{deployment_id}/pods")
            wrapper = APIWrapper[DeploymentPodsResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def get_logs(self, deployment_id: int, payload: DeploymentLogRequest) -> DeploymentLogResponse:
        try:
            resp = self._http.get(
                f"{_BASE}/deployment/{deployment_id}/logs",
                params=payload.model_dump(by_alias=True, exclude_none=True),
            )
            wrapper = APIWrapper[DeploymentLogResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e
