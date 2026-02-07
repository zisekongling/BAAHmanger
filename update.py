import os
import sys
import json
import requests
import zipfile
import shutil
import time
import subprocess
from pathlib import Path
from datetime import datetime

# ==================== 硬编码配置 ====================
CONFIG = {
    "gitee_owner": "zisekongling",          # Gitee仓库所有者
    "gitee_repo": "baah-statistics",        # 仓库名称
    "version_file": "version.txt",          # 本地版本文件
    "update_zip": "update.zip",             # 更新包文件名
    "update_json": "update.json",           # 更新配置文件
    "temp_dir": "_update_temp",             # 临时目录
    "backup_dir": "_backup",                # 备份目录
    "new_update_exe": "newupdate.exe",      # 新的更新程序文件名
    "self_update_bat": "self_update.bat",   # 自更新批处理文件
    "api_timeout": 30,                      # API请求超时(秒)
    "max_retry": 3,                         # 最大重试次数
    "max_release_check": 5,                 # 最多检查多少个release
}

class AppUpdater:
    """应用更新器"""
    
    def __init__(self):
        self.current_dir = Path.cwd()
        self.version_file = self.current_dir / CONFIG["version_file"]
        self.temp_dir = self.current_dir / CONFIG["temp_dir"]
        self.backup_dir = self.current_dir / CONFIG["backup_dir"]
        self.new_update_exe = self.current_dir / CONFIG["new_update_exe"]
        self.update_json = None
        self.downloaded_zip = None  # 记录下载的压缩包路径
        
        # 确保临时目录存在
        self.temp_dir.mkdir(exist_ok=True)
        
    def init_version_file(self):
        """初始化版本文件（如果不存在）"""
        if not self.version_file.exists():
            print("版本文件不存在，创建初始版本 0.0.0")
            self.write_version("0.0.0")
            return True
        return False
    
    def read_version(self):
        """读取当前版本"""
        try:
            with open(self.version_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            print(f"读取版本文件失败: {e}")
            return "0.0.0"
    
    def write_version(self, version):
        """写入版本"""
        try:
            with open(self.version_file, 'w', encoding='utf-8') as f:
                f.write(version)
            print(f"版本已更新为: {version}")
            return True
        except Exception as e:
            print(f"写入版本文件失败: {e}")
            return False
    
    def compare_versions(self, v1, v2):
        """比较版本号（简单字符串比较）"""
        # 去除可能的 'v' 前缀
        v1 = v1.lstrip('vV')
        v2 = v2.lstrip('vV')
        
        # 按点分割版本号
        try:
            v1_parts = list(map(int, v1.split('.')))
            v2_parts = list(map(int, v2.split('.')))
        except ValueError:
            # 如果版本号解析失败，使用字符串比较
            return -1 if v1 < v2 else (1 if v1 > v2 else 0)
        
        # 补齐版本号长度
        max_len = max(len(v1_parts), len(v2_parts))
        v1_parts.extend([0] * (max_len - len(v1_parts)))
        v2_parts.extend([0] * (max_len - len(v2_parts)))
        
        # 逐位比较
        for i in range(max_len):
            if v1_parts[i] < v2_parts[i]:
                return -1  # v1 < v2
            elif v1_parts[i] > v2_parts[i]:
                return 1   # v1 > v2
        return 0  # v1 == v2
    
    def get_releases(self):
        """从Gitee获取release列表（从最新到最旧）"""
        url = f"https://gitee.com/api/v5/repos/{CONFIG['gitee_owner']}/{CONFIG['gitee_repo']}/releases"
        
        for attempt in range(CONFIG["max_retry"]):
            try:
                print(f"正在获取release列表... (尝试 {attempt+1}/{CONFIG['max_retry']})")
                response = requests.get(url, timeout=CONFIG["api_timeout"])
                
                if response.status_code == 404:
                    print("仓库未找到或没有release")
                    return []
                elif response.status_code == 200:
                    releases = response.json()
                    # 按发布时间排序（最新的在前面）
                    releases.sort(key=lambda x: x.get('created_at', ''), reverse=True)
                    # 只保留前N个release
                    return releases[:CONFIG["max_release_check"]]
                else:
                    print(f"API请求失败，状态码: {response.status_code}")
                    
            except requests.exceptions.Timeout:
                print("请求超时")
            except requests.exceptions.RequestException as e:
                print(f"网络请求错误: {e}")
            except json.JSONDecodeError as e:
                print(f"JSON解析错误: {e}")
            
            if attempt < CONFIG["max_retry"] - 1:
                time.sleep(2)  # 重试前等待
        
        return []
    
    def download_and_parse_update_json(self, assets):
        """下载并解析update.json"""
        # 查找update.json
        json_asset = None
        for asset in assets:
            if asset.get('name') == CONFIG["update_json"]:
                json_asset = asset
                break
        
        if not json_asset:
            print(f"未找到{CONFIG['update_json']}文件")
            return None
        
        # 下载update.json
        download_url = json_asset.get('browser_download_url')
        if not download_url:
            print("update.json下载链接无效")
            return None
        
        temp_json = self.temp_dir / CONFIG["update_json"]
        try:
            response = requests.get(download_url, timeout=CONFIG["api_timeout"])
            response.raise_for_status()
            
            with open(temp_json, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            # 解析JSON
            with open(temp_json, 'r', encoding='utf-8') as f:
                update_info = json.load(f)
            
            # 验证必要字段
            required_fields = ['min_version', 'force_update']
            for field in required_fields:
                if field not in update_info:
                    print(f"update.json缺少必要字段: {field}")
                    return None
            
            self.update_json = update_info
            print(f"读取更新配置: 最低版本={update_info['min_version']}, 强制更新={update_info['force_update']}")
            return update_info
            
        except Exception as e:
            print(f"下载或解析update.json失败: {e}")
            return None
    
    def check_version_compatibility(self, update_info, current_version):
        """检查版本兼容性"""
        min_version = update_info.get('min_version', '0.0.0')
        
        # 如果当前版本大于等于最低要求版本，则兼容
        return self.compare_versions(current_version, min_version) >= 0
    
    def find_update_asset(self, assets):
        """在release附件中查找更新包"""
        # 优先查找 update.zip
        for asset in assets:
            if asset.get('name') == CONFIG["update_zip"]:
                return asset
        
        # 如果没找到 update.zip，查找第一个zip文件
        for asset in assets:
            if asset.get('name', '').lower().endswith('.zip'):
                return asset
        
        # 查找第一个文件
        if assets:
            return assets[0]
        
        return None
    
    def download_file(self, url, filename):
        """下载文件"""
        try:
            print(f"正在下载: {filename}")
            
            # 创建临时目录
            self.temp_dir.mkdir(exist_ok=True)
            filepath = self.temp_dir / filename
            
            # 下载文件
            response = requests.get(url, stream=True, timeout=CONFIG["api_timeout"])
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # 显示下载进度
                        if total_size > 0:
                            percent = downloaded * 100 // total_size
                            print(f"\r下载进度: {percent}% ({downloaded}/{total_size} bytes)", end='')
            
            print()  # 换行
            print(f"下载完成: {filepath}")
            
            # 记录下载的压缩包路径，用于后续删除
            self.downloaded_zip = filepath
            return filepath
            
        except Exception as e:
            print(f"下载失败: {e}")
            return None
    
    def backup_file(self, filepath):
        """备份文件"""
        try:
            if not self.backup_dir.exists():
                self.backup_dir.mkdir(parents=True)
            
            # 计算相对路径
            relative_path = filepath.relative_to(self.current_dir)
            backup_path = self.backup_dir / relative_path
            
            # 确保目标目录存在
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 复制文件
            if filepath.is_file():
                shutil.copy2(filepath, backup_path)
                print(f"已备份: {relative_path}")
            elif filepath.is_dir():
                shutil.copytree(filepath, backup_path, dirs_exist_ok=True)
                print(f"已备份目录: {relative_path}")
            
            return True
        except Exception as e:
            print(f"备份失败 {filepath}: {e}")
            return False
    
    def extract_zip(self, zip_path):
        """解压ZIP文件"""
        try:
            print("正在解压更新包...")
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # 先获取所有文件列表
                file_list = zip_ref.namelist()
                total_files = len(file_list)
                
                # 解压所有文件
                for i, filename in enumerate(file_list, 1):
                    # 跳过目录条目
                    if filename.endswith('/'):
                        continue
                    
                    # 计算目标路径
                    target_path = self.temp_dir / filename
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # 提取文件
                    with zip_ref.open(filename) as source, open(target_path, 'wb') as target:
                        shutil.copyfileobj(source, target)
                    
                    # 显示进度
                    print(f"\r解压进度: {i}/{total_files}", end='')
            
            print()  # 换行
            print("解压完成")
            
            # 解压完成后删除下载的压缩包
            self.delete_downloaded_zip()
            
            return True
            
        except zipfile.BadZipFile:
            print("ZIP文件损坏")
            return False
        except Exception as e:
            print(f"解压失败: {e}")
            return False
    
    def delete_downloaded_zip(self):
        """删除下载的压缩包"""
        if self.downloaded_zip and self.downloaded_zip.exists():
            try:
                self.downloaded_zip.unlink()
                print(f"已删除下载的压缩包: {self.downloaded_zip.name}")
                self.downloaded_zip = None
                return True
            except Exception as e:
                print(f"删除压缩包失败: {e}")
                return False
        return False
    
    def apply_update(self):
        """应用更新"""
        print("开始应用更新...")
        
        # 获取临时目录中的文件
        update_root = self.temp_dir
        
        # 遍历临时目录中的所有文件和目录
        for item in update_root.rglob('*'):
            if item.is_file():
                # 计算目标路径
                relative_path = item.relative_to(update_root)
                target_path = self.current_dir / relative_path
                
                # 跳过update.json文件本身（已经在内存中）
                if item.name == CONFIG["update_json"]:
                    continue
                
                # 如果目标文件已存在，先备份（除了newupdate.exe，因为这是用于自更新的）
                if target_path.exists() and item.name != CONFIG["new_update_exe"]:
                    self.backup_file(target_path)
                
                # 确保目标目录存在
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                # 尝试复制文件
                try:
                    shutil.copy2(item, target_path)
                    print(f"更新: {relative_path}")
                except PermissionError:
                    print(f"文件被占用，跳过: {relative_path}")
                    print("请关闭正在运行的程序后重试")
                    return False
                except Exception as e:
                    print(f"更新失败 {relative_path}: {e}")
        
        print("更新应用完成")
        return True
    
    def create_self_update_bat(self):
        """创建自更新批处理文件"""
        bat_content = """@echo off
timeout /t 2 /nobreak >nul
if exist "update.exe" del "update.exe"
if exist "newupdate.exe" ren "newupdate.exe" "update.exe"
del "%~f0"
"""
        
        bat_path = self.current_dir / CONFIG["self_update_bat"]
        try:
            with open(bat_path, 'w', encoding='gbk') as f:
                f.write(bat_content)
            print(f"已创建自更新批处理文件")
            return bat_path
        except Exception as e:
            print(f"创建自更新批处理文件失败: {e}")
            return None
    
    def check_self_update(self):
        """检查是否需要更新更新程序本身"""
        if self.new_update_exe.exists():
            print("检测到更新程序需要自我更新...")
            bat_path = self.create_self_update_bat()
            if bat_path:
                print("将在退出后执行自更新...")
                return bat_path
        return None
    
    def cleanup(self):
        """清理临时文件"""
        try:
            # 首先确保删除下载的压缩包（如果还存在）
            self.delete_downloaded_zip()
            
            # 清理临时目录
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                print("已清理临时文件")
            
            # 清理备份（保留最近3个备份）
            if self.backup_dir.exists():
                backup_dirs = []
                for item in self.backup_dir.iterdir():
                    if item.is_dir():
                        try:
                            # 尝试将目录名解析为时间戳
                            backup_time = datetime.fromisoformat(item.name.replace('_', ':'))
                            backup_dirs.append((item, backup_time))
                        except:
                            pass
                
                # 按时间排序，保留最新的3个
                backup_dirs.sort(key=lambda x: x[1], reverse=True)
                for item, _ in backup_dirs[3:]:
                    shutil.rmtree(item)
                    print(f"清理旧备份: {item.name}")
                
            return True
        except Exception as e:
            print(f"清理失败: {e}")
            return False
    
    def check_and_update(self):
        """主更新流程"""
        print("=" * 50)
        print("应用更新检查")
        print("=" * 50)
        
        # 1. 初始化版本文件
        self.init_version_file()
        
        # 2. 获取当前版本
        current_version = self.read_version()
        print(f"当前版本: {current_version}")
        
        # 3. 获取release列表
        print("正在获取release列表...")
        releases = self.get_releases()
        
        if not releases:
            print("无法获取release信息或没有可用的release")
            return False
        
        print(f"找到 {len(releases)} 个release")
        
        # 4. 遍历release，寻找兼容的更新
        compatible_release = None
        compatible_update_info = None
        
        for i, release in enumerate(releases, 1):
            print(f"\n检查第 {i} 个release: {release.get('tag_name', '未知版本')}")
            
            # 获取release的assets
            assets = release.get('assets', [])
            
            # 下载并解析update.json
            update_info = self.download_and_parse_update_json(assets)
            if not update_info:
                print(f"跳过第 {i} 个release: 无法获取update.json")
                continue
            
            # 检查版本兼容性
            if self.check_version_compatibility(update_info, current_version):
                print(f"版本兼容性检查通过!")
                compatible_release = release
                compatible_update_info = update_info
                break
            else:
                print(f"版本不兼容: 当前版本 {current_version}, 要求最低版本 {update_info['min_version']}")
        
        if not compatible_release:
            print("\n未找到兼容的更新版本")
            return False
        
        # 5. 显示更新信息
        latest_version = compatible_release.get('tag_name', '0.0.0')
        print(f"\n找到兼容的更新版本: {latest_version}")
        print(f"更新标题: {compatible_release.get('name', '无标题')}")
        print(f"发布时间: {compatible_release.get('published_at', '未知时间')}")
        print(f"最低兼容版本: {compatible_update_info.get('min_version', '0.0.0')}")
        print(f"强制更新: {'是' if compatible_update_info.get('force_update', False) else '否'}")
        print("\n更新说明:")
        print("-" * 40)
        print(compatible_release.get('body', '无更新说明'))
        print("-" * 40)
        
        # 6. 比较版本
        compare_result = self.compare_versions(current_version, latest_version)
        
        if compare_result >= 0:
            print("当前已是最新版本，无需更新")
            return True
        
        # 7. 询问用户是否更新（除非是强制更新）
        if not compatible_update_info.get('force_update', False):
            print("\n发现新版本，是否立即更新？")
            print("按 Enter 键继续更新，按其他任意键取消")
            
            try:
                choice = input(">>> ").strip()
            except KeyboardInterrupt:
                print("\n更新已取消")
                return False
            
            if choice != "":
                print("更新已取消")
                return False
        else:
            print("\n检测到强制更新，即将开始更新...")
            time.sleep(2)
        
        # 8. 查找更新包
        update_asset = self.find_update_asset(compatible_release.get('assets', []))
        
        if not update_asset:
            print("未找到更新包")
            return False
        
        print(f"找到更新包: {update_asset.get('name', '未知文件')}")
        
        # 9. 下载更新包
        download_url = update_asset.get('browser_download_url')
        if not download_url:
            print("更新包下载链接无效")
            return False
        
        zip_path = self.download_file(download_url, CONFIG["update_zip"])
        if not zip_path:
            return False
        
        # 10. 解压更新包
        if not self.extract_zip(zip_path):
            return False
        
        # 11. 应用更新
        if not self.apply_update():
            print("更新失败")
            return False
        
        # 12. 更新版本号
        if not self.write_version(latest_version):
            print("警告：版本号更新失败")
        
        # 13. 清理临时文件
        self.cleanup()
        
        print("=" * 50)
        print("更新完成！")
        print("=" * 50)
        print(f"已从版本 {current_version} 更新到 {latest_version}")
        
        return True

def main():
    """主函数"""
    # 确保程序在正确的目录运行
    if getattr(sys, 'frozen', False):
        # 如果是打包的exe，切换到exe所在目录
        os.chdir(os.path.dirname(sys.executable))
    
    # 创建更新器实例
    updater = AppUpdater()
    
    try:
        # 执行更新检查
        success = updater.check_and_update()
        
        # 处理完更新后，检查是否需要自更新
        if success:
            # 检查是否需要更新更新程序本身
            bat_path = updater.check_self_update()
            if bat_path:
                print("\n检测到更新程序有更新，将在退出后自动更新...")
                time.sleep(1)
                
                # 启动批处理文件
                try:
                    # 使用Popen启动bat文件，不等待其完成
                    subprocess.Popen(
                        ['cmd', '/c', str(bat_path)],
                        shell=True
                    )
                    print("已启动自更新程序，当前程序即将退出...")
                    time.sleep(1)
                    return  # 直接退出，让bat文件处理后续
                except Exception as e:
                    print(f"启动自更新失败: {e}")
            
            # 如果没有自更新，正常退出
            print("\n按任意键退出...")
            input()
        else:
            print("\n更新过程中出现错误")
            print("按任意键退出...")
            input()
            
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
    except Exception as e:
        print(f"\n程序发生错误: {e}")
        import traceback
        traceback.print_exc()
        print("按任意键退出...")
        input()

if __name__ == "__main__":
    main()
