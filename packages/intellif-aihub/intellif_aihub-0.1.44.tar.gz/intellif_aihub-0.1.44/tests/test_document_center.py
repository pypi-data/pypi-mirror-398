from __future__ import annotations

import unittest
import unittest.mock as mock

import httpx

from src.aihub.client import Client
from src.aihub.exceptions import APIError
from src.aihub.services import (
    labelfree,
    dataset_management,
    tag_resource_management,
    document_center,
)


class TestDocumentCenter(unittest.TestCase):
    def setUp(self):
        # 创建一个模拟的httpx.Client对象
        self.mock_http = mock.MagicMock()
        self.client = Client(
            base_url="http://192.168.13.160:30021",
            token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NTIwNDgzOTgsImlhdCI6MTc1MTQ0MzU5OCwidWlkIjoxMH0.GqFDpRQuRlNx9YdHlC6zql-8_ZtCpDV4zUFvqM5p7EE",
        )
        # 替换客户端的http对象为模拟对象
        self.client._http = self.mock_http

        self.client.dataset_management = dataset_management.DatasetManagementService(
            self.mock_http
        )
        self.client.labelfree = labelfree.LabelfreeService(self.mock_http)
        self.client.tag_management = tag_resource_management.TagResourceManagementService(self.mock_http)
        self.client.document_center = document_center.DocumentCenterService(
            self.mock_http
        )

    def test_get_documents(self):
        # 准备模拟响应数据
        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 0,
            "msg": "success",
            "data": {
                "total": 2,
                "page_size": 10,
                "page_num": 1,
                "data": [
                    {
                        "id": 1,
                        "title": "测试文档1",
                        "type": 1,
                        "edit_time": 1620000000,
                        "need_update": False,
                        "content": "测试内容1",
                        "username": "test_user",
                        "user_id": 1,
                        "created_at": 1620000000,
                    },
                    {
                        "id": 2,
                        "title": "测试文档2",
                        "type": 1,
                        "edit_time": 1620000000,
                        "need_update": False,
                        "content": "测试内容2",
                        "username": "test_user",
                        "user_id": 1,
                        "created_at": 1620000000,
                    },
                ],
            },
        }
        self.mock_http.get.return_value = mock_response

        # 调用被测试的方法
        documents = self.client.document_center.get_documents(
            page_size=10, page_num=1, name="测试"
        )

        # # 验证http.get被正确调用
        self.mock_http.get.assert_called_once_with(
            "/document-center/api/v1/documents",
            params={"page_size": 10, "page_num": 1, "name": "测试"},
        )

        # 验证返回结果
        self.assertEqual(len(documents), 2)
        self.assertEqual(documents[0].id, 1)
        self.assertEqual(documents[0].title, "测试文档1")
        self.assertEqual(documents[1].id, 2)
        self.assertEqual(documents[1].title, "测试文档2")

    def test_get_documents_by_name(self):
        # 准备模拟响应数据 - 按名称搜索
        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 0,
            "msg": "success",
            "data": {
                "total": 1,
                "page_size": 10,
                "page_num": 1,
                "data": [
                    {
                        "id": 1,
                        "title": "特定文档",
                        "type": 1,
                        "edit_time": 1620000000,
                        "need_update": False,
                        "content": "特定内容",
                        "username": "test_user",
                        "user_id": 1,
                        "created_at": 1620000000,
                    }
                ],
            },
        }
        self.mock_http.get.return_value = mock_response

        # 调用被测试的方法 - 按名称搜索
        documents = self.client.document_center.get_documents(name="特定")

        # 验证http.get被正确调用
        self.mock_http.get.assert_called_once_with(
            "/document-center/api/v1/documents",
            params={"page_size": 9999, "page_num": 1, "name": "特定"},
        )

        # 验证返回结果
        self.assertEqual(len(documents), 1)
        self.assertEqual(documents[0].id, 1)
        self.assertEqual(documents[0].title, "特定文档")

    def test_get_documents_with_error(self):
        # 准备模拟响应数据 - 错误情况
        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 1,
            "msg": "error message",
            "data": None,
        }
        self.mock_http.get.return_value = mock_response

        # 验证抛出异常
        with self.assertRaises(APIError) as context:
            self.client.document_center.get_documents()

        # 验证异常信息
        self.assertIn("backend code 1: error message", str(context.exception))

    def test_get_documents_with_http_error(self):
        # 模拟HTTP错误
        self.mock_http.get.side_effect = httpx.HTTPStatusError(
            "404 Not Found",
            request=mock.MagicMock(),
            response=mock.MagicMock(status_code=404),
        )

        # 验证抛出异常
        with self.assertRaises(APIError) as context:
            self.client.document_center.get_documents()

        # 验证异常信息
        self.assertIn("404", str(context.exception))

    def test_integration_get_documents(self):
        """集成测试 - 获取文档列表

        注意：此测试需要实际的API环境，默认被注释掉。
        要运行此测试，请取消注释并提供有效的base_url和token。
        """
        # client = Client(
        #     base_url="http://your-api-base-url",
        #     token="your-token"
        # )
        #
        # # 获取所有文档
        # documents = client.document_center.get_documents()
        # print(f"\n✓ 获取到 {len(documents)} 个文档")
        #
        # if documents:
        #     print(f"第一个文档标题: {documents[0].title}")
        #
        #     # 按名称搜索文档
        #     search_term = documents[0].title[:5]  # 使用第一个文档标题的前5个字符作为搜索词
        #     filtered_docs = client.document_center.get_documents(name=search_term)
        #     print(f"搜索 '{search_term}' 找到 {len(filtered_docs)} 个文档")
        #
        #     # 测试分页
        #     paged_docs = client.document_center.get_documents(page_size=1, page_num=1)
        #     print(f"分页获取第1页(每页1条)找到 {len(paged_docs)} 个文档")
        pass


if __name__ == "__main__":
    unittest.main()
