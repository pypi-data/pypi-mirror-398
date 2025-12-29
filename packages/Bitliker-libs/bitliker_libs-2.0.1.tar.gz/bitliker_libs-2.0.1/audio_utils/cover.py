#!/usr/bin/env python
# pylint: disable=E0401,W0718

"""
Coding: UTF-8
Author: Bitliker
Date: 2025/12/15 16:44:28
Version: 1.0.0
Description: 封面处理
"""
import os
from .download import download


async def handler_cover(url: str, file_path: str, **kwargs) -> bool:
    """处理封面下载。

    如果文件不存在则下载。

    Args:
        url: 图片地址
        file_path: 保存路径

    Returns:
        是否成功
    """
    return await download(url, file_path, **kwargs)


def get_cover_byte(file_path: str) -> bytes:
    """获取封面图片"""
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return None
    print(f"获取封面图片: {file_path}")
    with open(file_path, "rb") as img_in:
        return img_in.read()
    return None
