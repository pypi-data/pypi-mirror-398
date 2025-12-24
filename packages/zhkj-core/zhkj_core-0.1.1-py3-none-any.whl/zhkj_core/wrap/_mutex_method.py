import threading
import time
from enum import Enum
from typing import Dict, Callable, Any, Optional, Union, List
from datetime import datetime
import logging
import functools
import inspect


class MethodStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"


class MethodMutex:
    """精简版互斥管理器，专注核心锁逻辑，避免状态冗余"""

    _instance = None
    _lock = threading.RLock()  # 确保所有操作线程安全

    def __new__(cls):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._locked_keys: Dict[str, datetime] = {}  # 仅存储运行中的key和开始时间
        self.logger = logging.getLogger(__name__)
        self._initialized = True

    def can_execute(self, key: str, timeout_seconds: int = 3600) -> bool:
        """判断key是否可执行（未锁定或已超时）"""
        with self._lock:
            if key not in self._locked_keys:
                return True
            # 检查超时
            elapsed = (datetime.now() - self._locked_keys[key]).total_seconds()
            if elapsed > timeout_seconds:
                self.logger.warning(f"Mutex key '{key}' timed out (elapsed: {elapsed}s), allowing execution")
                del self._locked_keys[key]
                return True
            return False

    def acquire(self, key: str, timeout_seconds: int = 3600) -> bool:
        """获取锁，成功返回True，失败返回False"""
        with self._lock:
            if self.can_execute(key, timeout_seconds):
                self._locked_keys[key] = datetime.now()
                self.logger.info(f"[Thread-{threading.get_ident()}] Acquired lock: {key}")
                return True
            self.logger.warning(f"[Thread-{threading.get_ident()}] Failed to acquire lock: {key} (already locked)")
            return False

    def release(self, key: str):
        """释放锁，无论是否存在都安全处理"""
        with self._lock:
            if key in self._locked_keys:
                del self._locked_keys[key]
                self.logger.info(f"[Thread-{threading.get_ident()}] Released lock: {key}")
            else:
                self.logger.warning(f"[Thread-{threading.get_ident()}] Lock not found for release: {key}")

    def is_locked(self, key: str) -> bool:
        """检查key是否处于锁定状态"""
        with self._lock:
            return key in self._locked_keys


# 全局单例
method_mutex = MethodMutex()


def _get_mutex_key(func: Callable, key: Union[str, Callable, None], args: tuple, kwargs: dict) -> str:
    """安全生成互斥key，逻辑清晰无歧义"""
    try:
        if key is None:
            # 场景1：未指定key → 模块.函数名
            return f"{func.__module__}.{func.__name__}"
        elif isinstance(key, str):
            # 场景2：字符串key → 直接使用
            return key
        elif callable(key):
            # 场景3：可调用key生成器 → 执行生成
            result = key(*args, **kwargs)
            if not isinstance(result, str):
                logging.warning(f"[Thread-{threading.get_ident()}] Key generator for {func.__name__} returned {type(result)}, converted to string")
                result = str(result)
            return result
        else:
            # 场景4：非法类型 → 默认key
            default_key = f"{func.__module__}.{func.__name__}.invalid"
            logging.warning(f"[Thread-{threading.get_ident()}] Invalid key type {type(key)} for {func.__name__}, using default: {default_key}")
            return default_key
    except Exception as e:
        default_key = f"{func.__module__}.{func.__name__}.error"
        logging.warning(f"[Thread-{threading.get_ident()}] Key generator failed for {func.__name__}: {e}, using default: {default_key}")
        return default_key


def mutex_method(key: Union[str, Callable, None] = None, timeout_seconds: int = 3600):
    """阻塞式互斥装饰器：同一key重复调用抛异常，逻辑极简无歧义"""
    # 处理直接装饰函数的情况（无参数使用：@mutex_method）
    if callable(key) and not isinstance(key, (str, type(lambda: None))):
        func = key
        key = None
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            mutex_key = _get_mutex_key(func, key, args, kwargs)
            if not method_mutex.acquire(mutex_key, timeout_seconds):
                raise RuntimeError(f"[Thread-{threading.get_ident()}] Mutex key '{mutex_key}' is locked, cannot execute {func.__name__}")
            try:
                return func(*args, **kwargs)
            finally:
                method_mutex.release(mutex_key)
        return wrapper

    # 处理带参数使用的情况（@mutex_method(key=...)）
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            mutex_key = _get_mutex_key(func, key, args, kwargs)
            if not method_mutex.acquire(mutex_key, timeout_seconds):
                raise RuntimeError(f"[Thread-{threading.get_ident()}] Mutex key '{mutex_key}' is locked, cannot execute {func.__name__}")
            try:
                return func(*args, **kwargs)
            finally:
                # 确保无论是否异常，都释放锁
                method_mutex.release(mutex_key)
        return wrapper
    return decorator


def nonblocking_mutex_method(key: Union[str, Callable, None] = None, timeout_seconds: int = 3600,
                             default_return: Any = None):
    """非阻塞式互斥装饰器：同一key重复调用返回默认值"""
    if callable(key) and not isinstance(key, (str, type(lambda: None))):
        func = key
        key = None
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            mutex_key = _get_mutex_key(func, key, args, kwargs)
            if method_mutex.acquire(mutex_key, timeout_seconds):
                try:
                    return func(*args, **kwargs)
                finally:
                    method_mutex.release(mutex_key)
            return default_return
        return wrapper

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            mutex_key = _get_mutex_key(func, key, args, kwargs)
            if method_mutex.acquire(mutex_key, timeout_seconds):
                try:
                    return func(*args, **kwargs)
                finally:
                    method_mutex.release(mutex_key)
            logging.warning(f"[Thread-{threading.get_ident()}] Non-blocking: {func.__name__} skipped (key '{mutex_key}' locked)")
            return default_return
        return wrapper
    return decorator


# ------------------------------ Key生成器（新增key_from_params）------------------------------
def key_from_args(*arg_indices, separator: str = "_"):
    """按参数索引生成key（原有功能）"""
    def generator(*args, **kwargs):
        parts = []
        for idx in arg_indices:
            parts.append(str(args[idx]) if idx < len(args) else f"arg{idx}_missing")
        return separator.join(parts)
    return generator


def simple_key(prefix: str, *arg_indices, **kwarg_names):
    """前缀+参数索引+关键字参数生成key（原有功能）"""
    def generator(*args, **kwargs):
        parts = [prefix]
        # 位置参数
        for idx in arg_indices:
            if idx < len(args):
                parts.append(str(args[idx]))
        # 关键字参数（kwarg_names的值为参数名，如project="project"）
        for param_name in kwarg_names.values():
            if param_name in kwargs:
                parts.append(str(kwargs[param_name]))
        return "_".join(parts)
    return generator


def key_from_param_names(*param_names, separator: str = "_"):
    """按参数名生成key（原有功能，需回溯栈帧）"""
    def generator(*args, **kwargs):
        frame = inspect.currentframe().f_back.f_back.f_back  # 回溯到被装饰函数
        local_vars = frame.f_locals if frame else {}
        parts = []
        for param in param_names:
            if param in local_vars:
                parts.append(str(local_vars[param]))
            elif param in kwargs:
                parts.append(str(kwargs[param]))
            else:
                parts.append(f"{param}_missing")
        return separator.join(parts)
    return generator


def key_from_params(*param_names, prefix: str = "", separator: str = "_"):
    """
    新增：按参数名提取值并拼接key（推荐使用，无需关心参数位置）
    Args:
        *param_names: 要包含的参数名（位置参数、关键字参数均可）
        prefix: key前缀（可选）
        separator: 参数值分隔符（默认"_"）
    示例：
        @mutex_method(key=key_from_params("user_id", "project", prefix="order"))
        def create_order(user_id: int, project: str, amount: float): ...
        → 调用 create_order(123, "test", 100) → key = "order_123_test"
    """
    def generator(*args, **kwargs):
        # 获取函数签名，解析参数名与位置的映射
        func = inspect.currentframe().f_back.f_back.f_back.f_code  # 回溯到被装饰函数
        param_spec = inspect.getfullargspec(func)
        param_names_list = param_spec.args  # 函数定义的参数名列表

        key_parts = [prefix] if prefix else []  # 前缀（可选）

        for param_name in param_names:
            # 1. 先从位置参数中找（根据参数名对应的索引）
            if param_name in param_names_list:
                param_idx = param_names_list.index(param_name)
                if param_idx < len(args):
                    key_parts.append(str(args[param_idx]))
                    continue
            # 2. 再从关键字参数中找
            if param_name in kwargs:
                key_parts.append(str(kwargs[param_name]))
                continue
            # 3. 参数缺失，用占位符
            key_parts.append(f"{param_name}_missing")

        # 移除空字符串（避免前缀为空时出现多余分隔符）
        key_parts = [part for part in key_parts if part]
        return separator.join(key_parts)
    return generator