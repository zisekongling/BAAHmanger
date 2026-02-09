import sys
import os
import time
import argparse
import subprocess
import threading
import webbrowser
from config_manager import ConfigManager
from check_module import CheckModule
from process_monitor import ProcessMonitor
from email_processor import EmailProcessor
from success_writer import SuccessWriter
from report_generator import ReportGenerator
from system_operations import SystemOperations

class BAAHManager:
    def __init__(self):
        self.config = ConfigManager()
    
    def run_check(self):
        """运行检查任务"""
        print("=" * 50)
        print("运行检查任务...")
        print("=" * 50)
        
        checker = CheckModule()
        checker.check_and_execute()
    
    def run_monitor(self):
        """运行监控任务"""
        print("=" * 50)
        print("运行监控任务...")
        print("=" * 50)
        
        monitor = ProcessMonitor()
        try:
            # 启动监控，当监控到任务完成后会返回True
            task_completed = monitor.monitor()
            
            if task_completed:
                print("检测到任务已完成，开始自动执行后续任务...")
                
                # 步骤1: 运行数据获取任务
                print("\n" + "=" * 50)
                print("步骤1: 运行数据获取任务...")
                print("=" * 50)
                
                email_processor = EmailProcessor()
                found_success_email = email_processor.process_baah_email()
                
                if found_success_email:
                    # 步骤2: 运行报告生成任务
                    print("\n" + "=" * 50)
                    print("步骤2: 运行报告生成任务...")
                    print("=" * 50)
                    
                    self.run_send()
                    
                    # 步骤3: 写入success状态
                    print("\n" + "=" * 50)
                    print("步骤3: 写入success状态...")
                    print("=" * 50)
                    
                    success_writer = SuccessWriter()
                    success_writer.write_success()
                    
                    # 步骤4: 执行完成操作
                    print("\n" + "=" * 50)
                    print("步骤4: 执行完成操作...")
                    print("=" * 50)
                    
                    system_ops = SystemOperations()
                    system_ops.execute_completion_action()
                else:
                    print("未找到BAAH结束邮件，可能为异常闪退，将通过计划任务重新启动BAAH")
                    
                    # 启动BAAH进程（通过计划任务）
                    baah_task_name = self.config.get('program_paths.baah_task_name')
                    if baah_task_name:
                        try:
                            subprocess.run(['schtasks', '/run', '/tn', baah_task_name], 
                                          shell=True, check=True)
                            print(f"已通过计划任务启动BAAH: {baah_task_name}")
                        except subprocess.CalledProcessError as e:
                            print(f"启动BAAH计划任务失败: {e}")
                        except Exception as e:
                            print(f"启动BAAH进程失败: {e}")
            
        except KeyboardInterrupt:
            print("\n监控程序被用户中断")
            monitor.stop()
    
    def run_getdata(self):
        """运行数据获取任务"""
        print("=" * 50)
        print("运行数据获取任务...")
        print("=" * 50)
        
        email_processor = EmailProcessor()
        found_success_email = email_processor.process_baah_email()
        
        if found_success_email:
            # 等待后运行send任务
            wait_time = self.config.get('timing.send_wait_time', 20)
            print(f"等待{wait_time}秒运行报告生成...")
            time.sleep(int(wait_time))
            
            # 生成报告
            print("运行报告生成...")
            report_generator = ReportGenerator()
            html_file = report_generator.process_baah_data()
            
            if html_file:
                # 上传到Gitee
                report_generator.upload_to_gitee(html_file)
            
            # 写入success
            print("写入success状态...")
            success_writer = SuccessWriter()
            success_writer.write_success()
            
            # 执行完成操作
            system_ops = SystemOperations()
            system_ops.execute_completion_action()
        else:
            print("未找到BAAH结束邮件，将通过计划任务启动BAAH进程")
            
            # 启动BAAH进程（通过计划任务）
            baah_task_name = self.config.get('program_paths.baah_task_name')
            if baah_task_name:
                try:
                    subprocess.run(['schtasks', '/run', '/tn', baah_task_name], 
                                  shell=True, check=True)
                    print(f"已通过计划任务启动BAAH: {baah_task_name}")
                except Exception as e:
                    print(f"启动BAAH计划任务失败: {e}")
    
    def run_send(self):
        """运行报告生成任务"""
        print("=" * 50)
        print("运行报告生成任务...")
        print("=" * 50)
        
        report_generator = ReportGenerator()
        html_file = report_generator.process_baah_data()
        
        if html_file:
            report_generator.upload_to_gitee(html_file)
    
    def run_writesuccess(self):
        """运行写入success任务"""
        print("=" * 50)
        print("运行写入success任务...")
        print("=" * 50)
        
        success_writer = SuccessWriter()
        success_writer.write_success()
    
    def show_help(self):
        """显示帮助信息"""
        print("=" * 50)
        print("BAAH任务管理程序")
        print("=" * 50)
        print("用法: baah_manager.exe [参数]")
        print()
        print("参数:")
        print("  -check       运行检查任务（检查今天是否已做BAAH）")
        print("  -monitor     运行监控任务（监控BAAH和MUMU进程，完成后自动执行后续任务）")
        print("  -getdata     运行数据获取任务（获取邮件数据并处理）")
        print("  -send        运行报告生成任务（生成HTML报告并上传）")
        print("  -writesuccess 写入success状态")
        print("  -preview     预览时间段操作配置")
        print("  -help        显示此帮助信息")
        print()
        print("注意: -monitor 参数会在监控到任务完成后自动执行 -getdata 和 -send 任务")
        print()
        print("示例:")
        print("  baah_manager.exe -check")
        print("  baah_manager.exe -monitor")
        print("  baah_manager.exe -getdata")
        print("  baah_manager.exe -send")
        print("  baah_manager.exe -writesuccess")
        print("  baah_manager.exe -preview")
        print("=" * 50)

def start_webui():
    """启动WebUI配置编辑器"""
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import json
    import urllib.parse
    import threading
    
    # 配置字段中文字典
    CONFIG_CHINESE_LABELS = {
        # 文件路径设置
        'file_paths': {
            'success_file': '成功状态文件',
            'log_file': '日志文件',
            'data_file': '数据文件',
            'report_file': '报告文件',
            'config_file': '配置文件'
        },
        # 程序路径设置
        'program_paths': {
            'mumu_path': 'Mumu模拟器路径',
            'baah_path': 'BAAH程序路径',
            'mumu_task_name': '模拟器计划任务名称',
            'baah_task_name': 'BAAH计划任务名称'
        },
        # 邮箱设置
        'email': {
            'imap_server': '邮箱服务器',
            'email_account': '邮箱用户名',
            'authorization_code': '邮箱授权码',
            'folder': '邮箱文件夹',
            'subject_keyword': '邮件主题关键词',
            'sender': '发件人'
        },
        # 进程名称设置
        'process_names': {
            'mumu_process': 'Mumu进程名',
            'baah_process': 'BAAH进程名'
        },
        # 时间设置
        'timing': {
            'check_interval': '检查间隔(秒)',
            'crash_timeout': '转换监控模式阈值(秒)',
            'send_wait_time': '发送等待时间(秒)',
            'logout_wait_time': '完成后操作等待时间(秒)'
        },
        # Gitee设置
        'gitee': {
            'repo': 'Gitee仓库',
            'token': 'Gitee Token',
            'branch': '分支',
            'owner': '仓库拥有者',
            'file_path': '文件路径'
        },
        # 完成操作设置
        'completion': {
            'global_action': '全局默认操作',
            'scheduled_actions': '时间段操作'
        }
    }
    
    class ConfigHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            config = ConfigManager().get_all_config()
            
            if self.path == '/':
                # 返回配置编辑页面
                html = """
                <!DOCTYPE html>
                <html>
                <head>
                    <title>BAAH配置编辑器</title>
                    <meta charset="utf-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <style>
                        /* 基础样式 */
                        :root {
                            --primary-color: #4CAF50;
                            --primary-dark: #45a049;
                            --secondary-color: #2196F3;
                            --secondary-dark: #1976D2;
                            --danger-color: #f44336;
                            --danger-dark: #d32f2f;
                            --warning-color: #ff9800;
                            --warning-dark: #f57c00;
                            --light-bg: #f8f9fa;
                            --dark-bg: #343a40;
                            --border-color: #dee2e6;
                            --text-color: #333;
                            --text-light: #6c757d;
                            --shadow: 0 4px 12px rgba(0,0,0,0.1);
                            --transition: all 0.3s ease;
                        }
                        
                        * {
                            box-sizing: border-box;
                            margin: 0;
                            padding: 0;
                        }
                        
                        body {
                            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                            color: var(--text-color);
                            line-height: 1.6;
                            min-height: 100vh;
                            padding: 20px;
                        }
                        
                        .container {
                            max-width: 1200px;
                            margin: 0 auto;
                            background: white;
                            border-radius: 12px;
                            box-shadow: var(--shadow);
                            overflow: hidden;
                        }
                        
                        /* 头部样式 */
                        .header {
                            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
                            color: white;
                            padding: 30px;
                            text-align: center;
                        }
                        
                        .header h1 {
                            font-size: 2.5rem;
                            margin-bottom: 10px;
                            font-weight: 600;
                        }
                        
                        .header p {
                            font-size: 1.1rem;
                            opacity: 0.9;
                        }
                        
                        /* 命令按钮区域 */
                        .command-section {
                            background: var(--light-bg);
                            padding: 25px;
                            border-bottom: 1px solid var(--border-color);
                        }
                        
                        .section-title {
                            font-size: 1.3rem;
                            color: var(--text-color);
                            margin-bottom: 20px;
                            display: flex;
                            align-items: center;
                            gap: 10px;
                        }
                        
                        .section-title i {
                            font-size: 1.5rem;
                        }
                        
                        .command-buttons {
                            display: grid;
                            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
                            gap: 15px;
                            margin-bottom: 20px;
                        }
                        
                        .command-btn {
                            padding: 15px;
                            border: none;
                            border-radius: 8px;
                            font-size: 16px;
                            font-weight: 500;
                            cursor: pointer;
                            transition: var(--transition);
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            gap: 10px;
                            min-height: 60px;
                        }
                        
                        .command-btn i {
                            font-size: 1.2rem;
                        }
                        
                        .command-btn.check {
                            background-color: var(--primary-color);
                            color: white;
                        }
                        
                        .command-btn.monitor {
                            background-color: var(--secondary-color);
                            color: white;
                        }
                        
                        .command-btn.getdata {
                            background-color: #9C27B0;
                            color: white;
                        }
                        
                        .command-btn.send {
                            background-color: var(--warning-color);
                            color: white;
                        }
                        
                        .command-btn.writesuccess {
                            background-color: #009688;
                            color: white;
                        }
                        
                        .command-btn:hover {
                            transform: translateY(-3px);
                            box-shadow: 0 6px 15px rgba(0,0,0,0.2);
                        }
                        
                        .command-btn:active {
                            transform: translateY(-1px);
                        }
                        
                        .command-btn.loading {
                            position: relative;
                            color: transparent !important;
                        }
                        
                        .command-btn.loading::after {
                            content: '';
                            position: absolute;
                            width: 20px;
                            height: 20px;
                            border: 3px solid rgba(255,255,255,0.3);
                            border-top-color: white;
                            border-radius: 50%;
                            animation: spin 1s linear infinite;
                        }
                        
                        @keyframes spin {
                            to { transform: rotate(360deg); }
                        }
                        
                        /* 状态提示 */
                        .status-container {
                            padding: 0 25px;
                        }
                        
                        .status {
                            padding: 15px;
                            border-radius: 8px;
                            margin: 15px 0;
                            display: none;
                            animation: fadeIn 0.3s ease;
                            align-items: center;
                            gap: 12px;
                        }
                        
                        .status i {
                            font-size: 1.5rem;
                        }
                        
                        .status.success {
                            background-color: #d4edda;
                            color: #155724;
                            border: 1px solid #c3e6cb;
                        }
                        
                        .status.error {
                            background-color: #f8d7da;
                            color: #721c24;
                            border: 1px solid #f5c6cb;
                        }
                        
                        .status.info {
                            background-color: #d1ecf1;
                            color: #0c5460;
                            border: 1px solid #bee5eb;
                        }
                        
                        @keyframes fadeIn {
                            from { opacity: 0; transform: translateY(-10px); }
                            to { opacity: 1; transform: translateY(0); }
                        }
                        
                        /* 配置表单区域 */
                        .config-section {
                            padding: 30px;
                        }
                        
                        .config-tabs {
                            display: flex;
                            flex-wrap: wrap;
                            gap: 10px;
                            margin-bottom: 30px;
                            border-bottom: 2px solid var(--border-color);
                            padding-bottom: 15px;
                        }
                        
                        .tab-btn {
                            padding: 12px 24px;
                            background: none;
                            border: none;
                            border-radius: 6px;
                            font-size: 16px;
                            font-weight: 500;
                            color: var(--text-light);
                            cursor: pointer;
                            transition: var(--transition);
                        }
                        
                        .tab-btn:hover {
                            background: var(--light-bg);
                            color: var(--text-color);
                        }
                        
                        .tab-btn.active {
                            background: var(--primary-color);
                            color: white;
                        }
                        
                        .tab-content {
                            display: none;
                            animation: fadeIn 0.5s ease;
                        }
                        
                        .tab-content.active {
                            display: block;
                        }
                        
                        .config-group {
                            background: var(--light-bg);
                            border-radius: 10px;
                            padding: 25px;
                            margin-bottom: 25px;
                            border: 1px solid var(--border-color);
                        }
                        
                        .config-group h3 {
                            color: var(--primary-color);
                            margin-bottom: 20px;
                            padding-bottom: 10px;
                            border-bottom: 2px solid var(--border-color);
                            font-size: 1.4rem;
                        }
                        
                        .field-row {
                            display: grid;
                            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                            gap: 20px;
                            margin-bottom: 20px;
                        }
                        
                        .field-group {
                            display: flex;
                            flex-direction: column;
                        }
                        
                        .field-group label {
                            font-weight: 600;
                            margin-bottom: 8px;
                            color: var(--text-color);
                            display: flex;
                            align-items: center;
                            gap: 8px;
                        }
                        
                        .field-group label .field-tip {
                            color: var(--text-light);
                            font-size: 0.9rem;
                            font-weight: normal;
                        }
                        
                        .field-group input,
                        .field-group select {
                            padding: 12px 15px;
                            border: 2px solid var(--border-color);
                            border-radius: 6px;
                            font-size: 16px;
                            transition: var(--transition);
                        }
                        
                        .field-group input:focus,
                        .field-group select:focus {
                            outline: none;
                            border-color: var(--primary-color);
                            box-shadow: 0 0 0 3px rgba(76, 175, 80, 0.1);
                        }
                        
                        .field-group input[readonly] {
                            background-color: #f8f9fa;
                            cursor: not-allowed;
                        }
                        
                        /* 操作按钮区域 */
                        .action-buttons {
                            display: flex;
                            gap: 15px;
                            justify-content: center;
                            padding: 30px;
                            background: var(--light-bg);
                            border-top: 1px solid var(--border-color);
                        }
                        
                        .action-btn {
                            padding: 15px 30px;
                            border: none;
                            border-radius: 8px;
                            font-size: 18px;
                            font-weight: 600;
                            cursor: pointer;
                            transition: var(--transition);
                            display: flex;
                            align-items: center;
                            gap: 10px;
                            min-width: 180px;
                            justify-content: center;
                        }
                        
                        .action-btn.save {
                            background: var(--primary-color);
                            color: white;
                        }
                        
                        .action-btn.reset {
                            background: var(--text-light);
                            color: white;
                        }
                        
                        .action-btn:hover {
                            transform: translateY(-3px);
                            box-shadow: 0 6px 15px rgba(0,0,0,0.2);
                        }
                        
                        .action-btn:active {
                            transform: translateY(-1px);
                        }
                        
                        /* 响应式设计 */
                        @media (max-width: 768px) {
                            .container {
                                border-radius: 0;
                            }
                            
                            .command-buttons {
                                grid-template-columns: 1fr;
                            }
                            
                            .field-row {
                                grid-template-columns: 1fr;
                            }
                            
                            .action-buttons {
                                flex-direction: column;
                            }
                            
                            .action-btn {
                                width: 100%;
                            }
                        }
                    </style>
                    <!-- Font Awesome 图标 -->
                    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1><i class="fas fa-robot"></i> BAAH任务管理程序</h1>
                            <p>自动化任务监控与报告生成系统</p>
                        </div>
                        
                        <div class="command-section">
                            <h2 class="section-title"><i class="fas fa-play-circle"></i> 快速执行命令</h2>
                            <div class="command-buttons">
                                <button class="command-btn check" onclick="runCommand('check')">
                                    <i class="fas fa-search"></i> 检查任务
                                </button>
                                <button class="command-btn monitor" onclick="runCommand('monitor')">
                                    <i class="fas fa-desktop"></i> 监控任务
                                </button>
                                <button class="command-btn getdata" onclick="runCommand('getdata')">
                                    <i class="fas fa-envelope"></i> 获取数据
                                </button>
                                <button class="command-btn send" onclick="runCommand('send')">
                                    <i class="fas fa-file-export"></i> 生成报告
                                </button>
                                <button class="command-btn writesuccess" onclick="runCommand('writesuccess')">
                                    <i class="fas fa-check-circle"></i> 写入成功
                                </button>
                            </div>
                        </div>
                        
                        <div class="status-container">
                            <div id="status" class="status"></div>
                        </div>
                        
                        <div class="config-section">
                            <h2 class="section-title"><i class="fas fa-cog"></i> 系统配置</h2>
                            
                            <div class="config-tabs" id="configTabs">
                                <!-- 选项卡将通过JavaScript动态生成 -->
                            </div>
                            
                            <form id="configForm">
                                <div id="tabContents">
                                    <!-- 选项卡内容将通过JavaScript动态生成 -->
                                </div>
                                
                                <div class="action-buttons">
                                    <button type="submit" class="action-btn save">
                                        <i class="fas fa-save"></i> 保存配置
                                    </button>
                                    <button type="button" class="action-btn reset" onclick="resetForm()">
                                        <i class="fas fa-redo"></i> 重置表单
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                    
                    <script>
                        // 配置数据
                        let configData = """ + json.dumps(config, ensure_ascii=False) + """;
                        const chineseLabels = """ + json.dumps(CONFIG_CHINESE_LABELS, ensure_ascii=False) + """;
                        
                        // 初始化页面
                        document.addEventListener('DOMContentLoaded', function() {
                            initTabs();
                            renderConfigForm();
                            
                            // 获取当前配置
                            fetch('/config')
                                .then(response => response.json())
                                .then(data => {
                                    configData = data;
                                    renderConfigForm();
                                })
                                .catch(error => {
                                    showStatus('获取配置失败: ' + error, false);
                                });
                        });
                        
                        // 初始化选项卡
                        function initTabs() {
                            const tabsContainer = document.getElementById('configTabs');
                            const tabsContent = document.getElementById('tabContents');
                            
                            const tabNames = {
                                'file_paths': '文件路径',
                                'program_paths': '程序路径',
                                'email': '邮箱设置',
                                'process_names': '进程名称',
                                'timing': '时间设置',
                                'gitee': 'Gitee设置',
                                'completion': '完成操作'
                            };
                            
                            let firstTab = true;
                            for (const [tabId, tabName] of Object.entries(tabNames)) {
                                // 创建选项卡按钮
                                const tabBtn = document.createElement('button');
                                tabBtn.className = `tab-btn ${firstTab ? 'active' : ''}`;
                                tabBtn.textContent = tabName;
                                tabBtn.dataset.tab = tabId;
                                tabBtn.onclick = function() {
                                    switchTab(tabId);
                                };
                                tabsContainer.appendChild(tabBtn);
                                
                                // 创建选项卡内容
                                const tabContent = document.createElement('div');
                                tabContent.className = `tab-content ${firstTab ? 'active' : ''}`;
                                tabContent.id = `tab-${tabId}`;
                                tabsContent.appendChild(tabContent);
                                
                                firstTab = false;
                            }
                        }
                        
                        // 切换选项卡
                        function switchTab(tabId) {
                            // 移除所有激活状态
                            document.querySelectorAll('.tab-btn').forEach(btn => {
                                btn.classList.remove('active');
                            });
                            document.querySelectorAll('.tab-content').forEach(content => {
                                content.classList.remove('active');
                            });
                            
                            // 激活当前选项卡
                            document.querySelector(`.tab-btn[data-tab="${tabId}"]`).classList.add('active');
                            document.getElementById(`tab-${tabId}`).classList.add('active');
                        }
                        
                        // 渲染配置表单
                        function renderConfigForm() {
                            // 渲染各个选项卡内容
                            renderTabContent('file_paths', '文件路径设置', '不建议修改');
                            renderTabContent('program_paths', '程序路径设置', '请根据您的系统设置正确路径');
                            renderTabContent('email', '邮箱设置', '用于接收BAAH完成邮件的邮箱配置');
                            renderTabContent('process_names', '进程名称设置', '不建议修改');
                            renderTabContent('timing', '时间设置', '各项任务的时间间隔配置');
                            renderTabContent('gitee', 'Gitee设置', '用于上传报告的Gitee配置');
                            renderCompletionTab();
                        }
                        
                        // 渲染选项卡内容
                        function renderTabContent(tabId, title, description) {
                            const tabContent = document.getElementById(`tab-${tabId}`);
                            const configSection = configData[tabId] || {};
                            const labels = chineseLabels[tabId] || {};
                            
                            let html = `
                                <div class="config-group">
                                    <h3>${title} <span class="field-tip">${description}</span></h3>
                                    <div class="field-row">
                            `;
                            
                            for (const [key, value] of Object.entries(configSection)) {
                                const label = labels[key] || key;
                                const fieldId = `${tabId}.${key}`;
                                const fieldValue = value === null ? '' : String(value);
                                const isReadonly = tabId === 'file_paths' || tabId === 'process_names';
                                
                                html += `
                                    <div class="field-group">
                                        <label for="${fieldId}">
                                            ${label}
                                            ${isReadonly ? '<span class="field-tip">(只读)</span>' : ''}
                                        </label>
                                        <input type="text" 
                                               id="${fieldId}" 
                                               name="${fieldId}" 
                                               value="${escapeHtml(fieldValue)}"
                                               ${isReadonly ? 'readonly' : ''}>
                                    </div>
                                `;
                            }
                            
                            html += `
                                    </div>
                                </div>
                            `;
                            
                            tabContent.innerHTML = html;
                        }
                        
                        // 渲染完成操作选项卡
                        function renderCompletionTab() {
                            const tabContent = document.getElementById('tab-completion');
                            const globalAction = configData.task_completion_action || 'none';
                            const scheduledActions = configData.scheduled_completion_actions || [];
                            
                            const actions = [
                                {value: 'none', label: '不执行任何操作', icon: 'fas fa-times-circle'},
                                {value: 'logout', label: '注销系统', icon: 'fas fa-sign-out-alt'},
                                {value: 'shutdown', label: '关闭计算机', icon: 'fas fa-power-off'},
                                {value: 'restart', label: '重新启动', icon: 'fas fa-redo'}
                            ];
                            
                            let html = `
                                <div class="config-group">
                                    <h3>全局默认操作 <span class="field-tip">当时间段未匹配时执行的操作</span></h3>
                                    <div class="field-row">
                            `;
                            
                            actions.forEach(actionItem => {
                                html += `
                                    <div class="field-group">
                                        <label style="flex-direction: row; align-items: center;">
                                            <input type="radio" 
                                                   name="task_completion_action" 
                                                   value="${actionItem.value}"
                                                   ${globalAction === actionItem.value ? 'checked' : ''}
                                                   style="margin-right: 10px;">
                                            <i class="${actionItem.icon}" style="margin-right: 8px;"></i>
                                            ${actionItem.label}
                                        </label>
                                    </div>
                                `;
                            });
                            
                            html += `
                                    </div>
                                </div>
                                
                                <div class="config-group">
                                    <h3>时间段操作配置 <span class="field-tip">根据时间段执行不同的操作（支持跨午夜）</span></h3>
                                    <div id="scheduledActionsContainer">
                            `;
                            
                            // 渲染时间段配置
                            if (scheduledActions.length === 0) {
                                html += `
                                    <div class="no-schedule" style="text-align: center; padding: 20px; color: #666;">
                                        <i class="fas fa-clock fa-2x" style="margin-bottom: 10px;"></i>
                                        <p>未配置时间段，将使用全局默认操作</p>
                                        <button type="button" onclick="addNewSchedule()" class="action-btn save" style="margin-top: 10px;">
                                            <i class="fas fa-plus"></i> 添加时间段
                                        </button>
                                    </div>
                                `;
                            } else {
                                html += `
                                    <div style="margin-bottom: 15px;">
                                        <button type="button" onclick="addNewSchedule()" class="action-btn save" style="padding: 10px 15px;">
                                            <i class="fas fa-plus"></i> 添加新时间段
                                        </button>
                                    </div>
                                `;
                                
                                scheduledActions.forEach((schedule, index) => {
                                    const name = schedule.name || `时间段${index + 1}`;
                                    const startTime = schedule.start_time || '00:00';
                                    const endTime = schedule.end_time || '23:59';
                                    const action = schedule.action || 'none';
                                    const enabled = schedule.enabled !== false;
                                    
                                    html += `
                                        <div class="schedule-item" data-index="${index}" style="
                                            border: 1px solid #ddd;
                                            border-radius: 8px;
                                            padding: 15px;
                                            margin-bottom: 15px;
                                            background: ${enabled ? '#f8f9fa' : '#f0f0f0'};
                                        ">
                                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                                <h4 style="margin: 0; color: #333;">
                                                    ${enabled ? '✓' : '✗'} ${name}
                                                </h4>
                                                <div>
                                                    <button type="button" onclick="toggleSchedule(${index})" style="
                                                        background: ${enabled ? '#4CAF50' : '#f44336'};
                                                        color: white;
                                                        border: none;
                                                        padding: 5px 10px;
                                                        border-radius: 4px;
                                                        margin-right: 5px;
                                                        cursor: pointer;
                                                    ">
                                                        ${enabled ? '禁用' : '启用'}
                                                    </button>
                                                    <button type="button" onclick="removeSchedule(${index})" style="
                                                        background: #ff9800;
                                                        color: white;
                                                        border: none;
                                                        padding: 5px 10px;
                                                        border-radius: 4px;
                                                        cursor: pointer;
                                                    ">
                                                        删除
                                                    </button>
                                                </div>
                                            </div>
                                            
                                            <div class="field-row" style="grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));">
                                                <div class="field-group">
                                                    <label>名称</label>
                                                    <input type="text" 
                                                           class="schedule-name" 
                                                           value="${escapeHtml(name)}"
                                                           placeholder="例如：工作时间">
                                                </div>
                                                
                                                <div class="field-group">
                                                    <label>开始时间</label>
                                                    <input type="time" 
                                                           class="schedule-start" 
                                                           value="${startTime}"
                                                           step="60">
                                                </div>
                                                
                                                <div class="field-group">
                                                    <label>结束时间</label>
                                                    <input type="time" 
                                                           class="schedule-end" 
                                                           value="${endTime}"
                                                           step="60">
                                                </div>
                                                
                                                <div class="field-group">
                                                    <label>执行操作</label>
                                                    <select class="schedule-action">
                                    `;
                                    
                                    actions.forEach(actionItem => {
                                        html += `
                                            <option value="${actionItem.value}" ${action === actionItem.value ? 'selected' : ''}>
                                                ${actionItem.label}
                                            </option>
                                        `;
                                    });
                                    
                                    html += `
                                                    </select>
                                                </div>
                                            </div>
                                            <div style="margin-top: 10px; font-size: 12px; color: #666;">
                                                提示：如果要配置跨午夜的时间段（如 22:00 到 06:00），结束时间应小于开始时间
                                            </div>
                                        </div>
                                    `;
                                });
                            }
                            
                            html += `
                                    </div>
                                </div>
                            `;
                            
                            tabContent.innerHTML = html;
                        }
                        
                        // 转义HTML特殊字符
                        function escapeHtml(text) {
                            const map = {
                                '&': '&amp;',
                                '<': '&lt;',
                                '>': '&gt;',
                                '"': '&quot;',
                                "'": '&#039;'
                            };
                            return String(text).replace(/[&<>"']/g, function(m) { return map[m]; });
                        }
                        
                        // 显示状态消息
                        function showStatus(message, isSuccess) {
                            const statusDiv = document.getElementById('status');
                            const icon = isSuccess ? '<i class="fas fa-check-circle"></i>' : '<i class="fas fa-exclamation-circle"></i>';
                            const type = isSuccess ? 'success' : 'error';
                            
                            statusDiv.innerHTML = `${icon} ${message}`;
                            statusDiv.className = `status ${type}`;
                            statusDiv.style.display = 'flex';
                            
                            setTimeout(() => {
                                statusDiv.style.display = 'none';
                            }, 5000);
                        }
                        
                        // 运行命令
                        function runCommand(command) {
                            const button = document.querySelector(`.command-btn.${command}`);
                            const originalText = button.innerHTML;
                            
                            // 显示加载状态
                            button.classList.add('loading');
                            button.disabled = true;
                            
                            fetch('/command', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                },
                                body: JSON.stringify({command: command})
                            })
                            .then(response => response.json())
                            .then(data => {
                                // 恢复按钮状态
                                button.classList.remove('loading');
                                button.innerHTML = originalText;
                                button.disabled = false;
                                
                                if (data.success) {
                                    showStatus(`命令执行成功: ${command}`, true);
                                } else {
                                    showStatus(`命令执行失败: ${data.message}`, false);
                                }
                            })
                            .catch(error => {
                                // 恢复按钮状态
                                button.classList.remove('loading');
                                button.innerHTML = originalText;
                                button.disabled = false;
                                
                                showStatus('请求失败: ' + error, false);
                            });
                        }
                        
                        // 添加新时间段
                        function addNewSchedule() {
                            const container = document.getElementById('scheduledActionsContainer');
                            const index = document.querySelectorAll('.schedule-item').length;
                            
                            const newSchedule = `
                                <div class="schedule-item" data-index="${index}" style="
                                    border: 1px solid #ddd;
                                    border-radius: 8px;
                                    padding: 15px;
                                    margin-bottom: 15px;
                                    background: #f8f9fa;
                                ">
                                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                        <h4 style="margin: 0; color: #333;">
                                            ✓ 新时间段
                                        </h4>
                                        <div>
                                            <button type="button" onclick="toggleSchedule(${index})" style="
                                                background: #4CAF50;
                                                color: white;
                                                border: none;
                                                padding: 5px 10px;
                                                border-radius: 4px;
                                                margin-right: 5px;
                                                cursor: pointer;
                                            ">
                                                禁用
                                            </button>
                                            <button type="button" onclick="removeSchedule(${index})" style="
                                                background: #ff9800;
                                                color: white;
                                                border: none;
                                                padding: 5px 10px;
                                                border-radius: 4px;
                                                cursor: pointer;
                                            ">
                                                删除
                                            </button>
                                        </div>
                                    </div>
                                    
                                    <div class="field-row" style="grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));">
                                        <div class="field-group">
                                            <label>名称</label>
                                            <input type="text" 
                                                   class="schedule-name" 
                                                   value="新时间段"
                                                   placeholder="例如：工作时间">
                                        </div>
                                        
                                        <div class="field-group">
                                            <label>开始时间</label>
                                            <input type="time" 
                                                   class="schedule-start" 
                                                   value="09:00"
                                                   step="300">
                                        </div>
                                        
                                        <div class="field-group">
                                            <label>结束时间</label>
                                            <input type="time" 
                                                   class="schedule-end" 
                                                   value="17:00"
                                                   step="300">
                                        </div>
                                        
                                        <div class="field-group">
                                            <label>执行操作</label>
                                            <select class="schedule-action">
                                                <option value="none">不执行任何操作</option>
                                                <option value="logout">注销系统</option>
                                                <option value="shutdown" selected>关闭计算机</option>
                                                <option value="restart">重新启动</option>
                                            </select>
                                        </div>
                                    </div>
                                    <div style="margin-top: 10px; font-size: 12px; color: #666;">
                                        提示：如果要配置跨午夜的时间段（如 22:00 到 06:00），结束时间应小于开始时间
                                    </div>
                                </div>
                            `;
                            
                            if (container.querySelector('.no-schedule')) {
                                container.innerHTML = `
                                    <div style="margin-bottom: 15px;">
                                        <button type="button" onclick="addNewSchedule()" class="action-btn save" style="padding: 10px 15px;">
                                            <i class="fas fa-plus"></i> 添加新时间段
                                        </button>
                                    </div>
                                    ${newSchedule}
                                `;
                            } else {
                                container.insertAdjacentHTML('beforeend', newSchedule);
                            }
                        }
                        
                        // 切换时间段启用/禁用状态
                        function toggleSchedule(index) {
                            const scheduleItem = document.querySelector(`.schedule-item[data-index="${index}"]`);
                            if (!scheduleItem) return;
                            
                            const title = scheduleItem.querySelector('h4');
                            const toggleBtn = scheduleItem.querySelector('button[onclick^="toggleSchedule"]');
                            const isEnabled = !title.textContent.includes('✗');
                            
                            if (isEnabled) {
                                title.innerHTML = title.innerHTML.replace('✓', '✗');
                                scheduleItem.style.background = '#f0f0f0';
                                toggleBtn.textContent = '启用';
                                toggleBtn.style.background = '#f44336';
                            } else {
                                title.innerHTML = title.innerHTML.replace('✗', '✓');
                                scheduleItem.style.background = '#f8f9fa';
                                toggleBtn.textContent = '禁用';
                                toggleBtn.style.background = '#4CAF50';
                            }
                        }
                        
                        // 删除时间段
                        function removeSchedule(index) {
                            const scheduleItem = document.querySelector(`.schedule-item[data-index="${index}"]`);
                            if (!scheduleItem) return;
                            
                            if (confirm('确定要删除这个时间段配置吗？')) {
                                scheduleItem.remove();
                                
                                // 重新索引
                                const items = document.querySelectorAll('.schedule-item');
                                items.forEach((item, newIndex) => {
                                    item.setAttribute('data-index', newIndex);
                                    
                                    const toggleBtn = item.querySelector('button[onclick^="toggleSchedule"]');
                                    const removeBtn = item.querySelector('button[onclick^="removeSchedule"]');
                                    
                                    toggleBtn.setAttribute('onclick', `toggleSchedule(${newIndex})`);
                                    removeBtn.setAttribute('onclick', `removeSchedule(${newIndex})`);
                                });
                                
                                // 如果没有时间段了，显示空状态
                                if (items.length === 0) {
                                    const container = document.getElementById('scheduledActionsContainer');
                                    container.innerHTML = `
                                        <div class="no-schedule" style="text-align: center; padding: 20px; color: #666;">
                                            <i class="fas fa-clock fa-2x" style="margin-bottom: 10px;"></i>
                                            <p>未配置时间段，将使用全局默认操作</p>
                                            <button type="button" onclick="addNewSchedule()" class="action-btn save" style="margin-top: 10px;">
                                                <i class="fas fa-plus"></i> 添加时间段
                                            </button>
                                        </div>
                                    `;
                                }
                            }
                        }
                        
                        // 表单提交
                        document.getElementById('configForm').addEventListener('submit', function(e) {
                            e.preventDefault();
                            
                            const formData = new FormData(e.target);
                            const data = {};
                            
                            // 收集所有表单数据
                            for (let [key, value] of formData.entries()) {
                                // 处理嵌套对象
                                const keys = key.split('.');
                                let current = data;
                                
                                for (let i = 0; i < keys.length - 1; i++) {
                                    if (!current[keys[i]]) {
                                        current[keys[i]] = {};
                                    }
                                    current = current[keys[i]];
                                }
                                
                                current[keys[keys.length - 1]] = value;
                            }
                            
                            // 添加全局默认操作
                            const globalAction = document.querySelector('input[name="task_completion_action"]:checked');
                            if (globalAction) {
                                data.task_completion_action = globalAction.value;
                            }
                            
                            // 收集时间段配置
                            const scheduledActions = [];
                            const scheduleItems = document.querySelectorAll('.schedule-item');
                            
                            scheduleItems.forEach((item, index) => {
                                const nameInput = item.querySelector('.schedule-name');
                                const startInput = item.querySelector('.schedule-start');
                                const endInput = item.querySelector('.schedule-end');
                                const actionSelect = item.querySelector('.schedule-action');
                                const title = item.querySelector('h4');
                                
                                const isEnabled = !title.textContent.includes('✗');
                                
                                scheduledActions.push({
                                    name: nameInput.value || `时间段${index + 1}`,
                                    start_time: startInput.value || '00:00',
                                    end_time: endInput.value || '23:59',
                                    action: actionSelect.value || 'none',
                                    enabled: isEnabled
                                });
                            });
                            
                            data.scheduled_completion_actions = scheduledActions;
                            
                            // 显示保存状态
                            const saveBtn = document.querySelector('.action-btn.save');
                            const originalText = saveBtn.innerHTML;
                            saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 保存中...';
                            saveBtn.disabled = true;
                            
                            fetch('/save', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                },
                                body: JSON.stringify(data)
                            })
                            .then(response => response.json())
                            .then(data => {
                                // 恢复按钮状态
                                saveBtn.innerHTML = originalText;
                                saveBtn.disabled = false;
                                
                                if (data.success) {
                                    showStatus('配置保存成功！', true);
                                    // 重新加载配置
                                    fetch('/config')
                                        .then(response => response.json())
                                        .then(newConfig => {
                                            configData = newConfig;
                                            // 重新渲染表单以反映保存的数据
                                            renderConfigForm();
                                        });
                                } else {
                                    showStatus('保存失败: ' + data.message, false);
                                }
                            })
                            .catch(error => {
                                // 恢复按钮状态
                                saveBtn.innerHTML = originalText;
                                saveBtn.disabled = false;
                                
                                showStatus('请求失败: ' + error, false);
                            });
                        });
                        
                        // 重置表单
                        function resetForm() {
                            if (confirm('确定要重置表单吗？所有更改将丢失。')) {
                                fetch('/config')
                                    .then(response => response.json())
                                    .then(data => {
                                        configData = data;
                                        renderConfigForm();
                                        showStatus('表单已重置为当前配置', true);
                                    })
                                    .catch(error => {
                                        showStatus('重置失败: ' + error, false);
                                    });
                            }
                        }
                    </script>
                </body>
                </html>
                """
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(html.encode('utf-8'))
            elif self.path == '/config':
                # 返回JSON格式的配置
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(config, ensure_ascii=False).encode('utf-8'))
            else:
                self.send_response(404)
                self.end_headers()
        
        def do_POST(self):
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            if self.path == '/save':
                try:
                    data = json.loads(post_data.decode('utf-8'))
                    config_manager = ConfigManager()
                    
                    # 更新配置
                    success = config_manager.update_config(data)
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    
                    response = {
                        'success': success,
                        'message': '配置保存成功' if success else '配置保存失败'
                    }
                    self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
                except Exception as e:
                    self.send_response(500)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    
                    response = {
                        'success': False,
                        'message': str(e)
                    }
                    self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
            
            elif self.path == '/command':
                try:
                    data = json.loads(post_data.decode('utf-8'))
                    command = data.get('command', '')
                    
                    # 在新线程中执行命令以避免阻塞
                    def run_command():
                        try:
                            baah_manager = BAAHManager()
                            if command == 'check':
                                baah_manager.run_check()
                            elif command == 'monitor':
                                baah_manager.run_monitor()
                            elif command == 'getdata':
                                baah_manager.run_getdata()
                            elif command == 'send':
                                baah_manager.run_send()
                            elif command == 'writesuccess':
                                baah_manager.run_writesuccess()
                        except Exception as e:
                            print(f"执行命令 {command} 失败: {e}")
                    
                    # 启动线程执行命令
                    thread = threading.Thread(target=run_command, daemon=True)
                    thread.start()
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    
                    response = {
                        'success': True,
                        'message': f'已开始执行命令: {command}'
                    }
                    self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
                except Exception as e:
                    self.send_response(500)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    
                    response = {
                        'success': False,
                        'message': str(e)
                    }
                    self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
            else:
                self.send_response(404)
                self.end_headers()
        
        def log_message(self, format, *args):
            """静默日志"""
            pass
    
    # 启动Web服务器
    host = 'localhost'
    port = 8080
    
    # 尝试多个端口
    for port in range(8080, 8100):
        try:
            server = HTTPServer((host, port), ConfigHandler)
            print(f"WebUI已启动: http://{host}:{port}")
            print("按Ctrl+C停止WebUI")
            
            # 自动打开浏览器
            try:
                webbrowser.open(f'http://{host}:{port}')
            except:
                pass
            
            server.serve_forever()
            break
        except OSError as e:
            if port == 8099:
                print(f"无法启动WebUI，所有端口都被占用: {e}")
                return

def main():
    # 初始化配置管理器，自动检查配置文件
    ConfigManager()
    
    parser = argparse.ArgumentParser(description='BAAH任务管理程序')
    parser.add_argument('-check', action='store_true', help='运行检查任务')
    parser.add_argument('-monitor', action='store_true', help='运行监控任务')
    parser.add_argument('-getdata', action='store_true', help='运行数据获取任务')
    parser.add_argument('-send', action='store_true', help='运行报告生成任务')
    parser.add_argument('-writesuccess', action='store_true', help='写入success状态')
    parser.add_argument('-preview', action='store_true', help='预览时间段操作配置')
    parser.add_argument('-help', action='store_true', help='显示帮助信息')
    
    # 如果没有参数，自动启动WebUI
    if len(sys.argv) == 1:
        print("=" * 50)
        print("BAAH任务管理程序 - WebUI模式")
        print("=" * 50)
        print("正在启动配置编辑器WebUI...")
        print("您也可以通过命令行参数直接运行特定功能:")
        print("  ba.py -check       运行检查任务")
        print("  ba.py -monitor     运行监控任务")
        print("  ba.py -getdata     运行数据获取")
        print("  ba.py -send        生成报告")
        print("  ba.py -writesuccess 写入成功状态")
        print("  ba.py -preview     预览时间段操作配置")
        print("  ba.py -help        显示帮助信息")
        print("=" * 50)
        
        try:
            start_webui()
        except KeyboardInterrupt:
            print("\nWebUI已停止")
        except Exception as e:
            print(f"启动WebUI失败: {e}")
            print("将显示帮助信息:")
            baah_manager = BAAHManager()
            baah_manager.show_help()
        return
    
    args = parser.parse_args()
    baah_manager = BAAHManager()
    
    if args.check:
        baah_manager.run_check()
    elif args.monitor:
        baah_manager.run_monitor()
    elif args.getdata:
        baah_manager.run_getdata()
    elif args.send:
        baah_manager.run_send()
    elif args.writesuccess:
        baah_manager.run_writesuccess()
    elif args.preview:
        system_ops = SystemOperations()
        system_ops.get_scheduled_actions_preview()
    elif args.help:
        baah_manager.show_help()
    else:
        baah_manager.show_help()

if __name__ == "__main__":
    main()
