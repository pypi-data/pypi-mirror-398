import asyncio
import os
import hashlib
from typing import Optional, Tuple, Callable

import aiohttp

async def do_download(
        url: str,
        file_path: Optional[str] = None,
        retry: int = 2,
        cookies: Optional[dict] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None
) -> Optional[Tuple[str, str]]:
    """
    异步下载指定文件链接到指定文件中，并支持进度回调

    参数:
        url: 下载链接
        file_path: 保存文件路径，None时不保存（仅计算MD5）
        retry: 下载失败重试次数
        cookies: 请求时携带的cookies
        progress_callback: 进度回调函数，接收参数为(已下载字节数, 总字节数)

    返回:
        保存的文件路径和文件MD5哈希值
    """
    if not url:
        raise ValueError('下载链接不能为空')

    for attempt in range(retry + 1):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, cookies=cookies) as response:
                    response.raise_for_status()  # 检查HTTP错误状态

                    # 获取文件总大小（从响应头获取）
                    total_size = int(response.headers.get('Content-Length', 0))
                    downloaded_size = 0

                    # 创建保存目录
                    if file_path:
                        os.makedirs(os.path.dirname(file_path), exist_ok=True)

                    # 计算MD5并处理文件内容
                    md5 = hashlib.md5()

                    if file_path:
                        with open(file_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(1024):
                                if chunk:
                                    f.write(chunk)
                                    md5.update(chunk)
                                    downloaded_size += len(chunk)
                                    # 调用进度回调（总大小已知时才触发）
                                    if progress_callback and total_size > 0:
                                        progress_callback(downloaded_size, total_size)
                    else:
                        # 不保存文件仅计算MD5
                        async for chunk in response.content.iter_chunked(1024):
                            if chunk:
                                md5.update(chunk)
                                downloaded_size += len(chunk)
                                if progress_callback and total_size > 0:
                                    progress_callback(downloaded_size, total_size)

                    # 统一路径格式
                    if file_path:
                        file_path = file_path.replace('\\', "/")
                    return file_path, md5.hexdigest()

        except Exception as e:
            if attempt == retry:
                raise RuntimeError(f"下载失败（已重试{retry}次）: {str(e)}") from e
            await asyncio.sleep(1)  # 重试间隔1秒
