# attendance.py - 靈活打卡系統（各2次機會）
import sqlite3
from datetime import datetime, timedelta
import pytz
from models import CompanySettings, WORK_STATUS
from network_security import NetworkSecurity

# 台灣時區設定
TW_TZ = pytz.timezone('Asia/Taipei')

class AttendanceManager:
    """出勤管理類 - 靈活打卡版"""
    
    @staticmethod
    def clock_in(employee_id, user_ip=None):
        """上班打卡 - 一天最多2次機會"""
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        today = datetime.now(TW_TZ).strftime('%Y-%m-%d')
        
        # 檢查今日上班打卡次數
        cursor.execute('''
            SELECT COUNT(*) FROM attendance_records 
            WHERE employee_id = ? AND DATE(taiwan_time) = ? AND action_type = 'clock_in'
        ''', (employee_id, today))
        
        clock_in_count = cursor.fetchone()[0]
        if clock_in_count >= 2:
            conn.close()
            return {'success': False, 'message': '今日上班打卡次數已達上限（2次）'}
        
        # 檢查當前狀態 - 如果已經是上班狀態，不允許重複上班打卡
        current_status = AttendanceManager.get_current_work_status(employee_id, today)
        if current_status == 'working':
            conn.close()
            return {'success': False, 'message': '您目前已經是上班狀態，請先下班打卡'}
        
        # 網路權限檢查
        network_result = NetworkSecurity.validate_punch_permission()
        if not network_result['success']:
            conn.close()
            return network_result
        
        now = datetime.now(TW_TZ)
        taiwan_time = now.strftime('%Y-%m-%d %H:%M:%S')
        
        # 判斷是否遲到（僅第一次上班打卡計算遲到）
        status = 'normal'
        if clock_in_count == 0:  # 第一次上班打卡
            work_start = CompanySettings.get_setting('work_start_time', '09:00')
            late_threshold = int(CompanySettings.get_setting('late_threshold', '10'))
            
            work_start_time = datetime.strptime(f"{today} {work_start}", '%Y-%m-%d %H:%M')
            work_start_time = TW_TZ.localize(work_start_time)
            
            if now > work_start_time + timedelta(minutes=late_threshold):
                status = 'late'
        
        # 記錄打卡
        cursor.execute('''
            INSERT INTO attendance_records 
            (employee_id, action_type, taiwan_time, ip_address, network_info, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (employee_id, 'clock_in', taiwan_time, network_result['ip'], 
              network_result['network_info'], status))
        
        conn.commit()
        conn.close()
        
        # 提示訊息
        attempt_msg = f"第{clock_in_count + 1}次" if clock_in_count > 0 else ""
        remaining_msg = f"\n💡 今日還可上班打卡 {1 - clock_in_count} 次" if clock_in_count == 0 else ""
        
        return {
            'success': True, 
            'message': f'上班打卡成功！{attempt_msg}',
            'time': taiwan_time,
            'status': status,
            'punch_count': clock_in_count + 1,
            'network_info': network_result['network_info'],
            'remaining_msg': remaining_msg
        }
    
    @staticmethod
    def clock_out(employee_id, user_ip=None):
        """下班打卡 - 一天最多2次機會"""
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        today = datetime.now(TW_TZ).strftime('%Y-%m-%d')
        
        # 檢查今日下班打卡次數
        cursor.execute('''
            SELECT COUNT(*) FROM attendance_records 
            WHERE employee_id = ? AND DATE(taiwan_time) = ? AND action_type = 'clock_out'
        ''', (employee_id, today))
        
        clock_out_count = cursor.fetchone()[0]
        if clock_out_count >= 2:
            conn.close()
            return {'success': False, 'message': '今日下班打卡次數已達上限（2次）'}
        
        # 檢查當前狀態 - 必須是上班狀態才能下班打卡
        current_status = AttendanceManager.get_current_work_status(employee_id, today)
        if current_status != 'working':
            conn.close()
            return {'success': False, 'message': '您目前不是上班狀態，請先上班打卡'}
        
        # 網路權限檢查
        network_result = NetworkSecurity.validate_punch_permission()
        if not network_result['success']:
            conn.close()
            return network_result
        
        now = datetime.now(TW_TZ)
        taiwan_time = now.strftime('%Y-%m-%d %H:%M:%S')
        
        # 記錄下班打卡
        cursor.execute('''
            INSERT INTO attendance_records 
            (employee_id, action_type, taiwan_time, ip_address, network_info)
            VALUES (?, ?, ?, ?, ?)
        ''', (employee_id, 'clock_out', taiwan_time, network_result['ip'], 
              network_result['network_info']))
        
        conn.commit()
        conn.close()
        
        # 計算工作時數
        total_working_hours = AttendanceManager.calculate_daily_hours(employee_id, today)
        current_session_hours = AttendanceManager.calculate_current_session_hours(employee_id, today)
        
        # 提示訊息
        attempt_msg = f"第{clock_out_count + 1}次" if clock_out_count > 0 else ""
        remaining_msg = f"\n💡 今日還可下班打卡 {1 - clock_out_count} 次" if clock_out_count == 0 else ""
        
        return {
            'success': True, 
            'message': f'下班打卡成功！{attempt_msg}',
            'time': taiwan_time,
            'current_session_hours': current_session_hours,
            'total_working_hours': total_working_hours,
            'punch_count': clock_out_count + 1,
            'network_info': network_result['network_info'],
            'remaining_msg': remaining_msg
        }
    
    @staticmethod
    def get_current_work_status(employee_id, date):
        """獲取員工當前工作狀態"""
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        # 獲取當日最後一筆打卡記錄
        cursor.execute('''
            SELECT action_type FROM attendance_records 
            WHERE employee_id = ? AND DATE(taiwan_time) = ? 
            ORDER BY timestamp DESC LIMIT 1
        ''', (employee_id, date))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return 'off'  # 未打卡
        
        last_action = result[0]
        return 'working' if last_action == 'clock_in' else 'off'
    
    @staticmethod
    def calculate_current_session_hours(employee_id, date):
        """計算當前工作階段的時數"""
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        # 獲取最後一次上班打卡時間
        cursor.execute('''
            SELECT taiwan_time FROM attendance_records 
            WHERE employee_id = ? AND DATE(taiwan_time) = ? AND action_type = 'clock_in'
            ORDER BY timestamp DESC LIMIT 1
        ''', (employee_id, date))
        
        last_clock_in = cursor.fetchone()
        conn.close()
        
        if not last_clock_in:
            return 0
        
        try:
            clock_in_time = datetime.strptime(last_clock_in[0], '%Y-%m-%d %H:%M:%S')
            now = datetime.now(TW_TZ)
            hours = (now - clock_in_time).total_seconds() / 3600
            return round(hours, 2)
        except:
            return 0
    
    @staticmethod
    def calculate_daily_hours(employee_id, date):
        """計算每日總工作時數"""
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT action_type, taiwan_time FROM attendance_records 
            WHERE employee_id = ? AND DATE(taiwan_time) = ? 
            ORDER BY timestamp
        ''', (employee_id, date))
        
        records = cursor.fetchall()
        conn.close()
        
        total_hours = 0
        clock_in_time = None
        
        for action_type, time_str in records:
            try:
                time_obj = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
                
                if action_type == 'clock_in':
                    clock_in_time = time_obj
                elif action_type == 'clock_out' and clock_in_time:
                    hours = (time_obj - clock_in_time).total_seconds() / 3600
                    total_hours += hours
                    clock_in_time = None
            except:
                continue
        
        return round(total_hours, 2)
    
    @staticmethod
    def get_employee_status(employee_id):
        """獲取員工當前狀態"""
        today = datetime.now(TW_TZ).strftime('%Y-%m-%d')
        current_status = AttendanceManager.get_current_work_status(employee_id, today)
        
        if current_status == 'working':
            return WORK_STATUS['WORKING']
        else:
            return WORK_STATUS['OFF']
    
    @staticmethod
    def get_today_status(employee_id):
        """獲取今日狀態詳情"""
        today = datetime.now(TW_TZ).strftime('%Y-%m-%d')
        today_records = AttendanceManager.get_today_records(employee_id)
        current_status = AttendanceManager.get_current_work_status(employee_id, today)
        working_hours = AttendanceManager.calculate_daily_hours(employee_id, today)
        
        status_emoji = "🟢 上班中" if current_status == 'working' else "🔴 未上班"
        
        # 統計打卡次數
        clock_in_count = len([r for r in today_records if r[0] == 'clock_in'])
        clock_out_count = len([r for r in today_records if r[0] == 'clock_out'])
        
        result = f"📊 今日出勤狀態\n"
        result += f"─" * 20 + "\n"
        result += f"目前狀態：{status_emoji}\n"
        result += f"上班打卡：{clock_in_count}/2 次\n"
        result += f"下班打卡：{clock_out_count}/2 次\n"
        result += f"總工作時數：{working_hours} 小時\n"
        
        if current_status == 'working':
            current_session = AttendanceManager.calculate_current_session_hours(employee_id, today)
            result += f"本次工作：{current_session} 小時\n"
        
        if today_records:
            result += f"\n📝 今日記錄：\n"
            for action_type, time_str in today_records:
                emoji = "🌅" if action_type == "clock_in" else "🌙"
                action_name = "上班" if action_type == "clock_in" else "下班"
                time_only = time_str.split(' ')[1]
                result += f"{emoji} {action_name}打卡 {time_only}\n"
        
        # 顯示剩餘打卡機會
        result += f"\n💡 剩餘機會：\n"
        if clock_in_count < 2:
            result += f"• 還可上班打卡 {2 - clock_in_count} 次\n"
        if clock_out_count < 2:
            result += f"• 還可下班打卡 {2 - clock_out_count} 次\n"
        
        return result
    
    @staticmethod
    def get_today_records(employee_id):
        """獲取今日打卡記錄"""
        today = datetime.now(TW_TZ).strftime('%Y-%m-%d')
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT action_type, taiwan_time FROM attendance_records 
            WHERE employee_id = ? AND DATE(taiwan_time) = ? ORDER BY timestamp
        ''', (employee_id, today))
        records = cursor.fetchall()
        conn.close()
        return records
    
    @staticmethod
    def get_attendance_records(employee_id, limit=10):
        """獲取出勤記錄"""
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT action_type, taiwan_time, status, network_info FROM attendance_records 
            WHERE employee_id = ? ORDER BY timestamp DESC LIMIT ?
        ''', (employee_id, limit))
        
        records = cursor.fetchall()
        conn.close()
        
        if not records:
            return "📝 暫無出勤記錄"
        
        result = "📋 最近出勤記錄：\n" + "─" * 30 + "\n"
        for action_type, time_str, status, network_info in records:
            action_map = {
                'clock_in': '🟢 上班',
                'clock_out': '🔴 下班'
            }
            
            status_emoji = ""
            
            result += f"{action_map.get(action_type, action_type)} {time_str}{status_emoji}\n"
        
        return result
    
    @staticmethod
    def get_personal_stats(employee_id):
        """獲取個人統計"""
        # 本月統計
        now = datetime.now(TW_TZ)
        month_start = now.replace(day=1).strftime('%Y-%m-%d')
        
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        # 計算本月工作天數
        cursor.execute('''
            SELECT DATE(taiwan_time) as work_date FROM attendance_records 
            WHERE employee_id = ? AND action_type = 'clock_in' 
            AND taiwan_time >= ? 
            GROUP BY DATE(taiwan_time)
        ''', (employee_id, month_start))
        
        work_days = len(cursor.fetchall())
        
        # 計算本月遲到次數
        cursor.execute('''
            SELECT COUNT(*) FROM attendance_records 
            WHERE employee_id = ? AND action_type = 'clock_in' 
            AND status = 'late' AND taiwan_time >= ?
        ''', (employee_id, month_start))
        
        late_count = cursor.fetchone()[0]
        conn.close()
        
        # 計算總工時
        total_hours = 0
        for i in range(work_days):
            date = (now - timedelta(days=i)).strftime('%Y-%m-%d')
            daily_hours = AttendanceManager.calculate_daily_hours(employee_id, date)
            total_hours += daily_hours
        
        return f"""📊 個人統計報表
{now.strftime('%Y年%m月')}

📅 本月出勤天數：{work_days} 天
⏰ 累計工時：{total_hours:.1f} 小時
📈 平均日工時：{total_hours/work_days if work_days > 0 else 0:.1f} 小時
⚠️ 遲到次數：{late_count} 次

🔄 打卡機會：
• 每日上班打卡：2 次機會
• 每日下班打卡：2 次機會

💡 如需詳細報表，請聯繫管理員"""