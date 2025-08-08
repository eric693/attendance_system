# models.py - 資料庫模型和初始化
import sqlite3
from datetime import datetime
import pytz

# 台灣時區設定
TW_TZ = pytz.timezone('Asia/Taipei')

# 權限等級定義
ROLES = {
    'ADMIN': 100,     # 管理員
    'EMPLOYEE': 20    # 一般員工
}

# 工作狀態定義
WORK_STATUS = {
    'OFF': 'off',          # 未上班
    'WORKING': 'working',  # 工作中
    'BREAK': 'break',      # 休息中
}

# 請假類型定義
LEAVE_TYPES = {
    'ANNUAL': '年假',
    'SICK': '病假',
    'PERSONAL': '事假',
    'MATERNITY': '產假',
    'COMPENSATORY': '補休',
    'OFFICIAL': '公假'
}

def init_db():
    """初始化資料庫"""
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    
    # 建立員工基本資料表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            employee_id TEXT PRIMARY KEY,
            line_user_id TEXT UNIQUE,
            name TEXT NOT NULL,
            email TEXT,
            department TEXT,
            position TEXT,
            role TEXT DEFAULT 'EMPLOYEE',
            hire_date DATE,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 建立出勤記錄表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT,
            action_type TEXT, -- clock_in, clock_out, break_start, break_end
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            taiwan_time TEXT,
            ip_address TEXT,
            network_info TEXT,
            status TEXT DEFAULT 'normal', -- normal, late, early_leave, network_violation
            notes TEXT,
            FOREIGN KEY (employee_id) REFERENCES employees (employee_id)
        )
    ''')
    
    # 建立請假記錄表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leave_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT,
            leave_type TEXT,
            start_date DATE,
            end_date DATE,
            start_time TIME,
            end_time TIME,
            total_hours REAL,
            reason TEXT,
            status TEXT DEFAULT 'pending', -- pending, approved, rejected
            approved_by TEXT,
            approved_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees (employee_id),
            FOREIGN KEY (approved_by) REFERENCES employees (employee_id)
        )
    ''')
    
    # 建立公司設定表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS company_settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            description TEXT,
            updated_by TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 建立待註冊用戶表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pending_registrations (
            line_user_id TEXT PRIMARY KEY,
            name TEXT,
            department TEXT,
            position TEXT,
            step INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 建立管理員會話表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin_sessions (
            session_id TEXT PRIMARY KEY,
            employee_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees (employee_id)
        )
    ''')
    
    # 插入預設設定 (重點：修改網路設定為)
    default_settings = [
        ('company_name', '企業出勤管理系統', '公司名稱'),
        ('work_start_time', '09:00', '標準上班時間'),
        ('work_end_time', '18:00', '標準下班時間'),
        ('late_threshold', '10', '遲到判定門檻(分鐘)'),
        ('allowed_networks', '172.20.10.0/24,192.168.101.0/24, 192.168.1.0/24, 147.92.150.192/28, 147.92.149.0/24', '允許打卡的網路範圍(用逗號分隔)'),
        ('network_check_enabled', 'true', '是否啟用網路檢查'),
        ('admin_line_id', '', '管理員LINE ID')
    ]
    
    for key, value, desc in default_settings:
        cursor.execute('''
            INSERT OR IGNORE INTO company_settings (key, value, description)
            VALUES (?, ?, ?)
        ''', (key, value, desc))
    
    # 建立預設管理員帳號
    cursor.execute('''
        INSERT OR IGNORE INTO employees 
        (employee_id, line_user_id, name, role, department, position, status)
        VALUES ('ADMIN001', '', '系統管理員', 'ADMIN', 'IT', '系統管理員', 'active')
    ''')
    
    conn.commit()
    conn.close()

class EmployeeManager:
    """員工管理類"""
    
    @staticmethod
    def create_employee(data):
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        employee_id = f"EMP{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        cursor.execute('''
            INSERT INTO employees 
            (employee_id, line_user_id, name, email, department, position, role, hire_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (employee_id, data.get('line_user_id'), data['name'], 
              data.get('email'), data.get('department'), data.get('position'),
              data.get('role', 'EMPLOYEE'), data.get('hire_date')))
        
        conn.commit()
        conn.close()
        return employee_id
    
    @staticmethod
    def get_employee_by_line_id(line_user_id):
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM employees WHERE line_user_id = ?', (line_user_id,))
        result = cursor.fetchone()
        
        if result:
            columns = [desc[0] for desc in cursor.description]
            employee = dict(zip(columns, result))
            conn.close()
            return employee
        
        conn.close()
        return None
    
    @staticmethod
    def get_employee_role(employee_id):
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        cursor.execute('SELECT role FROM employees WHERE employee_id = ?', (employee_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 'EMPLOYEE'
    
    @staticmethod
    def is_admin(employee_id):
        role = EmployeeManager.get_employee_role(employee_id)
        return role == 'ADMIN'

class CompanySettings:
    """公司設定管理類"""
    
    @staticmethod
    def get_setting(key, default=None):
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM company_settings WHERE key = ?', (key,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else default
    
    @staticmethod
    def update_setting(key, value, updated_by):
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        now = datetime.now(TW_TZ).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT OR REPLACE INTO company_settings (key, value, updated_by, updated_at)
            VALUES (?, ?, ?, ?)
        ''', (key, value, updated_by, now))
        
        conn.commit()
        conn.close()