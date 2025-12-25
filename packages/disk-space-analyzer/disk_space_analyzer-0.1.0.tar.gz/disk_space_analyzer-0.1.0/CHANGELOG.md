# 变更日志

本文档记录项目的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [0.1.0] - 2025-12-22

### 新增

- ✨ **pip 包安装支持**：项目现已支持通过 pip 安装
  - 命令行工具 `disk-analyzer` 可全局使用
  - 支持作为 Python 库导入使用
  - 提供开发模式安装选项
- 📦 **标准 Python 包结构**：重组为符合 PEP 标准的包结构
  - 创建 `disk_analyzer/` 主包目录
  - 添加 `__init__.py`、`__main__.py`、`cli.py` 等关键文件
- 🔧 **命令行参数支持**：
  - `--debug/-d`：调试模式
  - `--host`：自定义监听地址
  - `--port/-p`：自定义端口
  - `--no-browser`：禁用自动打开浏览器
  - `--version/-v`：显示版本信息
- 📝 **项目配置文件**：
  - `pyproject.toml`：现代化项目配置
  - `setup.py`：向后兼容配置
  - `MANIFEST.in`：非代码文件清单
  - `LICENSE`：MIT 开源许可证

### 变更

- 🔄 **文件重组**：
  - `disk_analyzer.py` → `disk_analyzer/analyzer.py`
  - `disk_web_tool.py` → `disk_analyzer/web_app.py`
  - `start_disk_tool.py` → `disk_analyzer/cli.py`
- 🔗 **导入路径调整**：更新为包内导入方式
- 📚 **文档更新**：更新 README.md 安装和使用说明

### 已知问题

- `start_disk_tool.py` 保留向后兼容，但建议使用新的命令行工具

### 详细变更日志

详见：`docs/changelog/CHANGLOG-20251222-192109.md`

---

## 版本说明

- **0.1.0**：首个 alpha 版本，支持 pip 安装
- 后续版本将遵循语义化版本控制
