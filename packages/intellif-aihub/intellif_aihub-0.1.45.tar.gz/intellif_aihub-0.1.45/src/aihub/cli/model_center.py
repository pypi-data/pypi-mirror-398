#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""模型中心 CLI 命令模块"""
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from ..models.model_center import (
    ListModelsRequest,
    CreateModelRequest,
    EditModelRequest,
)

console = Console()

# 创建模型中心子应用
model_app = typer.Typer(
    name="model",
    help="模型中心相关命令",
    no_args_is_help=True,
)


@model_app.command("list")
def list_models(
    page_size: int = typer.Option(20, "--page-size", "-s", help="每页显示数量"),
    page_num: int = typer.Option(1, "--page", "-p", help="页码"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="按名称过滤"),
    tags: Optional[str] = typer.Option(None, "--tags", "-t", help="按标签过滤"),
    model_ids: Optional[str] = typer.Option(None, "--ids", help="按模型ID过滤（逗号分隔）"),
):
    """列出模型"""
    from .main import get_client

    try:
        client = get_client()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("正在获取模型列表...", total=None)

            request = ListModelsRequest(
                page_size=page_size,
                page_num=page_num,
                name=name,
                tags=tags,
                model_ids=model_ids,
            )

            response = client.model_center.list_models(request)
            progress.remove_task(task)

        if not response.data:
            console.print("📭 没有找到模型")
            return

        # 创建表格显示结果
        table = Table(title=f"模型列表 (第 {page_num} 页，共 {response.total} 个)")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("名称", style="magenta")
        table.add_column("描述", style="green")
        table.add_column("公开", style="blue")

        for model in response.data:
            table.add_row(
                str(model.id),
                model.name,
                model.description or "-",
                "是" if model.is_public else "否",
            )

        console.print(table)

        # 显示分页信息
        total_pages = (response.total + page_size - 1) // page_size
        console.print(f"\n📄 第 {page_num}/{total_pages} 页，共 {response.total} 个模型")

    except Exception as e:
        console.print(f"❌ 获取模型列表失败: {e}", style="red")
        raise typer.Exit(1)


@model_app.command("get")
def get_model(
    model_id: int = typer.Argument(..., help="模型ID"),
):
    """获取模型详情"""
    from .main import get_client

    try:
        client = get_client()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"正在获取模型 {model_id} 详情...", total=None)
            model = client.model_center.get_model(model_id)
            progress.remove_task(task)

        # 显示模型详情
        console.print(f"\n🤖 [bold]模型详情[/bold]")
        console.print(f"ID: {model.id}")
        console.print(f"名称: {model.name}")
        console.print(f"描述: {model.description or '无'}")
        console.print(f"标签: {model.tags or '无'}")
        console.print(f"公开: {'是' if model.is_public else '否'}")
        console.print(f"创建时间: {'_' if model.created_at else '未知'}")

        if model.readme_content:
            console.print(f"\n📖 [bold]README:[/bold]")
            console.print(model.readme_content[:500] + ("..." if len(model.readme_content) > 500 else ""))

    except Exception as e:
        console.print(f"❌ 获取模型详情失败: {e}", style="red")
        raise typer.Exit(1)


@model_app.command("create")
def create_model(
    name: str = typer.Argument(..., help="模型名称"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="模型描述"),
    tags: Optional[str] = typer.Option(None, "--tags", "-t", help="模型标签"),
    public: bool = typer.Option(True, "--public/--private", help="是否公开"),
    readme: Optional[str] = typer.Option(None, "--readme", "-r", help="README 内容"),
):
    """创建模型"""
    from .main import get_client

    try:
        client = get_client()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"正在创建模型 '{name}'...", total=None)

            request = CreateModelRequest(
                name=name,
                description=description,
                tags=tags,
                is_public=public,
                readme_content=readme,
            )

            model_id = client.model_center.create_model(request)
            progress.remove_task(task)

        console.print(f"✅ 模型创建成功！")
        console.print(f"模型ID: {model_id}")
        console.print(f"名称: {name}")

    except Exception as e:
        console.print(f"❌ 创建模型失败: {e}", style="red")
        raise typer.Exit(1)


@model_app.command("edit")
def edit_model(
    model_id: int = typer.Argument(..., help="模型ID"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="新的模型名称"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="新的模型描述"),
    public: Optional[bool] = typer.Option(None, "--public/--private", help="是否公开"),
):
    """编辑模型信息"""
    from .main import get_client

    try:
        client = get_client()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"正在编辑模型 {model_id}...", total=None)

            request = EditModelRequest(
                name=name,
                description=description,
                is_public=public,
            )

            client.model_center.edit_model(model_id, request)
            progress.remove_task(task)

        console.print(f"✅ 模型 {model_id} 编辑成功！")

    except Exception as e:
        console.print(f"❌ 编辑模型失败: {e}", style="red")
        raise typer.Exit(1)


@model_app.command("delete")
def delete_model(
    model_id: int = typer.Argument(..., help="模型ID"),
    force: bool = typer.Option(False, "--force", "-f", help="强制删除，不询问确认"),
):
    """删除模型"""
    from .main import get_client

    if not force:
        confirm = typer.confirm(f"确定要删除模型 {model_id} 吗？此操作不可撤销！")
        if not confirm:
            console.print("❌ 操作已取消")
            return

    try:
        client = get_client()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"正在删除模型 {model_id}...", total=None)
            client.model_center.delete_model(model_id)
            progress.remove_task(task)

        console.print(f"✅ 模型 {model_id} 删除成功！")

    except Exception as e:
        console.print(f"❌ 删除模型失败: {e}", style="red")
        raise typer.Exit(1)


@model_app.command("upload")
def upload_model(
    local_dir: str = typer.Argument(..., help="本地模型目录路径"),
    model_id: Optional[int] = typer.Option(None, "--model-id", help="模型ID"),
    model_name: Optional[str] = typer.Option(None, "--model-name", help="模型名称"),
    timeout: int = typer.Option(3600, "--timeout", help="上传超时时间（秒）"),
):
    """上传模型文件"""
    from .main import get_client

    # 验证参数
    if not model_id and not model_name:
        console.print("❌ 必须提供 --model-id 或 --model-name 参数", style="red")
        raise typer.Exit(1)

    local_path = Path(local_dir)
    if not local_path.exists():
        console.print(f"❌ 本地目录不存在: {local_dir}", style="red")
        raise typer.Exit(1)

    try:
        client = get_client()

        console.print(f"🚀 开始上传模型...")
        console.print(f"本地目录: {local_dir}")
        if model_id:
            console.print(f"目标模型ID: {model_id}")
        if model_name:
            console.print(f"目标模型名称: {model_name}")

        client.model_center.upload(
            local_dir=str(local_path),
            model_id=model_id,
            model_name=model_name,
            timeout_seconds=timeout,
        )

        console.print("✅ 模型上传成功！")

    except Exception as e:
        console.print(f"❌ 上传模型失败: {e}", style="red")
        raise typer.Exit(1)


@model_app.command("download")
def download_model(
    local_dir: str = typer.Argument(..., help="下载到的本地目录路径"),
    model_id: Optional[int] = typer.Option(None, "--model-id", help="模型ID"),
    model_name: Optional[str] = typer.Option(None, "--model-name", help="模型名称"),
):
    """下载模型文件"""
    from .main import get_client

    # 验证参数
    if not model_id and not model_name:
        console.print("❌ 必须提供 --model-id 或 --model-name 参数", style="red")
        raise typer.Exit(1)

    try:
        client = get_client()

        console.print(f"📥 开始下载模型...")
        if model_id:
            console.print(f"模型ID: {model_id}")
        if model_name:
            console.print(f"模型名称: {model_name}")
        console.print(f"下载目录: {local_dir}")

        client.model_center.download(
            local_dir=local_dir,
            model_id=model_id,
            model_name=model_name,
        )

        console.print("✅ 模型下载成功！")

    except Exception as e:
        console.print(f"❌ 下载模型失败: {e}", style="red")
        raise typer.Exit(1)


@model_app.command("info")
def model_info(
    model_id: Optional[int] = typer.Option(None, "--model-id", help="模型ID"),
    model_name: Optional[str] = typer.Option(None, "--model-name", help="模型名称"),
):
    """获取模型数据库信息"""
    from .main import get_client

    # 验证参数
    if not model_id and not model_name:
        console.print("❌ 必须提供 --model-id 或 --model-name 参数", style="red")
        raise typer.Exit(1)

    try:
        client = get_client()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("正在获取模型信息...", total=None)
            model_db = client.model_center.get_model_db(id=model_id, name=model_name)
            progress.remove_task(task)

        # 显示模型数据库信息
        console.print(f"\n🗄️ [bold]模型数据库信息[/bold]")
        console.print(f"ID: {model_db.id}")
        console.print(f"名称: {model_db.name}")
        console.print(f"状态: {model_db.status}")
        console.print(f"对象存储路径: {model_db.object_storage_path or '无'}")
        console.print(f"CSV文件路径: {model_db.csv_file_path or '无'}")
        console.print(f"Parquet索引路径: {model_db.parquet_index_path or '无'}")
        console.print(f"任务状态S3路径: {model_db.task_status_s3_path or '无'}")

    except Exception as e:
        console.print(f"❌ 获取模型信息失败: {e}", style="red")
        raise typer.Exit(1)
