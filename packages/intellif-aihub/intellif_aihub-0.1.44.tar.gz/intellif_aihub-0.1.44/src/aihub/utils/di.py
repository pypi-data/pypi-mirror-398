import argparse
import csv
import hashlib
import json
import os
import queue
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, Any, Tuple

import minio
from loguru import logger


class UploadStatus:
    """上传状态类"""

    def __init__(self):
        self.uploaded_count = 0
        self.uploaded_size = 0
        self.updated_at = int(time.time() * 1000)

    def update(self, count: int, size: int):
        self.uploaded_count += count
        self.uploaded_size += size
        self.updated_at = int(time.time() * 1000)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "uploaded_count": self.uploaded_count,
            "uploaded_size": self.uploaded_size,
            "updated_at": self.updated_at,
        }


class SimpleS3Client:
    """简化的S3客户端"""

    def __init__(self, endpoint: str, access_key: str, secret_key: str, session_token: str):
        self.client = minio.Minio(
            endpoint, access_key=access_key, secret_key=secret_key, secure=False, session_token=session_token
        )

    def upload_file(self, local_path: str, bucket: str, object_name: str) -> Tuple[str, int]:
        """上传文件并返回哈希和大小"""
        file_size = os.path.getsize(local_path)

        # 计算文件哈希
        sha256_hash = hashlib.sha256()
        with open(local_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)

        file_hash = sha256_hash.hexdigest()

        # 上传文件
        with open(local_path, "rb") as f:
            self.client.put_object(bucket, object_name, f, file_size)

        return file_hash, file_size

    def upload_json(self, data: Dict[str, Any], bucket: str, object_name: str):
        """上传JSON数据"""
        json_str = json.dumps(data)
        json_bytes = json_str.encode("utf-8")

        from io import BytesIO

        self.client.put_object(
            bucket, object_name, BytesIO(json_bytes), len(json_bytes), content_type="application/json"
        )


class DataUploader:
    """数据上传器"""

    def __init__(
        self, task_id: int, local_path: str, s3_target: str, csv_path: str, status_path: str, num_workers: int = 10
    ):
        self.task_id = task_id
        self.local_path = local_path
        self.num_workers = num_workers

        # 解析S3路径
        self.target_bucket, self.target_prefix = self._parse_s3_path(s3_target)
        self.csv_bucket, self.csv_key = self._parse_s3_path(csv_path)
        self.status_bucket, self.status_key = self._parse_s3_path(status_path)

        # 创建工作目录
        self.work_dir = Path.home() / ".di_workspace" / str(task_id)
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.csv_file = self.work_dir / "upload_records.csv"

        # CSV记录队列
        self.csv_queue = queue.Queue()
        self.processed_files = set()
        self.total_files = 0

    def _parse_s3_path(self, s3_path: str) -> Tuple[str, str]:
        """解析S3路径"""
        if s3_path.startswith("s3://"):
            parts = s3_path[5:].split("/", 1)
            bucket = parts[0]
            key = parts[1] if len(parts) > 1 else ""
            return bucket, key
        return "", ""

    def _collect_files(self) -> list:
        """收集需要上传的文件"""
        files = []

        if os.path.isfile(self.local_path):
            files.append(self.local_path)
            self.total_files += 1
        else:
            for root, _, filenames in os.walk(self.local_path):
                for filename in filenames:
                    file_path = os.path.join(root, filename)
                    if not os.path.islink(file_path):  # 跳过符号链接
                        files.append(file_path)
                        self.total_files += 1

        # 过滤已处理的文件
        base_path = os.path.dirname(self.local_path) if os.path.isfile(self.local_path) else self.local_path
        unprocessed_files = []

        for file_path in files:
            rel_path = os.path.relpath(file_path, base_path)
            if rel_path not in self.processed_files:
                unprocessed_files.append(file_path)

        return unprocessed_files

    def _csv_writer_worker(self):
        """CSV写入工作器"""
        # 初始化CSV文件
        uploaded_count = 0
        file_exists = os.path.exists(self.csv_file)

        with open(self.csv_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["local_path", "sha256", "s3path", "file_size"])

            while True:
                try:
                    record = self.csv_queue.get(timeout=1)
                    if record is None:  # 结束信号
                        break

                    writer.writerow(
                        [record["local_path"], record["file_hash"], record["s3_path"], str(record["file_size"])]
                    )

                    f.flush()  # 确保数据写入磁盘
                    self.csv_queue.task_done()
                    uploaded_count += 1
                    # 每上传100个文件，打印进度
                    if uploaded_count % 1000 == 0:
                        logger.info(f"已上传 {uploaded_count} 个文件")

                except queue.Empty:
                    continue
                except Exception as e:
                    logger.error(f"Failed to write CSV record: {e}")
                    self.csv_queue.task_done()

    def _upload_worker(self, s3_client: SimpleS3Client, file_queue: queue.Queue, base_path: str):
        """上传工作器"""
        while True:
            try:
                file_path = file_queue.get(timeout=1)
                if file_path is None:  # 结束信号
                    break

                try:
                    # 计算相对路径和S3对象名
                    rel_path = os.path.relpath(file_path, base_path)

                    object_name = os.path.join(self.target_prefix, rel_path).replace("\\", "/")

                    # 上传文件
                    file_hash, file_size = s3_client.upload_file(file_path, self.target_bucket, object_name)

                    # 将记录放入CSV队列
                    s3_path = f"s3://{self.target_bucket}/{object_name}"
                    record = {
                        "local_path": os.path.join("/", rel_path),
                        "file_hash": file_hash,
                        "s3_path": s3_path,
                        "file_size": file_size,
                    }
                    self.csv_queue.put(record)

                    logger.debug(f"Uploaded: {rel_path}")

                except Exception as e:
                    logger.error(f"Failed to upload {file_path}: {e}")
                finally:
                    file_queue.task_done()

            except queue.Empty:
                break

    def _calculate_final_stats(self) -> UploadStatus:
        """从CSV文件计算最终统计信息"""
        stats = UploadStatus()
        if not os.path.exists(self.csv_file):
            return stats

        total_count = 0
        total_size = 0

        try:
            with open(self.csv_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    total_count += 1
                    total_size += int(row["file_size"])
        except Exception as e:
            logger.error(f"Failed to calculate stats: {e}")

        stats.update(total_count, total_size)

        return stats

    def run(self, s3_client: SimpleS3Client) -> UploadStatus:
        """执行上传任务"""
        # 收集文件
        files = self._collect_files()
        if not files:
            logger.info("No files to upload")
            return UploadStatus()

        logger.info(f"Found {len(files)} files to upload")

        # 准备文件队列
        file_queue = queue.Queue()
        for file_path in files:
            file_queue.put(file_path)

        base_path = os.path.dirname(self.local_path) if os.path.isfile(self.local_path) else self.local_path

        # 启动CSV写入线程
        csv_thread = threading.Thread(target=self._csv_writer_worker)
        csv_thread.daemon = True
        csv_thread.start()

        try:
            # 启动上传工作器
            with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
                futures = []
                for i in range(self.num_workers):
                    future = executor.submit(self._upload_worker, s3_client, file_queue, base_path)
                    futures.append(future)

                # 等待所有任务完成
                for future in as_completed(futures):
                    future.result()

            # 等待CSV队列处理完成
            self.csv_queue.join()

            # 发送结束信号给CSV写入线程
            self.csv_queue.put(None)
            csv_thread.join()

            # 上传记录文件到S3
            if os.path.exists(self.csv_file):
                s3_client.upload_file(str(self.csv_file), self.csv_bucket, self.csv_key)
                logger.info("Upload records saved to S3")

            # 计算并上传最终统计信息
            stats = self._calculate_final_stats()
            s3_client.upload_json(stats.to_dict(), self.status_bucket, self.status_key)
            logger.info(f"Upload completed: {stats.uploaded_count} files, {stats.uploaded_size} bytes")

        finally:
            # 清理工作目录
            try:
                import shutil

                shutil.rmtree(self.work_dir)
            except Exception as e:
                logger.warning(f"Failed to cleanup workspace: {e}")
        return stats


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="简化的数据摄取工具")
    parser.add_argument("-e", "--endpoint", default="192.168.13.160:9008", help="S3端点")
    parser.add_argument("-ak", "--access-key", default="admin2024", help="访问密钥")
    parser.add_argument("-sk", "--secret-key", default="root@23452024", help="秘密密钥")
    parser.add_argument("-t", "--target", default="s3://testbucket/test_ok11", help="目标S3路径")
    parser.add_argument("-l", "--local", default="./test_data", help="本地路径")
    parser.add_argument("-o", "--object-sheet", default="s3://testbucket/records/123.csv", help="记录文件S3路径")
    parser.add_argument("-s", "--status", default="s3://testbucket/status/123.json", help="状态文件S3路径")
    parser.add_argument("-i", "--task-id", type=int, default=123, help="任务ID")
    parser.add_argument("-n", "--num-workers", type=int, default=10, help="工作线程数")

    args = parser.parse_args()

    # 检查本地路径
    if not os.path.exists(args.local):
        logger.error(f"Local path does not exist: {args.local}")
        sys.exit(1)

    logger.info(f"Starting upload: {args.local} -> {args.target}")

    try:
        # 创建S3客户端
        s3_client = SimpleS3Client(args.endpoint, args.access_key, args.secret_key)

        # 创建上传器并执行
        uploader = DataUploader(
            task_id=args.task_id,
            local_path=args.local,
            s3_target=args.target,
            csv_path=args.object_sheet,
            status_path=args.status,
            num_workers=args.num_workers,
        )

        uploader.run(s3_client)
        logger.info("Upload completed successfully")

    except Exception as e:
        logger.error(f"Upload failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
