# !/usr/bin/env python
# -*-coding:utf-8 -*-


import unittest
from unittest.mock import patch, MagicMock

# 假设 main 函数在 di.py 中
from aihub.utils.di import main, SimpleS3Client, DataUploader


class TestMainFunction(unittest.TestCase):

    @patch("aihub.utils.di.argparse.ArgumentParser.parse_args")
    @patch("aihub.utils.di.os.path.exists")
    @patch("aihub.utils.di.SimpleS3Client")
    @patch("aihub.utils.di.DataUploader")
    @patch("aihub.utils.di.logger")
    @patch("aihub.utils.di.sys.exit")
    def test_main_success(
        self, mock_exit, mock_logger, mock_uploader_class, mock_s3_client_class, mock_exists, mock_parse_args
    ):
        """
        测试正常流程：所有参数合法，路径存在，上传成功
        """
        mock_args = MagicMock()
        mock_args.local = "./data"
        mock_args.endpoint = "192.168.14.17:9000"
        mock_args.access_key = "root"
        mock_args.secret_key = "rootroot"
        mock_args.target = "s3://testbucket/test_ok11"
        mock_args.object_sheet = "s3://testbucket/records/123.csv"
        mock_args.status = "s3://testbucket/status/123.json"
        mock_args.task_id = 123
        mock_args.num_workers = 10

        mock_parse_args.return_value = mock_args
        mock_exists.return_value = True

        # 模拟 run 不抛异常
        mock_uploader_instance = MagicMock()
        mock_uploader_class.return_value = mock_uploader_instance

        main()

        # 验证调用顺序
        mock_s3_client_class.assert_called_once_with(mock_args.endpoint, mock_args.access_key, mock_args.secret_key)
        mock_uploader_class.assert_called_once_with(
            task_id=mock_args.task_id,
            local_path=mock_args.local,
            s3_target=mock_args.target,
            csv_path=mock_args.object_sheet,
            status_path=mock_args.status,
            num_workers=mock_args.num_workers,
        )
        mock_uploader_instance.run.assert_called_once()
        mock_logger.info.assert_any_call("Upload completed successfully")
        mock_exit.assert_not_called()

    @patch("aihub.utils.di.argparse.ArgumentParser.parse_args")
    @patch("aihub.utils.di.os.path.exists")
    @patch("aihub.utils.di.logger")
    @patch("aihub.utils.di.sys.exit")
    def test_main_local_path_not_exist(self, mock_exit, mock_logger, mock_exists, mock_parse_args):
        """
        测试本地路径不存在的情况
        """
        mock_args = MagicMock()
        mock_args.local = "./non_exist_path"
        mock_parse_args.return_value = mock_args
        mock_exists.return_value = False

        main()

        mock_logger.error.assert_called_with(f"Local path does not exist: {mock_args.local}")
        mock_exit.assert_called_once_with(1)

    @patch("aihub.utils.di.argparse.ArgumentParser.parse_args")
    @patch("aihub.utils.di.os.path.exists")
    @patch("aihub.utils.di.SimpleS3Client")
    @patch("aihub.utils.di.logger")
    @patch("aihub.utils.di.sys.exit")
    def test_main_s3_client_init_fail(self, mock_exit, mock_logger, mock_s3_client_class, mock_exists, mock_parse_args):
        """
        测试 S3 客户端初始化失败
        """
        mock_args = MagicMock()
        mock_args.local = "./test_data"
        mock_parse_args.return_value = mock_args
        mock_exists.return_value = True
        mock_s3_client_class.side_effect = Exception("S3 init error")

        main()

        mock_logger.error.assert_called_with("Upload failed: S3 init error")
        mock_exit.assert_called_once_with(1)

    @patch("aihub.utils.di.argparse.ArgumentParser.parse_args")
    @patch("aihub.utils.di.os.path.exists")
    @patch("aihub.utils.di.SimpleS3Client")
    @patch("aihub.utils.di.DataUploader")
    @patch("aihub.utils.di.logger")
    @patch("aihub.utils.di.sys.exit")
    def test_main_uploader_run_fail(
        self, mock_exit, mock_logger, mock_uploader_class, mock_s3_client_class, mock_exists, mock_parse_args
    ):
        """
        测试 DataUploader.run 抛异常
        """
        mock_args = MagicMock()
        mock_args.local = "./test_data"
        mock_parse_args.return_value = mock_args
        mock_exists.return_value = True

        mock_uploader_instance = MagicMock()
        mock_uploader_instance.run.side_effect = Exception("Upload error")
        mock_uploader_class.return_value = mock_uploader_instance

        main()

        mock_logger.error.assert_called_with("Upload failed: Upload error")
        mock_exit.assert_called_once_with(1)

    def test_main(self):
        # mock_args.local = "./data"
        # mock_args.endpoint = "192.168.14.17:9000"
        # mock_args.access_key = "root"
        # mock_args.secret_key = "rootroot"
        # mock_args.target = "s3://testbucket/test_ok11"
        # mock_args.object_sheet = "s3://testbucket/records/123.csv"
        # mock_args.status = "s3://testbucket/status/123.json"
        # mock_args.task_id = 123
        # mock_args.num_workers = 10
        endpoint = "192.168.14.17:9000"
        access_key = "root"
        secret_key = "rootroot"
        local = "./data"
        target = "s3://test-data/test_ok11"
        object_sheet = "s3://test-data/records/123.csv"
        status = "s3://test-data/status/123.json"
        task_id = 123
        num_workers = 10

        s3_client = SimpleS3Client(endpoint, access_key, secret_key)

        # 创建上传器并执行
        uploader = DataUploader(
            task_id=task_id,
            local_path=local,
            s3_target=target,
            csv_path=object_sheet,
            status_path=status,
            num_workers=num_workers,
        )

        uploader.run(s3_client)


if __name__ == "__main__":
    unittest.main()
