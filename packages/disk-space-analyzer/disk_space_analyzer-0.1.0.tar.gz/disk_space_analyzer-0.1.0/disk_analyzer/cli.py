#!/usr/bin/env python3
# coding: utf-8
"""
磁盘分析工具命令行入口
"""

import os
import sys
import argparse
import subprocess
import webbrowser
from pathlib import Path


def check_dependencies():
    """检查并安装依赖"""
    requirements_file = Path(__file__).parent.parent / 'requirements.txt'
    
    if requirements_file.exists():
        print("检查依赖包...")
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', '-r', str(requirements_file)
            ])
            print("依赖安装完成")
        except subprocess.CalledProcessError as e:
            print(f"依赖安装失败: {e}")
            return False
    
    return True


def main():
    """主启动函数"""
    from disk_analyzer import __version__
    
    print("🔧 磁盘空间分析工具启动器")
    print("=" * 40)
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description='磁盘空间分析工具 - 提供直观的可视化界面和灵活的分析选项',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  disk-analyzer                    # 标准模式启动
  disk-analyzer --debug            # 调试模式启动
  disk-analyzer --port 9090        # 自定义端口
  disk-analyzer --no-browser       # 不自动打开浏览器
  disk-analyzer --version          # 显示版本信息
        """
    )
    
    parser.add_argument(
        '--debug', '-d',
        action='store_true',
        help='启用调试模式（支持热更新）'
    )
    
    parser.add_argument(
        '--host',
        default='0.0.0.0',
        help='Web服务监听地址（默认: 0.0.0.0）'
    )
    
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=8080,
        help='Web服务监听端口（默认: 8080）'
    )
    
    parser.add_argument(
        '--no-browser',
        action='store_true',
        help='启动后不自动打开浏览器'
    )
    
    parser.add_argument(
        '--version', '-v',
        action='version',
        version=f'Disk Space Analyzer v{__version__}'
    )
    
    args = parser.parse_args()
    
    # 检查依赖
    if not check_dependencies():
        print("❌ 依赖安装失败，程序退出")
        sys.exit(1)
    
    # 启动Web应用
    try:
        print(f"🚀 启动磁盘分析Web服务...")
        print(f"   监听地址: {args.host}:{args.port}")
        print(f"   调试模式: {'开启' if args.debug else '关闭'}")
        
        # 自动打开浏览器
        if not args.no_browser:
            url = f"http://localhost:{args.port}"
            print(f"   浏览器: {url}")
            try:
                webbrowser.open(url)
            except Exception as e:
                print(f"   ⚠️ 无法自动打开浏览器: {e}")
                print(f"   请手动访问: {url}")
        
        from disk_analyzer.web_app import app
        app.run(host=args.host, port=args.port, debug=args.debug)
        
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
