import os
import datetime
import subprocess
import sys
from config_manager import ConfigManager

class CheckModule:
    def __init__(self):
        self.config = ConfigManager()
    
    def check_and_execute(self):
        """检查并执行BAAH任务"""
        date_format = "%Y-%m-%d"
        today = datetime.datetime.now().strftime(date_format)
        
        status_file = self.config.get('file_paths.status_file')
        
        # 检查文件是否存在
        if not os.path.exists(status_file):
            print("文件不存在，执行命令并创建文件")
            self.start_baah_process()
            
            # 创建文件并写入日期和空行
            with open(status_file, "w") as f:
                f.write(today + "\n\n")
            return
        
        # 读取文件内容
        with open(status_file, "r") as f:
            lines = f.readlines()
        
        should_run = False
        
        if len(lines) < 2:
            print("文件内容不完整，执行命令")
            should_run = True
        else:
            # 检查第一行是否为当天日期
            if lines[0].strip() != today:
                print("日期不匹配，执行命令")
                should_run = True
            
            # 检查第二行是否为success
            if lines[1].strip() != "success":
                print("状态不是success，执行命令")
                should_run = True
        
        # 如果检查未通过，执行命令并更新文件
        if should_run:
            self.start_baah_process()
            
            # 更新文件内容
            with open(status_file, "w") as f:
                f.write(today + "\n")
                f.write("\n")
        else:
            print("检查通过，无需执行任何操作")
    
    def start_baah_process(self):
        """启动BAAH进程（通过计划任务）"""
        baah_task_name = self.config.get('program_paths.baah_task_name')
        if not baah_task_name:
            print("BAAH任务名称配置为空")
            return False
        
        try:
            # 使用schtasks命令运行任务
            subprocess.run(['schtasks', '/run', '/tn', baah_task_name], 
                          shell=True, check=True)
            print(f"已通过计划任务启动BAAH: {baah_task_name}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"启动BAAH计划任务失败: {e}")
            return False
        except Exception as e:
            print(f"启动BAAH进程失败: {e}")
            return False
