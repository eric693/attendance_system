# admin_leave_routes.py - 管理後台請假審核路由（移除管理員權限檢查）
from flask import request, jsonify, session
from datetime import datetime
import pytz
import sqlite3
import logging
from contextlib import contextmanager
from leave_manager import LeaveManager, LEAVE_TYPES, LEAVE_STATUS
from models import EmployeeManager

# 台灣時區設定
TW_TZ = pytz.timezone('Asia/Taipei')

# 設定日誌
logger = logging.getLogger(__name__)

@contextmanager
def get_db_connection():
    """資料庫連線上下文管理器"""
    conn = None
    try:
        conn = sqlite3.connect('attendance.db', timeout=30.0)
        conn.row_factory = sqlite3.Row
        yield conn
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        if conn:
            conn.close()

def setup_leave_admin_routes(app):
    """設定請假管理相關的管理後台路由"""
    
    @app.route('/api/leave/requests', methods=['GET'])
    def get_leave_requests():
        """獲取請假申請列表"""
        try:
            status = request.args.get('status', '')
            employee_id = request.args.get('employee_id', '')
            limit = min(int(request.args.get('limit', 50)), 200)  # 限制最大值
            
            # 獲取請假申請
            requests = LeaveManager.get_leave_requests(
                employee_id=employee_id if employee_id else None,
                status=status if status else None,
                limit=limit
            )
            
            # 添加類型和狀態的中文名稱
            for req in requests:
                req['leave_type_display'] = LEAVE_TYPES.get(
                    req['leave_type'], {}
                ).get('name', req['leave_type'])
                req['status_display'] = LEAVE_STATUS.get(
                    req['status'], {}
                ).get('name', req['status'])
                req['color'] = LEAVE_STATUS.get(
                    req['status'], {}
                ).get('color', '#666666')
            
            return jsonify({
                'success': True,
                'data': requests,
                'count': len(requests)
            })
            
        except ValueError as e:
            return jsonify({
                'success': False,
                'error': f'參數格式錯誤: {str(e)}'
            }), 400
        except Exception as e:
            logger.error(f"Get leave requests error: {e}")
            return jsonify({
                'success': False,
                'error': '獲取請假申請失敗'
            }), 500
    
    @app.route('/api/leave/pending', methods=['GET'])
    def get_pending_leave_requests():
        """獲取待審核的請假申請"""
        try:
            limit = min(int(request.args.get('limit', 100)), 200)
            requests = LeaveManager.get_pending_approvals(limit=limit)
            
            return jsonify({
                'success': True,
                'data': requests,
                'count': len(requests)
            })
        except Exception as e:
            logger.error(f"Get pending leave requests error: {e}")
            return jsonify({
                'success': False,
                'error': '獲取待審核申請失敗'
            }), 500
    
    @app.route('/api/leave/approve', methods=['POST'])
    def approve_leave_request():
        """審核請假申請"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    'success': False,
                    'error': '缺少請求數據'
                }), 400
            
            request_id = data.get('request_id')
            action = data.get('action', '').strip()
            reason = data.get('reason', '').strip()
            
            # 驗證輸入
            if not request_id or not isinstance(request_id, (int, str)):
                return jsonify({
                    'success': False,
                    'error': '請假申請ID無效'
                }), 400
                
            if action not in ['approve', 'reject']:
                return jsonify({
                    'success': False,
                    'error': '無效的審核動作'
                }), 400
            
            # 獲取審核者ID（從session或設定預設值）
            approver_id = session.get('employee_id', 'ADMIN001')
            
            result = LeaveManager.approve_leave_request(
                request_id=int(request_id),
                approver_id=approver_id,
                action=action,
                reason=reason
            )
            
            return jsonify(result)
            
        except ValueError as e:
            return jsonify({
                'success': False,
                'error': f'數據格式錯誤: {str(e)}'
            }), 400
        except Exception as e:
            logger.error(f"Approve leave request error: {e}")
            return jsonify({
                'success': False,
                'error': '審核請假申請失敗'
            }), 500

    @app.route('/api/overtime/approve/<int:request_id>', methods=['POST'])
    def approve_overtime_request_route(request_id):
        """批准加班申請路由（給加班管理用）"""
        try:
            data = request.get_json() or {}
            action = data.get('action', 'approve')
            comment = data.get('comment', '')
            
            if action not in ['approve', 'reject']:
                return jsonify({
                    'success': False,
                    'message': '無效的審核動作'
                }), 400
            
            # 這裡需要導入 OvertimeManager
            from overtime_manager import OvertimeManager
            
            result = OvertimeManager.approve_overtime_request(
                request_id, 
                session.get('employee_id', 'ADMIN001'),
                action
            )
            
            return jsonify(result)
            
        except ImportError:
            return jsonify({
                'success': False,
                'message': '加班管理模組未找到'
            }), 500
        except Exception as e:
            logger.error(f"Approve overtime error: {e}")
            return jsonify({
                'success': False,
                'message': f'審核加班申請失敗: {str(e)}'
            }), 500

    @app.route('/api/overtime/stats', methods=['GET'])
    def get_overtime_stats_route():
        """獲取加班統計數據"""
        try:
            from overtime_manager import OvertimeManager
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # 待審核統計
                cursor.execute('SELECT COUNT(*) FROM overtime_requests WHERE status = "pending"')
                pending_count = cursor.fetchone()[0] if cursor.fetchone() else 0
                
                # 本月統計
                now = datetime.now()
                month_start = now.replace(day=1).strftime('%Y-%m-%d')
                
                cursor.execute('''
                    SELECT status, COUNT(*), COALESCE(SUM(hours), 0)
                    FROM overtime_requests 
                    WHERE overtime_date >= ?
                    GROUP BY status
                ''', (month_start,))
                
                monthly_stats = {}
                for row in cursor.fetchall():
                    status, count, hours = row
                    monthly_stats[status] = {
                        'count': count or 0,
                        'hours': round(hours or 0, 1)
                    }
                
                # 預估本月加班費
                cursor.execute('''
                    SELECT COALESCE(SUM(ot.hours * 300), 0)
                    FROM overtime_requests ot
                    WHERE ot.overtime_date >= ? AND ot.status = 'approved'
                ''', (month_start,))
                
                estimated_cost = cursor.fetchone()[0] or 0
                
                return jsonify({
                    'success': True,
                    'data': {
                        'pending_count': pending_count,
                        'monthly_stats': monthly_stats,
                        'estimated_monthly_cost': round(estimated_cost, 0),
                        'month': f"{now.year}年{now.month:02d}月"
                    }
                })
                
        except ImportError:
            return jsonify({
                'success': False,
                'message': '加班管理模組未找到'
            }), 500
        except Exception as e:
            logger.error(f"Get overtime stats error: {e}")
            return jsonify({
                'success': False,
                'message': f'獲取加班統計失敗: {str(e)}'
            }), 500

    @app.route('/api/overtime/requests', methods=['GET'])
    def get_overtime_requests_route():
        """獲取加班申請列表"""
        try:
            from overtime_manager import OvertimeManager
            
            status = request.args.get('status', 'pending')
            limit = min(int(request.args.get('limit', 50)), 200)
            
            if status == 'all':
                requests = OvertimeManager.get_overtime_requests(status=None, limit=limit)
            else:
                requests = OvertimeManager.get_overtime_requests(status=status, limit=limit)
            
            return jsonify({
                'success': True,
                'data': requests,
                'count': len(requests)
            })
            
        except ImportError:
            return jsonify({
                'success': False,
                'message': '加班管理模組未找到'
            }), 500
        except Exception as e:
            logger.error(f"Get overtime requests error: {e}")
            return jsonify({
                'success': False,
                'message': f'獲取加班申請失敗: {str(e)}'
            }), 500
        
    @app.route('/api/leave/types', methods=['GET'])
    def get_leave_types():
        """獲取請假類型定義"""
        try:
            return jsonify({
                'success': True,
                'data': LEAVE_TYPES
            })
        except Exception as e:
            logger.error(f"Get leave types error: {e}")
            return jsonify({
                'success': False,
                'error': '獲取請假類型失敗'
            }), 500
    
    @app.route('/api/leave/statistics', methods=['GET'])
    def get_leave_statistics():
        """獲取請假統計"""
        try:
            year = request.args.get('year', datetime.now(TW_TZ).year)
            month = request.args.get('month', datetime.now(TW_TZ).month)
            
            # 轉換為整數
            try:
                year = int(year)
                month = int(month)
            except ValueError:
                year = datetime.now(TW_TZ).year
                month = datetime.now(TW_TZ).month
            
            # 獲取所有請假申請
            all_requests = LeaveManager.get_leave_requests(limit=1000)
            
            # 統計數據
            stats = {
                'total_requests': len(all_requests),
                'pending_count': len([r for r in all_requests if r['status'] == 'pending']),
                'approved_count': len([r for r in all_requests if r['status'] == 'approved']),
                'rejected_count': len([r for r in all_requests if r['status'] == 'rejected']),
                'by_type': {},
                'by_department': {},
                'recent_requests': all_requests[:10]  # 最近10筆申請
            }
            
            # 按假別統計
            for req in all_requests:
                leave_type = req['leave_type']
                if leave_type not in stats['by_type']:
                    stats['by_type'][leave_type] = {
                        'name': LEAVE_TYPES.get(leave_type, {}).get('name', leave_type),
                        'count': 0,
                        'approved_days': 0
                    }
                stats['by_type'][leave_type]['count'] += 1
                if req['status'] == 'approved':
                    stats['by_type'][leave_type]['approved_days'] += req.get('total_days', 0)
            
            return jsonify({
                'success': True,
                'data': stats
            })
            
        except Exception as e:
            logger.error(f"Get leave statistics error: {e}")
            return jsonify({
                'success': False,
                'error': '獲取請假統計失敗'
            }), 500
    
    @app.route('/api/leave/quotas', methods=['GET'])
    def get_leave_quotas():
        """獲取員工請假額度"""
        try:
            employee_id = request.args.get('employee_id')
            
            if not employee_id:
                return jsonify({
                    'success': False,
                    'error': '需要員工ID'
                }), 400
            
            summary = LeaveManager.get_employee_leave_summary(employee_id)
            return jsonify({
                'success': True,
                'data': summary
            })
            
        except Exception as e:
            logger.error(f"Get leave quotas error: {e}")
            return jsonify({
                'success': False,
                'error': '獲取請假額度失敗'
            }), 500
    
    @app.route('/api/leave/export', methods=['GET'])
    def export_leave_data():
        """匯出請假數據為CSV"""
        try:
            import csv
            import io
            from flask import Response
            
            status = request.args.get('status', '')
            start_date = request.args.get('start_date', '')
            end_date = request.args.get('end_date', '')
            
            # 獲取請假申請
            requests = LeaveManager.get_leave_requests(
                status=status if status else None,
                limit=1000
            )
            
            if not requests:
                return jsonify({
                    'success': False,
                    'error': '沒有數據可匯出'
                }), 400
            
            # 創建CSV
            output = io.StringIO()
            writer = csv.writer(output)
            
            # 寫入標題
            writer.writerow([
                '申請編號', '員工編號', '員工姓名', '假別類型', '開始日期', '結束日期',
                '請假天數', '請假時數', '申請原因', '狀態', '申請時間', '審核者', '審核時間'
            ])
            
            # 寫入數據
            for req in requests:
                writer.writerow([
                    req.get('id', ''),
                    req.get('employee_id', ''),
                    req.get('employee_name', ''),
                    req.get('leave_type_name', ''),
                    req.get('start_date', ''),
                    req.get('end_date', ''),
                    req.get('total_days', 0),
                    req.get('total_hours', 0),
                    req.get('reason', ''),
                    req.get('status_name', ''),
                    req.get('created_at', ''),
                    req.get('approved_by', ''),
                    req.get('approved_at', '')
                ])
            
            output.seek(0)
            
            # 創建回應
            response = Response(
                output.getvalue(),
                mimetype='text/csv',
                headers={
                    'Content-Disposition': f'attachment; filename=leave_requests_{datetime.now(TW_TZ).strftime("%Y%m%d")}.csv'
                }
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Export leave data error: {e}")
            return jsonify({
                'success': False,
                'error': '匯出數據失敗'
            }), 500