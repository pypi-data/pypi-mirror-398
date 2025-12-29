#!/usr/bin/env python
# pylint: disable=E0401,W0718

"""
Coding: UTF-8
Author: Bitliker
Date: 2025/12/08
Version: 1.0.0
Description: 音频处理器基类
"""

from abc import ABC, abstractmethod
from typing import Optional
from ..metadata import AudioMetadata


class BaseHandler(ABC):
    """音频文件处理器基类"""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self._file = None

    @abstractmethod
    def load(self) -> None:
        """加载音频文件"""
        pass

    @abstractmethod
    def read(self) -> AudioMetadata:
        """读取元数据"""
        pass

    @abstractmethod
    def write(self, metadata: AudioMetadata) -> None:
        """写入元数据"""
        pass

    @abstractmethod
    def save(self) -> None:
        """保存更改"""
        pass

    def _parse_track_number(self, value) -> tuple:
        """解析音轨号，返回 (track_number, total_tracks)"""
        if value is None:
            return None, None
        if isinstance(value, tuple):
            return value[0] if len(value) > 0 else None, value[1] if len(value) > 1 else None
        if isinstance(value, str):
            if '/' in value:
                parts = value.split('/')
                return int(parts[0]) if parts[0] else None, int(parts[1]) if len(parts) > 1 and parts[1] else None
            return int(value) if value else None, None
        return int(value), None

    def _parse_disc_number(self, value) -> tuple:
        """解析碟片号，返回 (disc_number, total_discs)"""
        return self._parse_track_number(value)

    def _get_first_value(self, values) -> Optional[str]:
        """获取列表的第一个值"""
        if values is None:
            return None
        if isinstance(values, list):
            return str(values[0]) if values else None
        return str(values)
