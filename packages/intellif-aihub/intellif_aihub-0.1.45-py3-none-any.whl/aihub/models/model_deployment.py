from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict


class Tag(BaseModel):
    """标签"""

    id: int = Field(alias="id", description="标签ID")
    name: str = Field(alias="name", description="标签名")


class SKU(BaseModel):
    """SKU配置"""

    cpu: int = Field(alias="cpu", description="CPU核心数")
    gpu_memory: int = Field(alias="gpu_memory", description="GPU内存(MB)")
    gpu_type: int = Field(alias="gpu_type", description="GPU类型")
    id: int = Field(alias="id", description="SKU ID")
    memory: int = Field(alias="memory", description="内存(MB)")
    network: int = Field(alias="network", description="网络带宽")


class VirtualClusterMsg(BaseModel):
    """虚拟集群信息"""

    created_at: Optional[int] = Field(default=None, alias="created_at", description="创建时间(毫秒时间戳)")
    id: int = Field(alias="id", description="集群ID")
    machine_cnt: Optional[int] = Field(default=None, alias="machine_cnt", description="机器数量")
    name: str = Field(alias="name", description="集群名称")
    tags: List[Tag] = Field(default_factory=list, alias="tags", description="标签列表")
    sku: SKU = Field(alias="sku", description="SKU配置")


class Storage(BaseModel):
    """存储配置"""

    id: int = Field(alias="id", description="存储ID")
    name: str = Field(alias="name", description="存储名称")
    path: str = Field(alias="path", description="挂载路径")
    server_path: str = Field(alias="server_path", description="服务器路径")
    server_host: str = Field(alias="server_host", description="服务器主机")
    server_type: str = Field(alias="server_type", description="服务器类型")
    permission: str = Field(alias="permission", description="权限")
    description: str = Field(alias="description", description="描述")


class DeploymentCreateRequest(BaseModel):
    """创建部署请求"""

    name: str = Field(alias="name", description="部署名称")
    docker_image_name: Optional[str] = Field(default=None, alias="docker_image_name", description="Docker镜像名称")
    container_concurrency: int = Field(default=1, alias="container_concurrency", description="容器并发数")
    envs: Optional[Dict[str, str]] = Field(default=None, alias="envs", description="环境变量")
    description: Optional[str] = Field(default=None, alias="description", description="描述")
    command_args: Optional[str] = Field(default=None, alias="command_args", description="命令参数")
    storage_ids: Optional[List[int]] = Field(default=None, alias="storage_ids", description="存储ID列表")
    container_port: Optional[int] = Field(default=None, alias="container_port", description="容器端口")
    virtual_cluster_id: int = Field(alias="virtual_cluster_id", description="虚拟集群ID")
    sku_cnt: Optional[int] = Field(default=None, alias="sku_cnt", description="SKU数量")
    deploy_template: str = Field(alias="deploy_template", description="部署模板")
    health_check_path: str = Field(alias="health_check_path", description="健康检查路径")
    share_machine: Optional[bool] = Field(default=None, alias="share_machine", description="是否共享机器")
    model_id: Optional[int] = Field(default=None, alias="model_id", description="模型ID")
    image_id: Optional[int] = Field(default=None, alias="image_id", description="镜像ID")

    model_config = ConfigDict(protected_namespaces=())


class DeploymentCreateResponse(BaseModel):
    """创建部署响应"""

    id: int = Field(alias="id", description="部署ID")


class DeploymentListRequest(BaseModel):
    """部署列表查询请求"""

    page_size: int = Field(default=20, alias="page_size", description="每页数量")
    page_num: int = Field(default=1, alias="page_num", description="当前页码")
    project_id: Optional[int] = Field(default=None, alias="project_id", description="项目ID")
    name: Optional[str] = Field(default=None, alias="name", description="部署名称过滤")
    status: int = Field(default=-1, alias="status", description="状态过滤")
    model_type: Optional[int] = Field(default=None, alias="model_type", description="模型类型")


class DeploymentDetail(BaseModel):
    """部署详情"""

    id: int = Field(alias="id", description="部署ID")
    name: str = Field(alias="name", description="部署名称")
    docker_image_name: Optional[str] = Field(default=None, alias="docker_image_name", description="Docker镜像名称")
    container_concurrency: Optional[int] = Field(default=None, alias="container_concurrency", description="容器并发数")
    envs: Optional[Dict[str, str]] = Field(default=None, alias="envs", description="环境变量")
    description: Optional[str] = Field(default=None, alias="description", description="描述")
    command_args: Optional[str] = Field(default=None, alias="command_args", description="命令参数")
    storage_ids: Optional[List[int]] = Field(default=None, alias="storage_ids", description="存储ID列表")
    container_port: Optional[int] = Field(default=None, alias="container_port", description="容器端口")
    virtual_cluster_id: Optional[int] = Field(default=None, alias="virtual_cluster_id", description="虚拟集群ID")
    sku_cnt: Optional[int] = Field(default=None, alias="sku_cnt", description="SKU数量")
    deploy_template: Optional[str] = Field(default=None, alias="deploy_template", description="部署模板")
    health_check_path: Optional[str] = Field(default=None, alias="health_check_path", description="健康检查路径")
    share_machine: Optional[bool] = Field(default=None, alias="share_machine", description="是否共享机器")
    model_id: Optional[int] = Field(default=None, alias="model_id", description="模型ID")
    image_id: Optional[int] = Field(default=None, alias="image_id", description="镜像ID")
    created_at: str = Field(alias="created_at", description="创建时间")
    updated_at: str = Field(alias="updated_at", description="更新时间")
    status: int = Field(alias="status", description="状态")
    version: int = Field(alias="version", description="版本")
    user_name: str = Field(alias="user_name", description="用户名")
    user_id: int = Field(alias="user_id", description="用户ID")
    need_force_start: bool = Field(alias="need_force_start", description="是否需要强制启动")
    is_vip: bool = Field(alias="is_vip", description="是否VIP")
    api_host: str = Field(alias="api_host", description="API主机地址")
    model_name: Optional[str] = Field(default=None, alias="model_name", description="模型名称")
    infer_service_id: Optional[int] = Field(default=None, alias="infer_service_id", description="推理服务ID")

    model_config = ConfigDict(protected_namespaces=())


class DeploymentListResponse(BaseModel):
    """部署列表响应"""

    total: int = Field(alias="total", description="总条数")
    page_size: int = Field(alias="page_size", description="每页数量")
    page_num: int = Field(alias="page_num", description="当前页码")
    data: List[DeploymentDetail] = Field(default_factory=list, alias="data", description="部署列表")


class DeploymentPodItem(BaseModel):
    """部署Pod信息"""

    name: str = Field(alias="name", description="Pod名称")
    node_name: str = Field(alias="node_name", description="节点名称")
    gpu_type: str = Field(alias="gpu_type", description="GPU类型")
    status: int = Field(alias="status", description="状态")
    gpu_num: int = Field(alias="gpu_num", description="GPU数量")
    cpu_num: int = Field(alias="cpu_num", description="CPU数量")
    memory: int = Field(alias="memory", description="内存(MB)")


class DeploymentPodsResponse(BaseModel):
    """部署Pods响应"""

    total: int = Field(alias="total", description="总条数")
    page_size: int = Field(alias="page_size", description="每页数量")
    page_num: int = Field(alias="page_num", description="当前页码")
    data: List[DeploymentPodItem] = Field(default_factory=list, alias="data", description="Pod列表")


class DeploymentLogRequest(BaseModel):
    """部署日志查询请求"""

    pod_name: Optional[str] = Field(default=None, alias="pod_name", description="Pod名称")
    page_size: int = Field(default=20, alias="page_size", description="每页数量")


class DeploymentLogResponse(BaseModel):
    """部署日志响应"""

    data: str = Field(alias="data", description="日志内容")
