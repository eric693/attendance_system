# overtime_manager.py - 加班管理模組
import sqlite3
from datetime import datetime, timedelta
import pytz
from models import EmployeeManager

# 台灣時區設定
TW_TZ = pytz.timezone('Asia/Taipei')

class OvertimeManager:
    """加班管理類"""
    
    @staticmethod
    def init_overtime_tables():
        """初始化加班相關資料表"""
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        # 建立加班申請表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS overtime_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT,
                request_date DATE,
                overtime_date DATE,
                start_time TIME,
                end_time TIME,
                hours REAL,
                reason TEXT,
                status TEXT DEFAULT 'pending', -- pending, approved, rejected
                approved_by TEXT,
                approved_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (employee_id) REFERENCES employees (employee_id),
                FOREIGN KEY (approved_by) REFERENCES employees (employee_id)
            )
        ''')
        
        # 建立加班記錄表（已批准的加班）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS overtime_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT,
                overtime_date DATE,
                start_time TIME,
                end_time TIME,
                hours REAL,
                hourly_rate REAL,
                overtime_pay REAL,
                reason TEXT,
                approved_by TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (employee_id) REFERENCES employees (employee_id),
                FOREIGN KEY (approved_by) REFERENCES employees (employee_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def submit_overtime_request(employee_id, overtime_data):
        """提交加班申請"""
        try:
            conn = sqlite3.connect('attendance.db')
            cursor = conn.cursor()
            
            now = datetime.now(TW_TZ)
            overtime_date = overtime_data['overtime_date']
            start_time = overtime_data['start_time']
            end_time = overtime_data['end_time']
            reason = overtime_data.get('reason', '')
            
            # 計算加班時數
            start_dt = datetime.strptime(f"{overtime_date} {start_time}", '%Y-%m-%d %H:%M')
            end_dt = datetime.strptime(f"{overtime_date} {end_time}", '%Y-%m-%d %H:%M')
            
            # 如果結束時間在開始時間之前，表示跨夜
            if end_dt <= start_dt:
                end_dt += timedelta(days=1)
            
            hours = (end_dt - start_dt).total_seconds() / 3600
            
            if hours <= 0 or hours > 24:
                return {
                    'success': False,
                    'message': '加班時數不合理，請檢查時間設定'
                }
            
            # 檢查是否有重複申請
            cursor.execute('''
                SELECT id FROM overtime_requests 
                WHERE employee_id = ? AND overtime_date = ? 
                AND status IN ('pending', 'approved')
            ''', (employee_id, overtime_date))
            
            if cursor.fetchone():
                conn.close()
                return {
                    'success': False,
                    'message': '該日期已有加班申請，請先取消原申請'
                }
            
            # 插入申請記錄
            cursor.execute('''
                INSERT INTO overtime_requests 
                (employee_id, request_date, overtime_date, start_time, end_time, hours, reason)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (employee_id, now.strftime('%Y-%m-%d'), overtime_date, 
                  start_time, end_time, round(hours, 2), reason))
            
            request_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'message': f'加班申請提交成功！\n申請編號：{request_id}\n加班時數：{hours:.1f}小時',
                'request_id': request_id,
                'hours': round(hours, 2)
            }
            
        except Exception as e:
            if conn:
                conn.close()
            return {
                'success': False,
                'message': f'提交失敗：{str(e)}'
            }
    
    @staticmethod
    def get_overtime_requests(employee_id=None, status=None, limit=10):
        """獲取加班申請列表"""
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        query = '''
            SELECT ot.id, ot.employee_id, e.name, ot.overtime_date, 
                   ot.start_time, ot.end_time, ot.hours, ot.reason, 
                   ot.status, ot.created_at, ot.approved_by, ot.approved_at
            FROM overtime_requests ot
            JOIN employees e ON ot.employee_id = e.employee_id
        '''
        
        params = []
        conditions = []
        
        if employee_id:
            conditions.append('ot.employee_id = ?')
            params.append(employee_id)
        
        if status:
            conditions.append('ot.status = ?')
            params.append(status)
        
        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
        
        query += ' ORDER BY ot.created_at DESC'
        
        if limit:
            query += ' LIMIT ?'
            params.append(limit)
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row[0],
                'employee_id': row[1],
                'employee_name': row[2],
                'overtime_date': row[3],
                'start_time': row[4],
                'end_time': row[5],
                'hours': row[6],
                'reason': row[7],
                'status': row[8],
                'created_at': row[9],
                'approved_by': row[10],
                'approved_at': row[11]
            }
            for row in results
        ]
    
    @staticmethod
    def get_employee_overtime_summary(employee_id):
        """獲取員工加班摘要"""
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        # 本月申請統計
        now = datetime.now(TW_TZ)
        month_start = now.replace(day=1).strftime('%Y-%m-%d')
        
        cursor.execute('''
            SELECT status, COUNT(*), SUM(hours) 
            FROM overtime_requests 
            WHERE employee_id = ? AND overtime_date >= ?
            GROUP BY status
        ''', (employee_id, month_start))
        
        stats = {
            'pending': {'count': 0, 'hours': 0},
            'approved': {'count': 0, 'hours': 0},
            'rejected': {'count': 0, 'hours': 0}
        }
        
        for row in cursor.fetchall():
            status, count, hours = row
            if status in stats:
                stats[status] = {'count': count, 'hours': hours or 0}
        
        # 本月已批准的加班費計算
        cursor.execute('''
            SELECT SUM(ot.hours * COALESCE(es.overtime_rate, 300))
            FROM overtime_requests ot
            LEFT JOIN employee_salary es ON ot.employee_id = es.employee_id
            WHERE ot.employee_id = ? AND ot.overtime_date >= ? AND ot.status = 'approved'
        ''', (employee_id, month_start))
        
        estimated_pay = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'month': f"{now.year}年{now.month:02d}月",
            'stats': stats,
            'estimated_overtime_pay': round(estimated_pay, 0)
        }
    
    @staticmethod
    def cancel_overtime_request(request_id, employee_id):
        """取消加班申請"""
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        # 檢查申請是否存在且屬於該員工
        cursor.execute('''
            SELECT status FROM overtime_requests 
            WHERE id = ? AND employee_id = ?
        ''', (request_id, employee_id))
        
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return {
                'success': False,
                'message': '找不到該申請記錄'
            }
        
        status = result[0]
        
        if status == 'approved':
            conn.close()
            return {
                'success': False,
                'message': '已批准的申請無法取消，請聯繫管理員'
            }
        
        if status == 'rejected':
            conn.close()
            return {
                'success': False,
                'message': '已拒絕的申請無法取消'
            }
        
        # 刪除申請
        cursor.execute('''
            DELETE FROM overtime_requests 
            WHERE id = ? AND employee_id = ?
        ''', (request_id, employee_id))
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'message': f'申請 #{request_id} 已成功取消'
        }
    
    @staticmethod
    def approve_overtime_request(request_id, approver_id, action='approve'):
        """批准或拒絕加班申請"""
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        # 檢查申請是否存在
        cursor.execute('''
            SELECT employee_id, overtime_date, hours FROM overtime_requests 
            WHERE id = ? AND status = 'pending'
        ''', (request_id,))
        
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return {
                'success': False,
                'message': '找不到待處理的申請記錄'
            }
        
        employee_id, overtime_date, hours = result
        now = datetime.now(TW_TZ)
        new_status = 'approved' if action == 'approve' else 'rejected'
        
        # 更新申請狀態
        cursor.execute('''
            UPDATE overtime_requests 
            SET status = ?, approved_by = ?, approved_at = ?, updated_at = ?
            WHERE id = ?
        ''', (new_status, approver_id, now.strftime('%Y-%m-%d %H:%M:%S'), 
              now.strftime('%Y-%m-%d %H:%M:%S'), request_id))
        
        # 如果批准，創建加班記錄
        if action == 'approve':
            # 獲取員工加班費率
            cursor.execute('''
                SELECT overtime_rate FROM employee_salary 
                WHERE employee_id = ?
            ''', (employee_id,))
            
            rate_result = cursor.fetchone()
            overtime_rate = rate_result[0] if rate_result else 300
            overtime_pay = hours * overtime_rate
            
            # 獲取完整的申請資訊
            cursor.execute('''
                SELECT start_time, end_time, reason FROM overtime_requests 
                WHERE id = ?
            ''', (request_id,))
            
            request_info = cursor.fetchone()
            start_time, end_time, reason = request_info
            
            cursor.execute('''
                INSERT INTO overtime_records 
                (employee_id, overtime_date, start_time, end_time, hours, 
                 hourly_rate, overtime_pay, reason, approved_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (employee_id, overtime_date, start_time, end_time, hours,
                  overtime_rate, overtime_pay, reason, approver_id))
        
        conn.commit()
        conn.close()
        
        action_text = '批准' if action == 'approve' else '拒絕'
        return {
            'success': True,
            'message': f'加班申請 #{request_id} 已{action_text}'
        }