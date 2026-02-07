import os
import time
import sys
from datetime import datetime
from config_manager import ConfigManager

class SystemOperations:
    def __init__(self):
        self.config = ConfigManager()
    
    def execute_completion_action(self):
        """执行任务完成后的操作"""
        # 根据当前时间获取对应的操作
        action = self.config.get_action_for_current_time()
        
        # 获取操作名称描述
        action_names = {
            "none": "不执行任何操作",
            "logout": "注销系统",
            "shutdown": "关闭计算机",
            "restart": "重新启动"
        }
        
        current_time = datetime.now().strftime("%H:%M")
        action_desc = action_names.get(action, f"未知操作 ({action})")
        
        print(f"当前时间: {current_time}")
        print(f"将执行操作: {action_desc}")
        
        wait_time = self.config.get('timing.logout_wait_time', 10)
        print(f"{wait_time}秒后执行操作...")
        time.sleep(int(wait_time))
        
        try:
            if sys.platform == "win32":
                # Windows系统
                if action == "logout":
                    os.system("shutdown /l /f")
                elif action == "shutdown":
                    os.system("shutdown /s /f /t 0")
                elif action == "restart":
                    os.system("shutdown /r /f /t 0")
                elif action == "none":
                    print("不执行任何操作，正常退出")
                else:
                    print(f"未知的操作类型: {action}")
            
            elif sys.platform == "darwin":
                # macOS系统
                if action == "logout":
                    os.system("pkill loginwindow")
                elif action == "shutdown":
                    os.system("sudo shutdown -h now")
                elif action == "restart":
                    os.system("sudo shutdown -r now")
                elif action == "none":
                    print("不执行任何操作，正常退出")
                else:
                    print(f"未知的操作类型: {action}")
            
            else:
                # Linux系统
                if action == "logout":
                    os.system("gnome-session-quit --force --logout")
                elif action == "shutdown":
                    os.system("sudo shutdown -h now")
                elif action == "restart":
                    os.system("sudo shutdown -r now")
                elif action == "none":
                    print("不执行任何操作，正常退出")
                else:
                    print(f"未知的操作类型: {action}")
                    
        except Exception as e:
            print(f"执行系统操作时出错: {e}")
    
    def get_scheduled_actions_preview(self):
        """获取时间段操作预览"""
        scheduled_actions = self.config.get('scheduled_completion_actions', [])
        current_time = datetime.now().strftime("%H:%M")
        current_action = self.config.get_action_for_current_time()
        
        action_names = {
            "none": "无操作",
            "logout": "注销",
            "shutdown": "关机",
            "restart": "重启"
        }
        
        print("=" * 60)
        print("时间段操作配置预览")
        print("=" * 60)
        print(f"当前时间: {current_time}")
        print(f"当前将执行: {action_names.get(current_action, current_action)}")
        print("-" * 60)
        
        if scheduled_actions:
            print("配置的时间段:")
            for i, schedule in enumerate(scheduled_actions, 1):
                name = schedule.get('name', f'时间段{i}')
                enabled = schedule.get('enabled', True)
                start_time = schedule.get('start_time', '00:00')
                end_time = schedule.get('end_time', '23:59')
                action = schedule.get('action', 'none')
                
                status = "✓ 启用" if enabled else "✗ 禁用"
                print(f"  {i}. {name} [{status}]")
                print(f"     时间: {start_time} - {end_time}")
                print(f"     操作: {action_names.get(action, action)}")
                print()
        else:
            print("未配置时间段操作，使用全局默认操作")
        
        print("=" * 60)
