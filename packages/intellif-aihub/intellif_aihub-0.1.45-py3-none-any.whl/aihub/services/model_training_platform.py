# !/usr/bin/env python
# -*- coding:utf-8 -*-
"""模型训练平台服务模块

对接 **model‑training‑platform** 后端，以 **训练任务** 为核心提供常用业务能力，包括：

- **创建训练任务**
- **分页查询 / 获取训练详情**
- **停止训练任务**
- **查询训练 Pod 及其 Logs / Events / Spec**
- **查询训练相关用户、容器等辅助信息**
"""

from __future__ import annotations

import httpx
from loguru import logger
from pydantic import ValidationError

from ..exceptions import APIError, convert_errors
from ..models.common import APIWrapper
from ..models.model_training_platform import (
    CreateTrainingRequest,
    ListTrainingsRequest,
    ListTrainingsResponse,
    ListTrainingPodsRequest,
    GetTrainingPodLogsNewResponse,
    GetTrainingPodEventsResponse,
    Training,
    CreateTrainingResponse,
    ListTrainingUsersRequest,
    ListTrainingPodsResponse,
    GetTrainingPodSpecResponse,
    ListTrainingContainersRequest,
    ListTrainingUsersResponse,
    ListTrainingContainersResponse,
    Pod,
    ListStoragesResponse,
)

_BASE = "/model-training-platform/api/v1"


class ModelTrainingPlatformService:
    """训练任务业务封装"""

    def __init__(self, http: httpx.Client):
        self._training = _Training(http)
        self._storage = _Storage(http)

    def create_training(self, payload: CreateTrainingRequest) -> int:
        """创建训练任务

        Args:
            payload (CreateTrainingRequest): 创建训练任务参数

        Returns:
            int: 训练任务ID
        """
        return self._training.create(payload)

    def list_trainings(self, payload: ListTrainingsRequest) -> ListTrainingsResponse:
        """分页查询训练任务

        Args:
            payload: 分页与过滤条件，详见 ``ListTrainingsRequest``

        Returns:
            ListTrainingsResponse: 训练任务分页结果
        """
        return self._training.list(payload)

    def get_training(self, training_id: int) -> Training:
        """获取训练任务详情

        Args:
            training_id: 训练任务 ID

        Returns:
            Training: 训练任务完整信息
        """
        return self._training.get(training_id)

    def stop_training(self, training_id: int) -> None:
        """停止训练任务

        Args:
            training_id: 训练任务 ID
        """
        self._training.stop(training_id)

    def list_training_pods(self, training_id: int, payload: ListTrainingPodsRequest) -> ListTrainingPodsResponse:
        """查询训练任务的 Pod 列表

        Args:
            training_id: 训练任务 ID
            payload: 分页参数，详见 ``ListTrainingPodsRequest``

        Returns:
            ListTrainingPodsResponse: Pod 分页结果
        """
        return self._training.list_training_pods(training_id, payload)

    def get_training_pod(self, training_id: int, pod_id: int) -> Pod:
        """获取单个 Pod 详情

        Args:
            training_id: 训练任务 ID
            pod_id: Pod ID

        Returns:
            Pod: Pod 详细信息
        """
        return self._training.get_training_pod(training_id, pod_id)

    def get_pod_logs_new(self, training_id: int, pod_id: int) -> GetTrainingPodLogsNewResponse:
        """获取 Pod 日志

        Args:
            training_id: 训练任务 ID
            pod_id: Pod ID

        Returns:
            GetTrainingPodLogsNewResponse: 日志文件信息（名称 / URL 列表）
        """
        return self._training.get_training_logs_new(training_id, pod_id)

    def get_pod_spec(self, training_id: int, pod_id: int) -> GetTrainingPodSpecResponse:
        """获取 Pod Spec

        Args:
            training_id: 训练任务 ID
            pod_id: Pod ID

        Returns:
            GetTrainingPodSpecResponse: Pod Spec 字符串
        """
        return self._training.get_training_spec(training_id, pod_id)

    def get_pod_events(self, training_id: int, pod_id: int) -> GetTrainingPodEventsResponse:
        """获取 Pod Events

        Args:
            training_id: 训练任务 ID
            pod_id: Pod ID

        Returns:
            GetTrainingPodEventsResponse: 事件文本
        """
        return self._training.get_training_events(training_id, pod_id)

    def list_training_users(self, payload: ListTrainingUsersRequest) -> ListTrainingUsersResponse:
        """查询训练任务的用户列表

        Args:
            payload: 分页参数 ``ListTrainingUsersRequest``

        Returns:
            ListTrainingUsersResponse: 用户分页结果
        """
        return self._training.list_training_users(payload)

    def list_training_containers(self, payload: ListTrainingContainersRequest) -> ListTrainingContainersResponse:
        """查询训练容器信息

        Args:
            payload: 分页参数 ``ListTrainingContainersRequest``

        Returns:
            ListTrainingContainersResponse: 训练容器列表
        """
        return self._training.list_training_containers(payload)

    def list_storages(self) -> ListStoragesResponse:
        """获取存储列表

        Returns:
            ListStoragesResponse: 存储列表
        """
        return self._storage.list_storages()

    @property
    def training(self) -> _Training:
        return self._training

    @property
    def storage(self) -> _Storage:
        return self._storage


class _Training:

    def __init__(self, http: httpx.Client):
        self._http = http

    def create(self, payload: CreateTrainingRequest) -> int:
        try:
            resp = self._http.post(f"{_BASE}/trainings", json=payload.model_dump(by_alias=True, exclude_none=True))
            wrapper = APIWrapper[CreateTrainingResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data.id
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def list(self, payload: ListTrainingsRequest) -> ListTrainingsResponse:
        try:
            resp = self._http.get(f"{_BASE}/trainings", params=payload.model_dump(by_alias=True, exclude_none=True))
            wrapper = APIWrapper[ListTrainingsResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def get(self, training_id: int) -> Training:
        try:
            resp = self._http.get(f"{_BASE}/trainings/{training_id}")
            wrapper = APIWrapper[Training].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def stop(self, training_id: int) -> None:
        try:
            resp = self._http.post(f"{_BASE}/trainings/{training_id}/stop")
            wrapper = APIWrapper[dict].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def list_training_pods(self, training_id: int, payload: ListTrainingPodsRequest) -> ListTrainingPodsResponse:
        try:
            resp = self._http.get(
                f"{_BASE}/trainings/{training_id}/pods", params=payload.model_dump(by_alias=True, exclude_none=True)
            )
            wrapper = APIWrapper[ListTrainingPodsResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def get_training_pod(self, training_id: int, pod_id: int) -> Pod:
        try:
            resp = self._http.get(f"{_BASE}/trainings/{training_id}/pods/{pod_id}")
            wrapper = APIWrapper[Pod].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def get_training_logs_new(self, training_id: int, pod_id: int) -> GetTrainingPodLogsNewResponse:
        try:
            resp = self._http.get(f"{_BASE}/trainings/{training_id}/pods/{pod_id}/logs/new")
            wrapper = APIWrapper[GetTrainingPodLogsNewResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def get_training_spec(self, training_id: int, pod_id: int) -> GetTrainingPodSpecResponse:
        try:
            resp = self._http.get(f"{_BASE}/trainings/{training_id}/pods/{pod_id}/spec")
            wrapper = APIWrapper[GetTrainingPodSpecResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def get_training_events(self, training_id: int, pod_id: int) -> GetTrainingPodEventsResponse:
        try:
            resp = self._http.get(f"{_BASE}/trainings/{training_id}/pods/{pod_id}/events")
            wrapper = APIWrapper[GetTrainingPodEventsResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def list_training_users(self, payload: ListTrainingUsersRequest) -> ListTrainingUsersResponse:
        try:
            resp = self._http.get(f"{_BASE}/training-users", params=payload.model_dump(by_alias=True))
            wrapper = APIWrapper[ListTrainingUsersResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def list_training_containers(self, payload: ListTrainingContainersRequest) -> ListTrainingContainersResponse:
        try:
            resp = self._http.get(f"{_BASE}/training-containers", params=payload.model_dump(by_alias=True))
            wrapper = APIWrapper[ListTrainingContainersResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e


class _Storage:

    def __init__(self, http: httpx.Client):
        self._http = http

    def list_storages(self) -> ListStoragesResponse:
        try:
            resp = self._http.get(f"{_BASE}/storages")
            wrapper = APIWrapper[ListStoragesResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e
