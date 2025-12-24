import logging
import os
from typing import Any, Optional
from . import ffmpeg_utils

logger = logging.getLogger(__name__)


def get_duration(material_path: str, track_type: Optional[str] = "Video") -> Any:
    from pymediainfo import MediaInfo
    media_info = MediaInfo.parse(material_path)
    material_duration = 0
    for track in media_info.tracks:
        if track.track_type == track_type:
            material_duration = track.duration * 1000  # 微秒
            break
    return material_duration


def extract_audio_stream(input_file: str, output_file: str):
    """
    使用 FFmpeg 的流复制模式从视频文件中无损提取音频。

    :param input_file: 输入视频文件的路径。
    :param output_file: 输出音频文件的路径 (例如: 'audio.aac', 'audio.mp3' 等)。
    """
    # 确保输出目录存在，以及构建准确的命令
    if not os.path.exists(input_file):
        logger.error(f"❌ 错误：输入文件不存在 - {input_file}")
        return

    # 逻辑分析：确保命令的效率和精确性
    command = [
        'ffmpeg',
        '-i', input_file,  # 输入文件
        '-vn',  # 忽略视频流 (Video No)
        '-acodec', 'copy',  # 音频流复制，确保无损和速度 (Audio Codec Copy)
        '-y',  # 遇到同名文件时覆盖输出 (非必须，但方便自动化)
        output_file  # 输出文件
    ]

    ffmpeg_utils.execute_command(command)
