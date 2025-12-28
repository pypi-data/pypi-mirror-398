# !/usr/bin/env python
# -*- coding:utf-8 -*-
"""文档中心服务模块

本模块围绕 **“文档检索”** 提供以下能力：

- **分页查询文档列表**
"""

from __future__ import annotations

from typing import List

import httpx
from loguru import logger
from pydantic import ValidationError

from ..exceptions import APIError, convert_errors
from ..models.common import APIWrapper
from ..models.document_center import Document, GetDocumentsResponse

_BASE = "/document-center/api/v1"


class DocumentCenterService:
    """文档中心服务封装"""

    def __init__(self, http: httpx.Client):
        self._document = _Document(http)

    def get_documents(self, page_size: int = 9999, page_num: int = 1, name: str = "") -> List[Document]:
        """分页查询文档

        Args:
            page_size: 每页条数，默认 9999
            page_num: 当前页码，默认第 1 页
            name: 按名字过滤，默认为空

        Returns:
            List[Document]: 文档对象列表
        """
        return self._document.get_documents(page_size, page_num, name)

    @property
    def document(self) -> _Document:
        return self._document


class _Document:
    def __init__(self, http: httpx.Client):
        self._http = http

    def get_documents(self, page_size: int = 9999, page_num: int = 1, name: str = "") -> List[Document]:
        params = {"page_size": page_size, "page_num": page_num, "name": name}
        resp = self._http.get(f"{_BASE}/documents", params=params)
        if resp.status_code != 200:
            raise APIError(f"backend code {resp.status_code}: {resp.text}")
        try:
            res = resp.json()
            wrapper = APIWrapper[GetDocumentsResponse].model_validate(res)
            if wrapper.code != 0:
                logger.error(f"backend code {wrapper.code}: {wrapper.msg}")
                raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
            return wrapper.data.data
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise e
