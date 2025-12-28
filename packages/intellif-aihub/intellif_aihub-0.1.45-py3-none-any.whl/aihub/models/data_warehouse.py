from __future__ import annotations

from enum import IntEnum
from typing import List, Optional

from pydantic import BaseModel, Field


class SearchType(IntEnum):
    """搜索类型：1-SQL；2-图片；3-文本"""
    SQL = 1  # SQL
    IMAGE = 2  # 图片
    TEXT = 3  # 文本


class SearchStatus(IntEnum):
    """搜索任务状态：1-等待中；2-运行中；3-成功；4-失败"""
    WAITING = 1  # 等待中
    RUNNING = 2  # 运行中
    SUCCESS = 3  # 成功
    FAIL = 4  # 失败


class Image(BaseModel):
    """检索图片对象"""
    url: str = Field(alias="url", description="URL")
    box: Optional[List[int]] = Field(default_factory=list, description="检测框坐标 [x1, y1, x2, y2]")


class SearchResult(BaseModel):
    """单条检索结果"""
    image_url: str = Field(alias="image_url", description="图片URL")
    label: str = Field(description="标签")
    box: List[int] = Field(description="检测框坐标 [x1, y1, x2, y2]")
    score: float = Field(description="分数")


class Search(BaseModel):
    """搜索任务完整信息"""
    id: int = Field(description="任务ID")
    type: SearchType = Field(description="搜索类型")
    name: str = Field(description="任务名称")
    description: str = Field(description="任务描述")
    sql: str = Field(description="SQL语句")
    feature_lib_id: int = Field(alias="feature_lib_id", description="特征库ID")
    feature_lib_name: str = Field(alias="feature_lib_name", description="特征库名称")
    images: Optional[List[Image]] = Field(default_factory=list, description="搜索图片列表")
    keywords: str = Field(description="关键词")
    top_k: int = Field(alias="top_k", description="返回前K个候选")
    status: SearchStatus = Field(description="任务状态")
    message: str = Field(description="信息")
    result_url: str = Field(alias="result_url", description="结果地址")
    results: Optional[List[SearchResult]] = Field(default_factory=list, description="检索结果列表")
    created_at: int = Field(alias="created_at", description="创建时间戳 (ms)")
    username: str = Field(description="创建人用户名")

    model_config = {"use_enum_values": True}


class ListSearchRequest(BaseModel):
    """分页搜索任务请求"""
    page_size: int = Field(20, alias="page_size", description="每页数量")
    page_num: int = Field(1, alias="page_num", description="当前页码，从1开始")
    name: Optional[str] = Field(None, description="名称过滤")
    status: Optional[SearchStatus] = Field(None, description="状态过滤")
    user_id: Optional[int] = Field(None, alias="user_id", description="用户ID过滤")

    model_config = {"use_enum_values": True}


class ListSearchResponse(BaseModel):
    """分页搜索任务返回"""
    total: int = Field(description="总条数")
    page_size: int = Field(alias="page_size", description="每页数量")
    page_num: int = Field(alias="page_num", description="当前页码")
    data: Optional[List[Search]] = Field(default_factory=list, description="搜索任务列表")


class CreateSearchRequest(BaseModel):
    """创建搜索任务请求"""
    type: SearchType = Field(description="搜索类型")
    name: str = Field(description="名称")
    description: Optional[str] = Field(None, description="描述")
    sql: Optional[str] = Field(None, description="SQL语句")
    feature_lib_id: Optional[int] = Field(None, alias="feature_lib_id", description="特征库ID")
    images: Optional[List[Image]] = Field(default_factory=list, description="搜索图片列表")
    keywords: Optional[str] = Field(None, description="关键词")
    top_k: Optional[int] = Field(None, alias="top_k", description="返回前K条")

    model_config = {"use_enum_values": True}


class CreateSearchResponse(BaseModel):
    """创建搜索任务返回"""
    id: int = Field(description="任务ID")
