# config.py - 系統設定檔案
import os
from datetime import timedelta

class Config:
    """基礎設定類"""
    
    # Flask 設定
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-in-production'
    
    # LINE Bot 設定
    LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN') or \
        'E7zP9wng9dQwxKXxGTnMFb7F57fmeLQC55Xmaap77EXfk/BMhu9fGz8VGLx3KjRgtZ4CIyKaiJ/2Ih/iispaeQKRwtRxci4L1uw67T/QUk3HOJaWSoOHh0q329PCOj0wAo1jGWRh40x7g7dTkGOW0gdB04t89/1O/w1cDnyilFU='
    
    LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET') or \
        'b277fba0a28a0278861a69f8de4df0cd'
    
    # 資料庫設定
    DATABASE_PATH = os.environ.get('DATABASE_PATH') or 'attendance.db'
    
    # 伺服器設定
    HOST = os.environ.get('HOST') or '0.0.0.0'
    PORT = int(os.environ.get('PORT', 5008))
    DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    # 網路安全設定
    DEFAULT_ALLOWED_NETWORKS = os.environ.get('ALLOWED_NETWORKS') or '172.20.10.0/24,192.168.101.0/24, 192.168.1.0/24, 147.92.150.192/28,147.92.149.0/24'
    NETWORK_CHECK_ENABLED = os.environ.get('NETWORK_CHECK_ENABLED', 'true').lower() == 'true'
    
    # 工作時間設定
    DEFAULT_WORK_START_TIME = os.environ.get('WORK_START_TIME') or '09:00'
    DEFAULT_WORK_END_TIME = os.environ.get('WORK_END_TIME') or '18:00'
    DEFAULT_LATE_THRESHOLD = int(os.environ.get('LATE_THRESHOLD', 10))  # 分鐘
    
    # 會話設定
    SESSION_LIFETIME = timedelta(hours=int(os.environ.get('SESSION_HOURS', 8)))
    
    # 時區設定
    TIMEZONE = os.environ.get('TIMEZONE') or 'Asia/Taipei'
    
    # 管理員設定
    DEFAULT_ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME') or 'admin'
    DEFAULT_ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or 'admin123'
    
    # 系統設定
    COMPANY_NAME = os.environ.get('COMPANY_NAME') or '企業出勤管理系統'
    
    # 日誌設定
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    LOG_FILE = os.environ.get('LOG_FILE') or 'attendance.log'

class DevelopmentConfig(Config):
    """開發環境設定"""
    DEBUG = True
    
class ProductionConfig(Config):
    """生產環境設定"""
    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'production-secret-key-must-be-changed'
    
    # 生產環境安全設定
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

class TestingConfig(Config):
    """測試環境設定"""
    TESTING = True
    DATABASE_PATH = ':memory:'  # 使用記憶體資料庫進行測試

# 設定字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """根據環境變數取得對應設定"""
    env = os.environ.get('FLASK_ENV', 'default')
    return config.get(env, config['default'])