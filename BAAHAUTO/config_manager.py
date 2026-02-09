import json
import os
import sys
from datetime import datetime

class ConfigManager:
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _get_default_config(self):
        """获取默认配置"""
        return {
            "file_paths": {
                "status_file": "data/status.txt",
                "resources_folder": "data/resources",
                "html_output": "output/baah_task_report.html",
                "log_file": "logs/baah.log"
            },
            "program_paths": {
                "baah_task_name": "启动BAAH任务",
                "mumu_task_name": "启动MUMU模拟器",
                "baah_folder": "C:\\Path\\To\\BAAH"
            },
            "email": {
                "imap_server": "imap.qq.com",
                "email_account": "your_email@qq.com",
                "authorization_code": "your_authorization_code",
                "folder": "INBOX",
                "subject_keyword": "BAAH",
                "sender": "baah@example.com"
            },
            "process_names": {
                "baah_process": "BAAH.exe",
                "mumu_process": "MuMuNxDevice.exe"
            },
            "timing": {
                "check_interval": 5,
                "crash_timeout": 600,
                "logout_wait_time": 10,
                "send_wait_time": 20
            },
            "task_completion_action": "shutdown",  # 全局默认操作
            "scheduled_completion_actions": [  # 新增：按时间段的自定义操作
                {
                    "name": "工作时间",
                    "start_time": "09:00",
                    "end_time": "17:00",
                    "action": "none",
                    "enabled": True
                },
                {
                    "name": "夜间休息",
                    "start_time": "22:00",
                    "end_time": "06:00",
                    "action": "shutdown",
                    "enabled": True
                },
                {
                    "name": "午休时间",
                    "start_time": "12:00",
                    "end_time": "13:00",
                    "action": "logout",
                    "enabled": True
                }
            ],
            "gitee": {
                "owner": "your_gitee_username",
                "repo": "your_repository_name",
                "branch": "main",
                "access_token": "your_access_token",
                "file_path": "reports/baah_report.html"
            }
        }
    
    def _load_config(self):
        """加载配置文件，如果不存在则创建"""
        config_path = self._get_config_path()
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
                
                # 向下兼容：检查是否有scheduled_completion_actions，没有则添加默认
                if 'scheduled_completion_actions' not in self._config:
                    self._config['scheduled_completion_actions'] = [
                        {
                            "name": "默认时间段",
                            "start_time": "00:00",
                            "end_time": "23:59",
                            "action": self._config.get('task_completion_action', 'none'),
                            "enabled": True
                        }
                    ]
                    self._save_config_to_file(config_path)
            else:
                # 配置文件不存在，创建默认配置
                print(f"配置文件不存在，正在创建默认配置文件: {config_path}")
                self._config = self._get_default_config()
                self._save_config_to_file(config_path)
            
            # 设置根目录路径
            root_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            self._config['root_dir'] = root_dir
            
            # 确保文件路径是完整的
            self._ensure_full_paths()
            
        except json.JSONDecodeError as e:
            print(f"配置文件格式错误: {e}")
            print("将使用默认配置")
            self._config = self._get_default_config()
            self._save_config_to_file(config_path)
            self._ensure_full_paths()
        except Exception as e:
            print(f"加载配置失败: {e}")
            self._config = self._get_default_config()
    
    def _save_config_to_file(self, config_path):
        """保存配置到文件"""
        try:
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            print(f"配置文件已创建: {config_path}")
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def _get_config_path(self):
        """获取配置文件路径"""
        # 先检查当前目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, "config.json")
        
        # 如果不在当前目录，检查执行目录
        if not os.path.exists(config_path):
            exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            config_path = os.path.join(exe_dir, "config.json")
        
        return config_path
    
    def _ensure_full_paths(self):
        """确保所有文件路径都是完整路径"""
        if not self._config:
            return
        
        root_dir = self._config.get('root_dir', '')
        if not root_dir:
            root_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            self._config['root_dir'] = root_dir
        
        # 更新文件路径
        file_paths = self._config.get('file_paths', {})
        for key, path in file_paths.items():
            if not os.path.isabs(path):
                file_paths[key] = os.path.join(root_dir, path)
        
        # 确保目录存在
        folders = [
            os.path.dirname(file_paths.get('status_file', '')),
            file_paths.get('resources_folder', ''),
            os.path.dirname(file_paths.get('html_output', '')),
            os.path.dirname(file_paths.get('log_file', ''))
        ]
        
        for folder in folders:
            if folder and not os.path.exists(folder):
                os.makedirs(folder, exist_ok=True)
    
    def get(self, key, default=None):
        """获取配置值"""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key, value):
        """设置配置值（仅在内存中）"""
        keys = key.split('.')
        config = self._config
        
        for i, k in enumerate(keys[:-1]):
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save(self):
        """保存配置到文件"""
        config_path = self._get_config_path()
        try:
            # 移除临时字段
            config_to_save = self._config.copy()
            if 'root_dir' in config_to_save:
                del config_to_save['root_dir']
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False
    
    def get_all_config(self):
        """获取所有配置（排除临时字段）"""
        config = self._config.copy()
        if 'root_dir' in config:
            del config['root_dir']
        return config
    
    def update_config(self, new_config):
        """更新整个配置"""
        if not isinstance(new_config, dict):
            return False
        
        # 保留根目录
        root_dir = self._config.get('root_dir', '')
        self._config = new_config
        if root_dir:
            self._config['root_dir'] = root_dir
        
        # 确保文件路径是完整的
        self._ensure_full_paths()
        
        # 保存到文件
        return self.save()
    
    def get_action_for_current_time(self):
        """根据当前时间获取对应的操作"""
        scheduled_actions = self.get('scheduled_completion_actions', [])
        current_time = datetime.now().strftime("%H:%M")
        
        # 如果没有配置时间段或为空，返回全局默认
        if not scheduled_actions:
            return self.get('task_completion_action', 'none')
        
        # 查找当前时间所在的时间段
        for schedule in scheduled_actions:
            if not schedule.get('enabled', True):
                continue
                
            start_time = schedule.get('start_time', '00:00')
            end_time = schedule.get('end_time', '23:59')
            
            # 处理跨午夜的时间段
            if start_time <= end_time:
                # 正常时间段（同一天内）
                if start_time <= current_time <= end_time:
                    return schedule.get('action', 'none')
            else:
                # 跨午夜的时间段
                if current_time >= start_time or current_time <= end_time:
                    return schedule.get('action', 'none')
        
        # 如果没有匹配的时间段，返回全局默认
        return self.get('task_completion_action', 'none')
