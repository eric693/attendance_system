# admin_routes.py - 管理後台路由模組
from flask import session, request, jsonify, render_template_string
from functools import wraps
import sqlite3
from datetime import datetime
import pytz
from models import EmployeeManager, CompanySettings
from network_security import NetworkSecurity
from templates import INDEX_TEMPLATE, ADMIN_TEMPLATE

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