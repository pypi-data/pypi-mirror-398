#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AICP Helper SDK Setup Script
AI Cloud Platform 公共SDK安装配置文件
"""

from setuptools import setup, find_packages
import os


# 读取依赖项
def get_requirements():
    """从 requirements.txt 读取依赖项"""
    requirements_file = "requirements.txt"
    if os.path.exists(requirements_file):
        with open(requirements_file, "r", encoding="utf-8") as f:
            requirements = []
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    requirements.append(line)
            return requirements
    return []

setup(
    name="aicp-helper",
    version="1.0.9",
    description="AICP Helper SDK - AI Cloud Platform 工具库",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",

    # 作者信息
    author="AICP Team",
    author_email="aicp-team@coreshub.cn",
    maintainer="syw",
    maintainer_email="syw@coreshub.cn",

    # 包配置
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,

    # Python 版本要求
    python_requires=">=3.9",

    # 依赖项
    install_requires=get_requirements(),
)