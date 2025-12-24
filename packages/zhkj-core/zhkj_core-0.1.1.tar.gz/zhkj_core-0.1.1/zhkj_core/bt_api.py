# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 黄文良 <2879625666@qq.com>
# +-------------------------------------------------------------------
import logging
import random
import string
import time
import hashlib
import sys
import os
import json
from pathlib import Path
from typing import Optional, Callable, AsyncGenerator, Dict

import aiohttp
import aiofiles
import ssl


class bt_api:
    __BT_KEY: str
    __BT_PANEL: str
    __UPLOAD_DIR: str

    def __init__(self, bt_panel=None, bt_key=None, upload_dir=None):
        bt_api.__BT_PANEL = bt_panel
        bt_api.__BT_KEY = bt_key
        bt_api.__UPLOAD_DIR = upload_dir
        # 创建SSL上下文（忽略证书验证）
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

    async def http_post(self, url, p_data, timeout=1800):
        """发送POST请求（异步）"""
        try:
            timeout_obj = aiohttp.ClientTimeout(total=timeout)
            async with aiohttp.ClientSession(timeout=timeout_obj) as session:
                async with session.post(
                        url,
                        data=p_data,
                        ssl_context=self.ssl_context
                ) as response:
                    response.encoding = 'utf-8'
                    result = await response.json()
                    return self.chech_result(result)
        except Exception as e:
            print(f"POST请求失败: {str(e)}")
            return None

    def _generate_boundary(self):
        """生成随机boundary"""
        return '----WebKitFormBoundary' + ''.join(
            random.choices(string.ascii_letters + string.digits, k=16)
        )

    async def _build_multipart_generator(
            self,
            file_path: str,
            data: dict,
            boundary: str,
            chunk_size: int,
            progress_callback: Optional[Callable[[int, int], None]]
    ) -> AsyncGenerator[bytes, None]:
        """
        异步生成器函数，用于逐块构建multipart/form-data请求体。
        """
        file = Path(file_path)
        file_size = file.stat().st_size
        file_name = os.path.basename(file)

        # 1. 生成表单数据部分
        for key, value in data.items():
            part = (
                f'--{boundary}\r\n'
                f'Content-Disposition: form-data; name="{key}"\r\n'
                f'\r\n'
                f'{value}\r\n'
            ).encode('utf-8')
            yield part

        # 2. 生成文件数据部分的头部
        file_header = (
            f'--{boundary}\r\n'
            f'Content-Disposition: form-data; name="blob"; filename="{file_name}"\r\n'
            f'Content-Type: application/octet-stream\r\n'
            f'\r\n'
        ).encode('utf-8')
        yield file_header

        # 3. 生成文件数据部分的内容（分块）
        bytes_read = 0
        async with aiofiles.open(file, 'rb') as f:
            while True:
                chunk = await f.read(chunk_size)
                if not chunk:
                    break
                yield chunk
                bytes_read += len(chunk)
                if progress_callback:
                    progress_callback(bytes_read, file_size)

        # 4. 生成结束分隔符
        end_boundary = f'\r\n--{boundary}--\r\n'.encode('utf-8')
        yield end_boundary

    async def http_multipart_post(
            self,
            url: str,
            file_path: str,
            path: str = None,
            timeout=1800,
            progress_callback: Optional[Callable[[int, int], None]] = None,
            chunk_size: int = 8192  # 每次上传的块大小，可以根据网络情况调整
    ):
        """
        不依赖第三方库，实现带进度条的流式文件上传（异步）。
        """
        if path is None:
            path = bt_api.__UPLOAD_DIR
        file = Path(file_path)
        if not file.exists():
            print(f"文件不存在: {file_path}")
            return None

        file_size = file.stat().st_size
        file_name = os.path.basename(file)

        # 生成一个随机的boundary，用于分隔请求体中的不同部分
        boundary = '--------------------------' + os.urandom(16).hex()

        # 构造表单数据
        form_data = {
            'f_path': f"{path}/",
            'f_name': file_name,
            'f_size': str(file_size),
            'f_start': '0'
        }

        # 准备请求头，必须包含Content-Type
        headers = {
            'Content-Type': f'multipart/form-data; boundary={boundary}'
        }

        # 创建进度回调的包装器，用于在无回调时打印默认进度
        wrapped_callback = progress_callback
        if wrapped_callback is None:
            last_percent = -1

            def default_callback(bytes_uploaded: int, total_bytes: int):
                nonlocal last_percent
                if total_bytes == 0:
                    return
                percent = int((bytes_uploaded / total_bytes) * 100)
                if percent != last_percent:
                    last_percent = percent
                    sys.stdout.write(
                        f"\r上传进度: {percent}% ({bytes_uploaded}/{total_bytes} bytes)"
                    )
                    sys.stdout.flush()

            wrapped_callback = default_callback

        # 使用异步生成器构建请求体
        request_body_generator = self._build_multipart_generator(
            file_path, form_data, boundary, chunk_size, wrapped_callback
        )

        try:
            timeout_obj = aiohttp.ClientTimeout(total=timeout)
            async with aiohttp.ClientSession(timeout=timeout_obj) as session:
                # 发送请求，data参数接收异步生成器
                async with session.post(
                        url,
                        data=request_body_generator,
                        headers=headers,
                        ssl_context=self.ssl_context
                ) as response:
                    response.raise_for_status()
                    result = await response.json()

                    if progress_callback is None:
                        print("\n上传成功!")

                    return result
        except Exception as e:
            if progress_callback is None:
                print("\n上传失败!")
            print(f"文件上传请求失败: {str(e)}")
            return None

    # 取面板日志（异步）
    async def get_logs(self):
        url = f"{self.__BT_PANEL}/data?action=getData"
        p_data = self.__get_key_data()
        p_data['table'] = 'logs'
        p_data['limit'] = 10
        p_data['tojs'] = 'test'

        result = await self.http_post(url, p_data)
        return result

    # 搜索文件（异步）
    async def search_files(self, search: str, path: str = None):
        if path is None:
            path = bt_api.__UPLOAD_DIR
        url = f"{self.__BT_PANEL}/files?action=GetDirNew"
        payload = self.__get_key_data()
        payload.update({
            'p': '1',
            'showRow': 500,
            'path': path,
            'sort': '',
            'reverse': 'True',
            'search': search
        })

        result = await self.http_post(url, payload)
        return result

    # 检查文件是否存在（异步）
    async def file_exists(self, filename: str, path: str = None):
        if path is None:
            path = bt_api.__UPLOAD_DIR
        url = f"{self.__BT_PANEL}/files?action=upload_files_exists"
        payload = self.__get_key_data()
        payload['files'] = f"{path}/{filename}"

        result = await self.http_post(url, payload)
        return result

    # 文件上传（异步）
    async def file_upload(self, file_path: str, path: str = None):
        if path is None:
            path = bt_api.__UPLOAD_DIR
        payload = self.__get_key_data()
        url = f"{self.__BT_PANEL}/files?action=upload"

        # 将签名参数添加到URL
        params = '&'.join([f"{k}={v}" for k, v in payload.items()])
        url = f"{url}&{params}"

        result = await self.http_multipart_post(url, file_path, path)
        return result

    # 获取文件内容（异步）
    async def get_file(self, filename: str, path: str = None):
        if path is None:
            path = bt_api.__UPLOAD_DIR
        payload = self.__get_key_data()
        url = f"{self.__BT_PANEL}/files?action=GetFileBody"

        payload["path"] = f"{path}/{filename}"

        result = await self.http_post(url, payload)
        return result

    # 计算MD5
    def __get_md5(self, s):
        m = hashlib.md5()
        m.update(s.encode('utf-8'))
        return m.hexdigest()

    # 构造带有签名的关联数组
    def __get_key_data(self):
        now_time = int(time.time())
        return {
            'request_token': self.__get_md5(str(now_time) + self.__get_md5(self.__BT_KEY)),
            'request_time': now_time
        }

    def chech_result(self, result):
        if isinstance(result, Dict) and "status" in result and not result.get("status"):
            logging.error(result.get("msg"))
            return None
        return result


if __name__ == '__main__':
    import asyncio


    async def main():
        # 请替换为实际的面板地址和密钥
        my_api = bt_api(
            bt_panel="https://你的面板地址:端口",
            bt_key="你的面板密钥",
            upload_dir="/www/wwwroot"
        )

        # 示例调用
        # logs = await my_api.get_logs()
        # print(json.dumps(logs, indent=2))

        exists = await my_api.file_exists("api_demo_python.zip")
        print(exists)

        # files = await my_api.search_files("")
        # print(files)

        # result = await my_api.file_upload("/Users/yasin/Downloads/api_demo_python.zip")
        # print(json.dumps(result, ensure_ascii=False, indent=2))

        # result = await my_api.get_file("jianying-1.0.0.json")
        # print(result.get("data"))


    # 运行异步主函数
    asyncio.run(main())