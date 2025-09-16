# salary_calculator.py - 薪資計算模組
import sqlite3
from datetime import datetime, timedelta
import pytz
from typing import Dict, Optional, Any
import logging

# 台灣時區設定
TW_TZ = pytz.timezone('Asia/Taipei')

# 設定日誌
logger = logging.getLogger(__name__)

class SalaryCalculator:
    """薪資計算類"""
    
    @staticmethod
    def get_employee_salary_info(employee_id: str) -> Dict[str, float]:
        """獲取員工薪資資訊"""
        conn = None
        try:
            conn = sqlite3.connect('attendance.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT base_salary, hourly_rate, overtime_rate, bonus, deductions 
                FROM employee_salary 
                WHERE employee_id = ?
            ''', (employee_id,))
            
            result = cursor.fetchone()
            
            if result:
                return {
                    'base_salary': float(result[0] or 0),
                    'hourly_rate': float(result[1] or 0),
                    'overtime_rate': float(result[2] or 0),
                    'bonus': float(result[3] or 0),
                    'deductions': float(result[4] or 0)
                }
            
            # 如果沒有薪資資料，返回預設值
            return {
                'base_salary': 0.0,
                'hourly_rate': 200.0,  # 預設時薪
                'overtime_rate': 300.0,  # 預設加班費
                'bonus': 0.0,
                'deductions': 0.0
            }
            
        except sqlite3.Error as e:
            logger.error(f"資料庫錯誤 - 獲取員工薪資資訊: {e}")
            raise
        except Exception as e:
            logger.error(f"未預期錯誤 - 獲取員工薪資資訊: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def calculate_monthly_salary(employee_id: str, year: Optional[int] = None, month: Optional[int] = None) -> Dict[str, Any]:
        """計算月薪"""
        try:
            now = datetime.now(TW_TZ)
            if not year:
                year = now.year
            if not month:
                month = now.month
            
            # 驗證月份範圍
            if not (1 <= month <= 12):
                raise ValueError(f"無效的月份: {month}")
            
            # 獲取薪資設定
            salary_info = SalaryCalculator.get_employee_salary_info(employee_id)
            
            # 獲取工時統計
            work_stats = SalaryCalculator.get_monthly_work_stats(employee_id, year, month)
            
            # 計算基本薪資
            base_salary = salary_info['base_salary']
            
            # 計算時薪 (如果有工時)
            hourly_pay = work_stats['total_hours'] * salary_info['hourly_rate']
            
            # 計算加班費 (超過 8 小時/天的部分)
            overtime_pay = work_stats['overtime_hours'] * salary_info['overtime_rate']
            
            # 計算獎金
            bonus = salary_info['bonus']
            
            # 計算扣款
            deductions = salary_info['deductions']
            
            # 遲到扣款 (每次扣50元)
            late_penalty = work_stats['late_count'] * 50
            
            # 總薪資計算
            gross_salary = base_salary + hourly_pay + overtime_pay + bonus
            total_deductions = deductions + late_penalty
            net_salary = max(0, gross_salary - total_deductions)  # 確保實發薪資不為負數
            
            return {
                'year': year,
                'month': month,
                'base_salary': round(base_salary, 2),
                'hourly_pay': round(hourly_pay, 2),
                'overtime_pay': round(overtime_pay, 2),
                'bonus': round(bonus, 2),
                'gross_salary': round(gross_salary, 2),
                'deductions': round(deductions, 2),
                'late_penalty': round(late_penalty, 2),
                'total_deductions': round(total_deductions, 2),
                'net_salary': round(net_salary, 2),
                'work_stats': work_stats
            }
            
        except Exception as e:
            logger.error(f"計算月薪時發生錯誤: employee_id={employee_id}, year={year}, month={month}, error={e}")
            raise
    
    @staticmethod
    def get_monthly_work_stats(employee_id: str, year: int, month: int) -> Dict[str, float]:
        """獲取月度工作統計"""
        conn = None
        try:
            conn = sqlite3.connect('attendance.db')
            cursor = conn.cursor()
            
            # 獲取工作天數
            cursor.execute('''
                SELECT DATE(taiwan_time) as work_date
                FROM attendance_records 
                WHERE employee_id = ? 
                AND strftime('%Y', taiwan_time) = ? 
                AND strftime('%m', taiwan_time) = ?
                AND action_type = 'clock_in'
                GROUP BY DATE(taiwan_time)
                ORDER BY work_date
            ''', (employee_id, str(year), f"{month:02d}"))
            
            work_dates = [row[0] for row in cursor.fetchall()]
            
            # 計算總工時和加班時數
            total_hours = 0.0
            overtime_hours = 0.0
            
            # 導入 AttendanceReport 時進行錯誤處理
            try:
                from attendance_report import AttendanceReport
            except ImportError as e:
                logger.warning(f"無法導入 AttendanceReport: {e}")
                # 如果無法導入，使用替代計算方法
                AttendanceReport = None
            
            for date in work_dates:
                if AttendanceReport:
                    try:
                        daily_hours = AttendanceReport.calculate_daily_hours(employee_id, date)
                    except Exception as e:
                        logger.warning(f"計算每日工時失敗 {date}: {e}")
                        daily_hours = 0
                else:
                    # 替代計算方法：簡單的上下班時間差計算
                    daily_hours = SalaryCalculator._calculate_simple_daily_hours(employee_id, date, cursor)
                
                total_hours += daily_hours
                
                # 超過8小時的部分算加班
                if daily_hours > 8:
                    overtime_hours += (daily_hours - 8)
            
            # 獲取遲到次數
            cursor.execute('''
                SELECT COUNT(*) FROM attendance_records 
                WHERE employee_id = ? AND action_type = 'clock_in' 
                AND status = 'late'
                AND strftime('%Y', taiwan_time) = ? 
                AND strftime('%m', taiwan_time) = ?
            ''', (employee_id, str(year), f"{month:02d}"))
            
            late_count_result = cursor.fetchone()
            late_count = late_count_result[0] if late_count_result else 0
            
            return {
                'work_days': len(work_dates),
                'total_hours': round(total_hours, 2),
                'overtime_hours': round(overtime_hours, 2),
                'late_count': late_count,
                'avg_hours': round(total_hours / len(work_dates), 2) if work_dates else 0
            }
            
        except sqlite3.Error as e:
            logger.error(f"資料庫錯誤 - 獲取工作統計: {e}")
            raise
        except Exception as e:
            logger.error(f"獲取工作統計時發生錯誤: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def _calculate_simple_daily_hours(employee_id: str, date: str, cursor) -> float:
        """簡單的每日工時計算（當 AttendanceReport 不可用時）"""
        try:
            # 獲取當天的打卡記錄
            cursor.execute('''
                SELECT action_type, taiwan_time 
                FROM attendance_records 
                WHERE employee_id = ? AND DATE(taiwan_time) = ?
                ORDER BY taiwan_time
            ''', (employee_id, date))
            
            records = cursor.fetchall()
            if len(records) < 2:
                return 0.0
            
            # 找到第一次上班和最後一次下班
            clock_in_time = None
            clock_out_time = None
            
            for action_type, time_str in records:
                time_obj = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                if action_type == 'clock_in' and clock_in_time is None:
                    clock_in_time = time_obj
                elif action_type == 'clock_out':
                    clock_out_time = time_obj
            
            if clock_in_time and clock_out_time:
                duration = clock_out_time - clock_in_time
                return duration.total_seconds() / 3600  # 轉換為小時
            
            return 0.0
            
        except Exception as e:
            logger.warning(f"計算簡單每日工時失敗: {e}")
            return 0.0
    
    @staticmethod
    def create_simple_salary_card(salary_data: Dict[str, Any], employee_name: str):
        """創建簡化版薪資資訊卡片"""
        try:
            from linebot.models import FlexSendMessage
        except ImportError:
            logger.error("無法導入 LINE Bot SDK")
            raise ImportError("請安裝 line-bot-sdk: pip install line-bot-sdk")
        
        if not salary_data or not employee_name:
            raise ValueError("薪資資料和員工姓名不能為空")
        
        year = salary_data['year']
        month = salary_data['month']
        work_stats = salary_data['work_stats']
        
        # 簡化版 Flex Message
        flex_content = {
            "type": "bubble",
            "styles": {
                "header": {
                    "backgroundColor": "#667eea"
                }
            },
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": f"💰 {employee_name}",
                        "weight": "bold",
                        "color": "#ffffff",
                        "size": "lg"
                    },
                    {
                        "type": "text",
                        "text": f"{year}年{month:02d}月薪資",
                        "color": "#ffffff",
                        "size": "sm"
                    }
                ],
                "paddingAll": "20px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    # 實發薪資 - 大字顯示
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "實發薪資",
                                "size": "sm",
                                "color": "#666666",
                                "align": "center"
                            },
                            {
                                "type": "text",
                                "text": f"${salary_data['net_salary']:,.0f}",
                                "size": "xxl",
                                "weight": "bold",
                                "color": "#4CAF50",
                                "align": "center"
                            }
                        ],
                        "margin": "lg"
                    },
                    
                    # 分隔線
                    {
                        "type": "separator",
                        "margin": "xl"
                    },
                    
                    # 工時資訊
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "📊 本月工時",
                                "weight": "bold",
                                "size": "md",
                                "margin": "xl"
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "出勤天數",
                                        "size": "sm",
                                        "color": "#666666",
                                        "flex": 1
                                    },
                                    {
                                        "type": "text",
                                        "text": f"{work_stats['work_days']} 天",
                                        "size": "sm",
                                        "align": "end"
                                    }
                                ],
                                "margin": "md"
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "總工時",
                                        "size": "sm",
                                        "color": "#666666",
                                        "flex": 1
                                    },
                                    {
                                        "type": "text",
                                        "text": f"{work_stats['total_hours']:.1f} 小時",
                                        "size": "sm",
                                        "align": "end"
                                    }
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "加班時數",
                                        "size": "sm",
                                        "color": "#666666",
                                        "flex": 1
                                    },
                                    {
                                        "type": "text",
                                        "text": f"{work_stats['overtime_hours']:.1f} 小時",
                                        "size": "sm",
                                        "color": "#FF9800",
                                        "align": "end"
                                    }
                                ]
                            }
                        ]
                    },
                    
                    # 分隔線
                    {
                        "type": "separator",
                        "margin": "xl"
                    },
                    
                    # 薪資組成
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "💵 薪資組成",
                                "weight": "bold",
                                "size": "md",
                                "margin": "xl"
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "基本薪資",
                                        "size": "sm",
                                        "color": "#666666",
                                        "flex": 1
                                    },
                                    {
                                        "type": "text",
                                        "text": f"${salary_data['base_salary']:,.0f}",
                                        "size": "sm",
                                        "align": "end"
                                    }
                                ],
                                "margin": "md"
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "工時薪資",
                                        "size": "sm",
                                        "color": "#666666",
                                        "flex": 1
                                    },
                                    {
                                        "type": "text",
                                        "text": f"${salary_data['hourly_pay']:,.0f}",
                                        "size": "sm",
                                        "align": "end"
                                    }
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "加班費",
                                        "size": "sm",
                                        "color": "#666666",
                                        "flex": 1
                                    },
                                    {
                                        "type": "text",
                                        "text": f"${salary_data['overtime_pay']:,.0f}",
                                        "size": "sm",
                                        "color": "#FF9800",
                                        "align": "end"
                                    }
                                ]
                            }
                        ]
                    }
                ],
                "spacing": "sm",
                "paddingAll": "20px"
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "button",
                        "style": "primary",
                        "action": {
                            "type": "message",
                            "label": "查看詳細",
                            "text": "薪資明細"
                        },
                        "color": "#667eea"
                    },
                    {
                        "type": "text",
                        "text": f"更新時間: {datetime.now(TW_TZ).strftime('%Y-%m-%d %H:%M')}",
                        "size": "xs",
                        "color": "#999999",
                        "align": "center",
                        "margin": "sm"
                    }
                ],
                "paddingAll": "15px"
            }
        }
        
        return FlexSendMessage(
            alt_text=f"{employee_name}的{year}年{month:02d}月薪資卡片",
            contents=flex_content
        )

    @staticmethod
    def create_salary_flex_message(salary_data: Dict[str, Any], employee_name: str):
        """創建薪資 Flex Message"""
        try:
            from linebot.models import FlexSendMessage
        except ImportError:
            logger.error("無法導入 LINE Bot SDK")
            raise ImportError("請安裝 line-bot-sdk: pip install line-bot-sdk")
        
        if not salary_data or not employee_name:
            raise ValueError("薪資資料和員工姓名不能為空")
        
        year = salary_data['year']
        month = salary_data['month']
        work_stats = salary_data['work_stats']
        
        flex_content = {
            "type": "bubble",
            "styles": {
                "header": {
                    "backgroundColor": "#667eea"
                }
            },
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "💰 薪資計算單",
                        "weight": "bold",
                        "color": "#ffffff",
                        "size": "lg",
                        "align": "center"
                    },
                    {
                        "type": "text",
                        "text": f"{employee_name} - {year}年{month:02d}月",
                        "color": "#ffffff",
                        "size": "sm",
                        "align": "center",
                        "margin": "sm"
                    }
                ],
                "paddingAll": "20px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    # 工時統計區塊
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "📊 工時統計",
                                "weight": "bold",
                                "size": "md",
                                "color": "#333333"
                            },
                            {
                                "type": "separator",
                                "margin": "sm"
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "出勤天數",
                                        "size": "sm",
                                        "color": "#666666",
                                        "flex": 1
                                    },
                                    {
                                        "type": "text",
                                        "text": f"{work_stats['work_days']} 天",
                                        "size": "sm",
                                        "color": "#333333",
                                        "align": "end"
                                    }
                                ],
                                "margin": "sm"
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "總工時",
                                        "size": "sm",
                                        "color": "#666666",
                                        "flex": 1
                                    },
                                    {
                                        "type": "text",
                                        "text": f"{work_stats['total_hours']:.1f} 小時",
                                        "size": "sm",
                                        "color": "#333333",
                                        "align": "end"
                                    }
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "加班時數",
                                        "size": "sm",
                                        "color": "#666666",
                                        "flex": 1
                                    },
                                    {
                                        "type": "text",
                                        "text": f"{work_stats['overtime_hours']:.1f} 小時",
                                        "size": "sm",
                                        "color": "#FF9800",
                                        "align": "end"
                                    }
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "遲到次數",
                                        "size": "sm",
                                        "color": "#666666",
                                        "flex": 1
                                    },
                                    {
                                        "type": "text",
                                        "text": f"{work_stats['late_count']} 次",
                                        "size": "sm",
                                        "color": "#f44336" if work_stats['late_count'] > 0 else "#4CAF50",
                                        "align": "end"
                                    }
                                ]
                            }
                        ],
                        "margin": "lg"
                    },
                    
                    # 薪資明細區塊
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "💵 薪資明細",
                                "weight": "bold",
                                "size": "md",
                                "color": "#333333",
                                "margin": "xl"
                            },
                            {
                                "type": "separator",
                                "margin": "sm"
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "基本薪資",
                                        "size": "sm",
                                        "color": "#666666",
                                        "flex": 1
                                    },
                                    {
                                        "type": "text",
                                        "text": f"${salary_data['base_salary']:,.0f}",
                                        "size": "sm",
                                        "color": "#333333",
                                        "align": "end"
                                    }
                                ],
                                "margin": "sm"
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "時薪計算",
                                        "size": "sm",
                                        "color": "#666666",
                                        "flex": 1
                                    },
                                    {
                                        "type": "text",
                                        "text": f"${salary_data['hourly_pay']:,.0f}",
                                        "size": "sm",
                                        "color": "#333333",
                                        "align": "end"
                                    }
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "加班費",
                                        "size": "sm",
                                        "color": "#666666",
                                        "flex": 1
                                    },
                                    {
                                        "type": "text",
                                        "text": f"${salary_data['overtime_pay']:,.0f}",
                                        "size": "sm",
                                        "color": "#FF9800",
                                        "align": "end"
                                    }
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "獎金",
                                        "size": "sm",
                                        "color": "#666666",
                                        "flex": 1
                                    },
                                    {
                                        "type": "text",
                                        "text": f"${salary_data['bonus']:,.0f}",
                                        "size": "sm",
                                        "color": "#4CAF50",
                                        "align": "end"
                                    }
                                ]
                            },
                            {
                                "type": "separator",
                                "margin": "md"
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "應發薪資",
                                        "size": "sm",
                                        "color": "#333333",
                                        "weight": "bold",
                                        "flex": 1
                                    },
                                    {
                                        "type": "text",
                                        "text": f"${salary_data['gross_salary']:,.0f}",
                                        "size": "sm",
                                        "color": "#333333",
                                        "weight": "bold",
                                        "align": "end"
                                    }
                                ],
                                "margin": "sm"
                            }
                        ]
                    },
                    
                    # 扣款區塊
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "📉 扣款明細",
                                "weight": "bold",
                                "size": "md",
                                "color": "#f44336",
                                "margin": "xl"
                            },
                            {
                                "type": "separator",
                                "margin": "sm"
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "其他扣款",
                                        "size": "sm",
                                        "color": "#666666",
                                        "flex": 1
                                    },
                                    {
                                        "type": "text",
                                        "text": f"-${salary_data['deductions']:,.0f}",
                                        "size": "sm",
                                        "color": "#f44336",
                                        "align": "end"
                                    }
                                ],
                                "margin": "sm"
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "遲到扣款",
                                        "size": "sm",
                                        "color": "#666666",
                                        "flex": 1
                                    },
                                    {
                                        "type": "text",
                                        "text": f"-${salary_data['late_penalty']:,.0f}",
                                        "size": "sm",
                                        "color": "#f44336",
                                        "align": "end"
                                    }
                                ]
                            }
                        ]
                    }
                ],
                "spacing": "sm",
                "paddingAll": "20px"
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "separator"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {
                                "type": "text",
                                "text": "實發薪資",
                                "size": "lg",
                                "color": "#ffffff",
                                "weight": "bold",
                                "flex": 1
                            },
                            {
                                "type": "text",
                                "text": f"${salary_data['net_salary']:,.0f}",
                                "size": "xl",
                                "color": "#ffffff",
                                "weight": "bold",
                                "align": "end"
                            }
                        ],
                        "margin": "md"
                    },
                    {
                        "type": "text",
                        "text": f"計算日期: {datetime.now(TW_TZ).strftime('%Y-%m-%d %H:%M')}",
                        "size": "xs",
                        "color": "#ffffff",
                        "align": "center",
                        "margin": "sm"
                    }
                ],
                "paddingAll": "20px",
                "backgroundColor": "#4CAF50"
            }
        }
        
        return FlexSendMessage(
            alt_text=f"{employee_name}的{year}年{month:02d}月薪資計算",
            contents=flex_content
        )


# 使用範例和測試函數
# if __name__ == "__main__":
#     # 測試用例
#     def test_salary_calculator():
#         """測試薪資計算器功能"""
#         try:
#             # 測試獲取員工薪資資訊
#             employee_id = "test_001"
#             salary_info = SalaryCalculator.get_employee_salary_info(employee_id)
#             print(f"員工薪資資訊: {salary_info}")
            
#             # 測試計算月薪
#             monthly_salary = SalaryCalculator.calculate_monthly_salary(employee_id, 2024, 9)
#             print(f"月薪計算結果: {monthly_salary}")
            
#             # 測試工作統計
#             work_stats = SalaryCalculator.get_monthly_work_stats(employee_id, 2024, 9)
#             print(f"工作統計: {work_stats}")
            
#         except Exception as e:
#             print(f"測試時發生錯誤: {e}")
    
