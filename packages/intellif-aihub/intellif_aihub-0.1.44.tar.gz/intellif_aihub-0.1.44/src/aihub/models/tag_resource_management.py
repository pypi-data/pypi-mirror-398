from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class Project(BaseModel):
    """项目"""
    id: int = Field(description="项目ID")
    name: str = Field(description="项目名称")


class ProjectListData(BaseModel):
    """项目列表数据"""
    data: List[Project] = Field(description="项目列表")


class SelectProjectsResponse(BaseModel):
    """选择项目返回"""
    data: List[Project] = Field(description="项目列表")


class Category(BaseModel):
    key: str
    value: str
    is_multi_select: bool


class Tag(BaseModel):
    id: int
    name: str
    value: str


class ModelTag(BaseModel):
    category: Category
    tags: List[Tag]


class SelectModelTagsResponse(BaseModel):
    """选择模型标签返回"""
    data: List[ModelTag] = Field(description="模型标签列表")


class SkuBrief(BaseModel):
    """SKU信息"""
    id: int = Field(description="SKU ID")
    description: str = Field(description="SKU 描述")
    cpu: int = Field(description="CPU 核数")
    memory: int = Field(description="内存 GiB")
    gpu_type: int = Field(alias="gpu_type", description="GPU类型，1-A800，2-4090，3-3090，4-2080，5-None")
    gpu_memory: int = Field(alias="gpu_memory", description="GPU 显存 GiB")
    network: int = Field(description="网络，0-Other，1-ROCE，2-IB")
    created_at: int = Field(alias="created_at", description="创建时间戳（ms）")


class VirtualClusterBrief(BaseModel):
    """虚拟集群信息"""
    id: int = Field(description="虚拟集群ID")
    name: str = Field(description="虚拟集群名称")
    uuid: str = Field(description="虚拟集群UUID")
    sku: Optional[SkuBrief] = Field(None, description="SKU")
    created_at: int = Field(alias="created_at", description="创建时间戳（ms）")


class SelectVirtualClustersRequest(BaseModel):
    """选择虚拟集群请求"""
    user_id: int = Field(alias="user_id", description="用户ID")
    module_type: Optional[int] = Field(None, alias="module_type",
                                       description="模块类型 (int)，0-部署，1-训练，2-工作流，3-配额调度")
    new_module_type: Optional[str] = Field(None, alias="new_module_type",
                                           description="新版模块类型 (字符串)，仅前端使用")


class SelectVirtualClustersResponse(BaseModel):
    """选择虚拟集群返回"""
    data: Optional[List[VirtualClusterBrief]] = Field(default_factory=list, description="虚拟集群列表")
