# !/usr/bin/env python
# -*-coding:utf-8 -*-
"""我的应用模块（原我的Notebook）

封装 **notebook_management** 相关接口，核心能力包括：

- **查询我的应用卡片** - 支持根据应用类型和硬件类型查询应用卡片
- **查询我的应用详情** - 支持根据应用卡片ID查询应用详情
- **获取应用默认启动配置** - 支持获取各种应用的默认启动配置
- **启动我的应用** - 支持根据应用卡片ID启动应用
- **停止我的应用** - 支持根据应用卡片ID停止应用

"""

from __future__ import annotations

import httpx
from loguru import logger
from pydantic import ValidationError

from ..exceptions import APIError, convert_errors
from ..models.common import APIWrapper
from ..models.notebook_management import (
    ListImagesReq,
    ListImagesResp,
    ListNotebooksReq,
    ListNotebooksResp,
    GetNotebookReq,
    Notebook,
    CreateNotebookReq,
    CreateNotebookResp,
    EditNotebookReq,
    EditNotebookResp,
    DeleteNotebookReq,
    DeleteNotebookResp,
    StartNotebookReq,
    StartNotebookResp,
    StopNotebookReq,
    StopNotebookResp,
    GetConfigsReq,
    GetConfigsResp,
)

_BASE = "/notebook-management/api/v1"


class NotebookManagementService:
    """我的应用管理服务"""

    def __init__(self, http: httpx.Client):
        self._image_service = _ImageService(http)
        self._notebook_service = _NotebookService(http)

    @property
    def image_service(self) -> _ImageService:
        return self._image_service

    @property
    def notebook_service(self) -> _NotebookService:
        return self._notebook_service

    def list_images(self, payload: ListImagesReq) -> ListImagesResp:
        """获取镜像列表

        Returns:
            list[Image]: 镜像列表
        """
        return self._image_service.list_images(payload)

    def list_notebooks(self, payload: ListNotebooksReq) -> ListNotebooksResp:
        """列出笔记本实例

        Args:
            payload (ListNotebooksReq): 列出笔记本实例请求

        Returns:
            ListNotebooksResp: 列出笔记本实例响应
        """
        return self._notebook_service.list_notebooks(payload)

    def get_notebook(self, payload: GetNotebookReq) -> Notebook:
        """获取笔记本详情

        Args:
            payload (GetNotebookReq): 获取笔记本详情请求

        Returns:
            Notebook: 笔记本详情
        """
        return self._notebook_service.get_notebook(payload)

    def create_notebook(self, payload: CreateNotebookReq) -> CreateNotebookResp:
        """创建笔记本实例

        Args:
            payload (CreateNotebookReq): 创建笔记本实例请求

        Returns:
            CreateNotebookResp: 创建笔记本实例响应
        """
        return self._notebook_service.create_notebook(payload)

    def edit_notebook(self, payload: EditNotebookReq) -> EditNotebookResp:
        """编辑笔记本实例

        Args:
            payload (EditNotebookReq): 编辑笔记本实例请求

        Returns:
            EditNotebookResp: 编辑笔记本实例响应
        """
        return self._notebook_service.edit_notebook(payload)

    def delete_notebook(self, payload: DeleteNotebookReq) -> DeleteNotebookResp:
        """删除笔记本实例

        Args:
            payload (DeleteNotebookReq): 删除笔记本实例请求

        Returns:
            DeleteNotebookResp: 删除笔记本实例响应
        """
        return self._notebook_service.delete_notebook(payload)

    def start_notebook(self, payload: StartNotebookReq) -> StartNotebookResp:
        """启动笔记本实例

        Args:
            payload (StartNotebookReq): 启动笔记本实例请求

        Returns:
            StartNotebookResp: 启动笔记本实例响应
        """
        return self._notebook_service.start_notebook(payload)

    def stop_notebook(self, payload: StopNotebookReq) -> StopNotebookResp:
        """停止笔记本实例

        Args:
            payload (StopNotebookReq): 停止笔记本实例请求

        Returns:
            StopNotebookResp: 停止笔记本实例响应
        """
        return self._notebook_service.stop_notebook(payload)

    def get_configs(self, payload: GetConfigsReq) -> GetConfigsResp:
        """获取应用默认启动配置

        Args:
            payload (GetConfigsReq): 获取应用默认启动配置请求

        Returns:
            GetConfigsResp: 获取应用默认启动配置响应
        """
        return self._notebook_service.get_configs(payload)


class _ImageService:
    def __init__(self, http: httpx.Client):
        self._http = http

    def list_images(self, payload: ListImagesReq) -> ListImagesResp:
        try:
            resp = self._http.get(f"{_BASE}/images", params=payload.model_dump(by_alias=True, exclude_none=True))
            wrapper = APIWrapper[ListImagesResp].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e


class _NotebookService:
    def __init__(self, http: httpx.Client):
        self._http = http

    def list_notebooks(self, payload: ListNotebooksReq) -> ListNotebooksResp:
        """列出笔记本实例"""
        try:
            resp = self._http.get(f"{_BASE}/notebooks", params=payload.model_dump(by_alias=True, exclude_none=True))
            wrapper = APIWrapper[ListNotebooksResp].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def get_notebook(self, payload: GetNotebookReq) -> Notebook:
        """获取笔记本详情"""
        try:
            resp = self._http.get(
                f"{_BASE}/notebooks/{payload.id}", params=payload.model_dump(by_alias=True, exclude_none=True)
            )
            wrapper = APIWrapper[Notebook].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def create_notebook(self, payload: CreateNotebookReq) -> CreateNotebookResp:
        """创建笔记本实例"""
        try:
            resp = self._http.post(f"{_BASE}/notebooks", json=payload.model_dump(by_alias=True, exclude_none=True))
            wrapper = APIWrapper[CreateNotebookResp].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def edit_notebook(self, payload: EditNotebookReq) -> EditNotebookResp:
        """编辑笔记本实例"""
        try:
            resp = self._http.put(
                f"{_BASE}/notebooks/{payload.id}", json=payload.model_dump(by_alias=True, exclude_none=True)
            )
            wrapper = APIWrapper[EditNotebookResp].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def delete_notebook(self, payload: DeleteNotebookReq) -> DeleteNotebookResp:
        """删除笔记本实例"""
        try:
            resp = self._http.delete(
                f"{_BASE}/notebooks/{payload.id}", params=payload.model_dump(by_alias=True, exclude_none=True)
            )
            wrapper = APIWrapper[DeleteNotebookResp].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def start_notebook(self, payload: StartNotebookReq) -> StartNotebookResp:
        """启动笔记本实例"""
        try:
            resp = self._http.post(
                f"{_BASE}/notebooks/{payload.id}/start", json=payload.model_dump(by_alias=True, exclude_none=True)
            )
            wrapper = APIWrapper[StartNotebookResp].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def stop_notebook(self, payload: StopNotebookReq) -> StopNotebookResp:
        """停止笔记本实例"""
        try:
            resp = self._http.post(
                f"{_BASE}/notebooks/{payload.id}/stop", json=payload.model_dump(by_alias=True, exclude_none=True)
            )
            wrapper = APIWrapper[StopNotebookResp].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e

    def get_configs(self, payload: GetConfigsReq) -> GetConfigsResp:
        """获取配置信息"""
        try:
            resp = self._http.get(f"{_BASE}/configs", params=payload.model_dump(by_alias=True, exclude_none=True))
            wrapper = APIWrapper[GetConfigsResp].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e
