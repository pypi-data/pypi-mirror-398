# !/usr/bin/env python
# -*- coding:utf-8 -*-
"""配额调度服务模块

封装 **quota‑schedule‑management** 后端接口，围绕 **配额调度任务** 提供常用能力：

- **创建 / 查询 / 停止调度任务**
- **Pod 维度信息**（列表 / Logs / Spec / Events）
- **GPU 资源概览、活跃用户、容器信息** 等辅助查询
- **Pre‑Stop** 机制：进程内检测平台下发的优雅终止信号
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List

import httpx
from loguru import logger
from pydantic import ValidationError

from ..exceptions import APIError, convert_errors
from ..models.common import APIWrapper
from ..models.quota_schedule_management import (
    CreateTaskRequest,
    CreateTaskResponse,
    ListTasksRequest,
    ListTasksResponse,
    Task,
    ListTaskPodsRequest,
    ListTaskPodsResponse,
    Pod,
    PodLogInfo,
    GetTaskPodLogsNewResponse,
    GetTaskPodSpecResponse,
    GetTaskPodEventsResponse,
    ListTaskUsersRequest,
    ListTaskUsersResponse,
    GetMetricsOverviewRequest,
    GetMetricsOverviewResponse,
)

_ENV_KEY = "PRE_STOP_SENTINEL_FILE"
_DEFAULT_SENTINEL = "/tmp/pre_stop_sentinel_file"
_SENTINEL_PATH = Path(os.getenv(_ENV_KEY, _DEFAULT_SENTINEL))
_BASE = "/quota-schedule-management/api/v1"


def is_pre_stopped() -> bool:
    """判断当前进程是否已收到 *pre‑stop* 信号

    该信号由调度平台通过创建哨兵文件的方式下发。文件路径可通过环境变量 ``PRE_STOP_SENTINEL_FILE`` 覆盖，
    默认为``/tmp/pre_stop_sentinel_file``。

    Returns:
        bool:  若哨兵文件存在，返回 ``True``，表示应尽快停止任务。
    """
    return _SENTINEL_PATH.exists()


class PreStopService:
    @staticmethod
    def is_pre_stopped() -> bool:
        return is_pre_stopped()


class QuotaScheduleManagementService:
    """配额调度任务业务封装"""

    def __init__(self, http: httpx.Client):
        self._task = _Task(http)

    def create_task(self, payload: CreateTaskRequest) -> int:
        """创建调度任务

        Args:
            payload: 创建任务的各项参数，详见 ``CreateTaskRequest``

        Returns:
            int: 后端生成的任务 ID
        """
        return self._task.create(payload)

    def list_tasks(self, payload: ListTasksRequest) -> ListTasksResponse:
        """分页查询任务列表

        Args:
            payload: 分页 / 过滤参数，详见 ``ListTasksRequest``

        Returns:
            ListTasksResponse: 任务分页结果
        """
        return self._task.list(payload)

    def get_task(self, task_id: int) -> Task:
        """获取任务详情

        Args:
            task_id: 任务 ID

        Returns:
            Task: 任务完整信息
        """
        return self._task.get(task_id)

    def stop_task(self, task_id: int) -> None:
        """停止任务

        Args:
            task_id: 任务 ID
        """
        self._task.stop(task_id)

    def list_task_pods(self, task_id: int, payload: ListTaskPodsRequest) -> ListTaskPodsResponse:
        """分页查询任务的 Pod 列表

        Args:
            task_id: 调度任务 ID
            payload: 分页参数，见 :class:`ListTaskPodsRequest`

        Returns:
            ListTaskPodsResponse: Pod 列表及分页信息
        """
        return self._task.list_pods(task_id, payload)

    def get_task_pod(self, task_id: int, pod_id: int) -> Pod:
        """获取单个 Pod 详情

        Args:
            task_id: 调度任务 ID
            pod_id:  Pod ID（数据库主键）

        Returns:
            Pod: Pod 详细信息
        """
        return self._task.get_pod(task_id, pod_id)

    def get_pod_logs_new(self, task_id: int, pod_id: int) -> List[PodLogInfo]:
        """获取新版日志

        Args:
            task_id: 调度任务 ID
            pod_id:  Pod ID

        Returns:
            list[PodLogInfo]: 每条日志文件的名称与下载地址
        """
        return self._task.get_logs_new(task_id, pod_id).logs

    def get_pod_spec(self, task_id: int, pod_id: int) -> str:
        """获取 Pod 运行时 Spec（YAML）

        Args:
            task_id: 调度任务 ID
            pod_id:  Pod ID

        Returns:
            str: Pod 描述 YAML 字符串
        """
        return self._task.get_spec(task_id, pod_id).spec

    def get_pod_events(self, task_id: int, pod_id: int) -> str:
        """获取 Pod 事件

        Args:
            task_id: 调度任务 ID
            pod_id:  Pod ID

        Returns:
            str: 事件文本（kubectl describe events）
        """
        return self._task.get_events(task_id, pod_id).events

    def list_task_users(self, payload: ListTaskUsersRequest) -> ListTaskUsersResponse:
        """查询任务的用户列表

        Args:
            payload: 分页参数，见 :class:`ListTaskUsersRequest`

        Returns:
            ListTaskUsersResponse: 用户列表及分页信息
        """
        return self._task.list_users(payload)

    def get_metrics_overview(self, payload: GetMetricsOverviewRequest) -> GetMetricsOverviewResponse:
        """获取虚拟集群维度的 GPU 使用概览

        Args:
            payload: 分页参数，见 :class:`GetMetricsOverviewRequest`

        Returns:
            GetMetricsOverviewResponse: 各虚拟集群资源统计
        """
        return self._task.get_metrics_overview(payload)

    @property
    def task(self) -> _Task:
        return self._task


class _Task:

    def __init__(self, http: httpx.Client):
        self._http = http

    def create(self, payload: CreateTaskRequest) -> int:
        try:
            resp = self._http.post(f"{_BASE}/tasks", json=payload.model_dump(by_alias=True, exclude_none=True))
            wrapper = APIWrapper[CreateTaskResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data.id
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise ValueError

    def list(self, payload: ListTasksRequest) -> ListTasksResponse:
        try:
            resp = self._http.get(f"{_BASE}/tasks", params=payload.model_dump(by_alias=True, exclude_none=True))
            wrapper = APIWrapper[ListTasksResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def get(self, task_id: int) -> Task:
        try:
            resp = self._http.get(f"{_BASE}/tasks/{task_id}")
            wrapper = APIWrapper[Task].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def stop(self, task_id: int) -> None:
        try:
            resp = self._http.post(f"{_BASE}/tasks/{task_id}/stop")
            wrapper = APIWrapper[dict].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def list_pods(self, task_id: int, payload: ListTaskPodsRequest) -> ListTaskPodsResponse:
        try:
            resp = self._http.get(f"{_BASE}/tasks/{task_id}/pods", params=payload.model_dump(by_alias=True))
            wrapper = APIWrapper[ListTaskPodsResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def get_pod(self, task_id: int, pod_id: int) -> Pod:
        try:
            resp = self._http.get(f"{_BASE}/tasks/{task_id}/pods/{pod_id}")
            wrapper = APIWrapper[Pod].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def get_logs_new(self, task_id: int, pod_id: int) -> GetTaskPodLogsNewResponse:
        try:
            resp = self._http.get(f"{_BASE}/tasks/{task_id}/pods/{pod_id}/logs/new")
            wrapper = APIWrapper[GetTaskPodLogsNewResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def get_spec(self, task_id: int, pod_id: int) -> GetTaskPodSpecResponse:
        try:
            resp = self._http.get(f"{_BASE}/tasks/{task_id}/pods/{pod_id}/spec")
            wrapper = APIWrapper[GetTaskPodSpecResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def get_events(self, task_id: int, pod_id: int) -> GetTaskPodEventsResponse:
        try:
            resp = self._http.get(f"{_BASE}/tasks/{task_id}/pods/{pod_id}/events")
            wrapper = APIWrapper[GetTaskPodEventsResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def list_users(self, payload: ListTaskUsersRequest) -> ListTaskUsersResponse:
        try:
            resp = self._http.get(f"{_BASE}/task-users", params=payload.model_dump(by_alias=True))
            wrapper = APIWrapper[ListTaskUsersResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def get_metrics_overview(self, payload: GetMetricsOverviewRequest) -> GetMetricsOverviewResponse:
        try:
            resp = self._http.get(f"{_BASE}/metrics/overview", params=payload.model_dump(by_alias=True))
            wrapper = APIWrapper[GetMetricsOverviewResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e
