from __future__ import annotations

import time
import unittest
import uuid

from src.aihub.client import Client
from src.aihub.models.model_center import *

BASE_URL = "http://192.168.13.160:30021"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NjYxMzU1NTksImlhdCI6MTc2NTUzMDc1OSwidWlkIjoyfQ.ejnQq7ejjfMMJg5Ar7ulfaST0VIPWZsCVkJF-fYKuk4"


class TestModelCenter(unittest.TestCase):
    def test_crud_model(self) -> None:
        client = Client(base_url=BASE_URL, token=TOKEN)

        name = f"sdk_test_{uuid.uuid4().hex[:6]}"
        model_id = client.model_center.create_model(
            CreateModelRequest(
                name=name,
                description="SDK 单测创建334",
                is_public=True,
            )
        )
        self.assertGreater(model_id, 0)

        list_models = client.model_center.list_models(ListModelsRequest(page_size=20, page_num=1, name=name))
        self.assertTrue(any(m.id == model_id for m in list_models.data))

        new_name = f"{name}_upd"
        client.model_center.edit_model(
            model_id=model_id,
            payload=EditModelRequest(name=new_name, description="SDK 单测修改", is_public=False),
        )

        model_db = client.model_center.get_model_db(id=model_id)
        self.assertTrue(model_db.name == new_name)

        client.model_center.delete_model(model_id=model_id)

    def test_get_model_db(self) -> None:
        client = Client(base_url=BASE_URL, token=TOKEN)
        model_id = 91222
        model_db = client.model_center.get_model_db(id=model_id)
        print(model_db.file_storage_path)

    def test_get_infer_service(self) -> None:
        client = Client(base_url=BASE_URL, token=TOKEN)
        s_id = 1
        infer_service = client.model_center.get_infer_service_by_id(s_id)
        print(infer_service.endpoint_url)
        
    def test_create_model(self) -> None:
        client = Client(base_url=BASE_URL, token=TOKEN)
        model_id = client.model_center.create(
            name= "sdk_test_model",
            description="SDK 创建模型测试",
            is_public=True,
            data_format= DataFormat.BF16,


        )
        print(model_id)

    def test_upload_and_download(self) -> None:
        client = Client(base_url=BASE_URL, token=TOKEN)
        local_dir = r"D:\git_project4\aihub_sdk\tests\data"
        local_download_dir = r"D:\git_project4\aihub_sdk\tests\data2"

        model_id = 0
        try:
            name = f"sdk_upload_{uuid.uuid4().hex[:6]}"
            model_id = client.model_center.create_model(
                CreateModelRequest(
                    name=name,
                    description="SDK 上传和下载测试",
                    is_public=True,
                )
            )
            self.assertGreater(model_id, 0)
            time.sleep(3)

            client.model_center.upload("23123", local_dir=local_dir)

            attempts = 0
            while True:
                db = client.model_center.get_model_db(id=model_id)
                status = (db.status or "").lower()
                pqt_ok = bool((db.parquet_index_path or "").strip())
                if status == "ready" and pqt_ok:
                    break

                attempts += 1
                if attempts >= 60:
                    self.fail(
                        f"轮询次数达到上限（10次），仍未就绪："
                        f"status={db.status!r}, parquet_index_path={db.parquet_index_path!r}"
                    )
                time.sleep(10)

            client.model_center.download(local_dir=local_download_dir, model_id=model_id)
        finally:
            if model_id:
                try:
                    client.model_center.delete_model(model_id)
                except Exception as e:
                    print(f"删除模型失败 id={model_id}: {e}")
