import asyncio
import time
from typing import List, Dict, Any, Optional, Callable, Awaitable


# ------------------------------
# 修复后的防抖实现
# ------------------------------
class Debounce:
    """防抖函数实现（支持异步函数，修复装饰器语法）"""

    def __init__(self, func: Callable[..., Any | Awaitable[Any]], delay: int, immediate: bool = False):
        self.func = func  # 要防抖的函数
        self.delay = delay / 1000  # 转换为秒（原JS的毫秒）
        self.immediate = immediate  # 是否立即执行
        self.timer: Optional[asyncio.Task] = None  # 定时器任务
        self.last_call_time = 0.0  # 最后一次调用时间

    async def __call__(self, *args, **kwargs):
        """使类实例可调用（兼容装饰器语法）"""
        current_time = time.time()
        self.last_call_time = current_time

        # 取消之前未执行的定时器任务
        if self.timer and not self.timer.done():
            self.timer.cancel()

        # 立即执行模式：如果是第一次调用且无未完成任务，直接执行
        if self.immediate and (not self.timer or self.timer.done()):
            result = self.func(*args, **kwargs)
            if isinstance(result, Awaitable):
                await result

        # 创建新的延迟执行任务
        async def delayed_execution():
            await asyncio.sleep(self.delay)
            # 确保当前是最后一次调用（避免重复执行）
            if time.time() - self.last_call_time >= self.delay - 0.001:  # 允许微小误差
                result = self.func(*args, **kwargs)
                if isinstance(result, Awaitable):
                    await result

        self.timer = asyncio.create_task(delayed_execution())


def debounce(delay: int, immediate: bool = False) -> Callable[[Callable], Debounce]:
    """带参数的装饰器工厂函数（修复核心）"""

    def decorator(func: Callable[..., Any | Awaitable[Any]]) -> Debounce:
        # 返回 Debounce 实例，将 func 传入
        return Debounce(func, delay, immediate)

    return decorator
