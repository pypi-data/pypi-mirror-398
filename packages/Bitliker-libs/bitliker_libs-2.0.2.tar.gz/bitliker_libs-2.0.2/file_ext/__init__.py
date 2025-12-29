#!/usr/bin/env python

"""
Author: Bitliker
Date: 2025-05-14 09:25:59
Version: 1.0
Description: 文件拓展管理

"""
import os
import re
import shutil
from typing import Optional, Callable

EXTENSION_AUDIO = [".mp3", ".m4a", ".flac", ".wav", ".ape", ".wma"]
EXTENSION_VIDEO = [".mp4", ".avi", ".mkv"]
EXTENSION_IMAGE = [".png", ".jpg", ".jpeg", "webp", "bmp"]


def get_extension(file_path: str) -> str:
    """获取文件拓展名

    Args:
        file_path (str): 文件路径

    Returns:
        str: 文件拓展名
    """
    _, extension = os.path.splitext(file_path)
    return extension


def get_not_extension(file_path: str) -> str:
    """获取文件拓展名

    Args:
        file_path (str): 文件路径

    Returns:
        str: 文件拓展名
    """
    filename, _ = os.path.splitext(os.path.basename(file_path))
    return filename


def is_audio(file_path: str) -> bool:
    """是否音频

    Args:
        file_path (str): 文件路径

    Returns:
        bool: 是否音频
    """
    return get_extension(file_path).lower() in EXTENSION_AUDIO


def is_video(file_path: str) -> bool:
    """是否视频

    Args:
        file_path (str): 文件路径

    Returns:
        bool: 是否视频
    """
    return get_extension(file_path) in EXTENSION_VIDEO


def is_image(file_path: str) -> bool:
    """是否视频

    Args:
        file_path (str): 文件路径

    Returns:
        bool: 是否视频
    """
    return get_extension(file_path) in EXTENSION_IMAGE


def extract_first_number(file_name: str) -> str:
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


def get_album_max_episode(album_path: str, by_audio_number: bool = False) -> int:
    """获取专辑最大集数

    Args:
        album_path (str): 专辑路径
        by_audio_number (bool, optional): 是否通过计算音频数量来确定, False: 取文件名中最大的数字 True: 取音频文件总和

    Returns:
        int: _description_
    """
    if by_audio_number:
        return len([file for file in os.listdir(album_path) if is_audio(file)])

    file_list = os.listdir(album_path)
    file_list.sort(reverse=True)
    max_episode = 0
    for file_name in file_list:
        if not is_audio(file_name):
            continue
        eposode = 0
        try:
            eposode = extract_first_number(file_name)
        except Exception as e:  # pylint: disable=broad-except
            print(e)
        max_episode = max(max_episode, int(eposode))
    return max_episode


def move_file(source_path: str, target_path: str, log_able: bool = False) -> bool:
    """移动文件

    Args:
        source_path (str): 来源文件路径
        target_path (str): 目标文件路径

    Returns:
        bool: 是否转移成功
    """
    try:
        if os.path.exists(target_path):
            print(f"目标文件已存在: {target_path}")
            return False
        dir_path = os.path.dirname(target_path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        print(f"移动文件: {source_path}  ==> {target_path}")
        if os.path.isdir(source_path):
            shutil.move(source_path, target_path)
        else:
            os.rename(source_path, target_path)
        if log_able:
            rename_logs(source_path, target_path)
        return True
    except Exception as e:  # pylint: disable=broad-except
        print(e)
        return False


def copy_file(source_path: str, target_path: str, log_able: bool = False) -> bool:
    """移动文件

    Args:
        source_path (str): 来源文件路径
        target_path (str): 目标文件路径

    Returns:
        bool: 是否转移成功
    """
    try:
        if os.path.exists(target_path):
            print(f"目标文件已存在: {target_path}")
            return False
        dir_path = os.path.dirname(target_path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        print(f"复制文件: {source_path}  ==> {target_path}")
        if os.path.isdir(source_path):
            shutil.copy2(source_path, target_path)
        else:
            shutil.copyfile(source_path, target_path)
        if log_able:
            rename_logs(source_path, target_path)
        return True
    except Exception as e:  # pylint: disable=broad-except
        print(e)
        return False


def rename_logs(
    from_path: str, to_path: str, append: bool = True, _logs_path: str = "rename.log"
):
    """记录日志信息

    Args:
        _logs_path (str): 日志文件路径
        from_path (str): 从文件路径
        to_path (str): 到文件路径
        appadd (bool, optional): 是否以追加方式写入文件。Defaults to True.
    """
    if not _logs_path or "rename.log" == _logs_path:
        _logs_path = os.path.join(os.path.dirname(to_path), "rename.log")
    with open(_logs_path, mode="a" if append else "w", encoding="utf-8") as file:
        file.write(f"{from_path} -> {to_path}\n")


def clear_empty(_root_path: str) -> bool:
    """清理空文件夹

    Args:
        _root_path (str): 当前路径是否需要清理

    Returns:
        bool: 是否成功清理 True:清理 False:未清理
    """
    file_list = [
        os.path.join(root, file)
        for root, _, files in os.walk(_root_path)
        for file in files
    ]
    if file_list:
        return False
    shutil.rmtree(_root_path)
    return True


def find_all_file(_root_path: str, filter_func: Optional[Callable] = None) -> list[str]:
    """查找所有文件

    Args:
        _root_path (str): 根目录 ， 寻找该目录下全部的文件
        filter_func (callable, optional): 过滤函数，用于过滤文件路径。默认为 None，表示不过滤。
    Usage:
        for file_path in find_all_file(_root_path, lambda file_path: is_video(file_path)):
            print(file_path)

    Returns:
        list[str]: 文件路径列表
    """
    for root, _, files in os.walk(_root_path):
        for file in files:
            file_path = os.path.join(root, file)
            if os.path.isfile(file_path):
                if filter_func is None or filter_func(file_path):
                    yield file_path
