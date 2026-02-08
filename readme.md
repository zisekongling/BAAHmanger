# BAAH统计

#### 介绍
BAAH统计是一个用于自动化管理和统计BAAH任务的工具，支持任务监控、数据采集、报告生成和自动更新等功能。

#### 功能特点
- 任务监控：监控BAAH和MUMU进程，自动执行后续任务
- 数据采集：从邮件中获取BAAH任务数据
- 报告生成：生成详细的HTML报告，包含每日、周度和月度数据统计
- 自动更新：支持从Gitee自动更新程序
- 路径修复：自动修复配置文件路径，确保程序正常运行
- WebUI配置：提供网页界面进行配置管理

#### 软件架构
- **ba.py**：主程序，包含任务管理和WebUI启动功能
- **config_manager.py**：配置管理，使用单例模式管理配置文件
- **report_generator.py**：报告生成，生成HTML格式的统计报告
- **email_processor.py**：邮件处理，从邮件中提取BAAH任务数据
- **process_monitor.py**：进程监控，监控BAAH和MUMU进程
- **system_operations.py**：系统操作，执行任务完成后的系统操作
- **update.py**：自动更新，从Gitee获取更新
- **templates/**：HTML模板目录，包含WebUI和报告模板

#### 安装教程
1.  下载并解压本仓库到本地
2.  运行 `python ba.py -fix` 修复路径配置
3.  运行 `python ba.py` 启动WebUI进行配置
4.  配置完成后，可使用 `python ba.py -monitor` 启动监控

#### 使用说明

**命令行参数：**
- `-check`：运行检查任务（检查今天是否已做BAAH）
- `-monitor`：运行监控任务（监控BAAH和MUMU进程）
- `-getdata`：运行数据获取任务（获取邮件数据并处理）
- `-send`：运行报告生成任务（生成HTML报告并上传）
- `-writesuccess`：写入success状态
- `-preview`：预览时间段操作配置
- `-fix`：修复配置文件路径
- `-help`：显示帮助信息

**配置说明：**
- 运行 `python ba.py` 启动WebUI配置界面
- 或直接编辑 `config.json` 文件进行配置

#### 参与贡献

1.  Fork 本仓库
2.  新建 Feat_xxx 分支
3.  提交代码
4.  新建 Pull Request

#### 许可证
本项目采用 MIT 许可证，详见 LICENSE 文件。
