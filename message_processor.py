# message_processor.py - 完整出勤管理訊息處理模組 (支援請假功能)
import sqlite3
from datetime import datetime, timedelta
import pytz
import re
from linebot.models import TextSendMessage, FlexSendMessage, QuickReply, QuickReplyButton, MessageAction
from models import EmployeeManager
from attendance import AttendanceManager
from network_security import NetworkSecurity
from salary_calculator import SalaryCalculator
from overtime_manager import OvertimeManager
from leave_manager import LeaveManager, LEAVE_TYPES

# 台灣時區設定
TW_TZ = pytz.timezone('Asia/Taipei')

class MessageProcessor:
    """訊息處理器 - 完整版本（支援員工薪資查詢、加班申報和請假功能）"""
    
    @staticmethod
    def create_main_menu():
        """創建主選單 Quick Reply"""
        quick_reply = QuickReply(items=[
            QuickReplyButton(action=MessageAction(label="上班打卡", text="上班打卡")),
            QuickReplyButton(action=MessageAction(label="下班打卡", text="下班打卡")),
            QuickReplyButton(action=MessageAction(label="今日狀態", text="今日狀態")),
            QuickReplyButton(action=MessageAction(label="薪資查詢", text="薪資查詢")),
            QuickReplyButton(action=MessageAction(label="加班申報", text="加班申報")),
            QuickReplyButton(action=MessageAction(label="請假申請", text="請假申請")),
            QuickReplyButton(action=MessageAction(label="個人資訊", text="個人資訊")),
            QuickReplyButton(action=MessageAction(label="幫助", text="幫助"))
        ])
        return quick_reply
    
    @staticmethod
    def create_leave_menu():
        """創建請假申請選單 Quick Reply"""
        quick_reply = QuickReply(items=[
            QuickReplyButton(action=MessageAction(label="申請請假", text="申請請假")),
            QuickReplyButton(action=MessageAction(label="我的請假", text="我的請假申請")),
            QuickReplyButton(action=MessageAction(label="請假記錄", text="請假記錄")),
            QuickReplyButton(action=MessageAction(label="請假額度", text="請假額度")),
            QuickReplyButton(action=MessageAction(label="取消申請", text="取消請假申請")),
            QuickReplyButton(action=MessageAction(label="返回主選單", text="選單"))
        ])
        return quick_reply
    
    @staticmethod
    def create_leave_type_menu():
        """創建請假類型選單"""
        quick_reply = QuickReply(items=[
            QuickReplyButton(action=MessageAction(label="🏖️ 特休假", text="請假類型:annual")),
            QuickReplyButton(action=MessageAction(label="🏥 病假", text="請假類型:sick")),
            QuickReplyButton(action=MessageAction(label="📋 事假", text="請假類型:personal")),
            QuickReplyButton(action=MessageAction(label="🕯️ 喪假", text="請假類型:funeral")),
            QuickReplyButton(action=MessageAction(label="👶 產假", text="請假類型:maternity")),
            QuickReplyButton(action=MessageAction(label="👨‍👶 陪產假", text="請假類型:paternity")),
            QuickReplyButton(action=MessageAction(label="🏛️ 公假", text="請假類型:official")),
            QuickReplyButton(action=MessageAction(label="💒 婚假", text="請假類型:marriage"))
        ])
        return quick_reply
    
    @staticmethod
    def create_overtime_menu():
        """創建加班申報選單 Quick Reply"""
        quick_reply = QuickReply(items=[
            QuickReplyButton(action=MessageAction(label="申報加班", text="申報加班")),
            QuickReplyButton(action=MessageAction(label="我的申請", text="我的加班申請")),
            QuickReplyButton(action=MessageAction(label="加班摘要", text="加班摘要")),
            QuickReplyButton(action=MessageAction(label="取消申請", text="取消加班申請")),
            QuickReplyButton(action=MessageAction(label="返回主選單", text="選單"))
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
        elif command in ['加班選單', '加班功能']:
            return MessageProcessor.show_overtime_menu()
        elif command in ['請假選單', '請假功能', '請假申請']:
            return MessageProcessor.show_leave_menu()
        
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
        
        # 加班申報功能
        elif command in ['加班申報', '申報加班', '加班申請']:
            return MessageProcessor.show_overtime_apply_form(employee_id)
        elif command in ['我的加班申請', '我的申請', '加班申請狀態']:
            return MessageProcessor.show_my_overtime_requests(employee_id)
        elif command in ['加班摘要', '加班統計']:
            return MessageProcessor.show_overtime_summary(employee_id)
        elif command in ['取消加班申請', '取消申請']:
            return MessageProcessor.show_cancel_overtime_form(employee_id)
        elif command.startswith('加班:'):
            return MessageProcessor.process_overtime_application(employee_id, command)
        elif command.startswith('取消申請:') or command.startswith('取消申請：'):
            return MessageProcessor.process_cancel_overtime(employee_id, command)
        
        # === 新增請假功能處理 ===
        elif command in ['請假申請', '申請請假', '請假']:
            return MessageProcessor.show_leave_application_form(employee_id)
        elif command in ['我的請假申請', '我的請假', '請假狀態']:
            return MessageProcessor.show_my_leave_requests(employee_id)
        elif command in ['請假記錄', '請假歷史']:
            return MessageProcessor.show_leave_history(employee_id)
        elif command in ['請假額度', '剩餘假期']:
            return MessageProcessor.show_leave_quotas(employee_id)
        elif command in ['取消請假申請', '取消請假']:
            return MessageProcessor.show_cancel_leave_form(employee_id)
        elif command.startswith('請假類型:'):
            return MessageProcessor.process_leave_type_selection(employee_id, command)
        elif command.startswith('請假:'):
            return MessageProcessor.process_leave_application(employee_id, command)
        elif command.startswith('取消請假:') or command.startswith('取消請假：'):
            return MessageProcessor.process_cancel_leave(employee_id, command)
        
        # 個人資訊查詢功能
        elif command in ['我的資訊', '個人資訊', '員工資訊']:
            return MessageProcessor.get_employee_info(employee_id)
        
        # 管理員功能
        elif role == 'ADMIN':
            if command in ['員工管理', '員工']:
                return MessageProcessor.show_employee_management()
            elif command in ['出勤統計', '統計管理']:
                return MessageProcessor.show_attendance_stats()
            elif command in ['加班審核', '審核加班']:
                return MessageProcessor.show_overtime_approvals()
            elif command in ['請假審核', '審核請假']:
                return MessageProcessor.show_leave_approvals()
            elif command in ['網路設定', '網路管理']:
                return MessageProcessor.show_network_settings()
        
        # 默認回應
        return MessageProcessor.get_help_with_menu(role)
    
    # === 請假功能方法 ===
    @staticmethod
    def show_leave_menu():
        """顯示請假申請選單"""
        text = """🏖️ 請假申請系統

選擇您要使用的請假功能：

📝 可用功能：
• 申請請假 - 提交新的請假申請
• 我的請假 - 查看申請狀態
• 請假記錄 - 查看歷史記錄
• 請假額度 - 查看剩餘假期
• 取消申請 - 取消待審申請

💡 點擊下方按鈕或輸入指令"""
        
        return TextSendMessage(
            text=text,
            quick_reply=MessageProcessor.create_leave_menu()
        )
    
    @staticmethod
    def show_leave_application_form(employee_id):
        """顯示請假申請表單"""
        text = """📝 請假申請

請先選擇您要申請的假別類型：

🏖️ 特休假 - 年度特休假期
🏥 病假 - 因病休養（超過3天需證明）
📋 事假 - 個人事務假期
🕯️ 喪假 - 直系親屬喪事
👶 產假 - 產前產後假期
👨‍👶 陪產假 - 配偶生產陪產
🏛️ 公假 - 公務出差訓練
💒 婚假 - 結婚假期

請點擊下方按鈕選擇假別類型"""
        
        return TextSendMessage(
            text=text,
            quick_reply=MessageProcessor.create_leave_type_menu()
        )
    
    @staticmethod
    def process_leave_type_selection(employee_id, command):
        """處理請假類型選擇"""
        leave_type = command.split(':', 1)[1].strip()
        
        if leave_type not in LEAVE_TYPES:
            return TextSendMessage(
                text="❌ 無效的請假類型，請重新選擇",
                quick_reply=MessageProcessor.create_leave_type_menu()
            )
        
        leave_info = LEAVE_TYPES[leave_type]
        
        # 保存用戶選擇的假別到臨時狀態（可以使用資料庫或緩存）
        # 這裡簡化處理，直接返回申請格式說明
        
        text = f"""📝 {leave_info['emoji']} {leave_info['name']} 申請表單

{leave_info['description']}

申請格式：
請假:假別,開始日期,結束日期,開始時間,結束時間,請假原因

範例：
• 請假:{leave_type},2024-01-15,2024-01-15,09:00,18:00,身體不適需要休息
• 請假:{leave_type},2024-01-16,2024-01-17,09:00,18:00,處理個人事務
• 請假:{leave_type},明天,明天,14:00,18:00,下午看醫生

📋 注意事項：
• 日期格式：YYYY-MM-DD 或 今天/明天/後天
• 時間格式：HH:MM（24小時制）
• 單次申請最多{leave_info['max_days_per_request']}天
• 請假原因請簡要說明"""

        if leave_info['requires_proof']:
            text += "\n⚠️ 此假別需要相關證明文件"
        
        return TextSendMessage(
            text=text,
            quick_reply=MessageProcessor.create_leave_menu()
        )
    
    @staticmethod
    def process_leave_application(employee_id, command):
        """處理請假申請"""
        try:
            # 解析指令：請假:假別,開始日期,結束日期,開始時間,結束時間,請假原因
            parts = command.split(':', 1)[1].split(',')
            
            if len(parts) < 3:
                return TextSendMessage(
                    text="❌ 格式錯誤！\n\n正確格式：\n請假:假別,開始日期,結束日期,開始時間,結束時間,請假原因\n\n範例：\n請假:sick,2024-01-15,2024-01-15,09:00,18:00,身體不適",
                    quick_reply=MessageProcessor.create_leave_menu()
                )
            
            leave_type = parts[0].strip()
            start_date = parts[1].strip()
            end_date = parts[2].strip() if len(parts) > 2 else start_date
            start_time = parts[3].strip() if len(parts) > 3 else '09:00'
            end_time = parts[4].strip() if len(parts) > 4 else '18:00'
            reason = parts[5].strip() if len(parts) > 5 else '個人事務'
            
            # 處理日期
            start_date = MessageProcessor.parse_date_string(start_date)
            end_date = MessageProcessor.parse_date_string(end_date)
            
            if not start_date or not end_date:
                return TextSendMessage(
                    text="❌ 日期格式錯誤！\n\n支援格式：\n• 2024-01-15\n• 明天\n• 今天",
                    quick_reply=MessageProcessor.create_leave_menu()
                )
            
            # 驗證時間格式
            if not re.match(r'^\d{1,2}:\d{2}$', start_time) or not re.match(r'^\d{1,2}:\d{2}$', end_time):
                return TextSendMessage(
                    text="❌ 時間格式錯誤！\n\n正確格式：HH:MM\n範例：09:00, 14:30",
                    quick_reply=MessageProcessor.create_leave_menu()
                )
            
            # 提交申請
            leave_data = {
                'leave_type': leave_type,
                'start_date': start_date,
                'end_date': end_date,
                'start_time': start_time,
                'end_time': end_time,
                'reason': reason
            }
            
            result = LeaveManager.submit_leave_request(employee_id, leave_data)
            
            if result['success']:
                response_text = f"✅ {result['message']}\n\n📋 申請詳情：\n日期：{start_date} - {end_date}\n時間：{start_time} - {end_time}\n天數：{result['total_days']}天\n原因：{reason}\n\n⏳ 請等待管理員審核"
            else:
                response_text = f"❌ {result['message']}"
            
            return TextSendMessage(
                text=response_text,
                quick_reply=MessageProcessor.create_leave_menu()
            )
            
        except Exception as e:
            return TextSendMessage(
                text=f"❌ 申請處理失敗：{str(e)}\n\n請檢查格式後重試",
                quick_reply=MessageProcessor.create_leave_menu()
            )
    
    @staticmethod
    def show_my_leave_requests(employee_id):
        """顯示我的請假申請"""
        try:
            requests = LeaveManager.get_leave_requests(employee_id=employee_id, limit=10)
            
            if not requests:
                return TextSendMessage(
                    text="📋 我的請假申請\n\n目前沒有請假申請記錄\n\n💡 輸入「申請請假」開始申請",
                    quick_reply=MessageProcessor.create_leave_menu()
                )
            
            text = "📋 我的請假申請記錄\n" + "─" * 25 + "\n\n"
            
            for req in requests:
                status_info = f"{req['status_emoji']} {req['status_name']}"
                leave_info = f"{req['leave_type_emoji']} {req['leave_type_name']}"
                
                text += f"🆔 申請 #{req['id']}\n"
                text += f"📅 {req['start_date']} - {req['end_date']}\n"
                text += f"⏰ {req['start_time']} - {req['end_time']} ({req['total_days']}天)\n"
                text += f"🏷️ {leave_info}\n"
                text += f"📊 {status_info}\n"
                text += f"📝 {req['reason']}\n"
                
                if req['status'] == 'rejected' and req['rejected_reason']:
                    text += f"❌ 拒絕原因：{req['rejected_reason']}\n"
                
                text += "\n"
            
            text += "💡 如需取消待審申請，輸入「取消請假申請」"
            
            return TextSendMessage(
                text=text,
                quick_reply=MessageProcessor.create_leave_menu()
            )
            
        except Exception as e:
            return TextSendMessage(
                text=f"❌ 查詢失敗：{str(e)}",
                quick_reply=MessageProcessor.create_leave_menu()
            )
    
    @staticmethod
    def show_leave_history(employee_id):
        """顯示請假歷史記錄"""
        try:
            requests = LeaveManager.get_leave_requests(employee_id=employee_id, limit=20)
            
            if not requests:
                return TextSendMessage(
                    text="📋 請假歷史記錄\n\n暫無請假記錄",
                    quick_reply=MessageProcessor.create_leave_menu()
                )
            
            # 按年月分組統計
            monthly_stats = {}
            total_approved_days = 0
            
            for req in requests:
                if req['status'] == 'approved':
                    total_approved_days += req['total_days']
                    
                month_key = req['start_date'][:7]  # YYYY-MM
                if month_key not in monthly_stats:
                    monthly_stats[month_key] = {'count': 0, 'days': 0}
                if req['status'] == 'approved':
                    monthly_stats[month_key]['count'] += 1
                    monthly_stats[month_key]['days'] += req['total_days']
            
            text = f"📋 請假歷史記錄\n" + "─" * 25 + "\n\n"
            text += f"📊 統計摘要：\n"
            text += f"• 總申請數：{len(requests)}筆\n"
            text += f"• 已批准天數：{total_approved_days:.1f}天\n\n"
            
            # 顯示最近的申請
            text += f"📝 最近申請記錄：\n\n"
            for req in requests[:5]:  # 只顯示最近5筆
                status_info = f"{req['status_emoji']} {req['status_name']}"
                leave_info = f"{req['leave_type_emoji']} {req['leave_type_name']}"
                
                text += f"{req['start_date']} {leave_info} {req['total_days']}天 {status_info}\n"
            
            if len(requests) > 5:
                text += f"\n還有 {len(requests) - 5} 筆記錄..."
            
            return TextSendMessage(
                text=text,
                quick_reply=MessageProcessor.create_leave_menu()
            )
            
        except Exception as e:
            return TextSendMessage(
                text=f"❌ 查詢失敗：{str(e)}",
                quick_reply=MessageProcessor.create_leave_menu()
            )
    
    @staticmethod
    def show_leave_quotas(employee_id):
        """顯示請假額度"""
        try:
            summary = LeaveManager.get_employee_leave_summary(employee_id)
            
            text = f"📊 請假額度查詢 - {summary['year']}年\n"
            text += "─" * 25 + "\n\n"
            
            # 顯示有額度限制的假別
            quota_types = ['annual', 'compensatory']
            for leave_type in quota_types:
                if leave_type in summary['quotas']:
                    quota = summary['quotas'][leave_type]
                    type_info = LEAVE_TYPES[leave_type]
                    
                    text += f"{type_info['emoji']} {type_info['name']}\n"
                    text += f"• 分配額度：{quota['allocated']}天\n"
                    text += f"• 已使用：{quota['used']}天\n"
                    text += f"• 剩餘額度：{quota['remaining']}天\n\n"
            
            # 顯示本年度各類型使用統計
            text += f"📈 {summary['year']}年使用統計：\n"
            for leave_type, stats in summary['stats'].items():
                if stats['approved']['days'] > 0:
                    type_info = LEAVE_TYPES.get(leave_type, {'name': leave_type, 'emoji': '📋'})
                    text += f"{type_info['emoji']} {type_info['name']}：{stats['approved']['days']}天\n"
            
            # 本月統計
            text += f"\n🗓️ {summary['month']}使用：{summary['this_month']['days']}天\n"
            
            text += f"\n💡 提醒：\n"
            text += f"• 特休假需事先申請\n"
            text += f"• 病假超過3天需診斷證明\n"
            text += f"• 補休來自加班時數累積"
            
            return TextSendMessage(
                text=text,
                quick_reply=MessageProcessor.create_leave_menu()
            )
            
        except Exception as e:
            return TextSendMessage(
                text=f"❌ 查詢額度失敗：{str(e)}",
                quick_reply=MessageProcessor.create_leave_menu()
            )
    
    @staticmethod
    def show_cancel_leave_form(employee_id):
        """顯示取消請假申請表單"""
        try:
            # 獲取待審核和已批准的申請
            pending_requests = LeaveManager.get_leave_requests(
                employee_id=employee_id, 
                status='pending', 
                limit=5
            )
            
            approved_requests = LeaveManager.get_leave_requests(
                employee_id=employee_id, 
                status='approved', 
                limit=3
            )
            
            all_requests = pending_requests + approved_requests
            
            if not all_requests:
                return TextSendMessage(
                    text="📋 取消請假申請\n\n目前沒有可以取消的申請",
                    quick_reply=MessageProcessor.create_leave_menu()
                )
            
            text = "📋 可取消的請假申請\n"
            text += "─" * 25 + "\n\n"
            
            for req in all_requests:
                status_info = f"{req['status_emoji']} {req['status_name']}"
                leave_info = f"{req['leave_type_emoji']} {req['leave_type_name']}"
                
                text += f"🆔 #{req['id']} | {req['start_date']}\n"
                text += f"⏰ {req['start_time']}-{req['end_time']} ({req['total_days']}天)\n"
                text += f"🏷️ {leave_info} | {status_info}\n"
                text += f"📝 {req['reason']}\n\n"
            
            text += "❌ 取消格式：\n"
            text += "取消請假:申請編號\n\n"
            text += "範例：取消請假:123"
            
            return TextSendMessage(
                text=text,
                quick_reply=MessageProcessor.create_leave_menu()
            )
            
        except Exception as e:
            return TextSendMessage(
                text=f"❌ 查詢失敗：{str(e)}",
                quick_reply=MessageProcessor.create_leave_menu()
            )
    
    @staticmethod
    def process_cancel_leave(employee_id, command):
        """處理取消請假申請"""
        try:
            # 解析申請編號
            request_id_str = command.split(':', 1)[1].strip()
            request_id = int(request_id_str)
            
            result = LeaveManager.cancel_leave_request(request_id, employee_id)
            
            if result['success']:
                response_text = f"✅ {result['message']}\n\n取消成功！"
            else:
                response_text = f"❌ {result['message']}"
            
            return TextSendMessage(
                text=response_text,
                quick_reply=MessageProcessor.create_leave_menu()
            )
            
        except ValueError:
            return TextSendMessage(
                text="❌ 申請編號格式錯誤！\n\n正確格式：取消請假:123",
                quick_reply=MessageProcessor.create_leave_menu()
            )
        except Exception as e:
            return TextSendMessage(
                text=f"❌ 取消失敗：{str(e)}",
                quick_reply=MessageProcessor.create_leave_menu()
            )
    
    # === 管理員請假審核功能 ===
    @staticmethod
    def show_leave_approvals():
        """顯示請假審核功能（管理員）"""
        return TextSendMessage(
            text="請假審核管理\n\n請使用管理後台進行請假審核：\nhttp://localhost:5008/admin",
            quick_reply=MessageProcessor.create_main_menu()
        )
    
    # === 其他既有功能方法（保持不變）===
    @staticmethod
    def show_main_menu():
        """顯示主選單"""
        text = """🟢 企業出勤管理系統 - 主選單

請選擇您要使用的功能：

📋 快速功能：
• 上班打卡 / 下班打卡
• 今日狀態 / 查看記錄  
• 薪資查詢 / 個人統計
• 加班申報 / 加班摘要
• 請假申請 / 請假記錄
• 網路檢查

💡 點擊下方按鈕快速操作，或直接輸入文字指令"""
        
        return TextSendMessage(
            text=text,
            quick_reply=MessageProcessor.create_main_menu()
        )
    
    @staticmethod
    def show_overtime_menu():
        """顯示加班申報選單"""
        text = """⏰ 加班申報系統

選擇您要使用的加班功能：

📝 可用功能：
• 申報加班 - 提交新的加班申請
• 我的申請 - 查看申請狀態
• 加班摘要 - 本月加班統計
• 取消申請 - 取消待審核申請

💡 點擊下方按鈕或輸入指令"""
        
        return TextSendMessage(
            text=text,
            quick_reply=MessageProcessor.create_overtime_menu()
        )
    
    @staticmethod
    def show_overtime_apply_form(employee_id):
        """顯示加班申請表單"""
        text = """📝 加班申報表單

請按照以下格式提交加班申請：

格式：加班:日期,開始時間,結束時間,原因

範例：
• 加班:2024-01-15,18:00,20:00,專案趕工
• 加班:2024-01-16,19:00,22:30,系統維護
• 加班:明天,17:30,19:00,會議延長

📋 注意事項：
• 日期格式：YYYY-MM-DD 或 明天/今天
• 時間格式：HH:MM（24小時制）
• 加班時數最多24小時
• 原因請簡要說明

⚠️ 申請後需等待管理員審核"""
        
        return TextSendMessage(
            text=text,
            quick_reply=MessageProcessor.create_overtime_menu()
        )
    
    @staticmethod
    def process_overtime_application(employee_id, command):
        """處理加班申請"""
        try:
            # 解析指令：加班:日期,開始時間,結束時間,原因
            parts = command.split(':', 1)[1].split(',')
            
            if len(parts) < 3:
                return TextSendMessage(
                    text="❌ 格式錯誤！\n\n正確格式：\n加班:日期,開始時間,結束時間,原因\n\n範例：\n加班:2024-01-15,18:00,20:00,專案趕工",
                    quick_reply=MessageProcessor.create_overtime_menu()
                )
            
            date_str = parts[0].strip()
            start_time = parts[1].strip()
            end_time = parts[2].strip()
            reason = parts[3].strip() if len(parts) > 3 else '其他'
            
            # 處理日期
            overtime_date = MessageProcessor.parse_date_string(date_str)
            
            if not overtime_date:
                return TextSendMessage(
                    text="❌ 日期格式錯誤！\n\n支援格式：\n• 2024-01-15\n• 明天\n• 今天",
                    quick_reply=MessageProcessor.create_overtime_menu()
                )
            
            # 驗證時間格式
            if not re.match(r'^\d{1,2}:\d{2}$', start_time) or not re.match(r'^\d{1,2}:\d{2}$', end_time):
                return TextSendMessage(
                    text="❌ 時間格式錯誤！\n\n正確格式：HH:MM\n範例：18:00, 20:30",
                    quick_reply=MessageProcessor.create_overtime_menu()
                )
            
            # 提交申請
            overtime_data = {
                'overtime_date': overtime_date,
                'start_time': start_time,
                'end_time': end_time,
                'reason': reason
            }
            
            result = OvertimeManager.submit_overtime_request(employee_id, overtime_data)
            
            if result['success']:
                response_text = f"✅ {result['message']}\n\n📋 申請詳情：\n日期：{overtime_date}\n時間：{start_time} - {end_time}\n時數：{result['hours']}小時\n原因：{reason}\n\n⏳ 請等待管理員審核"
            else:
                response_text = f"❌ {result['message']}"
            
            return TextSendMessage(
                text=response_text,
                quick_reply=MessageProcessor.create_overtime_menu()
            )
            
        except Exception as e:
            return TextSendMessage(
                text=f"❌ 申請處理失敗：{str(e)}\n\n請檢查格式後重試",
                quick_reply=MessageProcessor.create_overtime_menu()
            )
    
    @staticmethod
    def show_my_overtime_requests(employee_id):
        """顯示我的加班申請"""
        try:
            # 獲取最近的申請記錄
            requests = OvertimeManager.get_overtime_requests(employee_id=employee_id, limit=10)
            
            if not requests:
                return TextSendMessage(
                    text="📋 我的加班申請\n\n目前沒有加班申請記錄\n\n💡 輸入「申報加班」開始申請",
                    quick_reply=MessageProcessor.create_overtime_menu()
                )
            
            text = "📋 我的加班申請記錄\n" + "─" * 25 + "\n\n"
            
            for req in requests:
                status_emoji = {
                    'pending': '⏳ 待審核',
                    'approved': '✅ 已批准',
                    'rejected': '❌ 已拒絕'
                }.get(req['status'], req['status'])
                
                text += f"🆔 申請 #{req['id']}\n"
                text += f"📅 {req['overtime_date']} {req['start_time']}-{req['end_time']}\n"
                text += f"⏰ {req['hours']}小時 | {status_emoji}\n"
                text += f"📝 {req['reason']}\n\n"
            
            text += "💡 如需取消待審核申請，輸入「取消申請」"
            
            return TextSendMessage(
                text=text,
                quick_reply=MessageProcessor.create_overtime_menu()
            )
            
        except Exception as e:
            return TextSendMessage(
                text=f"❌ 查詢失敗：{str(e)}",
                quick_reply=MessageProcessor.create_overtime_menu()
            )
    
    @staticmethod
    def show_overtime_summary(employee_id):
        """顯示加班摘要"""
        try:
            summary = OvertimeManager.get_employee_overtime_summary(employee_id)
            
            text = f"📊 加班統計摘要 - {summary['month']}\n"
            text += "─" * 25 + "\n\n"
            
            stats = summary['stats']
            text += f"⏳ 待審核：{stats['pending']['count']}筆 ({stats['pending']['hours']:.1f}小時)\n"
            text += f"✅ 已批准：{stats['approved']['count']}筆 ({stats['approved']['hours']:.1f}小時)\n"
            text += f"❌ 已拒絕：{stats['rejected']['count']}筆 ({stats['rejected']['hours']:.1f}小時)\n\n"
            
            text += "💰 預估加班費：\n"
            text += f"${summary['estimated_overtime_pay']:,.0f}\n"
            text += "（僅計算已批准項目）\n\n"
            
            text += "💡 提示：\n"
            text += "• 輸入「申報加班」提交新申請\n"
            text += "• 輸入「我的申請」查看詳細記錄"
            
            return TextSendMessage(
                text=text,
                quick_reply=MessageProcessor.create_overtime_menu()
            )
            
        except Exception as e:
            return TextSendMessage(
                text=f"❌ 查詢摘要失敗：{str(e)}",
                quick_reply=MessageProcessor.create_overtime_menu()
            )
    
    @staticmethod
    def show_cancel_overtime_form(employee_id):
        """顯示取消加班申請表單"""
        try:
            # 獲取待審核的申請
            pending_requests = OvertimeManager.get_overtime_requests(
                employee_id=employee_id, 
                status='pending', 
                limit=5
            )
            
            if not pending_requests:
                return TextSendMessage(
                    text="📋 取消加班申請\n\n目前沒有待審核的申請可以取消",
                    quick_reply=MessageProcessor.create_overtime_menu()
                )
            
            text = "📋 可取消的加班申請\n"
            text += "─" * 25 + "\n\n"
            
            for req in pending_requests:
                text += f"🆔 #{req['id']} | {req['overtime_date']}\n"
                text += f"⏰ {req['start_time']}-{req['end_time']} ({req['hours']}h)\n"
                text += f"📝 {req['reason']}\n\n"
            
            text += "❌ 取消格式：\n"
            text += "取消申請:申請編號\n\n"
            text += "範例：取消申請:123"
            
            return TextSendMessage(
                text=text,
                quick_reply=MessageProcessor.create_overtime_menu()
            )
            
        except Exception as e:
            return TextSendMessage(
                text=f"❌ 查詢失敗：{str(e)}",
                quick_reply=MessageProcessor.create_overtime_menu()
            )
    
    @staticmethod
    def process_cancel_overtime(employee_id, command):
        """處理取消加班申請"""
        try:
            # 解析申請編號
            request_id_str = command.split(':', 1)[1].strip()
            request_id = int(request_id_str)
            
            result = OvertimeManager.cancel_overtime_request(request_id, employee_id)
            
            if result['success']:
                response_text = f"✅ {result['message']}\n\n取消成功！"
            else:
                response_text = f"❌ {result['message']}"
            
            return TextSendMessage(
                text=response_text,
                quick_reply=MessageProcessor.create_overtime_menu()
            )
            
        except ValueError:
            return TextSendMessage(
                text="❌ 申請編號格式錯誤！\n\n正確格式：取消申請:123",
                quick_reply=MessageProcessor.create_overtime_menu()
            )
        except Exception as e:
            return TextSendMessage(
                text=f"❌ 取消失敗：{str(e)}",
                quick_reply=MessageProcessor.create_overtime_menu()
            )
    
    @staticmethod
    def parse_date_string(date_str):
        """解析日期字串"""
        try:
            now = datetime.now(TW_TZ)
            
            if date_str in ['今天', '今日']:
                return now.strftime('%Y-%m-%d')
            elif date_str in ['明天', '明日']:
                tomorrow = now + timedelta(days=1)
                return tomorrow.strftime('%Y-%m-%d')
            elif date_str in ['後天']:
                day_after = now + timedelta(days=2)
                return day_after.strftime('%Y-%m-%d')
            else:
                # 嘗試解析 YYYY-MM-DD 格式
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                return date_obj.strftime('%Y-%m-%d')
        except:
            return None
    
    @staticmethod
    def show_salary_menu():
        """顯示薪資查詢選單"""
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
                text="您還可以查詢其他月份的薪資，或查看更多功能",
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
                text="查詢完成！您可以繼續查詢其他月份",
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
            text=f"{employee_name} 的薪資歷史記錄\n\n選擇要查看的時間範圍：",
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
                    text=f"{title}\n\n查無薪資記錄\n可能原因：\n• 尚未進行薪資計算\n• 該期間無出勤記錄\n\n請聯繫管理員確認",
                    quick_reply=MessageProcessor.create_salary_menu()
                )
            
            # 建立薪資記錄摘要
            history_text = f"{employee_name} - {title}\n"
            history_text += "─" * 25 + "\n\n"
            
            total_salary = 0
            for record in records:
                year_month = f"{record['year']}/{record['month']:02d}"
                net_salary = record['net_salary']
                work_days = record['work_days']
                total_hours = record['total_hours']
                
                total_salary += net_salary
                
                history_text += f"{year_month}月\n"
                history_text += f"實發薪資：${net_salary:,.0f}\n"
                history_text += f"出勤：{work_days}天 / {total_hours:.1f}小時\n\n"
            
            # 添加統計摘要
            avg_salary = total_salary / len(records) if records else 0
            history_text += "═" * 25 + "\n"
            history_text += f"統計摘要：\n"
            history_text += f"• 總薪資：${total_salary:,.0f}\n"
            history_text += f"• 平均月薪：${avg_salary:,.0f}\n"
            history_text += f"• 記錄筆數：{len(records)}個月"
            
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
                
                info_text = f"""個人資訊

員工編號：{emp_id}
姓名：{name}
部門：{department or '未設定'}
職位：{position or '未設定'}
權限：{'管理員' if role == 'ADMIN' else '一般員工'}
電子郵件：{email or '未設定'}
到職日期：{hire_date or '未設定'}

薪資功能：
• 輸入「薪資查詢」查看本月薪資
• 輸入「薪資記錄」查看歷史記錄

加班功能：
• 輸入「申報加班」提交加班申請
• 輸入「加班摘要」查看本月統計

請假功能：
• 輸入「申請請假」提交請假申請
• 輸入「請假記錄」查看請假歷史

輸入「選單」查看更多功能"""
                
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
        """獲取幫助訊息 - 支援員工薪資查詢、加班申報和請假功能"""
        base_help = """企業出勤管理系統

基本功能：
• 上班打卡 / 下班打卡
• 今日狀態 / 查看記錄
• 薪資查詢 / 個人資訊
• 加班申報 / 加班摘要
• 請假申請 / 請假記錄
• 網路檢查

薪資功能：
• 本月薪資 / 指定月份查詢
• 薪資歷史記錄

加班申報：
• 申報加班 - 提交加班申請
• 我的申請 - 查看申請狀態
• 加班摘要 - 統計預估加班費
• 取消申請 - 取消待審申請

請假申請：
• 申請請假 - 提交各類請假申請
• 我的請假 - 查看申請狀態
• 請假記錄 - 查看歷史記錄
• 請假額度 - 查看剩餘假期

個人資訊：
• 查看員工編號、姓名、部門
• 查看權限和到職日期

靈活打卡特色：
• 每日上班/下班打卡各2次機會
• 智能狀態檢查防重複

點擊下方按鈕快速操作"""
        
        if role == 'ADMIN':
            admin_help = """

管理功能：
• 員工管理 / 出勤統計
• 薪資管理 / 網路設定
• 加班審核 / 請假審核
• 審核管理

管理後台：http://localhost:5008/admin"""
            base_help += admin_help
        else:
            employee_help = """

常用指令：
• 輸入「個人資訊」查看基本資料
• 輸入「薪資查詢」查看本月薪資
• 輸入「薪資記錄」查看歷史記錄
• 輸入「薪資查詢:2024/03」查看特定月份
• 輸入「申報加班」提交加班申請
• 輸入「加班摘要」查看本月統計
• 輸入「申請請假」提交請假申請
• 輸入「請假記錄」查看請假歷史
• 輸入「請假額度」查看剩餘假期

如有薪資、加班或請假問題請聯繫管理部門"""
            base_help += employee_help
        
        return TextSendMessage(
            text=base_help,
            quick_reply=MessageProcessor.create_main_menu()
        )
    
    @staticmethod
    def show_salary_setup_notice():
        """顯示薪資設定提醒"""
        return """薪資查詢功能

尚未設定薪資資料

您的薪資設定可能尚未完成，請聯繫管理員進行以下設定：
• 基本薪資（月薪制）
• 時薪標準  
• 加班費標準
• 獎金設定

設定完成後即可查詢薪資明細

可用功能：
• 本月薪資 - 查看當月薪資試算
• 薪資查詢:2024/03 - 查看特定月份
• 薪資記錄 - 查看歷史薪資記錄

如有疑問請聯繫人事或管理部門"""
    
    # 管理員加班審核功能
    @staticmethod
    def show_overtime_approvals():
        """顯示加班審核功能（管理員）"""
        return TextSendMessage(
            text="加班審核管理\n\n請使用管理後台進行加班審核：\nhttp://localhost:5008/admin",
            quick_reply=MessageProcessor.create_main_menu()
        )
    
    @staticmethod
    def create_text_message(content):
        """創建訊息 - 支援多種格式"""
        if isinstance(content, (FlexSendMessage, list)):
            return content
        elif isinstance(content, TextSendMessage):
            return content
        else:
            return TextSendMessage(text=str(content))
    
    # 自助註冊相關功能
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
        
        return """開始自助註冊流程

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
            return "姓名格式不正確，請重新輸入\n格式：姓名:您的姓名"
        
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
        
        return f"""姓名已記錄：{name}

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
            return "部門格式不正確，請重新輸入\n格式：部門:您的部門"
        
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        # 檢查是否有註冊記錄
        cursor.execute('SELECT name FROM pending_registrations WHERE line_user_id = ?', (line_user_id,))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return "請先輸入姓名\n格式：姓名:您的姓名"
        
        # 更新註冊資料
        cursor.execute('''
            UPDATE pending_registrations 
            SET department = ?, step = 3 
            WHERE line_user_id = ?
        ''', (department, line_user_id))
        
        conn.commit()
        conn.close()
        
        name = result[0]
        
        return f"""部門已記錄：{department}

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
            return "註冊資料不完整，請重新開始註冊\n輸入「註冊員工」重新開始"
        
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
        
        return f"""註冊完成！

員工編號：{employee_id}
姓名：{name}
部門：{department}
權限：一般員工

現在您可以開始使用靈活打卡功能了！

靈活打卡特色：
• 每日上班打卡：2次機會
• 每日下班打卡：2次機會
• 智能狀態檢查：防止重複打卡

基本操作：
上班時輸入「上班打卡」
下班時輸入「下班打卡」
查看狀態輸入「今日狀態」
查看記錄輸入「查看記錄」

薪資查詢：
輸入「薪資查詢」查看本月薪資
輸入「薪資記錄」查看歷史記錄
輸入「薪資查詢:2024/03」查看特定月份

加班申報：
輸入「申報加班」提交加班申請
輸入「加班摘要」查看本月統計

請假申請：
輸入「申請請假」提交請假申請
輸入「請假記錄」查看請假歷史
輸入「請假額度」查看剩餘假期

請在公司網路環境內進行打卡
輸入「幫助」查看完整功能說明"""

    @staticmethod
    def handle_new_user():
        """處理新用戶"""
        return """歡迎使用企業出勤管理系統！

您尚未註冊，請開始自助註冊流程：

註冊步驟：
1. 輸入「註冊員工」開始註冊
2. 按照提示輸入姓名和部門
3. 完成後即可使用打卡功能

輸入「註冊員工」立即開始"""

    @staticmethod
    def show_employee_management():
        """顯示員工管理功能"""
        return TextSendMessage(
            text="員工管理功能\n\n請使用管理後台進行詳細操作：\nhttp://localhost:5008/admin",
            quick_reply=MessageProcessor.create_main_menu()
        )

    @staticmethod
    def show_attendance_stats():
        """顯示出勤統計功能"""
        return TextSendMessage(
            text="出勤統計功能\n\n請使用管理後台查看詳細報表：\nhttp://localhost:5008/admin",
            quick_reply=MessageProcessor.create_main_menu()
        )

    @staticmethod
    def show_network_settings():
        """顯示網路設定功能"""
        return TextSendMessage(
            text="網路設定功能\n\n請使用管理後台進行設定：\nhttp://localhost:5008/admin",
            quick_reply=MessageProcessor.create_main_menu()
        )

    @staticmethod
    def get_welcome_message():
        """獲取歡迎訊息"""
        return """歡迎使用企業出勤管理系統！

這是一個功能完整的智能打卡系統

靈活打卡特色：
• 每日上班打卡：2次機會
• 每日下班打卡：2次機會
• 智能狀態檢查

薪資查詢功能：
• 查看個人薪資明細
• 查詢歷史薪資記錄
• 支援多月份查詢

加班申報功能：
• 員工LINE Bot申報加班
• 管理員線上審核
• 自動計算加班費

請假申請功能：
• 支援多種假別申請
• 線上審核流程
• 自動額度管理

開始使用：
• 新用戶請輸入「註冊員工」
• 舊用戶直接輸入「上班打卡」
• 查看功能請輸入「幫助」

祝您使用愉快！"""