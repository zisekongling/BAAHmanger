import imaplib
import email
from email.header import decode_header
import re
import ast
from datetime import datetime
import json
import os
from config_manager import ConfigManager

class EmailProcessor:
    def __init__(self):
        self.config = ConfigManager()
    
    def decode_subject(self, encoded_subject):
        """解码邮件主题"""
        decoded = decode_header(encoded_subject)
        subject = ''
        for part, encoding in decoded:
            if isinstance(part, bytes):
                subject += part.decode(encoding or 'utf-8')
            else:
                subject += part
        return subject
    
    def extract_dict_from_line(self, line):
        """从文本行中提取字典数据"""
        match = re.search(r'(\{.*\})', line)
        if match:
            try:
                return ast.literal_eval(match.group(1))
            except (ValueError, SyntaxError):
                print(f"无法解析字典: {line}")
        return None
    
    def extract_time_from_line(self, line, prefix):
        """从文本行中提取时间信息"""
        if prefix in line:
            time_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
            if time_match:
                return time_match.group(1)
        return None
    
    def connect_to_email(self):
        """连接到邮箱服务器"""
        try:
            mail = imaplib.IMAP4_SSL(self.config.get('email.imap_server'))
            mail.login(
                self.config.get('email.email_account'),
                self.config.get('email.authorization_code')
            )
            mail.select('inbox')
            return mail
        except Exception as e:
            print(f"连接邮箱失败: {e}")
            return None
    
    def search_baah_emails(self, mail):
        """搜索BAAH邮件"""
        today = datetime.now().strftime('%d-%b-%Y')
        result, data = mail.search(None, f'SINCE "{today}"')
        
        if result != 'OK' or not data[0]:
            print("未找到今天的邮件")
            return []
        
        email_ids = data[0].split()
        print(f"找到 {len(email_ids)} 封今天邮件")
        
        baah_end_emails = []
        for email_id in email_ids:
            result, header_data = mail.fetch(email_id, '(BODY.PEEK[HEADER.FIELDS (SUBJECT)])')
            if result == 'OK':
                msg = email.message_from_bytes(header_data[0][1])
                subject = self.decode_subject(msg['Subject'])
                
                if "BAAH结束" in subject:
                    baah_end_emails.append(email_id)
                    print(f"找到BAAH结束邮件: {subject}")
        
        return baah_end_emails
    
    def get_email_body(self, mail, email_id):
        """获取邮件正文"""
        result, data = mail.fetch(email_id, '(RFC822)')
        if result != 'OK':
            print("获取邮件内容失败")
            return None
        
        raw_email = data[0][1]
        msg = email.message_from_bytes(raw_email)
        
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    body = part.get_payload(decode=True).decode()
                    break
        else:
            body = msg.get_payload(decode=True).decode()
        
        return body
    
    def process_success_email(self, body):
        """处理成功邮件并提取资源信息"""
        start_time = None
        start_resource = None
        end_time = None
        end_resource = None
        
        for line in body.split('\n'):
            if '任务开始时间:' in line:
                start_time = self.extract_time_from_line(line, '任务开始时间:')
            elif '开始时资源:' in line:
                start_resource = self.extract_dict_from_line(line)
            elif '任务结束时间:' in line:
                end_time = self.extract_time_from_line(line, '任务结束时间:')
            elif '结束时资源:' in line:
                end_resource = self.extract_dict_from_line(line)
        
        if start_time and start_resource and end_time and end_resource:
            resource_data = {
                "start_time": start_time,
                "start_resource": start_resource,
                "end_time": end_time,
                "end_resource": end_resource
            }
            
            folder_name = self.config.get('file_paths.resources_folder')
            if not os.path.exists(folder_name):
                os.makedirs(folder_name)
            
            today_date = datetime.now().strftime('%Y-%m-%d')
            filename = os.path.join(folder_name, f"{today_date}.json")
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(resource_data, f, ensure_ascii=False, indent=4)
            
            print(f"资源已保存到: {filename}")
            return True
        else:
            print("未找到完整的资源信息")
            return False
    
    def process_baah_email(self):
        """处理BAAH邮件的主函数"""
        mail = self.connect_to_email()
        if not mail:
            return False
        
        try:
            baah_emails = self.search_baah_emails(mail)
            if not baah_emails:
                print("未找到今天的BAAH结束邮件")
                return False
            
            latest_email_id = baah_emails[-1]
            body = self.get_email_body(mail, latest_email_id)
            
            if body:
                success = self.process_success_email(body)
                return success
            else:
                return False
                
        except Exception as e:
            print(f"处理邮件时出错: {e}")
            return False
        finally:
            try:
                mail.logout()
            except:
                pass