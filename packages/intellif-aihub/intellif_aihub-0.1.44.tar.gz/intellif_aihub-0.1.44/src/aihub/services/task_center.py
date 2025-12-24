# !/usr/bin/env python
# -*- coding:utf-8 -*-
"""任务中心服务模块

封装 **task‑center** 常用能力：

- **创建 / 查询任务**
- **一键创建标注任务**（高阶封装）
"""

from __future__ import annotations

import datetime

import httpx
from loguru import logger
from pydantic import ValidationError

from .tag_resource_management import TagResourceManagementService
from .user_system import UserSystemService
from ..exceptions import APIError, convert_errors
from ..models.common import APIWrapper
from ..models.task_center import (
    CreateTaskReq,
    CreateTaskResp,
    CreateTaskOtherInfo,
    LabelProjectTypeEnum,
    TaskCenterPriorityEnum,
    LabelTaskDetail,
    LabelValidateReq,
    LabelValidateStage,
)
from ..models.user_system import SearchUsersRequest

_BASE = "/task-center/api/v1"


def date_str_to_timestamp(date_str: str) -> int:
    date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
    return int(date_obj.timestamp())


class TaskCenterService:
    """任务中心服务"""

    def __init__(self, http: httpx.Client):
        self._TaskCenter = _TaskCenter(http)
        self._http = http

    def create(self, payload: CreateTaskReq) -> int:
        """创建任务

        Args:
            payload: 任务创建请求体，详见 :class:`CreateTaskReq`

        Returns:
            int: 后端生成的任务 ID
        """
        return self._TaskCenter.create(payload)

    def get(self, task_id: int) -> LabelTaskDetail:
        """根据任务 ID 获取详情

        Args:
            task_id: 任务 ID

        Returns:
            LabelTaskDetail: 任务完整信息
        """
        return self._TaskCenter.get(task_id)

    # 如果想要访问子对象，也保留属性
    @property
    def task_center(self) -> _TaskCenter:
        return self._TaskCenter

    def create_label_task(
        self,
        name: str,
        dataset_version_name: str,
        feishu_doc_name: str,
        task_receiver_name: str,
        estimated_delivery_at: str,
        project_name: str,
        label_type: LabelProjectTypeEnum = LabelProjectTypeEnum.IMAGE_CLASSIFICATION,
        description: str = "",
        task_priority: TaskCenterPriorityEnum = TaskCenterPriorityEnum.low,
        auto_valid_interval: int = 3,
    ) -> int:
        """创建标注任务

        Examples:
            >>> from aihub.client import Client
            >>> client = Client(base_url="xxx", token="xxxx")
            >>> task_id = client.task_center.create_label_task( \
name="test_task", dataset_version_name="re/V1",\
feishu_doc_name="人脸质量人脸照片分类", task_receiver_name="hyc", \
project_name="hycpro", label_type=LabelProjectTypeEnum.IMAGE_CLASSIFICATION, description="test_description", \
task_priority="low", estimated_delivery_at= "2025-08-01")
            1

        Args:
            name (str): 任务名称
            dataset_version_name (str): 数据集版本名称
            feishu_doc_name (str): 飞书文档名称
            task_receiver_name (str): 任务接收者名称
            estimated_delivery_at (str): 预计交付时间，格式为 "YYYY-MM-DD"
            project_name (str): 项目名称
            label_type (LabelProjectTypeEnum): 标注项目类型，默认为图像分类
            description (str): 任务描述，默认为空
            task_priority (TaskCenterPriorityEnum): 任务优先级，默认为低优先级
            auto_valid_interval(str): 标注自动验收时间（默认三天）
        Returns:
            任务ID
        """
        # 获取接收者ID
        user_service = UserSystemService(self._http)
        task_receiver_id = user_service.search_one(payload=SearchUsersRequest(nickname=task_receiver_name))

        # 获取项目ID
        tag_service = TagResourceManagementService(self._http)
        projects = tag_service.select_projects()
        project_id = None
        for project in projects:
            if project.name == project_name:
                project_id = project.id
                break

        if project_id is None:
            raise APIError(f"未找到项目: {project_name}")

        # 获取数据集ID
        from .dataset_management import DatasetManagementService

        dataset_service = DatasetManagementService(self._http)
        dataset_version = dataset_service.get_dataset_version_by_name(version_name=dataset_version_name)

        dataset_id = dataset_version.dataset_id
        dataset_version_id = dataset_version.id

        # 获取文档ID
        from .document_center import DocumentCenterService

        doc_service = DocumentCenterService(self._http)
        docs = doc_service.get_documents(name=feishu_doc_name)

        if not docs:
            raise APIError(f"未找到文档: {feishu_doc_name}")

        doc_id = docs[0].id

        # 创建任务
        other_info = CreateTaskOtherInfo(
            label_project_type=label_type,
            dataset_id=dataset_id,
            dataset_version_id=dataset_version_id,
            doc_id=doc_id,
            doc_type="doc_center",
            auto_valid_interval=auto_valid_interval,
        )
        estimated_delivery_at_timestamp = date_str_to_timestamp(estimated_delivery_at)
        task_req = CreateTaskReq(
            name=name,
            description=description,
            task_priority=task_priority,
            type="label",
            receiver_id=task_receiver_id,
            other_info=other_info,
            project_id=project_id,
            estimated_delivery_at=estimated_delivery_at_timestamp,
        )

        return self.create(task_req)

    def validate_label_project(
        self,
        task_id: int,
        label_project_name: str,
        stage: LabelValidateStage,
        passed: bool,
        note: str = "",
    ) -> None:
        """验证标注项目

        Args:
            label_project_name (str): 标注项目名称
            stage (LabelValidateStage):   验收的标注阶段
            passed (bool): 是否验收通过
            note (str)
            task_id (int): 任务ID
        """
        try:
            task_item = self.task_center.get(task_id)

            for project_info in task_item.other_info.label_projects:
                if project_info.label_project_name == label_project_name:
                    label_project_id = project_info.label_project_id
                    break
            else:
                raise APIError(f"未找到标注项目: {label_project_name}")

            req = LabelValidateReq(
                label_project_id=label_project_id,
                note=note,
                passed=passed,
                stage=stage,
            )
            self.task_center.validate_label_project(task_id=task_id, payload=req)
            logger.info(f"标注项目: {label_project_name} 完成了: {stage}, 验收结果: {passed}")
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise ValueError


class _TaskCenter:
    def __init__(self, http: httpx.Client):
        self._http = http

    def create(self, payload: CreateTaskReq) -> int:
        try:
            resp = self._http.post(
                f"{_BASE}/tasks",
                json=payload.model_dump(),
            )
            if resp.status_code != 200:
                logger.error(f"[create] 创建任务失败: {resp.text}")
                raise APIError(message="API Error", status=resp.status_code, detail=resp.json())
            wrapper = APIWrapper[CreateTaskResp].model_validate(resp.json())
            if wrapper.code != 0:
                logger.error(f"[create] 创建任务失败: {wrapper.msg}")
                raise APIError(message=wrapper.msg, status=wrapper.code)

            return wrapper.data.id
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def get(self, task_id: int) -> LabelTaskDetail:
        resp = self._http.get(
            f"{_BASE}/tasks/{task_id}",
        )

        try:
            wrapper = APIWrapper[LabelTaskDetail].model_validate(resp.json())
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def validate_label_project(self, task_id: int, payload: LabelValidateReq) -> None:
        try:
            payload_body = payload.model_dump()
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise ValueError
        resp = self._http.post(
            f"{_BASE}/tasks/{task_id}/label_validate",
            json=payload_body,
        )
        try:
            wrapper = APIWrapper[CreateTaskResp].model_validate(resp.json())
            if wrapper.code != 0:
                logger.error(f"[validate_label_project] 验证标注项目失败: {wrapper.msg}")

                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e
        return
