#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""CLI 配置管理模块"""

import json
import os
from pathlib import Path
from typing import Dict, Optional


class ConfigError(Exception):
    """配置相关错误"""

    pass


class Config:
    """CLI 配置管理类"""

    def __init__(self, config_file: Optional[str] = None):
        """初始化配置管理

        Args:
            config_file: 配置文件路径，如果不提供则使用默认路径
        """
        if config_file:
            self.config_file = Path(config_file)
        else:
            # 默认配置文件路径：~/.aihub/config.json
            config_dir = Path.home() / ".aihub"
            config_dir.mkdir(exist_ok=True)
            self.config_file = config_dir / "config.json"

    def _load_config(self) -> Dict[str, str]:
        """加载配置文件"""
        if not self.config_file.exists():
            return {}

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            raise ConfigError(f"无法读取配置文件 {self.config_file}: {e}")

    def _save_config(self, config: Dict[str, str]) -> None:
        """保存配置文件"""
        try:
            # 确保目录存在
            self.config_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except IOError as e:
            raise ConfigError(f"无法写入配置文件 {self.config_file}: {e}")

    def get(self, key: str) -> Optional[str]:
        """获取配置项

        Args:
            key: 配置项名称

        Returns:
            配置项值，如果不存在则返回 None
        """
        # 优先从环境变量获取
        env_key = f"AIHUB_{key.upper()}"
        env_value = os.getenv(env_key)
        if env_value:
            return env_value

        # 从配置文件获取
        config = self._load_config()
        return config.get(key)

    def set(self, key: str, value: str) -> None:
        """设置配置项

        Args:
            key: 配置项名称
            value: 配置项值
        """
        config = self._load_config()
        config[key] = value
        self._save_config(config)

    def list_all(self) -> Dict[str, str]:
        """列出所有配置项

        Returns:
            所有配置项的字典
        """
        config = self._load_config()

        # 合并环境变量
        for key in ["base_url", "token"]:
            env_key = f"AIHUB_{key.upper()}"
            env_value = os.getenv(env_key)
            if env_value:
                config[key] = env_value

        return config

    def delete(self, key: str) -> bool:
        """删除配置项

        Args:
            key: 配置项名称

        Returns:
            是否成功删除
        """
        config = self._load_config()
        if key in config:
            del config[key]
            self._save_config(config)
            return True
        return False


# 全局配置实例
_config_instance: Optional[Config] = None


def get_config(config_file: Optional[str] = None) -> Config:
    """获取配置实例（单例模式）

    Args:
        config_file: 配置文件路径

    Returns:
        配置实例
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config(config_file)
    return _config_instance
