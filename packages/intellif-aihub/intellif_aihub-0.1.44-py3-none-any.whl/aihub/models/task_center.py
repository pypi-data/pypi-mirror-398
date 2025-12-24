from __future__ import annotations

import json
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, Field, field_serializer, field_validator


class TaskCenterPriorityEnum(Enum):
    """任务优先级枚举"""

    low = "low"
    medium = "medium"
    high = "high"


class LabelProjectTypeEnum(Enum):
    """
    任务类型枚举
     1 - 目标检测 2 - 语义分割 3 - 图片分类 4 - 实例分割 5 - 视频标注 6 - 人类偏好文本标注 7- 敏感预料文本标注 8 - 文本标注 9 - 关键点标注
    """

    OBJECT_DETECTION = 1
    SEGMENTATION = 2
    IMAGE_CLASSIFICATION = 3
    INSTANCE_SEGMENTATION = 4
    VIDEO_LABELING = 5
    HUMAN_PREFERENCE_TEXT_LABELING = 6
    SENSITIVE_TEXT_LABELING = 7
    TEXT_LABELING = 8
    KEYPOINT_LABELING = 9


class CreateTaskOtherInfo(BaseModel):
    """创建任务附加信息"""

    label_project_type: LabelProjectTypeEnum = Field(LabelProjectTypeEnum.IMAGE_CLASSIFICATION, description="标注枚举")
    dataset_id: int = Field(alias="dataset_id", description="数据集ID")
    dataset_version_id: int = Field(alias="dataset_version_id", description="数据集版本ID")
    doc_id: int = Field(alias="doc_id", description="文档中心文档ID")
    doc_type: str = Field(alias="doc_type", default="doc_center", description="文档类型")

    model_config = {"use_enum_values": True}
    auto_valid_interval: int = Field(3, description="自动验收间隔")


class ProjectInfo(BaseModel):
    """项目信息"""

    label_project_id: int = Field(alias="label_project_id", description="项目ID")
    label_project_name: str = Field(alias="label_project_name", description="项目名称")


class TaskDetailOtherInfo(BaseModel):
    """任务详情附加信息"""

    label_project_type: LabelProjectTypeEnum = Field(LabelProjectTypeEnum.IMAGE_CLASSIFICATION, description="标注枚举")
    dataset_id: Optional[int] = Field(default=None, alias="dataset_id", description="数据集ID")
    dataset_version_id: Optional[int] = Field(default=None, alias="dataset_version_id", description="数据集版本ID")
    doc_id: int = Field(alias="doc_id", description="文档中心文档ID")
    doc_type: str = Field(alias="doc_type", default="doc_center", description="文档类型")
    label_projects: Optional[List[ProjectInfo]] = Field(
        alias="label_projects", default=None, description="关联标注项目列表"
    )

    model_config = {"use_enum_values": True}


class CreateTaskReq(BaseModel):
    """创建标注任务请求"""

    name: str = Field(description="任务名称")
    description: Optional[str] = Field(None, description="任务描述")
    task_priority: Optional[str] = Field(None, alias="task_priority", description="优先级")
    type: Optional[str] = Field(None, description="任务类型")
    receiver_id: Optional[int] = Field(None, description="接收人ID")
    project_id: Optional[int] = Field(None, description="项目ID")
    other_info: CreateTaskOtherInfo = Field(alias="other_info", description="附加信息")
    estimated_delivery_at: Optional[int] = Field(None, description="预计交付时间")

    @field_serializer("other_info")
    def serialize_other_info(self, value: CreateTaskOtherInfo) -> str:
        """将 other_info 序列化为 JSON 字符串"""
        return value.model_dump_json()


class CreateTaskResp(BaseModel):
    """创建标注任务返回"""

    id: int = Field(alias="id", description="任务ID")


class LabelTaskDetail(BaseModel):
    """任务详情"""

    name: str = Field(description="任务名称")
    description: Optional[str] = Field(default=None, alias="description", description="任务描述")
    task_priority: Optional[str] = Field(default=None, alias="task_priority", description="优先级")
    type: Optional[str] = Field(default=None, alias="type", description="任务类型")
    receiver_id: Optional[int] = Field(default=None, alias="receiver_id", description="接收人ID")
    project_id: Optional[int] = Field(default=None, description="项目ID")
    other_info: Optional[TaskDetailOtherInfo] = Field(default=None, alias="other_info", description="附加信息")
    estimated_delivery_at: Optional[int] = Field(default=None, description="预计交付时间")

    @field_serializer("other_info")
    def serialize_other_info(self, value: Optional[TaskDetailOtherInfo]) -> Optional[str]:
        """将 other_info 序列化为 JSON 字符串"""
        return value.model_dump_json() if value else None

    @field_validator("other_info", mode="before")
    @classmethod
    def parse_other_info(cls, value):
        """将字符串解析为 TaskDetailOtherInfo 对象"""
        if value is None:
            return None
        if isinstance(value, str):
            try:
                # 解析 JSON 字符串为字典
                data = json.loads(value)
                # 创建 TaskDetailOtherInfo 对象
                return TaskDetailOtherInfo(**data)
            except (json.JSONDecodeError, TypeError, ValueError) as e:
                raise ValueError(f"无法解析 other_info 字符串: {e}")
        elif isinstance(value, dict):
            # 如果传入的是字典，直接创建对象
            return TaskDetailOtherInfo(**value)
        elif isinstance(value, TaskDetailOtherInfo):
            # 如果已经是对象，直接返回
            return value
        else:
            raise ValueError(f"other_info 必须是字符串、字典或 TaskDetailOtherInfo 对象，得到: {type(value)}")


class LabelValidateStage(Enum):
    """任务验收阶段"""

    TEN_PERCENT = "标注阶段（10%）"
    """10%阶段"""
    FIFTY_PERCENT = "标注阶段（50%）"
    """50%阶段"""
    LABEL_FINISHED = "标注阶段（100%）"
    """标注完成"""


class LabelValidateReq(BaseModel):
    """任务验收"""

    label_project_id: int = Field(alias="label_project_id", description="项目ID")
    stage: LabelValidateStage = Field(alias="stage", description="阶段")
    passed: bool = Field(alias="passed", description="是否通过")
    note: str = Field(alias="note", description="备注")
    model_config = {"use_enum_values": True}
