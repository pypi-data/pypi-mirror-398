from __future__ import annotations

import os
import sys

import httpx
from loguru import logger

from .exceptions import APIError
from .services import artifact
from .services import data_warehouse
from .services import dataset_management
from .services import document_center
from .services import eval
from .services import labelfree
from .services import model_center
from .services import model_deployment
from .services import model_training_platform
from .services import notebook_management
from .services import quota_schedule_management
from .services import tag_resource_management
from .services import task_center
from .services import user_system
from .services import workflow_center
from .services.artifact import ArtifactService
from .services.data_warehouse import DataWarehouseService
from .services.dataset_management import DatasetManagementService
from .services.document_center import DocumentCenterService
from .services.eval import EvalService
from .services.labelfree import LabelfreeService
from .services.model_center import ModelCenterService
from .services.model_deployment import ModelDeploymentService
from .services.model_training_platform import ModelTrainingPlatformService
from .services.notebook_management import NotebookManagementService
from .services.quota_schedule_management import QuotaScheduleManagementService
from .services.tag_resource_management import TagResourceManagementService
from .services.task_center import TaskCenterService
from .services.user_system import UserSystemService
from .services.workflow_center import WorkflowCenterService


class Client:
    """AI-HUB python SDK 客户端

    Attributes:
        artifact (ArtifactService): 制品管理服务
        data_warehouse (DataWarehouseService): 数据仓库服务
        dataset_management (DatasetManagementService): 数据集管理服务
        document_center (DocumentCenterService): 文档中心服务
        eval (EvalService): 评测服务
        labelfree (LabelfreeService): 标注服务
        model_center (ModelCenterService): 模型中心服务
        model_deployment (ModelDeploymentService): 模型部署服务
        model_training_platform (ModelTrainingPlatformService): 模型训练服务
        quota_schedule_management (QuotaScheduleManagementService): 配额调度服务
        tag_resource_management (TagResourceManagementService): 标签管理服务
        task_center (TaskCenterService): 任务中心服务
        workflow_center (WorkflowCenterService): 工作流服务
    """

    artifact: ArtifactService = None
    data_warehouse: DataWarehouseService = None
    dataset_management: DatasetManagementService = None
    document_center: DocumentCenterService = None
    eval: EvalService = None
    labelfree: LabelfreeService = None
    model_center: ModelCenterService = None
    model_deployment: ModelDeploymentService = None
    model_training_platform: ModelTrainingPlatformService = None
    quota_schedule_management: QuotaScheduleManagementService = None
    tag_resource_management: TagResourceManagementService = None
    task_center: TaskCenterService = None
    user_system: UserSystemService = None
    workflow_center: WorkflowCenterService = None
    notebook_management: NotebookManagementService = None

    def __init__(
        self,
        *,
        base_url: str,
        token: str | None = None,
        timeout: float = 60.0,
        log_level: str = "INFO",
    ):
        """AI-HUB python SDK 客户端

        Args:
            base_url (str): 服务地址
            token (str): 密钥，显式传入，或在环境变量AI_HUB_TOKEN中设置

        Examples:
            >>> from aihub.client import Client
            >>> client = Client(base_url="xxx", token="xxxx")

        """
        logger.remove()
        log_format_detailed = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<yellow>{process.id}</yellow>:<yellow>{thread.id}</yellow> | "  # 添加进程和线程ID
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        )
        logger.add(
            sys.stdout,
            colorize=True,
            format=log_format_detailed,
            level=log_level,
        )
        logger.info(f"AI-HUB Python SDK initialized with log level: {log_level}")

        if not base_url:
            raise ValueError("base_url必须填写")

        token = os.getenv("AI_HUB_TOKEN") or token
        if not token:
            raise ValueError("缺少token：请显式传入，或在环境变量AI_HUB_TOKEN中设置")

        self._http = httpx.Client(
            base_url=base_url.rstrip("/"),
            timeout=timeout,
            headers={"Authorization": f"Bearer {token}", "User-Agent": "aihub_sdk"},
            event_hooks={"response": [self._raise_for_status]},
        )
        self.artifact = artifact.ArtifactService(self._http)
        self.data_warehouse = data_warehouse.DataWarehouseService(self._http)
        self.dataset_management = dataset_management.DatasetManagementService(self._http)
        self.document_center = document_center.DocumentCenterService(self._http)
        self.eval = eval.EvalService(self._http)
        self.labelfree = labelfree.LabelfreeService(self._http)
        self.model_center = model_center.ModelCenterService(self._http)
        self.model_deployment = model_deployment.ModelDeploymentService(self._http)
        self.model_training_platform = model_training_platform.ModelTrainingPlatformService(self._http)
        self.quota_schedule_management = quota_schedule_management.QuotaScheduleManagementService(self._http)
        self.tag_resource_management = tag_resource_management.TagResourceManagementService(self._http)
        self.task_center = task_center.TaskCenterService(self._http)
        self.user_system = user_system.UserSystemService(self._http)
        self.workflow_center = workflow_center.WorkflowCenterService(self._http)
        self.notebook_management = notebook_management.NotebookManagementService(self._http)

    @staticmethod
    def _raise_for_status(r: httpx.Response):
        try:
            r.raise_for_status()
        except httpx.HTTPStatusError as e:
            # 在访问 .text 之前，先读取响应内容
            e.response.read()
            raise APIError.from_response(e.response) from e

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self._http.close()
