from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator

class BaseAppSettings(BaseSettings):
    """
    应用配置基类，封装公共配置逻辑，子类直接继承使用
    """

    class Config:
        # 公共环境变量配置：默认读取项目根目录的 .env 文件
        env_file = Path(".env").absolute()
        # 支持嵌套环境变量（如：DB.HOST=localhost）
        env_nested_delimiter = "."
        # 允许环境变量覆盖配置文件
        case_sensitive = False

    # 可选：添加全局公共配置属性（所有子类共享，可被覆盖）
    app_env: Optional[str] = "development"  # 环境：development/production/test

    # 可选：添加公共校验逻辑（子类自动继承）
    @field_validator("app_env")
    def validate_app_env(cls, v):
        valid_envs = ["development", "production", "test"]
        if v not in valid_envs:
            raise ValueError(f"app_env 必须是 {valid_envs} 中的一种")
        return v
