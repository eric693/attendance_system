# attendance_report.py - 出勤報表模組
import sqlite3
from datetime import datetime, timedelta
import pytz
from models import CompanySettings

# 台灣時區設定
TW_TZ = pytz.timezone('Asia/Taipei')

class AttendanceReport:
    """出勤報表生成器"""
    
    @staticmethod
    def get_daily_summary(date=None):
        """每日出勤摘要"""
        if not date:
            date = datetime.now(TW_TZ).strftime('%Y-%m-%d')
        
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        # 今日出勤統計
        cursor.execute('''
            SELECT 
                e.employee_id,
                e.name,
                e.department,
                MIN(CASE WHEN ar.action_type = 'clock_in' THEN ar.taiwan_time END) as clock_in_time,
                MAX(CASE WHEN ar.action_type = 'clock_out' THEN ar.taiwan_time END) as clock_out_time,
                MAX(CASE WHEN ar.action_type = 'clock_in' THEN ar.status END) as status,
                MAX(CASE WHEN ar.action_type = 'clock_in' THEN ar.ip_address END) as ip_address
            FROM employees e
            LEFT JOIN attendance_records ar ON e.employee_id = ar.employee_id 
                AND DATE(ar.taiwan_time) = ?
            WHERE e.status = 'active'
            GROUP BY e.employee_id, e.name, e.department
            ORDER BY e.department, e.name
        ''', (date,))
        
        records = cursor.fetchall()
        conn.close()
        
        # 計算工作時數
        results = []
        for record in records:
            employee_id, name, department, clock_in, clock_out, status, ip = record
            
            working_hours = 0
            if clock_in and clock_out:
                try:
                    in_time = datetime.strptime(clock_in, '%Y-%m-%d %H:%M:%S')
                    out_time = datetime.strptime(clock_out, '%Y-%m-%d %H:%M:%S')
                    working_hours = round((out_time - in_time).total_seconds() / 3600, 2)
                except:
                    working_hours = 0
            
            # 判斷出勤狀態
            attendance_status = "未打卡"
            if clock_in and clock_out:
                attendance_status = "正常"
            elif clock_in:
                attendance_status = "未下班"
            
            if status == 'late':
                attendance_status += " (遲到)"
            
            results.append({
                'employee_id': employee_id,
                'name': name,
                'department': department,
                'clock_in': clock_in,
                'clock_out': clock_out,
                'working_hours': working_hours,
                'status': attendance_status,
                'ip_address': ip or '-'
            })
        
        return results
    
    @staticmethod
    def get_monthly_summary(year=None, month=None):
        """月度出勤摘要"""
        if not year:
            year = datetime.now(TW_TZ).year
        if not month:
            month = datetime.now(TW_TZ).month
        
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        # 月度統計
        cursor.execute('''
            SELECT 
                e.employee_id,
                e.name,
                e.department,
                COUNT(DISTINCT DATE(ar.taiwan_time)) as work_days,
                COUNT(CASE WHEN ar.action_type = 'clock_in' AND ar.status = 'late' THEN 1 END) as late_count,
                COUNT(CASE WHEN ar.action_type = 'clock_in' THEN 1 END) as checkin_count,
                COUNT(CASE WHEN ar.action_type = 'clock_out' THEN 1 END) as checkout_count
            FROM employees e
            LEFT JOIN attendance_records ar ON e.employee_id = ar.employee_id 
                AND strftime('%Y', ar.taiwan_time) = ? 
                AND strftime('%m', ar.taiwan_time) = ?
            WHERE e.status = 'active'
            GROUP BY e.employee_id, e.name, e.department
            ORDER BY e.department, e.name
        ''', (str(year), f"{month:02d}"))
        
        records = cursor.fetchall()
        
        # 計算每個員工的總工時
        results = []
        for record in records:
            employee_id, name, department, work_days, late_count, checkin_count, checkout_count = record
            
            # 計算總工時
            cursor.execute('''
                SELECT DATE(taiwan_time) as work_date
                FROM attendance_records 
                WHERE employee_id = ? 
                AND strftime('%Y', taiwan_time) = ? 
                AND strftime('%m', taiwan_time) = ?
                AND action_type = 'clock_in'
                GROUP BY DATE(taiwan_time)
            ''', (employee_id, str(year), f"{month:02d}"))
            
            work_dates = [row[0] for row in cursor.fetchall()]
            total_hours = 0
            
            for date in work_dates:
                daily_hours = AttendanceReport.calculate_daily_hours(employee_id, date)
                total_hours += daily_hours
            
            results.append({
                'employee_id': employee_id,
                'name': name,
                'department': department,
                'work_days': work_days,
                'total_hours': round(total_hours, 2),
                'late_count': late_count,
                'checkin_count': checkin_count,
                'checkout_count': checkout_count,
                'avg_hours': round(total_hours / work_days, 2) if work_days > 0 else 0
            })
        
        conn.close()
        return results
    
    @staticmethod
    def calculate_daily_hours(employee_id, date):
        """計算單日工作時數"""
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
    def get_network_violations(start_date=None, end_date=None):
        """獲取網路違規記錄"""
        if not start_date:
            start_date = (datetime.now(TW_TZ) - timedelta(days=30)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now(TW_TZ).strftime('%Y-%m-%d')
        
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                ar.taiwan_time,
                e.name,
                e.department,
                ar.action_type,
                ar.ip_address,
                ar.network_info,
                ar.status
            FROM attendance_records ar
            JOIN employees e ON ar.employee_id = e.employee_id
            WHERE ar.status = 'network_violation'
            AND DATE(ar.taiwan_time) BETWEEN ? AND ?
            ORDER BY ar.taiwan_time DESC
        ''', (start_date, end_date))
        
        records = cursor.fetchall()
        conn.close()
        
        return [
            {
                'time': record[0],
                'name': record[1],
                'department': record[2],
                'action': '上班' if record[3] == 'clock_in' else '下班',
                'ip_address': record[4],
                'network_info': record[5],
                'status': record[6]
            }
            for record in records
        ]
    
    @staticmethod
    def get_late_statistics(year=None, month=None):
        """遲到統計"""
        if not year:
            year = datetime.now(TW_TZ).year
        if not month:
            month = datetime.now(TW_TZ).month
        
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                e.name,
                e.department,
                COUNT(*) as late_count,
                GROUP_CONCAT(DATE(ar.taiwan_time)) as late_dates
            FROM attendance_records ar
            JOIN employees e ON ar.employee_id = e.employee_id
            WHERE ar.action_type = 'clock_in' 
            AND ar.status = 'late'
            AND strftime('%Y', ar.taiwan_time) = ? 
            AND strftime('%m', ar.taiwan_time) = ?
            GROUP BY e.employee_id, e.name, e.department
            ORDER BY late_count DESC, e.department, e.name
        ''', (str(year), f"{month:02d}"))
        
        records = cursor.fetchall()
        conn.close()
        
        return [
            {
                'name': record[0],
                'department': record[1],
                'late_count': record[2],
                'late_dates': record[3].split(',') if record[3] else []
            }
            for record in records
        ]
    
    @staticmethod
    def get_department_summary(date=None):
        """部門出勤摘要"""
        if not date:
            date = datetime.now(TW_TZ).strftime('%Y-%m-%d')
        
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                e.department,
                COUNT(DISTINCT e.employee_id) as total_employees,
                COUNT(DISTINCT CASE WHEN ar.action_type = 'clock_in' THEN e.employee_id END) as present_count,
                COUNT(CASE WHEN ar.action_type = 'clock_in' AND ar.status = 'late' THEN 1 END) as late_count
            FROM employees e
            LEFT JOIN attendance_records ar ON e.employee_id = ar.employee_id 
                AND DATE(ar.taiwan_time) = ?
            WHERE e.status = 'active'
            GROUP BY e.department
            ORDER BY e.department
        ''', (date,))
        
        records = cursor.fetchall()
        conn.close()
        
        return [
            {
                'department': record[0] or '未分類',
                'total_employees': record[1],
                'present_count': record[2],
                'absent_count': record[1] - record[2],
                'late_count': record[3],
                'attendance_rate': round((record[2] / record[1] * 100), 1) if record[1] > 0 else 0
            }
            for record in records
        ]
    
    @staticmethod
    def export_to_csv(data, filename):
        """導出為 CSV 格式"""
        import csv
        import io
        
        if not data:
            return None
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        
        return output.getvalue()
    
    @staticmethod
    def get_employee_detail_report(employee_id, start_date=None, end_date=None):
        """個人詳細出勤報表"""
        if not start_date:
            start_date = datetime.now(TW_TZ).replace(day=1).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now(TW_TZ).strftime('%Y-%m-%d')
        
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        # 獲取員工基本資訊
        cursor.execute('SELECT name, department, position FROM employees WHERE employee_id = ?', (employee_id,))
        employee_info = cursor.fetchone()
        
        if not employee_info:
            return None
        
        # 獲取出勤記錄
        cursor.execute('''
            SELECT 
                DATE(taiwan_time) as work_date,
                MIN(CASE WHEN action_type = 'clock_in' THEN taiwan_time END) as clock_in,
                MAX(CASE WHEN action_type = 'clock_out' THEN taiwan_time END) as clock_out,
                MAX(CASE WHEN action_type = 'clock_in' THEN status END) as status,
                MAX(CASE WHEN action_type = 'clock_in' THEN ip_address END) as ip
            FROM attendance_records 
            WHERE employee_id = ? 
            AND DATE(taiwan_time) BETWEEN ? AND ?
            GROUP BY DATE(taiwan_time)
            ORDER BY work_date DESC
        ''', (employee_id, start_date, end_date))
        
        records = cursor.fetchall()
        conn.close()
        
        # 處理記錄
        daily_records = []
        total_hours = 0
        late_count = 0
        
        for record in records:
            work_date, clock_in, clock_out, status, ip = record
            
            working_hours = 0
            if clock_in and clock_out:
                try:
                    in_time = datetime.strptime(clock_in, '%Y-%m-%d %H:%M:%S')
                    out_time = datetime.strptime(clock_out, '%Y-%m-%d %H:%M:%S')
                    working_hours = round((out_time - in_time).total_seconds() / 3600, 2)
                    total_hours += working_hours
                except:
                    working_hours = 0
            
            if status == 'late':
                late_count += 1
            
            daily_records.append({
                'date': work_date,
                'clock_in': clock_in.split(' ')[1] if clock_in else '-',
                'clock_out': clock_out.split(' ')[1] if clock_out else '-',
                'working_hours': working_hours,
                'status': '遲到' if status == 'late' else '正常',
                'ip_address': ip or '-'
            })
        
        return {
            'employee_info': {
                'name': employee_info[0],
                'department': employee_info[1],
                'position': employee_info[2]
            },
            'summary': {
                'work_days': len([r for r in daily_records if r['clock_in'] != '-']),
                'total_hours': round(total_hours, 2),
                'late_count': late_count,
                'avg_hours': round(total_hours / len(daily_records), 2) if daily_records else 0
            },
            'daily_records': daily_records
        }