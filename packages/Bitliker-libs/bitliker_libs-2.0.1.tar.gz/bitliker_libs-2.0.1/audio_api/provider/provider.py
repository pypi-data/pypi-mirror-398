#!/usr/bin/env python
# pylint: disable=E0401,W0718

"""
Coding: UTF-8
Author: Bitliker
Date: 2025/12/22 11:20:07
Version: 1.0.0
Description: Provider 接口
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from ..models import AlbumBean, TrackBean


class Provider(ABC):
    """
    Provider 抽象类
    """

    @abstractmethod
    async def close(self):
        """关闭客户端。"""

    @property
    @abstractmethod
    def name(self) -> str:
        """获取 API 提供者名称。"""

    @abstractmethod
    async def search_albums(self, keyword: str) -> List[AlbumBean]:
        """根据关键词搜索专辑列表。

        Args:
            keyword: 搜索关键词

        Returns:
            专辑列表
        """

    async def fetch_track_list(self, album_id: int) -> List[TrackBean]:
        """获取专辑的音轨列表。

        Args:
            album_id: 专辑 ID

        Returns:
            音轨列表
        """

    async def fetch_track_detail(self, track_id: int) -> Optional[TrackBean]:
        """获取音轨详情。

        Args:
            track_id: 音轨 ID

        Returns:
            音轨详情，未找到返回 None
        """

    async def fetch_album_detail(self, album_id: int) -> Optional[AlbumBean]:
        """获取专辑详情（使用官方 API）。

        Args:
            album_id: 专辑 ID

        Returns:
            专辑详情，失败返回 None
        """
