# !/usr/bin/env python
# -*- coding:utf-8 -*-
"""评测平台服务模块

本模块围绕 **"模型评测（Run → Report）"** 提供能力：

- **创建评测任务 / 评测报告**
- **获取评测任务列表**
"""
import os
import uuid
from typing import List, Dict, Any, Optional

import httpx
from loguru import logger
from pydantic import ValidationError

from .model_center import ModelCenterService
from ..exceptions import APIError, convert_errors
from ..models.common import APIWrapper
from ..models.eval import (
    CreateLLMEvalReq,
    CreateCVEvalReq,
    CreateReidEvalReq,
    CreateEvalResp,
    ListEvalReq,
    ListEvalResp,
    GrantPermissionReq,
    ClientType,
    ReidConfig,
    MetricsArtifact,
    CreatePerformanceEvalReq,
    # V2 API models
    CreateEvalRunV2Req,
    CreateEvalRunV2Resp,
    EvalRunDatasetReportV2,
    ReidConfigV2,
    PerformanceMetric,
    OverallMetrics,
)

_BASE = "/eval-platform/api/v1"
_BASE_V2 = "/eval-platform/api/v2"


class EvalService:
    """评测服务"""

    def __init__(self, http: httpx.Client):
        self._http = http
        self._eval = _Eval(http)

    def create(
        self,
        dataset_version_name: str,
        prediction_artifact_path: str,
        evaled_artifact_path: str,
        report_json: Dict[str, Any],
        run_id,
        user_id: int = 0,
        is_public: bool = True,
        access_user_ids: List[int] = None,
    ) -> int:
        """创建评测报告

        Args:
            is_public (bool): 是否公开
            run_id (str): RUN ID
            report_json (dict): 报告内容
            evaled_artifact_path:   评测结果制品路径
            prediction_artifact_path: 推理结果制品路径
            dataset_version_name (str): 数据集名称
            user_id (int, optional): 用户ID，默认为0
            access_user_ids (list): 授权访问的用户id

        Returns:
            id (int): 评测报告id

        """
        from .dataset_management import DatasetManagementService

        dataset_service = DatasetManagementService(self._http)
        dataset_version = dataset_service.get_dataset_version_by_name(dataset_version_name)
        payload = CreateLLMEvalReq(
            dataset_id=dataset_version.dataset_id,
            dataset_version_id=dataset_version.id,
            evaled_artifact_path=evaled_artifact_path,
            prediction_artifact_path=prediction_artifact_path,
            report=report_json,
            run_id=run_id,
            user_id=user_id,
            is_public=is_public,
            type="llm",
            client_type=ClientType.Workflow,
        )
        resp = self._eval.create(payload)
        if is_public is False and access_user_ids:
            self.grant_permission(user_ids=access_user_ids, run_id=resp)

        return resp

    def create_cv_run(
        self,
        run_id: str,
        prediction_artifact_path: str,
        metrics_artifact_path: str,
        ground_truth_artifact_path: str,
        user_id: int = 0,
        is_public: bool = True,
        access_user_ids: List[int] = None,
    ) -> int:
        """创建 CV 类型评测运行

        Args:
            access_user_ids: 授权访问的用户ID
            is_public (bool): 是否公开
            run_id (str): 运行ID
            prediction_artifact_path (str): 推理产物的路径
            metrics_artifact_path (str): 指标产物的路径
            ground_truth_artifact_path (str): 真实标签产物的路径
            user_id (int, optional): 用户ID，默认为0
            access_user_ids (list): 授权访问的用户id

        Returns:
            id (int): 评测运行id
        """
        payload = CreateCVEvalReq(
            run_id=run_id,
            prediction_artifact_path=prediction_artifact_path,
            metrics_artifact_path=metrics_artifact_path,
            ground_truth_artifact_path=ground_truth_artifact_path,
            user_id=user_id,
            is_public=is_public,
            type="cv",
            client_type=ClientType.Workflow,
        )
        resp = self._eval.create(payload)
        if is_public is False and access_user_ids:
            self.grant_permission(user_ids=access_user_ids, run_id=resp)

        return resp

    def create_performance_run(
        self,
        eval_name: str,
        benchmark_artifact_path: str,
        model_name: str,
        infer_service_id: int,
        benchmark_report: list[Dict[str, Any]],
        eval_config: Dict[str, Any],
        is_public: bool = True,
        run_id: Optional[str] = None,
        access_user_ids: List[int] = None,
    ) -> int:
        """创建性能评测运行

        Args:
            access_user_ids: 授权访问的用户ID
            is_public (bool): 是否公开
            run_id (str): 运行ID
            model_name (str): 模型名称
            benchmark_artifact_path (str): 性能评测产物的路径
            infer_service_id (int): 推理服务ID
            benchmark_report (list[dict]): 性能评测结果
            eval_config (dict): 评测配置
            access_user_ids: List[int] : 授权用户

        """
        if not run_id:
            run_id = os.getenv("AI_HUB_WORKFLOW_RUN_ID", uuid.uuid4().hex)

        model_service = ModelCenterService(self._http)
        model_item = model_service.get_model_db(name=model_name)

        payload = CreatePerformanceEvalReq(
            name=eval_name,
            run_id=run_id,
            performance_artifact_path=benchmark_artifact_path,
            is_public=is_public,
            model_id=model_item.id,
            report={"performance": benchmark_report},
            eval_config=eval_config,
            type="performance",
            client_type=ClientType.Workflow,
            infer_service_id=infer_service_id,
        )
        resp = self._eval.create(payload)
        if is_public is False and access_user_ids:
            self.grant_permission(user_ids=access_user_ids, run_id=resp)

        return resp

    def create_reid_run(
        self,
        run_id: str,
        model_id: int,
        prediction_artifact_path: str,
        gallery_dataset_id: int,
        gallery_dataset_version_id: int,
        query_dataset_id: int,
        query_dataset_version_id: int,
        id_dataset_id: int,
        id_dataset_version_id: int,
        metrics_viz_artifacts: List[MetricsArtifact],
        search_result_artifact_path: str,
        metrics_artifact_path: str,
        user_id: int = 0,
        is_public: bool = True,
        access_user_ids: List[int] = None,
    ) -> int:
        """创建 ReID 类型评测运行

        Args:
            run_id (str): 运行ID
            model_id (int): 模型ID
            prediction_artifact_path (str): 推理产物的路径
            gallery_dataset_id (int): 底库数据集ID
            gallery_dataset_version_id (int): 底库数据集版本ID
            query_dataset_id (int): 查询数据集ID
            query_dataset_version_id (int): 查询数据集版本ID
            id_dataset_id (int): ID数据集ID
            id_dataset_version_id (int): ID数据集版本ID
            metrics_viz_artifacts (List[MetricsArtifact]): 指标可视化产物列表
            search_result_artifact_path (str): 搜索结果产物路径
            metrics_artifact_path (str): 指标产物路径
            user_id (int, optional): 用户ID，默认为0
            is_public (bool): 是否公开
            access_user_ids (list): 授权访问的用户id

        Returns:
            id (int): 评测运行id
        """
        reid_config = ReidConfig(
            gallery_dataset_id=gallery_dataset_id,
            gallery_dataset_version_id=gallery_dataset_version_id,
            query_dataset_id=query_dataset_id,
            query_dataset_version_id=query_dataset_version_id,
            id_dataset_id=id_dataset_id,
            id_dataset_version_id=id_dataset_version_id,
            metrics_viz_artifacts=metrics_viz_artifacts,
            search_result_artifact_path=search_result_artifact_path,
        )

        payload = CreateReidEvalReq(
            run_id=run_id,
            model_id=model_id,
            prediction_artifact_path=prediction_artifact_path,
            reid_config=reid_config,
            metrics_artifact_path=metrics_artifact_path,
            user_id=user_id,
            is_public=is_public,
            type="reid",
            client_type=ClientType.Workflow,
        )
        resp = self._eval.create(payload)
        if is_public is False and access_user_ids:
            self.grant_permission(user_ids=access_user_ids, run_id=resp)

        return resp

    def list(
        self,
        page_size: int = 20,
        page_num: int = 1,
        status: str = None,
        name: str = None,
        model_id: int = None,
        dataset_id: int = None,
        dataset_version_id: int = None,
        run_id: str = None,
        user_id: int = None,
        model_ids: str = None,
        dataset_ids: str = None,
        dataset_version_ids: str = None,
    ) -> ListEvalResp:
        """列出评测结果

        Args:
            page_size (int): 页面大小，默认为20
            page_num (int): 页码，默认为1
            status (str, optional): 状态过滤
            name (str, optional): 名称过滤
            model_id (int, optional): 模型ID过滤
            dataset_id (int, optional): 数据集ID过滤
            dataset_version_id (int, optional): 数据集版本ID过滤
            run_id (str, optional): 运行ID过滤
            user_id (int, optional): 用户ID过滤
            model_ids (str, optional): 模型ID列表过滤（逗号分隔）
            dataset_ids (str, optional): 数据集ID列表过滤（逗号分隔）
            dataset_version_ids (str, optional): 数据集版本ID列表过滤（逗号分隔）

        Returns:
            ListEvalResp: 评测结果列表响应
        """
        payload = ListEvalReq(
            page_size=page_size,
            page_num=page_num,
            status=status,
            name=name,
            model_id=model_id,
            dataset_id=dataset_id,
            dataset_version_id=dataset_version_id,
            run_id=run_id,
            user_id=user_id,
            model_ids=model_ids,
            dataset_ids=dataset_ids,
            dataset_version_ids=dataset_version_ids,
        )

        return self._eval.list(payload)

    def grant_permission(self, user_ids: List[int], run_id: int):
        """授权访问

        Args:
            user_ids (list): 授权信息
            run_id (int): 任务ID

        Returns:
            dict: 授权信息
        """
        req = GrantPermissionReq(
            user_ids=user_ids,
        )
        return self._eval.grant_permission(req, run_id)

    def create_run_v2(
        self,
        run_id: str,
        name: str,
        datasets: List[EvalRunDatasetReportV2],
        eval_type: Optional[str] = None,
        model_id: Optional[int] = None,
        user_id: Optional[int] = None,
        is_public: bool = True,
        eval_config: Optional[Dict[str, Any]] = None,
        arctern_model_group_id: Optional[int] = None,
        arctern_model_name: Optional[str] = None,
        reid_config: Optional[ReidConfigV2] = None,
        performance_artifact_path: Optional[str] = None,
        performance: Optional[List[PerformanceMetric]] = None,
        overall_metrics: Optional[OverallMetrics] = None,
        access_user_ids: Optional[List[int]] = None,
    ) -> int:
        """创建 V2 版本评测运行（支持多数据集）

        Args:
            run_id (str): 运行ID
            name (str): 评测名称
            datasets (List[EvalRunDatasetReportV2]): 数据集报告列表
            eval_type (str, optional): 评测类型: cv, llm, reid, performance
            model_id (int, optional): 模型ID
            user_id (int, optional): 用户ID
            is_public (bool): 是否公开，默认True
            eval_config (dict, optional): 评测配置
            arctern_model_group_id (int, optional): Arctern模型组ID（CV类型）
            arctern_model_name (str, optional): Arctern模型名称（CV类型）
            reid_config (ReidConfigV2, optional): ReID配置（ReID类型）
            performance_artifact_path (str, optional): 性能产物路径（Performance类型）
            performance (List[PerformanceMetric], optional): 性能指标列表（Performance类型）
            overall_metrics (OverallMetrics, optional): 整体指标
            access_user_ids (List[int], optional): 授权访问的用户ID列表

        Returns:
            int: 评测运行ID
        """
        payload = CreateEvalRunV2Req(
            run_id=run_id,
            type=eval_type,
            name=name,
            model_id=model_id,
            user_id=user_id,
            is_public=is_public,
            eval_config=eval_config,
            datasets=datasets,
            arctern_model_group_id=arctern_model_group_id,
            arctern_model_name=arctern_model_name,
            reid_config=reid_config,
            performance_artifact_path=performance_artifact_path,
            performance=performance,
            overall_metrics=overall_metrics,
        )

        resp = self._eval.create_v2(payload)

        if is_public is False and access_user_ids:
            self.grant_permission(user_ids=access_user_ids, run_id=resp)

        return resp


class _Eval:
    def __init__(self, http: httpx.Client):
        self._http = http

    def create(self, payload) -> int:
        try:
            body = payload.model_dump()
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise ValueError
        resp = self._http.post(f"{_BASE}/run/", json=body)

        if resp.status_code != 200:
            raise APIError(f"HTTP {resp.status_code} error. " f"Response: {resp.text[:1000]}")

        if not resp.content:
            raise APIError(f"Empty response from server (HTTP {resp.status_code})")

        try:
            json_data = resp.json()
        except Exception as e:
            raise APIError(
                f"Failed to parse JSON response: {e}. " f"Status: {resp.status_code}, " f"Content: {resp.text[:1000]}"
            )

        try:
            wrapper = APIWrapper[CreateEvalResp].model_validate(json_data)
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise ValueError
        except Exception as e:
            raise APIError(f"Failed to validate response structure: {e}. " f"Response: {json_data}")

        if wrapper.code != 0:
            raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
        return wrapper.data.eval_run.id

    def grant_permission(self, payload, task_id):
        try:
            body = payload.model_dump()
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise ValueError
        resp = self._http.post(f"{_BASE}/run/{task_id}/permissions", json=body)

        if resp.status_code != 200:
            raise APIError(f"HTTP {resp.status_code} error. " f"Response: {resp.text[:1000]}")

        try:
            json_data = resp.json()
        except Exception as e:
            raise APIError(
                f"Failed to parse JSON response: {e}. " f"Status: {resp.status_code}, " f"Content: {resp.text[:1000]}"
            )

        try:
            wrapper = APIWrapper[CreateEvalResp].model_validate(json_data)
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise ValueError
        except Exception as e:
            raise APIError(f"Failed to validate response structure: {e}. " f"Response: {json_data}")

        if wrapper.code != 0:
            raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
        return wrapper.data

    def list(self, payload: ListEvalReq) -> ListEvalResp:
        # Build query parameters, excluding None values
        params = {}
        for field, value in payload.model_dump().items():
            if value is not None:
                params[field] = value

        resp = self._http.get(f"{_BASE}/run/", params=params)

        if resp.status_code != 200:
            logger.error(f"HTTP {resp.status_code} error. " f"Response: {resp.text}")
            raise APIError(f"HTTP {resp.status_code} error. " f"Response: {resp.text[:1000]}")

        try:
            json_data = resp.json()
        except Exception as e:
            raise APIError(
                f"Failed to parse JSON response: {e}. " f"Status: {resp.status_code}, " f"Content: {resp.text[:1000]}"
            )

        try:
            wrapper = APIWrapper[ListEvalResp].model_validate(json_data)
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise ValueError
        except Exception as e:
            raise APIError(f"Failed to validate response structure: {e}. " f"Response: {json_data}")

        if wrapper.code != 0:
            raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
        return wrapper.data

    def create_v2(self, payload: CreateEvalRunV2Req) -> int:
        """创建 V2 评测运行"""
        try:
            request_data = payload.model_dump(exclude_none=True)
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise ValueError

        resp = self._http.post(f"{_BASE_V2}/run/", json=request_data)

        if resp.status_code != 200:
            raise APIError(f"HTTP {resp.status_code} error. " f"Response: {resp.text[:1000]}")

        if not resp.content:
            raise APIError(f"Empty response from server (HTTP {resp.status_code})")

        try:
            json_data = resp.json()
        except Exception as e:
            raise APIError(
                f"Failed to parse JSON response: {e}. " f"Status: {resp.status_code}, " f"Content: {resp.text[:1000]}"
            )

        try:
            wrapper = APIWrapper[CreateEvalRunV2Resp].model_validate(json_data)
        except ValidationError as e:
            logger.error(convert_errors(e))
            raise ValueError
        except Exception as e:
            raise APIError(f"Failed to validate response structure: {e}. " f"Response: {json_data}")

        if wrapper.code != 0:
            raise APIError(f"backend code {wrapper.code}: {wrapper.msg}")
        return wrapper.data.id
