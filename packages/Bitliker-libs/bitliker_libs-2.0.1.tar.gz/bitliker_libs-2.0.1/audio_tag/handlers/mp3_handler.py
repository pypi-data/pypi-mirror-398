#!/usr/bin/env python
# pylint: disable=E0401,W0718

"""
Coding: UTF-8
Author: Bitliker
Date: 2025/12/08
Version: 1.0.0
Description: MP3 文件处理器 (ID3)
"""

from typing import List, Optional
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TPE2, TDRC, TCON, TRCK, TPOS, USLT, TCOM, COMM, APIC
from mutagen.mp3 import MP3
from .base import BaseHandler
from ..metadata import AudioMetadata


class MP3Handler(BaseHandler):
    """MP3 文件处理器"""

    def load(self) -> None:
        self._file = MP3(self.filepath)
        if self._file.tags is None:
            self._file.add_tags()

    def read(self) -> AudioMetadata:
        tags = self._file.tags
        if tags is None:
            return AudioMetadata()

        track_num, total_tracks = self._parse_track_number(
            self._get_first_value(tags.get('TRCK'))
        )
        disc_num, total_discs = self._parse_disc_number(
            self._get_first_value(tags.get('TPOS'))
        )

        # 获取歌词
        lyrics = None
        for key in tags.keys():
            if key.startswith('USLT'):
                lyrics = str(tags[key])
                break

        # 获取评论
        comment = None
        for key in tags.keys():
            if key.startswith('COMM'):
                comment = str(tags[key])
                break

        # 获取封面
        artwork = None
        for key in tags.keys():
            if key.startswith('APIC'):
                artwork = tags[key].data
                break

        # 获取流派列表
        genre = self._parse_genre(tags.get('TCON'))

        return AudioMetadata(
            title=self._get_first_value(tags.get('TIT2')),
            artist=self._get_first_value(tags.get('TPE1')),
            album=self._get_first_value(tags.get('TALB')),
            album_artist=self._get_first_value(tags.get('TPE2')),
            year=self._get_first_value(tags.get('TDRC')),
            genre=genre,
            track_number=track_num,
            total_tracks=total_tracks,
            disc_number=disc_num,
            total_discs=total_discs,
            lyrics=lyrics,
            composer=self._get_first_value(tags.get('TCOM')),
            comment=comment,
            artwork=artwork,
        )

    def _parse_genre(self, tcon) -> List[str]:
        """解析流派标签"""
        if tcon is None:
            return []
        genres = []
        for genre in tcon.genres:
            genres.append(str(genre))
        return genres

    def write(self, metadata: AudioMetadata) -> None:
        tags = self._file.tags

        if metadata.title is not None:
            tags['TIT2'] = TIT2(encoding=3, text=metadata.title)
        if metadata.artist is not None:
            tags['TPE1'] = TPE1(encoding=3, text=metadata.artist)
        if metadata.album is not None:
            tags['TALB'] = TALB(encoding=3, text=metadata.album)
        if metadata.album_artist is not None:
            tags['TPE2'] = TPE2(encoding=3, text=metadata.album_artist)
        if metadata.year is not None:
            tags['TDRC'] = TDRC(encoding=3, text=metadata.year)
        if metadata.genre:
            print(metadata.genre)
            print(list(metadata.genre))
            tags['TCON'] = TCON(encoding=3, text=list(metadata.genre))
        if metadata.composer is not None:
            tags['TCOM'] = TCOM(encoding=3, text=metadata.composer)

        # 音轨号
        if metadata.track_number is not None:
            track_str = str(metadata.track_number)
            if metadata.total_tracks is not None:
                track_str += f'/{metadata.total_tracks}'
            tags['TRCK'] = TRCK(encoding=3, text=track_str)

        # 碟片号
        if metadata.disc_number is not None:
            disc_str = str(metadata.disc_number)
            if metadata.total_discs is not None:
                disc_str += f'/{metadata.total_discs}'
            tags['TPOS'] = TPOS(encoding=3, text=disc_str)

        # 歌词
        if metadata.lyrics is not None:
            tags['USLT::eng'] = USLT(encoding=3, lang='eng', desc='', text=metadata.lyrics)

        # 评论
        if metadata.comment is not None:
            tags['COMM::eng'] = COMM(encoding=3, lang='eng', desc='', text=metadata.comment)

        # 封面
        if metadata.artwork is not None:
            tags['APIC:'] = APIC(
                encoding=3,
                mime='image/jpeg',
                type=3,
                desc='Cover',
                data=metadata.artwork
            )

    def save(self) -> None:
        self._file.save()
