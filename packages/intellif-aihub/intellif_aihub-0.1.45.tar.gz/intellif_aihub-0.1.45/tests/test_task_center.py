# !/usr/bin/env python
# -*-coding:utf-8 -*-


from __future__ import annotations

import unittest

BASE_URL = "http://192.168.13.160:30021"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjQ5MDY2ODUwODAsImlhdCI6MTc1MzA4NTA4MCwidWlkIjoxMH0.89bQ66BJDGoCzwxuxugRRt9acPFKEVmgqXMZX7ApnhM"


class TestTaskCenter(unittest.TestCase):
    def test_create_label_task(self):
        from src.aihub.models.task_center import LabelProjectTypeEnum, LabelValidateStage
        from src.aihub.client import Client
        from src.aihub.models.task_center import TaskCenterPriorityEnum
        from src.aihub.models.labelfree import LabelProjectStatus
        import time

        # 创建任务
        client = Client(base_url=BASE_URL, token=TOKEN)
        task_id = client.task_center.create_label_task(
            name="test_tas2k232",
            dataset_version_name="re/V1",
            feishu_doc_name="人脸质量人脸照片分类",
            task_receiver_name="hyc",
            project_name="hycpro",
            label_type=LabelProjectTypeEnum.IMAGE_CLASSIFICATION,
            description="test_description",
            task_priority=TaskCenterPriorityEnum.low,
            estimated_delivery_at="2025-08-01",
        )
        # 等待任务完成
        while True:
            # 获取任务信息
            task_item = client.task_center.get(task_id)
            # 使用sdkl
            if not task_item.other_info.label_projects:
                print("任务未完成，请稍后...")
                time.sleep(5)
                continue
            p = task_item.other_info.label_projects[0]
            label_stats = client.labelfree.get_project_global_stats(p.label_project_name)
            # 等待标注完成、完成100%验收、存在数据导出
            if label_stats.status == LabelProjectStatus.Finished and label_stats.data_exported_count != 0:
                exported_dataset_name = label_stats.exported_dataset_name
                client.task_center.validate_label_project(
                    task_id, p.label_project_name, LabelValidateStage.LABEL_FINISHED, True
                )

                break
            else:
                print("任务未完成，请稍后...")
                time.sleep(5)
                continue

        # 下载数据
        client.dataset_management.run_download(exported_dataset_name, local_dir="./output")
        # 结束

    def test_validate_label_project(self):
        from src.aihub.client import Client
        from src.aihub.models.task_center import LabelValidateStage

        client = Client(base_url=BASE_URL, token=TOKEN)
        client.task_center.validate_label_project(1923, "project_893437", LabelValidateStage.LABEL_FINISHED, True)

    def test_get_label_project(self):
        from src.aihub.client import Client

        client = Client(base_url=BASE_URL, token=TOKEN)
        client.labelfree.get_project_global_stats("project_889552")

    def test_get_task(self):
        from src.aihub.client import Client

        client = Client(base_url=BASE_URL, token=TOKEN)
        task = client.task_center.get(2034)
        print(task)
