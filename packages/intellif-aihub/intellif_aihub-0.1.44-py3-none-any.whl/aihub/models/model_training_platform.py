from __future__ import annotations

from enum import IntEnum
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict


class Env(BaseModel):
    """环境变量"""

    key: str = Field(description="变量名")
    value: str = Field(description="变量值")


class Sku(BaseModel):
    """sku"""

    cpu: int = Field(description="CPU数")
    gpu: int = Field(description="GPU数")
    memory: int = Field(description="内存GiB")


class VirtualCluster(BaseModel):
    """虚拟集群"""

    id: int = Field(description="ID")
    name: str = Field(description="名称")
    gpu_type: str = Field(alias="gpu_type", description="GPU类型，A800/4090/3090/2080")
    label: str = Field(description="标签")
    sku: Sku = Field(description="SKU")


class Storage(BaseModel):
    """存储"""

    id: int = Field(description="存储ID")
    name: str = Field(description="存储名称")
    path: str = Field(description="挂载路径")
    server_path: str = Field(alias="server_path", description="服务器路径")
    server_host: str = Field(alias="server_host", description="服务器地址")
    server_type: str = Field(alias="server_type", description="服务器类型")
    permission: str = Field(description="权限")
    description: str = Field(description="说明")


class Category(BaseModel):
    """分类"""

    id: int = Field(description="分类ID")
    name: str = Field(description="分类名称")


class Project(BaseModel):
    """项目"""

    id: int = Field(description="项目ID")
    name: str = Field(description="项目名称")
    description: str = Field(description="项目描述")


class User(BaseModel):
    """用户"""

    id: int = Field(description="用户ID")
    name: str = Field(description="用户名")


class TrainingStatus(IntEnum):
    """训练任务状态：1-Waiting；2-Running；3-Success；4-Failed；5-Stopped"""
    Waiting = 1
    Running = 2
    Success = 3
    Failed = 4
    Stopped = 5


class PreemptPolicy(IntEnum):
    """抢占策略：0-非VIP任务；1-等待任务完成；2-停止任务"""
    NONE = 0  # 非VIP任务
    WAIT = 1  # 等待任务完成
    STOP = 2  # 停止任务


class CreateTrainingRequest(BaseModel):
    """创建训练任务请求"""

    framework: str = Field(description="训练框架，如PyTorchJob/MpiJobMpiRun/MpiJobDeepspeed")
    name: str = Field(description="任务名称")
    description: Optional[str] = Field(None, description="描述")
    command: Optional[str] = Field(None, description="命令")
    image: str = Field(description="镜像")
    virtual_cluster_id: int = Field(alias="virtual_cluster_id", description="虚拟集群ID")
    sku_cnt: int = Field(alias="sku_cnt", description="sku数量")
    enable_ssh: Optional[bool] = Field(False, alias="enable_ssh", description="是否开启SSH")
    envs: Optional[List[Env]] = Field(default_factory=list, description="环境变量")
    storage_ids: Optional[List[int]] = Field(default_factory=list, alias="storage_ids", description="挂载存储ID列表")
    instances: int = Field(description="实例数")
    use_ib_network: Optional[bool] = Field(False, alias="use_ib_network", description="是否使用IB网络")
    always_pull_image: Optional[bool] = Field(False, alias="always_pull_image", description="每次强制拉镜像")
    shm: Optional[int] = Field(None, description="共享内存")
    category_id: int = Field(alias="category_id", description="分类ID")
    project_id: int = Field(alias="project_id", description="项目ID")
    estimate_run_time: Optional[int] = Field(None, alias="estimate_run_time", description="预计运行时长(s)")
    is_quota_schedule: Optional[bool] = Field(False, alias="is_quota_schedule", description="是否配额调度")

    model_config = {"use_enum_values": True}


class CreateTrainingResponse(BaseModel):
    """创建训练任务返回"""

    id: int = Field(description="训练任务ID")


class ListTrainingsRequest(BaseModel):
    """查询训练任务列表请求"""

    page_size: int = Field(20, alias="page_size", description="每页数量")
    page_num: int = Field(1, alias="page_num", description="当前页码")
    user_id: Optional[int] = Field(None, alias="user_id", description="用户过滤")
    name: Optional[str] = Field(None, description="名称过滤")
    virtual_cluster_id: Optional[int] = Field(None, alias="virtual_cluster_id", description="虚拟集群过滤")
    status: Optional[TrainingStatus] = Field(None, description="状态过滤")
    category_id: Optional[int] = Field(None, alias="category_id", description="分类过滤")
    project_id: Optional[int] = Field(None, alias="project_id", description="项目过滤")
    is_quota_schedule: Optional[bool] = Field(None, alias="is_quota_schedule", description="配额调度过滤")

    model_config = {"use_enum_values": True}


class Training(BaseModel):
    """训练任务详情"""

    id: int = Field(description="任务ID")
    framework: str = Field(description="训练框架")
    name: str = Field(description="名称")
    description: str = Field(description="描述")
    command: str = Field(description="命令")
    image: str = Field(description="镜像")
    virtual_cluster: VirtualCluster = Field(alias="virtual_cluster", description="虚拟集群")
    sku_cnt: int = Field(alias="sku_cnt", description="SKU数量")
    enable_ssh: bool = Field(alias="enable_ssh", description="SSH开启")
    envs: Optional[List[Env]] = Field(None, description="环境变量")
    storages: Optional[List[Storage]] = Field(None, description="挂载存储")
    instances: int = Field(description="实例数")
    created_at: int = Field(alias="created_at", description="创建时间")
    username: str = Field(description="提交人")
    user_id: int = Field(alias="user_id", description="提交人ID")
    namespace: str = Field(description="K8s Namespace")
    res_name: str = Field(alias="res_name", description="K8s资源名")
    status: TrainingStatus = Field(description="状态")
    use_ib_network: bool = Field(alias="use_ib_network", description="IB网络")
    always_pull_image: bool = Field(alias="always_pull_image", description="每次拉镜像")
    shm: int = Field(description="共享内存")
    category: Category = Field(description="分类")
    project: Project = Field(description="项目")
    avg_gpu_util: float = Field(alias="avg_gpu_util", description="平均GPU利用率")
    finished_at: int = Field(alias="finished_at", description="结束时间")
    started_at: int = Field(alias="started_at", description="开始时间")
    estimate_run_time: int = Field(alias="estimate_run_time", description="预计运行时长")
    cluster_partition: str = Field(alias="cluster_partition", description="集群分区")
    preempt_policy: PreemptPolicy = Field(alias="preempt_policy", description="抢占策略")
    stop_op_user: Optional[User] = Field(None, alias="stop_op_user", description="停止操作人")
    use_new_log: bool = Field(alias="use_new_log", description="是否使用新版日志")
    is_quota_schedule: bool = Field(alias="is_quota_schedule", description="配额调度")

    model_config = ConfigDict(protected_namespaces=(), use_enum_values=True)


class ListTrainingsResponse(BaseModel):
    """查询训练任务列表返回"""

    total: int = Field(description="总条数")
    page_size: int = Field(alias="page_size", description="每页数量")
    page_num: int = Field(alias="page_num", description="当前页码")
    data: List[Training] = Field(description="训练列表")


class Pod(BaseModel):
    """训练任务Pod"""

    id: int = Field(description="ID")
    namespace: str = Field(description="Namespace")
    name: str = Field(description="名称")
    status: str = Field(description="状态")
    created_at: int = Field(alias="created_at", description="创建时间")
    started_at: int = Field(alias="started_at", description="启动时间")
    finished_at: int = Field(alias="finished_at", description="结束时间")
    host_ip: str = Field(alias="host_ip", description="宿主机IP")
    node_name: str = Field(alias="node_name", description="节点名")
    ssh_port: int = Field(alias="ssh_port", description="SSH端口")
    ssh_info: str = Field(alias="ssh_info", description="SSH连接信息")
    use_new_log: bool = Field(alias="use_new_log", description="是否使用新版日志")


class ListTrainingPodsRequest(BaseModel):
    """查询训练任务Pod列表请求"""

    page_size: int = Field(20, alias="page_size", description="每页数量")
    page_num: int = Field(1, alias="page_num", description="当前页码")


class ListTrainingPodsResponse(BaseModel):
    """查询训练任务Pod列表返回"""

    total: int = Field(description="总条数")
    page_size: int = Field(alias="page_size", description="每页数量")
    page_num: int = Field(alias="page_num", description="当前页码")
    data: List[Pod] = Field(description="Pod列表")


class PodLogInfo(BaseModel):
    """pod日志信息"""

    name: str = Field(description="日志名称")
    url: str = Field(description="URL")


class GetTrainingPodLogsNewResponse(BaseModel):
    """查询训练任务Pod日志返回"""

    logs: List[PodLogInfo] = Field(description="日志列表")


class GetTrainingPodSpecResponse(BaseModel):
    """查询训练任务Pod Spec返回"""

    spec: str = Field(description="Pod YAML Spec")


class GetTrainingPodEventsResponse(BaseModel):
    """查询训练任务Pod Event返回"""

    events: str = Field(description="事件内容")


class TrainingUser(BaseModel):
    """训练任务用户"""

    user_id: int = Field(alias="user_id", description="用户ID")
    username: str = Field(description="用户名")


class ListTrainingUsersRequest(BaseModel):
    """查询训练任务用户列表请求"""

    page_size: int = Field(20, alias="page_size", description="每页数量")
    page_num: int = Field(1, alias="page_num", description="当前页码")


class ListTrainingUsersResponse(BaseModel):
    """查询训练任务用户列表返回"""

    total: int = Field(description="总条数")
    page_size: int = Field(alias="page_size", description="每页数量")
    page_num: int = Field(alias="page_num", description="当前页码")
    data: Optional[List[TrainingUser]] = Field(default_factory=list, description="用户列表")


class Container(BaseModel):
    """容器"""

    namespace: str = Field(description="Namespace")
    pod_name: str = Field(alias="pod_name", description="Pod名")
    container_name: str = Field(alias="container_name", description="容器名")


class TrainingContainer(BaseModel):
    """训练容器"""

    training_id: int = Field(alias="training_id", description="训练ID")
    training_name: str = Field(alias="training_name", description="训练名")
    containers: List[Container] = Field(description="容器列表")


class ListTrainingContainersRequest(BaseModel):
    """查询训练任务容器列表请求"""

    page_size: int = Field(20, alias="page_size", description="每页数量")
    page_num: int = Field(1, alias="page_num", description="当前页码")


class ListTrainingContainersResponse(BaseModel):
    """查询训练任务容器列表返回"""

    total: int = Field(description="总条数")
    page_size: int = Field(alias="page_size", description="每页数量")
    page_num: int = Field(alias="page_num", description="当前页码")
    data: Optional[List[TrainingContainer]] = Field(default_factory=list, description="训练容器列表")


class ListStoragesResponse(BaseModel):
    data: List[Storage] = Field(default_factory=list, description="存储列表")
