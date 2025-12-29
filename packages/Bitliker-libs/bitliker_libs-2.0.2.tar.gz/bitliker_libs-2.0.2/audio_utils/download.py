#!/usr/bin/env python
# pylint: disable=E0401,W0718

"""
Coding: UTF-8
Author: Bitliker
Date: 2025/12/25 14:45:35
Version: 1.0.0
Description: 下载
"""
import os
import httpx
import log_ext


async def download(url: str, file_path: str, **kwargs) -> bool:
    """处理封面下载。

    如果文件不存在则下载。

    Args:
        url: 图片地址
        file_path: 保存路径

    Returns:
        是否成功
    """
    if os.path.exists(file_path):
        log_ext.error(f"封面已存在: {file_path}")
        return True

    log_ext.info(f"正在下载封面: {url} => {file_path}")

    # 确保目录存在
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    file_tmp = file_path + ".tmp"
    # 使用 httpx 下载
    try:
        async with httpx.AsyncClient().stream("GET", url, **kwargs) as response:
            if response.status_code != 200:
                log_ext.error(f"下载失败: {response.status_code}")
                return False
            with open(file_tmp, "wb") as f:
                async for chunk in response.aiter_bytes():
                    f.write(chunk)
            os.rename(file_tmp, file_path)
            return True
    except Exception as e:
        log_ext.error(f"下载文件时出错: {e}")
        if os.path.exists(file_tmp):
            os.remove(file_tmp)
        if os.path.exists(file_path):
            os.remove(file_path)
        return False
    return False
