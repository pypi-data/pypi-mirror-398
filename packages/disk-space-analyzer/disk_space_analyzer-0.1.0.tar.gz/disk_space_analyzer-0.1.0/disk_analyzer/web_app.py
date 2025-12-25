#!/usr/bin/env python3
# coding: utf-8
"""
磁盘空间分析Web工具 - Flask应用
"""

import os
import sys
import json
import shutil
import time
from pathlib import Path
from flask import Flask, render_template_string, jsonify, request
from flask_cors import CORS
import logging
from threading import Lock
import traceback
from dataclasses import asdict  # 导入asdict函数

# 导入我们的磁盘分析器
from disk_analyzer.analyzer import DiskAnalyzer, build_tree_structure, DiskUsage

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)
CORS(app)

# 线程锁，防止并发分析
analysis_lock = Lock()
current_analysis = {}
progress_storage = {}  # 存储分析进度

# HTML模板
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>磁盘空间分析工具</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.7.2/font/bootstrap-icons.css" rel="stylesheet">
    <style>
        .progress-container { height: 20px; }
        .file-icon { color: #6c757d; }
        .folder-icon { color: #ffc107; }
        .danger-icon { color: #dc3545; }
        .table-hover tbody tr:hover { background-color: #f8f9fa; cursor: pointer; }
        .loading { display: none; }
        .system-info { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .card { transition: transform 0.2s; }
        .card:hover { transform: translateY(-2px); }
        .path-input { font-family: 'Courier New', monospace; }
        
        /* 分区卡片样式 */
        .partition-card { cursor: pointer; border-radius: 8px; transition: all 0.3s ease; }
        .partition-card.local-disk { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
        .partition-card.remote-disk { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); color: white; }
        .partition-card.other-disk { background: linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%); color: white; }
        .partition-card:hover { box-shadow: 0 4px 15px rgba(0,0,0,0.2); }
        .partition-badge { font-size: 0.75rem; padding: 0.25rem 0.5rem; border-radius: 4px; }
        .partition-badge { background-color: rgba(255,255,255,0.3); }
        .device-info { font-size: 0.85rem; opacity: 0.9; margin-top: 0.5rem; font-family: 'Courier New', monospace; }
        
        /* 磁盘卡片显示模式样式 */
        .partition-card { position: relative; min-height: 120px; }
        .card-mode-toggle {
            position: absolute;
            top: 10px;
            right: 10px;
            background: rgba(255,255,255,0.3);
            border: none;
            color: white;
            width: 24px;
            height: 24px;
            border-radius: 4px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.8rem;
            transition: all 0.2s ease;
        }
        .card-mode-toggle:hover {
            background: rgba(255,255,255,0.5);
            transform: scale(1.1);
        }
        
        /* Mini模式 */
        .partition-card.mode-mini {
            min-height: 60px;
        }
        .partition-card.mode-mini .card-body {
            padding: 10px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .partition-card.mode-mini .partition-mini-content {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .partition-card.mode-mini .partition-full-content {
            display: none;
        }
        .partition-card.mode-mini .partition-badge {
            display: none;
        }
        .partition-card.mode-mini .device-info {
            display: none;
        }
        .partition-card.mode-mini .mini-progress-circle {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: conic-gradient(rgba(255,255,255,0.9) var(--progress), rgba(255,255,255,0.2) 0);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.75rem;
            font-weight: bold;
        }
        .partition-card.mode-mini .mini-name {
            font-size: 0.9rem;
            font-weight: bold;
        }
        
        /* 横条模式 */
        .partition-card.mode-bar {
            min-height: 100px;
        }
        .partition-card.mode-bar .card-body {
            padding: 15px;
        }
        .partition-card.mode-bar .partition-mini-content {
            display: none;
        }
        .partition-card.mode-bar .partition-bar-content {
            display: block;
        }
        .partition-card.mode-bar .partition-full-content {
            display: none;
        }
        .partition-card.mode-bar .device-info {
            display: none;
        }
        .partition-card.mode-bar .bar-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        .partition-card.mode-bar .bar-info {
            display: flex;
            gap: 15px;
            font-size: 0.85rem;
            margin-top: 5px;
        }
        
        /* 完整模式（默认）*/
        .partition-card.mode-full {
            min-height: 120px;
        }
        .partition-card.mode-full .partition-mini-content {
            display: none;
        }
        .partition-card.mode-full .partition-bar-content {
            display: none;
        }
        .partition-card.mode-full .partition-full-content {
            display: block;
        }
        
        /* 分析结果视觉增强 */
        #resultsSection .card {
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            border-left: 4px solid #667eea;
        }
        #resultsSection .card-header {
            background: linear-gradient(90deg, #667eea, #764ba2);
            color: white;
        }
        #resultsSection .card-header .nav-tabs {
            border-bottom: none;
        }
        #resultsSection .card-header .nav-link {
            color: rgba(255,255,255,0.8);
            border: none;
        }
        #resultsSection .card-header .nav-link.active {
            color: white;
            background: rgba(255,255,255,0.2);
            border-radius: 4px 4px 0 0;
        }
        #resultsSection .card-header .nav-link:hover {
            color: white;
            background: rgba(255,255,255,0.1);
        }
        
        /* 系统磁盘信息折叠 */
        .disk-info-collapsible .card-body {
            max-height: 500px;
            overflow-y: auto;
            transition: max-height 0.3s ease;
        }
        .disk-info-collapsible.collapsed .card-body {
            max-height: 0;
            overflow: hidden;
        }
        .disk-info-summary {
            display: none;
            padding: 10px 0;
            font-size: 0.9rem;
        }
        .disk-info-collapsible.collapsed .disk-info-summary {
            display: block;
        }
        
        /* 侧边栏样式 */
        .sidebar {
            position: fixed;
            left: 0;
            top: 56px;
            width: 320px;
            height: calc(100vh - 56px);
            background: #f8f9fa;
            border-right: 1px solid #dee2e6;
            overflow-y: auto;
            transition: all 0.3s ease;
            z-index: 1000;
        }
        .sidebar.collapsed {
            width: 60px;
        }
        .sidebar .sidebar-content {
            padding: 15px;
            opacity: 1;
            transition: opacity 0.2s ease;
        }
        .sidebar.collapsed .sidebar-content {
            opacity: 0;
            pointer-events: none;
        }
        .sidebar .sidebar-mini {
            display: none;
            padding: 15px 10px;
            text-align: center;
        }
        .sidebar.collapsed .sidebar-mini {
            display: block;
            opacity: 1;
            transition: opacity 0.2s ease 0.1s;
        }
        .sidebar-toggle {
            position: absolute;
            right: -15px;
            top: 20px;
            width: 30px;
            height: 30px;
            background: #667eea;
            border: none;
            border-radius: 50%;
            color: white;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            transition: all 0.3s ease;
        }
        .sidebar-toggle:hover {
            background: #764ba2;
            transform: scale(1.1);
        }
        .main-content {
            margin-left: 340px;
            padding: 20px;
            transition: margin-left 0.3s ease;
        }
        .main-content.sidebar-collapsed {
            margin-left: 80px;
        }
        
        /* 响应式设计 */
        @media (max-width: 1199px) {
            .sidebar {
                width: 60px;
            }
            .sidebar .sidebar-content {
                opacity: 0;
                pointer-events: none;
            }
            .sidebar .sidebar-mini {
                display: block;
            }
            .main-content {
                margin-left: 80px;
            }
        }
        @media (max-width: 767px) {
            .sidebar {
                transform: translateX(-100%);
            }
            .sidebar.mobile-open {
                transform: translateX(0);
            }
            .main-content {
                margin-left: 0;
            }
        }
    </style>
</head>
<body class="bg-light">
    <!-- 导航栏 -->
    <nav class="navbar navbar-expand-lg navbar-dark system-info">
        <div class="container-fluid">
            <a class="navbar-brand" href="#">
                <i class="bi bi-hdd-rack-fill"></i> 磁盘空间分析工具
            </a>
            <div class="navbar-nav ms-auto">
                <span class="navbar-text">
                    <i class="bi bi-shield-check"></i> 安全删除，谨慎操作
                </span>
            </div>
        </div>
    </nav>

    <!-- 侧边栏 -->
    <div class="sidebar" id="sidebar">
        <button class="sidebar-toggle" id="sidebarToggle" title="收起/展开侧边栏">
            <i class="bi bi-chevron-left"></i>
        </button>
        
        <!-- 侧边栏完整内容 -->
        <div class="sidebar-content">
            <h5 class="mb-3"><i class="bi bi-sliders"></i> 分析设置</h5>
            <form id="analysisForm">
                <div class="mb-3">
                    <label for="pathInput" class="form-label">分析路径</label>
                    <div class="input-group input-group-sm">
                        <input type="text" class="form-control path-input" id="pathInput" 
                               value="/" placeholder="输入目录路径">
                        <button class="btn btn-outline-secondary" type="button" id="browsePathBtn">
                            <i class="bi bi-folder"></i>
                        </button>
                    </div>
                </div>
                <div class="mb-3">
                    <label for="depthInput" class="form-label">分析深度</label>
                    <select class="form-select form-select-sm" id="depthInput">
                        <option value="1">1层</option>
                        <option value="2">2层</option>
                        <option value="3" selected>3层</option>
                        <option value="4">4层</option>
                        <option value="5">5层</option>
                    </select>
                </div>
                <div class="mb-3">
                    <label for="limitInput" class="form-label">显示数量</label>
                    <input type="number" class="form-control form-control-sm" id="limitInput" value="50" min="10" max="200">
                </div>
                <div class="mb-3">
                    <label for="excludePathsInput" class="form-label">排除路径</label>
                    <div class="input-group input-group-sm">
                        <input type="text" class="form-control" id="excludePathsInput" placeholder="/tmp,/var/log">
                        <button class="btn btn-outline-secondary" type="button" id="browseExcludePathBtn">
                            <i class="bi bi-folder"></i>
                        </button>
                    </div>
                    <div class="form-text" style="font-size: 0.75rem;">示例: /tmp,/var/log</div>
                    <div class="mt-2">
                        <div id="excludePathsList" class="border rounded p-2" style="max-height: 120px; overflow-y: auto; font-size: 0.85rem;">
                        </div>
                    </div>
                </div>
                <div class="mb-3">
                    <label for="excludeExtensionsInput" class="form-label">排除扩展名</label>
                    <input type="text" class="form-control form-control-sm" id="excludeExtensionsInput" placeholder=".log,.tmp">
                    <div class="form-text" style="font-size: 0.75rem;">示例: .log,.tmp,.cache</div>
                </div>
                <div class="d-grid">
                    <button type="submit" class="btn btn-primary" id="analyzeBtn">
                        <i class="bi bi-search"></i> 开始分析
                    </button>
                </div>
            </form>
        </div>
        
        <!-- 迷你显示内容 -->
        <div class="sidebar-mini">
            <div class="mb-3" title="分析路径">
                <i class="bi bi-folder" style="font-size: 1.5rem;"></i>
                <div style="font-size: 0.7rem; margin-top: 5px;" id="miniPath">/</div>
            </div>
            <div class="mb-3" title="分析深度">
                <i class="bi bi-layers" style="font-size: 1.5rem;"></i>
                <div style="font-size: 0.7rem; margin-top: 5px;" id="miniDepth">3</div>
            </div>
            <button class="btn btn-sm btn-primary w-100" onclick="startAnalysis()" title="开始分析">
                <i class="bi bi-search"></i>
            </button>
        </div>
    </div>
    
    <!-- 主内容区 -->
    <div class="main-content" id="mainContent">
        <!-- 系统磁盘信息 -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="card disk-info-collapsible" id="diskInfoCard">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h5 class="mb-0"><i class="bi bi-pc-display"></i> 系统磁盘信息</h5>
                        <div>
                            <button class="btn btn-sm btn-outline-secondary me-2" onclick="loadSystemInfo()">
                                <i class="bi bi-arrow-clockwise"></i> 刷新
                            </button>
                            <button class="btn btn-sm btn-outline-secondary" id="toggleDiskInfo" title="折叠/展开">
                                <i class="bi bi-chevron-up"></i>
                            </button>
                        </div>
                    </div>
                    <div class="disk-info-summary">
                        <div class="px-3">
                            <span id="diskSummaryText">加载中...</span>
                        </div>
                    </div>
                    <div class="card-body">
                        <div class="alert alert-info mb-3" role="alert">
                            <i class="bi bi-info-circle"></i> 显示系统独立物理分区，相同分区上的多个路径已合并显示。点击分区卡片可查看详细目录结构。
                        </div>
                        <div class="row" id="diskInfo">
                            <!-- 磁盘信息将通过JavaScript填充 -->
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- 加载进度 -->
        <div class="row mb-4" id="loadingSection" style="display: none;">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="bi bi-speedometer2"></i> 分析进度</h5>
                    </div>
                    <div class="card-body">
                        <div class="progress mb-3">
                            <div class="progress-bar progress-bar-striped progress-bar-animated" 
                                 role="progressbar" id="analysisProgress" style="width: 0%">0%</div>
                        </div>
                        <div class="mb-2">
                            <span id="progressText">准备开始分析...</span>
                        </div>
                        <div class="mb-2">
                            <small class="text-muted" id="progressDetails"></small>
                        </div>
                        <div class="mt-3" id="currentItem" style="display: none;">
                            <div class="alert alert-info mb-0">
                                <i class="bi bi-hourglass-split"></i> 当前分析: <span id="currentItemName"></span> 
                                (<span id="currentItemSize"></span>)
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- 分析结果 -->
        <div class="row" id="resultsSection">
            <div class="col-12">
                <div class="card">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <ul class="nav nav-tabs card-header-tabs" id="resultTabs" role="tablist">
                            <li class="nav-item" role="presentation">
                                <button class="nav-link active" id="table-tab" data-bs-toggle="tab" data-bs-target="#table-view" type="button" role="tab">表格视图</button>
                            </li>
                            <li class="nav-item" role="presentation">
                                <button class="nav-link" id="tree-tab" data-bs-toggle="tab" data-bs-target="#tree-view" type="button" role="tab">树形视图</button>
                            </li>
                        </ul>
                        <div>
                            <button class="btn btn-sm btn-outline-secondary" onclick="refreshResults()">
                                <i class="bi bi-arrow-clockwise"></i> 刷新
                            </button>
                        </div>
                    </div>
                    <div class="card-body">
                        <div class="tab-content" id="resultTabsContent">
                            <div class="tab-pane fade show active" id="table-view" role="tabpanel">
                                <div class="table-responsive">
                                    <table class="table table-hover" id="resultsTable">
                                        <thead class="table-light">
                                            <tr>
                                                <th>大小</th>
                                                <th>文件数</th>
                                                <th>目录数</th>
                                                <th>最后修改</th>
                                                <th>路径</th>
                                                <th>操作</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            <tr>
                                                <td colspan="6" class="text-center text-muted">
                                                    点击"开始分析"查看结果
                                                </td>
                                            </tr>
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                            <div class="tab-pane fade" id="tree-view" role="tabpanel">
                                <div class="mb-3 d-flex justify-content-between align-items-center">
                                    <div>
                                        <small class="text-muted">
                                            <i class="bi bi-info-circle"></i>
                                            树形视图显示目录层级结构，子目录已按大小降序排列。
                                            <span id="treeDepthInfo"></span>
                                        </small>
                                        <button class="btn btn-sm btn-outline-primary ms-2" onclick="reanalyzeWithDifferentDepth()" id="reanalyzeBtn" style="display: none;">
                                            <i class="bi bi-arrow-repeat"></i> 重新分析
                                        </button>
                                    </div>
                                    <div id="treeControlButtons" style="display: none;">
                                        <button class="btn btn-sm btn-outline-success me-1" onclick="expandAllTreeNodes()" title="展开所有节点">
                                            <i class="bi bi-arrows-expand"></i> 全部展开
                                        </button>
                                        <button class="btn btn-sm btn-outline-warning" onclick="collapseAllTreeNodes()" title="折叠所有节点">
                                            <i class="bi bi-arrows-collapse"></i> 全部折叠
                                        </button>
                                    </div>
                                </div>
                                <div id="treeContainer" style="min-height: 400px;">
                                    <div class="text-center text-muted py-5">
                                        <i class="bi bi-diagram-3" style="font-size: 3rem;"></i>
                                        <p class="mt-3">点击“开始分析”后切换到此标签页查看树形结构</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- 删除确认模态框 -->
    <div class="modal fade" id="deleteModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header bg-danger text-white">
                    <h5 class="modal-title"><i class="bi bi-exclamation-triangle"></i> 确认删除</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <p>您确定要删除以下目录吗？</p>
                    <div class="alert alert-warning">
                        <strong>路径:</strong> <span id="deletePath"></span><br>
                        <strong>大小:</strong> <span id="deleteSize"></span><br>
                        <strong>文件数:</strong> <span id="deleteFiles"></span>
                    </div>
                    <div class="alert alert-danger">
                        <i class="bi bi-shield-exclamation"></i> 
                        <strong>警告:</strong> 此操作不可恢复，请谨慎操作！
                    </div>
                    
                    <!-- 安全验证步骤 -->
                    <div class="mt-3">
                        <h6 class="text-danger"><i class="bi bi-shield-lock"></i> 安全验证</h6>
                        
                        <!-- 步骤1: 路径验证 -->
                        <div class="mb-3">
                            <label for="deletePathInput" class="form-label">
                                <strong>步骤1:</strong> 请手动输入完整路径（禁止粘贴）
                            </label>
                            <input type="text" class="form-control" id="deletePathInput" 
                                   placeholder="手动输入待删除路径" autocomplete="off">
                            <div class="form-text" id="pathMatchStatus">
                                <span id="pathMatchIcon"></span>
                                <span id="pathMatchText">请输入完整路径进行验证</span>
                            </div>
                        </div>
                        
                        <!-- 步骤2: 验证码 -->
                        <div class="mb-3" id="captchaSection" style="display: none;">
                            <label for="captchaInput" class="form-label">
                                <strong>步骤2:</strong> 请计算并输入答案
                            </label>
                            <div class="input-group">
                                <span class="input-group-text bg-warning" id="captchaQuestion">
                                    <strong>? + ? = ?</strong>
                                </span>
                                <input type="number" class="form-control" id="captchaInput" 
                                       placeholder="输入答案" autocomplete="off">
                            </div>
                            <div class="form-text" id="captchaStatus">
                                <span id="captchaIcon"></span>
                                <span id="captchaText">请输入正确答案</span>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                    <button type="button" class="btn btn-danger" id="confirmDeleteBtn" disabled>
                        <i class="bi bi-trash"></i> 确认删除
                    </button>
                </div>
            </div>
        </div>
    </div>

    <!-- 分区目录树弹窗 -->
    <div class="modal fade" id="partitionTreeModal" tabindex="-1">
        <div class="modal-dialog modal-xl">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">
                        <i class="bi bi-diagram-3"></i> 分区目录结构 - <span id="partitionTreeTitle"></span>
                    </h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body" id="partitionTreeBody">
                    <div class="text-center text-muted py-5">
                        <div class="spinner-border" role="status">
                            <span class="visually-hidden">加载中...</span>
                        </div>
                        <p class="mt-3">正在分析目录结构...</p>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                    <button type="button" class="btn btn-primary" id="analyzePartitionBtn" style="display: none;">
                        <i class="bi bi-search"></i> 分析此目录
                    </button>
                </div>
            </div>
        </div>
    </div>

    <!-- JavaScript -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        let currentDeletePath = null;
        let analysisInterval = null;  // 用于定期检查分析进度
        let currentAnalysisId = null;  // 当前分析的ID
        let captchaAnswer = null;  // 当前验证码答案

        // 页面加载时获取系统信息
        document.addEventListener('DOMContentLoaded', function() {
            loadSystemInfo();
            
            // 侧边栏折叠/展开功能
            const sidebar = document.getElementById('sidebar');
            const mainContent = document.getElementById('mainContent');
            const sidebarToggle = document.getElementById('sidebarToggle');
            
            if (sidebar && mainContent && sidebarToggle) {
                const toggleIcon = sidebarToggle.querySelector('i');
                
                // 检查localStorage中是否有保存的状态
                const savedState = localStorage.getItem('sidebarCollapsed');
                if (savedState === 'true') {
                    sidebar.classList.add('collapsed');
                    mainContent.classList.add('sidebar-collapsed');
                    if (toggleIcon) {
                        toggleIcon.classList.remove('bi-chevron-left');
                        toggleIcon.classList.add('bi-chevron-right');
                    }
                }
                
                // 响应式设计：小屏幕默认折叠
                if (window.innerWidth < 1200 && !savedState) {
                    sidebar.classList.add('collapsed');
                    mainContent.classList.add('sidebar-collapsed');
                    if (toggleIcon) {
                        toggleIcon.classList.remove('bi-chevron-left');
                        toggleIcon.classList.add('bi-chevron-right');
                    }
                }
                
                // 折叠/展开切换
                sidebarToggle.addEventListener('click', function() {
                    const isCollapsed = sidebar.classList.toggle('collapsed');
                    mainContent.classList.toggle('sidebar-collapsed');
                    
                    if (toggleIcon) {
                        if (isCollapsed) {
                            toggleIcon.classList.remove('bi-chevron-left');
                            toggleIcon.classList.add('bi-chevron-right');
                        } else {
                            toggleIcon.classList.remove('bi-chevron-right');
                            toggleIcon.classList.add('bi-chevron-left');
                        }
                    }
                    
                    // 保存状态到localStorage
                    localStorage.setItem('sidebarCollapsed', isCollapsed);
                });
            } else {
                console.warn('侧边栏元素未找到');
            }
            
            // 监听路径和深度输入，更新迷你显示
            document.getElementById('pathInput').addEventListener('input', function() {
                const path = this.value || '/';
                document.getElementById('miniPath').textContent = path.length > 10 ? path.substring(0, 10) + '...' : path;
            });
            
            document.getElementById('depthInput').addEventListener('change', function() {
                document.getElementById('miniDepth').textContent = this.value;
            });
            
            // 系统磁盘信息折叠功能
            const toggleDiskInfo = document.getElementById('toggleDiskInfo');
            const diskInfoCard = document.getElementById('diskInfoCard');
            
            if (toggleDiskInfo && diskInfoCard) {
                const diskInfoToggleIcon = toggleDiskInfo.querySelector('i');
                
                toggleDiskInfo.addEventListener('click', function() {
                    const isCollapsed = diskInfoCard.classList.toggle('collapsed');
                    
                    if (diskInfoToggleIcon) {
                        if (isCollapsed) {
                            diskInfoToggleIcon.classList.remove('bi-chevron-up');
                            diskInfoToggleIcon.classList.add('bi-chevron-down');
                        } else {
                            diskInfoToggleIcon.classList.remove('bi-chevron-down');
                            diskInfoToggleIcon.classList.add('bi-chevron-up');
                        }
                    }
                });
            } else {
                console.warn('系统磁盘信息折叠元素未找到');
            }
            
            // 添加路径选择按钮事件监听器
            document.getElementById('browsePathBtn').addEventListener('click', function() {
                // 获取当前路径
                const currentPath = document.getElementById('pathInput').value || '/';
                
                // 显示目录选择器
                showDirectorySelector(currentPath);
            });
            
            // 添加排除路径选择按钮事件监听器
            document.getElementById('browseExcludePathBtn').addEventListener('click', function() {
                // 获取当前路径
                const currentPath = document.getElementById('excludePathsInput').value || '/';
                
                // 显示目录选择器，但用于排除路径
                showExcludeDirectorySelector(currentPath);
            });
            
            // 初始化排除路径列表
            initializeExcludePathsList();
        });

        // 初始化排除路径列表
        function initializeExcludePathsList() {
            // 默认排除路径
            const defaultExcludePaths = [
                '/proc', '/sys', '/run', '/var/tmp', '/boot', 
                '/lost+found', '~/.cache', '/var/cache', '/media', '/mnt'
            ];
            
            const container = document.getElementById('excludePathsList');
            container.innerHTML = '';
            
            // 为每个默认路径创建复选框
            defaultExcludePaths.forEach(path => {
                const div = document.createElement('div');
                div.className = 'form-check';
                
                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.className = 'form-check-input';
                checkbox.id = `excludePath_${path.replace(/[^a-zA-Z0-9]/g, '_')}`;
                checkbox.value = path;
                
                // 检查该路径是否已在输入框中
                const currentPaths = getExcludePathsFromInput();
                if (currentPaths.includes(path)) {
                    checkbox.checked = true;
                }
                
                // 添加事件监听器
                checkbox.addEventListener('change', function() {
                    updateExcludePathsInput();
                });
                
                const label = document.createElement('label');
                label.className = 'form-check-label';
                label.htmlFor = checkbox.id;
                label.textContent = path;
                
                div.appendChild(checkbox);
                div.appendChild(label);
                container.appendChild(div);
            });
            
            // 添加自定义路径输入事件监听器
            document.getElementById('excludePathsInput').addEventListener('input', function() {
                syncExcludePathsList();
            });
        }

        // 从输入框获取排除路径数组
        function getExcludePathsFromInput() {
            const input = document.getElementById('excludePathsInput');
            return input.value.split(',').map(p => p.trim()).filter(p => p);
        }

        // 更新输入框中的排除路径
        function updateExcludePathsInput() {
            const checkboxes = document.querySelectorAll('#excludePathsList input[type="checkbox"]');
            const selectedPaths = [];
            
            checkboxes.forEach(checkbox => {
                if (checkbox.checked) {
                    selectedPaths.push(checkbox.value);
                }
            });
            
            // 获取输入框中的其他路径
            const inputPaths = getExcludePathsFromInput();
            const defaultPaths = Array.from(checkboxes).map(cb => cb.value);
            
            // 过滤出不在默认路径列表中的自定义路径
            const customPaths = inputPaths.filter(path => !defaultPaths.includes(path));
            
            // 合并选中的默认路径和自定义路径
            const allPaths = [...selectedPaths, ...customPaths];
            
            // 更新输入框
            document.getElementById('excludePathsInput').value = allPaths.join(', ');
        }

        // 显示目录选择器
        function showDirectorySelector(initialPath) {
            showDirectorySelectorModal(initialPath, '选择分析目录', function(selectedPath) {
                document.getElementById('pathInput').value = selectedPath;
            });
        }

        // 显示排除路径目录选择器
        function showExcludeDirectorySelector(initialPath) {
            showDirectorySelectorModal(initialPath, '选择排除目录', function(selectedPath) {
                // 获取当前排除路径
                const currentExcludePaths = getExcludePathsFromInput();
                
                // 如果路径尚未在排除列表中，则添加
                if (!currentExcludePaths.includes(selectedPath)) {
                    currentExcludePaths.push(selectedPath);
                    document.getElementById('excludePathsInput').value = currentExcludePaths.join(', ');
                    
                    // 同步复选框状态
                    syncExcludePathsList();
                }
            });
        }

        // 显示通用目录选择器模态框
        function showDirectorySelectorModal(initialPath, title, onSelectCallback) {
            // 创建模态框
            const modalHtml = `
                <div class="modal fade" id="directorySelectorModal" tabindex="-1">
                    <div class="modal-dialog modal-lg">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">${title}</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body">
                                <div class="mb-3">
                                    <label class="form-label">当前路径:</label>
                                    <input type="text" class="form-control" id="currentPathDisplay" readonly>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">子目录列表:</label>
                                    <div id="directoryList" class="border rounded p-2" style="max-height: 300px; overflow-y: auto;">
                                        <div class="text-center text-muted">加载中...</div>
                                    </div>
                                </div>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                                <button type="button" class="btn btn-primary" id="selectCurrentPathBtn">选择当前路径</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            // 添加模态框到页面
            let modalElement = document.getElementById('directorySelectorModal');
            if (!modalElement) {
                const modalContainer = document.createElement('div');
                modalContainer.innerHTML = modalHtml;
                document.body.appendChild(modalContainer);
                modalElement = document.getElementById('directorySelectorModal');
            }
            
            // 显示模态框
            const modal = new bootstrap.Modal(modalElement);
            modal.show();
            
            // 设置初始路径
            document.getElementById('currentPathDisplay').value = initialPath;
            
            // 加载目录列表
            loadDirectoryList(initialPath, 1);
            
            // 添加选择当前路径按钮事件
            document.getElementById('selectCurrentPathBtn').onclick = function() {
                const selectedPath = document.getElementById('currentPathDisplay').value;
                onSelectCallback(selectedPath);
                modal.hide();
            };
        }

        // 加载目录列表
        function loadDirectoryList(path, depth) {
            const directoryListElement = document.getElementById('directoryList');
            directoryListElement.innerHTML = '<div class="text-center text-muted">加载中...</div>';
            
            fetch('/api/list-directories', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    path: path,
                    max_depth: Math.min(depth, 5)  // 限制最大深度为5层
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    renderDirectoryList(data.directories, path);
                } else {
                    directoryListElement.innerHTML = `<div class="alert alert-danger">加载失败: ${data.error}</div>`;
                }
            })
            .catch(error => {
                directoryListElement.innerHTML = `<div class="alert alert-danger">加载失败: ${error.message}</div>`;
            });
        }

        // 渲染目录列表
        function renderDirectoryList(directories, basePath) {
            const directoryListElement = document.getElementById('directoryList');
            
            if (!directories || directories.length === 0) {
                directoryListElement.innerHTML = '<div class="text-center text-muted">该目录下没有子目录</div>';
                return;
            }
            
            directoryListElement.innerHTML = '';
            
            // 递归渲染目录树
            function renderDirectoryTree(dirs, container, level = 0) {
                dirs.forEach(dir => {
                    const div = document.createElement('div');
                    div.style.marginLeft = `${level * 20}px`;
                    div.className = 'directory-item mb-1';
                    
                    const button = document.createElement('button');
                    button.type = 'button';
                    button.className = 'btn btn-sm btn-outline-primary w-100 text-start';
                    button.innerHTML = `
                        <i class="bi bi-folder me-2"></i>
                        ${dir.name}
                    `;
                    
                    button.onclick = function() {
                        // 更新当前路径显示
                        document.getElementById('currentPathDisplay').value = dir.path;
                        
                        // 如果有子目录，加载下一级
                        if (dir.children && dir.children.length > 0) {
                            renderDirectoryTree(dir.children, container, level + 1);
                        } else if (dir.level < 4) {  // 如果还没达到最大深度，尝试加载更多
                            loadDirectoryList(dir.path, 1);
                        }
                    };
                    
                    div.appendChild(button);
                    container.appendChild(div);
                    
                    // 如果有子目录，递归渲染
                    if (dir.children && dir.children.length > 0) {
                        renderDirectoryTree(dir.children, container, level + 1);
                    }
                });
            }
            
            renderDirectoryTree(directories, directoryListElement);
        }

        // 加载系统磁盘信息
        function loadSystemInfo() {
            fetch('/api/partitions')
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    // 检查响应是否成功
                    if (!data || !data.success) {
                        console.error('获取分区信息失败:', data ? data.error : '未知错误');
                        const diskInfo = document.getElementById('diskInfo');
                        if (diskInfo) {
                            diskInfo.innerHTML = '<div class="col-12"><p class="text-muted text-center">获取分区信息失败</p></div>';
                        }
                        return;
                    }
                            
                    const diskInfo = document.getElementById('diskInfo');
                    if (!diskInfo) {
                        console.error('无法找到diskInfo元素');
                        return;
                    }
                            
                    diskInfo.innerHTML = '';
                            
                    const partitions = data.partitions || [];
                    
                    partitions.forEach((partition, index) => {
                        const usageColor = partition.usage_percent > 80 ? 'danger' : 
                                         partition.usage_percent > 60 ? 'warning' : 'success';
                        
                        // 判断分区类型和显示文本
                        let partitionTypeLabel = '本地磁盘';
                        let partitionClass = 'local-disk';
                        if (partition.partition_type === 'remote') {
                            partitionTypeLabel = '远程挂载';
                            partitionClass = 'remote-disk';
                        } else if (partition.partition_type === 'other') {
                            partitionTypeLabel = '其他';
                            partitionClass = 'other-disk';
                        }
                        
                        const icon = partition.icon || 'bi-hdd-fill';
                        const cardId = `partition-card-${index}`;
                        
                        // 获取保存的模式，默认为full
                        const savedMode = localStorage.getItem('partition-mode-' + partition.mount_point) || 'full';
                        
                        // 构建设备信息显示
                        const deviceInfo = `
                            <div class="device-info">
                                <small>
                                    <i class="bi bi-disc"></i> 设备: ${partition.device || '未知'}<br>
                                    <i class="bi bi-file-earmark-text"></i> 文件系统: ${partition.fs_type || '未知'}
                                </small>
                            </div>
                        `;
                        
                        // Mini模式内容
                        const miniContent = `
                            <div class="partition-mini-content">
                                <div class="mini-progress-circle" style="--progress: ${partition.usage_percent * 3.6}deg;">
                                    ${partition.usage_percent || 0}%
                                </div>
                                <span class="mini-name">${partition.mount_point || '未知'}</span>
                            </div>
                        `;
                        
                        // 横条模式内容
                        const barContent = `
                            <div class="partition-bar-content" style="display: none;">
                                <div class="bar-header">
                                    <h6 class="card-title mb-0">
                                        <i class="bi ${icon}"></i> ${partition.mount_point || '未知'}
                                    </h6>
                                    <span class="partition-badge">${partitionTypeLabel}</span>
                                </div>
                                <div class="progress mb-2" style="height: 10px; background-color: rgba(255,255,255,0.3);">
                                    <div class="progress-bar bg-light" 
                                         style="width: ${partition.usage_percent || 0}%"></div>
                                </div>
                                <div class="bar-info">
                                    <span><i class="bi bi-hdd"></i> 总计: ${partition.total || '未知'}</span>
                                    <span><i class="bi bi-pie-chart"></i> 已用: ${partition.usage_percent || 0}%</span>
                                    <span><i class="bi bi-check-circle"></i> 可用: ${partition.free || '未知'}</span>
                                </div>
                            </div>
                        `;
                        
                        // 完整模式内容
                        const fullContent = `
                            <div class="partition-full-content">
                                <div class="d-flex justify-content-between align-items-start mb-2">
                                    <h6 class="card-title mb-0">
                                        <i class="bi ${icon}"></i> ${partition.mount_point || '未知'}
                                    </h6>
                                    <span class="partition-badge">${partitionTypeLabel}</span>
                                </div>
                                <div class="progress mb-2" style="height: 10px; background-color: rgba(255,255,255,0.3);">
                                    <div class="progress-bar bg-light" 
                                         style="width: ${partition.usage_percent || 0}%"></div>
                                </div>
                                <small>
                                    总计: ${partition.total || '未知'} | 已用: ${partition.used || '未知'} | 
                                    可用: ${partition.free || '未知'} (${partition.usage_percent || 0}%)
                                </small>
                                ${deviceInfo}
                            </div>
                        `;
                        
                        diskInfo.innerHTML += `
                            <div class="col-md-6 col-lg-4 mb-3">
                                <div id="${cardId}" class="card partition-card ${partitionClass} mode-${savedMode}" 
                                     onclick="showPartitionTree('${partition.mount_point || ''}')" 
                                     style="border: none;" 
                                     data-mount-point="${partition.mount_point || ''}">
                                    <button class="card-mode-toggle" 
                                            onclick="event.stopPropagation(); toggleCardMode('${cardId}', '${partition.mount_point || ''}')" 
                                            title="切换显示模式">
                                        <i class="bi bi-arrows-angle-contract"></i>
                                    </button>
                                    <div class="card-body">
                                        ${miniContent}
                                        ${barContent}
                                        ${fullContent}
                                    </div>
                                </div>
                            </div>
                        `;
                    });
                    
                    if (partitions.length === 0) {
                        diskInfo.innerHTML = '<div class="col-12"><p class="text-muted text-center">未检测到可用分区</p></div>';
                    }
                    
                    // 生成摘要信息
                    const totalCapacity = partitions.reduce((sum, p) => sum + (p.total_bytes || 0), 0);
                    const usedCapacity = partitions.reduce((sum, p) => sum + ((p.total_bytes || 0) * (p.usage_percent || 0) / 100), 0);
                    const avgUsage = partitions.length > 0 ? (usedCapacity / totalCapacity * 100).toFixed(1) : 0;
                    const summaryText = `共 ${partitions.length} 个分区 | 平均使用率: ${avgUsage}%`;
                    const summaryElement = document.getElementById('diskSummaryText');
                    if (summaryElement) {
                        summaryElement.textContent = summaryText;
                    }
                })
                .catch(error => {
                    console.error('获取系统信息失败:', error);
                    const diskInfo = document.getElementById('diskInfo');
                    if (diskInfo) {
                        diskInfo.innerHTML = '<div class="col-12"><p class="text-muted text-center">获取系统信息失败: ' + error.message + '</p></div>';
                    }
                });
        }
        
        // 切换卡片显示模式
        function toggleCardMode(cardId, mountPoint) {
            const card = document.getElementById(cardId);
            if (!card) return;
            
            // 获取当前模式
            let currentMode = 'full';
            if (card.classList.contains('mode-mini')) currentMode = 'mini';
            else if (card.classList.contains('mode-bar')) currentMode = 'bar';
            else if (card.classList.contains('mode-full')) currentMode = 'full';
            
            // 循环切换: full -> bar -> mini -> full
            let newMode = 'full';
            if (currentMode === 'full') newMode = 'bar';
            else if (currentMode === 'bar') newMode = 'mini';
            else if (currentMode === 'mini') newMode = 'full';
            
            // 更新样式
            card.classList.remove('mode-mini', 'mode-bar', 'mode-full');
            card.classList.add('mode-' + newMode);
            
            // 更新bar-content的显示状态
            const barContent = card.querySelector('.partition-bar-content');
            if (barContent) {
                barContent.style.display = newMode === 'bar' ? 'block' : 'none';
            }
            
            // 更新按钮图标
            const toggleBtn = card.querySelector('.card-mode-toggle i');
            if (toggleBtn) {
                toggleBtn.className = newMode === 'mini' ? 'bi bi-arrows-angle-expand' : 
                                      newMode === 'bar' ? 'bi bi-arrows-angle-contract' : 
                                      'bi bi-arrows-angle-contract';
            }
            
            // 保存到localStorage
            localStorage.setItem('partition-mode-' + mountPoint, newMode);
        }

        // 表单提交
        document.getElementById('analysisForm').addEventListener('submit', function(e) {
            e.preventDefault();
            startAnalysis();
        });

        // 开始分析
        function startAnalysis() {
            const path = document.getElementById('pathInput').value;
            const depth = document.getElementById('depthInput').value;
            const limit = document.getElementById('limitInput').value;
            const excludePaths = document.getElementById('excludePathsInput').value;
            const excludeExtensions = document.getElementById('excludeExtensionsInput').value;

            if (!path) {
                alert('请输入要分析的路径');
                return;
            }

            // 自动隐藏分析设置侧边栏
            const sidebar = document.getElementById('sidebar');
            const mainContent = document.getElementById('mainContent');
            const toggleIcon = document.querySelector('#sidebarToggle i');
            
            if (sidebar && mainContent && toggleIcon) {
                // 检查侧边栏是否已经折叠
                if (!sidebar.classList.contains('collapsed')) {
                    // 折叠侧边栏
                    sidebar.classList.add('collapsed');
                    mainContent.classList.add('sidebar-collapsed');
                    
                    // 更新图标
                    toggleIcon.classList.remove('bi-chevron-left');
                    toggleIcon.classList.add('bi-chevron-right');
                    
                    // 保存状态到localStorage
                    localStorage.setItem('sidebarCollapsed', 'true');
                }
            }

            // 显示加载动画
            document.getElementById('loadingSection').style.display = 'block';
            document.getElementById('resultsSection').style.display = 'none';
            
            // 重置进度显示
            document.getElementById('analysisProgress').style.width = '0%';
            document.getElementById('analysisProgress').textContent = '0%';
            document.getElementById('progressText').textContent = '准备开始分析...';
            document.getElementById('progressDetails').textContent = '';
            document.getElementById('currentItem').style.display = 'none';

            // 发送分析请求
            fetch('/api/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    path: path,
                    depth: parseInt(depth),
                    limit: parseInt(limit),
                    exclude_paths: excludePaths ? excludePaths.split(',').map(p => p.trim()).filter(p => p) : [],
                    exclude_extensions: excludeExtensions ? excludeExtensions.split(',').map(e => e.trim()).filter(e => e) : []
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.analysis_id) {
                    currentAnalysisId = data.analysis_id;
                    // 开始定期检查进度
                    startProgressPolling();
                } else {
                    throw new Error(data.error || '分析启动失败');
                }
            })
            .catch(error => {
                console.error('分析启动失败:', error);
                alert('分析启动失败: ' + error.message);
                document.getElementById('loadingSection').style.display = 'none';
            });
        }

        // 开始定期检查分析进度
        function startProgressPolling() {
            if (analysisInterval) {
                clearInterval(analysisInterval);
            }
            
            analysisInterval = setInterval(checkAnalysisProgress, 500);  // 每500毫秒检查一次
        }

        // 检查分析进度
        function checkAnalysisProgress() {
            if (!currentAnalysisId) return;
            
            fetch(`/api/analysis-progress/${currentAnalysisId}`)
            .then(response => response.json())
            .then(data => {
                updateProgressDisplay(data);
                
                // 如果分析完成或出错，停止轮询
                if (data.status === 'completed' || data.status === 'error') {
                    if (analysisInterval) {
                        clearInterval(analysisInterval);
                        analysisInterval = null;
                    }
                    
                    if (data.status === 'completed') {
                        displayResults(data);
                        document.getElementById('loadingSection').style.display = 'none';
                        document.getElementById('resultsSection').style.display = 'block';
                    } else if (data.status === 'error') {
                        alert('分析出错: ' + data.message);
                        document.getElementById('loadingSection').style.display = 'none';
                    }
                }
            })
            .catch(error => {
                console.error('获取进度失败:', error);
                // 如果获取进度失败，停止轮询
                if (analysisInterval) {
                    clearInterval(analysisInterval);
                    analysisInterval = null;
                }
            });
        }

        // 更新进度显示
        function updateProgressDisplay(data) {
            const progressBar = document.getElementById('analysisProgress');
            const progressText = document.getElementById('progressText');
            const progressDetails = document.getElementById('progressDetails');
            const currentItemDiv = document.getElementById('currentItem');
            const currentItemName = document.getElementById('currentItemName');
            const currentItemSize = document.getElementById('currentItemSize');
            
            if (data.status === 'analyzing') {
                // 更新进度条
                progressBar.style.width = data.progress + '%';
                progressBar.textContent = data.progress + '%';
                
                // 更新文本信息
                progressText.textContent = `正在分析目录 (${data.processed}/${data.total})`;
                progressDetails.textContent = `已完成 ${data.processed} 个目录，共 ${data.total} 个目录`;
                
                // 显示当前分析项
                if (data.current_item) {
                    currentItemDiv.style.display = 'block';
                    currentItemName.textContent = data.current_item;
                    currentItemSize.textContent = data.current_size;
                } else {
                    currentItemDiv.style.display = 'none';
                }
            } else if (data.status === 'completed') {
                progressBar.style.width = '100%';
                progressBar.textContent = '100%';
                progressText.textContent = '分析完成';
                progressDetails.textContent = `分析完成，找到 ${data.count} 个目录，耗时 ${data.elapsed_time} 秒`;
                currentItemDiv.style.display = 'none';
            } else if (data.status === 'error') {
                progressBar.style.width = '100%';
                progressBar.textContent = '错误';
                progressBar.className = 'progress-bar bg-danger';
                progressText.textContent = '分析出错';
                progressDetails.textContent = data.message;
                currentItemDiv.style.display = 'none';
            } else if (data.status === 'started') {
                progressBar.style.width = '0%';
                progressBar.textContent = '0%';
                progressText.textContent = data.message;
                progressDetails.textContent = '';
                currentItemDiv.style.display = 'none';
            }
        }

        // 安全的路径编码函数（支持中文等非Latin1字符）
        function safePathEncode(path) {
            try {
                // 使用 encodeURIComponent 然后替换特殊字符
                return encodeURIComponent(path).replace(/[^a-zA-Z0-9]/g, '_');
            } catch (e) {
                // 如果编码失败，使用路径的哈希值
                let hash = 0;
                for (let i = 0; i < path.length; i++) {
                    const char = path.charCodeAt(i);
                    hash = ((hash << 5) - hash) + char;
                    hash = hash & hash; // Convert to 32bit integer
                }
                return 'path_' + Math.abs(hash);
            }
        }
        
        // 设置表格样式，优化路径显示
        const style = document.createElement('style');
        style.textContent = `
            #resultsTable {
                table-layout: auto;
                width: 100%;
            }
                        
            #resultsTable tbody tr {
                height: auto;
            }
                        
            #resultsTable tbody td {
                vertical-align: middle;
                word-break: break-word;
            }
                        
            /* 路径列样式 */
            #resultsTable td:nth-child(5) {
                max-width: 350px;
                overflow: hidden;
                position: relative;
            }
                        
            #resultsTable code {
                display: block;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                max-width: 100%;
            }
                        
            /* 大小列样式 - 固定宽度，避免被路径挤压 */
            #resultsTable td:nth-child(1) {
                min-width: 100px;
                font-weight: bold;
            }
                        
            /* 文件数和目录数列 */
            #resultsTable td:nth-child(2),
            #resultsTable td:nth-child(3) {
                min-width: 70px;
                text-align: center;
            }
                        
            /* 最后修改列 */
            #resultsTable td:nth-child(4) {
                min-width: 100px;
                white-space: nowrap;
            }
                        
            /* 操作列 */
            #resultsTable td:nth-child(6) {
                min-width: 60px;
                text-align: center;
            }
                        
            /* 路径代码块的悬停效果 */
            #resultsTable code:hover {
                background-color: #f0f0f0;
                text-decoration: underline;
            }
        `;
        document.head.appendChild(style);
                
        // 全局变量：存储树形结构数据和展开状态
        let treeStructureData = null;
        let expandedRows = new Set(); // 存储已展开的行路径
        function drillDownToPath(path) {
            console.log('drillDownToPath called with path:', path);
            
            // 获取当前活跃的标签页
            const navTabs = document.querySelectorAll('#resultsSection .nav-link');
            let activeTab = null;
            navTabs.forEach(tab => {
                if (tab.classList.contains('active')) {
                    activeTab = tab.getAttribute('data-bs-target');
                }
            });
            
            console.log('Active tab:', activeTab);
            
            // 如果在表格视图标签页，则在表格中展开
            if (activeTab === '#table-view') {
                const tbody = document.querySelector('#resultsTable tbody');
                if (tbody) {
                    const rows = Array.from(tbody.querySelectorAll('tr'));
                    const currentRow = rows.find(row => row.getAttribute('data-path') === path);
                    if (currentRow) {
                        console.log('Found row in table, toggling...');
                        toggleTableRow(path);
                        return;
                    }
                }
            }
            
            // 如果在树形视图标签页，则在树形视图中展开
            if (activeTab === '#tree-view') {
                const treeNodeId = 'tree_' + safePathEncode(path);
                console.log('Looking for tree node with id:', treeNodeId);
                const treeNode = document.getElementById(treeNodeId);
                if (treeNode) {
                    console.log('Found tree node, toggling...');
                    toggleTreeNodeExpand(treeNodeId);
                    return;
                }
            }
            
            console.log('Could not find element to expand in active tab');
        }
        
        // 显示分析结果
        function displayResults(data) {
            const tbody = document.querySelector('#resultsTable tbody');
            tbody.innerHTML = '';

            // 获取结果数据（可能是直接来自分析API或进度API）
            const results = data.results || [];
            
            if (results && results.length > 0) {
                // 按大小排序（降序）
                results.sort((a, b) => b.size_bytes - a.size_bytes);
                
                // 保存分析深度信息
                const analysisDepth = data.depth || parseInt(document.getElementById('depthInput').value) || 3;
                const rootPath = data.path || '/';
                
                // 构建树形结构数据用于表格视图
                buildTableTreeStructure(results);
                
                // 只显示顶层目录（根目录的直接子目录）
                const topLevelDirs = results.filter(item => {
                    const itemPath = item.path;
                    
                    // 特殊处理：如果根路径是 '/'，则计算绝对路径深度
                    if (rootPath === '/') {
                        // 移除开头的 /，然后分割
                        const pathWithoutRoot = itemPath.substring(1);
                        const pathParts = pathWithoutRoot.split('/').filter(p => p);
                        // 只显示第一层：如 /var, /usr, /home
                        return pathParts.length === 1;
                    } else {
                        // 其他情况：计算相对路径深度
                        const rootPathNormalized = rootPath.endsWith('/') ? rootPath : rootPath + '/';
                        
                        // 如果路径不以根目录开头，跳过
                        if (!itemPath.startsWith(rootPathNormalized) && itemPath !== rootPath) {
                            return false;
                        }
                        
                        // 计算相对路径
                        const relativePath = itemPath === rootPath ? '' : itemPath.substring(rootPathNormalized.length);
                        
                        // 只显示第一层
                        const pathParts = relativePath.split('/').filter(p => p);
                        return pathParts.length === 1;
                    }
                });
                
                console.log(`Total results: ${results.length}, Top level dirs: ${topLevelDirs.length}`);
                console.log('Root path:', rootPath);
                console.log('Sample top level dirs:', topLevelDirs.slice(0, 5).map(d => d.path));
                
                topLevelDirs.forEach((item, index) => {
                    const row = document.createElement('tr');
                    const lastModified = item.last_modified ? 
                        new Date(item.last_modified * 1000).toLocaleDateString() : '未知';
                    
                    // 检查是否有子目录
                    const hasChildren = checkHasChildren(item.path, results);
                    const isExpanded = expandedRows.has(item.path);
                    
                    row.setAttribute('data-path', item.path);
                    row.setAttribute('data-level', '0');
                                        
                    row.innerHTML = `
                        <td>
                            ${hasChildren ? `
                                <i class="toggle-icon bi ${isExpanded ? 'bi-chevron-down' : 'bi-chevron-right'} text-primary me-1" 
                                   style="cursor: pointer;"></i>
                            ` : '<span style="display: inline-block; width: 20px;"></span>'}
                            <strong>${item.size_human}</strong>
                        </td>
                        <td>${item.file_count}</td>
                        <td>${item.dir_count}</td>
                        <td>${lastModified}</td>
                        <td>
                            <code style="font-size: 0.9em; cursor: pointer; color: #0066cc;" 
                                  class="drill-down-path"
                                  title="点击下钻查看此目录">${item.path}</code>
                        </td>
                        <td>
                            <button class="btn btn-sm btn-outline-danger" 
                                    onclick="confirmDelete('${item.path}', '${item.size_human}', ${item.file_count})"
                                    ${item.error ? 'disabled' : ''}>
                                <i class="bi bi-trash"></i>
                            </button>
                        </td>
                    `;
                    tbody.appendChild(row);
                                        
                    // 为路径添加点击事件处理器
                    const pathCode = row.querySelector('.drill-down-path');
                    if (pathCode) {
                        pathCode.addEventListener('click', function(e) {
                            e.stopPropagation();
                            drillDownToPath(item.path);
                        });
                        // 添加 Tooltip：鼠标悬停显示完整路径
                        pathCode.title = item.path;
                        pathCode.style.cursor = 'pointer';
                    }
                                        
                    // 为展开图标添加点击事件处理器
                    const toggleIcon = row.querySelector('.toggle-icon');
                    if (toggleIcon) {
                        toggleIcon.addEventListener('click', function(e) {
                            e.stopPropagation();
                            toggleTableRow(item.path);
                        });
                    }
                });
                
                // 更新树形结构（无论当前在哪个标签页）
                loadTreeStructure(data);
            } else {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="6" class="text-center text-muted">
                            ${data.error || '没有找到结果'}
                        </td>
                    </tr>
                `;
            }
        }
        
        // 构建表格树形结构数据
        function buildTableTreeStructure(results) {
            treeStructureData = {};
            results.forEach(item => {
                treeStructureData[item.path] = item;
            });
        }
        
        // 检查是否有子目录
        function checkHasChildren(path, results) {
            // 确保路径以/结尾用于比较
            const normalizedPath = path.endsWith('/') ? path : path + '/';
            return results.some(item => {
                return item.path !== path && item.path.startsWith(normalizedPath) && 
                       item.path.substring(normalizedPath.length).split('/').filter(p => p).length === 1;
            });
        }
        
        // 切换表格行展开/折叠
        function toggleTableRow(path) {
            const tbody = document.querySelector('#resultsTable tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            
            // 查找当前行
            const currentRow = rows.find(row => row.getAttribute('data-path') === path);
            if (!currentRow) return;
            
            const isExpanded = expandedRows.has(path);
            const icon = currentRow.querySelector('i.bi-chevron-right, i.bi-chevron-down');
            
            if (isExpanded) {
                // 折叠：移除子行
                expandedRows.delete(path);
                if (icon) {
                    icon.classList.remove('bi-chevron-down');
                    icon.classList.add('bi-chevron-right');
                }
                removeChildRows(path);
            } else {
                // 展开：添加子行
                expandedRows.add(path);
                if (icon) {
                    icon.classList.remove('bi-chevron-right');
                    icon.classList.add('bi-chevron-down');
                }
                insertChildRows(path, currentRow);
            }
        }
        
        // 插入子行
        function insertChildRows(parentPath, parentRow) {
            if (!treeStructureData) return;
            
            const normalizedPath = parentPath.endsWith('/') ? parentPath : parentPath + '/';
            const children = [];
            
            // 查找直接子目录
            Object.keys(treeStructureData).forEach(path => {
                if (path !== parentPath && path.startsWith(normalizedPath)) {
                    const relativePath = path.substring(normalizedPath.length);
                    if (relativePath.split('/').filter(p => p).length === 1) {
                        children.push(treeStructureData[path]);
                    }
                }
            });
            
            // 按大小降序排序
            children.sort((a, b) => b.size_bytes - a.size_bytes);
            
            // 计算缩进级别
            const parentLevel = parseInt(parentRow.getAttribute('data-level') || 0);
            const childLevel = parentLevel + 1;
            const indent = childLevel * 20;
            
            // 插入子行
            let insertAfter = parentRow;
            children.forEach(child => {
                const childRow = document.createElement('tr');
                childRow.setAttribute('data-path', child.path);
                childRow.setAttribute('data-level', childLevel.toString());
                childRow.setAttribute('data-parent', parentPath);
                childRow.style.backgroundColor = childLevel % 2 === 0 ? '#f8f9fa' : '#ffffff';
                
                const lastModified = child.last_modified ? 
                    new Date(child.last_modified * 1000).toLocaleDateString() : '未知';
                
                const hasChildren = checkHasChildren(child.path, Object.values(treeStructureData));
                const isExpanded = expandedRows.has(child.path);
                
                childRow.innerHTML = `
                    <td style="padding-left: ${indent}px;">
                        ${hasChildren ? `
                            <i class="toggle-icon bi ${isExpanded ? 'bi-chevron-down' : 'bi-chevron-right'} text-primary me-1" 
                               style="cursor: pointer;"></i>
                        ` : '<span style="display: inline-block; width: 20px;"></span>'}
                        <strong>${child.size_human}</strong>
                    </td>
                    <td>${child.file_count}</td>
                    <td>${child.dir_count}</td>
                    <td>${lastModified}</td>
                    <td>
                        <code style="font-size: 0.9em; cursor: pointer; color: #0066cc;" 
                              class="drill-down-path"
                              title="点击下钻查看此目录">${child.path}</code>
                    </td>
                    <td>
                        <button class="btn btn-sm btn-outline-danger" 
                                onclick="confirmDelete('${child.path}', '${child.size_human}', ${child.file_count})"
                                ${child.error ? 'disabled' : ''}>
                            <i class="bi bi-trash"></i>
                        </button>
                    </td>
                `;
                
                insertAfter.after(childRow);
                insertAfter = childRow;
                
                // 为路径添加点击事件处理器
                const pathCode = childRow.querySelector('.drill-down-path');
                if (pathCode) {
                    pathCode.addEventListener('click', function(e) {
                        e.stopPropagation();
                        drillDownToPath(child.path);
                    });
                    // 添加 Tooltip：鼠标悬停显示完整路径
                    pathCode.title = child.path;
                    pathCode.style.cursor = 'pointer';
                }
                
                // 为展开图标添加点击事件处理器
                const toggleIcon = childRow.querySelector('.toggle-icon');
                if (toggleIcon) {
                    toggleIcon.addEventListener('click', function(e) {
                        e.stopPropagation();
                        toggleTableRow(child.path);
                    });
                }
                
                // 如果该子节点已经是展开状态，递归插入其子节点
                if (isExpanded) {
                    insertChildRows(child.path, childRow);
                }
            });
        }
        
        // 移除子行
        function removeChildRows(parentPath) {
            const tbody = document.querySelector('#resultsTable tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            
            rows.forEach(row => {
                const rowParent = row.getAttribute('data-parent');
                const rowPath = row.getAttribute('data-path');
                
                // 直接子节点
                if (rowParent === parentPath) {
                    // 如果子节点也是展开状态，先折叠它
                    if (expandedRows.has(rowPath)) {
                        removeChildRows(rowPath);
                    }
                    row.remove();
                }
                // 间接子节点（递归检查）
                else if (rowPath && rowPath.startsWith(parentPath + '/')) {
                    row.remove();
                }
            });
        }

        // 加载并显示树形结构
        function loadTreeStructure(data) {
            if (!currentAnalysisId) return;
            
            fetch(`/api/tree-structure/${currentAnalysisId}`)
            .then(response => response.json())
            .then(treeData => {
                if (treeData.success && treeData.tree) {
                    // 显示分析参数
                    const depth = data.depth || parseInt(document.getElementById('depthInput').value) || 3;
                    const limit = data.limit || 50;
                    currentTreeDepth = depth; // 更新当前分析深度
                    document.getElementById('treeDepthInfo').textContent = 
                        `分析深度: ${depth}层, 显示限制: ${limit}个目录`;
                    
                    // 显示重新分析按钮
                    document.getElementById('reanalyzeBtn').style.display = 'inline-block';
                    
                    renderTree(treeData.tree);
                } else {
                    document.getElementById('treeContainer').innerHTML = `
                        <div class="alert alert-warning">
                            <i class="bi bi-exclamation-triangle"></i> 无法加载树形结构: ${treeData.message || '未知错误'}
                        </div>
                    `;
                }
            })
            .catch(error => {
                console.error('加载树形结构失败:', error);
                document.getElementById('treeContainer').innerHTML = `
                    <div class="alert alert-danger">
                        <i class="bi bi-exclamation-circle"></i> 加载树形结构失败: ${error.message}
                    </div>
                `;
            });
        }

        // 重新分析功能
        function reanalyzeWithDifferentDepth() {
            // 获取当前设置
            const path = document.getElementById('pathInput').value;
            const currentDepth = parseInt(document.getElementById('depthInput').value);
            const limit = parseInt(document.getElementById('limitInput').value);
            const excludePaths = document.getElementById('excludePathsInput').value;
            const excludeExtensions = document.getElementById('excludeExtensionsInput').value;
            
            // 提示用户输入新的分析深度
            const newDepth = prompt(`当前分析深度: ${currentDepth}层\n请输入新的分析深度 (1-10):`, currentDepth);
            
            if (newDepth !== null) {
                const depthValue = parseInt(newDepth);
                if (!isNaN(depthValue) && depthValue >= 1 && depthValue <= 10) {
                    // 更新深度输入框
                    document.getElementById('depthInput').value = depthValue;
                    
                    // 重新开始分析
                    startAnalysis();
                } else {
                    alert('请输入有效的深度值 (1-10)');
                }
            }
        }

        // 渲染树形结构
        let treeNodeStates = new Map(); // 存储树节点展开/折叠状态
        let currentTreeDepth = 3; // 当前分析深度
        
        function renderTree(tree) {
            const container = document.getElementById('treeContainer');
            container.innerHTML = '';
            
            // 显示树控制按钮
            document.getElementById('treeControlButtons').style.display = 'block';
            
            // 创建树容器
            const treeElement = document.createElement('div');
            treeElement.className = 'tree';
            treeElement.style.cssText = `
                font-family: monospace;
                font-size: 14px;
                line-height: 1.5;
            `;
            
            // 递归渲染节点
            function renderNode(node, depth = 0, path = '') {
                const nodeElement = document.createElement('div');
                const nodePath = path + '/' + node.name;
                const nodeId = 'tree_' + safePathEncode(nodePath);
                
                nodeElement.style.cssText = `
                    margin-left: ${depth * 20}px;
                    padding: 4px 0;
                `;
                
                // 节点内容
                const content = document.createElement('div');
                content.style.cssText = `
                    display: flex;
                    align-items: center;
                    cursor: pointer;
                    padding: 2px 4px;
                    border-radius: 4px;
                `;
                content.onmouseover = () => content.style.backgroundColor = '#f0f0f0';
                content.onmouseout = () => content.style.backgroundColor = 'transparent';
                
                // 检查是否有子节点
                const hasChildren = node.children && node.children.length > 0;
                
                // 展开/折叠图标
                if (hasChildren) {
                    const toggleIcon = document.createElement('i');
                    // 默认展开至分析深度
                    const shouldExpand = depth < currentTreeDepth;
                    toggleIcon.className = `bi ${shouldExpand ? 'bi-chevron-down' : 'bi-chevron-right'} text-primary me-1`;
                    toggleIcon.style.cursor = 'pointer';
                    toggleIcon.onclick = (e) => {
                        e.stopPropagation();
                        toggleTreeNodeExpand(nodeId);
                    };
                    content.appendChild(toggleIcon);
                    
                    // 记录初始状态
                    treeNodeStates.set(nodeId, shouldExpand);
                } else {
                    const spacer = document.createElement('span');
                    spacer.style.width = '20px';
                    spacer.style.display = 'inline-block';
                    content.appendChild(spacer);
                }
                
                // 文件夹图标
                const icon = document.createElement('i');
                icon.className = 'bi bi-folder-fill me-2 text-warning';
                
                // 名称
                const name = document.createElement('span');
                name.textContent = node.name;
                name.className = 'me-2';
                name.style.cursor = 'pointer';
                name.style.color = '#0066cc';
                name.title = '点击下钻查看此目录';
                name.onclick = (e) => {
                    e.stopPropagation();
                    drillDownToPath(node.path);
                };
                
                // 大小信息
                const size = document.createElement('span');
                size.textContent = `(${node.size_human})`;
                size.className = 'text-muted';
                
                content.appendChild(icon);
                content.appendChild(name);
                content.appendChild(size);
                
                // 添加点击事件，支持下钻
                content.onclick = (e) => {
                    // 如果是切换图标点击，则不触发下钻
                    if (e.target.classList.contains('bi-chevron-right') || e.target.classList.contains('bi-chevron-down')) {
                        return;
                    }
                    
                    // 实现下钻功能：分析当前节点路径
                    drillDownToPath(node.path);
                };
                
                nodeElement.appendChild(content);
                
                // 子节点容器
                if (hasChildren) {
                    const childrenContainer = document.createElement('div');
                    childrenContainer.id = nodeId;
                    // 默认展开至分析深度
                    const shouldExpand = depth < currentTreeDepth;
                    childrenContainer.style.display = shouldExpand ? 'block' : 'none';
                    
                    // 按大小降序排序
                    const sortedChildren = [...node.children].sort((a, b) => b.size_bytes - a.size_bytes);
                    sortedChildren.forEach(child => {
                        const childElement = renderNode(child, depth + 1, nodePath);
                        childrenContainer.appendChild(childElement);
                    });
                    
                    nodeElement.appendChild(childrenContainer);
                }
                
                return nodeElement;
            }
            
            // 渲染根节点
            const treeRoot = renderNode(tree);
            treeElement.appendChild(treeRoot);
            
            container.appendChild(treeElement);
        }
        
        // 切换树节点展开/折叠
        function toggleTreeNodeExpand(nodeId) {
            const node = document.getElementById(nodeId);
            if (!node) return;
            
            const isExpanded = node.style.display === 'block';
            node.style.display = isExpanded ? 'none' : 'block';
            
            // 更新图标
            const parent = node.previousElementSibling;
            if (parent) {
                const icon = parent.querySelector('i.bi-chevron-right, i.bi-chevron-down');
                if (icon) {
                    if (isExpanded) {
                        icon.classList.remove('bi-chevron-down');
                        icon.classList.add('bi-chevron-right');
                    } else {
                        icon.classList.remove('bi-chevron-right');
                        icon.classList.add('bi-chevron-down');
                    }
                }
            }
            
            // 保存状态
            treeNodeStates.set(nodeId, !isExpanded);
        }
        
        // 展开所有树节点
        function expandAllTreeNodes() {
            const treeContainer = document.getElementById('treeContainer');
            if (!treeContainer) return;
            
            // 查找所有有ID的div（子节点容器）
            const nodes = treeContainer.querySelectorAll('[id^="tree_"]');
            nodes.forEach(node => {
                node.style.display = 'block';
                
                // 更新图标
                const parent = node.previousElementSibling;
                if (parent) {
                    const icon = parent.querySelector('i.bi-chevron-right, i.bi-chevron-down');
                    if (icon) {
                        icon.classList.remove('bi-chevron-right');
                        icon.classList.add('bi-chevron-down');
                    }
                }
                
                // 保存状态
                treeNodeStates.set(node.id, true);
            });
        }
        
        // 折叠所有树节点
        function collapseAllTreeNodes() {
            const treeContainer = document.getElementById('treeContainer');
            if (!treeContainer) return;
            
            // 查找所有有ID的div（子节点容器）
            const nodes = treeContainer.querySelectorAll('[id^="tree_"]');
            nodes.forEach(node => {
                node.style.display = 'none';
                
                // 更新图标
                const parent = node.previousElementSibling;
                if (parent) {
                    const icon = parent.querySelector('i.bi-chevron-right, i.bi-chevron-down');
                    if (icon) {
                        icon.classList.remove('bi-chevron-down');
                        icon.classList.add('bi-chevron-right');
                    }
                }
                
                // 保存状态
                treeNodeStates.set(node.id, false);
            });
        }

        // 标签页切换事件
        // 在主DOMContentLoaded事件中已经添加了标签页切换监听器
        // 这里只需要添加shown.bs.tab事件监听器
        document.getElementById('tree-tab').addEventListener('shown.bs.tab', function (e) {
            // 如果已经有分析结果，加载树形结构
            if (currentAnalysisId) {
                // 检查是否已经有树形结构数据
                const container = document.getElementById('treeContainer');
                if (container.innerHTML.includes('点击"开始分析"后切换到此标签页')) {
                    // 如果还没有加载过，尝试加载
                    const tableRows = document.querySelectorAll('#resultsTable tbody tr');
                    if (tableRows.length > 0 && !tableRows[0].querySelector('.text-muted')) {
                        // 表格中有数据，加载树形结构
                        loadTreeStructure({});
                    }
                }
            }
        });

        // 生成随机验证码
        function generateCaptcha() {
            const num1 = Math.floor(Math.random() * 20) + 1;
            const num2 = Math.floor(Math.random() * 20) + 1;
            const isAdd = Math.random() > 0.5;
            
            if (isAdd) {
                captchaAnswer = num1 + num2;
                document.getElementById('captchaQuestion').innerHTML = `<strong>${num1} + ${num2} = ?</strong>`;
            } else {
                // 确保减法结果为正数
                if (num1 >= num2) {
                    captchaAnswer = num1 - num2;
                    document.getElementById('captchaQuestion').innerHTML = `<strong>${num1} - ${num2} = ?</strong>`;
                } else {
                    captchaAnswer = num2 - num1;
                    document.getElementById('captchaQuestion').innerHTML = `<strong>${num2} - ${num1} = ?</strong>`;
                }
            }
        }

        // 确认删除
        function confirmDelete(path, size, fileCount) {
            currentDeletePath = path;
            document.getElementById('deletePath').textContent = path;
            document.getElementById('deleteSize').textContent = size;
            document.getElementById('deleteFiles').textContent = fileCount;
            
            // 重置输入框和验证状态
            document.getElementById('deletePathInput').value = '';
            document.getElementById('captchaInput').value = '';
            document.getElementById('captchaSection').style.display = 'none';
            document.getElementById('confirmDeleteBtn').disabled = true;
            
            // 重置验证状态显示
            document.getElementById('pathMatchIcon').innerHTML = '';
            document.getElementById('pathMatchText').textContent = '请输入完整路径进行验证';
            document.getElementById('pathMatchText').style.color = '#6c757d';
            
            // 生成验证码
            generateCaptcha();
            
            // 绑定路径输入框事件
            const pathInput = document.getElementById('deletePathInput');
            
            // 禁止粘贴
            pathInput.addEventListener('paste', function(e) {
                e.preventDefault();
                document.getElementById('pathMatchIcon').innerHTML = '<i class="bi bi-x-circle text-danger"></i>';
                document.getElementById('pathMatchText').textContent = '禁止粘贴，请手动输入';
                document.getElementById('pathMatchText').style.color = '#dc3545';
                setTimeout(() => {
                    document.getElementById('pathMatchIcon').innerHTML = '';
                    document.getElementById('pathMatchText').textContent = '请输入完整路径进行验证';
                    document.getElementById('pathMatchText').style.color = '#6c757d';
                }, 2000);
            });
            
            // 实时验证路径输入
            pathInput.addEventListener('input', function() {
                const inputPath = this.value.trim();
                
                if (inputPath === '') {
                    document.getElementById('pathMatchIcon').innerHTML = '';
                    document.getElementById('pathMatchText').textContent = '请输入完整路径进行验证';
                    document.getElementById('pathMatchText').style.color = '#6c757d';
                    document.getElementById('captchaSection').style.display = 'none';
                    document.getElementById('confirmDeleteBtn').disabled = true;
                } else if (inputPath === currentDeletePath) {
                    // 路径匹配成功
                    document.getElementById('pathMatchIcon').innerHTML = '<i class="bi bi-check-circle text-success"></i>';
                    document.getElementById('pathMatchText').textContent = '路径验证通过';
                    document.getElementById('pathMatchText').style.color = '#198754';
                    document.getElementById('captchaSection').style.display = 'block';
                } else {
                    // 路径不匹配
                    document.getElementById('pathMatchIcon').innerHTML = '<i class="bi bi-x-circle text-danger"></i>';
                    document.getElementById('pathMatchText').textContent = '路径不匹配，请仔细核对';
                    document.getElementById('pathMatchText').style.color = '#dc3545';
                    document.getElementById('captchaSection').style.display = 'none';
                    document.getElementById('confirmDeleteBtn').disabled = true;
                }
            });
            
            // 验证码输入验证
            const captchaInput = document.getElementById('captchaInput');
            captchaInput.addEventListener('input', function() {
                const answer = parseInt(this.value);
                
                if (isNaN(answer)) {
                    document.getElementById('captchaIcon').innerHTML = '';
                    document.getElementById('captchaText').textContent = '请输入正确答案';
                    document.getElementById('captchaText').style.color = '#6c757d';
                    document.getElementById('confirmDeleteBtn').disabled = true;
                } else if (answer === captchaAnswer) {
                    // 验证码正确
                    document.getElementById('captchaIcon').innerHTML = '<i class="bi bi-check-circle text-success"></i>';
                    document.getElementById('captchaText').textContent = '验证通过，可以删除';
                    document.getElementById('captchaText').style.color = '#198754';
                    document.getElementById('confirmDeleteBtn').disabled = false;
                } else {
                    // 验证码错误
                    document.getElementById('captchaIcon').innerHTML = '<i class="bi bi-x-circle text-danger"></i>';
                    document.getElementById('captchaText').textContent = '答案错误，请重新计算';
                    document.getElementById('captchaText').style.color = '#dc3545';
                    document.getElementById('confirmDeleteBtn').disabled = true;
                }
            });
            
            const modal = new bootstrap.Modal(document.getElementById('deleteModal'));
            modal.show();
        }

        // 执行删除
        document.getElementById('confirmDeleteBtn').addEventListener('click', function() {
            if (!currentDeletePath) return;

            const btn = this;
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> 删除中...';

            fetch('/api/delete', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    path: currentDeletePath
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('删除成功！');
                    // 关闭模态框
                    bootstrap.Modal.getInstance(document.getElementById('deleteModal')).hide();
                    // 重新分析
                    startAnalysis();
                } else {
                    alert('删除失败: ' + data.error);
                }
            })
            .catch(error => {
                console.error('删除失败:', error);
                alert('删除失败: ' + error.message);
            })
            .finally(() => {
                btn.disabled = false;
                btn.innerHTML = '<i class="bi bi-trash"></i> 确认删除';
                currentDeletePath = null;
            });
        });

        // 显示分区目录树
        function showPartitionTree(mountPoint) {
            // 显示模态框
            const modal = new bootstrap.Modal(document.getElementById('partitionTreeModal'));
            modal.show();
            
            // 设置标题
            document.getElementById('partitionTreeTitle').textContent = mountPoint;
            
            // 显示加载中状态
            const modalBody = document.getElementById('partitionTreeBody');
            modalBody.innerHTML = `
                <div class="text-center text-muted py-5">
                    <div class="spinner-border" role="status">
                        <span class="visually-hidden">加载中...</span>
                    </div>
                    <p class="mt-3">正在分析目录结构...</p>
                </div>
            `;
            
            // 请求分区树形数据
            fetch('/api/partition-tree', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    mount_point: mountPoint,
                    max_depth: 2,
                    limit: 20
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    renderPartitionTree(data.tree);
                } else {
                    modalBody.innerHTML = `
                        <div class="alert alert-danger">
                            <i class="bi bi-exclamation-triangle"></i> 加载失败: ${data.error}
                        </div>
                    `;
                }
            })
            .catch(error => {
                console.error('获取分区树失败:', error);
                modalBody.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="bi bi-exclamation-triangle"></i> 加载失败: ${error.message}
                    </div>
                `;
            });
        }

        // 渲染分区树形结构
        function renderPartitionTree(tree) {
            const modalBody = document.getElementById('partitionTreeBody');
            
            if (!tree || !tree.children || tree.children.length === 0) {
                modalBody.innerHTML = '<p class="text-muted text-center">此目录下没有子目录</p>';
                return;
            }
            
            // 创建树形容器
            const treeHtml = `
                <div class="tree-view">
                    <div class="tree-node" style="margin-left: 0;">
                        <div class="tree-node-content">
                            <strong><i class="bi bi-hdd"></i> ${tree.name || tree.path}</strong>
                            <span class="text-muted ms-2">${tree.size_human}</span>
                        </div>
                        <div class="tree-node-children">
                            ${renderTreeNode(tree.children)}
                        </div>
                    </div>
                </div>
            `;
            
            modalBody.innerHTML = treeHtml;
        }

        // 递归渲染树节点
        function renderTreeNode(nodes) {
            if (!nodes || nodes.length === 0) {
                return '';
            }
            
            return nodes.map(node => {
                const hasChildren = node.children && node.children.length > 0;
                const nodeId = 'node_' + Math.random().toString(36).substr(2, 9);
                
                const usageBar = node.usage_percent ? `
                    <div class="progress" style="width: 100px; height: 6px; display: inline-block; margin-left: 10px;">
                        <div class="progress-bar bg-info" style="width: ${node.usage_percent}%"></div>
                    </div>
                    <span class="text-muted ms-1" style="font-size: 0.85em;">${node.usage_percent}%</span>
                ` : '';
                
                return `
                    <div class="tree-node" style="margin-left: 20px;">
                        <div class="tree-node-content" style="cursor: pointer; padding: 5px; border-radius: 4px;" onmouseover="this.style.backgroundColor='#f0f0f0'" onmouseout="this.style.backgroundColor='transparent'" onclick="toggleTreeNode('${nodeId}')">
                            <i class="bi ${hasChildren ? 'bi-folder-fill' : 'bi-folder'}" style="color: #ffc107;"></i>
                            <strong style="cursor: pointer; color: #0066cc;" onclick="event.stopPropagation(); drillDownToPath('${node.path.replace(/'/g, "\\'")}')"> ${node.name}</strong>
                            <span class="text-muted ms-2">${node.size_human}</span>
                            <span class="text-muted ms-2" style="font-size: 0.85em;">(文件: ${node.file_count}, 目录: ${node.dir_count})</span>
                            ${usageBar}
                        </div>
                        ${hasChildren ? `
                            <div id="${nodeId}" class="tree-node-children" style="display: none;">
                                ${renderTreeNode(node.children)}
                            </div>
                        ` : ''}
                    </div>
                `;
            }).join('');
        }

        // 切换树节点展开/折叠
        function toggleTreeNode(nodeId) {
            const node = document.getElementById(nodeId);
            if (node) {
                node.style.display = node.style.display === 'none' ? 'block' : 'none';
            }
        }

        // 刷新结果
        function refreshResults() {
            if (document.getElementById('pathInput').value) {
                startAnalysis();
            } else {
                loadSystemInfo();
            }
        }

        // 定期刷新系统信息
        setInterval(loadSystemInfo, 30000); // 每30秒刷新一次
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    """主页"""
    return render_template_string(HTML_TEMPLATE, default_path=os.getcwd())


@app.route('/api/system-info')
def get_system_info():
    """获取系统磁盘信息"""
    try:
        analyzer = DiskAnalyzer()
        disk_info = analyzer.get_system_info()
        return jsonify(disk_info)
    except Exception as e:
        logger.error(f"获取系统信息失败: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/partitions')
def get_partitions():
    """获取去重后的分区信息"""
    try:
        analyzer = DiskAnalyzer()
        partitions = analyzer.get_unique_partitions()
        return jsonify({
            'success': True,
            'partitions': partitions
        })
    except Exception as e:
        logger.error(f"获取分区信息失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/partition-tree', methods=['POST'])
def get_partition_tree():
    """获取分区目录树结构"""
    try:
        data = request.get_json()
        mount_point = data.get('mount_point', '/')
        max_depth = data.get('max_depth', 2)
        limit = data.get('limit', 20)
        
        analyzer = DiskAnalyzer()
        result = analyzer.analyze_partition_tree(mount_point, max_depth, limit)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"获取分区树失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/analysis-progress/<analysis_id>')
def get_analysis_progress(analysis_id):
    """获取分析进度"""
    with analysis_lock:
        if analysis_id in progress_storage:
            return jsonify(progress_storage[analysis_id])
        else:
            return jsonify({"status": "not_found", "message": "分析ID未找到"}), 404


@app.route('/api/tree-structure/<analysis_id>')
def get_tree_structure(analysis_id):
    """获取分析结果的树形结构"""
    with analysis_lock:
        if analysis_id in progress_storage:
            analysis_data = progress_storage[analysis_id]
            if analysis_data.get('status') == 'completed' and 'results' in analysis_data:
                # 构建树形结构
                from disk_analyzer import build_tree_structure
                tree = build_tree_structure(
                    [DiskUsage(**item) for item in analysis_data['results']], 
                    analysis_data.get('path', '.'),
                    analysis_data.get('depth', 3)
                )
                return jsonify({
                    "success": True,
                    "tree": tree
                })
            else:
                return jsonify({
                    "success": False, 
                    "message": "分析尚未完成或无结果"
                }), 400
        else:
            return jsonify({
                "success": False, 
                "message": "分析ID未找到"
            }), 404


@app.route('/api/analyze', methods=['POST'])
def analyze_directory():
    """分析目录"""
    try:
        data = request.get_json()
        path = data.get('path', '')
        depth = data.get('depth', 3)
        limit = data.get('limit', 50)
        exclude_paths = data.get('exclude_paths', [])
        exclude_extensions = data.get('exclude_extensions', [])

        if not path:
            return jsonify({"error": "请提供有效的路径"}), 400

        # 生成唯一的分析ID
        import uuid
        analysis_id = str(uuid.uuid4())

        # 检查是否已有分析在进行
        with analysis_lock:
            if current_analysis.get('running'):
                return jsonify({"error": "已有分析任务在进行中，请稍后再试"}), 429

            current_analysis['running'] = True
            current_analysis['analysis_id'] = analysis_id
            progress_storage[analysis_id] = {
                "status": "started",
                "progress": 0,
                "message": "开始分析..."
            }

        # 定义进度回调函数
        def progress_callback(progress_data):
            with analysis_lock:
                progress_storage[analysis_id] = progress_data

        # 在后台线程中执行分析
        import threading
        def run_analysis():
            try:
                from dataclasses import asdict  # 在内部函数中重新导入
                analyzer = DiskAnalyzer(
                    max_depth=depth, 
                    exclude_paths=exclude_paths, 
                    exclude_extensions=exclude_extensions,
                    progress_callback=progress_callback
                )
                results = analyzer.analyze_directory(path, limit)
                
                # 分析完成后更新状态
                with analysis_lock:
                    progress_storage[analysis_id] = {
                        "status": "completed",
                        "results": [asdict(result) for result in results],
                        "path": path,
                        "depth": depth,
                        "limit": limit,
                        "exclude_paths": exclude_paths,
                        "exclude_extensions": exclude_extensions
                    }
            except Exception as e:
                logger.error(f"分析失败: {e}")
                logger.error(traceback.format_exc())
                with analysis_lock:
                    progress_storage[analysis_id] = {
                        "status": "error",
                        "message": str(e)
                    }
            finally:
                with analysis_lock:
                    current_analysis['running'] = False
                    del current_analysis['analysis_id']

        # 启动分析线程
        thread = threading.Thread(target=run_analysis)
        thread.daemon = True
        thread.start()

        # 立即返回分析ID
        return jsonify({
            "success": True,
            "analysis_id": analysis_id,
            "message": "分析已启动"
        })

    except Exception as e:
        logger.error(f"分析失败: {e}")
        logger.error(traceback.format_exc())
        with analysis_lock:
            if 'analysis_id' in current_analysis:
                del current_analysis['analysis_id']
            current_analysis['running'] = False
        return jsonify({"error": str(e)}), 500


@app.route('/api/list-directories', methods=['POST'])
def list_directories():
    """列出指定目录下的子目录"""
    try:
        data = request.get_json()
        path = data.get('path', '.')
        max_depth = data.get('max_depth', 1)
        
        # 检查路径是否存在
        if not os.path.exists(path):
            return jsonify({"error": "路径不存在"}), 404
        
        if not os.path.isdir(path):
            return jsonify({"error": "路径不是目录"}), 400
        
        # 获取子目录列表
        def get_subdirectories(current_path, current_depth=0):
            if current_depth > max_depth:
                return []
            
            subdirs = []
            try:
                with os.scandir(current_path) as entries:
                    for entry in entries:
                        if entry.is_dir(follow_symlinks=False):
                            subdir_path = os.path.join(current_path, entry.name)
                            subdir_info = {
                                "name": entry.name,
                                "path": subdir_path,
                                "level": current_depth
                            }
                            
                            # 如果还没达到最大深度，继续获取子目录
                            if current_depth < max_depth - 1:
                                subdir_info["children"] = get_subdirectories(subdir_path, current_depth + 1)
                            
                            subdirs.append(subdir_info)
            except (OSError, PermissionError) as e:
                logger.warning(f"无法读取目录 {current_path}: {e}")
            
            return subdirs
        
        directories = get_subdirectories(path, 0)
        
        return jsonify({
            "success": True,
            "path": path,
            "directories": directories
        })
        
    except Exception as e:
        logger.error(f"获取目录列表失败: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


@app.route('/api/delete', methods=['POST'])
def delete_directory():
    """删除目录"""
    try:
        data = request.get_json()
        path = data.get('path', '')

        if not path:
            return jsonify({"error": "请提供有效的路径"}), 400

        # 安全检查
        abs_path = os.path.abspath(path)
        if abs_path == '/' or abs_path.startswith('/proc') or abs_path.startswith('/sys'):
            return jsonify({"error": "不能删除系统关键目录"}), 400

        if not os.path.exists(path):
            return jsonify({"error": "路径不存在"}), 404

        # 再次确认
        if not os.path.isdir(path):
            return jsonify({"error": "只能删除目录"}), 400

        # 执行删除
        logger.warning(f"正在删除目录: {path}")
        shutil.rmtree(path, ignore_errors=False)

        logger.info(f"成功删除目录: {path}")
        return jsonify({
            "success": True,
            "message": f"成功删除: {path}"
        })

    except PermissionError as e:
        return jsonify({"error": f"权限不足: {str(e)}"}), 403
    except OSError as e:
        return jsonify({"error": f"删除失败: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"删除失败: {e}")
        return jsonify({"error": f"未知错误: {str(e)}"}), 500


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='磁盘空间分析Web工具')
    parser.add_argument('--host', default='127.0.0.1', help='服务器地址')
    parser.add_argument('--port', type=int, default=8080, help='服务器端口')
    parser.add_argument('--debug', action='store_true', help='调试模式')
    
    args = parser.parse_args()
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                    磁盘空间分析Web工具                          ║
╠══════════════════════════════════════════════════════════════╣
║  访问地址: http://{args.host}:{args.port}                        ║
║  功能特点:                                                    ║
║    • 基于文件系统元数据的高效分析                              ║
║    • 可配置的分析深度                                          ║
║    • 人性化的Web界面                                           ║
║    • 安全删除功能（带确认）                                    ║
║    • 实时系统磁盘监控                                          ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    app.run(
        host=args.host,
        port=args.port,
        debug=args.debug
    )