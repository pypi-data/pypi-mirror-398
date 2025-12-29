#!/usr/bin/env python
# pylint: disable=E0401,W0718

"""
Coding: UTF-8
Author: Bitliker
Date: 2025/12/15 10:47:39
Version: 1.0.0
Description: 对外接口的api模型
"""
import dataclasses
from typing import Optional, Set


@dataclasses.dataclass
class ArtistBean:
    """作者实体类。
    Attributes:
        artist_id (Optional[str]): 作者ID
        name (Optional[str]): 作者名称
        avatar (Optional[str]): 作者头像
        org_avatar (Optional[str]): 作者原始头像
        website (Optional[str]): 作者网站
        intro (Optional[str]): 作者简介
    """

    artist_id: Optional[str] = None
    name: Optional[str] = None
    avatar: Optional[str] = None
    org_avatar: Optional[str] = None
    website: Optional[str] = None
    intro: Optional[str] = None


@dataclasses.dataclass
class AlbumBean:
    """专辑信息实体类
    Attributes:
        album_id (Optional[int]): 专辑ID
        title (Optional[str]): 专辑标题
        category (Optional[str]): 专辑分类
        artist (Optional[str]): 专辑作者
        cover (Optional[str]): 专辑封面
        intro (Optional[str]): 专辑简介

    """

    album_id: Optional[int] = None
    org_title: Optional[str] = None
    title: Optional[str] = None
    category: Optional[str] = None
    artist: Optional[ArtistBean] = None
    org_cover: Optional[str] = None
    cover: Optional[str] = None
    intro: Optional[str] = None
    is_finished: bool = False
    year: int = 2024
    create_at: Optional[str] = ""
    tags: list[str] = dataclasses.field(default_factory=list)
    track_count: int = 0


@dataclasses.dataclass
class TrackBean:
    """音轨详情实体类。"""

    track_id: Optional[str] = None
    org_title: Optional[str] = None
    title: Optional[str] = None
    artist: Optional[ArtistBean] = None
    category: Optional[str] = None
    cover: Optional[str] = None
    org_cover: Optional[str] = None
    link: Optional[str] = None
    play_url: Optional[str] = None
