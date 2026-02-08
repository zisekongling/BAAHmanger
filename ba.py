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
    
    def run_monitor(self, only=False):
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
                
                if not only:
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
                else:
                    print("--only模式: 仅执行监控任务，跳过后续操作")
            
        except KeyboardInterrupt:
            print("\n监控程序被用户中断")
            monitor.stop()
    
    def run_getdata(self, only=False, date=None):
        """运行数据获取任务"""
        print("=" * 50)
        print("运行数据获取任务...")
        print("=" * 50)
        
        email_processor = EmailProcessor()
        found_success_email = email_processor.process_baah_email(date)
        
        if found_success_email:
            if not only:
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
                print("--only模式: 仅执行数据获取任务，跳过后续操作")
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
        print("  -fix         修复配置文件路径")
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
        print("  baah_manager.exe -fix")
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
                # 从外部文件加载配置编辑页面
                template_path = os.path.join(os.path.dirname(__file__), 'templates', 'webui.html')
                try:
                    with open(template_path, 'r', encoding='utf-8') as f:
                        html_template = f.read()
                    
                    # 替换模板中的变量
                    html = html_template.replace('{{CONFIG_DATA}}', json.dumps(config, ensure_ascii=False))
                    html = html.replace('{{CHINESE_LABELS}}', json.dumps(CONFIG_CHINESE_LABELS, ensure_ascii=False))
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(html.encode('utf-8'))
                except Exception as e:
                    self.send_response(500)
                    self.send_header('Content-type', 'text/plain; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(f'加载模板失败: {str(e)}'.encode('utf-8'))
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
                    only = data.get('only', False)
                    date = data.get('date', None)
                    
                    # 在新线程中执行命令以避免阻塞
                    def run_command():
                        try:
                            baah_manager = BAAHManager()
                            if command == 'check':
                                baah_manager.run_check()
                            elif command == 'monitor':
                                baah_manager.run_monitor(only)
                            elif command == 'getdata':
                                baah_manager.run_getdata(only, date)
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

def fix_paths():
    """修复配置文件中的路径设置"""
    print("=" * 50)
    print("运行路径修复任务...")
    print("=" * 50)
    
    # 获取当前项目路径
    current_dir = os.path.abspath(os.path.dirname(__file__))
    print(f"当前项目路径: {current_dir}")
    
    # 创建必要的目录结构
    data_dir = os.path.join(current_dir, 'data')
    resources_dir = os.path.join(data_dir, 'resources')
    output_dir = os.path.join(current_dir, 'output')
    logs_dir = os.path.join(current_dir, 'logs')
    
    dirs_to_create = [data_dir, resources_dir, output_dir, logs_dir]
    for dir_path in dirs_to_create:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"创建目录: {dir_path}")
        else:
            print(f"目录已存在: {dir_path}")
    
    # 更新配置文件
    config_manager = ConfigManager()
    current_config = config_manager.get_all_config()
    
    # 更新文件路径
    new_file_paths = {
        'status_file': os.path.join(data_dir, 'status.txt'),
        'resources_folder': resources_dir,
        'html_output': os.path.join(output_dir, 'baah_task_report.html'),
        'log_file': os.path.join(logs_dir, 'baah.log')
    }
    
    # 更新程序路径
    new_program_paths = {
        'baah_task_name': current_config.get('program_paths', {}).get('baah_task_name', 'BAAH'),
        'mumu_task_name': current_config.get('program_paths', {}).get('mumu_task_name', 'MUMU'),
        'baah_folder': os.path.join(current_dir, 'BAAH')
    }
    
    # 构建新配置
    new_config = {
        **current_config,
        'file_paths': new_file_paths,
        'program_paths': new_program_paths
    }
    
    # 保存配置
    success = config_manager.update_config(new_config)
    
    if success:
        print("=" * 50)
        print("路径修复成功!")
        print("=" * 50)
        print("更新后的文件路径:")
        for key, value in new_file_paths.items():
            print(f"  {key}: {value}")
        print("更新后的程序路径:")
        for key, value in new_program_paths.items():
            print(f"  {key}: {value}")
    else:
        print("=" * 50)
        print("路径修复失败!")
        print("=" * 50)

def main():
    # 初始化配置管理器，自动检查配置文件
    ConfigManager()
    
    # 处理特殊情况：-getdata 后直接跟日期
    if len(sys.argv) > 2 and sys.argv[1] == '-getdata':
        # 检查第二个参数是否为日期格式 (6位数字)
        if sys.argv[2].isdigit() and len(sys.argv[2]) == 6:
            # 构建新的参数列表，将日期转换为 --date 参数
            new_argv = sys.argv[:2] + ['--date', sys.argv[2]] + sys.argv[3:]
            sys.argv = new_argv
    
    parser = argparse.ArgumentParser(description='BAAH任务管理程序')
    parser.add_argument('-check', action='store_true', help='运行检查任务')
    parser.add_argument('-monitor', action='store_true', help='运行监控任务')
    parser.add_argument('-getdata', action='store_true', help='运行数据获取任务')
    parser.add_argument('-send', action='store_true', help='运行报告生成任务')
    parser.add_argument('-writesuccess', action='store_true', help='写入success状态')
    parser.add_argument('-preview', action='store_true', help='预览时间段操作配置')
    parser.add_argument('-fix', action='store_true', help='修复配置文件路径')
    parser.add_argument('-help', action='store_true', help='显示帮助信息')
    parser.add_argument('--only', action='store_true', help='仅执行指定任务，跳过后续操作')
    parser.add_argument('--date', type=str, help='指定日期（格式：YYMMDD，如260101表示2026年1月1日）')
    
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
        print("  ba.py -getdata YYMMDD 运行数据获取并指定日期")
        print("  ba.py -send        生成报告")
        print("  ba.py -writesuccess 写入成功状态")
        print("  ba.py -preview     预览时间段操作配置")
        print("  ba.py -help        显示帮助信息")
        print("  --only             仅执行指定任务，跳过后续操作")
        print("  --date YYMMDD      指定日期（如260101表示2026年1月1日）")
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
        baah_manager.run_monitor(args.only)
    elif args.getdata:
        baah_manager.run_getdata(args.only, args.date)
    elif args.send:
        baah_manager.run_send()
    elif args.writesuccess:
        baah_manager.run_writesuccess()
    elif args.preview:
        system_ops = SystemOperations()
        system_ops.get_scheduled_actions_preview()
    elif args.fix:
        fix_paths()
    elif args.help:
        baah_manager.show_help()
    else:
        baah_manager.show_help()

if __name__ == "__main__":
    main()
