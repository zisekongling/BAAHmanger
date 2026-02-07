import os
from config_manager import ConfigManager

class SuccessWriter:
    def __init__(self):
        self.config = ConfigManager()
    
    def write_success(self):
        """写入success到状态文件"""
        status_file = self.config.get('file_paths.status_file')
        return self.write_success_to_file(status_file)
    
    def write_success_to_file(self, file_path):
        """写入success到指定文件"""
        try:
            # 读取文件内容
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            # 确保文件至少有2行
            while len(lines) < 2:
                lines.append('\n')
            
            # 将第二行替换为"success"
            lines[1] = "success\n"
            
            # 写回文件
            with open(file_path, 'w') as f:
                f.writelines(lines)
            
            print(f"已成功将'success'写入文件 {file_path} 的第二行")
            return True
        
        except Exception as e:
            print(f"写入文件时出错: {e}")
            return False