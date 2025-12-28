from __future__ import annotations

from enum import IntEnum
from typing import List, Optional

from pydantic import BaseModel, Field


class Env(BaseModel):
    """环境变量"""
    key: str = Field(description="变量名")
    value: Optional[str] = Field(None, description="变量值")


class Source(BaseModel):
    """节点输入来源"""
    node: Optional[str] = Field(None, description="节点")
    param: Optional[str] = Field(None, description="参数名")


class InputParam(BaseModel):
    """节点输入"""
    input_param: str = Field(alias="input_param", description="输入参数名")
    source: Optional[Source] = Field(None, description="来源")


class PipelineInput(BaseModel):
    """顶层输入"""
    input_param: str = Field(alias="input_param", description="顶层输入参数名")


class OutputParam(BaseModel):
    """节点输出"""
    output_param: str = Field(alias="output_param", description="输出参数名")
    output_file: str = Field(alias="output_file", description="生成文件路径")
    value_type: Optional[int] = Field(None, alias="value_type", description="0-字符串，1-文件路径")


class Node(BaseModel):
    """工作流节点"""
    uuid: str = Field(description="节点唯一ID")
    position: Optional[List[int]] = Field(default_factory=list, description="画布坐标")
    name: str = Field(description="节点名称")
    task_type: str = Field(alias="task_type", description="任务类别 compute/monitor")
    depends_on: List[str] = Field(alias="depends_on", description="依赖节点uuid列表")
    command: Optional[str] = Field(None, description="执行命令")
    image: Optional[str] = Field(None, description="镜像")
    retry_cnt: Optional[int] = Field(0, alias="retry_cnt", description="失败重试次数")
    virtual_cluster_id: Optional[int] = Field(None, alias="virtual_cluster_id", description="虚拟集群ID")
    sku_cnt: Optional[int] = Field(None, alias="sku_cnt", description="sku数量")
    envs: List[Env] = Field(default_factory=list, alias="envs", description="环境变量")
    inputs: List[InputParam] = Field(default_factory=list, alias="inputs", description="输入列表")
    outputs: List[OutputParam] = Field(default_factory=list, alias="outputs", description="输出列表")
    storage_ids: List[int] = Field(default_factory=list, alias="storage_ids", description="挂载存储 ID")
    module_id: Optional[int] = Field(None, alias="module_id", description="模块 ID")
    module_version: Optional[int] = Field(None, alias="module_version", description="模块版本号")


class User(BaseModel):
    """用户"""
    id: int = Field(description="用户ID")
    name: str = Field(description="用户名")


class EnvDef(BaseModel):
    """模块环境变量定义"""
    key: str = Field(description="名称")
    description: str = Field(description="描述")
    is_optional: Optional[bool] = Field(False, alias="is_optional", description="是否可选")
    suggestion: Optional[str] = Field(None, description="建议配置")


class InputDef(BaseModel):
    """模块输入定义"""
    name: str = Field(description="名称")
    description: str = Field(description="描述")
    is_optional: Optional[bool] = Field(False, alias="is_optional", description="是否可选")


class OutputDef(BaseModel):
    """模块输出定义"""
    name: str = Field(description="名称")
    value_type: int = Field(alias="value_type", description="类型，0-普通文本，1-文件路径")
    description: str = Field(description="描述")
    path: str = Field(description="路径")


class ModuleCategory(BaseModel):
    """模块类别"""
    id: int = Field(description="类别 ID")
    name: str = Field(description="类别名称")
    description: str = Field(description="类别描述")


class CodeConfig(BaseModel):
    """构建镜像所需的代码仓库信息"""
    repo: str = Field(description="仓库地址")
    ref: str = Field(description="分支/Tag")
    commit: str = Field(description="Commit 哈希")
    dockerfile: str = Field(description="Dockerfile路径")
    build_dir: str = Field(alias="build_dir", description="构建目录")
    readme_path: str = Field(alias="readme_path", description="README文件路径")
    readme_content: str = Field(alias="readme_content", description="README纯文本")
    image_id: int = Field(alias="image_id", description="生成镜像记录ID")
    image_uri: str = Field(alias="image_uri", description="镜像仓库URI")




# ------------------------------------------------------------------ #
# Pipeline
# ------------------------------------------------------------------ #
class Pipeline(BaseModel):
    """工作流"""
    id: int = Field(description="工作流 ID")
    name: str = Field(description="名称")
    description: str = Field(description="描述")
    latest_version_id: Optional[int] = Field(None, alias="latest_version_id", description="最新版本ID")
    latest_version_name: Optional[str] = Field(None, alias="latest_version_name", description="最新版本名")
    version_cnt: int = Field(alias="version_cnt", description="版本数量")
    created_at: int = Field(alias="created_at", description="创建时间戳（ms）")
    user_id: int = Field(alias="user_id", description="创建者ID")
    username: str = Field(description="创建者用户名")
    ran_cnt: int = Field(alias="ran_cnt", description="累计运行次数")


class ListPipelinesRequest(BaseModel):
    """查询工作流列表请求"""
    page_size: int = Field(20, alias="page_size", description="每页数量")
    page_num: int = Field(1, alias="page_num", description="当前页码")
    name: Optional[str] = Field(None, description="名称过滤")
    user_id: Optional[int] = Field(None, alias="user_id", description="用户过滤")
    order_by: Optional[str] = Field(None, alias="order_by", description="排序字段")
    order_type: Optional[str] = Field(None, alias="order_type", description="asc/desc")


class ListPipelinesResponse(BaseModel):
    """查询工作流列表返回"""
    total: int = Field(description="总数")
    page_size: int = Field(alias="page_size", description="每页数量")
    page_num: int = Field(alias="page_num", description="当前页码")
    data: Optional[List[Pipeline]] = Field(default_factory=list, description="工作流列表")


class CreatePipelineRequest(BaseModel):
    """创建工作流请求"""
    pipeline_name: str = Field(alias="pipeline_name", description="工作流名称")
    version_name: str = Field(alias="version_name", description="版本名称")
    description: Optional[str] = Field(None, description="描述")
    nodes: Optional[List[Node]] = Field(default_factory=list, description="节点定义列表")
    inputs: Optional[List[PipelineInput]] = Field(default_factory=list, description="顶层输入参数列表")


class CreatePipelineResponse(BaseModel):
    """创建工作流返回"""
    id: int = Field(description="工作流ID")


class PipelineBrief(BaseModel):
    """工作流简要信息"""
    id: int = Field(description="工作流ID")
    name: str = Field(description="名称")


class SelectPipelinesRequest(BaseModel):
    """选择工作流请求"""
    name: Optional[str] = Field(None, description="名称过滤")


class SelectPipelinesResponse(BaseModel):
    """选择工作流返回"""
    data: Optional[List[PipelineBrief]] = Field(default_factory=list, description="工作流简要列表")


class PipelineUserBrief(BaseModel):
    """工作流用户信息"""
    id: int = Field(description="用户ID")
    name: str = Field(description="用户名")


class SelectPipelineUsersResponse(BaseModel):
    """选择工作流用户返回"""
    data: Optional[List[PipelineUserBrief]] = Field(default_factory=list, description="工作流用户列表")


# ------------------------------------------------------------------ #
# Pipeline-Version
# ------------------------------------------------------------------ #
class PipelineVersion(BaseModel):
    """工作流版本信息"""
    id: int = Field(description="版本ID")
    pipeline_id: int = Field(alias="pipeline_id", description="工作流ID")
    name: str = Field(description="版本名")
    description: str = Field(description="描述")
    created_at: int = Field(alias="created_at", description="创建时间")
    input_config: str = Field(alias="input_config", description="输入配置")
    can_copy: bool = Field(alias="can_copy", description="是否允许复制")


class ListPipelineVersionsRequest(BaseModel):
    """查询工作流版本列表请求"""
    page_size: int = Field(20, alias="page_size", description="每页数量")
    page_num: int = Field(1, alias="page_num", description="当前页码")
    pipeline_id: Optional[int] = Field(None, alias="pipeline_id", description="按工作流ID过滤")


class ListPipelineVersionsResponse(BaseModel):
    """查询工作流版本列表返回"""
    total: int = Field(description="总数")
    page_size: int = Field(alias="page_size", description="每页数量")
    page_num: int = Field(alias="page_num", description="当前页码")
    data: Optional[List[PipelineVersion]] = Field(default_factory=list, description="工作流版本列表")


class CreatePipelineVersionRequest(BaseModel):
    """创建工作流版本请求"""
    pipeline_id: int = Field(alias="pipeline_id", description="工作流ID")
    version_name: str = Field(alias="version_name", description="版本名")
    description: Optional[str] = Field(None, description="描述")
    nodes: Optional[List[Node]] = Field(default_factory=list, description="节点定义")
    inputs: Optional[List[PipelineInput]] = Field(default_factory=list, description="输入定义")


class CreatePipelineVersionResponse(BaseModel):
    """创建工作流版本返回"""
    id: int = Field(description="工作流版本ID")


class PipelineVersionBrief(BaseModel):
    """工作流版本简要信息"""
    id: int = Field(description="工作流版本ID")
    name: str = Field(description="版本名")


class SelectPipelineVersionsRequest(BaseModel):
    """选择工作流版本请求"""
    name: Optional[str] = Field(None, description="名称过滤")
    pipeline_id: int = Field(alias="pipeline_id", description="工作流ID过滤")


class SelectPipelineVersionsResponse(BaseModel):
    """选择工作流版本返回"""
    data: Optional[List[PipelineVersionBrief]] = Field(default_factory=list, description="工作流版本下拉列表")


class GetPipelineVersionInputParamsResponse(BaseModel):
    """获取工作流版本输入参数返回"""
    data: Optional[List[str]] = Field(default_factory=list, description="工作流版本的输入参数")


class MigratePipelineVersionsRequest(BaseModel):
    """迁移工作流版本请求"""
    start_id: int = Field(alias="start_id", description="开始版本ID")
    end_id: int = Field(alias="end_id", description="结束版本ID")


# ------------------------------------------------------------------ #
# Run
# ------------------------------------------------------------------ #
class Sku(BaseModel):
    """sku"""
    cpu: int = Field(description="CPU")
    gpu: int = Field(description="GPU")
    memory: int = Field(description="内存 GiB")


class VirtualCluster(BaseModel):
    """虚拟集群"""
    id: int = Field(description="虚拟集群ID")
    name: str = Field(description="虚拟集群名称")
    sku: Sku = Field(description="sku")


class Project(BaseModel):
    """项目"""
    id: int = Field(description="项目ID")
    name: str = Field(description="项目名称")


class IOParam(BaseModel):
    """输入/输出参数"""
    input: str = Field(description="输入参数")
    output: str = Field(description="输出参数")


class TaskNodeStatus(IntEnum):
    """任务节点状态：1-Waiting；2-Running；3-Success；4-Fail"""
    Waiting = 1
    Running = 2
    Success = 3
    Fail = 4


class TaskNode(BaseModel):
    """运行任务的单个节点信息"""
    name: str = Field(description="节点名称")
    params: IOParam = Field(description="输入/输出")
    message: str = Field(description="消息")
    status: TaskNodeStatus = Field(description="状态")
    namespace: str = Field(description="K8s Namespace")
    pod_name: str = Field(alias="pod_name", description="Pod 名称")
    started_at: int = Field(alias="started_at", description="启动时间戳")
    finished_at: int = Field(alias="finished_at", description="完成时间戳")
    dependencies: Optional[List[str]] = Field(default_factory=list, description="依赖节点 uuid")
    task_id: int = Field(alias="task_id", description="任务ID")
    module_id: int = Field(alias="module_id", description="模块ID")
    module_version: int = Field(alias="module_version", description="模块版本号")
    use_cache: bool = Field(alias="use_cache", description="是否使用缓存")
    virtual_cluster: VirtualCluster = Field(alias="virtual_cluster", description="虚拟集群")
    avg_gpu_util: float = Field(alias="avg_gpu_util", description="平均GPU利用率")

    model_config = {"use_enum_values": True}


class Param(BaseModel):
    """参数"""
    key: str = Field(description="键")
    value: Optional[str] = Field(None, description="值")


class NodeVirtualCluster(BaseModel):
    """节点虚拟集群"""
    virtual_cluster: VirtualCluster = Field(alias="virtual_cluster", description="虚拟集群")
    nodes: List[str] = Field(description="节点列表")


class RunStatus(IntEnum):
    """运行状态：1-Waiting；2-Running；3-Success；4-Failed；5-Stopped"""
    Waiting = 1
    Running = 2
    Success = 3
    Failed = 4
    Stopped = 5


class Run(BaseModel):
    """运行实例"""
    id: int = Field(description="ID")
    name: str = Field(description="名称")
    description: str = Field(description="描述")
    duration: int = Field(description="总耗时(s)")
    pipeline_id: int = Field(alias="pipeline_id", description="工作流ID")
    pipeline_name: str = Field(alias="pipeline_name", description="工作流名称")
    pipeline_version_id: int = Field(alias="pipeline_version_id", description="工作流版本ID")
    pipeline_version_name: str = Field(alias="pipeline_version_name", description="工作流版本名")
    started_at: int = Field(alias="started_at", description="开始时间")
    finished_at: int = Field(alias="finished_at", description="结束时间")
    created_at: int = Field(alias="created_at", description="创建时间")
    status: RunStatus = Field(description="状态码")
    task_nodes: Optional[List[TaskNode]] = Field(default_factory=list, alias="task_nodes", description="节点信息")
    params: Optional[List[Param]] = Field(default_factory=list, description="运行时入参")
    username: str = Field(description="用户名")
    node_virtual_clusters: Optional[List[NodeVirtualCluster]] = Field(default_factory=list,
                                                                      alias="node_virtual_clusters",
                                                                      description="节点虚拟集群")
    project: Project = Field(description="所属项目")
    avg_gpu_util: float = Field(alias="avg_gpu_util", description="平均GPU利用率")
    total_gpu_time: float = Field(alias="total_gpu_time", description="总的gpu用时")

    model_config = {"use_enum_values": True}


class ListRunsRequest(BaseModel):
    """查询运行实例列表请求"""
    page_size: int = Field(20, alias="page_size", description="每页数量")
    page_num: int = Field(1, alias="page_num", description="当前页码")
    name: Optional[str] = Field(None, description="名称过滤")
    user_id: Optional[int] = Field(None, alias="user_id", description="用户过滤")
    status: Optional[RunStatus] = Field(None, description="状态过滤")

    model_config = {"use_enum_values": True}


class ListRunsResponse(BaseModel):
    """查询运行实例列表返回"""
    total: int = Field(description="总数")
    page_size: int = Field(alias="page_size", description="每页数量")
    page_num: int = Field(alias="page_num", description="当前页码")
    data: Optional[List[Run]] = Field(default_factory=list, description="运行列表")


class NodeVirtualClusterSetting(BaseModel):
    """节点虚拟集群设置"""
    virtual_cluster_id: int = Field(alias="virtual_cluster_id", description="虚拟集群ID")
    nodes: List[str] = Field(description="节点列表")


class CreateRunRequest(BaseModel):
    """创建运行实例请求"""
    pipeline_id: int = Field(alias="pipeline_id", description="工作流ID")
    pipeline_version_id: int = Field(alias="pipeline_version_id", description="工作流版本ID")
    name: str = Field(description="运行名称")
    description: Optional[str] = Field(None, description="描述")
    params: Optional[List[Param]] = Field(default_factory=list, description="运行时入参")
    user_id: Optional[int] = Field(None, alias="user_id", description="用户ID")
    use_cache: Optional[bool] = Field(False, alias="use_cache", description="是否使用缓存")
    node_virtual_clusters: Optional[List[NodeVirtualClusterSetting]] = Field(default_factory=list,
                                                                             alias="node_virtual_clusters",
                                                                             description="节点虚拟集群")
    project_id: int = Field(alias="project_id", description="所属项目ID")


class CreateRunResponse(BaseModel):
    """创建运行实例返回"""
    id: int = Field(description="运行ID")


class GetRunTaskLogsResponse(BaseModel):
    """获取运行实例日志返回"""
    log: str = Field(description="日志文本")
    log_s3_url: str = Field(alias="log_s3_url", description="日志文件S3链接")


class GetRunTaskPodResponse(BaseModel):
    """获取运行实例Pod返回"""
    pod: str = Field(description="Pod描述YAML")


class GetRunTaskEventsResponse(BaseModel):
    """获取运行实例Event返回"""
    events: str = Field(description="事件文本")


class RunUserBrief(BaseModel):
    """运行实例用户简要信息"""
    id: int = Field(description="用户ID")
    name: str = Field(description="用户名")


class SelectRunUsersResponse(BaseModel):
    """选择运行实例用户返回"""
    data: Optional[List[RunUserBrief]] = Field(default_factory=list, description="运行用户列表")


class RetryRunResponse(Run):
    """重试Run返回"""
    pass


class StopRunResponse(Run):
    """停止Run返回"""
    pass


class ResubmitRunResponse(Run):
    """重新提交Run返回"""
    pass


# ------------------------------------------------------------------ #
# Module
# ------------------------------------------------------------------ #
class VersionBrief(BaseModel):
    """模块版本简要信息"""
    id: int = Field(description="版本ID")
    version: int = Field(description="版本号")
    status: int = Field(description="状态")


class LatestVersion(BaseModel):
    """模块最新版本信息"""
    id: int = Field(description="版本ID")
    name: str = Field(description="版本名称")
    description: str = Field(description="版本描述")
    version: int = Field(description="版本号")
    status: int = Field(description="状态：1-构建中，2-构建成功，3-构建失败，4-审核中，5-已发布，6-审核失败")
    created_at: int = Field(alias="created_at", description="创建时间")
    updated_at: int = Field(alias="updated_at", description="更新时间")


class Module(BaseModel):
    """可复用任务模块（新版，包含版本列表）"""
    id: int = Field(description="模块ID")
    name: str = Field(description="模块名称")
    category: ModuleCategory = Field(description="所属类别")
    creator: User = Field(description="创建人")
    used_cnt: int = Field(alias="used_cnt", description="被引用次数")
    ran_cnt: int = Field(alias="ran_cnt", description="累计运行次数")
    latest_version: LatestVersion = Field(alias="latest_version", description="最新版本")
    version_list: List[VersionBrief] = Field(alias="version_list", description="版本列表")


class ModuleVersion(BaseModel):
    """模块版本详情"""
    module_id: int = Field(alias="module_id", description="模块ID")
    id: int = Field(description="版本ID")
    name: str = Field(description="版本名称")
    version: int = Field(description="版本号")
    description: str = Field(description="版本描述")
    category: ModuleCategory = Field(description="所属类别")
    code_config: CodeConfig = Field(alias="code_config", description="代码配置")
    envs: List[EnvDef] = Field(description="环境变量")
    inputs: List[InputDef] = Field(description="输入参数")
    outputs: List[OutputDef] = Field(description="输出参数")
    creator: User = Field(description="创建人")
    created_at: int = Field(alias="created_at", description="创建时间")
    updated_at: int = Field(alias="updated_at", description="更新时间")
    status: int = Field(description="状态：1-构建中，2-构建成功，3-构建失败，4-审核中，5-已发布，6-审核失败")
    hardware_suggestion: str = Field(alias="hardware_suggestion", description="硬件配置建议")
    audit_fail_reason: str = Field(alias="audit_fail_reason", description="审核失败原因")
    used_cnt: int = Field(alias="used_cnt", description="被引用次数")
    ran_cnt: int = Field(alias="ran_cnt", description="累计运行次数")
    image_build_log_url: str = Field(alias="image_build_log_url", description="镜像构建日志链接")
    version_list: List[VersionBrief] = Field(alias="version_list", description="版本列表")


class ListModulesRequest(BaseModel):
    """查询模块列表请求"""
    page_size: int = Field(20, alias="page_size", description="每页数量")
    page_num: int = Field(1, alias="page_num", description="当前页码")
    filter: Optional[int] = Field(None, description="特殊过滤，1 自己的或已发布的，2 自己的且可用的，3 已发布的")
    order_by: Optional[str] = Field(None, alias="order_by", description="排序字段")
    order_type: Optional[str] = Field(None, alias="order_type", description="排序类型")
    name: Optional[str] = Field(None, description="名称过滤")
    category_id: Optional[int] = Field(None, alias="category_id", description="类别ID过滤")
    user_id: Optional[int] = Field(None, alias="user_id", description="用户ID过滤")


class ListModulesResponse(BaseModel):
    """查询模块列表返回"""
    total: int = Field(description="总数")
    page_size: int = Field(alias="page_size", description="每页数量")
    page_num: int = Field(alias="page_num", description="当前页码")
    data: Optional[List[Module]] = Field(default_factory=list, description="模块列表")


class CreateModuleRequest(BaseModel):
    """创建模块请求（同时创建第一个版本）"""
    name: str = Field(description="模块名称")
    description: str = Field(description="模块描述")
    category_id: int = Field(alias="category_id", description="类别ID")
    repo: str = Field(description="仓库地址")
    ref: str = Field(description="分支/Tag")
    dockerfile_path: str = Field(alias="dockerfile_path", description="Dockerfile路径")
    build_dir: str = Field(alias="build_dir", description="构建目录")
    readme_path: str = Field(alias="readme_path", description="README文件路径")
    envs: Optional[List[EnvDef]] = Field(default_factory=list, description="环境变量定义")
    inputs: List[InputDef] = Field(description="输入定义")
    outputs: Optional[List[OutputDef]] = Field(default_factory=list, description="输出定义")
    hardware_suggestion: Optional[str] = Field(None, alias="hardware_suggestion", description="硬件建议")


class CreateModuleResponse(BaseModel):
    """创建模块返回"""
    id: int = Field(description="模块ID")


class SelectModuleUsersResponse(BaseModel):
    """选择模块用户返回"""
    data: Optional[List[User]] = Field(default_factory=list, description="模块用户列表")


# ------------------------------------------------------------------ #
# Module Version
# ------------------------------------------------------------------ #
class CreateModuleVersionRequest(BaseModel):
    """创建模块版本请求"""
    module_id: int = Field(alias="module_id", description="模块ID")
    name: str = Field(description="版本名称")
    description: str = Field(description="版本描述")
    category_id: int = Field(alias="category_id", description="类别ID")
    repo: str = Field(description="仓库地址")
    ref: str = Field(description="分支/Tag")
    dockerfile_path: str = Field(alias="dockerfile_path", description="Dockerfile路径")
    build_dir: str = Field(alias="build_dir", description="构建目录")
    readme_path: str = Field(alias="readme_path", description="README文件路径")
    envs: Optional[List[EnvDef]] = Field(default_factory=list, description="环境变量定义")
    inputs: List[InputDef] = Field(description="输入定义")
    outputs: Optional[List[OutputDef]] = Field(default_factory=list, description="输出定义")
    hardware_suggestion: Optional[str] = Field(None, alias="hardware_suggestion", description="硬件建议")


class CreateModuleVersionResponse(BaseModel):
    """创建模块版本返回"""
    id: int = Field(description="模块版本ID")


class EditModuleVersionRequest(BaseModel):
    """编辑模块版本请求"""
    id: int = Field(description="模块版本ID")
    name: str = Field(description="版本名称")
    description: str = Field(description="版本描述")
    category_id: int = Field(alias="category_id", description="类别ID")
    repo: str = Field(description="仓库地址")
    ref: str = Field(description="分支/Tag")
    dockerfile_path: str = Field(alias="dockerfile_path", description="Dockerfile路径")
    build_dir: str = Field(alias="build_dir", description="构建目录")
    readme_path: str = Field(alias="readme_path", description="README文件路径")
    envs: Optional[List[EnvDef]] = Field(default_factory=list, description="环境变量定义")
    inputs: List[InputDef] = Field(description="输入定义")
    outputs: Optional[List[OutputDef]] = Field(default_factory=list, description="输出定义")
    hardware_suggestion: Optional[str] = Field(None, alias="hardware_suggestion", description="硬件建议")


class EditModuleVersionResponse(BaseModel):
    """编辑模块版本返回"""
    pass


class RebuildModuleVersionResponse(BaseModel):
    """重新构建模块版本返回"""
    pass


class ReleaseModuleVersionResponse(BaseModel):
    """发布模块版本返回"""
    pass
