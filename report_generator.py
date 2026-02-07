import json
import os
import glob
from datetime import datetime, timedelta
import pandas as pd
import base64
import requests
import sys
from config_manager import ConfigManager

def get_resource_path(relative_path):
    """获取资源文件路径，适配打包环境"""
    try:
        # 打包后的路径
        base_path = sys._MEIPASS
    except Exception:
        # 未打包的路径
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

class ReportGenerator:
    def __init__(self):
        self.config = ConfigManager()
    
    def parse_resource_value(self, value_str):
        """解析资源字符串为数值"""
        if isinstance(value_str, (int, float)):
            return value_str
        
        # 移除逗号和非数字字符（保留数字和负号）
        cleaned = ''.join(c for c in str(value_str) if c.isdigit() or c == '-')
        if cleaned and cleaned != '-':
            return int(cleaned)
        return 0
    
    def calculate_weekly_report(self, df):
        """计算周度报告数据"""
        # 确保日期是datetime类型
        df['datetime'] = pd.to_datetime(df['datetime'])
        
        # 按周分组（周一到周日）
        df['week_start'] = df['datetime'] - pd.to_timedelta(df['datetime'].dt.dayofweek, unit='D')
        weekly_data = []
        
        for week_start, week_group in df.groupby('week_start'):
            week_end = week_start + timedelta(days=6)
            days_in_week = len(week_group)
            
            # 过滤掉负数数据计算平均值
            positive_baah_days = week_group[week_group['baah_diamond_gain'] > 0]
            positive_net_days = week_group[week_group['net_diamond_gain'] > 0]
            positive_duration_days = week_group[week_group['duration_minutes'] > 0]
            
            avg_baah_diamond = (positive_baah_days['baah_diamond_gain'].sum() / 
                                len(positive_baah_days)) if len(positive_baah_days) > 0 else 0
            avg_net_diamond = (positive_net_days['net_diamond_gain'].sum() / 
                              len(positive_net_days)) if len(positive_net_days) > 0 else 0
            avg_duration = (positive_duration_days['duration_minutes'].sum() / 
                           len(positive_duration_days)) if len(positive_duration_days) > 0 else 0
            
            weekly_data.append({
                'week_range': f"{week_start.strftime('%Y-%m-%d')} 至 {week_end.strftime('%Y-%m-%d')}",
                'week_start': week_start,
                'days_count': days_in_week,
                'total_baah_diamond': week_group['baah_diamond_gain'].sum(),
                'total_net_diamond': week_group['net_diamond_gain'].sum(),
                'avg_baah_diamond': avg_baah_diamond,
                'avg_net_diamond': avg_net_diamond,
                'total_duration': week_group['duration_minutes'].sum(),
                'avg_duration': avg_duration
            })
        
        # 按周开始时间降序排序（最近的在前）
        weekly_data.sort(key=lambda x: x['week_start'], reverse=True)
        return weekly_data
    
    def calculate_monthly_report(self, df):
        """计算月度报告数据"""
        # 确保日期是datetime类型
        df['datetime'] = pd.to_datetime(df['datetime'])
        
        # 按月分组
        df['year_month'] = df['datetime'].dt.to_period('M')
        monthly_data = []
        
        for year_month, month_group in df.groupby('year_month'):
            days_in_month = len(month_group)
            
            # 过滤掉负数数据计算平均值
            positive_baah_days = month_group[month_group['baah_diamond_gain'] > 0]
            positive_net_days = month_group[month_group['net_diamond_gain'] > 0]
            positive_duration_days = month_group[month_group['duration_minutes'] > 0]
            
            avg_baah_diamond = (positive_baah_days['baah_diamond_gain'].sum() / 
                                len(positive_baah_days)) if len(positive_baah_days) > 0 else 0
            avg_net_diamond = (positive_net_days['net_diamond_gain'].sum() / 
                              len(positive_net_days)) if len(positive_net_days) > 0 else 0
            avg_duration = (positive_duration_days['duration_minutes'].sum() / 
                           len(positive_duration_days)) if len(positive_duration_days) > 0 else 0
            
            monthly_data.append({
                'month': year_month.strftime('%Y年%m月'),
                'month_start': year_month.start_time,
                'days_count': days_in_month,
                'total_baah_diamond': month_group['baah_diamond_gain'].sum(),
                'total_net_diamond': month_group['net_diamond_gain'].sum(),
                'avg_baah_diamond': avg_baah_diamond,
                'avg_net_diamond': avg_net_diamond,
                'total_duration': month_group['duration_minutes'].sum(),
                'avg_duration': avg_duration
            })
        
        # 按月份降序排序（最近的在前）
        monthly_data.sort(key=lambda x: x['month_start'], reverse=True)
        return monthly_data
    
    def calculate_diamond_reduction(self, df):
        """计算青辉石减少量数据"""
        # 按日期升序排序
        df_sorted = df.sort_values('datetime')
        reduction_data = []
        
        # 计算每天的开始青辉石减去前一天的结束青辉石
        for i in range(1, len(df_sorted)):
            current_day = df_sorted.iloc[i]
            previous_day = df_sorted.iloc[i-1]
            
            # 计算减少量
            reduction = previous_day['end_diamond'] - current_day['start_diamond']
            
            # 只有当减少量为正时才计入
            if reduction > 0:
                draws = reduction // 120  # 计算对应的抽卡次数
                reduction_data.append({
                    'date': current_day['date'],
                    'start_diamond': current_day['start_diamond'],
                    'previous_end_diamond': previous_day['end_diamond'],
                    'reduction': reduction,
                    'draws': draws,
                    'datetime': current_day['datetime']
                })
        
        # 按日期降序排序（最近的在前）
        reduction_data.sort(key=lambda x: x['datetime'], reverse=True)
        return reduction_data
    
    def process_baah_data(self):
        """处理BAAH资源数据并生成HTML报告"""
        # 读取所有JSON文件
        folder_path = self.config.get('file_paths.resources_folder')
        json_files = glob.glob(os.path.join(folder_path, "*.json"))
        
        if not json_files:
            print("未找到BAAH资源文件")
            return None
        
        # 解析数据
        data = []
        for file_path in json_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_data = json.load(f)
                    
                    # 提取日期作为文件名
                    date_str = os.path.basename(file_path).replace('.json', '')
                    
                    # 解析开始和结束时间
                    start_time = datetime.strptime(file_data['start_time'], '%Y-%m-%d %H:%M:%S')
                    end_time = datetime.strptime(file_data['end_time'], '%Y-%m-%d %H:%M:%S')
                    
                    # 计算任务时长（分钟）
                    duration_minutes = (end_time - start_time).total_seconds() / 60
                    
                    # 解析资源值
                    start_diamond = self.parse_resource_value(file_data['start_resource'].get('diamond', 0))
                    end_diamond = self.parse_resource_value(file_data['end_resource'].get('diamond', 0))
                    
                    start_credit = self.parse_resource_value(file_data['start_resource'].get('credit', 0))
                    end_credit = self.parse_resource_value(file_data['end_resource'].get('credit', 0))
                    
                    data.append({
                        'date': date_str,
                        'datetime': start_time.date(),
                        'start_time': file_data['start_time'],
                        'end_time': file_data['end_time'],
                        'duration_minutes': duration_minutes,
                        'start_diamond': start_diamond,
                        'end_diamond': end_diamond,
                        'start_credit': start_credit,
                        'end_credit': end_credit
                    })
            except Exception as e:
                print(f"处理文件 {file_path} 时出错: {e}")
        
        if not data:
            print("没有有效数据")
            return None
        
        # 按日期升序排序（用于计算净增益）
        data.sort(key=lambda x: x['datetime'])
        
        # 计算两种增益
        for i in range(len(data)):
            # BAAH增益：今天的结束减去今天的开始
            data[i]['baah_diamond_gain'] = data[i]['end_diamond'] - data[i]['start_diamond']
            data[i]['baah_credit_gain'] = data[i]['end_credit'] - data[i]['start_credit']
            
            # 净增益：今天减去上一天结束（第一天没有前一天，净增益等于BAAH增益）
            if i == 0:
                data[i]['net_diamond_gain'] = data[i]['baah_diamond_gain']
                data[i]['net_credit_gain'] = data[i]['baah_credit_gain']
            else:
                data[i]['net_diamond_gain'] = data[i]['end_diamond'] - data[i-1]['end_diamond']
                data[i]['net_credit_gain'] = data[i]['end_credit'] - data[i-1]['end_credit']
        
        # 创建DataFrame
        df = pd.DataFrame(data)
        
        # 移除数据获取上限，使用全部数据
        # one_year_ago = datetime.now().date() - timedelta(days=365)
        # df = df[df['datetime'] >= one_year_ago]
        
        # 按日期降序排序（最近的在前）
        df = df.sort_values('datetime', ascending=False)
        
        # 计算周度和月度报告
        weekly_report = self.calculate_weekly_report(df.copy())
        monthly_report = self.calculate_monthly_report(df.copy())
        
        # 计算青辉石减少量报告
        reduction_report = self.calculate_diamond_reduction(df.copy())
        
        # 生成HTML报告
        html_file_path = self.generate_html_report(df, weekly_report, monthly_report, reduction_report)
        
        return html_file_path
    
    def generate_html_report(self, df, weekly_report, monthly_report, reduction_report):
        """生成HTML报告"""
        # 准备数据用于JavaScript - 使用json.dumps确保正确的JSON格式
        data_json_str = df.to_json(orient='records', date_format='iso')
        weekly_json_str = json.dumps(weekly_report, default=str, ensure_ascii=False)
        monthly_json_str = json.dumps(monthly_report, default=str, ensure_ascii=False)
        reduction_json_str = json.dumps(reduction_report, default=str, ensure_ascii=False)
        
        # 计算总体统计信息（全部数据）
        total_days = len(df)
        
        # 计算当前总抽卡次数（基于最近一天的结束青辉石）
        if len(df) > 0:
            current_total_draws = int(df.iloc[0]['end_diamond'] // 120)  # 使用最近一天的结束青辉石
        else:
            current_total_draws = 0
        
        # 计算青辉石减少总量和抽卡次数
        total_diamond_reduction = sum(item['reduction'] for item in reduction_report)
        total_draws = sum(item['draws'] for item in reduction_report)
        
        # 计算总青辉石获得
        total_baah_diamond_gain = df['baah_diamond_gain'].sum()
        total_net_diamond_gain = df['net_diamond_gain'].sum()
        total_baah_credit_gain = df['baah_credit_gain'].sum()
        total_net_credit_gain = df['net_credit_gain'].sum()
        
        # 过滤掉负数数据计算平均值
        positive_baah_days = df[df['baah_diamond_gain'] > 0]
        positive_net_days = df[df['net_diamond_gain'] > 0]
        positive_credit_days = df[df['baah_credit_gain'] > 0]
        positive_duration_days = df[df['duration_minutes'] > 0]
        
        avg_baah_diamond_per_day = (positive_baah_days['baah_diamond_gain'].sum() / 
                                    len(positive_baah_days)) if len(positive_baah_days) > 0 else 0
        avg_net_diamond_per_day = (positive_net_days['net_diamond_gain'].sum() / 
                                  len(positive_net_days)) if len(positive_net_days) > 0 else 0
        avg_baah_credit_per_day = (positive_credit_days['baah_credit_gain'].sum() / 
                                  len(positive_credit_days)) if len(positive_credit_days) > 0 else 0
        avg_duration_per_day = (positive_duration_days['duration_minutes'].sum() / 
                               len(positive_duration_days)) if len(positive_duration_days) > 0 else 0
        
        # 计算总抽卡次数（基于净青辉石获得）
        total_net_draws = total_net_diamond_gain // 120
        
        # 将信用点数据转换为万为单位（只取整数部分）
        total_baah_credit_wan = int(total_baah_credit_gain / 10000)
        total_net_credit_wan = int(total_net_credit_gain / 10000)
        avg_baah_credit_wan = int(avg_baah_credit_per_day / 10000) if avg_baah_credit_per_day > 0 else 0
        
        # 生成每日数据表格行HTML
        table_rows = []
        for _, row in df.iterrows():
            baah_diamond_class = 'ba-positive' if row['baah_diamond_gain'] >= 0 else 'ba-negative'
            net_diamond_class = 'ba-positive' if row['net_diamond_gain'] >= 0 else 'ba-negative'
            baah_credit_class = 'ba-positive' if row['baah_credit_gain'] >= 0 else 'ba-negative'
            net_credit_class = 'ba-positive' if row['net_credit_gain'] >= 0 else 'ba-negative'
            
            table_rows.append(f"""
            <tr>
                <td>{row['date']}</td>
                <td>{row['start_diamond']}</td>
                <td>{row['end_diamond']}</td>
                <td class="{baah_diamond_class}">{row['baah_diamond_gain']}</td>
                <td class="{net_diamond_class}">{row['net_diamond_gain']}</td>
                <td>{row['start_credit']:,}</td>
                <td>{row['end_credit']:,}</td>
                <td class="{baah_credit_class}">{row['baah_credit_gain']:,}</td>
                <td class="{net_credit_class}">{row['net_credit_gain']:,}</td>
                <td>{row['duration_minutes']:.2f}</td>
            </tr>
            """)
        
        # 生成青辉石减少量表格行HTML
        reduction_rows = []
        for item in reduction_report:
            reduction_rows.append(f"""
            <tr>
                <td>{item['date']}</td>
                <td>{item['previous_end_diamond']:,}</td>
                <td>{item['start_diamond']:,}</td>
                <td class="ba-negative">{item['reduction']:,}</td>
                <td class="ba-warning">{item['draws']:,} 抽</td>
            </tr>
            """)
        
        # 生成周度报告表格行
        weekly_rows = []
        for week in weekly_report:
            baah_class = 'ba-positive' if week['total_baah_diamond'] >= 0 else 'ba-negative'
            net_class = 'ba-positive' if week['total_net_diamond'] >= 0 else 'ba-negative'
            
            weekly_rows.append(f"""
            <tr>
                <td>{week['week_range']}</td>
                <td>{week['days_count']}</td>
                <td class="{baah_class}">{week['total_baah_diamond']}</td>
                <td class="{net_class}">{week['total_net_diamond']}</td>
                <td>{week['avg_baah_diamond']:.2f}</td>
                <td>{week['avg_net_diamond']:.2f}</td>
                <td>{week['total_duration']:.2f}</td>
                <td>{week['avg_duration']:.2f}</td>
            </tr>
            """)
        
        # 生成月度报告表格行
        monthly_rows = []
        for month in monthly_report:
            baah_class = 'ba-positive' if month['total_baah_diamond'] >= 0 else 'ba-negative'
            net_class = 'ba-positive' if month['total_net_diamond'] >= 0 else 'ba-negative'
            
            monthly_rows.append(f"""
            <tr>
                <td>{month['month']}</td>
                <td>{month['days_count']}</td>
                <td class="{baah_class}">{month['total_baah_diamond']}</td>
                <td class="{net_class}">{month['total_net_diamond']}</td>
                <td>{month['avg_baah_diamond']:.2f}</td>
                <td>{month['avg_net_diamond']:.2f}</td>
                <td>{month['total_duration']:.2f}</td>
                <td>{month['avg_duration']:.2f}</td>
            </tr>
            """)
        
        # 创建完整的HTML内容
        # 注意：JSON数据需要被正确转义，使用json.dumps将JSON字符串再次转义为JavaScript字符串
        data_json_js = json.dumps(data_json_str)
        weekly_json_js = json.dumps(weekly_json_str)
        monthly_json_js = json.dumps(monthly_json_str)
        reduction_json_js = json.dumps(reduction_json_str)
        
        # 加载外部HTML模板
        template_path = get_resource_path('templates/report_template.html')
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                html_template = f.read()
            
            # 替换模板变量
            html_content = html_template.replace('{{CURRENT_TIME}}', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            html_content = html_content.replace('{{TOTAL_DAYS}}', str(total_days))
            html_content = html_content.replace('{{TOTAL_BAAH_DIAMOND}}', str(total_baah_diamond_gain))
            html_content = html_content.replace('{{TOTAL_NET_DIAMOND}}', str(total_net_diamond_gain))
            html_content = html_content.replace('{{TOTAL_DRAWS}}', f'{total_net_draws:,}')
            html_content = html_content.replace('{{CURRENT_TOTAL_DRAWS}}', f'{current_total_draws:,}')
            html_content = html_content.replace('{{TOTAL_BAAH_CREDIT}}', str(total_baah_credit_wan))
            html_content = html_content.replace('{{AVG_BAAH_DIAMOND}}', f'{avg_baah_diamond_per_day:.2f}')
            html_content = html_content.replace('{{AVG_NET_DIAMOND}}', f'{avg_net_diamond_per_day:.2f}')
            html_content = html_content.replace('{{AVG_BAAH_CREDIT}}', str(avg_baah_credit_wan))
            html_content = html_content.replace('{{AVG_DURATION}}', f'{avg_duration_per_day:.2f}')
            html_content = html_content.replace('{{TOTAL_REDUCTION}}', f'{total_diamond_reduction:,}')
            html_content = html_content.replace('{{REDUCTION_DRAWS}}', f'{total_draws:,} 抽')
            html_content = html_content.replace('{{REDUCTION_DAYS}}', str(len(reduction_report)))
            html_content = html_content.replace('{{TABLE_ROWS}}', ''.join(table_rows))
            html_content = html_content.replace('{{WEEKLY_ROWS}}', ''.join(weekly_rows))
            html_content = html_content.replace('{{MONTHLY_ROWS}}', ''.join(monthly_rows))
            html_content = html_content.replace('{{REDUCTION_ROWS}}', ''.join(reduction_rows))
            html_content = html_content.replace('{{DATA_JSON_JS}}', data_json_js)
            html_content = html_content.replace('{{WEEKLY_JSON_JS}}', weekly_json_js)
            html_content = html_content.replace('{{MONTHLY_JSON_JS}}', monthly_json_js)
            html_content = html_content.replace('{{REDUCTION_JSON_JS}}', reduction_json_js)
        except Exception as e:
            print(f"加载模板失败: {e}")
            return None
        
        # 保存HTML文件
        output_path = self.config.get('file_paths.html_output')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"报告已生成: {output_path}")
        return output_path
    
    def upload_to_gitee(self, file_path):
        """
        通过Gitee API将文件上传到指定仓库
        """
        owner = self.config.get('gitee.owner')
        repo = self.config.get('gitee.repo')
        branch = self.config.get('gitee.branch')
        access_token = self.config.get('gitee.access_token')
        file_name = "baah_task_report.html"
        
        if not all([owner, repo, access_token]):
            print("Gitee配置不完整，跳过上传")
            return
        
        # 读取文件内容
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"读取文件失败: {e}")
            return
        
        # Base64编码内容
        content_base64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        
        # Gitee API URL
        api_url = f"https://gitee.com/api/v5/repos/{owner}/{repo}/contents/{file_name}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Content-Type": "application/json;charset=UTF-8"
        }
        
        params = {
            "access_token": access_token,
            "ref": branch
        }
        
        try:
            # 检查文件是否存在
            response = requests.get(api_url, headers=headers, params=params)
            
            sha = None
            if response.status_code == 200:
                file_info = response.json()
                if isinstance(file_info, dict):
                    sha = file_info.get('sha')
                    print("文件已存在，将更新")
                elif isinstance(file_info, list):
                    for item in file_info:
                        if isinstance(item, dict) and item.get('name') == file_name:
                            sha = item.get('sha')
                            print("文件已存在，将更新")
                            break
            elif response.status_code == 404:
                print("文件不存在，将创建新文件")
            else:
                print(f"检查文件失败: {response.status_code} - {response.text}")
                return
            
            # 准备上传数据
            data = {
                "access_token": access_token,
                "message": f"更新BAAH任务报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "content": content_base64,
                "branch": branch
            }
            
            if sha:
                data["sha"] = sha
            
            # 上传文件
            upload_response = requests.put(api_url, headers=headers, json=data)
            
            if upload_response.status_code in [200, 201]:
                result = upload_response.json()
                if isinstance(result, dict):
                    content_info = result.get('content', {})
                    if isinstance(content_info, dict):
                        html_url = content_info.get('html_url')
                    else:
                        html_url = result.get('html_url')
                    
                    if html_url:
                        print(f"成功上传文件到Gitee: {html_url}")
                    else:
                        print("成功上传文件到Gitee，但无法获取URL")
                else:
                    print("上传成功")
            else:
                print(f"上传文件失败: {upload_response.status_code} - {upload_response.text}")
                
        except Exception as e:
            print(f"上传到Gitee时出错: {e}")