from __future__ import annotations

from enum import IntEnum
from typing import List, Optional, Any

from pydantic import BaseModel, Field


class DocumentType(IntEnum):
    """文档类型：0-Markdown；1-飞书文档生成的pdf"""
    MARKDOWN = 0  # Markdown
    PDF = 1  # 飞书文档生成的pdf


class Document(BaseModel):
    """文档"""
    id: int = Field(description="文档ID")
    title: str = Field(description="标题")
    type: DocumentType = Field(description="文档类型")
    edit_time: int = Field(alias="edit_time", description="编辑时间")
    need_update: bool = Field(alias="need_update", description="是否需要更新")
    content: str = Field(description="内容")
    username: str = Field(description="用户名")
    user_id: int = Field(alias="user_id", description="作者ID")
    created_at: int = Field(alias="created_at", description="创建时间戳 (ms)")
    comments: Optional[Any] = Field(None, description="评论")

    model_config = {"use_enum_values": True}


class GetDocumentsResponse(BaseModel):
    """分页文档返回"""
    total: int = Field(description="总条数")
    page_size: int = Field(alias="page_size", description="每页数量")
    page_num: int = Field(alias="page_num", description="当前页码")
    data: List[Document] = Field(description="文档列表")
