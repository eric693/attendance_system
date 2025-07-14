# admin_routes.py - 管理後台路由模組 (加入出勤報表)
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
    
    @app.route('/api/reports/late')
    @require_admin
    def get_late_report():
        """遲到統計報表"""
        year = request.args.get('year', datetime.now(TW_TZ).year, type=int)
        month = request.args.get('month', datetime.now(TW_TZ).month, type=int)
        data = AttendanceReport.get_late_statistics(year, month)
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