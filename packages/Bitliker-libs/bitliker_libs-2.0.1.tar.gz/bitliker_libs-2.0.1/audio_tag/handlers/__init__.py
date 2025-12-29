#!/usr/bin/env python
# pylint: disable=E0401,W0718

"""
Coding: UTF-8
Author: Bitliker
Date: 2025/12/08
Version: 1.0.0
Description: 音频处理器模块
"""
from .base import BaseHandler
from .mp3_handler import MP3Handler
from .flac_handler import FLACHandler
from .mp4_handler import MP4Handler
from .ogg_handler import OggHandler

__all__ = [
    "BaseHandler",
    "MP3Handler",
    "FLACHandler",
    "MP4Handler",
    "OggHandler",
]
