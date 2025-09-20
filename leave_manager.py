# leave_manager.py - 請假管理模組（修正版）
import sqlite3
from datetime import datetime, timedelta
import pytz
from typing import Dict, List, Optional

# 台灣時區設定
TW_TZ = pytz.timezone('Asia/Taipei')

# 請假類型定義
LEAVE_TYPES = {
    'annual': {
        'name': '特休假',
        'emoji': '🏖️',
        'color': '#4CAF50',
        'requires_proof': False,
        'max_days_per_request': 30,
        'description': '年度特休假，需事先申請'
    },
    'sick': {
        'name': '病假',
        'emoji': '🏥',
        'color': '#FF5722',
        'requires_proof': True,
        'max_days_per_request': 30,
        'description': '因病需要休養，超過3天需診斷證明'
    },
    'personal': {
        'name': '事假',
        'emoji': '📋',
        'color': '#FF9800',
        'requires_proof': False,
        'max_days_per_request': 14,
        'description': '個人事務，不支薪假別'
    },
    'funeral': {
        'name': '喪假',
        'emoji': '🕯️',
        'color': '#757575',
        'requires_proof': True,
        'max_days_per_request': 8,
        'description': '直系親屬喪事，需相關證明文件'
    },
    'maternity': {
        'name': '產假',
        'emoji': '👶',
        'color': '#E91E63',
        'requires_proof': True,
        'max_days_per_request': 56,
        'description': '產前產後假期，需醫院證明'
    },
    'paternity': {
        'name': '陪產假',
        'emoji': '👨‍👶',
        'color': '#2196F3',
        'requires_proof': True,
        'max_days_per_request': 5,
        'description': '配偶生產陪產假期'
    },
    'official': {
        'name': '公假',
        'emoji': '🏛️',
        'color': '#9C27B0',
        'requires_proof': True,
        'max_days_per_request': 30,
        'description': '公務出差、訓練等公假'
    },
    'compensatory': {
        'name': '補休',
        'emoji': '⚖️',
        'color': '#607D8B',
        'requires_proof': False,
        'max_days_per_request': 10,
        'description': '加班換取之補休假期'
    },
    'marriage': {
        'name': '婚假',
        'emoji': '💒',
        'color': '#E91E63',
        'requires_proof': True,
        'max_days_per_request': 8,
        'description': '結婚假期，需結婚證書'
    }
}

# 請假狀態定義
LEAVE_STATUS = {
    'pending': {'name': '待審核', 'emoji': '⏳', 'color': '#FF9800'},
    'approved': {'name': '已批准', 'emoji': '✅', 'color': '#4CAF50'},
    'rejected': {'name': '已拒絕', 'emoji': '❌', 'color': '#F44336'},
    'cancelled': {'name': '已取消', 'emoji': '🚫', 'color': '#757575'},
    'expired': {'name': '已過期', 'emoji': '⏰', 'color': '#9E9E9E'}
}

class LeaveManager:
    """請假管理類"""
    
    @staticmethod
    def init_leave_tables():
        """初始化請假相關資料表"""
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        # 建立請假申請表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS leave_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT,
                leave_type TEXT,
                start_date DATE,
                end_date DATE,
                start_time TIME,
                end_time TIME,
                total_days REAL,
                total_hours REAL,
                reason TEXT,
                proof_document TEXT,
                status TEXT DEFAULT 'pending',
                approved_by TEXT,
                approved_at TIMESTAMP,
                rejected_reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 建立員工請假額度表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS employee_leave_quotas (
                employee_id TEXT,
                year INTEGER,
                leave_type TEXT,
                allocated_days REAL DEFAULT 0,
                used_days REAL DEFAULT 0,
                remaining_days REAL DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (employee_id, year, leave_type)
            )
        ''')
        
        # 建立請假審核記錄表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS leave_approval_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                leave_request_id INTEGER,
                reviewer_id TEXT,
                action TEXT, -- approve, reject, cancel
                reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def submit_leave_request(employee_id: str, leave_data: Dict) -> Dict:
        """提交請假申請"""
        try:
            conn = sqlite3.connect('attendance.db')
            cursor = conn.cursor()
            
            now = datetime.now(TW_TZ)
            leave_type = leave_data['leave_type']
            start_date = leave_data['start_date']
            end_date = leave_data.get('end_date', start_date)
            start_time = leave_data.get('start_time', '09:00')
            end_time = leave_data.get('end_time', '18:00')
            reason = leave_data.get('reason', '')
            
            # 驗證請假類型
            if leave_type not in LEAVE_TYPES:
                return {
                    'success': False,
                    'message': f'無效的請假類型：{leave_type}'
                }
            
            # 計算請假天數和時數
            start_dt = datetime.strptime(f"{start_date} {start_time}", '%Y-%m-%d %H:%M')
            end_dt = datetime.strptime(f"{end_date} {end_time}", '%Y-%m-%d %H:%M')
            
            if end_dt <= start_dt:
                return {
                    'success': False,
                    'message': '結束時間必須晚於開始時間'
                }
            
            # 計算請假時數和天數
            total_hours = (end_dt - start_dt).total_seconds() / 3600
            total_days = total_hours / 8  # 假設一天工作8小時
            
            # 檢查是否超過單次申請限制
            max_days = LEAVE_TYPES[leave_type]['max_days_per_request']
            if total_days > max_days:
                return {
                    'success': False,
                    'message': f'{LEAVE_TYPES[leave_type]["name"]}單次申請不可超過{max_days}天'
                }
            
            # 檢查是否有衝突的請假申請
            cursor.execute('''
                SELECT id FROM leave_requests 
                WHERE employee_id = ? 
                AND status IN ('pending', 'approved')
                AND NOT (end_date < ? OR start_date > ?)
            ''', (employee_id, start_date, end_date))
            
            if cursor.fetchone():
                return {
                    'success': False,
                    'message': '該時段已有其他請假申請'
                }
            
            # 插入請假申請
            cursor.execute('''
                INSERT INTO leave_requests 
                (employee_id, leave_type, start_date, end_date, start_time, end_time,
                 total_days, total_hours, reason, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (employee_id, leave_type, start_date, end_date, start_time, end_time,
                  round(total_days, 2), round(total_hours, 2), reason, 'pending'))
            
            request_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'message': f'{LEAVE_TYPES[leave_type]["name"]}申請提交成功！\n申請編號：{request_id}\n請假時間：{total_days:.1f}天',
                'request_id': request_id,
                'total_days': round(total_days, 2),
                'total_hours': round(total_hours, 2)
            }
            
        except Exception as e:
            if conn:
                conn.close()
            return {
                'success': False,
                'message': f'提交失敗：{str(e)}'
            }
    
    @staticmethod
    def get_leave_requests(employee_id: str = None, status: str = None, limit: int = 10) -> List[Dict]:
        """獲取請假申請列表"""
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        # 修正查詢，移除對 employees 表的依賴
        query = '''
            SELECT lr.id, lr.employee_id, lr.employee_id as name, lr.leave_type, lr.start_date, lr.end_date,
                   lr.start_time, lr.end_time, lr.total_days, lr.total_hours, lr.reason,
                   lr.status, lr.created_at, lr.approved_by, lr.approved_at, lr.rejected_reason
            FROM leave_requests lr
        '''
        
        params = []
        conditions = []
        
        if employee_id:
            conditions.append('lr.employee_id = ?')
            params.append(employee_id)
        
        if status:
            conditions.append('lr.status = ?')
            params.append(status)
        
        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
        
        query += ' ORDER BY lr.created_at DESC'
        
        if limit:
            query += ' LIMIT ?'
            params.append(limit)
        
        try:
            cursor.execute(query, params)
            results = cursor.fetchall()
            conn.close()
            
            return [
                {
                    'id': row[0],
                    'employee_id': row[1],
                    'employee_name': row[2] or row[1],  # 如果沒有名字就用員工ID
                    'leave_type': row[3],
                    'leave_type_name': LEAVE_TYPES.get(row[3], {}).get('name', row[3]),
                    'leave_type_emoji': LEAVE_TYPES.get(row[3], {}).get('emoji', '📋'),
                    'start_date': row[4],
                    'end_date': row[5],
                    'start_time': row[6],
                    'end_time': row[7],
                    'total_days': row[8] or 0,
                    'total_hours': row[9] or 0,
                    'reason': row[10] or '',
                    'status': row[11],
                    'status_name': LEAVE_STATUS.get(row[11], {}).get('name', row[11]),
                    'status_emoji': LEAVE_STATUS.get(row[11], {}).get('emoji', ''),
                    'created_at': row[12],
                    'approved_by': row[13],
                    'approved_at': row[14],
                    'rejected_reason': row[15]
                }
                for row in results
            ]
        except Exception as e:
            conn.close()
            print(f"Database error in get_leave_requests: {e}")
            return []
    
    @staticmethod
    def approve_leave_request(request_id: int, approver_id: str, action: str = 'approve', reason: str = '') -> Dict:
        """審核請假申請"""
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        try:
            # 檢查申請是否存在
            cursor.execute('''
                SELECT employee_id, leave_type, total_days, status FROM leave_requests 
                WHERE id = ?
            ''', (request_id,))
            
            result = cursor.fetchone()
            if not result:
                return {
                    'success': False,
                    'message': '找不到該請假申請'
                }
            
            employee_id, leave_type, total_days, current_status = result
            
            if current_status != 'pending':
                return {
                    'success': False,
                    'message': f'該申請已處理，目前狀態：{LEAVE_STATUS.get(current_status, {}).get("name", current_status)}'
                }
            
            now = datetime.now(TW_TZ)
            new_status = 'approved' if action == 'approve' else 'rejected'
            
            # 更新申請狀態
            if action == 'approve':
                cursor.execute('''
                    UPDATE leave_requests 
                    SET status = ?, approved_by = ?, approved_at = ?, updated_at = ?
                    WHERE id = ?
                ''', (new_status, approver_id, now.strftime('%Y-%m-%d %H:%M:%S'), 
                      now.strftime('%Y-%m-%d %H:%M:%S'), request_id))
                
                # 更新員工請假額度（如果是特休假等有額度限制的假別）
                if leave_type in ['annual', 'compensatory']:
                    LeaveManager.update_leave_quota(employee_id, leave_type, total_days)
            
            else:  # reject
                cursor.execute('''
                    UPDATE leave_requests 
                    SET status = ?, rejected_reason = ?, updated_at = ?
                    WHERE id = ?
                ''', (new_status, reason, now.strftime('%Y-%m-%d %H:%M:%S'), request_id))
            
            # 記錄審核日誌
            cursor.execute('''
                INSERT INTO leave_approval_logs 
                (leave_request_id, reviewer_id, action, reason)
                VALUES (?, ?, ?, ?)
            ''', (request_id, approver_id, action, reason))
            
            conn.commit()
            
            action_text = '批准' if action == 'approve' else '拒絕'
            return {
                'success': True,
                'message': f'請假申請 #{request_id} 已{action_text}'
            }
            
        except Exception as e:
            conn.rollback()
            return {
                'success': False,
                'message': f'審核失敗：{str(e)}'
            }
        finally:
            conn.close()
    
    @staticmethod
    def cancel_leave_request(request_id: int, employee_id: str) -> Dict:
        """取消請假申請"""
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        try:
            # 檢查申請是否存在且屬於該員工
            cursor.execute('''
                SELECT status, leave_type, total_days FROM leave_requests 
                WHERE id = ? AND employee_id = ?
            ''', (request_id, employee_id))
            
            result = cursor.fetchone()
            if not result:
                return {
                    'success': False,
                    'message': '找不到該請假申請記錄'
                }
            
            status, leave_type, total_days = result
            
            if status not in ['pending', 'approved']:
                return {
                    'success': False,
                    'message': f'無法取消已{LEAVE_STATUS.get(status, {}).get("name", status)}的申請'
                }
            
            now = datetime.now(TW_TZ)
            
            # 更新狀態為已取消
            cursor.execute('''
                UPDATE leave_requests 
                SET status = 'cancelled', updated_at = ?
                WHERE id = ?
            ''', (now.strftime('%Y-%m-%d %H:%M:%S'), request_id))
            
            # 如果是已批准的假期，需要恢復額度
            if status == 'approved' and leave_type in ['annual', 'compensatory']:
                LeaveManager.restore_leave_quota(employee_id, leave_type, total_days)
            
            # 記錄取消日誌
            cursor.execute('''
                INSERT INTO leave_approval_logs 
                (leave_request_id, reviewer_id, action, reason)
                VALUES (?, ?, ?, ?)
            ''', (request_id, employee_id, 'cancel', '員工主動取消'))
            
            conn.commit()
            
            return {
                'success': True,
                'message': f'請假申請 #{request_id} 已成功取消'
            }
            
        except Exception as e:
            conn.rollback()
            return {
                'success': False,
                'message': f'取消失敗：{str(e)}'
            }
        finally:
            conn.close()
    
    @staticmethod
    def get_employee_leave_summary(employee_id: str) -> Dict:
        """獲取員工請假摘要"""
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        now = datetime.now(TW_TZ)
        current_year = now.year
        current_month = f"{now.year}-{now.month:02d}"
        
        try:
            # 本年度各類型請假統計
            cursor.execute('''
                SELECT leave_type, status, COUNT(*), SUM(total_days) 
                FROM leave_requests 
                WHERE employee_id = ? 
                AND strftime('%Y', start_date) = ?
                GROUP BY leave_type, status
            ''', (employee_id, str(current_year)))
            
            stats = {}
            for row in cursor.fetchall():
                leave_type, status, count, days = row
                if leave_type not in stats:
                    stats[leave_type] = {
                        'pending': {'count': 0, 'days': 0},
                        'approved': {'count': 0, 'days': 0},
                        'rejected': {'count': 0, 'days': 0}
                    }
                stats[leave_type][status] = {'count': count, 'days': days or 0}
            
            # 獲取請假額度信息
            cursor.execute('''
                SELECT leave_type, allocated_days, used_days, remaining_days 
                FROM employee_leave_quotas 
                WHERE employee_id = ? AND year = ?
            ''', (employee_id, current_year))
            
            quotas = {}
            for row in cursor.fetchall():
                leave_type, allocated, used, remaining = row
                quotas[leave_type] = {
                    'allocated': allocated,
                    'used': used,
                    'remaining': remaining
                }
            
            # 本月請假統計
            cursor.execute('''
                SELECT COUNT(*), SUM(total_days) 
                FROM leave_requests 
                WHERE employee_id = ? 
                AND strftime('%Y-%m', start_date) = ?
                AND status = 'approved'
            ''', (employee_id, current_month))
            
            month_result = cursor.fetchone()
            month_count = month_result[0] if month_result else 0
            month_days = month_result[1] if month_result and month_result[1] else 0
            
            conn.close()
            
            return {
                'year': current_year,
                'month': f"{now.month:02d}月",
                'stats': stats,
                'quotas': quotas,
                'this_month': {
                    'count': month_count,
                    'days': round(month_days, 1)
                }
            }
            
        except Exception as e:
            conn.close()
            print(f"Database error in get_employee_leave_summary: {e}")
            return {
                'year': current_year,
                'month': f"{now.month:02d}月",
                'stats': {},
                'quotas': {},
                'this_month': {'count': 0, 'days': 0}
            }
    
    @staticmethod
    def update_leave_quota(employee_id: str, leave_type: str, used_days: float) -> None:
        """更新請假額度"""
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        current_year = datetime.now(TW_TZ).year
        now = datetime.now(TW_TZ).strftime('%Y-%m-%d %H:%M:%S')
        
        try:
            # 檢查是否已有額度記錄
            cursor.execute('''
                SELECT allocated_days, used_days FROM employee_leave_quotas 
                WHERE employee_id = ? AND year = ? AND leave_type = ?
            ''', (employee_id, current_year, leave_type))
            
            result = cursor.fetchone()
            if result:
                allocated, current_used = result
                new_used = current_used + used_days
                remaining = allocated - new_used
                
                cursor.execute('''
                    UPDATE employee_leave_quotas 
                    SET used_days = ?, remaining_days = ?, updated_at = ?
                    WHERE employee_id = ? AND year = ? AND leave_type = ?
                ''', (new_used, remaining, now, employee_id, current_year, leave_type))
            else:
                # 創建新的額度記錄（預設分配額度）
                default_allocations = {
                    'annual': 7,  # 預設特休7天
                    'compensatory': 0  # 補休需要從加班累積
                }
                allocated = default_allocations.get(leave_type, 0)
                remaining = allocated - used_days
                
                cursor.execute('''
                    INSERT INTO employee_leave_quotas 
                    (employee_id, year, leave_type, allocated_days, used_days, remaining_days, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (employee_id, current_year, leave_type, allocated, used_days, remaining, now))
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Database error in update_leave_quota: {e}")
        finally:
            conn.close()
    
    @staticmethod
    def restore_leave_quota(employee_id: str, leave_type: str, restore_days: float) -> None:
        """恢復請假額度"""
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        current_year = datetime.now(TW_TZ).year
        now = datetime.now(TW_TZ).strftime('%Y-%m-%d %H:%M:%S')
        
        try:
            cursor.execute('''
                UPDATE employee_leave_quotas 
                SET used_days = used_days - ?, 
                    remaining_days = remaining_days + ?,
                    updated_at = ?
                WHERE employee_id = ? AND year = ? AND leave_type = ?
            ''', (restore_days, restore_days, now, employee_id, current_year, leave_type))
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Database error in restore_leave_quota: {e}")
        finally:
            conn.close()
    
    @staticmethod
    def get_available_leave_types() -> Dict:
        """獲取可用的請假類型"""
        return LEAVE_TYPES
    
    @staticmethod
    def get_pending_approvals(limit: int = 20) -> List[Dict]:
        """獲取待審核的請假申請"""
        try:
            return LeaveManager.get_leave_requests(status='pending', limit=limit)
        except Exception as e:
            print(f"Error in get_pending_approvals: {e}")
            return []