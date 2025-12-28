# !/usr/bin/env python
# -*- coding:utf-8 -*-
"""
工作流中心服务模块

封装 **Workflow‑Center** 相关接口，围绕三大核心资源展开：

- **Pipeline** – *工作流定义*

    - 列表
    - 创建
    - 删除
    - 下拉选择
    - 创建者

- **Pipeline Version** – *工作流版本*

    - 列表
    - 创建
    - 删除
    - 输入参数查询
    - 批量迁移

- **Run** – *运行实例*

    - 创建
    - 重试
    - 停止
    - 重新提交
    - 日志查询
    - Pod 查询
    - 事件查询
    - 运行用户
"""

from __future__ import annotations

from typing import List

import httpx
from loguru import logger
from pydantic import ValidationError

from ..exceptions import APIError, convert_errors
from ..models.common import APIWrapper
from ..models.workflow_center import (
    ListPipelinesRequest,
    ListPipelinesResponse,
    CreatePipelineRequest,
    CreatePipelineResponse,
    Pipeline,
    PipelineBrief,
    SelectPipelinesRequest,
    SelectPipelinesResponse,
    PipelineUserBrief,
    SelectPipelineUsersResponse,
    ListPipelineVersionsRequest,
    ListPipelineVersionsResponse,
    CreatePipelineVersionRequest,
    CreatePipelineVersionResponse,
    PipelineVersion,
    PipelineVersionBrief,
    SelectPipelineVersionsRequest,
    SelectPipelineVersionsResponse,
    GetPipelineVersionInputParamsResponse,
    MigratePipelineVersionsRequest,
    ListRunsRequest,
    ListRunsResponse,
    CreateRunRequest,
    CreateRunResponse,
    Run,
    RetryRunResponse,
    StopRunResponse,
    ResubmitRunResponse,
    GetRunTaskLogsResponse,
    GetRunTaskPodResponse,
    GetRunTaskEventsResponse,
    RunUserBrief,
    SelectRunUsersResponse,
    ListModulesRequest,
    ListModulesResponse,
    Module,
    ModuleVersion,
    CreateModuleRequest,
    CreateModuleResponse,
    SelectModuleUsersResponse,
    CreateModuleVersionRequest,
    CreateModuleVersionResponse,
    EditModuleVersionRequest,
    EditModuleVersionResponse,
    RebuildModuleVersionResponse,
    ReleaseModuleVersionResponse,
    User,
)

_BASE = "/workflow-center/api/v1"


class WorkflowCenterService:
    """工作流中心服务"""

    def __init__(self, http: httpx.Client):
        self._pipeline = _Pipeline(http)
        self._pipeline_version = _PipelineVersion(http)
        self._run = _Run(http)
        self._module = _Module(http)
        self._module_version = _ModuleVersion(http)

    def list_pipelines(self, payload: ListPipelinesRequest) -> ListPipelinesResponse:
        """分页查询工作流列表

        Args:
            payload: 分页 + 过滤条件，请参见 ``ListPipelinesRequest``

        Returns:
            ListPipelinesResponse: 分页结果
        """
        return self._pipeline.list(payload)

    def get_pipeline(self, pipeline_id: int) -> Pipeline:
        """获取单个工作流详情

        Args:
            pipeline_id: 工作流 ID

        Returns:
            Pipeline: 工作流完整信息
        """
        return self._pipeline.get(pipeline_id)

    def create_pipeline(self, payload: CreatePipelineRequest) -> int:
        """创建工作流

        Args:
            payload: 创建请求体，包含节点 / 输入等

        Returns:
            int: 新建工作流 ID
        """
        return self._pipeline.create(payload)

    def delete_pipeline(self, pipeline_id: int) -> None:
        """删除工作流

        Args:
            pipeline_id: 目标工作流 ID
        """
        self._pipeline.delete(pipeline_id)

    def select_pipelines(self, name: str | None = None) -> List[PipelineBrief]:
        """下拉搜索工作流

        Args:
            name: 名称关键字（可选）

        Returns:
            list[PipelineBrief]: 简要信息列表
        """
        return self._pipeline.select(SelectPipelinesRequest(name=name)).data

    def select_pipeline_users(self) -> List[PipelineUserBrief]:
        """获取创建工作流的用户列表

        Returns:
            list[PipelineUserBrief]: 用户简要信息
        """
        return self._pipeline.select_users().data

    def list_pipeline_versions(self, payload: ListPipelineVersionsRequest) -> ListPipelineVersionsResponse:
        """分页查询工作流版本

        Args:
            payload: 分页 + 过滤条件

        Returns:
            ListPipelineVersionsResponse: 分页结果
        """
        return self._pipeline_version.list(payload)

    def get_pipeline_version(self, version_id: int) -> PipelineVersion:
        """获取工作流版本详情

        Args:
            version_id: 版本 ID

        Returns:
            PipelineVersion: 版本详细信息
        """
        return self._pipeline_version.get(version_id)

    def create_pipeline_version(self, payload: CreatePipelineVersionRequest) -> int:
        """创建工作流版本

        Args:
            payload: 创建请求体

        Returns:
            int: 新建版本 ID
        """
        return self._pipeline_version.create(payload)

    def delete_pipeline_version(self, version_id: int) -> None:
        """删除工作流版本

        Args:
            version_id: 目标版本 ID
        """
        self._pipeline_version.delete(version_id)

    def select_pipeline_versions(self, payload: SelectPipelineVersionsRequest) -> List[PipelineVersionBrief]:
        """下拉搜索工作流版本

        Args:
            payload: 过滤条件

        Returns:
            list[PipelineVersionBrief]: 版本简要列表
        """
        return self._pipeline_version.select(payload).data

    def get_pipeline_version_input_params(self, version_id: int) -> list[str]:
        """获取指定版本的输入参数

        Args:
            version_id: 版本 ID

        Returns:
            list[str]: 输入参数名列表
        """
        return self._pipeline_version.get_input_params(version_id).data

    def migrate_pipeline_versions(self, payload: MigratePipelineVersionsRequest) -> None:
        """批量迁移工作流版本

        Args:
            payload: 起止版本 ID 等迁移参数

        Returns:
            None
        """
        self._pipeline_version.migrate(payload)

    def list_runs(self, payload: ListRunsRequest) -> ListRunsResponse:
        """分页检索运行实例

        Args:
            payload: 分页与过滤条件

        Returns:
            ListRunsResponse: 运行实例分页结果
        """
        return self._run.list_runs(payload)

    def get_run(self, run_id: int) -> Run:
        """获取单次运行详情

        Args:
            run_id: Run ID

        Returns:
            Run: 运行完整信息
        """
        return self._run.get_run(run_id)

    def create_run(self, payload: CreateRunRequest) -> int:
        """创建新的运行实例

        Args:
            payload: 运行提交参数

        Returns:
            int: 新建 Run ID
        """
        return self._run.create_run(payload)

    def retry_run(self, run_id: int) -> Run:
        """重试指定运行

        Args:
            run_id: 待重试的 Run ID

        Returns:
            Run: 新生成的运行实例
        """
        return self._run.retry_run(run_id)

    def stop_run(self, run_id: int) -> Run:
        """停止正在执行的运行

        Args:
            run_id: 目标 Run ID

        Returns:
            Run: 已停止的运行信息
        """
        return self._run.stop_run(run_id)

    def resubmit_run(self, run_id: int) -> Run:
        """复制参数重新提交一次运行

        Args:
            run_id: 原始 Run ID

        Returns:
            Run: 新的运行实例
        """
        return self._run.resubmit_run(run_id)

    def get_run_task_logs(self, run_id: int, pod_name: str) -> GetRunTaskLogsResponse:
        """获取某 Task‑Pod 的日志

        Args:
            run_id: Run ID
            pod_name: Pod 名称

        Returns:
            GetRunTaskLogsResponse: 含日志文本及 S3 链接
        """
        return self._run.get_run_task_logs(run_id, pod_name)

    def get_run_task_pod(self, run_id: int, pod_name: str) -> GetRunTaskPodResponse:
        """获取运行任务 Pod

        Args:
            run_id: 运行实例 ID
            pod_name: 目标 Pod 名称（对应 task 节点）

        Returns:
            GetRunTaskPodResponse: 含 Pod 详细 YAML 字符串
        """
        return self._run.get_run_task_pod(run_id, pod_name)

    def get_run_task_events(self, run_id: int, pod_name: str) -> GetRunTaskEventsResponse:
        """查询运行任务 Pod 的事件记录

        Args:
            run_id: 运行实例 ID
            pod_name: 目标 Pod 名称

        Returns:
            GetRunTaskEventsResponse: 事件文本等信息
        """
        return self._run.get_run_task_events(run_id, pod_name)

    def select_run_users(self) -> list[RunUserBrief]:
        """列出提交运行任务的用户

        Returns:
            list[RunUserBrief]: 用户 ID 与名称简要信息
        """
        return self._run.select_run_users()

    def list_modules(self, payload: ListModulesRequest) -> ListModulesResponse:
        """分页查询模块列表

        Args:
            payload: 分页 + 过滤条件

        Returns:
            ListModulesResponse: 分页结果
        """
        return self._module.list(payload)

    def create_module(self, payload: CreateModuleRequest) -> int:
        """创建模块（同时创建第一个版本）

        Args:
            payload: 创建请求体

        Returns:
            int: 新建模块 ID
        """
        return self._module.create(payload)

    def select_module_users(self) -> List[User]:
        """获取创建模块的用户列表

        Returns:
            list[User]: 用户简要信息
        """
        return self._module.select_users().data

    # ------------------------------------------------------------------ #
    # Module Version
    # ------------------------------------------------------------------ #
    def get_module_version(self, version_id: int) -> ModuleVersion:
        """获取模块版本详情

        Args:
            version_id: 模块版本 ID

        Returns:
            ModuleVersion: 模块版本完整信息
        """
        return self._module_version.get(version_id)

    def create_module_version(self, payload: CreateModuleVersionRequest) -> int:
        """创建模块版本

        Args:
            payload: 创建请求体

        Returns:
            int: 新建模块版本 ID
        """
        return self._module_version.create(payload)

    def edit_module_version(self, payload: EditModuleVersionRequest) -> None:
        """编辑模块版本

        Args:
            payload: 编辑请求体
        """
        self._module_version.edit(payload)

    def delete_module_version(self, version_id: int) -> None:
        """删除模块版本

        Args:
            version_id: 模块版本 ID
        """
        self._module_version.delete(version_id)

    def release_module_version(self, version_id: int) -> None:
        """发布模块版本

        Args:
            version_id: 模块版本 ID
        """
        self._module_version.release(version_id)

    def rebuild_module_version(self, version_id: int) -> None:
        """重新构建模块版本

        Args:
            version_id: 模块版本 ID
        """
        self._module_version.rebuild(version_id)

    @property
    def module(self) -> _Module:
        return self._module

    @property
    def module_version(self) -> _ModuleVersion:
        return self._module_version

    @property
    def pipeline(self) -> _Pipeline:
        return self._pipeline

    @property
    def pipeline_version(self) -> _PipelineVersion:
        return self._pipeline_version

    @property
    def run(self) -> _Run:
        return self._run


class _Pipeline:

    def __init__(self, http: httpx.Client):
        self._http = http

    def list(self, payload: ListPipelinesRequest) -> ListPipelinesResponse:
        try:
            resp = self._http.get(f"{_BASE}/pipelines", params=payload.model_dump(by_alias=True, exclude_none=True))
            if resp.status_code != 200:
                logger.error(f"backend code {resp.status_code}: {resp.text}")
                raise APIError(f"backend code {resp.status_code}: {resp.text}", status=resp.status_code)
            wrapper = APIWrapper[ListPipelinesResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def get(self, pipeline_id: int) -> Pipeline:
        try:
            resp = self._http.get(f"{_BASE}/pipelines/{pipeline_id}")
            if resp.status_code != 200:
                logger.error(f"backend code {resp.status_code}: {resp.text}")
                raise APIError(f"backend code {resp.status_code}: {resp.text}", status=resp.status_code)
            wrapper = APIWrapper[Pipeline].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def create(self, payload: CreatePipelineRequest) -> int:
        try:
            resp = self._http.post(f"{_BASE}/pipelines", json=payload.model_dump(by_alias=True, exclude_none=True))
            if resp.status_code != 200:
                logger.error(f"backend code {resp.status_code}: {resp.text}")
                raise APIError(f"backend code {resp.status_code}: {resp.text}", status=resp.status_code)
            wrapper = APIWrapper[CreatePipelineResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data.id
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def delete(self, pipeline_id: int) -> None:
        try:
            resp = self._http.delete(f"{_BASE}/pipelines/{pipeline_id}")
            if resp.status_code != 200:
                logger.error(f"backend code {resp.status_code}: {resp.text}")
                raise APIError(f"backend code {resp.status_code}: {resp.text}", status=resp.status_code)
            wrapper = APIWrapper[dict].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def select(self, payload: SelectPipelinesRequest) -> SelectPipelinesResponse:
        try:
            resp = self._http.get(
                f"{_BASE}/select-pipelines", params=payload.model_dump(by_alias=True, exclude_none=True)
            )
            if resp.status_code != 200:
                logger.error(f"backend code {resp.status_code}: {resp.text}")
                raise APIError(f"backend code {resp.status_code}: {resp.text}", status=resp.status_code)
            wrapper = APIWrapper[SelectPipelinesResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def select_users(self) -> SelectPipelineUsersResponse:
        try:
            resp = self._http.get(f"{_BASE}/select-pipeline-users")
            wrapper = APIWrapper[SelectPipelineUsersResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e


class _PipelineVersion:

    def __init__(self, http: httpx.Client):
        self._http = http

    def list(self, payload: ListPipelineVersionsRequest) -> ListPipelineVersionsResponse:
        try:
            resp = self._http.get(
                f"{_BASE}/pipeline-versions", params=payload.model_dump(by_alias=True, exclude_none=True)
            )
            wrapper = APIWrapper[ListPipelineVersionsResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def get(self, version_id: int) -> PipelineVersion:
        try:
            resp = self._http.get(f"{_BASE}/pipeline-versions/{version_id}")
            wrapper = APIWrapper[PipelineVersion].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def create(self, payload: CreatePipelineVersionRequest) -> int:
        try:
            resp = self._http.post(
                f"{_BASE}/pipeline-versions", json=payload.model_dump(by_alias=True, exclude_none=True)
            )
            wrapper = APIWrapper[CreatePipelineVersionResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data.id
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def delete(self, version_id: int) -> None:
        try:
            resp = self._http.delete(f"{_BASE}/pipeline-versions/{version_id}")
            wrapper = APIWrapper[dict].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def select(self, payload: SelectPipelineVersionsRequest) -> SelectPipelineVersionsResponse:
        try:
            resp = self._http.get(
                f"{_BASE}/select-pipeline-versions", params=payload.model_dump(by_alias=True, exclude_none=True)
            )
            wrapper = APIWrapper[SelectPipelineVersionsResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def get_input_params(self, version_id: int) -> GetPipelineVersionInputParamsResponse:
        try:
            resp = self._http.get(f"{_BASE}/pipeline-versions/{version_id}/input-params")
            wrapper = APIWrapper[GetPipelineVersionInputParamsResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def migrate(self, payload: MigratePipelineVersionsRequest) -> None:
        try:
            resp = self._http.post(f"{_BASE}/migrate-pipeline-versions", json=payload.model_dump(by_alias=True))
            wrapper = APIWrapper[dict].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e


class _Run:

    def __init__(self, http: httpx.Client):
        self._http = http

    def list_runs(self, payload: ListRunsRequest) -> ListRunsResponse:
        try:
            resp = self._http.get(f"{_BASE}/runs", params=payload.model_dump(by_alias=True, exclude_none=True))
            wrapper = APIWrapper[ListRunsResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def get_run(self, run_id: int) -> Run:
        try:
            resp = self._http.get(f"{_BASE}/runs/{run_id}")
            wrapper = APIWrapper[Run].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def create_run(self, payload: CreateRunRequest) -> int:
        try:
            resp = self._http.post(f"{_BASE}/runs", json=payload.model_dump(by_alias=True, exclude_none=True))
            wrapper = APIWrapper[CreateRunResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data.id
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def retry_run(self, run_id: int) -> Run:
        try:
            resp = self._http.put(f"{_BASE}/runs/{run_id}/retry")
            wrapper = APIWrapper[RetryRunResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def stop_run(self, run_id: int) -> Run:
        try:
            resp = self._http.put(f"{_BASE}/runs/{run_id}/stop")
            wrapper = APIWrapper[StopRunResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def resubmit_run(self, run_id: int) -> Run:
        try:
            resp = self._http.put(f"{_BASE}/runs/{run_id}/resubmit")
            wrapper = APIWrapper[ResubmitRunResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def get_run_task_logs(self, run_id: int, pod_name: str) -> GetRunTaskLogsResponse:
        try:
            resp = self._http.get(f"{_BASE}/runs/{run_id}/tasks/{pod_name}/logs")
            wrapper = APIWrapper[GetRunTaskLogsResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def get_run_task_pod(self, run_id: int, pod_name: str) -> GetRunTaskPodResponse:
        try:
            resp = self._http.get(f"{_BASE}/runs/{run_id}/tasks/{pod_name}/pod")
            wrapper = APIWrapper[GetRunTaskPodResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def get_run_task_events(self, run_id: int, pod_name: str) -> GetRunTaskEventsResponse:
        try:
            resp = self._http.get(f"{_BASE}/runs/{run_id}/tasks/{pod_name}/events")
            wrapper = APIWrapper[GetRunTaskEventsResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def select_run_users(self) -> List[RunUserBrief]:
        try:
            resp = self._http.get(f"{_BASE}/select-run-users")
            wrapper = APIWrapper[SelectRunUsersResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e


class _Module:

    def __init__(self, http: httpx.Client):
        self._http = http

    def list(self, payload: ListModulesRequest) -> ListModulesResponse:
        try:
            resp = self._http.get(f"{_BASE}/modules", params=payload.model_dump(by_alias=True, exclude_none=True))
            wrapper = APIWrapper[ListModulesResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def create(self, payload: CreateModuleRequest) -> int:
        try:
            resp = self._http.post(f"{_BASE}/modules", json=payload.model_dump(by_alias=True, exclude_none=True))
            wrapper = APIWrapper[CreateModuleResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data.id
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def select_users(self) -> SelectModuleUsersResponse:
        try:
            resp = self._http.get(f"{_BASE}/select-module-users")
            wrapper = APIWrapper[SelectModuleUsersResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e


class _ModuleVersion:

    def __init__(self, http: httpx.Client):
        self._http = http

    def get(self, version_id: int) -> ModuleVersion:
        try:
            resp = self._http.get(f"{_BASE}/module-versions/{version_id}")
            if resp.status_code != 200:
                logger.error(f"backend code {resp.status_code}: {resp.text}")
                raise APIError(f"backend code {resp.status_code}: {resp.text}", status=resp.status_code)
            wrapper = APIWrapper[ModuleVersion].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def create(self, payload: CreateModuleVersionRequest) -> int:
        try:
            resp = self._http.post(f"{_BASE}/module-versions", json=payload.model_dump(by_alias=True, exclude_none=True))
            if resp.status_code != 200:
                logger.error(f"backend code {resp.status_code}: {resp.text}")
                raise APIError(f"backend code {resp.status_code}: {resp.text}", status=resp.status_code)
            wrapper = APIWrapper[CreateModuleVersionResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data.id
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def edit(self, payload: EditModuleVersionRequest) -> None:
        try:
            resp = self._http.put(f"{_BASE}/module-versions/{payload.id}", json=payload.model_dump(by_alias=True, exclude_none=True))
            if resp.status_code != 200:
                logger.error(f"backend code {resp.status_code}: {resp.text}")
                raise APIError(f"backend code {resp.status_code}: {resp.text}", status=resp.status_code)
            wrapper = APIWrapper[EditModuleVersionResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def delete(self, version_id: int) -> None:
        try:
            resp = self._http.delete(f"{_BASE}/module-versions/{version_id}")
            if resp.status_code != 200:
                logger.error(f"backend code {resp.status_code}: {resp.text}")
                raise APIError(f"backend code {resp.status_code}: {resp.text}", status=resp.status_code)
            wrapper = APIWrapper[dict].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def release(self, version_id: int) -> None:
        try:
            resp = self._http.post(f"{_BASE}/module-versions/{version_id}/release")
            if resp.status_code != 200:
                logger.error(f"backend code {resp.status_code}: {resp.text}")
                raise APIError(f"backend code {resp.status_code}: {resp.text}", status=resp.status_code)
            wrapper = APIWrapper[ReleaseModuleVersionResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def rebuild(self, version_id: int) -> None:
        try:
            resp = self._http.post(f"{_BASE}/module-versions/{version_id}/rebuild")
            if resp.status_code != 200:
                logger.error(f"backend code {resp.status_code}: {resp.text}")
                raise APIError(f"backend code {resp.status_code}: {resp.text}", status=resp.status_code)
            wrapper = APIWrapper[RebuildModuleVersionResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

