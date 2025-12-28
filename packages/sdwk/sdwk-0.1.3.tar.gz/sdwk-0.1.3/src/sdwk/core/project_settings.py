"""项目配置管理模块.

为用户项目提供统一的配置加载和管理功能。
用户项目只需要在项目根目录创建 config/settings.yaml，
然后通过 SDK 提供的接口加载配置。
"""

import os
from pathlib import Path
from typing import Any

from dynaconf import Dynaconf


class ProjectSettings:
    """项目配置管理器.

    自动查找并加载用户项目的配置文件。
    支持的配置文件位置（按优先级）:
    1. 当前工作目录下的 config/settings.yaml
    2. 项目根目录下的 config/settings.yaml
    3. src/{project_name}/config/settings.yaml
    """

    _instance = None
    _settings = None

    def __new__(cls):
        """单例模式."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化配置."""
        if self._settings is None:
            self._settings = self._load_settings()

    def _find_config_file(self) -> Path | None:
        """查找配置文件.

        Returns:
            配置文件路径，如果找不到返回 None
        """
        # 当前工作目录
        cwd = Path.cwd()

        # 候选路径列表
        candidates = [
            cwd / "config" / "settings.yaml",
            cwd / "src" / "config" / "settings.yaml",
        ]

        # 尝试查找项目根目录（包含 sdw.json 的目录）
        current = cwd
        for _ in range(5):  # 最多向上查找5层
            if (current / "sdw.json").exists():
                candidates.insert(0, current / "config" / "settings.yaml")
                break
            if current.parent == current:
                break
            current = current.parent

        # 查找第一个存在的配置文件
        for candidate in candidates:
            if candidate.exists():
                return candidate

        return None

    def _load_settings(self) -> Dynaconf:
        """加载配置.

        Returns:
            Dynaconf 配置对象
        """
        config_file = self._find_config_file()

        if config_file:
            # 找到配置文件，加载它
            settings = Dynaconf(
                settings_files=[str(config_file)],
                envvar_prefix="SDWK",
                env_nested_delimiter="__",
                load_dotenv=False,
                encoding="utf-8",
                merge_enabled=True,
            )
        else:
            # 没有找到配置文件，使用空配置
            settings = Dynaconf(
                envvar_prefix="SDWK",
                env_nested_delimiter="__",
                load_dotenv=False,
                encoding="utf-8",
                merge_enabled=True,
            )

        return settings

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值.

        Args:
            key: 配置键，使用点号分隔，如 "platform.url"
            default: 默认值

        Returns:
            配置值或默认值
        """
        try:
            return self._settings.get(key, default)
        except Exception:
            return default

    def __getattr__(self, name: str) -> Any:
        """支持属性访问方式.

        Args:
            name: 属性名

        Returns:
            配置值
        """
        if name.startswith("_"):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
        return getattr(self._settings, name)


# 全局配置实例
_project_settings = None


def get_project_settings() -> ProjectSettings:
    """获取项目配置实例.

    Returns:
        ProjectSettings 实例
    """
    global _project_settings
    if _project_settings is None:
        _project_settings = ProjectSettings()
    return _project_settings


# 便捷访问
settings = get_project_settings()
