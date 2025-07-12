# network_security.py - 網路安全管理模組
from flask import request
import ipaddress
from models import CompanySettings

class NetworkSecurity:
    """網路安全管理類"""
    
    @staticmethod
    def get_client_ip():
        """獲取客戶端真實IP地址"""
        # 檢查是否通過代理
        if request.headers.get('X-Forwarded-For'):
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        elif request.headers.get('X-Real-IP'):
            return request.headers.get('X-Real-IP')
        else:
            return request.remote_addr
    
    @staticmethod
    def is_allowed_network(ip_address):
        """檢查IP是否在允許的網路範圍內"""
        allowed_networks = CompanySettings.get_setting('allowed_networks', '').split(',')
        
        if not allowed_networks or allowed_networks == ['']:
            # 如果未設定網路限制，則允許所有IP
            return True, "未設定網路限制"
        
        try:
            client_ip = ipaddress.ip_address(ip_address.strip())
            
            for network_str in allowed_networks:
                network_str = network_str.strip()
                if not network_str:
                    continue
                    
                try:
                    # 支援單一IP或網路區段
                    if '/' in network_str:
                        allowed_network = ipaddress.ip_network(network_str, strict=False)
                        if client_ip in allowed_network:
                            return True, f"通過網路驗證: {network_str}"
                    else:
                        if str(client_ip) == network_str:
                            return True, f"通過IP驗證: {network_str}"
                except ValueError:
                    continue
            
            return False, f"IP {ip_address} 不在允許的網路範圍內"
            
        except ValueError:
            return False, f"無效的IP地址: {ip_address}"
    
    @staticmethod
    def check_punch_network():
        """檢查打卡網路權限"""
        client_ip = NetworkSecurity.get_client_ip()
        is_allowed, message = NetworkSecurity.is_allowed_network(client_ip)
        
        return {
            'allowed': is_allowed,
            'ip': client_ip,
            'message': message
        }
    
    @staticmethod
    def validate_punch_permission():
        """驗證打卡權限（完整版）"""
        network_check_enabled = CompanySettings.get_setting('network_check_enabled', 'true').lower() == 'true'
        
        if not network_check_enabled:
            return {
                'success': True,
                'network_info': "網路檢查已停用",
                'ip': NetworkSecurity.get_client_ip()
            }
        
        client_ip = NetworkSecurity.get_client_ip()
        is_allowed, network_message = NetworkSecurity.is_allowed_network(client_ip)
        
        if not is_allowed:
            return {
                'success': False,
                'message': f'網路驗證失敗：{network_message}\n請確認您在公司網路環境內',
                'network_error': True,
                'ip': client_ip
            }
        
        return {
            'success': True,
            'network_info': network_message,
            'ip': client_ip
        }