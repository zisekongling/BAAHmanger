[file name]: task_scheduler_setup.md
[file content begin]
# 任务计划程序配置指南

## 1. 创建BAAH启动任务

1. 打开"任务计划程序"
2. 点击"创建任务"
3. 在"常规"选项卡中：
   - 名称：`启动BAAH任务`
   - 勾选"使用最高权限运行"
   - 配置为：`Windows 10`

4. 在"触发器"选项卡中：
   - 点击"新建"
   - 根据需要设置触发时间（如每天特定时间）
   - 或者不设置触发器，只手动运行

5. 在"操作"选项卡中：
   - 点击"新建"
   - 操作：`启动程序`
   - 程序或脚本：`C:\Path\To\BAAH\BAAH.exe`
   - 起始于：`C:\Path\To\BAAH\`

6. 在"条件"选项卡中：
   - 取消勾选"只有在计算机使用交流电源时才启动此任务"
   - 勾选"唤醒计算机运行此任务"

## 2. 创建MUMU模拟器启动任务

1. 重复上述步骤
2. 任务名称：`启动MUMU模拟器`
3. 程序或脚本：`C:\Program Files\MuMu\emulator\nemu9\EmulatorShell\NemuPlayer.exe`
4. 起始于：`C:\Program Files\MuMu\emulator\nemu9\EmulatorShell\`

## 3. 配置文件设置

在 `config.json` 中配置：

```json
"program_paths": {
  "baah_task_name": "启动BAAH任务",
  "mumu_task_name": "启动MUMU模拟器",
  "baah_folder": "C:\\Path\\To\\BAAH"
}