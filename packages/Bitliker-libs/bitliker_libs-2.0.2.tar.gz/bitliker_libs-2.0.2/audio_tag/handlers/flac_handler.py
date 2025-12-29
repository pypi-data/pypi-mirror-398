#!/usr/bin/env python
# pylint: disable=E0401,W0718

"""
Coding: UTF-8
Author: Bitliker
Date: 2025/12/08
Version: 1.0.0
Description: FLAC 文件处理器
"""

from typing import List
from mutagen.flac import FLAC, Picture
from .base import BaseHandler
from ..metadata import AudioMetadata


class FLACHandler(BaseHandler):
    """FLAC 文件处理器"""

    def load(self) -> None:
        self._file = FLAC(self.filepath)

    def read(self) -> AudioMetadata:
        tags = self._file.tags
        if tags is None:
            tags = {}

        track_num, total_tracks = self._parse_track_number(
            self._get_first_value(tags.get('tracknumber'))
        )
        disc_num, total_discs = self._parse_disc_number(
            self._get_first_value(tags.get('discnumber'))
        )

        # 获取封面
        artwork = None
        if self._file.pictures:
            artwork = self._file.pictures[0].data

        # 获取流派列表
        genre = self._parse_genre(tags.get('genre'))

        return AudioMetadata(
            title=self._get_first_value(tags.get('title')),
            artist=self._get_first_value(tags.get('artist')),
            album=self._get_first_value(tags.get('album')),
            album_artist=self._get_first_value(tags.get('albumartist')),
            year=self._get_first_value(tags.get('date')),
            genre=genre,
            track_number=track_num,
            total_tracks=total_tracks or self._safe_int(tags.get('totaltracks')),
            disc_number=disc_num,
            total_discs=total_discs or self._safe_int(tags.get('totaldiscs')),
            lyrics=self._get_first_value(tags.get('lyrics')),
            composer=self._get_first_value(tags.get('composer')),
            comment=self._get_first_value(tags.get('comment')),
            artwork=artwork,
        )

    def _parse_genre(self, genres) -> List[str]:
        """解析流派标签"""
        if genres is None:
            return []
        return list(genres)

    def _safe_int(self, value) -> int:
        """安全转换为整数"""
        v = self._get_first_value(value)
        return int(v) if v else None

    def write(self, metadata: AudioMetadata) -> None:
        if metadata.title is not None:
            self._file['title'] = metadata.title
        if metadata.artist is not None:
            self._file['artist'] = metadata.artist
        if metadata.album is not None:
            self._file['album'] = metadata.album
        if metadata.album_artist is not None:
            self._file['albumartist'] = metadata.album_artist
        if metadata.year is not None:
            self._file['date'] = metadata.year
        if metadata.genre:
            self._file['genre'] = list(metadata.genre)
        if metadata.composer is not None:
            self._file['composer'] = metadata.composer
        if metadata.comment is not None:
            self._file['comment'] = metadata.comment
        if metadata.lyrics is not None:
            self._file['lyrics'] = metadata.lyrics

        if metadata.track_number is not None:
            self._file['tracknumber'] = str(metadata.track_number)
        if metadata.total_tracks is not None:
            self._file['totaltracks'] = str(metadata.total_tracks)
        if metadata.disc_number is not None:
            self._file['discnumber'] = str(metadata.disc_number)
        if metadata.total_discs is not None:
            self._file['totaldiscs'] = str(metadata.total_discs)

        # 封面
        if metadata.artwork is not None:
            picture = Picture()
            picture.type = 3
            picture.mime = 'image/jpeg'
            picture.desc = 'Cover'
            picture.data = metadata.artwork
            self._file.clear_pictures()
            self._file.add_picture(picture)

    def save(self) -> None:
        self._file.save()
