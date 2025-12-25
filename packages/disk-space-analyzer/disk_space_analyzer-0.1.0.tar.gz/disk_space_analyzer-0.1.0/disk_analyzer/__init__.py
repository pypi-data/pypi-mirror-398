#!/usr/bin/env python3
# coding: utf-8
"""
磁盘空间分析工具

一个功能强大的磁盘空间分析和管理工具，提供直观的可视化界面、安全的删除机制和灵活的分析选项。
"""

from disk_analyzer.analyzer import DiskAnalyzer, DiskUsage, build_tree_structure
from disk_analyzer.web_app import app

__version__ = "0.1.0"
__author__ = "Disk Analyzer Team"
__all__ = ['DiskAnalyzer', 'DiskUsage', 'build_tree_structure', 'app']
