#!/usr/bin/env python
# pylint: disable=E0401,W0718

"""
Coding: UTF-8
Author: Bitliker
Date: 2025/12/08
Version: 1.0.0
Description: 音频文件封装类
"""

import os
import logging
from typing import Optional
from .metadata import AudioMetadata
from .handlers.base import BaseHandler
from .handlers.mp3_handler import MP3Handler
from .handlers.flac_handler import FLACHandler
from .handlers.mp4_handler import MP4Handler
from .handlers.ogg_handler import OggHandler

logger = logging.getLogger(__name__)


def _fallback_save_with_music_tag(filepath: str, metadata: AudioMetadata) -> bool:
    """
    使用 music_tag 库作为备选方案保存元数据

    Args:
        filepath: 音频文件路径
        metadata: 元数据对象

    Returns:
        bool: 是否成功
    """
    try:
        import music_tag
    except ImportError:
        logger.warning("music_tag 库未安装，无法使用备选方案")
        return False

    try:
        file_tag = music_tag.load_file(filepath)

        if metadata.title:
            file_tag["tracktitle"] = metadata.title.strip()
        if metadata.artist:
            file_tag.remove_tag("artist")
            artists = metadata.artist if isinstance(metadata.artist, list) else [metadata.artist]
            for a in artists:
                file_tag.append_tag("artist", a.strip())
        if metadata.composer:
            file_tag["composer"] = metadata.composer.strip()
        if metadata.album_artist:
            file_tag["albumartist"] = metadata.album_artist
        if metadata.album:
            file_tag["album"] = metadata.album.strip()
        if metadata.genre:
            file_tag.remove_tag("genre")
            for g in metadata.genre:
                file_tag.append_tag("genre", g.strip())
        if metadata.year:
            file_tag["year"] = metadata.year
        if metadata.comment:
            file_tag["comment"] = metadata.comment.strip()
        if metadata.track_number:
            file_tag["tracknumber"] = metadata.track_number
        if metadata.total_tracks:
            file_tag["totaltracks"] = metadata.total_tracks
        if metadata.disc_number:
            file_tag["discnumber"] = metadata.disc_number
        if metadata.total_discs:
            file_tag["totaldiscs"] = metadata.total_discs
        if metadata.lyrics:
            file_tag["lyrics"] = metadata.lyrics
        if metadata.artwork:
            file_tag["artwork"] = metadata.artwork

        file_tag.save()
        logger.info("使用 music_tag 备选方案写入成功: %s", filepath)
        return True
    except Exception as e:
        logger.error("music_tag 备选方案写入失败: %s", e)
        return False


class AudioFile:
    """
    音频文件封装类，提供统一的元数据读写接口。
    自动识别文件格式并使用对应的处理器。
    """

    # 支持的文件扩展名映射
    SUPPORTED_FORMATS = {
        '.mp3': 'mp3',
        '.flac': 'flac',
        '.m4a': 'mp4',
        '.mp4': 'mp4',
        '.m4b': 'mp4',
        '.m4p': 'mp4',
        '.m4r': 'mp4',
        '.aac': 'mp4',
        '.ogg': 'ogg',
        '.opus': 'opus',
        '.oga': 'ogg',
    }

    def __init__(self, filepath: str):
        """
        初始化音频文件对象。

        Args:
            filepath: 音频文件路径
        """
        self.filepath = filepath
        self._handler: Optional[BaseHandler] = None
        self._metadata: Optional[AudioMetadata] = None
        self._load()

    def _load(self) -> None:
        """加载音频文件"""
        if not os.path.exists(self.filepath):
            raise FileNotFoundError(f"文件不存在: {self.filepath}")

        ext = os.path.splitext(self.filepath)[1].lower()
        format_type = self.SUPPORTED_FORMATS.get(ext)

        if format_type is None:
            raise ValueError(f"不支持的音频格式: {ext}")

        self._handler = self._create_handler(format_type)
        self._handler.load()
        self._metadata = self._handler.read()

    def _create_handler(self, format_type: str) -> BaseHandler:
        """根据格式类型创建对应的处理器"""
        if format_type == 'mp3':
            return MP3Handler(self.filepath)
        elif format_type == 'flac':
            return FLACHandler(self.filepath)
        elif format_type == 'mp4':
            return MP4Handler(self.filepath)
        elif format_type == 'ogg':
            return OggHandler(self.filepath, is_opus=False)
        elif format_type == 'opus':
            return OggHandler(self.filepath, is_opus=True)
        else:
            raise ValueError(f"未知的格式类型: {format_type}")

    @property
    def metadata(self) -> AudioMetadata:
        """获取元数据对象"""
        return self._metadata

    @metadata.setter
    def metadata(self, value: str):
        self._metadata = value
    # 属性访问器
    @property
    def title(self) -> Optional[str]:
        return self._metadata.title

    @title.setter
    def title(self, value: str):
        self._metadata.title = value

    @property
    def artist(self) -> Optional[str]:
        return self._metadata.artist

    @artist.setter
    def artist(self, value: str):
        self._metadata.artist = value

    @property
    def album(self) -> Optional[str]:
        return self._metadata.album

    @album.setter
    def album(self, value: str):
        self._metadata.album = value

    @property
    def album_artist(self) -> Optional[str]:
        return self._metadata.album_artist

    @album_artist.setter
    def album_artist(self, value: str):
        self._metadata.album_artist = value

    @property
    def year(self) -> Optional[str]:
        return self._metadata.year

    @year.setter
    def year(self, value: str):
        self._metadata.year = value

    @property
    def genre(self) -> list:
        return self._metadata.genre

    @genre.setter
    def genre(self, value: list):
        self._metadata.genre = value

    @property
    def track_number(self) -> Optional[int]:
        return self._metadata.track_number

    @track_number.setter
    def track_number(self, value: int):
        self._metadata.track_number = value

    @property
    def total_tracks(self) -> Optional[int]:
        return self._metadata.total_tracks

    @total_tracks.setter
    def total_tracks(self, value: int):
        self._metadata.total_tracks = value

    @property
    def disc_number(self) -> Optional[int]:
        return self._metadata.disc_number

    @disc_number.setter
    def disc_number(self, value: int):
        self._metadata.disc_number = value

    @property
    def total_discs(self) -> Optional[int]:
        return self._metadata.total_discs

    @total_discs.setter
    def total_discs(self, value: int):
        self._metadata.total_discs = value

    @property
    def lyrics(self) -> Optional[str]:
        return self._metadata.lyrics

    @lyrics.setter
    def lyrics(self, value: str):
        self._metadata.lyrics = value

    @property
    def composer(self) -> Optional[str]:
        return self._metadata.composer

    @composer.setter
    def composer(self, value: str):
        self._metadata.composer = value

    @property
    def comment(self) -> Optional[str]:
        return self._metadata.comment

    @comment.setter
    def comment(self, value: str):
        self._metadata.comment = value

    @property
    def artwork(self) -> Optional[bytes]:
        return self._metadata.artwork

    @artwork.setter
    def artwork(self, value: bytes):
        self._metadata.artwork = value

    def save(self, use_fallback: bool = True) -> bool:
        """
        保存元数据更改到文件

        Args:
            use_fallback: 主方案失败时是否使用 music_tag 备选方案

        Returns:
            bool: 是否保存成功
        """
        try:
            self._handler.write(self._metadata)
            self._handler.save()
            return True
        except Exception as e:
            logger.warning("主方案保存失败: %s", e)
            if use_fallback:
                logger.info("尝试使用 music_tag 备选方案...")
                return _fallback_save_with_music_tag(self.filepath, self._metadata)
            return False

    def set_artwork_from_file(self, image_path: str) -> None:
        """从文件设置封面图片"""
        with open(image_path, 'rb') as f:
            self._metadata.artwork = f.read()

    def save_artwork_to_file(self, output_path: str) -> bool:
        """将封面图片保存到文件"""
        if self._metadata.artwork is None:
            return False
        with open(output_path, 'wb') as f:
            f.write(self._metadata.artwork)
        return True

    def __repr__(self) -> str:
        return f"AudioFile('{self.filepath}')"

    def __str__(self) -> str:
        return f"{self.artist} - {self.title}" if self.artist and self.title else self.filepath
