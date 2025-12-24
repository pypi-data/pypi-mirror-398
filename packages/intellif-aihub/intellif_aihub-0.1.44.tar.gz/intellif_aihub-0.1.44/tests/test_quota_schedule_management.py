from __future__ import annotations

import unittest
import uuid
from time import sleep

from src.aihub.client import Client
from src.aihub.models.quota_schedule_management import *

BASE_URL = "http://192.168.13.160:30021"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjQ5MDY2ODUwODAsImlhdCI6MTc1MzA4NTA4MCwidWlkIjoxMH0.89bQ66BJDGoCzwxuxugRRt9acPFKEVmgqXMZX7ApnhM"


class TestQuotaScheduleManagement(unittest.TestCase):
    def test_task(self) -> None:
        client = Client(base_url=BASE_URL, token=TOKEN)

        name = f"sdk_test_task_{uuid.uuid4().hex[:6]}"
        task_id = client.quota_schedule_management.create_task(
            CreateTaskRequest(
                priority=2,
                framework="PyTorchJob",
                name=name,
                description="SDK 单测创建",
                command="echo 1234; sleep 10m",
                image="ubuntu:latest",
                virtual_cluster_id=239,
                sku_cnt=1,
                instances=1,
                category_id=3,
                project_id=2,
                always_pull_image=True,
                enable_ssh=False,
                estimate_run_time=86400,
                use_ib_network=False,
            )
        )
        self.assertGreater(task_id, 0)

        lst_req = ListTasksRequest(name=name)
        tasks = client.quota_schedule_management.list_tasks(lst_req)
        self.assertTrue(any(t.id == task_id for t in tasks.data))

        detail = client.quota_schedule_management.get_task(task_id)
        self.assertEqual(detail.name, name)

        # 调度器调度等待
        sleep(10)

        pods_resp = client.quota_schedule_management.list_task_pods(
            task_id,
            ListTaskPodsRequest(page_size=20, page_num=1))
        self.assertIsNotNone(pods_resp.data)

        if pods_resp.data:
            pod_id = pods_resp.data[0].id

            pod_detail = client.quota_schedule_management.get_task_pod(task_id, pod_id)
            self.assertEqual(pod_detail.id, pod_id)

            logs_new = client.quota_schedule_management.get_pod_logs_new(task_id, pod_id)
            self.assertIsInstance(logs_new, list)

            spec = client.quota_schedule_management.get_pod_spec(task_id, pod_id)
            self.assertTrue(spec)

            events = client.quota_schedule_management.get_pod_events(task_id, pod_id)
            self.assertIsInstance(events, str)

        client.quota_schedule_management.stop_task(task_id)

        users = client.quota_schedule_management.list_task_users(ListTaskUsersRequest())
        self.assertIsInstance(users.data, list)

        metrics = client.quota_schedule_management.get_metrics_overview(GetMetricsOverviewRequest())
        self.assertGreater(metrics.total, 0)
