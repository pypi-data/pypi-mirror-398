#!/usr/bin/env python
# pylint: disable=E0401,W0718

"""
Coding: UTF-8
Author: Bitliker
Date: 2025/12/08 09:16:25
Version: 1.0.0
Description: 标签
"""


from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class AudioMetadata:
    """
    统一的音频元数据实体类。
    所有字段默认为 None，表示未设置或读取时不存在。
    """
    # 专辑
    album: Optional[str] = None
    # 标题
    title: Optional[str] = None
    # 艺术家
    artist: Optional[str] = None
    # 专辑艺术家
    album_artist: Optional[str] = None
    # 年份
    year: Optional[str] = None
    # 评论
    comment: Optional[str] = None
    # 作词人
    composer: Optional[str] = None
    lyrics: Optional[str] = None
    # 音轨 number
    track_number: Optional[int] = None
    total_tracks: Optional[int] = None
    # disc number
    disc_number: Optional[int] = None
    total_discs: Optional[int] = None
    # 风格
    genre: Optional[List[str]] = field(default_factory=list)
    # 简单的封面图片处理 (二进制数据)
    artwork: Optional[bytes] = field(default=None, repr=False)
