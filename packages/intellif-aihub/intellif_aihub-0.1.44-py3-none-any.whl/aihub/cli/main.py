#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""AI-HUB SDK CLI 主入口

提供命令行接口来使用 AI-HUB SDK 的各项功能
"""

import sys
from typing import Optional

import typer
from loguru import logger

from .config import get_config, ConfigError
from .model_center import model_app
from ..client import Client

# 创建主应用
app = typer.Typer(
    name="aihub",
    help="AI-HUB SDK 命令行工具",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

# 添加子命令
app.add_typer(model_app, name="model", help="模型中心相关命令")
# app.add_typer(dataset_app, name="dataset", help="数据集管理相关命令")


def version_callback(value: bool):
    """显示版本信息"""
    if value:
        typer.echo("AI-HUB SDK CLI v0.1.0")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(None, "--version", "-v", callback=version_callback, help="显示版本信息"),
    verbose: bool = typer.Option(False, "--verbose", help="启用详细日志输出"),
    config_file: Optional[str] = typer.Option(None, "--config", "-c", help="指定配置文件路径"),
):
    """AI-HUB SDK 命令行工具

    使用此工具可以通过命令行操作 AI-HUB 平台的各项功能，包括：
    - 模型管理（上传、下载、列表等）
    - 数据集管理（创建、上传、下载等）

    首次使用前请配置 base_url 和 token：
    aihub config init --base-url https://your-aihub-server.com --token your-access-token

    或使用传统方式：
    aihub config manage set base_url https://your-aihub-server.com
    aihub config manage set token your-access-token
    """
    # 设置日志级别
    log_level = "DEBUG" if verbose else "INFO"
    logger.remove()
    logger.add(
        sys.stderr,
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level=log_level,
    )


# 创建 config 子应用
config_app = typer.Typer(
    name="config",
    help="配置管理",
    no_args_is_help=True,
)

# 添加 config 子命令到主应用
app.add_typer(config_app, name="config", help="配置管理相关命令")


@config_app.command("init")
def config_init(
        base_url: Optional[str] = typer.Option("http://192.168.99.63:30021", "--base-url", help="AI-HUB 服务器地址"),
    token: Optional[str] = typer.Option(None, "--token", help="访问令牌"),
):
    """初始化配置

    使用选项参数快速设置 base_url 和 token
    base_url 有默认值 https://api.aihub.com，如需使用其他地址请指定

    示例：
    aihub config init --token your-token  # 使用默认 base_url
    aihub config init --base-url https://your-server.com --token your-token
    """
    try:
        config_obj = get_config()

        # 由于 base_url 现在有默认值，只有当 token 也为 None 时才报错
        if not token:
            typer.echo("错误: 需要提供 --token 参数", err=True)
            raise typer.Exit(1)

        success_count = 0
        total_count = 0

        # base_url 现在总是有值（要么是用户提供的，要么是默认值）
        if base_url:
            total_count += 1
            try:
                config_obj.set("base_url", base_url)
                typer.echo(f"✅ 已设置 base_url = {base_url}")
                success_count += 1
            except Exception as e:
                typer.echo(f"❌ 设置 base_url 失败: {e}", err=True)

        if token:
            total_count += 1
            try:
                config_obj.set("token", token)
                # 隐藏 token 的部分内容用于显示
                display_token = f"{token[:8]}..." if len(token) > 8 else token
                typer.echo(f"✅ 已设置 token = {display_token}")
                success_count += 1
            except Exception as e:
                typer.echo(f"❌ 设置 token 失败: {e}", err=True)

        if success_count == total_count:
            typer.echo(f"\n🎉 配置初始化完成！成功设置 {success_count} 个参数")
        else:
            typer.echo(f"\n⚠️  配置初始化部分完成，成功设置 {success_count}/{total_count} 个参数")
            raise typer.Exit(1)

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"❌ 配置初始化失败: {e}", err=True)
        raise typer.Exit(1)


@config_app.command("manage")
def config_manage(
    action: str = typer.Argument(..., help="操作类型: set, get, list, delete, batch-set"),
    key: Optional[str] = typer.Argument(None, help="配置项名称"),
    value: Optional[str] = typer.Argument(None, help="配置项值"),
    batch_params: Optional[str] = typer.Option(
        None, "--batch", "-b", help="批量设置参数，格式: key1=value1,key2=value2"
    ),
):
    """配置管理（传统方式）

    支持的配置项：
    - base_url: AI-HUB 服务器地址
    - token: 访问令牌

    示例：
    # 单个设置
    aihub config manage set base_url https://your-server.com
    aihub config manage set token your-token

    # 批量设置
    aihub config manage batch-set --batch "base_url=https://your-server.com,token=your-token"
    aihub config manage set --batch "base_url=https://your-server.com,token=your-token"

    # 其他操作
    aihub config manage get base_url
    aihub config manage list
    aihub config manage delete token
    """
    try:
        config_obj = get_config()

        if action == "set":
            # 支持批量设置
            if batch_params:
                _batch_set_config(config_obj, batch_params)
            elif key and value:
                config_obj.set(key, value)
                typer.echo(f"✅ 已设置 {key} = {value}")
            else:
                typer.echo("错误: set 操作需要提供 key 和 value，或使用 --batch 参数", err=True)
                raise typer.Exit(1)

        elif action == "batch-set":
            if not batch_params:
                typer.echo("错误: batch-set 操作需要提供 --batch 参数", err=True)
                raise typer.Exit(1)
            _batch_set_config(config_obj, batch_params)

        elif action == "get":
            if not key:
                typer.echo("错误: get 操作需要提供 key", err=True)
                raise typer.Exit(1)
            value = config_obj.get(key)
            if value:
                typer.echo(f"{key} = {value}")
            else:
                typer.echo(f"配置项 {key} 未设置")

        elif action == "list":
            config_dict = config_obj.list_all()
            if config_dict:
                typer.echo("当前配置:")
                for k, v in config_dict.items():
                    # 隐藏 token 的部分内容
                    if k == "token" and v:
                        display_value = f"{v[:8]}..." if len(v) > 8 else v
                    else:
                        display_value = v
                    typer.echo(f"  {k} = {display_value}")
            else:
                typer.echo("暂无配置项")

        elif action == "delete":
            if not key:
                typer.echo("错误: delete 操作需要提供 key", err=True)
                raise typer.Exit(1)
            config_obj.delete(key)
            typer.echo(f"✅ 已删除配置项 {key}")

        else:
            typer.echo(f"错误: 不支持的操作 '{action}'", err=True)
            typer.echo("支持的操作: set, get, list, delete, batch-set")
            raise typer.Exit(1)

    except Exception as e:
        typer.echo(f"❌ 配置操作失败: {e}", err=True)
        raise typer.Exit(1)


def _batch_set_config(config_obj, batch_params: str):
    """批量设置配置参数"""
    try:
        # 解析批量参数
        params = {}
        for param in batch_params.split(","):
            param = param.strip()
            if "=" not in param:
                typer.echo(f"错误: 参数格式不正确 '{param}'，应为 key=value", err=True)
                raise typer.Exit(1)

            key, value = param.split("=", 1)
            key = key.strip()
            value = value.strip()

            if not key or not value:
                typer.echo(f"错误: 参数不能为空 '{param}'", err=True)
                raise typer.Exit(1)

            params[key] = value

        if not params:
            typer.echo("错误: 没有有效的参数", err=True)
            raise typer.Exit(1)

        # 批量设置
        success_count = 0
        for key, value in params.items():
            try:
                config_obj.set(key, value)
                typer.echo(f"✅ 已设置 {key} = {value}")
                success_count += 1
            except Exception as e:
                typer.echo(f"❌ 设置 {key} 失败: {e}", err=True)

        typer.echo(f"\n🎉 批量设置完成，成功设置 {success_count}/{len(params)} 个参数")

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"❌ 批量设置失败: {e}", err=True)
        raise typer.Exit(1)


def get_client() -> Client:
    """获取配置好的客户端实例"""
    try:
        config_obj = get_config()
        base_url = config_obj.get("base_url")
        token = config_obj.get("token")

        if not base_url:
            typer.echo("错误: 未配置 base_url，请先运行: aihub config init --base-url <your-server-url>", err=True)
            raise typer.Exit(1)

        if not token:
            typer.echo("错误: 未配置 token，请先运行: aihub config init --token <your-token>", err=True)
            raise typer.Exit(1)

        return Client(base_url=base_url, token=token, log_level="INFO")

    except ConfigError as e:
        typer.echo(f"配置错误: {e}", err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
