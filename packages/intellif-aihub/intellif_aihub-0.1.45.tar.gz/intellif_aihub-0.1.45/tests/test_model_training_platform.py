from __future__ import annotations

import unittest
import uuid
from time import sleep

from src.aihub.client import Client
from src.aihub.models.model_training_platform import *

BASE_URL = "http://192.168.13.160:30021"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjQ5MDY2ODUwODAsImlhdCI6MTc1MzA4NTA4MCwidWlkIjoxMH0.89bQ66BJDGoCzwxuxugRRt9acPFKEVmgqXMZX7ApnhM"


class TestModelTrainingPlatform(unittest.TestCase):
    def test_training(self) -> None:
        client = Client(base_url=BASE_URL, token=TOKEN)

        name = f"sdk_test_train_{uuid.uuid4().hex[:6]}"
        tid = client.model_training_platform.create_training(
            CreateTrainingRequest(
                framework="PyTorchJob",
                name=name,
                description="SDK 单测创建",
                command="echo 1234; sleep 10m",
                image="ubuntu:latest",
                virtual_cluster_id=289,
                sku_cnt=1,
                instances=1,
                category_id=4,
                project_id=1,
                always_pull_image=True,
                enable_ssh=False,
                estimate_run_time=86400,
                use_ib_network=False,
            )
        )
        self.assertGreater(tid, 0)

        lst_req = ListTrainingsRequest(name=name)
        trainings = client.model_training_platform.list_trainings(lst_req)
        self.assertTrue(any(t.id == tid for t in trainings.data))

        detail = client.model_training_platform.get_training(tid)
        self.assertEqual(detail.name, name)

        # 调度器调度等待
        sleep(10)

        pods_resp = client.model_training_platform.list_training_pods(
            tid,
            ListTrainingPodsRequest(page_size=20, page_num=1))
        self.assertIsNotNone(pods_resp.data)

        if pods_resp.data:
            pod_id = pods_resp.data[0].id

            pod_detail = client.model_training_platform.get_training_pod(tid, pod_id)
            self.assertEqual(pod_detail.id, pod_id)

            logs_new = client.model_training_platform.get_pod_logs_new(tid, pod_id)
            self.assertIsInstance(logs_new.logs, list)

            spec = client.model_training_platform.get_pod_spec(tid, pod_id)
            self.assertTrue(spec.spec)

            events = client.model_training_platform.get_pod_events(tid, pod_id)
            self.assertIsInstance(events.events, str)

        client.model_training_platform.stop_training(tid)

        users = client.model_training_platform.list_training_users(ListTrainingUsersRequest())
        self.assertIsInstance(users.data, list)

        containers = client.model_training_platform.list_training_containers(ListTrainingContainersRequest())
        data = containers.data or []
        self.assertIsInstance(data, list)

        storages = client.model_training_platform.list_storages()
        self.assertIsInstance(storages.data, list)
