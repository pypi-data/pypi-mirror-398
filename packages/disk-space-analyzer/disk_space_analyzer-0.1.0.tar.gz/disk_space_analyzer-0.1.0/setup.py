#!/usr/bin/env python3
# coding: utf-8
"""
setup.py - 传统安装配置文件（向后兼容）

推荐使用 pyproject.toml 进行安装配置
"""

from setuptools import setup, find_packages
from pathlib import Path

# 读取 README
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# 读取依赖
requirements = (this_directory / "requirements.txt").read_text(encoding='utf-8').splitlines()
requirements = [r.strip() for r in requirements if r.strip() and not r.startswith('#')]

setup(
    name="disk-space-analyzer",
    version="0.1.0",
    author="Disk Analyzer Team",
    description="一个功能强大的磁盘空间分析和管理工具",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/username/disk_analyzer",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: System Administrators",
        "Topic :: System :: Filesystems",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-cov>=4.0.0',
            'black>=23.0.0',
            'flake8>=6.0.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'disk-analyzer=disk_analyzer.cli:main',
        ],
    },
    include_package_data=True,
)
