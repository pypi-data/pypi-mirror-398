import sys
import time
from typing import Callable, Optional

def default_progress_callback(progress, step):
    # 进度条长度
    bar_length = 25
    # 计算进度条填充长度
    filled_length = int(bar_length * progress // 100)
    # 创建进度条字符串
    bar = '█' * filled_length + '-' * (bar_length - filled_length)

    # 构建消息
    msg = f"\r进度：|{bar}| {progress:.1f}% | 步骤：{step}"

    # 输出进度条（使用\r回车到行首，实现单行刷新）
    sys.stdout.write(msg)
    sys.stdout.flush()

    # 如果进度达到100%，换行
    if progress >= 100:
        print()


class NestedProgressCallback:
    """嵌套进度回调类"""

    def __init__(self, parent_callback: Optional[Callable[[float, str], None]],
                 start_percent: float, end_percent: float, parent_step: str = ""):
        """
        :param parent_callback: 父进度回调函数
        :param start_percent: 子进度开始的百分比
        :param end_percent: 子进度结束的百分比
        :param parent_step: 父步骤描述
        """
        self.parent_callback = parent_callback or (lambda progress, step: ())
        self.start_percent = start_percent
        self.end_percent = end_percent
        self.parent_step = parent_step
        self.range_size = end_percent - start_percent

    def __call__(self, progress: float, step: str = ""):
        """更新嵌套进度"""
        progress = max(0.0, min(100.0, progress))  # 确保进度在0-100之间

        # 计算在总进度中的位置
        total_progress = self.start_percent + int(self.range_size * progress / 100)

        # 构建完整的步骤描述
        full_step = self.parent_step
        if step:
            if full_step:
                full_step += f" > {step}"
            else:
                full_step = step

        # 调用父回调
        self.parent_callback(total_progress, full_step)

    def create_sub_callback(self, sub_start: float, sub_end: float, sub_step: str = ""):
        """创建子进度回调（支持多级嵌套）"""
        # 计算在父进度范围内的起始和结束位置
        absolute_start = self.start_percent + int(self.range_size * sub_start / 100)
        absolute_end = self.start_percent + int(self.range_size * sub_end / 100)

        # 构建步骤描述
        full_step = self.parent_step
        if sub_step:
            if full_step:
                full_step += f" > {sub_step}"
            else:
                full_step = sub_step

        return NestedProgressCallback(
            self.parent_callback, absolute_start, absolute_end, full_step
        )



class InstallDownloadBridge:
    """
    download_with_progress 所需的 (downloaded, total) -> 嵌套进度。

    __call__ 签名兼容可选的 speed 参数。如果 speed 为 None，则内部计算速度。
    """
    # 增加 slots 以保持内存效率
    __slots__ = ("_inner_cb", "_last_downloaded", "_last_time")

    def __init__(self, nested_cb: NestedProgressCallback):
        self._inner_cb = nested_cb
        # 初始化速度计算所需的变量
        self._last_downloaded = 0
        self._last_time = time.time()  # 记录初始时间

    def __call__(
            self,
            downloaded: int,
            total: int,
            speed: Optional[float] = None
    ) -> None:

        calculated_speed_kbs: float = 0.0  # 初始化速度

        # 1. 如果传入了速度，则直接使用
        if speed is not None:
            calculated_speed_kbs = speed
            # 即使传入了外部速度，也更新状态，以便下次内部计算
            self._last_downloaded = downloaded
            self._last_time = time.time()

        # 2. 如果未传入速度 (或 speed 为 None)，使用您的简化逻辑
        else:
            current_time = time.time()
            time_diff = current_time - self._last_time

            # 仅在时间流逝超过 0.1 秒时才进行速度计算和更新
            if time_diff > 0.1:
                bytes_diff = downloaded - self._last_downloaded

                # 计算速度 (KB/s)
                speed_bps = bytes_diff / time_diff
                calculated_speed_kbs = speed_bps / 1024

                # 状态更新 (仅在此 if 内部发生)
                self._last_downloaded = downloaded
                self._last_time = current_time
            else:
                # 如果时间不足 0.1s，使用上次计算的速度或默认为 0.0
                # 由于 self._last_downloaded/time 未更新，如果回调频繁，
                # 最好能存储上一次计算的 speed，否则它会一直显示 0.0 KB/s
                # 如果是这种情况，可以增加一个 self._last_calculated_speed 变量。
                # 但为了简单，我们假设下载库回调频率不会高到导致 time_diff 连续 < 0.1s
                # 并且在 time_diff < 0.1s 时，我们选择不进行任何操作并退出回调。
                # ⚠️ 注意：如果不更新进度，需要确保调用方能接受不触发回调的情况
                # 如果您是直接在下载库的回调中实现此逻辑，通常的做法是:
                # 1. 计算 speed
                # 2. 如果 time_diff > 0.1，则调用 progress_callback

                # 适应 InstallDownloadBridge 类结构，如果 time_diff <= 0.1，我们必须退出
                return  # 退出，不进行回调和更新。

        # 3. 格式化并调用嵌套回调 (仅在计算/使用了新速度后执行)
        if total == 0:
            step = f"已下载 {downloaded / 1024:.1f} KB | 速度 {calculated_speed_kbs:.1f} KB/s"
            self._inner_cb(0, step)
            return

        percent = int(downloaded / total * 100)
        total_mb = total / 1024 / 1024
        down_mb = downloaded / 1024 / 1024

        step = f"{down_mb:.1f}/{total_mb:.1f} MB  速度 {calculated_speed_kbs:.1f} KB/s"
        self._inner_cb(percent, step)


class SubProgress:
    """把 parent 的 [start, end] 再切成 n 段，支持实时汇报"""

    def __init__(self, parent: "NestedProgressCallback", start: int, end: int, step_name: str, segments: int = 1):
        self.parent = parent.create_sub_callback(start, end, step_name)
        self.segs = segments
        self.idx = 0

    def __call__(self, progress: float, step: str = ""):
        self.update(progress, step)

    def update(self, seg_progress: float, msg: str = ""):
        """
        seg_progress: 0~100  当前 segment 的进度
        """
        overall = (self.idx * 100 + seg_progress) / self.segs
        self.parent(int(overall), msg)

    def next_segment(self):
        self.idx += 1
