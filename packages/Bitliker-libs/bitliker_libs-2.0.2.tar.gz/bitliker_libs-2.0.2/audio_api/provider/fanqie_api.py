#!/usr/bin/env python
# pylint: disable=E0401,W0718

"""
Coding: UTF-8
Author: Bitliker
Date: 2025/12/22 11:18:44
Version: 1.0.0
Description: 番茄api接口
"""
import os
import re
import time
from abc import abstractmethod
from typing import List, Optional, Dict, Any, Callable
import httpx
from ..models import AlbumBean, TrackBean, ArtistBean
from .provider import Provider

_RATE_LIMIT_ = 0.5  # 速率, 每秒可请求个数, 使用 time.sleep(xx) ; 比如 0.5/s


class FanqieApiProvider(Provider):
    """API 提供者抽象基类。"""

    def __init__(
        self,
        base_url: str,
        default_params: Dict[str, Any] = None,
        log_info: Optional[Callable[[str], None]] = None,
        log_error: Optional[Callable[[str], None]] = None,
    ):
        self._log_info = log_info or print
        self._log_error = log_error or print
        self._client = httpx.AsyncClient(
            base_url=base_url,
            params=default_params or {},
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/000000000 Safari/537.36"
            },
            timeout=10,
        )
        self._rate_limit = _RATE_LIMIT_

    async def __aenter__(self):
        """异步上下文管理器入口。"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口。"""
        await self.close()

    async def close(self):
        """关闭客户端。"""
        self._client.aclose()

    @property
    @abstractmethod
    def name(self) -> str:
        """获取 API 提供者名称。"""

    async def search_albums(self, keyword: str) -> List[AlbumBean]:
        """根据关键词搜索专辑列表。

        Args:
            keyword: 搜索关键词

        Returns:
            专辑列表
        """
        self._log_info(f"搜索专辑: {keyword}")
        ok, json_data = await self._requests("/", params={"name": keyword})
        time.sleep(1 / self._rate_limit)
        if ok:
            return []
        return self._parse_album_list(json_data.get("data", []))

    async def fetch_track_list(self, album_id: int) -> List[TrackBean]:
        """获取专辑的音轨列表。

        Args:
            album_id: 专辑 ID

        Returns:
            音轨列表
        """
        ok, json_data = await self._requests("/", params={"book_id": album_id})
        time.sleep(1 / self._rate_limit)
        if ok:
            return []
        return self._parse_track_list(json_data.get("data", []))

    def _parse_track_list(self, data: List[Dict[str, Any]]) -> List[TrackBean]:
        """解析音轨列表数据。"""
        tracks = []
        for item in data:
            track_id = item.get("item_id")
            if not track_id:
                continue
            org_title = item.get("title", "未知标题")
            tracks.append(
                TrackBean(
                    track_id=str(track_id),
                    title=self.filter_track_title(org_title),
                    org_title=org_title,
                )
            )
        return tracks

    async def fetch_track_detail(self, track_id: int) -> Optional[TrackBean]:
        """获取音轨详情。

        Args:
            track_id: 音轨 ID

        Returns:
            音轨详情，未找到返回 None
        """
        ok, json_data = await self._requests(
            "/", params={"item_id": track_id, "video_id": track_id}
        )
        time.sleep(1 / self._rate_limit)
        if ok:
            return None
        return self._parse_track_detail(track_id, json_data.get("data", {}))

    def _parse_track_detail(
        self, track_id: int, data: Dict[str, Any]
    ) -> Optional[TrackBean]:
        """解析音轨详情数据。"""
        self._log_info(f"获取音轨详情: {data}")
        if not data:
            return None
        org_cover = self.ensure_http(data.get("pic", ""))
        org_title = data.get("title", "未知标题")
        return TrackBean(
            track_id=str(track_id),
            title=self.filter_track_title(org_title),
            org_title=org_title,
            artist=ArtistBean(
                name=data.get("author", ""),
            ),
            category="Audiobook",
            cover=self.stable_picture(org_cover),
            org_cover=org_cover,
            link=data.get("url", ""),
            play_url=data.get("url", ""),
        )

    def _parse_album_list(self, data: List[Dict[str, Any]]) -> List[AlbumBean]:
        """解析专辑列表数据。"""
        albums = []
        for item in data:
            album_id = item.get("book_id")
            if not album_id:
                continue
            org_cover = item.get("cover", "")
            org_title = item.get("title", "未知标题")
            albums.append(
                AlbumBean(
                    album_id=album_id,
                    title=self.filter_album_title(org_title),
                    org_title=org_title,
                    category="Audiobook",
                    artist=ArtistBean(
                        name=item.get("author", "未知作者"),
                    ),
                    tags=item.get("intro", "").join(","),
                    org_cover=self.ensure_http(org_cover),
                    cover=self.stable_picture(org_cover),
                    intro=item.get("intro", ""),
                )
            )
        return albums

    def filter_album_title(self, org_album_title: str) -> str:
        """过滤专辑标题

        Args:
            org_album_title (str): 原始的标题

        Returns:
            str: 过滤后的标题
        """
        _title = org_album_title
        try:
            match = re.search(r"《([^》]+)》", org_album_title)
            if match:
                _title = match.group(1)
            if "|" in _title:
                _title = _title.split("|")[0]
            if "丨" in _title:
                _title = _title.split("丨")[0]
            if "【" in _title:
                _cache_title = re.sub(r"【.*】", "", _title)
                if _cache_title:
                    _title = _cache_title
            return self._remove_special_characters(_title)
        except Exception:  # pylint: disable=broad-except
            return _title

    def _remove_special_characters(self, _title: str) -> str:
        """去除特殊字符"""
        return (
            re.sub(r'[\\/*?:"<>|]', "", _title)
            .replace("%", "\\%")
            .replace("&", "&amp;")
            .strip()
        )

    def ensure_http(self, url: str) -> str:
        """补充http"""
        if not url:
            return ""
        url = url.strip()
        if url.startswith("//"):
            return "https:" + url
        if not re.match(r"^https?://", url, flags=re.I):
            return "https://" + url.lstrip("/")
        return url

    def stable_picture(self, cover: str) -> str:
        """将图片 URL 规范化。

        处理规则:
            - 确保带有协议（默认 https）
            - 若无 rows -> 添加 !op_type=3&columns=1080&rows=1080&magick=png
            - 若有 rows -> 强制 &columns=1080&rows=1080
            - 若无 magick -> 添加 &magick=png
            - 若有 magick -> 强制 magick=png

        Args:
            cover: 原始图片 URL

        Returns:
            规范化后的图片 URL
        """
        if not cover:
            return ""
        return self.ensure_http(cover)

    def filter_track_title(self, _title: str, _max_episode: int = 1000) -> str:
        """过滤标题内容 --> 提取简化标题

        Args:
            _title (str): 原始专辑名称
            _max_episode (int, optional): 最大集数. Defaults to 0.

        Returns:
            str: 过滤过后的名称
        """
        try:
            # 1. 过滤特殊字符 和垃圾字符
            _new_title = (
                self._remove_special_characters(_title)
                .replace("-点击订阅，不迷路", "")
                .replace("?", "?")
            )

            # 2. 提取特性内容
            _new_title = self._match_frist(
                _new_title,
                [
                    r".*(第\d+\s*.*)",
                    r"《([^》]+)》",
                ],
            )
            # 2. 提取 episode
            try:
                _episode = self._extract_first_number(file_name=_title)
                _new_episode = self._get_episode_name(
                    _episode, _max_episode=_max_episode
                )
                _new_title = _new_title.replace(_episode, _new_episode)
            except Exception:  # pylint: disable=broad-except
                self._log_error("解析报错")
            return _new_title
        except Exception:  # pylint: disable=broad-except
            return _title

    def _extract_first_number(self, file_name: str) -> str:
        """获取字符串的第一个数字

        Args:
            file_name (str): 输入内容

        Returns:
            str: 第一个数字 001 002 003 ... 100
        """
        numbers = re.findall(r"\d+", os.path.splitext(os.path.basename(file_name))[0])
        if numbers:
            return numbers[0]
        raise ImportError("No numbers found in the input string.")

    def _get_episode_name(self, _episode: str, _max_episode: int) -> str:
        """获取集数名称，1 - max_episode；补充 00 => 001

        Args:
            _episode (str): 集数
            _max_episode (int): 最大集数

        Returns:
            str: 1 -> 001
        """
        # 计算需要的零的个数
        num_zeros = len(str(_max_episode))
        # 使用 zfill 方法填充前导零
        episode_name = str(_episode).zfill(num_zeros)
        return episode_name

    def _match_frist(self, _msg: str, patterns: list) -> str:
        """正则处理并且提取第一个匹配内容

        Args:
            _msg (str): 信息
            patterns (list): 正则内容

        Returns:
            str: _description_
        """
        _new_msg = _msg
        for pattern in patterns:
            match = re.search(pattern, _new_msg)
            if match:
                _new_msg = match.group(1)
        return _new_msg

    async def fetch_album_detail(self, album_id: int) -> Optional[AlbumBean]:
        """获取详情

        Args:
            album_id (int): 专辑id

        Returns:
            Optional[AlbumBean]: 专辑信息
        """
        try:
            return None
        except Exception as e:  # pylint: disable=broad-except
            self._log_error(f"获取专辑详情失败[{album_id}] : {e}")
            return None

    async def _requests(self, url: str, params: dict) -> tuple[bool, dict[str, Any]]:
        """请求

        Args:
            url (str): 请求网址

        Returns:
            tuple[bool, dict[str, Any]]: 返回结果
        """
        try:
            response: httpx.Response = await self._client.get(url, params=params)
            if 200 <= response.status_code < 300:
                return True, response.json()
            self._log_error(f"请求失败: {response.status_code}, URL: {url}")
            return False, {}
        except httpx.RequestError as e:
            self._log_error(f"请求异常: {str(e)}, URL: {url}")
            return False, {}
        except Exception as e:
            self._log_error(f"解析响应异常: {str(e)}, URL: {url} params: {params}")
            return False, {}


class GuiguiFQApiProvider(FanqieApiProvider):
    """鬼鬼 API 提供者。

    API 地址: https://api.cenguigui.cn/api/tingshu
    """

    def __init__(
        self,
        log_info: Optional[Callable[[str], None]] = None,
        log_error: Optional[Callable[[str], None]] = None,
    ):
        super().__init__(
            base_url="https://api.cenguigui.cn/api/tingshu",
            default_params={},
            log_info=log_info,
            log_error=log_error,
        )

    @property
    def name(self) -> str:
        return "鬼鬼番茄API"


class LongzhuFQProvider(FanqieApiProvider):
    """龙珠 API 提供者。

    API 地址: https://sdkapi.hhlqilongzhu.cn/api/fanqie_tingshu
    """

    def __init__(
        self,
        api_key: str = "",
        log_info: Optional[Callable[[str], None]] = None,
        log_error: Optional[Callable[[str], None]] = None,
    ):
        super().__init__(
            base_url="https://sdkapi.hhlqilongzhu.cn/api/fanqie_tingshu",
            default_params={"key": api_key} if api_key else {},
            log_info=log_info,
            log_error=log_error,
        )

    @property
    def name(self) -> str:
        return "龙珠番茄API"
