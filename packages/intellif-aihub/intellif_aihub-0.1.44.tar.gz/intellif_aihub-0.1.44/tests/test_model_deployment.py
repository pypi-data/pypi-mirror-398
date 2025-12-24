"""模型部署服务测试"""

import os
from aihub.client import Client
from aihub.models.model_deployment import (
    DeploymentCreateRequest,
    DeploymentListRequest,
)


def test_create_deployment():
    """测试创建部署"""
    client = Client(
        base_url=os.getenv("AI_HUB_BASE_URL", "http://localhost:8080"),
        token=os.getenv("AI_HUB_TOKEN", "test_token"),
    )

    # 创建部署请求
    request = DeploymentCreateRequest(
        name="test-deployment",
        description="测试部署",
        virtual_cluster_id=1,
        deploy_template="default",
        health_check_path="/health",
        container_concurrency=1,
        model_id=1,
    )

    deployment_id = client.model_deployment.create_deployment(request)
    print(f"Created deployment ID: {deployment_id}")
    assert deployment_id > 0


def test_list_deployments():
    """测试查询部署列表"""
    client = Client(
        base_url=os.getenv("AI_HUB_BASE_URL", "http://localhost:8080"),
        token=os.getenv("AI_HUB_TOKEN", "test_token"),
    )

    request = DeploymentListRequest(page_size=10, page_num=1)
    response = client.model_deployment.list_deployments(request)

    print(f"Total deployments: {response.total}")
    for deployment in response.data:
        print(f"  - {deployment.name} (ID: {deployment.id}, Status: {deployment.status})")


def test_get_deployment():
    """测试获取部署详情"""
    client = Client(
        base_url=os.getenv("AI_HUB_BASE_URL", "http://localhost:8080"),
        token=os.getenv("AI_HUB_TOKEN", "test_token"),
    )

    deployment_id = 1
    deployment = client.model_deployment.get_deployment(deployment_id)

    print(f"Deployment: {deployment.name}")
    print(f"  Status: {deployment.status}")
    print(f"  Created: {deployment.created_at}")
    print(f"  API Host: {deployment.api_host}")


def test_start_deployment():
    """测试启动部署"""
    client = Client(
        base_url=os.getenv("AI_HUB_BASE_URL", "http://localhost:8080"),
        token=os.getenv("AI_HUB_TOKEN", "test_token"),
    )

    deployment_id = 1
    client.model_deployment.start_deployment(deployment_id)
    print(f"Started deployment {deployment_id}")


def test_stop_deployment():
    """测试停止部署"""
    client = Client(
        base_url=os.getenv("AI_HUB_BASE_URL", "http://localhost:8080"),
        token=os.getenv("AI_HUB_TOKEN", "test_token"),
    )

    deployment_id = 1
    client.model_deployment.stop_deployment(deployment_id)
    print(f"Stopped deployment {deployment_id}")


def test_get_deployment_pods():
    """测试获取部署Pods"""
    client = Client(
        base_url=os.getenv("AI_HUB_BASE_URL", "http://localhost:8080"),
        token=os.getenv("AI_HUB_TOKEN", "test_token"),
    )

    deployment_id = 1
    pods = client.model_deployment.get_deployment_pods(deployment_id)

    print(f"Total pods: {pods.total}")
    for pod in pods.data:
        print(f"  - {pod.name} (Node: {pod.node_name}, Status: {pod.status})")


def test_get_deployment_logs():
    """测试获取部署日志"""
    client = Client(
        base_url=os.getenv("AI_HUB_BASE_URL", "http://localhost:8080"),
        token=os.getenv("AI_HUB_TOKEN", "test_token"),
    )

    deployment_id = 1
    logs = client.model_deployment.get_deployment_logs(deployment_id, page_size=50)

    print("Deployment logs:")
    print(logs.data)


if __name__ == "__main__":
    # 运行测试时请确保设置了正确的环境变量
    # export AI_HUB_BASE_URL=http://your-server
    # export AI_HUB_TOKEN=your-token

    print("Testing Model Deployment Service...")
    print("\n=== Test List Deployments ===")
    try:
        test_list_deployments()
    except Exception as e:
        print(f"Error: {e}")

    print("\n=== Test Get Deployment ===")
    try:
        test_get_deployment()
    except Exception as e:
        print(f"Error: {e}")

    print("\n=== Test Create Deployment ===")
    try:
        test_create_deployment()
    except Exception as e:
        print(f"Error: {e}")

    print("\n=== Test Start Deployment ===")
    try:
        test_start_deployment()
    except Exception as e:
        print(f"Error: {e}")

    print("\n=== Test Get Deployment Pods ===")
    try:
        test_get_deployment_pods()
    except Exception as e:
        print(f"Error: {e}")

    print("\n=== Test Get Deployment Logs ===")
    try:
        test_get_deployment_logs()
    except Exception as e:
        print(f"Error: {e}")

    print("\n=== Test Stop Deployment ===")
    try:
        test_stop_deployment()
    except Exception as e:
        print(f"Error: {e}")
