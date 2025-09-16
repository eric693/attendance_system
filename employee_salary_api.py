# employee_salary_api.py - 員工薪資查詢 API 模組
import requests
import sqlite3
from datetime import datetime
import pytz
from models import EmployeeManager
from salary_calculator import SalaryCalculator

# 台灣時區設定
TW_TZ = pytz.timezone('Asia/Taipei')

class EmployeeSalaryAPI:
    """員工薪資查詢 API 類"""
    
    def __init__(self, base_url='http://localhost:5008'):
        self.base_url = base_url
    
    def authenticate_employee(self, line_user_id):
        """驗證員工身份"""
        try:
            employee = EmployeeManager.get_employee_by_line_id(line_user_id)
            if not employee:
                return None
            
            return {
                'employee_id': employee['employee_id'],
                'name': employee['name'],
                'role': employee['role'],
                'department': employee['department']
            }
        except Exception as e:
            print(f"員工身份驗證失敗: {e}")
            return None
    
    def get_salary_data(self, employee_id, year=None, month=None):
        """獲取員工薪資數據"""
        try:
            if not year:
                year = datetime.now(TW_TZ).year
            if not month:
                month = datetime.now(TW_TZ).month
                
            # 檢查員工薪資設定
            salary_info = SalaryCalculator.get_employee_salary_info(employee_id)
            
            # 如果沒有薪資設定，返回提示
            if salary_info['base_salary'] == 0 and salary_info['hourly_rate'] == 200:
                return {
                    'success': False,
                    'error': 'salary_not_setup',
                    'message': '薪資設定尚未完成，請聯繫管理員'
                }
            
            # 計算薪資
            salary_data = SalaryCalculator.calculate_monthly_salary(employee_id, year, month)
            
            # 檢查是否有出勤記錄
            if salary_data['work_stats']['work_days'] == 0:
                return {
                    'success': False,
                    'error': 'no_attendance',
                    'message': f'{year}年{month:02d}月無出勤記錄'
                }
            
            return {
                'success': True,
                'data': salary_data
            }
            
        except Exception as e:
            print(f"獲取薪資數據失敗: {e}")
            return {
                'success': False,
                'error': 'calculation_error',
                'message': f'薪資計算失敗: {str(e)}'
            }
    
    def get_salary_history(self, employee_id, months_back=3):
        """獲取員工薪資歷史記錄"""
        try:
            conn = sqlite3.connect('attendance.db')
            cursor = conn.cursor()
            
            now = datetime.now(TW_TZ)
            current_year = now.year
            current_month = now.month
            
            # 計算查詢的年月範圍
            records = []
            for i in range(months_back):
                month = current_month - i
                year = current_year
                
                while month <= 0:
                    month += 12
                    year -= 1
                
                cursor.execute('''
                    SELECT year, month, work_days, total_hours, 
                           gross_salary, net_salary, overtime_hours, late_count
                    FROM salary_records 
                    WHERE employee_id = ? AND year = ? AND month = ?
                ''', (employee_id, year, month))
                
                record = cursor.fetchone()
                if record:
                    records.append({
                        'year': record[0],
                        'month': record[1],
                        'work_days': record[2],
                        'total_hours': record[3],
                        'gross_salary': record[4],
                        'net_salary': record[5],
                        'overtime_hours': record[6],
                        'late_count': record[7]
                    })
            
            conn.close()
            
            return {
                'success': True,
                'data': records
            }
            
        except Exception as e:
            print(f"獲取薪資歷史失敗: {e}")
            return {
                'success': False,
                'error': 'history_error',
                'message': f'薪資歷史查詢失敗: {str(e)}'
            }
    
    def check_salary_permission(self, line_user_id, target_employee_id):
        """檢查薪資查詢權限"""
        try:
            employee = self.authenticate_employee(line_user_id)
            if not employee:
                return False
            
            # 管理員可查看所有員工薪資
            if employee['role'] == 'ADMIN':
                return True
            
            # 員工只能查看自己的薪資
            if employee['employee_id'] == target_employee_id:
                return True
            
            return False
            
        except Exception as e:
            print(f"權限檢查失敗: {e}")
            return False
    
    def format_salary_summary(self, employee_name, salary_data):
        """格式化薪資摘要文字"""
        try:
            work_stats = salary_data['work_stats']
            
            summary = f"💰 {employee_name} - {salary_data['year']}年{salary_data['month']:02d}月薪資\n"
            summary += "─" * 25 + "\n"
            
            # 工時統計
            summary += f"📊 工時統計\n"
            summary += f"• 出勤天數：{work_stats['work_days']} 天\n"
            summary += f"• 總工時：{work_stats['total_hours']:.1f} 小時\n"
            summary += f"• 加班時數：{work_stats['overtime_hours']:.1f} 小時\n"
            summary += f"• 遲到次數：{work_stats['late_count']} 次\n\n"
            
            # 薪資明細
            summary += f"💵 薪資明細\n"
            summary += f"• 基本薪資：${salary_data['base_salary']:,.0f}\n"
            summary += f"• 時薪計算：${salary_data['hourly_pay']:,.0f}\n"
            summary += f"• 加班費：${salary_data['overtime_pay']:,.0f}\n"
            summary += f"• 獎金：${salary_data['bonus']:,.0f}\n"
            summary += f"• 應發薪資：${salary_data['gross_salary']:,.0f}\n\n"
            
            # 扣款明細
            if salary_data['total_deductions'] > 0:
                summary += f"📉 扣款明細\n"
                summary += f"• 其他扣款：${salary_data['deductions']:,.0f}\n"
                summary += f"• 遲到扣款：${salary_data['late_penalty']:,.0f}\n"
                summary += f"• 總扣款：${salary_data['total_deductions']:,.0f}\n\n"
            
            # 實發薪資
            summary += "═" * 25 + "\n"
            summary += f"💰 實發薪資：${salary_data['net_salary']:,.0f}\n"
            summary += f"📅 計算時間：{datetime.now(TW_TZ).strftime('%Y-%m-%d %H:%M')}"
            
            return summary
            
        except Exception as e:
            print(f"格式化薪資摘要失敗: {e}")
            return "薪資摘要格式化失敗"
    
    def format_salary_history(self, employee_name, records, period_name):
        """格式化薪資歷史記錄文字"""
        try:
            if not records:
                return f"📋 {employee_name} - {period_name}\n\n查無薪資記錄"
            
            history_text = f"📋 {employee_name} - {period_name}\n"
            history_text += "─" * 25 + "\n\n"
            
            total_salary = 0
            for record in records:
                year_month = f"{record['year']}/{record['month']:02d}"
                net_salary = record['net_salary']
                work_days = record['work_days']
                total_hours = record['total_hours']
                
                total_salary += net_salary
                
                history_text += f"📅 {year_month}月\n"
                history_text += f"💰 實發薪資：${net_salary:,.0f}\n"
                history_text += f"📊 出勤：{work_days}天 / {total_hours:.1f}小時\n\n"
            
            # 統計摘要
            avg_salary = total_salary / len(records) if records else 0
            history_text += "═" * 25 + "\n"
            history_text += f"📈 統計摘要\n"
            history_text += f"• 總薪資：${total_salary:,.0f}\n"
            history_text += f"• 平均月薪：${avg_salary:,.0f}\n"
            history_text += f"• 記錄筆數：{len(records)}個月"
            
            return history_text
            
        except Exception as e:
            print(f"格式化薪資歷史失敗: {e}")
            return "薪資歷史格式化失敗"

# 全局 API 實例
employee_salary_api = EmployeeSalaryAPI()