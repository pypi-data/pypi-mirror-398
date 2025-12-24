from __future__ import annotations

from typing import List, Optional
from enum import IntEnum

from pydantic import BaseModel, Field


class AppType(IntEnum):
    """应用类型：1-Notebook；2-VncSsh"""
    Notebook = 1
    VncSsh = 2

class HardwareType(IntEnum):
    """硬件类型：1-CPU；2-GPU"""
    CPU = 1
    GPU = 2

class Status(IntEnum):
    """应用状态：1-关闭；2-启动中；3-已启动"""
    Closed = 1
    Starting = 2
    Started = 3

class Image(BaseModel):
    """项目"""
    id: int = Field(description="镜像ID")
    name: str = Field(description="镜像名称")
    uri: str = Field(description="镜像地址")
    app_type: AppType = Field(description="应用类型")
    hardware_type: HardwareType = Field(description="硬件类型")

class ListImagesReq(BaseModel):
    """查询镜像列表请求"""
    app_type: AppType = Field(description="应用类型")
    hardware_type: HardwareType = Field(description="硬件类型")

    model_config = {"use_enum_values": True}

class ListImagesResp(BaseModel):
    """查询镜像列表响应"""
    data: List[Image] = Field(description="镜像列表")

class User(BaseModel):
    """用户信息"""
    id: int = Field(description="用户ID")
    name: str = Field(description="用户名称")

class Env(BaseModel):
    """环境变量"""
    key: str = Field(description="环境变量键")
    value: str = Field(description="环境变量值")

class Storage(BaseModel):
    """存储信息"""
    id: int = Field(description="存储ID")
    name: str = Field(description="存储名称")
    path: str = Field(description="路径")
    server_path: str = Field(description="服务器路径", alias="server_path")
    server_host: str = Field(description="服务器主机", alias="server_host")
    server_type: str = Field(description="服务器类型", alias="server_type")
    permission: str = Field(description="权限")
    description: str = Field(description="描述")

class Notebook(BaseModel):
    """笔记本信息"""
    id: int = Field(description="笔记本ID")
    image: Image = Field(description="镜像信息")
    sku_cnt: int = Field(description="SKU数量", alias="sku_cnt")
    envs: Optional[List[Env]] = Field(description="环境变量列表", alias="envs")
    storages: List[Storage] = Field(description="存储列表", alias="storages")
    shm: int = Field(description="共享内存大小", alias="shm")
    hardware_type: HardwareType = Field(description="硬件类型", alias="hardware_type")
    status: Status = Field(description="状态")
    namespace: str = Field(description="命名空间")
    pod: str = Field(description="Pod名称")
    notebook_url: str = Field(description="笔记本URL", alias="notebook_url")
    vscode_url: str = Field(description="VSCode URL", alias="vscode_url")
    created_at: int = Field(description="创建时间", alias="created_at")
    creator: User = Field(description="创建者信息")
    app_type: AppType = Field(description="应用类型", alias="app_type")
    vnc_web_url: str = Field(description="VNC Web URL", alias="vnc_web_url")
    vnc_svr_addr: str = Field(description="VNC服务器地址", alias="vnc_svr_addr")
    vnc_resolution: str = Field(description="VNC分辨率", alias="vnc_resolution")
    ssh_info: str = Field(description="SSH信息", alias="ssh_info")

class ListNotebooksReq(BaseModel):
    """列出笔记本请求参数"""
    hardware_type: Optional[int] = Field(None, description="硬件类型，可选", alias="hardware_type")
    app_type: Optional[int] = Field(None, description="应用类型，可选", alias="app_type")

class ListNotebooksResp(BaseModel):
    """列出笔记本响应数据"""
    data: List[Notebook] = Field(description="笔记本列表数据")

class GetNotebookReq(BaseModel):
    """获取笔记本请求参数"""
    id: int = Field(description="笔记本ID", alias="id")

class CreateNotebookReq(BaseModel):
    """创建笔记本请求参数"""
    hardware_type: int = Field(description="硬件类型", alias="hardware_type")
    image_id: int = Field(description="镜像ID", alias="image_id")
    sku_cnt: Optional[int] = Field(None, description="SKU数量，可选", alias="sku_cnt")
    envs: Optional[List[Env]] = Field(None, description="环境变量列表，可选", alias="envs")
    storage_ids: Optional[List[int]] = Field(None, description="存储ID列表，可选", alias="storage_ids")
    shm: Optional[int] = Field(None, description="共享内存大小，可选", alias="shm")
    app_type: int = Field(description="应用类型", alias="app_type")
    resolution: Optional[str] = Field(None, description="分辨率，可选", alias="resolution")

class CreateNotebookResp(BaseModel):
    """创建笔记本响应数据"""
    id: int = Field(description="创建的笔记本ID")

class EditNotebookReq(BaseModel):
    """编辑笔记本请求参数"""
    id: int = Field(description="笔记本ID", alias="id")
    image_id: int = Field(description="镜像ID", alias="image_id")
    sku_cnt: Optional[int] = Field(None, description="SKU数量，可选", alias="sku_cnt")
    envs: Optional[List[Env]] = Field(None, description="环境变量列表，可选", alias="envs")
    storage_ids: Optional[List[int]] = Field(None, description="存储ID列表，可选", alias="storage_ids")
    shm: Optional[int] = Field(None, description="共享内存大小，可选", alias="shm")
    resolution: Optional[str] = Field(None, description="分辨率，可选", alias="resolution")

class EditNotebookResp(BaseModel):
    """编辑笔记本响应数据"""
    pass

class DeleteNotebookReq(BaseModel):
    """删除笔记本请求参数"""
    id: int = Field(description="笔记本ID", alias="id")

class DeleteNotebookResp(BaseModel):
    """删除笔记本响应数据"""
    pass

class StartNotebookReq(BaseModel):
    """启动笔记本请求参数"""
    id: int = Field(description="笔记本ID", alias="id")

class StartNotebookResp(BaseModel):
    """启动笔记本响应数据"""
    pass

class StopNotebookReq(BaseModel):
    """停止笔记本请求参数"""
    id: int = Field(description="笔记本ID", alias="id")

class StopNotebookResp(BaseModel):
    """停止笔记本响应数据"""
    pass

class DefaultParams(BaseModel):
    """默认参数配置"""
    image: Image = Field(description="镜像信息")
    sku_cnt: int = Field(description="SKU数量", alias="sku_cnt")
    storages: List[Storage] = Field(description="存储列表", alias="storages")

class GetConfigsReq(BaseModel):
    """获取配置请求参数"""
    pass

class GetConfigsResp(BaseModel):
    """获取配置响应数据"""
    cpu_notebook_default_params: DefaultParams = Field(description="CPU笔记本默认参数", alias="cpu_notebook_default_params")
    gpu_notebook_default_params: DefaultParams = Field(description="GPU笔记本默认参数", alias="gpu_notebook_default_params")
    vnc_svr_default_params: DefaultParams = Field(description="VNC服务器默认参数", alias="vnc_svr_default_params")