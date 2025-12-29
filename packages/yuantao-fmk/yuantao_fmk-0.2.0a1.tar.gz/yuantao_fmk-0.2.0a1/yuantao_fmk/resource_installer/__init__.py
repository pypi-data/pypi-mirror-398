# Copyright (C) 2025 Tao Yuan
# This work is free. You can redistribute it and/or modify it under the
# terms of the Do What The Fuck You Want To Public License, Version 2,
# as published by Sam Hocevar. See http://www.wtfpl.net/ for more details.

import os
import shutil
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import List, Optional

from yuantao_fmk.downloader import Downloader, RequestsDownloader
from yuantao_fmk import Config, logger


class InstallerMode(Enum):
    """资源安装器运行模式枚举类。

    DDII: 全部下载后安装
    DIDI: 逐个资源下载后安装
    DO:   只下载，不安装
    """

    DDII = auto()
    DIDI = auto()
    DO = auto()


class InstallerBase(ABC):
    """资源安装器基类。

    提供通用的资源下载、预安装、安装和后处理方法，具体的资源管理逻辑由子类实现。
    """

    resource_downloader: Downloader

    def __init__(
        self,
        version: str,
        resource_type: str,
        resource_tags: List[str],
        download_path: str,
    ):
        """初始化资源安装器。

        参数:
            version (str): 资源版本号
            resource_type (str): 资源类型
            resource_tags (List[str]): 所需资源的标签列表
            download_path (str): 资源包下载保存路径
        """
        super().__init__()
        self.version = self.get_real_version(version)
        self.original_version = version
        self.resource_type = resource_type
        self.resource_tags = resource_tags
        self.download_path = download_path

    def get_real_version(self, original_version: str):
        """获取实际使用的版本号。可根据需要重载实现版本映射。

        参数:
            original_version (str): 原始版本号字符串

        返回:
            str: 实际使用的版本号
        """
        return original_version

    @abstractmethod
    def get_resource_filename(self, resource_tag: Optional[str]) -> str:
        """获取指定资源标签所对应的文件名。

        参数:
            resource_tag (Optional[str]): 资源标签

        返回:
            str: 文件名
        """
        pass

    @abstractmethod
    def get_resource_remote_location(self, resource_tag: Optional[str]) -> str:
        """获取指定资源标签远程存储目录的路径。

        参数:
            resource_tag (Optional[str]): 资源标签

        返回:
            str: 远程目录路径
        """
        pass

    def get_resource_remote_filename(self, resource_tag: Optional[str]) -> str:
        """获取资源标签远程文件名（默认直接与本地文件名一致）。

        参数:
            resource_tag (Optional[str]): 资源标签

        返回:
            str: 文件名
        """
        return self.get_resource_filename(resource_tag)

    @abstractmethod
    def get_resource_local_location(self, resource_tag: Optional[str]) -> str:
        """获取指定资源标签本地存储目录的路径。

        参数:
            resource_tag (Optional[str]): 资源标签

        返回:
            str: 本地存储路径
        """
        pass

    def get_resource_local_filename(self, resource_tag: Optional[str]) -> str:
        """获取本地文件名（默认直接与资源文件名一致）。

        参数:
            resource_tag (Optional[str]): 资源标签

        返回:
            str: 文件名
        """
        return self.get_resource_filename(resource_tag)

    def get_resource_remote_url(self, resource_tag: Optional[str]):
        """获取资源标签的完整远程URL。

        参数:
            resource_tag (Optional[str]): 资源标签

        返回:
            str: 远程完整URL
        """
        return (
            self.get_resource_remote_location(resource_tag).rstrip("/")
            + "/"
            + self.get_resource_remote_filename(resource_tag)
        )

    def get_resource_local_url(self, resource_tag: Optional[str]):
        """获取资源标签的本地完整文件路径。

        参数:
            resource_tag (Optional[str]): 资源标签

        返回:
            str: 本地完整路径
        """
        return os.path.join(
            self.get_resource_local_location(resource_tag),
            self.get_resource_local_filename(resource_tag),
        )

    def get_downloader(self) -> Downloader:
        """获取用于下载资源的 Downloader 对象。

        返回:
            Downloader: 用于资源下载的对象
        """
        return RequestsDownloader()

    def download_resource(
        self, resource_tag: Optional[str], download_path: Optional[str] = None
    ):
        """下载指定资源（如本地已存在，则跳过）。

        参数:
            resource_tag (Optional[str]): 资源标签
            download_path (Optional[str]): 指定下载目标路径（如不指定则用默认路径）

        返回:
            str: 资源包本地路径
        """
        package_storage_filename = self.get_resource_local_url(resource_tag)
        if os.path.exists(package_storage_filename):
            logger.info(f"{resource_tag} package file already exists.")
            return None
        if download_path is None:
            download_path = self.get_resource_local_location(resource_tag)
        logger.info(f"Start to download {resource_tag} package to {download_path}")
        if Config.DRYRUN:
            logger.debug(
                f"Dryrun: download {self.get_resource_remote_url(resource_tag)} to {package_storage_filename}"
            )
        else:
            logger.info(f"Downloading {self.get_resource_filename(resource_tag)}...")
            self.get_downloader().download_file(
                self.get_resource_remote_url(resource_tag), package_storage_filename
            )
            logger.info(
                f"Downloaded {resource_tag} package to {package_storage_filename}"
            )
        return package_storage_filename

    def clean(self):
        """清空当前版本的包的下载路径。

        删除下载目录并重建空目录。
        """
        shutil.rmtree(self.download_path)
        os.makedirs(self.download_path, exist_ok=True)

    def pre_install_all(self, target_path: Optional[str]):
        """所有资源安装之前的操作。

        参数:
            target_path (Optional[str]): 目标安装路径
        """
        pass

    def pre_install(self, resource_tag: Optional[str], target_path: Optional[str]):
        """单个资源安装前的操作。

        参数:
            resource_tag (Optional[str]): 资源标签
            target_path (Optional[str]): 目标安装路径
        """
        pass

    def post_install(self, resource_tag: Optional[str], target_path: Optional[str]):
        """单个资源安装后的操作。

        参数:
            resource_tag (Optional[str]): 资源标签
            target_path (Optional[str]): 目标安装路径
        """
        pass

    def post_install_all(self, target_path: Optional[str]):
        """所有资源安装之后的操作。

        参数:
            target_path (Optional[str]): 目标安装路径
        """
        pass

    @abstractmethod
    def install_resource(self, resource_tag: Optional[str], target_path: Optional[str]):
        """执行单个资源安装的抽象方法，应在子类中实现具体的安装逻辑。

        参数:
            resource_tag (Optional[str]): 资源标签
            target_path (Optional[str]): 目标安装路径
        """
        pass

    def download_and_install_all_resource(
        self, target_path: Optional[str], mode: InstallerMode = InstallerMode.DDII
    ):
        """批量下载并安装所有资源的主流程。

        参数:
            target_path (Optional[str]): 资源的安装目标目录
            mode (InstallerMode, 可选): 安装模式，可选为DDII、DIDI、DO，默认DDII。

        主要流程如下：
            - DDII/DO: 先下载全部资源；DO模式只下载不安装；否则继续做批量预处理和批量安装
            - DIDI: 先批量做预处理，逐条下载和安装资源，安装后做批量后处理
        """
        if mode == InstallerMode.DDII or mode == InstallerMode.DO:
            for resource_tag in self.resource_tags:
                self.download_resource(resource_tag, self.download_path)
            self.pre_install_all(target_path)
            if mode == InstallerMode.DO:
                return
            for resource_tag in self.resource_tags:
                self.pre_install(resource_tag, target_path)
                self.install_resource(resource_tag, target_path)
                self.post_install(resource_tag, target_path)
            self.post_install_all(target_path)
        elif mode == InstallerMode.DIDI:
            self.pre_install_all(target_path)
            for resource_tag in self.resource_tags:
                self.download_resource(resource_tag, self.download_path)
                self.pre_install(resource_tag, target_path)
                self.install_resource(resource_tag, target_path)
                self.post_install(resource_tag, target_path)
            self.post_install_all(target_path)
