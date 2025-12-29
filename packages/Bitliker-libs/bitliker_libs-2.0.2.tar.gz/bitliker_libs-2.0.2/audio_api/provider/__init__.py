#!/usr/bin/env python
# pylint: disable=E0401,W0718

"""
Coding: UTF-8
Author: Bitliker
Date: 2025/12/24 13:40:54
Version: 1.0.0
Description: 音频下载提供者
"""
from .fanqie_api import GuiguiFQApiProvider, LongzhuFQProvider
from .xmly_api import GuiguiApiProvider, LongzhuProvider
from .provider import Provider


__all__ = [
    "Provider",
    "LongzhuFQProvider",
    "GuiguiFQApiProvider",
    "GuiguiApiProvider",
    "LongzhuProvider",
]
