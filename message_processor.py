# message_processor.py - 靈活打卡訊息處理模組 (完整版 - 支援員工薪資查詢)
import sqlite3
from datetime import datetime, timedelta
import pytz
from linebot.models import TextSendMessage
from models import EmployeeManager
from attendance import AttendanceManager
from network_security import NetworkSecurity
from salary_calculator import SalaryCalculator
from linebot.models import FlexSendMessage
from linebot.models import (
    TextSendMessage, FlexSendMessage, QuickReply, QuickReplyButton, 
    MessageAction, PostbackAction, TemplateSendMessage, CarouselTemplate,
    CarouselColumn, URIAction
)

# 台灣時區設定
TW_TZ = pytz.timezone('Asia/Taipei')

class MessageProcessor:
    """訊息處理器 - 完整版本（支援員工薪資查詢）"""
    
    @staticmethod
    def create_main_menu():
        """創建主選單 Quick Reply"""
        quick_reply = QuickReply(items=[
            QuickReplyButton(action=MessageAction(label="上班打卡", text="上班打卡")),
            QuickReplyButton(action=MessageAction(label="下班打卡", text="下班打卡")),
            QuickReplyButton(action=MessageAction(label="今日狀態", text="今日狀態")),
            QuickReplyButton(action=MessageAction(label="薪資查詢", text="薪資查詢")),
            QuickReplyButton(action=MessageAction(label="個人資訊", text="個人資訊")),
            QuickReplyButton(action=MessageAction(label="查看記錄", text="查看記錄")),
            QuickReplyButton(action=MessageAction(label="網路檢查", text="網路檢查")),
            QuickReplyButton(action=MessageAction(label="幫助", text="幫助"))
        ])
        return quick_reply
    
    @staticmethod
    def create_salary_menu():
        """創建薪資查詢選單 Quick Reply"""
        quick_reply = QuickReply(items=[
            QuickReplyButton(action=MessageAction(label="本月薪資", text="本月薪資")),
            QuickReplyButton(action=MessageAction(label="上月薪資", text="薪資查詢:上月")),
            QuickReplyButton(action=MessageAction(label="指定月份", text="薪資查詢:2024/11")),
            QuickReplyButton(action=MessageAction(label="薪資記錄", text="薪資記錄")),
            QuickReplyButton(action=MessageAction(label="返回主選單", text="選單"))
        ])
        return quick_reply
    
    @staticmethod
    def create_attendance_menu():
        """創建出勤選單 Quick Reply"""
        quick_reply = QuickReply(items=[
            QuickReplyButton(action=MessageAction(label="上班打卡", text="上班打卡")),
            QuickReplyButton(action=MessageAction(label="下班打卡", text="下班打卡")),
            QuickReplyButton(action=MessageAction(label="今日狀態", text="今日狀態")),
            QuickReplyButton(action=MessageAction(label="查看記錄", text="查看記錄")),
            QuickReplyButton(action=MessageAction(label="返回主選單", text="選單"))
        ])
        return quick_reply
    
    @staticmethod
    def process_command(line_user_id, message_text):
        """處理訊息指令 - 完整版本"""
        employee = EmployeeManager.get_employee_by_line_id(line_user_id)
        command = message_text.strip()
        
        # 處理新用戶註冊
        if not employee:
            if command in ['註冊員工', '註冊', '自助註冊']:
                return MessageProcessor.start_self_registration(line_user_id)
            elif command.startswith('姓名:') or command.startswith('姓名：'):
                return MessageProcessor.process_registration_name(line_user_id, command)
            elif command.startswith('部門:') or command.startswith('部門：'):
                return MessageProcessor.process_registration_department(line_user_id, command)
            elif command in ['完成註冊', '確認註冊']:
                return MessageProcessor.complete_registration(line_user_id)
            else:
                return MessageProcessor.handle_new_user()
        
        employee_id = employee['employee_id']
        role = employee['role']
        
        # 主選單和導航
        if command in ['選單', '主選單', '功能選單', 'menu']:
            return MessageProcessor.show_main_menu()
        elif command in ['薪資選單', '薪資功能']:
            return MessageProcessor.show_salary_menu()
        elif command in ['出勤選單', '打卡選單']:
            return MessageProcessor.show_attendance_menu()
        
        # 基本出勤功能
        elif command in ['上班打卡', '上班', '打卡上班']:
            return MessageProcessor.handle_clock_in_with_menu(employee_id)
        elif command in ['下班打卡', '下班', '打卡下班']:
            return MessageProcessor.handle_clock_out_with_menu(employee_id)
        elif command in ['今日狀態', '狀態', '打卡狀態']:
            return MessageProcessor.get_today_status_with_menu(employee_id)
        elif command in ['查看記錄', '記錄', '出勤記錄']:
            return MessageProcessor.get_attendance_records_with_menu(employee_id)
        elif command in ['個人統計', '統計']:
            return MessageProcessor.get_personal_stats_with_menu(employee_id)
        elif command in ['網路檢查', '檢查網路']:
            return MessageProcessor.check_network_status_with_menu()
        
        # 薪資查詢功能 - 支援員工查看自己薪資
        elif command in ['薪資查詢', '薪資計算', '查薪資', '我的薪資']:
            return MessageProcessor.handle_salary_inquiry_enhanced(employee_id, employee['name'])
        elif command in ['本月薪資', '這個月薪資']:
            return MessageProcessor.handle_monthly_salary_enhanced(employee_id, employee['name'])
        elif command in ['薪資記錄', '薪資歷史', '薪資紀錄']:
            return MessageProcessor.show_salary_history_menu(employee_id, employee['name'])
        elif command.startswith('薪資查詢:'):
            return MessageProcessor.handle_specific_month_salary_enhanced(employee_id, employee['name'], command)
        elif command.startswith('薪資記錄:') or command.startswith('薪資紀錄:'):
            return MessageProcessor.handle_salary_history_query(employee_id, employee['name'], command)
        
        # 個人資訊查詢功能
        elif command in ['我的資訊', '個人資訊', '員工資訊']:
            return MessageProcessor.get_employee_info(employee_id)
        
        # 管理員功能
        elif role == 'ADMIN':
            if command in ['員工管理', '員工']:
                return MessageProcessor.show_employee_management()
            elif command in ['出勤統計', '統計管理']:
                return MessageProcessor.show_attendance_stats()
            elif command in ['請假審核', '審核']:
                return MessageProcessor.show_leave_approvals()
            elif command in ['網路設定', '網路管理']:
                return MessageProcessor.show_network_settings()
        
        # 預設回應
        return MessageProcessor.get_help_with_menu(role)
    
    @staticmethod
    def show_main_menu():
        """顯示主選單"""
        text = """🏢 企業出勤管理系統 - 主選單

請選擇您要使用的功能：

📋 快速功能：
• 上班打卡 / 下班打卡
• 今日狀態 / 查看記錄  
• 薪資查詢 / 個人統計
• 網路檢查

💡 點擊下方按鈕快速操作，或直接輸入文字指令"""
        
        return TextSendMessage(
            text=text,
            quick_reply=MessageProcessor.create_main_menu()
        )
    
    @staticmethod
    def show_salary_menu():
        """顯示薪資選單"""
        text = """💰 薪資查詢選單

選擇您要查詢的薪資資訊：

📊 可用功能：
• 本月薪資 - 查看當月薪資明細
• 上月薪資 - 查看上個月薪資  
• 指定月份 - 查看特定月份薪資
• 薪資記錄 - 查看歷史薪資記錄

💡 點擊下方按鈕或輸入指令"""
        
        return TextSendMessage(
            text=text,
            quick_reply=MessageProcessor.create_salary_menu()
        )
    
    @staticmethod
    def show_attendance_menu():
        """顯示出勤選單"""
        text = """📋 出勤管理選單

請選擇出勤相關功能：

🕘 打卡功能：
• 上班打卡 / 下班打卡
• 今日狀態 / 查看記錄

📊 靈活打卡特色：
• 每日上班打卡：2次機會
• 每日下班打卡：2次機會
• 智能狀態檢查

💡 點擊下方按鈕快速操作"""
        
        return TextSendMessage(
            text=text,
            quick_reply=MessageProcessor.create_attendance_menu()
        )
    
    @staticmethod
    def handle_clock_in_with_menu(employee_id):
        """處理上班打卡 - 附加選單"""
        result = AttendanceManager.clock_in(employee_id)
        
        if result['success']:
            status_text = result.get('status_msg', '')
            network_text = f"\n🌐 網路狀態：{result['network_info']}"
            remaining_text = result.get('remaining_msg', '')
            
            response_text = f"✅ {result['message']}\n⏰ 時間：{result['time']}{status_text}{network_text}{remaining_text}\n\n祝您工作順利！"
        else:
            if result.get('network_error'):
                response_text = f"🚫 上班打卡失敗\n\n{result['message']}\n\n💡 請確認網路環境後重試"
            else:
                response_text = f"❌ {result['message']}"
        
        return TextSendMessage(
            text=response_text,
            quick_reply=MessageProcessor.create_attendance_menu()
        )
    
    @staticmethod
    def handle_clock_out_with_menu(employee_id):
        """處理下班打卡 - 附加選單"""
        result = AttendanceManager.clock_out(employee_id)
        
        if result['success']:
            network_text = f"\n🌐 網路狀態：{result['network_info']}"
            hours_text = f"\n⏰ 本次工時：{result['current_session_hours']} 小時"
            total_text = f"\n📊 今日總工時：{result['total_working_hours']} 小時"
            remaining_text = result.get('remaining_msg', '')
            
            response_text = f"✅ {result['message']}\n⏰ 時間：{result['time']}{hours_text}{total_text}{network_text}{remaining_text}\n\n辛苦了！"
        else:
            if result.get('network_error'):
                response_text = f"🚫 下班打卡失敗\n\n{result['message']}\n\n💡 請確認網路環境後重試"
            else:
                response_text = f"❌ {result['message']}"
        
        return TextSendMessage(
            text=response_text,
            quick_reply=MessageProcessor.create_main_menu()
        )
    
    @staticmethod
    def get_today_status_with_menu(employee_id):
        """獲取今日狀態 - 附加選單"""
        status_text = AttendanceManager.get_today_status(employee_id)
        
        return TextSendMessage(
            text=status_text,
            quick_reply=MessageProcessor.create_attendance_menu()
        )
    
    @staticmethod
    def get_attendance_records_with_menu(employee_id):
        """獲取出勤記錄 - 附加選單"""
        records_text = AttendanceManager.get_attendance_records(employee_id)
        
        return TextSendMessage(
            text=records_text,
            quick_reply=MessageProcessor.create_main_menu()
        )
    
    @staticmethod
    def get_personal_stats_with_menu(employee_id):
        """獲取個人統計 - 附加選單"""
        stats_text = AttendanceManager.get_personal_stats(employee_id)
        
        return TextSendMessage(
            text=stats_text,
            quick_reply=MessageProcessor.create_main_menu()
        )
    
    @staticmethod
    def check_network_status_with_menu():
        """檢查網路狀態 - 附加選單"""
        network_result = NetworkSecurity.check_punch_network()
        status_emoji = "✅" if network_result['allowed'] else "❌"
        
        text = f"""🌐 網路狀態檢查

{status_emoji} 當前IP：{network_result['ip']}
📡 網路狀態：{network_result['message']}

{'✅ 可以進行打卡' if network_result['allowed'] else '❌ 無法打卡，請檢查網路連接'}

💡 如有問題請聯繫IT部門"""
        
        return TextSendMessage(
            text=text,
            quick_reply=MessageProcessor.create_main_menu()
        )
    
    @staticmethod
    def handle_salary_inquiry_enhanced(employee_id, employee_name):
        """處理薪資查詢 - 支援員工查看自己薪資"""
        try:
            # 檢查薪資設定
            salary_info = SalaryCalculator.get_employee_salary_info(employee_id)
            
            if salary_info['base_salary'] == 0 and salary_info['hourly_rate'] == 200:
                return TextSendMessage(
                    text=MessageProcessor.show_salary_setup_notice(),
                    quick_reply=MessageProcessor.create_main_menu()
                )
            
            # 計算薪資
            salary_data = SalaryCalculator.calculate_monthly_salary(employee_id)
            
            # 檢查是否有出勤記錄
            if salary_data['work_stats']['work_days'] == 0:
                return TextSendMessage(
                    text=f"查無本月出勤記錄\n\n請確認是否有進行打卡",
                    quick_reply=MessageProcessor.create_salary_menu()
                )
            
            # 創建 Flex Message
            flex_message = SalaryCalculator.create_salary_flex_message(salary_data, employee_name)
            
            # 創建後續選單訊息
            follow_up = TextSendMessage(
                text="💡 您還可以查詢其他月份的薪資，或查看更多功能",
                quick_reply=MessageProcessor.create_salary_menu()
            )
            
            return [flex_message, follow_up]
            
        except Exception as e:
            return TextSendMessage(
                text=f"薪資查詢失敗: {str(e)}\n\n請聯繫管理員確認薪資設定",
                quick_reply=MessageProcessor.create_main_menu()
            )
    
    @staticmethod
    def handle_monthly_salary_enhanced(employee_id, employee_name):
        """處理本月薪資查詢 - 支援員工查看自己薪資"""
        return MessageProcessor.handle_salary_inquiry_enhanced(employee_id, employee_name)
    
    @staticmethod
    def handle_specific_month_salary_enhanced(employee_id, employee_name, command):
        """處理特定月份薪資查詢 - 支援員工查看自己薪資"""
        try:
            month_str = command.split(':', 1)[-1].split('：', 1)[-1].strip()
            
            # 處理 "上月" 指令
            if month_str == '上月':
                last_month = datetime.now(TW_TZ) - timedelta(days=30)
                year = last_month.year
                month = last_month.month
            elif '/' in month_str:
                year_month = month_str.split('/')
                year = int(year_month[0])
                month = int(year_month[1])
            else:
                year = datetime.now(TW_TZ).year
                month = int(month_str)
            
            if month < 1 or month > 12:
                return TextSendMessage(
                    text="月份格式錯誤，請輸入 1-12 之間的數字\n\n範例：\n薪資查詢:2024/03\n薪資查詢:03",
                    quick_reply=MessageProcessor.create_salary_menu()
                )
            
            salary_data = SalaryCalculator.calculate_monthly_salary(employee_id, year, month)
            
            if salary_data['work_stats']['work_days'] == 0:
                return TextSendMessage(
                    text=f"查無 {year}年{month:02d}月 的出勤記錄\n\n請確認該月份是否有打卡記錄",
                    quick_reply=MessageProcessor.create_salary_menu()
                )
            
            flex_message = SalaryCalculator.create_salary_flex_message(salary_data, employee_name)
            
            follow_up = TextSendMessage(
                text="💡 查詢完成！您可以繼續查詢其他月份",
                quick_reply=MessageProcessor.create_salary_menu()
            )
            
            return [flex_message, follow_up]
            
        except ValueError:
            return TextSendMessage(
                text="月份格式錯誤\n\n正確格式：\n• 薪資查詢:2024/03\n• 薪資查詢:03\n• 薪資查詢:上月",
                quick_reply=MessageProcessor.create_salary_menu()
            )
        except Exception as e:
            return TextSendMessage(
                text=f"查詢失敗: {str(e)}",
                quick_reply=MessageProcessor.create_salary_menu()
            )
    
    @staticmethod
    def show_salary_history_menu(employee_id, employee_name):
        """顯示薪資歷史選單 - 支援員工查看自己薪資記錄"""
        quick_reply = QuickReply(items=[
            QuickReplyButton(action=MessageAction(label="近3個月", text="薪資記錄:3個月")),
            QuickReplyButton(action=MessageAction(label="近6個月", text="薪資記錄:6個月")),
            QuickReplyButton(action=MessageAction(label="今年度", text="薪資記錄:今年")),
            QuickReplyButton(action=MessageAction(label="返回薪資選單", text="薪資選單"))
        ])
        
        return TextSendMessage(
            text=f"📋 {employee_name} 的薪資歷史記錄\n\n選擇要查看的時間範圍：",
            quick_reply=quick_reply
        )
    
    @staticmethod
    def handle_salary_history_query(employee_id, employee_name, command):
        """處理薪資歷史查詢"""
        try:
            period = command.split(':', 1)[-1].split('：', 1)[-1].strip()
            
            # 根據期間設定查詢範圍
            now = datetime.now(TW_TZ)
            
            if period == '3個月':
                months_back = 3
                title = "近3個月薪資記錄"
            elif period == '6個月':
                months_back = 6
                title = "近6個月薪資記錄"
            elif period == '今年':
                months_back = now.month
                title = f"{now.year}年薪資記錄"
            else:
                return TextSendMessage(
                    text="時間範圍格式錯誤",
                    quick_reply=MessageProcessor.create_salary_menu()
                )
            
            # 獲取薪資記錄
            records = MessageProcessor._get_salary_history(employee_id, months_back)
            
            if not records:
                return TextSendMessage(
                    text=f"📋 {title}\n\n查無薪資記錄\n可能原因：\n• 尚未進行薪資計算\n• 該期間無出勤記錄\n\n請聯繫管理員確認",
                    quick_reply=MessageProcessor.create_salary_menu()
                )
            
            # 建立薪資記錄摘要
            history_text = f"📋 {employee_name} - {title}\n"
            history_text += "─" * 25 + "\n\n"
            
            total_salary = 0
            for record in records:
                year_month = f"{record['year']}/{record['month']:02d}"
                net_salary = record['net_salary']
                work_days = record['work_days']
                total_hours = record['total_hours']
                
                total_salary += net_salary
                
                history_text += f"📅 {year_month}月\n"
                history_text += f"💰 實發薪資：${net_salary:,.0f}\n"
                history_text += f"📊 出勤：{work_days}天 / {total_hours:.1f}小時\n\n"
            
            # 添加統計摘要
            avg_salary = total_salary / len(records) if records else 0
            history_text += "═" * 25 + "\n"
            history_text += f"📈 統計摘要：\n"
            history_text += f"• 總薪資：${total_salary:,.0f}\n"
            history_text += f"• 平均月薪：${avg_salary:,.0f}\n"
            history_text += f"• 記錄筆數：{len(records)}個月\n"
            
            return TextSendMessage(
                text=history_text,
                quick_reply=MessageProcessor.create_salary_menu()
            )
            
        except Exception as e:
            return TextSendMessage(
                text=f"薪資記錄查詢失敗: {str(e)}",
                quick_reply=MessageProcessor.create_salary_menu()
            )
    
    @staticmethod
    def _get_salary_history(employee_id, months_back):
        """獲取員工薪資記錄"""
        try:
            conn = sqlite3.connect('attendance.db')
            cursor = conn.cursor()
            
            now = datetime.now(TW_TZ)
            current_year = now.year
            current_month = now.month
            
            # 計算查詢的年月範圍
            records = []
            for i in range(months_back):
                month = current_month - i
                year = current_year
                
                while month <= 0:
                    month += 12
                    year -= 1
                
                cursor.execute('''
                    SELECT year, month, work_days, total_hours, 
                           gross_salary, net_salary, overtime_hours, late_count
                    FROM salary_records 
                    WHERE employee_id = ? AND year = ? AND month = ?
                    ORDER BY year DESC, month DESC
                ''', (employee_id, year, month))
                
                record = cursor.fetchone()
                if record:
                    records.append({
                        'year': record[0],
                        'month': record[1],
                        'work_days': record[2],
                        'total_hours': record[3],
                        'gross_salary': record[4],
                        'net_salary': record[5],
                        'overtime_hours': record[6],
                        'late_count': record[7]
                    })
            
            conn.close()
            return records
            
        except Exception as e:
            print(f"獲取薪資記錄失敗: {e}")
            return []
    
    @staticmethod
    def get_employee_info(employee_id):
        """獲取員工個人資訊"""
        try:
            conn = sqlite3.connect('attendance.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT employee_id, name, department, position, role, hire_date, email
                FROM employees WHERE employee_id = ?
            ''', (employee_id,))
            
            employee = cursor.fetchone()
            conn.close()
            
            if employee:
                emp_id, name, department, position, role, hire_date, email = employee
                
                info_text = f"""👤 個人資訊

員工編號：{emp_id}
姓名：{name}
部門：{department or '未設定'}
職位：{position or '未設定'}
權限：{'管理員' if role == 'ADMIN' else '一般員工'}
電子郵件：{email or '未設定'}
到職日期：{hire_date or '未設定'}

💰 薪資功能：
• 輸入「薪資查詢」查看本月薪資
• 輸入「薪資記錄」查看歷史記錄

💡 輸入「選單」查看更多功能"""
                
                return TextSendMessage(
                    text=info_text,
                    quick_reply=MessageProcessor.create_main_menu()
                )
            else:
                return TextSendMessage(text="查無員工資訊")
                
        except Exception as e:
            return TextSendMessage(text=f"查詢失敗：{str(e)}")
    
    @staticmethod
    def get_help_with_menu(role):
        """獲取幫助訊息 - 支援員工薪資查詢功能"""
        base_help = """🤖 企業出勤管理系統

👤 基本功能：
• 上班打卡 / 下班打卡
• 今日狀態 / 查看記錄
• 薪資查詢 / 個人資訊
• 網路檢查

💰 薪資功能：
• 本月薪資 / 指定月份查詢
• 薪資歷史記錄

ℹ️ 個人資訊：
• 查看員工編號、姓名、部門
• 查看權限和到職日期

📄 靈活打卡特色：
• 每日上班/下班打卡各2次機會
• 智能狀態檢查防重複

💡 點擊下方按鈕快速操作"""
        
        if role == 'ADMIN':
            admin_help = """

👨‍💼 管理功能：
• 員工管理 / 出勤統計
• 薪資管理 / 網路設定

🔗 管理後台：http://localhost:5008/admin"""
            base_help += admin_help
        else:
            employee_help = """

💡 常用指令：
• 輸入「個人資訊」查看基本資料
• 輸入「薪資查詢」查看本月薪資
• 輸入「薪資記錄」查看歷史記錄
• 輸入「薪資查詢:2024/03」查看特定月份

📞 如有薪資問題請聯繫管理部門"""
            base_help += employee_help
        
        return TextSendMessage(
            text=base_help,
            quick_reply=MessageProcessor.create_main_menu()
        )
    
    @staticmethod
    def show_salary_setup_notice():
        """顯示薪資設定提醒"""
        return """💰 薪資查詢功能

⚠️ 尚未設定薪資資料

您的薪資設定可能尚未完成，請聯繫管理員進行以下設定：
• 基本薪資（月薪制）
• 時薪標準  
• 加班費標準
• 獎金設定

📞 設定完成後即可查詢薪資明細

💡 可用功能：
• 本月薪資 - 查看當月薪資試算
• 薪資查詢:2024/03 - 查看特定月份
• 薪資記錄 - 查看歷史薪資記錄

如有疑問請聯繫人事或管理部門"""
    
    @staticmethod
    def create_text_message(content):
        """創建訊息 - 支援多種格式"""
        if isinstance(content, (FlexSendMessage, list)):
            return content
        elif isinstance(content, TextSendMessage):
            return content
        else:
            return TextSendMessage(text=str(content))
    
    # === 自助註冊相關功能 ===
    @staticmethod
    def start_self_registration(line_user_id):
        """開始自助註冊流程"""
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        # 清除舊的註冊資料
        cursor.execute('DELETE FROM pending_registrations WHERE line_user_id = ?', (line_user_id,))
        
        # 創建新的註冊記錄
        cursor.execute('''
            INSERT INTO pending_registrations (line_user_id, step) VALUES (?, 1)
        ''', (line_user_id,))
        
        conn.commit()
        conn.close()
        
        return """✅ 開始自助註冊流程

步驟 1/3：請輸入您的姓名
格式：姓名:張小明

例如：
姓名:張小明
或
姓名：李小華"""
    
    @staticmethod
    def process_registration_name(line_user_id, command):
        """處理註冊姓名"""
        # 提取姓名
        name = command.split(':', 1)[-1].split('：', 1)[-1].strip()
        
        if not name or len(name) < 2:
            return "❌ 姓名格式不正確，請重新輸入\n格式：姓名:您的姓名"
        
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        # 更新註冊資料
        cursor.execute('''
            UPDATE pending_registrations 
            SET name = ?, step = 2 
            WHERE line_user_id = ?
        ''', (name, line_user_id))
        
        conn.commit()
        conn.close()
        
        return f"""✅ 姓名已記錄：{name}

步驟 2/3：請輸入您的部門
格式：部門:IT部

例如：
部門:IT部
部門:人事部
部門:業務部"""
    
    @staticmethod
    def process_registration_department(line_user_id, command):
        """處理註冊部門"""
        # 提取部門
        department = command.split(':', 1)[-1].split('：', 1)[-1].strip()
        
        if not department:
            return "❌ 部門格式不正確，請重新輸入\n格式：部門:您的部門"
        
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        # 檢查是否有註冊記錄
        cursor.execute('SELECT name FROM pending_registrations WHERE line_user_id = ?', (line_user_id,))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return "❌ 請先輸入姓名\n格式：姓名:您的姓名"
        
        # 更新註冊資料
        cursor.execute('''
            UPDATE pending_registrations 
            SET department = ?, step = 3 
            WHERE line_user_id = ?
        ''', (department, line_user_id))
        
        conn.commit()
        conn.close()
        
        name = result[0]
        
        return f"""✅ 部門已記錄：{department}

步驟 3/3：確認註冊資訊
姓名：{name}
部門：{department}

確認無誤請輸入「完成註冊」
如需修改請重新開始「註冊員工」"""
    
    @staticmethod
    def complete_registration(line_user_id):
        """完成註冊"""
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        # 取得註冊資料
        cursor.execute('''
            SELECT name, department FROM pending_registrations 
            WHERE line_user_id = ? AND step = 3
        ''', (line_user_id,))
        
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return "❌ 註冊資料不完整，請重新開始註冊\n輸入「註冊員工」重新開始"
        
        name, department = result
        
        # 創建員工帳號
        employee_id = EmployeeManager.create_employee({
            'line_user_id': line_user_id,
            'name': name,
            'department': department,
            'role': 'EMPLOYEE'
        })
        
        # 清除註冊資料
        cursor.execute('DELETE FROM pending_registrations WHERE line_user_id = ?', (line_user_id,))
        
        conn.commit()
        conn.close()
        
        return f"""🎉 註冊完成！

員工編號：{employee_id}
姓名：{name}
部門：{department}
權限：一般員工

現在您可以開始使用靈活打卡功能了！

📄 靈活打卡特色：
• 每日上班打卡：2次機會
• 每日下班打卡：2次機會
• 智能狀態檢查：防止重複打卡

💡 基本操作：
🌅 上班時輸入「上班打卡」
🌙 下班時輸入「下班打卡」
📊 查看狀態輸入「今日狀態」
📋 查看記錄輸入「查看記錄」

💰 薪資查詢：
💸 輸入「薪資查詢」查看本月薪資
📈 輸入「薪資記錄」查看歷史記錄
🔍 輸入「薪資查詢:2024/03」查看特定月份

🌐 請在公司網路環境內進行打卡
💡 輸入「幫助」查看完整功能說明"""

    @staticmethod
    def handle_new_user():
        """處理新用戶"""
        return """👋 歡迎使用企業出勤管理系統！

您尚未註冊，請開始自助註冊流程：

🔧 註冊步驟：
1. 輸入「註冊員工」開始註冊
2. 按照提示輸入姓名和部門
3. 完成後即可使用打卡功能

💡 輸入「註冊員工」立即開始"""

    @staticmethod
    def show_employee_management():
        """顯示員工管理功能"""
        return TextSendMessage(
            text="👨‍💼 員工管理功能\n\n請使用管理後台進行詳細操作：\nhttp://localhost:5008/admin",
            quick_reply=MessageProcessor.create_main_menu()
        )

    @staticmethod
    def show_attendance_stats():
        """顯示出勤統計功能"""
        return TextSendMessage(
            text="📊 出勤統計功能\n\n請使用管理後台查看詳細報表：\nhttp://localhost:5008/admin",
            quick_reply=MessageProcessor.create_main_menu()
        )

    @staticmethod
    def show_leave_approvals():
        """顯示請假審核功能"""
        return TextSendMessage(
            text="📝 請假審核功能\n\n請使用管理後台進行審核：\nhttp://localhost:5008/admin",
            quick_reply=MessageProcessor.create_main_menu()
        )

    @staticmethod
    def show_network_settings():
        """顯示網路設定功能"""
        return TextSendMessage(
            text="🌐 網路設定功能\n\n請使用管理後台進行設定：\nhttp://localhost:5008/admin",
            quick_reply=MessageProcessor.create_main_menu()
        )

    @staticmethod
    def get_welcome_message():
        """獲取歡迎訊息"""
        return """🎉 歡迎使用企業出勤管理系統！

這是一個功能完整的智能打卡系統

📄 靈活打卡特色：
• 每日上班打卡：2次機會
• 每日下班打卡：2次機會
• 智能狀態檢查

💰 薪資查詢功能：
• 查看個人薪資明細
• 查詢歷史薪資記錄
• 支援多月份查詢

💡 開始使用：
• 新用戶請輸入「註冊員工」
• 舊用戶直接輸入「上班打卡」
• 查看功能請輸入「幫助」

祝您使用愉快！"""