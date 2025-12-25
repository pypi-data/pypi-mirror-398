#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Created: 2025/12/22 16:48
# @File:    setup.py
# @Author:  Jinshuo Zhang
# @Contact: zhangjinshuowork@163.com
# @Software: PyCharm
# @Purpose:
# =============================================================================

""" ============================== 标准库 ============================== """
from setuptools import setup, find_packages

""" ============================== 打包配置 =============================== """
setup(
    name="ZJS_Tool",
    version="0.1.0",
    packages=find_packages(exclude=[]),
    author="Jinshuo Zhang",
    author_email="zhangjinshuowork@163.com",
    description="ZJS Python Tool",
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/MarchZJS/ZJS_Tool.git",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires='>=3.6',
)