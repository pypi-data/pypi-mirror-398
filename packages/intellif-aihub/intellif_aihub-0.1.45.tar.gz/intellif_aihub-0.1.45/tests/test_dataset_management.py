from __future__ import annotations

import unittest
import uuid

from src.aihub.client import Client

BASE_URL = "http://192.168.13.160:30021"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NjMwOTExMTgsImlhdCI6MTc2MjQ4NjMxOCwidWlkIjoyfQ.FmjVmtW7nIBPL_oWa-Yif2P8RPCTAn0uADkees0ZWfw"


class TestDatasetManagement(unittest.TestCase):
    def test_create_dataset_and_version(self):
        client = Client(base_url=BASE_URL, token=TOKEN)
        dataset_name = f"sdk_dataset_{uuid.uuid4().hex[:6]}"
        dataset_id, dataset_version_id, version_tag = client.dataset_management.create_dataset_and_version(
            dataset_name=dataset_name,
            dataset_description="xxxxx",
            is_local_upload=True,
            local_file_path=r"C:\Users\admin\Desktop\hbase\images.zip",
            server_file_path="",
            version_description="yyyyy",
        )
        print("dataset_id:", dataset_id)
        print("dataset_version_id:", dataset_version_id)
        print("version_tag:", version_tag)

    def test_run_download(self):
        client = Client(base_url=BASE_URL, token=TOKEN)
        client.dataset_management.run_download(
            dataset_version_name="re/V12",
            local_dir=r"./data/output",
            worker=4,
        )
        print("Done!")

    def test_upload_dir(self):
        client = Client(base_url=BASE_URL, token=TOKEN)
        dataset_name = f"sdk_dataset_{uuid.uuid4().hex[:6]}"
        dataset_id, dataset_version_id, version_tag = client.dataset_management.create_dataset_and_version(
            dataset_name=dataset_name,
            dataset_description="xxxxx",
            is_local_upload=True,
            local_file_path="./data",
            server_file_path="",
            version_description="yyyyy",
        )
        print("dataset_id:", dataset_id)
        print("dataset_version_id:", dataset_version_id)
        print("version_tag:", version_tag)

    def test_list_datasets(self):
        client = Client(base_url=BASE_URL, token=TOKEN)

        # Test basic list with default parameters
        datasets_resp = client.dataset_management.list_datasets()

        print(f"Total datasets: {datasets_resp.total}")
        print(f"Page size: {datasets_resp.page_size}")
        print(f"Page number: {datasets_resp.page_num}")
        print(f"Number of datasets in current page: {len(datasets_resp.data)}")

        # Print first few datasets if any
        for i, dataset in enumerate(datasets_resp.data[:3]):
            print(f"Dataset {i+1}: ID={dataset.id}, Name={dataset.name}, Description={dataset.description}")

        # Test with custom page size
        datasets_resp_custom = client.dataset_management.list_datasets(page_size=5, page_num=1)
        print(
            f"Custom page size test - Total: {datasets_resp_custom.total}, Page size: {datasets_resp_custom.page_size}"
        )

        # Test with name filter
        if datasets_resp.data:
            first_dataset_name = datasets_resp.data[0].name
            datasets_resp_filtered = client.dataset_management.list_datasets(name=first_dataset_name)
            print(f"Filtered by name '{first_dataset_name}': {len(datasets_resp_filtered.data)} results")

    def test_list_dataset_versions(self):
        client = Client(base_url=BASE_URL, token=TOKEN)

        # First get list of datasets to find a valid dataset_id
        datasets_resp = client.dataset_management.list_datasets(page_size=5)

        if not datasets_resp.data:
            print("No datasets found, creating one for testing...")
            # Create a dataset for testing
            dataset_name = f"test_list_versions_{uuid.uuid4().hex[:6]}"
            dataset_id, _, _ = client.dataset_management.create_dataset_and_version(
                dataset_name=dataset_name,
                dataset_description="Test dataset for list versions",
                is_local_upload=True,
                local_file_path="./data",
                version_description="Test version",
            )
        else:
            dataset_id = datasets_resp.data[0].id
            print(f"Using existing dataset ID: {dataset_id}")

        # Test basic list without dataset_id filter (all versions)
        versions_resp = client.dataset_management.list_dataset_versions()

        print(f"Total dataset versions: {versions_resp.total}")
        print(f"Page size: {versions_resp.page_size}")
        print(f"Page number: {versions_resp.page_num}")
        print(f"Number of versions in current page: {len(versions_resp.data)}")

        # Print first few versions if any
        for i, version in enumerate(versions_resp.data[:3]):
            print(
                f"Version {i+1}: ID={version.id}, Dataset={version.dataset_name}, Version={version.version}, Status={version.status}"
            )

        # Test with dataset_id filter
        versions_resp_filtered = client.dataset_management.list_dataset_versions(dataset_id=dataset_id)
        print(f"Versions for dataset {dataset_id}: {len(versions_resp_filtered.data)} results")

        if versions_resp_filtered.data:
            for version in versions_resp_filtered.data:
                print(f"  Version: ID={version.id}, Version={version.version}, Status={version.status}")

        # Test with custom page size
        versions_resp_custom = client.dataset_management.list_dataset_versions(page_size=10, page_num=1)
        print(
            f"Custom page size test - Total: {versions_resp_custom.total}, Page size: {versions_resp_custom.page_size}"
        )

    def test_get_dataset_version(self):
        client = Client(base_url=BASE_URL, token=TOKEN)

        dataset = client.dataset_management.get_dataset_version_by_name("re/V12")
        dataset.id

        # First get list of datasets to find a valid dataset_id
        dataset = client.dataset_management.get_dataset_version(991)
        print(dataset.file_storage_path)
