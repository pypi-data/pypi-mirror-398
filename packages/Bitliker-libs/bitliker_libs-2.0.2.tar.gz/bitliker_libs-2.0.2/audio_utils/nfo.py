#!/usr/bin/env python
# pylint: disable=E0401,W0718

"""
Coding: UTF-8
Author: Bitliker
Date: 2025/12/15 14:40:51
Version: 1.0.0
Description: nfo 处理类
"""
import os
import xml.etree.ElementTree as ET
from audio_api import AlbumBean, ArtistBean


def create_artist_nfo(_artist_nfo_path: str, artist: ArtistBean) -> bool:
    """创建艺术家 nfo 文件
    <?xml version="1.0" encoding="UTF-8"?>
    <artist>
        <name>艺术家名称</name>
        <sortname>排序名称</sortname>
        <bio><![CDATA[简介]]></bio>
        <genre>音乐风格</genre>
        <yearsactive>活跃年份（如 1960-1970）</yearsactive>
        <!-- 主唱Thom Yorke生日 -->
        <born>生日(如 1968-10-07, 牛津, 英国)</born>
        <died>去世信息 (如 2020-01-01, 纽约)</died>
        <thumb>头像路径</thumb>
        <fanart>背景图路径</fanart>
    </artist>
    """
    if os.path.exists(_artist_nfo_path):
        return True
    if not artist:
        return False
    try:
        _nfo_info = '<?xml version="1.0" encoding="UTF-8"?>\n'
        _nfo_info += "<artist>\n"
        _nfo_info += f"\t<artist_id>{artist.artist_id}</artist_id>\n"
        _nfo_info += f"\t<name>{artist.name}</name>\n"
        _nfo_info += f"\t<sortname>{artist.name}</sortname>\n\n"
        if artist.intro:
            _nfo_info += f"\t<bio><![CDATA[{artist.intro}]]></bio>\n"
            _nfo_info += f"\t<description><![CDATA[{artist.intro}]]></description>\n"
            _nfo_info += f"\t<biography>{artist.intro}</biography>\n\n"

        _nfo_info += f"\t<thumb>{artist.avatar}</thumb>\n"
        _nfo_info += f"\t<fanart>{artist.org_avatar}</fanart>\n"
        _nfo_info += f"\t<website>{artist.website}</website>\n"
        _nfo_info += f"\t<xmly>{artist.artist_id}</xmly>\n"
        _nfo_info += "</artist>"
        with open(_artist_nfo_path, "w", encoding="utf-8") as f:
            f.write(_url_code(_nfo_info))
        return os.path.exists(_artist_nfo_path)
    except Exception as e:
        print(e)
        return False


def read_artist_nfo(nfo_file_path: str) -> ArtistBean:
    """
    从.nfo文件读取艺术家信息，并转换为ArtistBean对象

    Args:
        nfo_file_path (str): .nfo文件路径

    Returns:
        ArtistBean: 包含艺术家信息的对象
    """
    # 检查文件是否存在
    if not os.path.exists(nfo_file_path):
        return None

    try:
        # 解析XML文件
        tree = ET.parse(nfo_file_path)
        root = tree.getroot()

        # 提取信息
        artist_id = root.findtext("artist_id", "")
        name = root.findtext("name", "")
        intro = (
            root.findtext("bio", "")
            or root.findtext("description", "")
            or root.findtext("biography", "")
        )
        avatar = root.findtext("thumb", "")
        org_avatar = root.findtext("fanart", "")
        website = root.findtext("website", "")

        # 创建ArtistBean实例
        artist_bean = ArtistBean(
            artist_id=artist_id,
            name=name,
            intro=intro,
            avatar=avatar,
            org_avatar=org_avatar,
            website=website,
        )

        return artist_bean
    except Exception as e:
        print(f"读取艺术家nfo文件出错: {e}")
        return None


def create_album_nfo(_album_nfo_path: str, album_detail: AlbumBean) -> bool:
    """创建专辑 nfo 文件


    Args:
        _album_nfo_path (str): nfo 文件路径
        _xmly_info (XmlyAlbumInfo): 专辑相关信息

    Returns:
        bool: 是否完成创建
    """
    _nfo_info = '<?xml version="1.0" encoding="UTF-8"?>\n'
    _nfo_info += "<album>\n"
    _nfo_info += f"\t<album_id>{album_detail.album_id}</album_id>\n"
    _nfo_info += f"\t<org_title>{album_detail.org_title}</org_title>\n"
    _nfo_info += f"\t<title>{album_detail.title}</title>\n"
    if album_detail.artist:
        _nfo_info += f"\t<artist_id>{album_detail.artist.artist_id}</artist_id>\n"
        _nfo_info += f"\t<artist>{album_detail.artist.name}</artist>\n"
        _nfo_info += f"\t<artist_avatar>{album_detail.artist.avatar}</artist_avatar>\n"
        _nfo_info += f"\t<artist_org_avatar>{album_detail.artist.org_avatar}</artist_org_avatar>\n"
        _nfo_info += (
            f"\t<artist_website>{album_detail.artist.website}</artist_website>\n"
        )
        _nfo_info += f"\t<artist_intro>{album_detail.artist.website}</artist_intro>\n"
    _nfo_info += f"\t<year>{album_detail.year}</year>\n"
    _nfo_info += f"\t<releasedate>{album_detail.create_at}</releasedate>\n"
    genres = ", ".join(album_detail.tags)
    _nfo_info += f"\t<genre>{genres}</genre>\n"
    if album_detail.intro:
        _nfo_info += f"\t<description><![CDATA[{album_detail.intro}]]></description>\n"
        _nfo_info += f"\t<shortdescription>{album_detail.intro}</shortdescription>\n"
    _nfo_info += f"\t<thumb>{album_detail.cover}</thumb>\n"
    _nfo_info += f"\t<fanart>{album_detail.org_cover}</fanart>\n"
    _nfo_info += f"\t<xmly>{album_detail.cover}</xmly>\n"
    _nfo_info += f"\t<category>{album_detail.category}</category>\n"
    _nfo_info += f"\t<is_finished>{album_detail.is_finished}</is_finished>\n"
    _nfo_info += f"\t<track_count>{album_detail.track_count}</track_count>\n"
    _nfo_info += "</album>"
    with open(_album_nfo_path, "w", encoding="utf-8") as f:
        f.write(_url_code(_nfo_info))
    return os.path.exists(_album_nfo_path)


def _url_code(_url: str) -> str:
    """URL编码解码"""
    return _url.replace("%", "\\%").replace("&", "&amp;")


def read_album_nfo(nfo_file_path: str) -> AlbumBean:
    """
    从.nfo文件读取专辑信息，并转换为AlbumBean对象

    Args:
        nfo_file_path (str): .nfo文件路径

    Returns:
        AlbumBean: 包含专辑信息的对象
    """
    # 检查文件是否存在
    if not os.path.exists(nfo_file_path):
        return None

    try:
        # 解析XML文件
        tree = ET.parse(nfo_file_path)
        root = tree.getroot()

        # 提取基础专辑信息
        album_id = root.findtext("album_id", "")
        org_title = root.findtext("org_title", "")
        title = root.findtext("title", "")
        year = root.findtext("year", "")
        create_at = root.findtext("releasedate", "")
        cover = root.findtext("thumb", "")
        org_cover = root.findtext("fanart", "")
        category = root.findtext("category", "")
        is_finished_str = root.findtext("is_finished", "False")
        track_count_str = root.findtext("track_count", "0")

        # 转换数据类型
        is_finished = is_finished_str.lower() == "true"
        track_count = int(track_count_str) if track_count_str.isdigit() else 0

        # 提取简介信息
        intro = root.findtext("description", "") or root.findtext(
            "shortdescription", ""
        )

        # 提取标签信息
        genre_text = root.findtext("genre", "")
        tags = [tag.strip() for tag in genre_text.split(",")] if genre_text else []

        # 提取艺术家信息
        artist = None
        artist_id = root.findtext("artist_id", "")
        artist_name = root.findtext("artist", "")
        if artist_id and artist_name:
            artist_avatar = root.findtext("artist_avatar", "")
            artist_org_avatar = root.findtext("artist_org_avatar", "")
            artist_website = root.findtext("artist_website", "")

            # 创建ArtistBean实例
            artist = ArtistBean(
                artist_id=artist_id,
                name=artist_name,
                avatar=artist_avatar,
                org_avatar=artist_org_avatar,
                website=artist_website,
            )

        # 创建AlbumBean实例
        album_bean = AlbumBean(
            album_id=album_id,
            org_title=org_title,
            title=title,
            artist=artist,
            year=year,
            create_at=create_at,
            tags=tags,
            intro=intro,
            cover=cover,
            org_cover=org_cover,
            category=category,
            is_finished=is_finished,
            track_count=track_count,
        )

        return album_bean
    except Exception as e:
        print(f"读取专辑nfo文件出错: {e}")
        return None
