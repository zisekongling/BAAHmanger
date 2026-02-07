import psutil
import time
import subprocess
import threading
from datetime import datetime
import os
import sys
import shlex
from config_manager import ConfigManager

class ProcessMonitor:
    def __init__(self):
        self.config = ConfigManager()
        self.start_time = time.time()
        self.running = True
        self.baah_process_name = self.config.get('process_names.baah_process')
        self.mumu_process_name = self.config.get('process_names.mumu_process')
        self.check_interval = self.config.get('timing.check_interval', 5)
        self.crash_timeout = int(self.config.get('timing.crash_timeout', 600))
        
        # 记录上一次检查时进程的状态
        self.last_baah_state = False
        self.last_mumu_state = False
        
        print("进程监控已启动，开始计时...")
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    def is_process_running(self, process_name):
        """检查指定进程是否正在运行"""
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] and process_name.lower() == proc.info['name'].lower():
                return True
        return False
    
    def start_task_scheduler_task(self, task_name):
        """通过Windows任务计划程序启动任务"""
        try:
            # 使用schtasks命令运行任务
            cmd = ['schtasks', '/run', '/tn', task_name]
            
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
            
            if result.returncode == 0:
                print(f"已通过任务计划程序启动任务: {task_name}")
                return True
            else:
                print(f"启动任务失败: {task_name}")
                print(f"错误信息: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"启动任务时出错: {e}")
            return False
    
    def start_baah_process(self):
        """启动BAAH进程（通过计划任务）"""
        baah_task_name = self.config.get('program_paths.baah_task_name')
        if not baah_task_name:
            print("BAAH任务名称配置为空")
            return False
        
        return self.start_task_scheduler_task(baah_task_name)
    
    def start_mumu_process(self):
        """启动MUMU进程（通过计划任务）"""
        mumu_task_name = self.config.get('program_paths.mumu_task_name')
        if not mumu_task_name:
            print("MUMU任务名称配置为空")
            return False
        
        return self.start_task_scheduler_task(mumu_task_name)
    
    def terminate_processes(self):
        """终止BAAH和MUMU进程"""
        terminated = False
        for proc in psutil.process_iter():
            try:
                if proc.name().lower() in [self.baah_process_name.lower(), self.mumu_process_name.lower()]:
                    proc.terminate()
                    proc.wait(timeout=3)
                    print(f"已终止进程: {proc.name()}")
                    terminated = True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                continue
        
        return terminated
    
    def reset_monitoring_time(self):
        """重置监控开始时间"""
        self.start_time = time.time()
        print(f"重置监控时间，新的开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"防崩溃保护模式重新计时: {self.crash_timeout}秒")
    
    def monitor(self):
        """主监控循环，返回True表示任务完成"""
        print("进程监控已启动，开始计时...")
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"防崩溃保护模式持续时间: {self.crash_timeout}秒")
        
        while self.running:
            current_time = time.time()
            elapsed = current_time - self.start_time
            
            baah_running = self.is_process_running(self.baah_process_name)
            mumu_running = self.is_process_running(self.mumu_process_name)
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 已运行: {int(elapsed)}秒, BAAH运行: {baah_running}, MUMU运行: {mumu_running}")
            
            # 检查进程状态变化（崩溃检测）
            process_restarted = False
            
            # 检测BAAH是否崩溃并重新启动
            if self.last_baah_state and not baah_running and elapsed < self.crash_timeout:
                print("检测到BAAH进程崩溃!")
                time.sleep(5)  # 等待一下，避免误判
                if not self.is_process_running(self.baah_process_name):  # 确认确实崩溃
                    print("尝试重新启动BAAH进程...")
                    if self.start_baah_process():
                        process_restarted = True
            
            # 检测MUMU是否崩溃并重新启动
            if self.last_mumu_state and not mumu_running and elapsed < self.crash_timeout:
                print("检测到MUMU进程崩溃!")
                time.sleep(5)  # 等待一下，避免误判
                if not self.is_process_running(self.mumu_process_name):  # 确认确实崩溃
                    print("尝试重新启动MUMU进程...")
                    if self.start_mumu_process():
                        process_restarted = True
            
            # 如果进程崩溃并成功重启，重置监控时间
            if process_restarted:
                self.reset_monitoring_time()
                # 更新当前状态
                baah_running = self.is_process_running(self.baah_process_name)
                mumu_running = self.is_process_running(self.mumu_process_name)
            
            # 更新上一次的状态记录
            self.last_baah_state = baah_running
            self.last_mumu_state = mumu_running
            
            # 前crash_timeout秒逻辑（防闪退）
            if elapsed < self.crash_timeout:
                if not baah_running or not mumu_running:
                    time.sleep(10)
                    
                    baah_running = self.is_process_running(self.baah_process_name)
                    mumu_running = self.is_process_running(self.mumu_process_name)
                    
                    if not baah_running:
                        print("BAAH进程未运行，尝试通过计划任务启动...")
                        if self.start_baah_process():
                            self.reset_monitoring_time()  # 启动后重置时间
                    
                    if not mumu_running:
                        print("MUMU进程未运行，尝试通过计划任务启动...")
                        if self.start_mumu_process():
                            self.reset_monitoring_time()  # 启动后重置时间
            else:
                # crash_timeout秒后逻辑（任务完成）
                if not baah_running or not mumu_running:
                    print(f"防崩溃保护期({self.crash_timeout}秒)已过，检测到进程关闭，等待20秒...")
                    time.sleep(20)
                    
                    baah_running = self.is_process_running(self.baah_process_name)
                    mumu_running = self.is_process_running(self.mumu_process_name)
                    
                    if baah_running or mumu_running:
                        print("等待后仍有进程在运行，终止所有进程...")
                        self.terminate_processes()
                    
                    print("任务已完成，准备进行后续处理...")
                    self.running = False
                    return True  # 返回True表示任务完成
            
            time.sleep(int(self.check_interval))
        
        return False  # 返回False表示监控被中断或未检测到任务完成
    
    def stop(self):
        """停止监控"""
        self.running = False
