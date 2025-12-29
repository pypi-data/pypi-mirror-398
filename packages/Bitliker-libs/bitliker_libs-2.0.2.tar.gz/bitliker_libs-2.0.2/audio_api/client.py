#!/usr/bin/env python
# pylint: disable=E0401,W0718

"""
Coding: UTF-8
Author: Bitliker
Date: 2025/12/15 11:09:11
Version: 1.0.0
Description: api 客户端入口
"""
from typing import List, Optional, Callable
from .provider import (
    Provider,
    LongzhuProvider,
    GuiguiApiProvider,
    LongzhuFQProvider,
    GuiguiFQApiProvider,
)
from .models import (
    AlbumBean,
    TrackBean,
)


class ApiClient:
    """Api客户端"""

    def __init__(
        self,
        longzhu_key: str = "",
        provider: str = "xmly",
        log_info: Optional[Callable[[str], None]] = None,
        log_error: Optional[Callable[[str], None]] = None,
    ):
        """初始化客户端。"""
        self._log_info = log_info or (lambda x: None)
        self._log_error = log_error or (lambda x: None)
        # 初始化 API 提供者列表（龙珠优先）
        self._providers: List[Provider] = []
        is_xmly = provider == "xmly"
        if longzhu_key:
            self._providers.append(
                LongzhuProvider(
                    api_key=longzhu_key, log_info=log_info, log_error=log_error
                )
                if is_xmly
                else LongzhuFQProvider(
                    api_key=longzhu_key, log_info=log_info, log_error=log_error
                )
            )
        self._providers.append(
            GuiguiApiProvider(log_info=log_info, log_error=log_error)
            if is_xmly
            else GuiguiFQApiProvider(log_info=log_info, log_error=log_error)
        )
        for provider in self._providers:
            self._log_info(f"初始化 API 提供者: {provider.name}")

    async def __aenter__(self):
        """异步上下文管理器入口。"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口。"""
        await self.close()

    async def close(self):
        """关闭客户端。"""
        for provider in self._providers:
            await provider.close()

    async def search_albums(self, keyword: str) -> List[AlbumBean]:
        """根据关键词搜索专辑列表。

        自动在多个 API 源之间切换，直到获取成功。

        Args:
            keyword: 搜索关键词

        Returns:
            专辑列表，失败返回空列表
        """
        albums = await self._try_providers(
            lambda p: p.search_albums(keyword), f"搜索专辑 '{keyword}'"
        )
        # 过滤专辑标题
        return albums

    async def fetch_track_list(self, album_id: int) -> List[TrackBean]:
        """获取专辑的音轨列表。

        自动在多个 API 源之间切换，直到获取成功。

        Args:
            album_id: 专辑 ID

        Returns:
            音轨列表，失败返回空列表
        """
        return await self._try_providers(
            lambda p: p.fetch_track_list(album_id),
            f"获取专辑音轨列表 album_id={album_id}",
        )

    async def fetch_track_detail(self, track_id: int) -> Optional[TrackBean]:
        """获取音轨详情。

        自动在多个 API 源之间切换，直到获取成功。

        Args:
            track_id: 音轨 ID

        Returns:
            音轨详情，失败返回 None
        """
        track_detail = await self._try_providers(
            lambda p: p.fetch_track_detail(track_id),
            f"获取音轨详情 track_id={track_id}",
        )
        return track_detail

    async def fetch_album_detail(self, album_id: int) -> Optional[AlbumBean]:
        """获取专辑详情（使用官方 API）。

        Args:
            album_id: 专辑 ID

        Returns:
            专辑详情，失败返回 None
        """
        album_detail = await self._try_providers(
            lambda p: p.fetch_album_detail(album_id),
            f"获取音轨详情 track_id={album_id}",
        )
        return album_detail

    async def _try_providers(self, func, operation: str):
        """尝试使用多个 API 提供者执行操作。

        Args:
            func: 要执行的异步函数，接收 ApiProvider 参数
            operation: 操作描述（用于日志）

        Returns:
            操作结果，所有提供者都失败时返回空列表或 None
        """
        for provider in self._providers:
            try:
                self._log_info(f"[{provider.name}] 正在{operation}")
                result = await func(provider)
                if result:
                    self._log_info(f"[{provider.name}] {operation}成功")
                    return result
                self._log_info(f"[{provider.name}] {operation}返回空结果，尝试下一个")
            except Exception as e:
                self._log_error(f"[{provider.name}] {operation}失败: {e}")

        self._log_error(f"所有 API 源均失败: {operation}")
        return [] if "列表" in operation or "搜索" in operation else None
