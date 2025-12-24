import aiohttp
import yaml
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Type, TypeVar, Generic
from pathlib import Path
from pydantic import ValidationError, BaseModel

from .common import deep_merge
from .settings import BaseAppSettings

# 泛型类型：约束为 Pydantic BaseModel 子类
T = TypeVar("T", bound=BaseAppSettings)
C = TypeVar("C", bound='BaseConfigLoader')


class BaseConfigLoader(Generic[T]):
    """
    通用配置加载基类，支持 YAML 文件、远程配置中心加载（后台线程异步加载）
    对外提供同步接口，内部通过线程池处理异步逻辑
    """
    # 子类必须指定的配置模型（Pydantic BaseModel 子类）
    CONFIG_MODEL: Type[T] = None
    # 缓存配置（类级共享）
    _cached_config: T = None
    _last_load_time: float = 0
    # 缓存过期时间（秒），可被子类覆盖
    CACHE_TTL: int = 60
    # 线程池（用于执行异步远程加载）
    _executor = ThreadPoolExecutor(max_workers=1)

    @classmethod
    def load(cls: Type[C], config_path: str = "config/config.yaml", force_reload: bool = False) -> T:
        """同步加载配置（对外接口，内部处理异步逻辑）"""
        if not cls.CONFIG_MODEL:
            raise NotImplementedError("子类必须指定 CONFIG_MODEL（Pydantic 配置模型）")

        current_time = time.time()
        # 缓存有效且不强制刷新时，直接返回缓存
        if (not force_reload and cls._cached_config and
                current_time - cls._last_load_time < cls.CACHE_TTL):
            return cls._cached_config

        # 1. 加载默认配置（Pydantic 模型默认值）
        default_config = cls.CONFIG_MODEL()
        # 2. 加载 YAML 配置并合并
        yaml_config = cls._load_yaml_config(config_path)
        merged_config = cls._merge_configs(default_config, yaml_config)
        # 3. 若配置了远程地址，通过线程池异步加载远程配置并合并
        if hasattr(merged_config, "CONFIG_CENTER_URL") and merged_config.CONFIG_CENTER_URL:
            # 提交异步任务到线程池，并同步等待结果
            remote_config = cls._executor.submit(
                cls._run_async_remote_load, merged_config
            ).result()  # 同步等待，但实际加载在后台线程执行
            merged_config = cls._merge_configs(merged_config, remote_config)

        # 更新缓存
        cls._cached_config = merged_config
        cls._last_load_time = current_time

        return merged_config

    @classmethod
    def _run_async_remote_load(cls, config: T) -> Dict[str, Any]:
        """改进：不修改全局事件循环，避免冲突"""
        # 创建新的事件循环（仅用于当前任务，不关联到线程全局）
        loop = asyncio.new_event_loop()
        try:
            # 直接用 loop 执行任务，不调用 asyncio.set_event_loop
            return loop.run_until_complete(cls._load_remote_config(config))
        finally:
            loop.close()  # 确保事件循环关闭，释放资源

    @classmethod
    async def _load_remote_config(cls, config: T) -> Dict[str, Any]:
        """异步加载远程配置（实际加载逻辑，在子线程的事件循环中执行）"""
        try:
            headers = {}
            if hasattr(config, "CONFIG_CENTER_TOKEN") and config.CONFIG_CENTER_TOKEN:
                headers["Authorization"] = f"Bearer {config.CONFIG_CENTER_TOKEN}"
            remote_url = None
            if hasattr(config, "CONFIG_CENTER_URL") and config.CONFIG_CENTER_URL:
                remote_url = config.CONFIG_CENTER_URL
            else:
                return {}

            async with aiohttp.ClientSession() as session:
                async with session.get(
                        url=remote_url,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    response.raise_for_status()
                    return await response.json()
        except Exception as e:
            print(f"[远程配置加载失败] {e}")
            return {}

    @classmethod
    def _load_yaml_config(cls, config_path_str: str = "config/config.yaml") -> Dict[str, Any]:
        """加载 YAML 配置文件（同步操作）"""
        config_path = Path(config_path_str)
        if not config_path.exists():
            return {}

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"[YAML 配置加载失败] {e}")
            return {}

    @classmethod
    def _merge_configs(cls: Type[C], base_config: T, new_config: Dict[str, Any]) -> T:
        """深度合并配置并通过 Pydantic 验证"""
        if not new_config:
            return base_config

        base_dict = base_config.dict()
        merged_dict = deep_merge(base_dict, new_config)

        try:
            return cls.CONFIG_MODEL(**merged_dict)
        except ValidationError as e:
            print(f"[配置合并验证失败] {e}")
            return base_config

    @classmethod
    def clear_cache(cls: Type[C]) -> None:
        """清除缓存"""
        cls._cached_config = None
        cls._last_load_time = 0

    @classmethod
    def shutdown(cls) -> None:
        """关闭线程池（程序退出时调用）"""
        cls._executor.shutdown()
