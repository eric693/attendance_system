# message_processor.py - LINE Bot 訊息處理模組
import sqlite3
from linebot.models import TextSendMessage
from models import EmployeeManager
from attendance import AttendanceManager
from network_security import NetworkSecurity

class MessageProcessor:
    """訊息處理器"""
    
    @staticmethod
    def process_command(line_user_id, message_text):
        """處理訊息指令"""
        # 取得或註冊員工
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
        
        # 基本出勤功能 - 重點保留的功能
        if command in ['上班打卡', '上班']:
            return MessageProcessor.handle_clock_in(employee_id)
        elif command in ['下班打卡', '下班']:
            return MessageProcessor.handle_clock_out(employee_id)
        elif command in ['今日狀態', '狀態']:
            return MessageProcessor.get_today_status(employee_id)
        elif command in ['查看記錄', '記錄']:
            return MessageProcessor.get_attendance_records(employee_id)
        elif command in ['個人統計', '統計']:
            return MessageProcessor.get_personal_stats(employee_id)
        elif command in ['請假申請', '請假']:
            return MessageProcessor.show_leave_options()
        elif command in ['網路檢查', '檢查網路']:
            return MessageProcessor.check_network_status()
        
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
        
        # 幫助資訊
        return MessageProcessor.get_help(role)
    
    @staticmethod
    def handle_new_user():
        """處理新用戶"""
        return """🎉 歡迎使用企業出勤管理系統！

您是新用戶，有兩種方式開始使用：

🔥 方式一：自助註冊（推薦）
輸入「註冊員工」開始快速註冊

👨‍💼 方式二：聯繫管理員
• 請管理員在後台新增您的帳號
• 管理後台：http://localhost:5008/admin
• 需要提供您的姓名和部門資訊

💡 註冊完成後即可開始打卡！"""
    
    @staticmethod
    def handle_clock_in(employee_id):
        """處理上班打卡"""
        result = AttendanceManager.clock_in(employee_id)
        
        if result['success']:
            status_text = ""
            if result['status'] == 'late':
                status_text = "\n⚠️ 注意：您已遲到"
            
            network_text = f"\n🌐 網路狀態：{result['network_info']}"
            
            return f"✅ 上班打卡成功！\n⏰ 時間：{result['time']}{status_text}{network_text}\n\n祝您工作順利！"
        else:
            if result.get('network_error'):
                return f"🚫 打卡失敗\n\n{result['message']}\n\n💡 請確認：\n• 是否連接公司WiFi\n• 是否在公司網路環境內 (147.92.150.0/24)\n• 聯繫IT部門確認網路設定"
            return f"❌ {result['message']}"
    
    @staticmethod
    def handle_clock_out(employee_id):
        """處理下班打卡"""
        result = AttendanceManager.clock_out(employee_id)
        
        if result['success']:
            network_text = f"\n🌐 網路狀態：{result['network_info']}"
            return f"✅ 下班打卡成功！\n⏰ 時間：{result['time']}\n🕐 今日工時：{result['working_hours']} 小時{network_text}\n\n辛苦了！"
        else:
            if result.get('network_error'):
                return f"🚫 打卡失敗\n\n{result['message']}\n\n💡 請確認：\n• 是否連接公司WiFi\n• 是否在公司網路環境內 (147.92.150.0/24)\n• 聯繫IT部門確認網路設定"
            return f"❌ {result['message']}"
    
    @staticmethod
    def get_today_status(employee_id):
        """獲取今日狀態"""
        return AttendanceManager.get_today_status(employee_id)
    
    @staticmethod
    def get_attendance_records(employee_id):
        """獲取出勤記錄"""
        return AttendanceManager.get_attendance_records(employee_id)
    
    @staticmethod
    def get_personal_stats(employee_id):
        """獲取個人統計"""
        return AttendanceManager.get_personal_stats(employee_id)
    
    @staticmethod
    def check_network_status():
        """檢查當前網路狀態"""
        network_result = NetworkSecurity.check_punch_network()
        
        status_emoji = "✅" if network_result['allowed'] else "❌"
        
        return f"""🌐 網路狀態檢查

{status_emoji} 當前IP：{network_result['ip']}
📡 網路狀態：{network_result['message']}

{'✅ 可以進行打卡' if network_result['allowed'] else '❌ 無法打卡，請檢查網路連接'}

💡 允許網路：147.92.150.0/24
如有問題請聯繫IT部門"""
    
    @staticmethod
    def show_leave_options():
        return """📝 請假申請

請選擇請假類型：
• 年假 - 輸入「年假申請」
• 病假 - 輸入「病假申請」
• 事假 - 輸入「事假申請」

💡 詳細申請請使用管理後台
🌐 網址：http://localhost:5008"""
    
    @staticmethod
    def show_employee_management():
        return """👥 員工管理功能

管理員可用操作：
• 查看員工列表 - 輸入「員工列表」
• 新增員工 - 輸入「新增員工」
• 網路設定 - 輸入「網路設定」

🌐 完整功能請使用管理後台
📊 網址：http://localhost:5008/admin"""
    
    @staticmethod
    def show_attendance_stats():
        return """📊 出勤統計管理

統計功能：
• 今日出勤 - 輸入「今日統計」
• 本月統計 - 輸入「本月統計」
• 網路日誌 - 輸入「網路記錄」

📈 詳細報表請使用管理後台"""
    
    @staticmethod
    def show_leave_approvals():
        return """✅ 請假審核

審核功能：
• 待審請假 - 輸入「待審請假」
• 審核記錄 - 輸入「審核記錄」

⚡ 快速審核請使用管理後台"""
    
    @staticmethod
    def show_network_settings():
        return """🌐 網路管理設定

網路設定功能：
• 查看允許網路 - 輸入「查看網路」
• 網路檢查記錄 - 輸入「網路記錄」

🔧 完整設定請使用管理介面
⚙️ 當前允許網路：147.92.150.0/24"""
    
    @staticmethod
    def get_help(role):
        """獲取幫助訊息"""
        base_help = """🤖 企業出勤管理系統

👤 基本功能：
• 上班打卡 / 下班打卡
• 今日狀態 / 查看記錄
• 個人統計 / 請假申請
• 網路檢查

🌐 網路限制：
系統會檢查您的網路位置 (147.92.150.0/24)
確保在公司環境內才能打卡

💡 使用底部選單快速操作"""
        
        if role == 'ADMIN':
            admin_help = """

👨‍💼 管理功能：
• 員工管理 / 出勤統計
• 請假審核 / 網路設定

🔗 管理後台：http://localhost:5008/admin"""
            base_help += admin_help
        
        return base_help
    
    @staticmethod
    def get_welcome_message():
        """獲取歡迎訊息"""
        return """🎉 歡迎使用企業出勤管理系統！

本系統提供安全的企業級出勤管理：

✨ 主要功能：
• 🕘 智能打卡（網路位置驗證）
• 📊 出勤記錄與統計
• 📝 請假申請
• 🌐 網路安全控制

🚀 快速開始：
方式一：自助註冊（推薦）
➡️ 輸入「註冊員工」立即開始

方式二：管理員新增
➡️ 請管理員在後台新增您的帳號

🔒 安全特色：
• 限制特定網路才能打卡 (147.92.150.0/24)
• IP位置記錄與驗證
• 管理員/員工權限分離

💡 設定完成後輸入「幫助」查看完整功能
🌐 記得在公司網路環境內進行打卡！"""
    
    @staticmethod
    def create_text_message(text):
        """創建文字訊息"""
        return TextSendMessage(text=text)
    
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

現在您可以開始使用打卡功能了！

快速操作：
• 上班打卡
• 下班打卡
• 今日狀態
• 查看記錄
• 網路檢查

💡 輸入「幫助」查看完整功能說明
🌐 請在公司網路環境 (147.92.150.0/24) 內打卡"""