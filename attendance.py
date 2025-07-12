# attendance.py - 出勤管理模組
import sqlite3
from datetime import datetime, timedelta
import pytz
from models import CompanySettings, WORK_STATUS
from network_security import NetworkSecurity

# 台灣時區設定
TW_TZ = pytz.timezone('Asia/Taipei')

class AttendanceManager:
    """出勤管理類"""
    
    @staticmethod
    def clock_in(employee_id, user_ip=None):
        """上班打卡"""
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        # 檢查是否已經打卡
        today = datetime.now(TW_TZ).strftime('%Y-%m-%d')
        cursor.execute('''
            SELECT * FROM attendance_records 
            WHERE employee_id = ? AND DATE(taiwan_time) = ? AND action_type = 'clock_in'
        ''', (employee_id, today))
        
        if cursor.fetchone():
            conn.close()
            return {'success': False, 'message': '今日已經打過上班卡'}
        
        # 網路權限檢查
        network_result = NetworkSecurity.validate_punch_permission()
        if not network_result['success']:
            conn.close()
            return network_result
        
        now = datetime.now(TW_TZ)
        taiwan_time = now.strftime('%Y-%m-%d %H:%M:%S')
        
        # 判斷是否遲到
        work_start = CompanySettings.get_setting('work_start_time', '09:00')
        late_threshold = int(CompanySettings.get_setting('late_threshold', '10'))
        
        work_start_time = datetime.strptime(f"{today} {work_start}", '%Y-%m-%d %H:%M')
        work_start_time = TW_TZ.localize(work_start_time)
        
        status = 'normal'
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
        
        return {
            'success': True, 
            'message': '上班打卡成功',
            'time': taiwan_time,
            'status': status,
            'network_info': network_result['network_info']
        }
    
    @staticmethod
    def clock_out(employee_id, user_ip=None):
        """下班打卡"""
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        today = datetime.now(TW_TZ).strftime('%Y-%m-%d')
        
        # 檢查是否有上班打卡記錄
        cursor.execute('''
            SELECT * FROM attendance_records 
            WHERE employee_id = ? AND DATE(taiwan_time) = ? AND action_type = 'clock_in'
        ''', (employee_id, today))
        
        if not cursor.fetchone():
            conn.close()
            return {'success': False, 'message': '請先進行上班打卡'}
        
        # 檢查是否已經打過下班卡
        cursor.execute('''
            SELECT * FROM attendance_records 
            WHERE employee_id = ? AND DATE(taiwan_time) = ? AND action_type = 'clock_out'
        ''', (employee_id, today))
        
        if cursor.fetchone():
            conn.close()
            return {'success': False, 'message': '今日已經打過下班卡'}
        
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
        
        # 計算工作時數
        working_hours = AttendanceManager.calculate_daily_hours(employee_id, today)
        
        conn.commit()
        conn.close()
        
        return {
            'success': True, 
            'message': '下班打卡成功',
            'time': taiwan_time,
            'working_hours': working_hours,
            'network_info': network_result['network_info']
        }
    
    @staticmethod
    def calculate_daily_hours(employee_id, date):
        """計算每日工作時數"""
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
            time_obj = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
            
            if action_type == 'clock_in':
                clock_in_time = time_obj
            elif action_type == 'clock_out' and clock_in_time:
                hours = (time_obj - clock_in_time).total_seconds() / 3600
                total_hours += hours
                clock_in_time = None
        
        return round(total_hours, 2)
    
    @staticmethod
    def get_employee_status(employee_id):
        """獲取員工當前狀態"""
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        today = datetime.now(TW_TZ).strftime('%Y-%m-%d')
        
        cursor.execute('''
            SELECT action_type, taiwan_time FROM attendance_records 
            WHERE employee_id = ? AND DATE(taiwan_time) = ? 
            ORDER BY timestamp DESC LIMIT 1
        ''', (employee_id, today))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return WORK_STATUS['OFF']
        
        last_action = result[0]
        if last_action == 'clock_in':
            return WORK_STATUS['WORKING']
        else:
            return WORK_STATUS['OFF']
    
    @staticmethod
    def get_today_status(employee_id):
        """獲取今日狀態詳情"""
        today_records = AttendanceManager.get_today_records(employee_id)
        current_status = AttendanceManager.get_employee_status(employee_id)
        working_hours = AttendanceManager.calculate_daily_hours(employee_id, 
                                                               datetime.now(TW_TZ).strftime('%Y-%m-%d'))
        
        status_emoji = "🟢 工作中" if current_status == 'working' else "🔴 未工作"
        
        result = f"🟣 今日狀態\n📊 今日狀態報告\n"
        result += f"─" * 20 + "\n"
        result += f"目前狀態：{status_emoji}\n"
        result += f"今日打卡次數：{len(today_records)}\n"
        result += f"工作時數：{working_hours} 小時\n"
        
        if today_records:
            result += f"\n📝 今日記錄：\n"
            for action_type, time_str in today_records:
                emoji = "🌅" if action_type == "clock_in" else "🌙"
                time_only = time_str.split(' ')[1]
                result += f"{emoji} {action_type} {time_only}\n"
        
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
            if status == 'late':
                status_emoji = " ⚠️"
            
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

💡 如需詳細報表，請聯繫管理員"""