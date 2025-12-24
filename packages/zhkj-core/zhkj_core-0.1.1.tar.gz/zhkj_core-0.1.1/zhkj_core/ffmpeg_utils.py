import functools
import logging
import subprocess
from typing import List
from zhkj_core.wrap import mutex_method

logger = logging.getLogger(__name__)


@functools.lru_cache
def check_available():
    """检查 FFmpeg 是否能正常调用"""
    try:
        return execute_command(['ffmpeg', "-version"])
    except (subprocess.CalledProcessError, FileNotFoundError):
        raise RuntimeError("FFmpeg 未找到或无法正常运行！请确保已安装并加入环境变量，或指定正确的 ffmpeg_path")


@mutex_method()
def execute_command(cmd: List[str]) -> bool:
    """执行FFmpeg命令

    Args:
        cmd: FFmpeg命令列表

    Returns:
        命令执行是否成功
    """
    logger.debug(f"执行FFmpeg命令: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd,
                                timeout=600,
                                check=True,
                                shell=True,
                                encoding="utf-8")  # 超时时间10分钟
        try:
            return_code = result.returncode
            if return_code != 0:
                logger.error(f"FFmpeg命令执行失败，错误码:{return_code}，命令:{cmd}", exc_info=True)
                raise Exception(f"FFmpeg命令执行失败，错误码:{return_code}")
            return True
        except subprocess.TimeoutExpired:
            logger.error(f"FFmpeg命令执行超时: {' '.join(cmd)}", exc_info=True)
    except Exception as e:
        logger.error(f"执行FFmpeg命令时发生异常: {e}")
    return False
