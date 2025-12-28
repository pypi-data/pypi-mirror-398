# !/usr/bin/env python
# -*-coding:utf-8 -*-
from enum import Enum
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field, ConfigDict


class BaseEvalReq(BaseModel):
    """评测任务基础请求模型"""

    run_id: str = Field(description="运行ID")
    type: str = Field(description="评测类型，支持 'llm' 和 'cv'")
    prediction_artifact_path: str = Field(description="推理产物的路径")
    user_id: int = Field(0, description="用户ID，默认0")


class ClientType(Enum):
    """客户端类型枚举"""

    Workflow = "workflow"
    sdk = "sdk"


class CreateLLMEvalReq(BaseEvalReq):
    """创建LLM类型评测任务请求"""

    type: str = Field(default="llm", description="评测类型，固定为 'llm'")
    dataset_id: int = Field(description="数据集ID")
    dataset_version_id: int = Field(description="数据集版本ID")
    evaled_artifact_path: str = Field(description="评测结果产物的路径")
    report: Dict = Field(description="评测报告")
    is_public: bool = Field(default=False, description="是否公开")
    client_type: ClientType = Field(default=ClientType.Workflow, description="客户端类型")
    model_config = {"use_enum_values": True}


class CreateCVEvalReq(BaseEvalReq):
    """创建CV类型评测任务请求"""

    type: str = Field(default="cv", description="评测类型，固定为 'cv'")
    metrics_artifact_path: str = Field(description="指标产物的路径")
    ground_truth_artifact_path: str = Field(description="真实标签产物的路径")
    is_public: bool = Field(default=False, description="是否公开")
    client_type: ClientType = Field(default=ClientType.Workflow, description="客户端类型")
    model_config = {"use_enum_values": True}


class MetricsArtifact(BaseModel):
    """指标产物配置"""

    MetricVizConfigID: int = Field(description="指标可视化配置ID")
    MetricArtifactPath: str = Field(description="指标产物路径")


class ReidConfig(BaseModel):
    """检索配置"""

    gallery_dataset_id: int = Field(description="底库数据集ID")
    gallery_dataset_version_id: int = Field(description="底库数据集版本ID")
    query_dataset_id: int = Field(description="查询数据集ID")
    query_dataset_version_id: int = Field(description="查询数据集版本ID")
    id_dataset_id: int = Field(description="ID数据集ID")
    id_dataset_version_id: int = Field(description="ID数据集版本ID")
    metrics_viz_artifacts: List[MetricsArtifact] = Field(description="指标可视化产物列表")
    search_result_artifact_path: str = Field(description="搜索结果产物路径")


class CreateReidEvalReq(BaseEvalReq):
    """创建检索类型评测任务请求"""

    type: str = Field(default="reid", description="评测类型，固定为 'reid'")
    model_id: int = Field(description="模型ID")
    reid_config: ReidConfig = Field(description="检索配置")
    metrics_artifact_path: str = Field(description="指标产物路径")
    is_public: bool = Field(default=False, description="是否公开")
    client_type: ClientType = Field(default=ClientType.Workflow, description="客户端类型")
    model_config = ConfigDict(protected_namespaces=(), use_enum_values=True)


class EvalRunDatasetV2(BaseModel):
    """V2 API 多数据集支持"""

    dataset_id: Optional[int] = Field(None, description="数据集ID")
    dataset_version_id: Optional[int] = Field(None, description="数据集版本ID")
    dataset_name: str = Field(description="数据集名称")
    dataset_summary: Optional[Dict[str, Any]] = Field(None, description="数据集摘要")
    metrics_summary: Optional[Dict[str, Any]] = Field(None, description="指标摘要")
    prediction_artifact_path: Optional[str] = Field(None, description="推理产物路径")
    evaled_artifact_path: Optional[str] = Field(None, description="评测产物路径")
    ground_truth_artifact_path: Optional[str] = Field(None, description="真实标签产物路径")
    sort_order: Optional[int] = Field(None, description="显示顺序")
    viz_summary: Optional[Dict[str, Any]] = Field(None, description="可视化摘要")
    arctern_dataset_id: Optional[int] = Field(None, description="Arctern数据集ID")
    arctern_dataset_name: Optional[str] = Field(None, description="Arctern数据集名称")
    arctern_metrics: Optional[Dict[str, Any]] = Field(None, description="Arctern指标")
    metrics_artifact_path: Optional[str] = Field(None, description="指标产物路径")


class EvalRun(BaseModel):
    """评测任务的运行实体"""

    id: int = Field(description="评测的运行ID")
    name: str = Field(description="评测名称")
    description: str = Field(description="评测描述")
    type: Optional[str] = Field(None, description="评测类型: llm, cv, reid, performance")
    user_id: int = Field(description="用户ID")
    user_name: Optional[str] = Field(None, description="用户名称")
    model_id: int = Field(description="模型ID")
    model_name: str = Field(description="模型名称")
    dataset_id: Optional[int] = Field(None, description="数据集ID")
    dataset_version_id: Optional[int] = Field(None, description="数据集版本ID")
    dataset_name: Optional[str] = Field(None, description="数据集名称")
    status: str = Field(description="状态")
    prediction_artifact_path: str = Field(description="推理产物路径")
    evaled_artifact_path: str = Field(description="评测结果产物路径")
    run_id: str = Field(description="运行ID")
    dataset_summary: Dict = Field(default_factory=dict, description="数据集摘要")
    metrics_summary: Dict = Field(default_factory=dict, description="指标摘要")
    viz_summary: Optional[Dict] = Field(default_factory=dict, description="可视化摘要")
    eval_config: Optional[Dict] = Field(default=None, description="评测配置")
    created_at: int = Field(description="创建时间")
    updated_at: int = Field(description="更新时间")
    ground_truth_artifact_path: Optional[str] = Field(None, description="真实标签产物路径")
    arctern_model_group_id: Optional[int] = Field(None, description="Arctern模型组ID")
    arctern_model_name: Optional[str] = Field(None, description="Arctern模型名称")
    arctern_dataset_id: Optional[int] = Field(None, description="Arctern数据集ID")
    arctern_dataset_name: Optional[str] = Field(None, description="Arctern数据集名称")
    is_public: bool = Field(default=False, description="是否公开")
    multi_datasets: Optional[List["EvalRunDatasetV2"]] = Field(None, description="V2多数据集支持")
    client_type: ClientType = Field(default=ClientType.Workflow, description="客户端类型")
    model_config = {"use_enum_values": True, "protected_namespaces": ()}


class CreateEvalResp(BaseModel):
    """创建评测任务的返回结果"""

    eval_run: EvalRun = Field(alias="eval_run", description="评测运行信息")


class ListEvalReq(BaseModel):
    """列出评测任务请求"""

    page_size: int = Field(20, description="页面大小")
    page_num: int = Field(1, description="页码")
    status: Optional[str] = Field(None, description="状态过滤")
    name: Optional[str] = Field(None, description="名称过滤")
    model_id: Optional[int] = Field(None, description="模型ID过滤")
    dataset_id: Optional[int] = Field(None, description="数据集ID过滤")
    dataset_version_id: Optional[int] = Field(None, description="数据集版本ID过滤")
    run_id: Optional[str] = Field(None, description="运行ID过滤")
    user_id: Optional[int] = Field(None, description="用户ID过滤")
    model_ids: Optional[str] = Field(None, description="模型ID列表过滤")
    dataset_ids: Optional[str] = Field(None, description="数据集ID列表过滤")
    dataset_version_ids: Optional[str] = Field(None, description="数据集版本ID列表过滤")
    type: Optional[str] = Field(None, description="评测类型过滤: llm, cv, reid, performance")
    device_info: Optional[str] = Field(None, description="设备信息过滤")
    gpu_count: Optional[int] = Field(None, description="GPU数量过滤")
    model_config = ConfigDict(protected_namespaces=(), use_enum_values=True)


class ListEvalResp(BaseModel):
    """列出评测任务响应"""

    total: int = Field(description="总数")
    page_size: int = Field(description="页面大小")
    page_num: int = Field(description="页码")
    data: List[EvalRun] = Field(description="评测运行列表")


class GrantPermissionReq(BaseModel):
    """授权权限请求"""

    user_ids: list[int] = Field(description="用户ID数组")


class CreatePerformanceEvalReq(BaseModel):
    """创建CV类型评测任务请求"""

    name: str = Field(description="评测名称")
    type: str = Field(default="performance", description="评测类型，固定为 'performance'")
    is_public: bool = Field(default=False, description="是否公开")
    client_type: ClientType = Field(default=ClientType.Workflow, description="客户端类型")

    # PerformanceArtifactPath
    performance_artifact_path: str = Field(description="性能产物路径")
    report: Dict = Field(description="评测报告")
    run_id: str = Field(description="运行ID")
    model_id: int = Field(description="模型ID")
    infer_service_id: int = Field(description="推理服务ID")
    eval_config: Dict[str, Any] = Field(description="评测配置")
    model_config = ConfigDict(protected_namespaces=(), use_enum_values=True)


# V2 API Models
class EvalRunDatasetReportV2(BaseModel):
    """V2 API 数据集报告结构"""

    dataset_id: Optional[int] = Field(None, description="数据集ID")
    dataset_version_id: Optional[int] = Field(None, description="数据集版本ID")
    dataset_name: str = Field(description="数据集名称")
    metrics: Optional[Dict[str, Any]] = Field(
        None, description="指标数据，格式: {'metrics': {...}, 'categories': {...}}"
    )
    viz: Optional[Dict[str, Any]] = Field(None, description="可视化数据")
    prediction_artifact_path: Optional[str] = Field(None, description="推理产物路径")
    evaled_artifact_path: Optional[str] = Field(None, description="评测产物路径")
    ground_truth_artifact_path: Optional[str] = Field(None, description="真实标签产物路径")
    metrics_artifact_path: Optional[str] = Field(None, description="指标产物路径")
    sort_order: Optional[int] = Field(None, description="显示顺序")
    arctern_dataset_id: Optional[int] = Field(None, description="Arctern数据集ID")
    arctern_dataset_name: Optional[str] = Field(None, description="Arctern数据集名称")
    arctern_metrics: Optional[Dict[str, Any]] = Field(None, description="Arctern指标")


class ReidConfigV2(BaseModel):
    """V2 API 检索配置"""

    gallery_dataset_id: int = Field(description="底库数据集ID")
    gallery_dataset_version_id: Optional[int] = Field(None, description="底库数据集版本ID")
    query_dataset_id: int = Field(description="查询数据集ID")
    query_dataset_version_id: Optional[int] = Field(None, description="查询数据集版本ID")
    id_dataset_id: Optional[int] = Field(None, description="ID数据集ID")
    id_dataset_version_id: Optional[int] = Field(None, description="ID数据集版本ID")
    metrics_viz_artifacts: List[MetricsArtifact] = Field(description="指标可视化产物列表")
    search_result_artifact_path: str = Field(description="搜索结果产物路径")


class PerformanceMetric(BaseModel):
    """V2 API 性能指标"""

    metric_name: str = Field(description="指标名称")
    value: float = Field(description="指标值")
    unit: str = Field(description="单位")


class SubDomainMetrics(BaseModel):
    """V2 API 子域指标"""

    sub_domain_name: str = Field(description="子域名称")
    metrics: Dict[str, Any] = Field(description="子域指标")


class OverallMetrics(BaseModel):
    """V2 API 整体指标"""

    overall: Dict[str, Any] = Field(description="整体指标")
    overall_description: Optional[Dict[str, Any]] = Field(None, description="整体指标描述")
    sub_domain: Optional[List[SubDomainMetrics]] = Field(None, description="子域指标列表")


class CreateEvalRunV2Req(BaseModel):
    """V2 API 创建评测运行请求"""

    run_id: str = Field(description="运行ID")
    name: str = Field(description="评测名称")
    type: Optional[str] = Field(None, description="评测类型: cv, llm, reid, performance")
    model_id: Optional[int] = Field(None, description="模型ID")
    user_id: Optional[int] = Field(None, description="用户ID")
    is_public: Optional[bool] = Field(True, description="是否公开")
    eval_config: Optional[Dict[str, Any]] = Field(None, description="评测配置")
    datasets: List[EvalRunDatasetReportV2] = Field(description="数据集报告列表")

    # CV specific fields
    arctern_model_group_id: Optional[int] = Field(None, description="Arctern模型组ID")
    arctern_model_name: Optional[str] = Field(None, description="Arctern模型名称")

    # ReID specific fields
    reid_config: Optional[ReidConfigV2] = Field(None, description="ReID配置")

    # Performance specific fields
    performance_artifact_path: Optional[str] = Field(None, description="性能产物路径")
    performance: Optional[List[PerformanceMetric]] = Field(None, description="性能指标列表")

    # Overall metrics
    overall_metrics: Optional[OverallMetrics] = Field(None, description="整体指标")
    model_config = ConfigDict(protected_namespaces=(), use_enum_values=True)


class CreateEvalRunV2Resp(BaseModel):
    """V2 API 创建评测运行响应"""

    id: int = Field(description="评测运行ID")
