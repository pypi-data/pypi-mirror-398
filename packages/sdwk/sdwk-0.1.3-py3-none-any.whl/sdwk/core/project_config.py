"""Project configuration management."""

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class ProjectConfig(BaseModel):
    """SDW项目配置."""

    name: str = Field(..., description="项目名称")
    type: str = Field(..., description="项目类型 (node/graph)")
    description: str = Field(default="", description="项目描述")
    version: str = Field(default="0.1.0", description="项目版本")
    platform_url: str = Field(default="https://platform.sdw.com", description="平台地址")
    author: str | None = Field(default=None, description="作者")
    python_version: str = Field(default=">=3.10", description="Python版本要求")

    # 项目特定配置
    entry_point: str | None = Field(default=None, description="入口点")
    dependencies: dict[str, str] = Field(default_factory=dict, description="依赖包")
    dev_dependencies: dict[str, str] = Field(default_factory=dict, description="开发依赖")

    class Config:
        extra = "allow"  # 允许额外字段

    @classmethod
    def from_file(cls, config_path: Path) -> "ProjectConfig":
        """从配置文件加载."""
        if not config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")

        with open(config_path, encoding="utf-8") as f:
            data = json.load(f)

        return cls(**data)

    def to_file(self, config_path: Path) -> None:
        """保存到配置文件."""
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(self.model_dump(), f, indent=2, ensure_ascii=False)

    def get_template_context(self) -> dict[str, Any]:
        """获取模板渲染上下文."""
        # 生成PascalCase类名，尽量保留用户输入中的大小写
        raw_name = self.name.strip()
        parts = raw_name.replace("-", " ").replace("_", " ").split()
        pascal_parts = []
        for p in parts:
            if p.islower():
                pascal_parts.append(p.capitalize())
            else:
                pascal_parts.append(p)
        project_name_pascal = "".join(pascal_parts) if pascal_parts else raw_name.title().replace(" ", "")

        return {
            # 基本项目信息
            "project_name": self.name,
            "project_type": self.type,
            "project_description": self.description,
            "project_version": self.version,
            "platform_url": self.platform_url,
            "author": self.author or "Unknown",
            "python_version": self.python_version,
            "entry_point": self.entry_point or "src.main:app",
            # 依赖信息
            "dependencies": self.dependencies,
            "dev_dependencies": self.dev_dependencies,
            # 派生字段 - 项目名称的不同格式
            "project_name_snake": self.name.lower().replace("-", "_").replace(" ", "_"),
            "project_name_kebab": self.name.lower().replace("_", "-").replace(" ", "-"),
            "project_name_title": self.name.replace("-", " ").replace("_", " ").title(),
            "project_name_pascal": project_name_pascal,
            # 其他常用变量
            "author_name": self.author or "Unknown",
            "author_email": "author@example.com",  # 默认邮箱
            "current_year": 2023,  # 可以使用 datetime.now().year，但为了一致性使用固定值
        }
