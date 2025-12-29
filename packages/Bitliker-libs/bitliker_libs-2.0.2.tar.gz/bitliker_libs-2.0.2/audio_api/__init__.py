#!/usr/bin/env python
# pylint: disable=E0401,W0718

"""
Coding: UTF-8
Author: Bitliker
Date: 2025/12/15 10:46:29
Version: 1.0.0
Description: 第三方接口入口
依赖:
httpx

使用:
import asyncio
from bit_xly import ApiClient, AlbumBean, TrackBean, ArtistBean
async def main():
    client = ApiClient(
        longzhu_key="",
        log_info=print,
        log_error=print,
    )
    # albums: list[AlbumBean] = await client.search_albums("贝乐虎")
    # tracks: list[TrackBean] = await client.fetch_track_list("79314710")
    # track: TrackBean = await client.fetch_track_detail("687883523")
    # album = await client.fetch_album_detail(album_id=6233693)
"""
from .client import ApiClient
from .models import AlbumBean, TrackBean, ArtistBean
from .nfo import NfoHandler


__all__ = [
    "ApiClient",
    "NfoHandler",
    "AlbumBean",
    "TrackBean",
    "ArtistBean",
]
