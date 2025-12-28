# !/usr/bin/env python
# -*-coding:utf-8 -*-
"""制品管理模型模块

该模块定义了制品管理相关的数据模型，包括制品类型、创建制品请求、制品响应等。
"""
from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class ArtifactType(str, Enum):
    """制品类型枚举："dataset"-数据集类型；"model"-模型类型；"metrics"-指标类型；"log"-日志类型；"checkpoint"-检查点类型；"image"-图像类型；"prediction"-预测结果类型；"other"-其他类型"""

    dataset = "dataset"  # 数据集类型
    model = "model"  # 模型类型
    metrics = "metrics"  # 指标类型
    log = "log"  # 日志类型
    checkpoint = "checkpoint"  # 检查点类型
    image = "image"  # 图像类型
    prediction = "prediction"  # 预测结果类型
    other = "other"  # 其他类型


class CreateArtifactsReq(BaseModel):
    """创建制品请求"""

    entity_id: str = Field(alias="entity_id", description="实体ID，通常是运行ID，用于关联制品与特定运行")
    entity_type: ArtifactType = Field(
        default=ArtifactType.other, alias="entity_type", description="制品类型，指定制品的类型，默认为other"
    )
    src_path: str = Field(alias="src_path", description="源路径，制品在系统中的路径标识")
    is_dir: bool = Field(
        default=False, alias="is_dir", description="是否为目录，True表示制品是一个目录，False表示是单个文件"
    )

    model_config = {"use_enum_values": True}


class CreateArtifactsResponseData(BaseModel):
    """创建制品响应数据"""

    id: int = Field(description="制品ID")
    s3_path: str = Field(alias="s3_path", description="S3存储路径")


class CreateArtifactsResponseModel(BaseModel):
    """创建制品响应模型"""

    code: int = Field(description="响应码，0表示成功")
    msg: str = Field(default="", description="响应消息")
    data: Optional[CreateArtifactsResponseData] = Field(default=None, description="响应数据")


class CreateEvalReq(BaseModel):
    """创建评估请求"""

    dataset_id: int = Field(alias="dataset_id", description="数据集ID")
    dataset_version_id: int = Field(alias="dataset_version_id", description="数据集版本ID")
    prediction_artifact_path: str = Field(alias="prediction_artifact_path", description="预测结果制品路径")
    evaled_artifact_path: str = Field(alias="evaled_artifact_path", description="评估结果制品路径")
    run_id: str = Field(alias="run_id", description="运行ID")
    user_id: int = Field(alias="user_id", description="用户ID")
    report: dict = Field(default_factory=dict, description="评估报告")


class ArtifactResp(BaseModel):
    """制品响应模型，表示一个制品的详细信息"""

    id: int = Field(description="制品ID")
    entity_type: str = Field(alias="entity_type", description="实体类型")
    entity_id: str = Field(alias="entity_id", description="实体ID")
    src_path: str = Field(alias="src_path", description="源路径")
    s3_path: str = Field(alias="s3_path", description="S3存储路径")
    is_dir: bool = Field(alias="is_dir", description="是否为目录")


class ArtifactRespData(BaseModel):
    """制品分页数据"""

    total: int = Field(description="总记录数")
    page_size: int = Field(alias="page_size", description="每页大小")
    page_num: int = Field(alias="page_num", description="页码")
    data: List[ArtifactResp] = Field(default_factory=list, description="制品列表")


class ArtifactRespModel(BaseModel):
    """获取制品响应模型"""

    code: int = Field(description="响应码，0表示成功")
    msg: str = Field(default="", description="响应消息")
    data: ArtifactRespData = Field(description="响应数据")


# 无限大的页面大小，用于一次性获取所有制品
InfinityPageSize = 10000 * 100


class StsResp(BaseModel):
    """STS 临时凭证"""

    access_key_id: Optional[str] = Field(default=None, alias="access_key_id", description="访问密钥ID")
    secret_access_key: Optional[str] = Field(default=None, alias="secret_access_key", description="秘密访问密钥")
    session_token: Optional[str] = Field(default=None, alias="session_token", description="会话令牌")
    expiration: Optional[int] = Field(default=None, alias="expiration", description="过期时间")
    endpoint: Optional[str] = Field(default=None, alias="endpoint", description="端点URL")
    bucket: Optional[str] = Field(default=None, alias="bucket", description="存储桶名称")
