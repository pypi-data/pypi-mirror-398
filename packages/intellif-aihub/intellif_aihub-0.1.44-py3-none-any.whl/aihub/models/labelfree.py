from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class LabelProjectStatus(Enum):
    """标注状态"""

    Pending = "pending"
    """未开始"""
    Loading = "loading"
    """数据读取中"""
    Error = "failed"
    """数据读取异常"""
    In_Progress = "ready"
    """进行中"""
    Finished = "finished"
    """标注完成"""


class Stats(BaseModel):
    """标注统计信息"""

    total_annotations: int = Field(alias="total_annotations", description="总数据量")
    labeled_annotations: int = Field(alias="labeled_annotations", description="已标注数据量")
    total_labels: int = Field(alias="total_labels", description="总标签量")
    total_reviews: Optional[int] = Field(None, alias="total_reviews", description="总质检量")
    unlabeled_reviews: Optional[int] = Field(None, alias="unlabeled_reviews", description="未质检量")
    labeled_reviews: Optional[int] = Field(None, alias="labeled_reviews", description="已质检量")
    accepted_count: Optional[int] = Field(None, alias="accepted_count", description="质检通过量")
    rejected_count: Optional[int] = Field(None, alias="rejected_count", description="质检打回量")


class GetGlobalStatsResponse(BaseModel):
    """标注统计概况"""

    global_stats: Stats = Field(alias="global_stats")
    valid_ten_percent: bool = Field(alias="valid_ten_percent", description="是否完成验收10%")
    valid_fifty_percent: bool = Field(alias="valid_fifty_percent", description="是否完成验收50%")
    valid_hundred_percent: bool = Field(alias="valid_hundred_percent", description="是否完成验收100%")
    data_exported_count: int = Field(alias="data_exported_count", description="已导出数据次数")
    exported_dataset_name: str = Field(alias="exported_dataset_name", description="最新数据集名称")
    status: LabelProjectStatus = Field(description="状态")
    model_config = {"use_enum_values": True}
