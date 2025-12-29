#!/usr/bin/env python
# pylint: disable=E0401,W0718

"""
Coding: UTF-8
Author: Bitliker
Date: 2025/12/24 17:20:01
Version: 1.0.0
Description:
"""
import os
import re


def filter_album_title(org_album_title: str) -> str:
    """过滤专辑标题

    Args:
        org_album_title (str): 原始的标题

    Returns:
        str: 过滤后的标题
    """
    _title = org_album_title
    try:
        match = re.search(r"《([^》]+)》", org_album_title)
        if match:
            _title = match.group(1)
        if "|" in _title:
            _title = _title.split("|")[0]
        if "丨" in _title:
            _title = _title.split("丨")[0]
        if "【" in _title:
            _cache_title = re.sub(r"【.*】", "", _title)
            if _cache_title:
                _title = _cache_title
        return remove_special_characters(_title)
    except Exception:  # pylint: disable=broad-except
        return _title


def remove_special_characters(_title: str) -> str:
    """去除特殊字符"""
    return (
        re.sub(r'[\\/*?:"<>|]', "", _title)
        .replace("%", "\\%")
        .replace("&", "&amp;")
        .strip()
    )


def filter_track_title(_title: str, _max_episode: int = 1000) -> str:
    """过滤标题内容 --> 提取简化标题

    Args:
        _title (str): 原始专辑名称
        _max_episode (int, optional): 最大集数. Defaults to 0.

    Returns:
        str: 过滤过后的名称
    """
    try:
        # 1. 过滤特殊字符 和垃圾字符
        _new_title = (
            remove_special_characters(_title)
            .replace("-点击订阅，不迷路", "")
            .replace("?", "?")
        )

        # 2. 提取特性内容
        _new_title = _match_frist(
            _new_title,
            [
                r".*(第\d+\s*.*)",
                # r"(\d+)(.*)",
                r"《([^》]+)》",
            ],
        )
        # 2. 提取 episode
        try:
            _episode = _extract_first_number(file_name=_title)
            _new_episode = _get_episode_name(_episode, _max_episode=_max_episode)
            _new_title = _new_title.replace(_episode, _new_episode)
        except Exception:  # pylint: disable=broad-except
            pass
        # 取关键字符前置部分
        if "|" in _new_title:
            _new_title = _new_title.split("|")[0]
        if "【" in _new_title:
            _new_title = _new_title.split("【")[0]
        # 正则移除字符规则
        _pattern = r"([\(\[\（【《].*?[\)\]\）】》])"
        _matches = re.findall(_pattern, _new_title)
        if _matches:
            for match in _matches:
                print(f"去除 {match}")
                _new_title = _new_title.replace(match, "")
        _new_title = _new_title.strip()
        return (
            remove_special_characters(_title)
            if not _new_title
            else remove_special_characters(_new_title)
        )

    except Exception:  # pylint: disable=broad-except
        return _title


def _match_frist(_msg: str, patterns: list) -> str:
    """正则处理并且提取第一个匹配内容

    Args:
        _msg (str): 信息
        patterns (list): 正则内容

    Returns:
        str: _description_
    """
    _new_msg = _msg
    for pattern in patterns:
        match = re.search(pattern, _new_msg)
        if match:
            _new_msg = match.group(1)
    return _new_msg


def _extract_first_number(file_name: str) -> str:
    """获取字符串的第一个数字

    Args:
        file_name (str): 输入内容

    Returns:
        str: 第一个数字 001 002 003 ... 100
    """
    numbers = re.findall(r"\d+", os.path.splitext(os.path.basename(file_name))[0])
    if numbers:
        return numbers[0]
    raise ImportError("No numbers found in the input string.")


def _get_episode_name(_episode: str, _max_episode: int) -> str:
    """获取集数名称，1 - max_episode；补充 00 => 001

    Args:
        _episode (str): 集数
        _max_episode (int): 最大集数

    Returns:
        str: 1 -> 001
    """
    # 计算需要的零的个数
    num_zeros = len(str(_max_episode))
    # 使用 zfill 方法填充前导零
    episode_name = str(_episode).zfill(num_zeros)
    return episode_name


def _fill_zeros(_index: int, _max: int) -> str:
    """补充 0"""
    # 计算需要的零的个数
    num_zeros = len(str(_max))
    # 使用 zfill 方法填充前导零
    episode_name = str(_index).zfill(num_zeros)
    return episode_name
