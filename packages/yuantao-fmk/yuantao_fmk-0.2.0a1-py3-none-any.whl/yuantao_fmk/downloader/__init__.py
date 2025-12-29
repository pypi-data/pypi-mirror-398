# Copyright (C) 2025 Tao Yuan
# This work is free. You can redistribute it and/or modify it under the
# terms of the Do What The Fuck You Want To Public License, Version 2,
# as published by Sam Hocevar. See http://www.wtfpl.net/ for more details.

import os
import shutil
from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Optional

import requests
import urllib3
from alive_progress import alive_bar
from hdfs import HdfsError
from urllib3.exceptions import InsecureRequestWarning

from yuantao_fmk import Config, logger

urllib3.disable_warnings(InsecureRequestWarning)

class DownloadError(Exception):
    def __init__(self, message: Optional[str] = None):
        self.message = message


class Downloader(ABC):
    """下载器抽象基类，包含进度条功能"""

    def __init__(self, chunk_size=8192, **kwargs):
        self.chunk_size = chunk_size  # 下载块大小

    @abstractmethod
    def _get_file_size(self, source_path):
        """获取远程文件大小（字节）"""
        pass

    @abstractmethod
    @contextmanager
    def _get_stream(self, source_path):
        """获取文件内容流的上下文管理器"""
        pass

    def download_file(self, source_path, destination_path):
        """下载文件并显示进度条，中断时自动清理未完成文件"""
        if Config.VERBOSE:
            logger.debug(f"Src: {source_path}")
            logger.debug(f"Dst: {destination_path}")
        # 定义临时文件路径（目标路径 + .tmp 后缀）
        temp_path = destination_path + ".tmp"
        completed = False  # 标记下载是否完成

        try:
            # 获取文件大小
            total_size = self._get_file_size(source_path)

            # 创建目标目录
            destination_dir = os.path.dirname(destination_path)
            if destination_dir and not os.path.exists(destination_dir):
                os.makedirs(os.path.dirname(destination_path), exist_ok=True)

            filename = os.path.basename(destination_path)

            # 使用alive-progress显示进度条
            with alive_bar(
                    total=total_size,
                    title=filename,
                    force_tty=True,
            ) as bar:
                bar.text('666')
                # 使用_get_stream返回的上下文管理器获取流
                with self._get_stream(source_path) as stream, open(
                        temp_path, "wb"
                ) as f:
                    for chunk in stream:
                        f.write(chunk)
                        bar(len(chunk))  # 更新进度条

            # 下载完成，重命名临时文件为目标文件
            shutil.move(temp_path, destination_path)
            completed = True  # 标记下载成功
        except DownloadError as e:
            logger.critical(e.message)
            exit(1)
        finally:
            # 如果未完成（被中断或出错），删除临时文件
            if not completed and os.path.exists(temp_path):
                os.remove(temp_path)

        return completed


class RequestsDownloader(Downloader):
    """使用requests库的HTTP下载器"""

    def __init__(self, session=None, **kwargs):
        super().__init__(**kwargs)

        self.session = session or requests.Session()
        self.headers = kwargs.get("headers", {})

    def _get_file_size(self, url):
        """通过HEAD请求获取文件大小"""
        try:
            with self.session.head(url, verify=False, headers=self.headers) as response:
                response.raise_for_status()
                return int(response.headers.get("Content-Length", 0))
        except requests.exceptions.HTTPError as e:
            raise DownloadError(e)

    @contextmanager
    def _get_stream(self, url):
        """获取HTTP响应流的上下文管理器"""
        response = self.session.get(
            url, stream=True, verify=False, headers=self.headers
        )
        response.raise_for_status()
        try:
            yield response.iter_content(chunk_size=self.chunk_size)
        finally:
            response.close()


class HdfsDownloader(Downloader):
    """HDFS文件下载器"""

    def __init__(self, client, **kwargs):
        super().__init__(**kwargs)
        self.client = client  # hdfs.Client实例

    def _get_file_size(self, hdfs_path):
        """获取HDFS文件大小"""
        try:
            file_info = self.client.status(hdfs_path)
            return file_info["length"]
        except HdfsError as e:
            raise DownloadError(e.message)

    @contextmanager
    def _get_stream(self, hdfs_path):
        """获取HDFS文件流的上下文管理器"""
        with self.client.read(hdfs_path, chunk_size=self.chunk_size) as reader:
            yield reader


class S3Downloader(Downloader):
    """AWS S3下载器"""

    def __init__(self, s3_client, bucket_name, **kwargs):
        super().__init__(**kwargs)
        self.s3 = s3_client
        self.bucket = bucket_name

    def _get_file_size(self, s3_key):
        """获取S3文件大小"""
        response = self.s3.head_object(Bucket=self.bucket, Key=s3_key)
        return response["ContentLength"]

    @contextmanager
    def _get_stream(self, s3_key):
        """获取S3文件流的上下文管理器"""
        response = self.s3.get_object(Bucket=self.bucket, Key=s3_key)
        try:
            yield response["Body"].iter_chunks(chunk_size=self.chunk_size)
        finally:
            response["Body"].close()
