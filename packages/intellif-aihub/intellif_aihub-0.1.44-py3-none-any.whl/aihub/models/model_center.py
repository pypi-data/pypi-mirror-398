from __future__ import annotations

import enum
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict, field_validator


class ListModelCard(BaseModel):
    """模型卡片"""

    id: int = Field(alias="id", description="模型ID")
    name: str = Field(alias="name", description="名称")
    description: str = Field(alias="description", description="描述")
    creator_id: int = Field(alias="creator_id", description="创建人ID")
    creator_name: str = Field(alias="creator_name", description="创建人名称")
    created_at: int = Field(alias="created_at", description="创建时间戳")
    updated_at: int = Field(alias="updated_at", description="更新时间戳")
    tags: List[int] = Field(default_factory=list, alias="tags", description="标签ID集合")
    status: str = Field(alias="status", description="状态")
    is_public: bool = Field(alias="is_public", description="是否公开")

    @field_validator("tags", mode="before")
    @classmethod
    def _none_to_empty_list(cls, v):
        return [] if v is None else v

    model_config = ConfigDict(protected_namespaces=())


class ModelTreeNode(BaseModel):
    """模型树节点"""

    model_id: int = Field(alias="model_id", description="模型ID")
    name: str = Field(alias="name", description="名称")
    relationship: str = Field(alias="relationship", description="与基模型关系")

    model_config = ConfigDict(protected_namespaces=())


class ModelCardDetail(ListModelCard):
    """模型卡片详情"""

    readme_content: str = Field(alias="readme_content", description="README 内容")
    model_tree: Optional[List[ModelTreeNode]] = Field(default=None, alias="model_tree", description="模型树")
    base_model: Optional[ModelTreeNode] = Field(default=None, alias="base_model", description="基模型")
    file_storage_path: Optional[str] = Field(alias="file_storage_path", description="文件存储路径")

    model_config = ConfigDict(protected_namespaces=())


class ModelDb(BaseModel):
    """模型"""

    id: int = Field(description="ID")
    name: str = Field(description="名称")
    description: str = Field(description="描述")
    readme_content: str = Field(alias="readme_content", description="README")
    user_id: int = Field(alias="user_id", description="创建人ID")
    status: str = Field(description="状态")
    is_public: bool = Field(alias="is_public", description="是否公开")
    base_model_id: int = Field(alias="base_model_id", description="基模型ID")
    relation: str = Field(description="与基模型关系")
    object_cnt: int = Field(alias="object_cnt", description="对象数量")
    data_size: int = Field(alias="data_size", description="数据大小")
    object_storage_path: str = Field(alias="object_storage_path", description="对象存储路径")
    file_storage_path: str = Field(alias="file_storage_path", description="文件存储路径")
    parquet_index_path: str = Field(alias="parquet_index_path", description="Parquet 索引路径")
    csv_file_path: str = Field(alias="csv_file_path", description="CSV 文件路径")
    task_status_s3_path: str = Field(alias="task_status_s3_path", description="任务状态S3路径")
    created_at: int = Field(alias="created_at", description="创建时间戳")
    updated_at: int = Field(alias="updated_at", description="更新时间戳")


class ListModelsRequest(BaseModel):
    """查询模型列表请求"""

    page_size: int = Field(20, alias="page_size", description="每页数量")
    page_num: int = Field(1, alias="page_num", description="当前页码")
    name: Optional[str] = Field(default=None, alias="name", description="名称过滤")
    tags: Optional[str] = Field(default=None, alias="tags", description="标签过滤")
    model_ids: Optional[str] = Field(default=None, alias="model_ids", description="模型ID过滤")

    model_config = ConfigDict(protected_namespaces=())


class ListModelsResponse(BaseModel):
    """查询模型列表返回"""

    total: int = Field(alias="total", description="总条数")
    page_size: int = Field(alias="page_size", description="每页数量")
    page_num: int = Field(alias="page_num", description="当前页码")
    data: List[ListModelCard] = Field(default_factory=list, alias="data", description="模型卡片列表")

    model_config = ConfigDict(protected_namespaces=())


class GetModelRequest(BaseModel):
    """查询模型详情请求"""

    id: int = Field(alias="id", description="模型ID")


class CreateModelRequest(BaseModel):
    """创建模型请求"""

    name: str = Field(alias="name", description="名称")
    description: Optional[str] = Field(default=None, alias="description", description="描述")
    tags: Optional[str] = Field(default=None, alias="tags", description="标签")
    is_public: bool = Field(alias="is_public", description="是否公开")
    readme_content: Optional[str] = Field(default=None, description="README 文本内容")


class CreateModelResponse(BaseModel):
    id: int = Field(alias="id", description="模型ID")


class EditModelRequest(BaseModel):
    """编辑模型请求"""

    name: Optional[str] = Field(default=None, alias="name", description="名称")
    description: Optional[str] = Field(default=None, alias="description", description="描述")
    is_public: Optional[bool] = Field(default=None, alias="is_public", description="是否公开")


class EditModelResponse(BaseModel):
    """编辑模型返回"""

    pass


class InferService(BaseModel):
    id: int = Field(..., description="唯一记录ID")
    model_id: int = Field(..., description="关联的模型ID")
    model_name: str = Field(default="", description="模型名称")
    user_id: int
    user_name: str
    name: str = Field(..., description="节点名称")

    # 使用 HttpUrl 自动验证链接格式
    endpoint_url: str = Field(..., description="服务端地址")

    status: str = Field(..., examples=["online", "offline"])

    # 对应 JSON 中的毫秒时间戳
    created_at: int
    updated_at: int

    api_key: str = Field(..., description="访问密钥")
    health_check_path: str
    os_info: str
    device_info: str
    infer_engine_type: str
    infer_engine_info: str
    driver_version: str
    model_config = ConfigDict(protected_namespaces=())


class TaskType(enum.Enum):
    """任务类型"""

    DETECTION = "detection"  # 目标检测
    IMAGE_SEGMENTATION = "Image_segmentation"  # 图像分割
    IMAGE_CLASSIFICATION = "image_classification"  # 图像分类
    LLM = "llm"  # LLM
    MASK_GENERATION = "mask-generation"  # 掩码生成
    TEXT_GENERATION = "text-generation"  # 文本生成
    IMAGE_TEXT_TO_TEXT = "image-text-to-text"  # 图文转文本
    TEXT_TO_IMAGE = "text-to-image"  # 文本转图像
    VISION_LANGUAGE = "vision-language"  # 视觉语言
    TEXT_EMBEDDING = "Text-Embedding"  # 文本嵌入


class Licence(enum.Enum):
    """许可证类型"""

    MIT = "MIT"
    APACHE_2_0 = "Apache 2.0"
    OTHER = "other"


class Framework(enum.Enum):
    """模型框架"""

    ONNX = "onnx"
    PYTORCH = "pytorch"
    TRANSFORMERS = "transformers"


class Language(enum.Enum):
    """模型语言"""

    MULTILINGUAL = "multilingual"  # 多语言
    CHINESE = "Zhc"  # 中文
    ENGLISH = "en"  # 英文


class DataFormat(enum.Enum):
    """数据格式"""

    FP16 = "fp16"
    BF16 = "bf16"
    VISUAL_W8A8_LLM_W4A8 = "Visual(Wi8Ai8) LLM(Wi4Ai8)"
    VISUAL_W8A8_LLM_W8A8 = "Visual(Wi8Ai8) LLM(Wi8Ai8)"
    VISUAL_W8A8_LLM_W4AF16 = "Visual(Wi8Ai8) LLM(Wi4Af16)"
    VISUAL_NONE_LLM_W8A8 = "Visual(\\) LLM(Wi8Ai8)"
    VISUAL_NONE_LLM_W4AF16 = "Visual(\\) LLM(Wi4Af16)"
    W4A8 = "Wi4Ai8"
    W8A8 = "Wi8Ai8"
    W4AF16 = "Wi4Af16"


class Param(BaseModel):
    """任务参数"""

    key: str = Field(alias="key", description="参数名")
    value: Optional[str] = Field(default=None, alias="value", description="参数值")


class CreateModelEvalTaskRequest(BaseModel):
    """创建模型评测任务请求"""

    task_name: str = Field(alias="task_name", description="任务名称")
    eval_type: Optional[str] = Field(default=None, alias="eval_type", description="评测类型")
    eval_method: str = Field(default="service", alias="eval_method", description="评测方法")
    infer_service_id: Optional[int] = Field(default=None, alias="infer_service_id", description="推理服务ID")
    workflow_tmp_id: Optional[int] = Field(default=None, alias="workflow_tmp_id", description="工作流模板ID")
    eval_config: Optional[dict] = Field(default=None, alias="eval_config", description="评测配置")
    params: Optional[List[Param]] = Field(default=None, alias="params", description="任务参数")
    virtual_cluster_id: Optional[int] = Field(default=None, alias="virtual_cluster_id", description="虚拟集群ID")

    model_config = ConfigDict(protected_namespaces=())


class CreateModelEvalTaskResponse(BaseModel):
    """创建模型评测任务响应"""

    id: int = Field(alias="id", description="任务ID")


class ModelTaskItem(BaseModel):
    """模型任务项"""

    eval_report_id: int = Field(alias="eval_report_id", description="评测报告ID")
    eval_report_name: str = Field(alias="eval_report_name", description="评测报告名称")
    id: int = Field(alias="id", description="任务ID")
    model_id: int = Field(alias="model_id", description="模型ID")
    model_name: str = Field(alias="model_name", description="模型名称")
    status: str = Field(alias="status", description="任务状态")
    task_name: str = Field(alias="task_name", description="任务名称")
    task_type: str = Field(alias="task_type", description="任务类型")
    workflow_run_id: int = Field(alias="workflow_run_id", description="工作流运行ID")
    workflow_run_name: str = Field(alias="workflow_run_name", description="工作流运行名称")
    workflow_tmp_id: int = Field(alias="workflow_tmp_id", description="工作流模板ID")
    workflow_tmp_name: str = Field(alias="workflow_tmp_name", description="工作流模板名称")

    model_config = ConfigDict(protected_namespaces=())


class GetModelTasksRequest(BaseModel):
    """获取模型任务列表请求"""

    page_size: int = Field(default=20, alias="page_size", description="每页数量")
    page_num: int = Field(default=1, alias="page_num", description="当前页码")

    model_config = ConfigDict(protected_namespaces=())


class GetModelTasksResponse(BaseModel):
    """获取模型任务列表响应"""

    total: int = Field(alias="total", description="总数")
    page_size: int = Field(alias="page_size", description="每页数量")
    page_num: int = Field(alias="page_num", description="当前页码")
    data: List[ModelTaskItem] = Field(default_factory=list, alias="data", description="任务列表")

    model_config = ConfigDict(protected_namespaces=())
