# !/usr/bin/env python
# -*- coding:utf-8 -*-
"""标注服务模块

本模块用于对接 **标注平台**，提供以下能力：

- **获取指定项目的整体标注 / 审核完成度等统计信息**
"""

from __future__ import annotations

import httpx
from loguru import logger
from pydantic import ValidationError

from ..exceptions import APIError, convert_errors
from ..models.common import APIWrapper
from ..models.labelfree import GetGlobalStatsResponse

_BASE = "/labelfree/api/v2"


class LabelfreeService:
    """标注服务"""

    def __init__(self, http: httpx.Client):
        self._project = _Project(http)

    def get_project_global_stats(self, project_name: str) -> GetGlobalStatsResponse:
        """获取标注项目的进展信息

        Args:
            project_name: 标注项目名称

        Returns:
            GetGlobalStatsResponse

        """
        return self._project.get_global_stats(project_name)

    @property
    def project(self) -> _Project:
        return self._project


class _Project:
    def __init__(self, http: httpx.Client):
        self._http = http

    def get_global_stats(self, project_name: str) -> GetGlobalStatsResponse:
        try:
            resp = self._http.get(f"{_BASE}/projects/global_stats", params={"project_name": project_name})
            wrapper = APIWrapper[GetGlobalStatsResponse].model_validate(resp.json())
            if wrapper.code != 0:
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e
