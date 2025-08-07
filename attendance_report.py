# attendance_report.py - 出勤報表模組 (支援多次打卡)
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
        """每日出勤摘要 - 支援多次打卡"""
        if not date:
            date = datetime.now(TW_TZ).strftime('%Y-%m-%d')
        
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        # 今日出勤統計 - 支援多次打卡
        cursor.execute('''
            SELECT 
                e.employee_id,
                e.name,
                e.department,
                GROUP_CONCAT(CASE WHEN ar.action_type = 'clock_in' THEN ar.taiwan_time END, '|') as clock_in_times,
                GROUP_CONCAT(CASE WHEN ar.action_type = 'clock_out' THEN ar.taiwan_time END, '|') as clock_out_times,
                COUNT(CASE WHEN ar.action_type = 'clock_in' THEN 1 END) as clock_in_count,
                COUNT(CASE WHEN ar.action_type = 'clock_out' THEN 1 END) as clock_out_count,
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
        
        # 處理記錄
        results = []
        for record in records:
            employee_id, name, department, clock_in_times, clock_out_times, clock_in_count, clock_out_count, status, ip = record
            
            # 解析打卡時間
            clock_ins = [t for t in (clock_in_times or '').split('|') if t]
            clock_outs = [t for t in (clock_out_times or '').split('|') if t]
            
            # 計算總工作時數
            working_hours = AttendanceReport.calculate_daily_hours_from_records(clock_ins, clock_outs)
            
            # 判斷出勤狀態
            attendance_status = AttendanceReport.get_attendance_status(clock_in_count, clock_out_count, status)
            
            # 格式化打卡時間顯示
            clock_in_display = AttendanceReport.format_punch_times(clock_ins, 'in')
            clock_out_display = AttendanceReport.format_punch_times(clock_outs, 'out')
            
            results.append({
                'employee_id': employee_id,
                'name': name,
                'department': department,
                'clock_in_times': clock_in_display,
                'clock_out_times': clock_out_display,
                'clock_in_count': clock_in_count,
                'clock_out_count': clock_out_count,
                'working_hours': working_hours,
                'status': attendance_status,
                'ip_address': ip or '-'
            })
        
        return results
    
    @staticmethod
    def format_punch_times(times, punch_type):
        """格式化打卡時間顯示"""
        if not times:
            return '-'
        
        formatted_times = []
        for i, time_str in enumerate(times):
            if time_str:
                time_only = time_str.split(' ')[1] if ' ' in time_str else time_str
                if punch_type == 'in':
                    label = '上午' if i == 0 else '下午'
                else:
                    label = '中午' if i == 0 else '晚上'
                formatted_times.append(f'{label}:{time_only}')
        
        return ' | '.join(formatted_times)
    
    @staticmethod
    def get_attendance_status(clock_in_count, clock_out_count, status):
        """判斷出勤狀態"""
        if clock_in_count == 0:
            return "未打卡"
        elif clock_in_count == 1 and clock_out_count == 0:
            return "上午上班中"
        elif clock_in_count == 1 and clock_out_count == 1:
            return "中午休息"
        elif clock_in_count == 2 and clock_out_count == 1:
            return "下午上班中"
        elif clock_in_count == 2 and clock_out_count == 2:
            return "正常下班"
        elif clock_in_count > clock_out_count:
            return "上班中"
        else:
            return "已下班"
        
        # 添加遲到標記
        if status == 'late':
            return attendance_status + " (遲到)"
        
        return attendance_status
    
    @staticmethod
    def calculate_daily_hours_from_records(clock_ins, clock_outs):
        """從打卡記錄計算每日工作時數"""
        total_hours = 0
        
        try:
            # 配對打卡記錄計算工時
            for i in range(len(clock_ins)):
                if i < len(clock_outs):
                    in_time = datetime.strptime(clock_ins[i], '%Y-%m-%d %H:%M:%S')
                    out_time = datetime.strptime(clock_outs[i], '%Y-%m-%d %H:%M:%S')
                    hours = (out_time - in_time).total_seconds() / 3600
                    total_hours += hours
        except Exception as e:
            print(f"計算工時錯誤: {e}")
            total_hours = 0
        
        return round(total_hours, 2)
    
    @staticmethod
    def get_monthly_summary(year=None, month=None):
        """月度出勤摘要 - 支援多次打卡統計"""
        if not year:
            year = datetime.now(TW_TZ).year
        if not month:
            month = datetime.now(TW_TZ).month
        
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        # 月度統計 - 包含多次打卡資訊
        cursor.execute('''
            SELECT 
                e.employee_id,
                e.name,
                e.department,
                COUNT(DISTINCT DATE(ar.taiwan_time)) as work_days,
                COUNT(CASE WHEN ar.action_type = 'clock_in' AND ar.status = 'late' THEN 1 END) as late_count,
                COUNT(CASE WHEN ar.action_type = 'clock_in' THEN 1 END) as total_clock_ins,
                COUNT(CASE WHEN ar.action_type = 'clock_out' THEN 1 END) as total_clock_outs,
                AVG(CASE WHEN ar.action_type = 'clock_in' THEN 
                    (SELECT COUNT(*) FROM attendance_records ar2 
                     WHERE ar2.employee_id = ar.employee_id 
                     AND DATE(ar2.taiwan_time) = DATE(ar.taiwan_time) 
                     AND ar2.action_type = 'clock_in')
                END) as avg_daily_clock_ins
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
            employee_id, name, department, work_days, late_count, total_clock_ins, total_clock_outs, avg_daily_clock_ins = record
            
            # 計算總工時
            total_hours = AttendanceReport.calculate_monthly_hours(employee_id, year, month)
            
            # 計算完整出勤天數（上下班都有打卡2次的天數）
            complete_days = AttendanceReport.calculate_complete_attendance_days(employee_id, year, month)
            
            results.append({
                'employee_id': employee_id,
                'name': name,
                'department': department,
                'work_days': work_days,
                'complete_days': complete_days,
                'total_hours': round(total_hours, 2),
                'late_count': late_count,
                'total_clock_ins': total_clock_ins,
                'total_clock_outs': total_clock_outs,
                'avg_daily_clock_ins': round(avg_daily_clock_ins or 0, 1),
                'avg_hours': round(total_hours / work_days, 2) if work_days > 0 else 0
            })
        
        conn.close()
        return results
    
    @staticmethod
    def calculate_monthly_hours(employee_id, year, month):
        """計算月度總工時"""
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
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
        
        conn.close()
        return total_hours
    
    @staticmethod
    def calculate_complete_attendance_days(employee_id, year, month):
        """計算完整出勤天數（上下班都打卡2次）"""
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DATE(taiwan_time) as work_date,
                   COUNT(CASE WHEN action_type = 'clock_in' THEN 1 END) as clock_ins,
                   COUNT(CASE WHEN action_type = 'clock_out' THEN 1 END) as clock_outs
            FROM attendance_records 
            WHERE employee_id = ? 
            AND strftime('%Y', taiwan_time) = ? 
            AND strftime('%m', taiwan_time) = ?
            GROUP BY DATE(taiwan_time)
            HAVING clock_ins = 2 AND clock_outs = 2
        ''', (employee_id, str(year), f"{month:02d}"))
        
        complete_days = len(cursor.fetchall())
        conn.close()
        return complete_days
    
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
    def get_department_summary(date=None):
        """部門出勤摘要 - 支援多次打卡統計"""
        if not date:
            date = datetime.now(TW_TZ).strftime('%Y-%m-%d')
        
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                e.department,
                COUNT(DISTINCT e.employee_id) as total_employees,
                COUNT(DISTINCT CASE WHEN ar.action_type = 'clock_in' THEN e.employee_id END) as present_count,
                COUNT(CASE WHEN ar.action_type = 'clock_in' AND ar.status = 'late' THEN 1 END) as late_count,
                AVG(CASE WHEN ar.action_type = 'clock_in' THEN 
                    (SELECT COUNT(*) FROM attendance_records ar2 
                     WHERE ar2.employee_id = e.employee_id 
                     AND DATE(ar2.taiwan_time) = DATE(ar.taiwan_time) 
                     AND ar2.action_type = 'clock_in')
                END) as avg_clock_ins_per_person
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
                'avg_clock_ins_per_person': round(record[4] or 0, 1),
                'attendance_rate': round((record[2] / record[1] * 100), 1) if record[1] > 0 else 0
            }
            for record in records
        ]
    
    @staticmethod
    def get_punch_pattern_analysis(start_date=None, end_date=None):
        """打卡模式分析 - 分析員工的打卡習慣"""
        if not start_date:
            start_date = (datetime.now(TW_TZ) - timedelta(days=30)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now(TW_TZ).strftime('%Y-%m-%d')
        
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                e.name,
                e.department,
                DATE(ar.taiwan_time) as work_date,
                COUNT(CASE WHEN ar.action_type = 'clock_in' THEN 1 END) as daily_clock_ins,
                COUNT(CASE WHEN ar.action_type = 'clock_out' THEN 1 END) as daily_clock_outs,
                GROUP_CONCAT(CASE WHEN ar.action_type = 'clock_in' THEN TIME(ar.taiwan_time) END, ',') as clock_in_times,
                GROUP_CONCAT(CASE WHEN ar.action_type = 'clock_out' THEN TIME(ar.taiwan_time) END, ',') as clock_out_times
            FROM employees e
            JOIN attendance_records ar ON e.employee_id = ar.employee_id
            WHERE DATE(ar.taiwan_time) BETWEEN ? AND ?
            GROUP BY e.employee_id, e.name, e.department, DATE(ar.taiwan_time)
            ORDER BY e.name, work_date
        ''', (start_date, end_date))
        
        records = cursor.fetchall()
        conn.close()
        
        return [
            {
                'name': record[0],
                'department': record[1],
                'date': record[2],
                'clock_ins': record[3],
                'clock_outs': record[4],
                'clock_in_times': record[5].split(',') if record[5] else [],
                'clock_out_times': record[6].split(',') if record[6] else [],
                'pattern': AttendanceReport.analyze_punch_pattern(record[3], record[4])
            }
            for record in records
        ]
    
    @staticmethod
    def analyze_punch_pattern(clock_ins, clock_outs):
        """分析打卡模式"""
        if clock_ins == 0 and clock_outs == 0:
            return "未打卡"
        elif clock_ins == 1 and clock_outs == 1:
            return "單段工時"
        elif clock_ins == 2 and clock_outs == 2:
            return "標準雙段工時"
        elif clock_ins > clock_outs:
            return "未完成下班打卡"
        elif clock_outs > clock_ins:
            return "異常：下班打卡多於上班"
        else:
            return f"自訂模式({clock_ins}進{clock_outs}出)"
    
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
        """遲到統計 - 支援多次打卡"""
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
    def get_employee_detail_report(employee_id, start_date=None, end_date=None):
        """個人詳細出勤報表 - 支援多次打卡"""
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
        
        # 獲取出勤記錄 - 支援多次打卡
        cursor.execute('''
            SELECT 
                DATE(taiwan_time) as work_date,
                GROUP_CONCAT(CASE WHEN action_type = 'clock_in' THEN taiwan_time END, '|') as clock_in_times,
                GROUP_CONCAT(CASE WHEN action_type = 'clock_out' THEN taiwan_time END, '|') as clock_out_times,
                COUNT(CASE WHEN action_type = 'clock_in' THEN 1 END) as clock_in_count,
                COUNT(CASE WHEN action_type = 'clock_out' THEN 1 END) as clock_out_count,
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
        complete_days = 0  # 完整出勤天數（上下班各2次）
        
        for record in records:
            work_date, clock_in_times, clock_out_times, clock_in_count, clock_out_count, status, ip = record
            
            # 解析打卡時間
            clock_ins = [t for t in (clock_in_times or '').split('|') if t]
            clock_outs = [t for t in (clock_out_times or '').split('|') if t]
            
            # 計算當日工時
            working_hours = AttendanceReport.calculate_daily_hours_from_records(clock_ins, clock_outs)
            total_hours += working_hours
            
            if status == 'late':
                late_count += 1
            
            if clock_in_count == 2 and clock_out_count == 2:
                complete_days += 1
            
            # 格式化打卡時間
            clock_in_display = []
            clock_out_display = []
            
            for i, time_str in enumerate(clock_ins):
                if time_str:
                    time_part = time_str.split(' ')[1]
                    label = '上午' if i == 0 else '下午'
                    clock_in_display.append(f'{label}:{time_part}')
            
            for i, time_str in enumerate(clock_outs):
                if time_str:
                    time_part = time_str.split(' ')[1]
                    label = '中午' if i == 0 else '晚上'
                    clock_out_display.append(f'{label}:{time_part}')
            
            daily_records.append({
                'date': work_date,
                'clock_in_times': ' | '.join(clock_in_display) if clock_in_display else '-',
                'clock_out_times': ' | '.join(clock_out_display) if clock_out_display else '-',
                'clock_in_count': clock_in_count,
                'clock_out_count': clock_out_count,
                'working_hours': working_hours,
                'status': AttendanceReport.get_attendance_status(clock_in_count, clock_out_count, status),
                'ip_address': ip or '-'
            })
        
        return {
            'employee_info': {
                'name': employee_info[0],
                'department': employee_info[1],
                'position': employee_info[2]
            },
            'summary': {
                'work_days': len([r for r in daily_records if r['clock_in_count'] > 0]),
                'complete_days': complete_days,
                'total_hours': round(total_hours, 2),
                'late_count': late_count,
                'avg_hours': round(total_hours / len(daily_records), 2) if daily_records else 0,
                'completion_rate': round((complete_days / len(daily_records) * 100), 1) if daily_records else 0
            },
            'daily_records': daily_records
        }
    
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
    def get_working_hours_distribution(start_date=None, end_date=None):
        """工時分布分析"""
        if not start_date:
            start_date = (datetime.now(TW_TZ) - timedelta(days=30)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now(TW_TZ).strftime('%Y-%m-%d')
        
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        # 獲取期間內的所有員工和日期
        cursor.execute('''
            SELECT DISTINCT e.employee_id, e.name, DATE(ar.taiwan_time) as work_date
            FROM employees e
            JOIN attendance_records ar ON e.employee_id = ar.employee_id
            WHERE DATE(ar.taiwan_time) BETWEEN ? AND ?
            ORDER BY e.name, work_date
        ''', (start_date, end_date))
        
        employee_dates = cursor.fetchall()
        
        # 計算每人每日工時分布
        distribution = {
            '0-2小時': 0,
            '2-4小時': 0,
            '4-6小時': 0,
            '6-8小時': 0,
            '8-10小時': 0,
            '10+小時': 0
        }
        
        for employee_id, name, date in employee_dates:
            daily_hours = AttendanceReport.calculate_daily_hours(employee_id, date)
            
            if daily_hours == 0:
                continue
            elif daily_hours <= 2:
                distribution['0-2小時'] += 1
            elif daily_hours <= 4:
                distribution['2-4小時'] += 1
            elif daily_hours <= 6:
                distribution['4-6小時'] += 1
            elif daily_hours <= 8:
                distribution['6-8小時'] += 1
            elif daily_hours <= 10:
                distribution['8-10小時'] += 1
            else:
                distribution['10+小時'] += 1
        
        conn.close()
        return distribution
    
    @staticmethod
    def get_punch_time_analysis(date=None):
        """打卡時間分析"""
        if not date:
            date = datetime.now(TW_TZ).strftime('%Y-%m-%d')
        
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                e.name,
                e.department,
                ar.action_type,
                TIME(ar.taiwan_time) as punch_time,
                CASE 
                    WHEN ar.action_type = 'clock_in' THEN 
                        ROW_NUMBER() OVER (PARTITION BY ar.employee_id, DATE(ar.taiwan_time), ar.action_type ORDER BY ar.timestamp)
                    ELSE 
                        ROW_NUMBER() OVER (PARTITION BY ar.employee_id, DATE(ar.taiwan_time), ar.action_type ORDER BY ar.timestamp)
                END as punch_sequence
            FROM attendance_records ar
            JOIN employees e ON ar.employee_id = e.employee_id
            WHERE DATE(ar.taiwan_time) = ?
            ORDER BY ar.action_type, punch_sequence, punch_time
        ''', (date,))
        
        records = cursor.fetchall()
        conn.close()
        
        # 分析結果
        analysis = {
            'morning_checkin': [],  # 上午上班時間
            'lunch_checkout': [],   # 中午下班時間
            'afternoon_checkin': [], # 下午上班時間  
            'evening_checkout': []   # 晚上下班時間
        }
        
        for record in records:
            name, department, action_type, punch_time, sequence = record
            
            if action_type == 'clock_in' and sequence == 1:
                analysis['morning_checkin'].append({
                    'name': name, 
                    'department': department, 
                    'time': punch_time
                })
            elif action_type == 'clock_out' and sequence == 1:
                analysis['lunch_checkout'].append({
                    'name': name, 
                    'department': department, 
                    'time': punch_time
                })
            elif action_type == 'clock_in' and sequence == 2:
                analysis['afternoon_checkin'].append({
                    'name': name, 
                    'department': department, 
                    'time': punch_time
                })
            elif action_type == 'clock_out' and sequence == 2:
                analysis['evening_checkout'].append({
                    'name': name, 
                    'department': department, 
                    'time': punch_time
                })
        
        return analysis