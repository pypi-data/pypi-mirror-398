# !/usr/bin/env python
# -*- coding:utf-8 -*-
"""数据仓库服务模块

本模块围绕 **“检索任务”** 提供增查接口，包括：

- **创建检索任务**
- **分页查询检索任务列表**
- **根据检索任务 ID 获取详情**
"""

from __future__ import annotations

import httpx
from loguru import logger
from pydantic import ValidationError

from ..exceptions import APIError, convert_errors
from ..models.common import APIWrapper
from ..models.data_warehouse import (
    ListSearchRequest,
    ListSearchResponse,
    CreateSearchRequest,
    CreateSearchResponse,
    Search,
)

_BASE = "/data-warehouse/api/v1"


class DataWarehouseService:
    """数据仓库服务类"""

    def __init__(self, http: httpx.Client):
        self._search = _Search(http)

    def list_searches(self, payload: ListSearchRequest) -> ListSearchResponse:
        """分页查询检索任务

        Args:
            payload: 查询条件，包含分页信息、名称 / 状态 / 用户过滤条件等

        Returns:
            ListSearchResponse: 分页结果
        """
        return self._search.list(payload)

    def get_search(self, search_id: int) -> Search:
        """根据检索任务ID获取详情

        Args:
            search_id: 检索任务ID

        Returns:
            Search: 检索任务完整信息对象
        """
        return self._search.get(search_id)

    def create_search(self, payload: CreateSearchRequest) -> int:
        """创建检索任务，根据传入的检索类型及参数在后台创建任务，返回任务ID

        Args:
            payload: 创建检索任务请求体。字段含义见 `CreateSearchRequest`

        Returns:
            int: 新建检索任务的ID
        """
        return self._search.create(payload)

    @property
    def search(self) -> _Search:
        return self._search


class _Search:

    def __init__(self, http: httpx.Client):
        self._http = http

    def list(self, payload: ListSearchRequest) -> ListSearchResponse:
        try:
            resp = self._http.get(f"{_BASE}/searches", params=payload.model_dump(by_alias=True, exclude_none=True))
            wrapper = APIWrapper[ListSearchResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise ValueError

    def get(self, search_id: int) -> Search:
        try:
            resp = self._http.get(f"{_BASE}/searches/{search_id}")
            wrapper = APIWrapper[Search].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise ValueError

    def create(self, payload: CreateSearchRequest) -> int:
        try:
            resp = self._http.post(f"{_BASE}/searches", json=payload.model_dump(by_alias=True, exclude_none=True))
            wrapper = APIWrapper[CreateSearchResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data.id
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise ValueError
