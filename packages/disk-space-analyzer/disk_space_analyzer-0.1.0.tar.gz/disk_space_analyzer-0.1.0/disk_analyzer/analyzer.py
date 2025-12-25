#!/usr/bin/env python3
# coding: utf-8
"""
磁盘空间分析工具 - 使用文件系统元数据进行高效分析
"""

import os
import sys
import time
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class DiskUsage:
    """磁盘使用情况数据类"""
    path: str
    size_bytes: int
    size_human: str
    file_count: int
    dir_count: int
    last_modified: float
    error: Optional[str] = None


class DiskAnalyzer:
    """磁盘分析器 - 使用文件系统元数据"""
    
    def __init__(self, max_depth: int = 3, exclude_paths: List[str] = None, exclude_extensions: List[str] = None, progress_callback=None):
        self.max_depth = max_depth
        self.exclude_paths = exclude_paths or []  # 要排除的路径列表
        self.exclude_extensions = exclude_extensions or []  # 要排除的文件扩展名列表
        self.progress_callback = progress_callback or (lambda x: None)  # 进度回调函数
        self.size_units = ['B', 'KB', 'MB', 'GB', 'TB']
        
    def _format_size(self, size_bytes: int) -> str:
        """格式化字节大小为人类可读格式"""
        if size_bytes == 0:
            return "0 B"
        
        unit_index = 0
        size = float(size_bytes)
        
        while size >= 1024 and unit_index < len(self.size_units) - 1:
            size /= 1024
            unit_index += 1
            
        return f"{size:.2f} {self.size_units[unit_index]}"
    
    def _should_exclude_path(self, path: Path) -> bool:
        """检查路径是否应该被排除"""
        path_str = str(path)
        
        # 检查是否匹配排除的路径
        for exclude_path in self.exclude_paths:
            if path_str.startswith(exclude_path) or path_str == exclude_path:
                return True
        
        # 检查是否匹配排除的文件扩展名
        if path.is_file():
            for extension in self.exclude_extensions:
                if path_str.endswith(extension):
                    return True
        
        # 检查是否为系统目录
        system_dirs = ['/proc', '/sys', '/dev', '/run']
        for system_dir in system_dirs:
            if path_str.startswith(system_dir):
                return True
        
        return False
    
    def _get_dir_stats_fast(self, path: Path, current_depth: int = 0) -> DiskUsage:
        """
        快速获取目录统计信息 - 使用文件系统元数据
        
        主要使用 os.scandir() 和 os.stat() 获取元数据，避免读取文件内容
        """
        if self.max_depth is not None and current_depth > self.max_depth:
            # 超过深度限制，只获取目录本身的元数据
            try:
                stat = path.stat()
                return DiskUsage(
                    path=str(path),
                    size_bytes=0,
                    size_human="[深度限制]",
                    file_count=0,
                    dir_count=1,
                    last_modified=stat.st_mtime
                )
            except (OSError, PermissionError) as e:
                return DiskUsage(
                    path=str(path),
                    size_bytes=0,
                    size_human="[权限错误]",
                    file_count=0,
                    dir_count=0,
                    last_modified=0,
                    error=str(e)
                )
        
        total_size = 0
        file_count = 0
        dir_count = 0
        last_modified = 0
        
        try:
            # 使用 os.scandir() 更高效地获取目录内容
            with os.scandir(path) as entries:
                for entry in entries:
                    try:
                        # 检查是否应该排除该路径
                        entry_path = Path(entry.path)
                        if self._should_exclude_path(entry_path):
                            continue
                            
                        stat_info = entry.stat(follow_symlinks=False)
                        
                        if entry.is_file(follow_symlinks=False):
                            # 文件：累加大小，计数
                            total_size += stat_info.st_size
                            file_count += 1
                            # 更新最新修改时间
                            last_modified = max(last_modified, stat_info.st_mtime)
                            
                        elif entry.is_dir(follow_symlinks=False):
                            # 目录：计数，递归分析
                            dir_count += 1
                            if self.max_depth is None or current_depth < self.max_depth:
                                # 递归分析子目录
                                sub_stats = self._get_dir_stats_fast(Path(entry.path), current_depth + 1)
                                total_size += sub_stats.size_bytes
                                file_count += sub_stats.file_count
                                dir_count += sub_stats.dir_count
                                last_modified = max(last_modified, sub_stats.last_modified)
                    
                    except (OSError, PermissionError):
                        # 跳过无法访问的文件/目录
                        continue
            
            # 添加目录本身的大小（通常很小）
            dir_stat = path.stat(follow_symlinks=False)
            total_size += dir_stat.st_size
            last_modified = max(last_modified, dir_stat.st_mtime) if last_modified == 0 else last_modified
            
            return DiskUsage(
                path=str(path),
                size_bytes=total_size,
                size_human=self._format_size(total_size),
                file_count=file_count,
                dir_count=dir_count,
                last_modified=last_modified
            )
            
        except (OSError, PermissionError) as e:
            return DiskUsage(
                path=str(path),
                size_bytes=0,
                size_human="[访问被拒]",
                file_count=0,
                dir_count=0,
                last_modified=0,
                error=str(e)
            )
    
    def analyze_directory(self, root_path: str, limit: int = 50) -> List[DiskUsage]:
        """
        分析指定目录的磁盘使用情况（多层级递归分析）
        
        Args:
            root_path: 要分析的根目录路径
            limit: 返回结果的最大数量
            
        Returns:
            按大小排序的所有层级目录使用情况列表
        """
        root = Path(root_path)
        
        if not root.exists():
            logger.error(f"路径不存在: {root_path}")
            return []
        
        if not root.is_dir():
            logger.error(f"路径不是目录: {root_path}")
            return []
        
        # 检查是否为系统目录，如果是则拒绝分析
        if self._should_exclude_path(root):
            logger.error(f"拒绝分析系统目录: {root_path}")
            return []
        
        logger.info(f"开始分析目录: {root_path} (最大深度: {self.max_depth})")
        start_time = time.time()
        
        all_results = []  # 存储所有层级的目录信息
        
        # 递归收集所有层级的目录信息
        def collect_all_directories(current_path: Path, current_depth: int = 0):
            """递归收集所有目录的统计信息"""
            if self.max_depth is not None and current_depth > self.max_depth:
                return
            
            try:
                with os.scandir(current_path) as entries:
                    for entry in entries:
                        entry_path = Path(entry.path)
                        
                        # 跳过排除的路径
                        if self._should_exclude_path(entry_path):
                            continue
                        
                        # 只处理目录
                        if entry.is_dir(follow_symlinks=False):
                            # 获取此目录的统计信息（包括递归子目录的累计大小）
                            stats = self._get_dir_stats_fast(entry_path, current_depth)
                            all_results.append(stats)
                            
                            # 更新进度显示
                            print(f"已分析: {entry.name} - {stats.size_human}")
                            
                            # 如果未达到最大深度，继续递归收集子目录
                            if self.max_depth is None or current_depth < self.max_depth:
                                collect_all_directories(entry_path, current_depth + 1)
            
            except (OSError, PermissionError) as e:
                logger.warning(f"无法读取目录 {current_path}: {e}")
        
        # 开始从根目录收集所有层级的目录
        try:
            collect_all_directories(root, 0)
        except Exception as e:
            logger.error(f"分析失败: {e}")
            self.progress_callback({
                "status": "error",
                "message": f"分析失败: {str(e)}"
            })
            return []
        
        # 按大小排序（降序）
        all_results.sort(key=lambda x: x.size_bytes, reverse=True)
        
        # 限制结果数量（可选，建议保留所有结果以便前端树形展示）
        # results = all_results[:limit]
        results = all_results  # 保留所有层级的目录
        
        elapsed_time = time.time() - start_time
        logger.info(f"分析完成，耗时: {elapsed_time:.2f}秒，找到 {len(results)} 个目录")
        
        # 通知分析完成
        self.progress_callback({
            "status": "completed",
            "results": [asdict(r) for r in results],
            "elapsed_time": round(elapsed_time, 2),
            "count": len(results)
        })
        
        return results
    
    def get_unique_partitions(self) -> List[Dict]:
        """获取真实的磁盘分区和挂载信息，从 /proc/mounts 读取"""
        partitions = []
        
        # 要过滤的虚拟文件系统类型
        virtual_fs_types = {
            'proc', 'sysfs', 'devtmpfs', 'devpts', 'tmpfs', 'cgroup', 'cgroup2',
            'pstore', 'bpf', 'tracefs', 'debugfs', 'securityfs', 'fusectl',
            'configfs', 'mqueue', 'hugetlbfs', 'ramfs', 'efivarfs',
            'squashfs'  # snap 包
        }
        
        # 远程文件系统类型
        remote_fs_types = {
            'nfs', 'nfs4', 'cifs', 'smb', 'smbfs', 'fuse.sshfs', 'fuse.s3fs'
        }
        
        # 本地磁盘文件系统类型
        local_fs_types = {
            'ext2', 'ext3', 'ext4', 'xfs', 'btrfs', 'f2fs', 'jfs', 'reiserfs',
            'vfat', 'ntfs', 'exfat', 'hfs', 'hfsplus'
        }
        
        try:
            # 读取 /proc/mounts 获取所有挂载信息
            with open('/proc/mounts', 'r') as f:
                mounts = f.readlines()
            
            for line in mounts:
                parts = line.split()
                if len(parts) < 4:
                    continue
                
                device = parts[0]
                mount_point = parts[1]
                fs_type = parts[2]
                
                # 过滤虚拟文件系统
                if fs_type in virtual_fs_types:
                    continue
                
                # 过滤系统目录
                if mount_point.startswith(('/sys', '/proc', '/dev', '/run')):
                    continue
                
                # 过滤 snap 挂载点
                if mount_point.startswith('/snap/'):
                    continue
                
                # 过滤 Docker 相关路径
                if '/docker/' in mount_point or mount_point.startswith('/var/lib/docker/'):
                    continue
                
                # 获取磁盘使用情况
                try:
                    statvfs = os.statvfs(mount_point)
                    total = statvfs.f_frsize * statvfs.f_blocks
                    
                    # 跳过容量为0的文件系统
                    if total == 0:
                        continue
                    
                    free = statvfs.f_frsize * statvfs.f_bavail
                    used = total - free
                    
                    # 判断分区类型
                    if fs_type in remote_fs_types or device.startswith('//'):
                        partition_type = 'remote'  # 远程挂载
                        icon = 'bi-cloud'
                    elif fs_type in local_fs_types:
                        partition_type = 'local'  # 本地磁盘
                        icon = 'bi-hdd-fill'
                    else:
                        partition_type = 'other'  # 其他类型
                        icon = 'bi-device-hdd'
                    
                    partition = {
                        'device': device,
                        'mount_point': mount_point,
                        'fs_type': fs_type,
                        'partition_type': partition_type,
                        'icon': icon,
                        'is_primary': mount_point == '/',
                        'total': self._format_size(total),
                        'total_bytes': total,
                        'used': self._format_size(used),
                        'free': self._format_size(free),
                        'usage_percent': round((used / total) * 100, 2) if total > 0 else 0
                    }
                    
                    partitions.append(partition)
                    
                except (OSError, PermissionError) as e:
                    logger.warning(f"无法访问挂载点 {mount_point}: {e}")
                    continue
            
            # 排序：主分区优先，然后本地磁盘，然后远程挂载，最后按容量降序
            def sort_key(p):
                if p['is_primary']:
                    return (0, 0, -p['total_bytes'])
                elif p['partition_type'] == 'local':
                    return (1, 0, -p['total_bytes'])
                elif p['partition_type'] == 'remote':
                    return (2, 0, -p['total_bytes'])
                else:
                    return (3, 0, -p['total_bytes'])
            
            partitions.sort(key=sort_key)
            
        except Exception as e:
            logger.error(f"获取分区信息失败: {e}")
        
        return partitions
    
    def get_system_info(self) -> Dict:
        """获取系统磁盘信息（保持向后兼容）"""
        disk_info = {}
        
        try:
            # 获取主要挂载点的磁盘使用情况
            statvfs = os.statvfs('/')
            total = statvfs.f_frsize * statvfs.f_blocks
            free = statvfs.f_frsize * statvfs.f_bavail
            used = total - free
            
            disk_info['/'] = {
                'total': self._format_size(total),
                'used': self._format_size(used),
                'free': self._format_size(free),
                'usage_percent': round((used / total) * 100, 2) if total > 0 else 0
            }
            
            # 检查其他常见挂载点
            for mount_point in ['/home', '/var', '/tmp', '/usr']:
                if os.path.exists(mount_point):
                    try:
                        statvfs = os.statvfs(mount_point)
                        total = statvfs.f_frsize * statvfs.f_blocks
                        free = statvfs.f_frsize * statvfs.f_bavail
                        used = total - free
                        
                        if total > 0:
                            disk_info[mount_point] = {
                                'total': self._format_size(total),
                                'used': self._format_size(used),
                                'free': self._format_size(free),
                                'usage_percent': round((used / total) * 100, 2)
                            }
                    except (OSError, PermissionError):
                        continue
                        
        except Exception as e:
            logger.error(f"获取磁盘信息失败: {e}")
        
        return disk_info
    
    def analyze_partition_tree(self, mount_point: str, max_depth: int = 2, limit: int = 20) -> Dict:
        """
        分析分区目录树，用于分区详情展示
        
        Args:
            mount_point: 挂载点路径
            max_depth: 分析深度，默认2层
            limit: 每层最多返回的子目录数，默认20
            
        Returns:
            树形结构数据
        """
        root = Path(mount_point)
        
        if not root.exists():
            return {
                'success': False,
                'error': f'路径不存在: {mount_point}'
            }
        
        if not root.is_dir():
            return {
                'success': False,
                'error': f'路径不是目录: {mount_point}'
            }
        
        try:
            # 使用临时analyzer进行分析
            temp_analyzer = DiskAnalyzer(max_depth=max_depth)
            results = temp_analyzer.analyze_directory(mount_point, limit=limit * max_depth)
            
            # 构建树形结构
            tree = build_tree_structure(results, mount_point, max_depth)
            
            # 获取挂载点总容量
            statvfs = os.statvfs(mount_point)
            total_bytes = statvfs.f_frsize * statvfs.f_blocks
            
            # 计算每个节点的占比
            def add_usage_percent(node, parent_size=None):
                if parent_size is None:
                    parent_size = total_bytes
                
                if parent_size > 0:
                    node['usage_percent'] = round((node['size_bytes'] / parent_size) * 100, 2)
                else:
                    node['usage_percent'] = 0
                
                # 递归处理子节点
                for child in node.get('children', []):
                    add_usage_percent(child, node['size_bytes'])
            
            add_usage_percent(tree)
            
            return {
                'success': True,
                'mount_point': mount_point,
                'tree': tree
            }
            
        except Exception as e:
            logger.error(f"分析分区树失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }


def build_tree_structure(results: List[DiskUsage], root_path: str, max_depth: int = 3) -> Dict:
    """构建目录树结构"""
    # 创建根节点
    tree = {
        "name": os.path.basename(root_path) or root_path,
        "path": root_path,
        "size_bytes": 0,
        "size_human": "0 B",
        "file_count": 0,
        "dir_count": 0,
        "children": [],
        "level": 0
    }
    
    # 将结果按路径长度排序，确保父目录先处理
    sorted_results = sorted(results, key=lambda x: x.path)
    
    # 创建路径到节点的映射
    node_map = {root_path: tree}
    
    # 处理每个目录
    for item in sorted_results:
        # 计算目录层级
        level = item.path.replace(root_path, "").count(os.sep)
        
        # 如果超过最大深度，跳过
        if level > max_depth:
            continue
        
        # 查找最近的父目录
        parent_path = os.path.dirname(item.path)
        
        # 确保父目录存在
        while parent_path and parent_path not in node_map and parent_path != root_path:
            grandparent_path = os.path.dirname(parent_path)
            # 检查祖父目录层级
            grandparent_level = grandparent_path.replace(root_path, "").count(os.sep) if grandparent_path != root_path else 0
            
            # 如果祖父目录超过最大深度，跳过
            if grandparent_level > max_depth:
                break
                
            if grandparent_path not in node_map:
                # 创建中间目录节点
                node_map[parent_path] = {
                    "name": os.path.basename(parent_path),
                    "path": parent_path,
                    "size_bytes": 0,
                    "size_human": "0 B",
                    "file_count": 0,
                    "dir_count": 0,
                    "children": [],
                    "level": parent_path.replace(root_path, "").count(os.sep)
                }
                # 尝试添加到其父节点
                if grandparent_path in node_map:
                    node_map[grandparent_path]["children"].append(node_map[parent_path])
            parent_path = grandparent_path
        
        # 如果父目录超出深度限制，跳过当前目录
        parent_level = parent_path.replace(root_path, "").count(os.sep) if parent_path != root_path else 0
        if parent_level > max_depth:
            continue
        
        # 创建当前目录节点
        node = {
            "name": os.path.basename(item.path),
            "path": item.path,
            "size_bytes": item.size_bytes,
            "size_human": item.size_human,
            "file_count": item.file_count,
            "dir_count": item.dir_count,
            "children": [],
            "level": level
        }
        
        # 添加到父节点
        if parent_path in node_map:
            node_map[parent_path]["children"].append(node)
        else:
            # 如果找不到父节点，添加到根节点
            tree["children"].append(node)
        
        # 添加到映射
        node_map[item.path] = node
    
    # 递归函数：对每个节点的子节点按大小排序
    def sort_children_by_size(node):
        if node["children"]:
            # 按大小降序排序
            node["children"].sort(key=lambda x: x["size_bytes"], reverse=True)
            # 递归排序子节点
            for child in node["children"]:
                sort_children_by_size(child)
    
    # 对树的每个层级按大小排序
    sort_children_by_size(tree)
    
    return tree


def main():
    """命令行测试入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='磁盘空间分析工具')
    parser.add_argument('path', nargs='?', default='.', help='要分析的目录路径')
    parser.add_argument('--depth', '-d', type=int, default=3, help='分析深度')
    parser.add_argument('--limit', '-l', type=int, default=20, help='显示结果数量限制')
    
    args = parser.parse_args()
    
    analyzer = DiskAnalyzer(max_depth=args.depth)
    
    print(f"\n=== 磁盘空间分析报告 ===")
    print(f"分析路径: {os.path.abspath(args.path)}")
    print(f"分析深度: {args.depth}")
    print("=" * 50)
    
    # 显示系统磁盘信息
    disk_info = analyzer.get_system_info()
    print("\n系统磁盘使用情况:")
    for mount, info in disk_info.items():
        print(f"{mount:8} - 总计: {info['total']:8} | 已用: {info['used']:8} | 可用: {info['free']:8} | 使用率: {info['usage_percent']:5.1f}%")
    
    # 分析目录
    results = analyzer.analyze_directory(args.path, args.limit)
    
    print(f"\n目录大小排序 (前 {len(results)} 个):")
    print("-" * 80)
    print(f"{'大小':>10} {'文件数':>8} {'目录数':>8} {'最后修改':>12} 路径")
    print("-" * 80)
    
    for i, stats in enumerate(results, 1):
        last_mod = time.strftime('%Y-%m-%d', time.localtime(stats.last_modified))
        print(f"{stats.size_human:>10} {stats.file_count:8} {stats.dir_count:8} {last_mod:>12} {stats.path}")
    
    print(f"\n分析完成！")


if __name__ == '__main__':
    main()