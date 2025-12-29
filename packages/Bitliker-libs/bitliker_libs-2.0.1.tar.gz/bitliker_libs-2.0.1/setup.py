#!/usr/bin/env python

"""
Author: Bitliker
Date: 2025-03-19 09:03:04
Version: 1.0
Description: 打包当前的 python 项目

"""

import os
import sys
from setuptools import setup, find_packages
from setuptools.command.sdist import sdist
from setuptools.command.bdist_wheel import bdist_wheel
from setuptools.command.build import build
from setuptools.command.egg_info import egg_info


class CustomSdist(sdist):
    """自定义sdist命令，指定输出目录为building"""
    def initialize_options(self):
        super().initialize_options()
        # 设置输出目录为building
        if not os.path.exists('building/dist'):
            os.makedirs('building/dist')
        self.dist_dir = 'building/dist'


class CustomBdistWheel(bdist_wheel):
    """自定义bdist_wheel命令，指定输出目录为building"""
    def initialize_options(self):
        super().initialize_options()
        # 设置输出目录为building
        if not os.path.exists('building'):
            os.makedirs('building')
        self.dist_dir = 'building'


class CustomBuild(build):
    """自定义build命令，指定构建目录为building"""
    def initialize_options(self):
        super().initialize_options()
        # 设置构建目录为building下的build子目录
        if not os.path.exists('building'):
            os.makedirs('building')
        self.build_base = 'building/build'


class CustomEggInfo(egg_info):
    """自定义egg_info命令，指定egg-info目录为building"""
    def initialize_options(self):
        super().initialize_options()
        # 设置egg-info目录为building下的egg-info子目录
        if not os.path.exists('building'):
            os.makedirs('building')
        self.egg_base = 'building'


setup(
    name="Bitliker-libs",  # 包名
    version="2.0.1",  # 版本号
    packages=find_packages(),  # 包含的包
    description="Bitliker 个人集合工具类",  # 包的描述
    long_description=open("README.md", encoding="utf-8").read(),  # 包的详细描述
    long_description_content_type="text/markdown",  # 包的详细类型
    author="Bitliker",  # 作者
    author_email="gongpengming@163.com",
    url="https://github.com/BitlikerPython/Libs",
    install_requires=["music_tag","mutagen","httpx"],
    license="MIT",
    cmdclass={
        'sdist': CustomSdist,
        'bdist_wheel': CustomBdistWheel,
        'build': CustomBuild,
        'egg_info': CustomEggInfo,
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords="Bitliker Tools",
    python_requires=">=3.10",
)