"""配置管理模块.

使用 Dynaconf 进行配置管理
支持：default.yaml → {env}.yaml → local.yaml → 环境变量覆盖
"""

from pathlib import Path

from dynaconf import Dynaconf, Validator

# 项目根目录和配置目录
ROOT = Path(__file__).resolve().parent  # src/tracer/
CONFIG_DIR = ROOT / "config"


# 创建 Dynaconf 设置实例
settings = Dynaconf(
    # 配置文件
    settings_files=[
        str(CONFIG_DIR / "default.yaml"),
        str(CONFIG_DIR / "prompt.yaml"),  # Prompt 配置
        str(CONFIG_DIR / "local.yaml"),  # 本地覆盖配置
    ],
    # 启用分层环境
    environments=True,
    # 默认环境
    default_env="default",
    # 环境变量前缀
    envvar_prefix="SDWK",
    # 环境变量嵌套分隔符
    env_nested_delimiter="__",
    # 禁用 Dynaconf 的 .env 文件加载，避免编码问题
    # 注意：在 需要用到 .env 文件时 中用 UTF-8 编码预加载了 .env 文件
    load_dotenv=False,
    encoding="utf-8",
    # 启用深度合并，避免节点完全替换
    merge_enabled=True,
    # 验证器
    validators=[
        # 必需的配置项
        Validator("platform.url", must_exist=True),
        # 数值范围验证
        # Validator("server.port", gte=1, lte=65535),
        # Validator("database.port", gte=1, lte=65535),
        # Validator("database.pool_size", gte=1),
        # Validator("database.max_overflow", gte=0),
        # 枚举值验证
        # Validator("app.log_level", is_in=["DEBUG", "INFO", "WARNING", "ERROR"]),
        # Validator("app.log_format", is_in=["text", "json"]),
    ],
)

def get_prompt(key: str, default=None):
    """获取 Prompt 配置.

    Args:
        key: 配置键，使用点号分隔，如 "llm_service.language_prompts"
        default: 默认值

    Returns:
        配置值或默认值

    """
    try:
        # 使用 get 方法访问嵌套配置
        return settings.get(key, default)
    except Exception:
        return default


# 将方法绑定到 settings 对象
settings.get_prompt = get_prompt


def get_settings():
    """获取配置实例 - 返回全局 settings 对象."""
    return settings
