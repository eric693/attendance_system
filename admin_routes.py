# admin_routes.py - 管理後台路由模組 (加入出勤報表與員工薪資查詢)
from flask import session, request, jsonify, render_template_string, Response
from functools import wraps
import sqlite3
from datetime import datetime, timedelta
import pytz
from models import EmployeeManager, CompanySettings
from network_security import NetworkSecurity
from templates import INDEX_TEMPLATE, ADMIN_TEMPLATE
from attendance_report import AttendanceReport

# 台灣時區設定
TW_TZ = pytz.timezone('Asia/Taipei')

# 權限裝飾器
def require_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'employee_id' not in session:
            return jsonify({'error': '請先登入'}), 401
        
        user_role = EmployeeManager.get_employee_role(session['employee_id'])
        if user_role != 'ADMIN':
            return jsonify({'error': '需要管理員權限'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

# 新增：員工身份驗證裝飾器（可查看自己的薪資）
def require_employee_or_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'employee_id' not in session:
            return jsonify({'error': '請先登入'}), 401
        
        return f(*args, **kwargs)
    return decorated_function

def setup_admin_routes(app):
    """設定管理後台路由"""
    
    @app.route('/')
    def index():
        return render_template_string(INDEX_TEMPLATE)

    @app.route('/admin')
    def admin_dashboard():
        return render_template_string(ADMIN_TEMPLATE)

    @app.route('/login', methods=['POST'])
    def admin_login():
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        # 簡化登入驗證
        if username == 'admin' and password == 'admin123':
            session['employee_id'] = 'ADMIN001'
            session['role'] = 'ADMIN'
            return jsonify({'success': True})
        
        return jsonify({'success': False, 'message': '帳號或密碼錯誤'}), 401

    @app.route('/api/employees', methods=['GET', 'POST'])
    @require_admin
    def manage_employees():
        if request.method == 'GET':
            conn = sqlite3.connect('attendance.db')
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM employees WHERE status = "active"')
            employees = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            conn.close()
            
            return jsonify([dict(zip(columns, row)) for row in employees])
        
        elif request.method == 'POST':
            # 新增員工
            data = request.get_json()
            
            try:
                employee_id = EmployeeManager.create_employee({
                    'name': data['name'],
                    'email': data.get('email'),
                    'department': data.get('department'),
                    'position': data.get('position'),
                    'role': data.get('role', 'EMPLOYEE'),
                    'line_user_id': data.get('line_user_id', '')
                })
                
                return jsonify({
                    'success': True, 
                    'message': '員工新增成功',
                    'employee_id': employee_id
                })
                
            except Exception as e:
                return jsonify({
                    'success': False, 
                    'message': f'新增失敗：{str(e)}'
                }), 400

    @app.route('/api/pending-registrations')
    @require_admin  
    def get_pending_registrations():
        """取得待註冊的用戶列表"""
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT line_user_id, name, department, step, created_at 
            FROM pending_registrations 
            ORDER BY created_at DESC
        ''')
        pending = cursor.fetchall()
        columns = ['line_user_id', 'name', 'department', 'step', 'created_at']
        conn.close()
        
        return jsonify([dict(zip(columns, row)) for row in pending])

    @app.route('/api/network/status')
    def check_network_api():
        """API版本的網路檢查"""
        result = NetworkSecurity.check_punch_network()
        return jsonify(result)

    @app.route('/api/network/settings', methods=['GET', 'POST'])
    @require_admin
    def network_settings_api():
        if request.method == 'GET':
            # 取得當前網路設定
            settings = {
                'allowed_networks': CompanySettings.get_setting('allowed_networks', ''),
                'network_check_enabled': CompanySettings.get_setting('network_check_enabled', 'true'),
                'current_ip': NetworkSecurity.get_client_ip()
            }
            return jsonify(settings)
        
        elif request.method == 'POST':
            # 更新網路設定
            data = request.get_json()
            
            CompanySettings.update_setting(
                'allowed_networks', 
                data.get('allowed_networks', ''),
                session.get('employee_id', 'ADMIN001')
            )
            
            CompanySettings.update_setting(
                'network_check_enabled',
                data.get('network_check_enabled', 'true'),
                session.get('employee_id', 'ADMIN001')
            )
            
            return jsonify({'success': True, 'message': '網路設定更新成功'})

    @app.route('/api/attendance/stats')
    @require_admin
    def get_attendance_stats():
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        today = datetime.now(TW_TZ).strftime('%Y-%m-%d')
        
        # 今日出勤統計
        cursor.execute('''
            SELECT COUNT(DISTINCT employee_id) FROM attendance_records 
            WHERE DATE(taiwan_time) = ? AND action_type = 'clock_in'
        ''', (today,))
        today_checkin = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM employees WHERE status = "active"')
        total_employees = cursor.fetchone()[0]
        
        # 網路違規統計
        cursor.execute('''
            SELECT COUNT(*) FROM attendance_records 
            WHERE DATE(taiwan_time) = ? AND status = 'network_violation'
        ''', (today,))
        network_violations = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'today_checkin': today_checkin,
            'total_employees': total_employees,
            'network_violations': network_violations,
            'attendance_rate': round((today_checkin / total_employees * 100) if total_employees > 0 else 0, 1)
        })

    @app.route('/api/overtime/requests', methods=['GET'])
    @require_admin
    def get_overtime_requests():
        """獲取加班申請列表"""
        status = request.args.get('status', 'pending')  # pending, approved, rejected, all
        limit = int(request.args.get('limit', 50))
        
        try:
            if status == 'all':
                requests = OvertimeManager.get_overtime_requests(status=None, limit=limit)
            else:
                requests = OvertimeManager.get_overtime_requests(status=status, limit=limit)
            
            return jsonify({
                'success': True,
                'data': requests
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400
    
    @app.route('/api/overtime/approve/<int:request_id>', methods=['POST'])
    @require_admin
    def approve_overtime_request(request_id):
        """批准加班申請"""
        data = request.get_json()
        action = data.get('action', 'approve')  # approve or reject
        
        try:
            result = OvertimeManager.approve_overtime_request(
                request_id, 
                session.get('employee_id', 'ADMIN001'),
                action
            )
            
            return jsonify(result)
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400
    
    @app.route('/api/overtime/batch-approve', methods=['POST'])
    @require_admin
    def batch_approve_overtime():
        """批量處理加班申請"""
        data = request.get_json()
        request_ids = data.get('request_ids', [])
        action = data.get('action', 'approve')  # approve or reject
        
        if not request_ids:
            return jsonify({
                'success': False,
                'message': '未選擇要處理的申請'
            }), 400
        
        try:
            results = []
            success_count = 0
            
            for req_id in request_ids:
                try:
                    result = OvertimeManager.approve_overtime_request(
                        req_id,
                        session.get('employee_id', 'ADMIN001'),
                        action
                    )
                    
                    if result['success']:
                        success_count += 1
                    
                    results.append({
                        'request_id': req_id,
                        'success': result['success'],
                        'message': result['message']
                    })
                    
                except Exception as e:
                    results.append({
                        'request_id': req_id,
                        'success': False,
                        'message': str(e)
                    })
            
            action_text = '批准' if action == 'approve' else '拒絕'
            
            return jsonify({
                'success': True,
                'message': f'批量{action_text}完成：成功 {success_count}/{len(request_ids)} 筆',
                'results': results
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'批量處理失敗：{str(e)}'
            }), 400
    
    @app.route('/api/overtime/stats')
    @require_admin
    def get_overtime_stats():
        """獲取加班統計數據"""
        try:
            conn = sqlite3.connect('attendance.db')
            cursor = conn.cursor()
            
            # 待審核統計
            cursor.execute('SELECT COUNT(*) FROM overtime_requests WHERE status = "pending"')
            pending_count = cursor.fetchone()[0]
            
            # 本月統計
            now = datetime.now(TW_TZ)
            month_start = now.replace(day=1).strftime('%Y-%m-%d')
            
            cursor.execute('''
                SELECT status, COUNT(*), SUM(hours) 
                FROM overtime_requests 
                WHERE overtime_date >= ?
                GROUP BY status
            ''', (month_start,))
            
            monthly_stats = {}
            for row in cursor.fetchall():
                status, count, hours = row
                monthly_stats[status] = {
                    'count': count,
                    'hours': round(hours or 0, 1)
                }
            
            # 預估本月加班費
            cursor.execute('''
                SELECT SUM(ot.hours * COALESCE(es.overtime_rate, 300))
                FROM overtime_requests ot
                LEFT JOIN employee_salary es ON ot.employee_id = es.employee_id
                WHERE ot.overtime_date >= ? AND ot.status = 'approved'
            ''', (month_start,))
            
            estimated_cost = cursor.fetchone()[0] or 0
            
            conn.close()
            
            return jsonify({
                'success': True,
                'data': {
                    'pending_count': pending_count,
                    'monthly_stats': monthly_stats,
                    'estimated_monthly_cost': round(estimated_cost, 0),
                    'month': f"{now.year}年{now.month:02d}月"
                }
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400
    
    @app.route('/api/overtime/export/csv')
    @require_admin
    def export_overtime_csv():
        """導出加班記錄CSV"""
        status = request.args.get('status', 'all')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        try:
            conn = sqlite3.connect('attendance.db')
            cursor = conn.cursor()
            
            query = '''
                SELECT ot.id, ot.employee_id, e.name, e.department,
                       ot.overtime_date, ot.start_time, ot.end_time, 
                       ot.hours, ot.reason, ot.status, 
                       ot.created_at, ot.approved_at
                FROM overtime_requests ot
                JOIN employees e ON ot.employee_id = e.employee_id
            '''
            
            params = []
            conditions = []
            
            if status != 'all':
                conditions.append('ot.status = ?')
                params.append(status)
            
            if start_date:
                conditions.append('ot.overtime_date >= ?')
                params.append(start_date)
            
            if end_date:
                conditions.append('ot.overtime_date <= ?')
                params.append(end_date)
            
            if conditions:
                query += ' WHERE ' + ' AND '.join(conditions)
            
            query += ' ORDER BY ot.overtime_date DESC, ot.created_at DESC'
            
            cursor.execute(query, params)
            records = cursor.fetchall()
            conn.close()
            
            if not records:
                return jsonify({'error': '查無符合條件的記錄'}), 400
            
            # 建立CSV內容
            import io, csv
            output = io.StringIO()
            writer = csv.writer(output)
            
            # CSV標題
            writer.writerow([
                '申請編號', '員工編號', '姓名', '部門', '加班日期', 
                '開始時間', '結束時間', '加班時數', '申請原因', '狀態',
                '申請時間', '審核時間'
            ])
            
            # 寫入資料
            for record in records:
                status_text = {
                    'pending': '待審核',
                    'approved': '已批准',
                    'rejected': '已拒絕'
                }.get(record[9], record[9])
                
                writer.writerow([
                    record[0],  # id
                    record[1],  # employee_id
                    record[2],  # name
                    record[3] or '未分類',  # department
                    record[4],  # overtime_date
                    record[5],  # start_time
                    record[6],  # end_time
                    f"{record[7]:.1f}小時",  # hours
                    record[8],  # reason
                    status_text,  # status
                    record[10],  # created_at
                    record[11] or '未審核'  # approved_at
                ])
            
            filename = f'overtime_report_{datetime.now(TW_TZ).strftime("%Y%m%d")}.csv'
            csv_content = output.getvalue()
            output.close()
            
            return Response(
                csv_content,
                mimetype='text/csv; charset=utf-8-sig',
                headers={
                    'Content-Disposition': f'attachment; filename="{filename}"',
                    'Content-Type': 'text/csv; charset=utf-8-sig'
                }
            )
            
        except Exception as e:
            return jsonify({'error': f'導出失敗: {str(e)}'}), 500
        
    @app.route('/api/salary/employees', methods=['GET'])
    @require_admin
    def get_employees_salary():
        """獲取員工薪資設定列表"""
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT e.employee_id, e.name, e.department, e.position,
                   es.base_salary, es.hourly_rate, es.overtime_rate, 
                   es.bonus, es.deductions, es.salary_type, es.effective_date
            FROM employees e
            LEFT JOIN employee_salary es ON e.employee_id = es.employee_id
            WHERE e.status = 'active'
            ORDER BY e.department, e.name
        ''')
        
        employees = cursor.fetchall()
        columns = ['employee_id', 'name', 'department', 'position',
                  'base_salary', 'hourly_rate', 'overtime_rate', 
                  'bonus', 'deductions', 'salary_type', 'effective_date']
        conn.close()
        
        return jsonify([dict(zip(columns, row)) for row in employees])
    
    @app.route('/api/salary/quick-setup', methods=['POST'])
    @require_admin
    def quick_salary_setup():
        """快速薪資設定"""
        data = request.get_json()
        
        try:
            employee_ids = data.get('employee_ids', [])
            default_settings = {
                'base_salary': float(data.get('base_salary', 0)),
                'hourly_rate': float(data.get('hourly_rate', 200)),
                'overtime_rate': float(data.get('overtime_rate', 300)),
                'bonus': float(data.get('bonus', 0)),
                'deductions': float(data.get('deductions', 0)),
                'salary_type': data.get('salary_type', 'hourly'),
                'effective_date': data.get('effective_date', datetime.now(TW_TZ).strftime('%Y-%m-%d'))
            }
            
            # 如果沒有指定員工 ID，設定所有活躍員工
            if not employee_ids:
                conn = sqlite3.connect('attendance.db')
                cursor = conn.cursor()
                cursor.execute('SELECT employee_id FROM employees WHERE status = "active"')
                employee_ids = [row[0] for row in cursor.fetchall()]
                conn.close()
            
            # 批量設定薪資
            from models import SalaryManager
            
            success_count = 0
            error_count = 0
            results = []
            
            for employee_id in employee_ids:
                try:
                    # 檢查員工是否存在
                    conn = sqlite3.connect('attendance.db')
                    cursor = conn.cursor()
                    cursor.execute('SELECT name FROM employees WHERE employee_id = ? AND status = "active"', (employee_id,))
                    employee = cursor.fetchone()
                    conn.close()
                    
                    if not employee:
                        results.append({
                            'employee_id': employee_id,
                            'success': False,
                            'error': '員工不存在或已停用'
                        })
                        error_count += 1
                        continue
                    
                    # 設定薪資
                    SalaryManager.set_employee_salary(
                        employee_id, 
                        default_settings, 
                        session.get('employee_id', 'ADMIN001')
                    )
                    
                    results.append({
                        'employee_id': employee_id,
                        'name': employee[0],
                        'success': True,
                        'settings': default_settings
                    })
                    success_count += 1
                    
                except Exception as e:
                    results.append({
                        'employee_id': employee_id,
                        'success': False,
                        'error': str(e)
                    })
                    error_count += 1
            
            return jsonify({
                'success': True,
                'message': f'快速薪資設定完成：成功 {success_count}/{len(employee_ids)} 位員工',
                'summary': {
                    'total': len(employee_ids),
                    'success_count': success_count,
                    'error_count': error_count,
                    'settings_applied': default_settings
                },
                'results': results
            })
            
        except ValueError as e:
            return jsonify({
                'success': False,
                'message': f'數值格式錯誤：{str(e)}'
            }), 400
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'設定失敗：{str(e)}'
            }), 400

    # 修改：員工薪資管理，管理員可查看所有，員工只能查看自己
    @app.route('/api/salary/employee/<employee_id>', methods=['GET', 'POST'])
    @require_employee_or_admin
    def manage_employee_salary(employee_id):
        """管理員工薪資設定"""
        current_employee_id = session.get('employee_id')
        current_role = EmployeeManager.get_employee_role(current_employee_id)
        
        # 檢查權限：管理員可查看所有，員工只能查看自己
        if current_role != 'ADMIN' and current_employee_id != employee_id:
            return jsonify({'error': '權限不足：只能查看自己的薪資'}), 403
        
        if request.method == 'GET':
            from models import SalaryManager
            salary_info = SalaryManager.get_employee_salary(employee_id)
            
            if not salary_info:
                # 返回預設值
                salary_info = {
                    'base_salary': 0,
                    'hourly_rate': 200,
                    'overtime_rate': 300,
                    'bonus': 0,
                    'deductions': 0,
                    'salary_type': 'hourly',
                    'effective_date': datetime.now(TW_TZ).strftime('%Y-%m-%d')
                }
            
            return jsonify(salary_info)
        
        elif request.method == 'POST':
            # 只有管理員可以修改薪資設定
            if current_role != 'ADMIN':
                return jsonify({'error': '權限不足：只有管理員可以修改薪資設定'}), 403
                
            data = request.get_json()
            
            try:
                from models import SalaryManager
                
                salary_data = {
                    'base_salary': float(data.get('base_salary', 0)),
                    'hourly_rate': float(data.get('hourly_rate', 200)),
                    'overtime_rate': float(data.get('overtime_rate', 300)),
                    'bonus': float(data.get('bonus', 0)),
                    'deductions': float(data.get('deductions', 0)),
                    'salary_type': data.get('salary_type', 'hourly'),
                    'effective_date': data.get('effective_date', datetime.now(TW_TZ).strftime('%Y-%m-%d'))
                }
                
                SalaryManager.set_employee_salary(
                    employee_id, 
                    salary_data, 
                    session.get('employee_id', 'ADMIN001')
                )
                
                return jsonify({
                    'success': True,
                    'message': '薪資設定更新成功'
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'更新失敗：{str(e)}'
                }), 400
    
    # 修改：員工薪資計算，管理員可計算所有，員工只能查看自己
    @app.route('/api/salary/calculate/<employee_id>')
    @require_employee_or_admin
    def calculate_employee_salary(employee_id):
        """計算員工薪資"""
        current_employee_id = session.get('employee_id')
        current_role = EmployeeManager.get_employee_role(current_employee_id)
        
        # 檢查權限：管理員可查看所有，員工只能查看自己
        if current_role != 'ADMIN' and current_employee_id != employee_id:
            return jsonify({'error': '權限不足：只能查看自己的薪資'}), 403
        
        year = request.args.get('year', datetime.now(TW_TZ).year, type=int)
        month = request.args.get('month', datetime.now(TW_TZ).month, type=int)
        
        try:
            from salary_calculator import SalaryCalculator
            from models import SalaryManager
            
            # 檢查員工是否存在
            conn = sqlite3.connect('attendance.db')
            cursor = conn.cursor()
            cursor.execute('SELECT name FROM employees WHERE employee_id = ?', (employee_id,))
            employee = cursor.fetchone()
            conn.close()
            
            if not employee:
                return jsonify({'error': '員工不存在'}), 404
            
            # 計算薪資
            salary_data = SalaryCalculator.calculate_monthly_salary(employee_id, year, month)
            
            # 只有管理員可以保存計算記錄
            if current_role == 'ADMIN':
                SalaryManager.save_salary_record(
                    employee_id, 
                    salary_data, 
                    session.get('employee_id', 'ADMIN001')
                )
            
            # 加入員工姓名
            salary_data['employee_name'] = employee[0]
            
            return jsonify(salary_data)
            
        except Exception as e:
            return jsonify({'error': f'計算失敗：{str(e)}'}), 400
    
    @app.route('/api/salary/records')
    @require_admin
    def get_salary_records():
        """獲取薪資計算記錄"""
        year = request.args.get('year', datetime.now(TW_TZ).year, type=int)
        month = request.args.get('month', datetime.now(TW_TZ).month, type=int)
        
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT sr.*, e.name, e.department
            FROM salary_records sr
            JOIN employees e ON sr.employee_id = e.employee_id
            WHERE sr.year = ? AND sr.month = ?
            ORDER BY e.department, e.name
        ''', (year, month))
        
        records = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        conn.close()
        
        return jsonify([dict(zip(columns, row)) for row in records])
    
    @app.route('/api/salary/summary')
    @require_admin
    def get_salary_summary():
        """獲取薪資統計摘要"""
        year = request.args.get('year', datetime.now(TW_TZ).year, type=int)
        month = request.args.get('month', datetime.now(TW_TZ).month, type=int)
        
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        # 總薪資統計
        cursor.execute('''
            SELECT 
                COUNT(*) as employee_count,
                SUM(gross_salary) as total_gross,
                SUM(net_salary) as total_net,
                AVG(net_salary) as avg_salary,
                SUM(overtime_pay) as total_overtime,
                SUM(late_penalty) as total_penalty
            FROM salary_records
            WHERE year = ? AND month = ?
        ''', (year, month))
        
        summary = cursor.fetchone()
        
        # 部門薪資統計
        cursor.execute('''
            SELECT 
                e.department,
                COUNT(*) as count,
                SUM(sr.net_salary) as total_salary,
                AVG(sr.net_salary) as avg_salary
            FROM salary_records sr
            JOIN employees e ON sr.employee_id = e.employee_id
            WHERE sr.year = ? AND sr.month = ?
            GROUP BY e.department
            ORDER BY total_salary DESC
        ''', (year, month))
        
        departments = cursor.fetchall()
        conn.close()
        
        return jsonify({
            'summary': {
                'employee_count': summary[0] or 0,
                'total_gross': summary[1] or 0,
                'total_net': summary[2] or 0,
                'avg_salary': round(summary[3] or 0, 2),
                'total_overtime': summary[4] or 0,
                'total_penalty': summary[5] or 0
            },
            'departments': [
                {
                    'department': dept[0] or '未分類',
                    'count': dept[1],
                    'total_salary': dept[2],
                    'avg_salary': round(dept[3], 2)
                }
                for dept in departments
            ]
        })
    
    @app.route('/api/reports/export/monthly-csv')
    @require_admin
    def export_monthly_csv():
        """匯出月度CSV報表"""
        year = request.args.get('year', datetime.now(TW_TZ).year, type=int)
        month = request.args.get('month', datetime.now(TW_TZ).month, type=int)
        report_type = request.args.get('type', 'attendance')  # attendance, salary
        
        try:
            if report_type == 'salary':
                # 匯出薪資報表
                conn = sqlite3.connect('attendance.db')
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT sr.employee_id, e.name, e.department, sr.work_days, 
                        sr.total_hours, sr.overtime_hours, sr.base_salary,
                        sr.hourly_pay, sr.overtime_pay, sr.bonus, 
                        sr.gross_salary, sr.deductions, sr.net_salary,
                        sr.calculated_at
                    FROM salary_records sr
                    JOIN employees e ON sr.employee_id = e.employee_id
                    WHERE sr.year = ? AND sr.month = ?
                    ORDER BY e.department, e.name
                ''', (year, month))
                
                records = cursor.fetchall()
                conn.close()
                
                if not records:
                    return jsonify({'error': '該月份無薪資記錄'}), 400
                
                # 建立CSV內容
                import io, csv
                output = io.StringIO()
                writer = csv.writer(output)
                
                # CSV標題
                writer.writerow([
                    '員工編號', '姓名', '部門', '出勤天數', '總工時', '加班時數',
                    '基本薪資', '時薪計算', '加班費', '獎金', 
                    '應發薪資', '扣款', '實發薪資', '計算時間'
                ])
                
                # 寫入資料
                for record in records:
                    writer.writerow([
                        record[0],  # employee_id
                        record[1],  # name
                        record[2] or '未分類',  # department
                        record[3],  # work_days
                        f"{record[4]:.1f}",  # total_hours
                        f"{record[5]:.1f}",  # overtime_hours
                        f"${record[6]:,.0f}",  # base_salary
                        f"${record[7]:,.0f}",  # hourly_pay
                        f"${record[8]:,.0f}",  # overtime_pay
                        f"${record[9]:,.0f}",  # bonus
                        f"${record[10]:,.0f}",  # gross_salary
                        f"${record[11]:,.0f}",  # deductions
                        f"${record[12]:,.0f}",  # net_salary
                        record[13]  # calculated_at
                    ])
                
                filename = f'salary_report_{year}_{month:02d}.csv'
            
            else:
                # 匯出出勤報表
                data = AttendanceReport.get_monthly_summary(year, month)
                
                if not data:
                    return jsonify({'error': '該月份無出勤記錄'}), 400
                
                import io, csv
                output = io.StringIO()
                writer = csv.writer(output)
                
                # CSV標題 - 移除打卡完整度相關欄位
                writer.writerow([
                    '員工編號', '姓名', '部門', '出勤天數', '總工時', '平均工時'
                ])
                
                # 寫入資料 - 移除完整度計算
                for record in data:
                    writer.writerow([
                        record['employee_id'],
                        record['name'],
                        record['department'] or '未分類',
                        record['work_days'],
                        f"{record['total_hours']:.1f}",
                        f"{record['avg_hours']:.1f}"
                    ])
                
                filename = f'attendance_report_{year}_{month:02d}.csv'
            
            csv_content = output.getvalue()
            output.close()
            
            return Response(
                csv_content,
                mimetype='text/csv; charset=utf-8-sig',  # 支援中文
                headers={
                    'Content-Disposition': f'attachment; filename="{filename}"',
                    'Content-Type': 'text/csv; charset=utf-8-sig'
                }
            )
            
        except Exception as e:
            return jsonify({'error': f'匯出失敗: {str(e)}'}), 500
        
    @app.route('/api/salary/batch-calculate', methods=['POST'])
    @require_admin
    def batch_calculate_salary():
        """批量計算薪資"""
        data = request.get_json()
        year = data.get('year', datetime.now(TW_TZ).year)
        month = data.get('month', datetime.now(TW_TZ).month)
        employee_ids = data.get('employee_ids', [])
        
        if not employee_ids:
            # 如果沒有指定員工，計算所有活躍員工
            conn = sqlite3.connect('attendance.db')
            cursor = conn.cursor()
            cursor.execute('SELECT employee_id FROM employees WHERE status = "active"')
            employee_ids = [row[0] for row in cursor.fetchall()]
            conn.close()
        
        try:
            from salary_calculator import SalaryCalculator
            from models import SalaryManager
            
            results = []
            
            for employee_id in employee_ids:
                try:
                    # 計算薪資
                    salary_data = SalaryCalculator.calculate_monthly_salary(employee_id, year, month)
                    
                    # 保存記錄
                    SalaryManager.save_salary_record(
                        employee_id, 
                        salary_data, 
                        session.get('employee_id', 'ADMIN001')
                    )
                    
                    results.append({
                        'employee_id': employee_id,
                        'success': True,
                        'net_salary': salary_data['net_salary']
                    })
                    
                except Exception as e:
                    results.append({
                        'employee_id': employee_id,
                        'success': False,
                        'error': str(e)
                    })
            
            success_count = len([r for r in results if r['success']])
            
            return jsonify({
                'success': True,
                'message': f'批量計算完成：成功 {success_count}/{len(results)} 位員工',
                'results': results
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'批量計算失敗：{str(e)}'
            }), 400
    
    # === 新增員工薪資查詢 API ===
    @app.route('/api/my-salary')
    @require_employee_or_admin
    def get_my_salary():
        """員工查看自己的薪資（LINE Bot 調用）"""
        employee_id = session.get('employee_id')
        year = request.args.get('year', datetime.now(TW_TZ).year, type=int)
        month = request.args.get('month', datetime.now(TW_TZ).month, type=int)
        
        try:
            from salary_calculator import SalaryCalculator
            
            # 檢查員工是否存在
            conn = sqlite3.connect('attendance.db')
            cursor = conn.cursor()
            cursor.execute('SELECT name FROM employees WHERE employee_id = ?', (employee_id,))
            employee = cursor.fetchone()
            conn.close()
            
            if not employee:
                return jsonify({'error': '員工不存在'}), 404
            
            # 計算薪資
            salary_data = SalaryCalculator.calculate_monthly_salary(employee_id, year, month)
            salary_data['employee_name'] = employee[0]
            
            return jsonify(salary_data)
            
        except Exception as e:
            return jsonify({'error': f'查詢失敗：{str(e)}'}), 400
    
    # === 新增員工身份驗證 API (供 LINE Bot 使用) ===
    @app.route('/api/employee/login', methods=['POST'])
    def employee_login():
        """員工身份驗證（供 LINE Bot 使用）"""
        data = request.get_json()
        line_user_id = data.get('line_user_id')
        
        if not line_user_id:
            return jsonify({'error': '缺少 LINE 用戶 ID'}), 400
        
        # 根據 LINE ID 查找員工
        employee = EmployeeManager.get_employee_by_line_id(line_user_id)
        
        if not employee:
            return jsonify({'error': '員工不存在'}), 404
        
        # 建立會話
        session['employee_id'] = employee['employee_id']
        session['role'] = employee['role']
        session['line_user_id'] = line_user_id
        
        return jsonify({
            'success': True,
            'employee_id': employee['employee_id'],
            'name': employee['name'],
            'role': employee['role']
        })
            
    # === 新增出勤報表 API ===
    
    @app.route('/api/reports/daily')
    @require_admin
    def get_daily_report():
        """每日出勤報表"""
        date = request.args.get('date', datetime.now(TW_TZ).strftime('%Y-%m-%d'))
        data = AttendanceReport.get_daily_summary(date)
        return jsonify(data)
    
    @app.route('/api/reports/monthly')
    @require_admin
    def get_monthly_report():
        """月度出勤報表"""
        year = request.args.get('year', datetime.now(TW_TZ).year, type=int)
        month = request.args.get('month', datetime.now(TW_TZ).month, type=int)
        data = AttendanceReport.get_monthly_summary(year, month)
        return jsonify(data)
    
    @app.route('/api/reports/department')
    @require_admin
    def get_department_report():
        """部門出勤摘要"""
        date = request.args.get('date', datetime.now(TW_TZ).strftime('%Y-%m-%d'))
        data = AttendanceReport.get_department_summary(date)
        return jsonify(data)
    
    @app.route('/api/reports/network-violations')
    @require_admin
    def get_network_violations():
        """網路違規記錄"""
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        data = AttendanceReport.get_network_violations(start_date, end_date)
        return jsonify(data)
    
    @app.route('/api/reports/employee/<employee_id>')
    @require_admin
    def get_employee_report(employee_id):
        """個人詳細出勤報表"""
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        data = AttendanceReport.get_employee_detail_report(employee_id, start_date, end_date)
        
        if not data:
            return jsonify({'error': '員工不存在'}), 404
        
        return jsonify(data)
    
    @app.route('/api/reports/export/csv')
    @require_admin
    def export_csv():
        """導出 CSV 報表"""
        report_type = request.args.get('type', 'daily')
        date = request.args.get('date', datetime.now(TW_TZ).strftime('%Y-%m-%d'))
        
        if report_type == 'daily':
            data = AttendanceReport.get_daily_summary(date)
            filename = f'daily_report_{date}.csv'
        elif report_type == 'department':
            data = AttendanceReport.get_department_summary(date)
            filename = f'department_report_{date}.csv'
        else:
            return jsonify({'error': '不支援的報表類型'}), 400
        
        csv_content = AttendanceReport.export_to_csv(data, filename)
        
        if not csv_content:
            return jsonify({'error': '無資料可導出'}), 400
        
        return Response(
            csv_content,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )