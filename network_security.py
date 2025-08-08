# network_security.py - 網路安全管理模組 (完整修正版)
from flask import request
import ipaddress
import socket
import subprocess
import re
from models import CompanySettings

class NetworkSecurity:
    """網路安全管理類"""
    
    @staticmethod
    def get_client_ip():
        """獲取客戶端真實IP地址 (支援本地開發)"""
        # 檢查是否通過代理
        if request.headers.get('X-Forwarded-For'):
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        elif request.headers.get('X-Real-IP'):
            return request.headers.get('X-Real-IP')
        else:
            client_ip = request.remote_addr
            
            # 如果是本地環路地址，嘗試獲取真實的本地網路 IP
            if client_ip in ['127.0.0.1', 'localhost', '::1']:
                real_ip = NetworkSecurity.get_local_network_ip()
                if real_ip:
                    print(f"🔍 本地開發模式：將 {client_ip} 替換為 {real_ip}")
                    return real_ip
            
            return client_ip
    
    @staticmethod
    def get_local_network_ip():
        """獲取本地網路 IP 地址"""
        try:
            # 方法1: 嘗試連接外部地址來獲取本地 IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                print(f"🌐 偵測到本地網路 IP: {local_ip}")
                return local_ip
        except Exception as e:
            print(f"⚠️ 方法1失敗: {e}")
        
        try:
            # 方法2: 在 macOS 上使用 ifconfig 來獲取真實 IP
            result = subprocess.run(['ifconfig'], capture_output=True, text=True)
            if result.returncode == 0:
                # 支援多種網路範圍的 IP 偵測
                network_patterns = [
                    # 你的 ifconfig 中的網路
                    (r'inet (172\.20\.10\.\d+)', 'iPhone 熱點網路'),
                    (r'inet (192\.168\.101\.\d+)', 'PPP 連接'),
                    (r'inet (10\.243\.\d+\.\d+)', 'feth 虛擬網路'),
                    
                    # 其他常見網路
                    (r'inet (192\.168\.\d+\.\d+)', '私有網路 192.168.x.x'),
                    (r'inet (10\.\d+\.\d+\.\d+)', '私有網路 10.x.x.x'),
                    (r'inet (172\.1[6-9]\.\d+\.\d+)', '私有網路 172.16-19.x.x'),
                    (r'inet (172\.2[0-9]\.\d+\.\d+)', '私有網路 172.20-29.x.x'),
                    (r'inet (172\.3[0-1]\.\d+\.\d+)', '私有網路 172.30-31.x.x'),
                ]
                
                for pattern, description in network_patterns:
                    for line in result.stdout.split('\n'):
                        ip_match = re.search(pattern, line)
                        if ip_match:
                            detected_ip = ip_match.group(1)
                            print(f"🍎 macOS ifconfig 偵測到 {description}: {detected_ip}")
                            return detected_ip
                
                # 備用：尋找任何私有網路 IP (排除 127.x.x.x)
                for line in result.stdout.split('\n'):
                    if 'inet ' in line and 'inet 127.' not in line and 'inet 169.254.' not in line:
                        ip_match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', line)
                        if ip_match:
                            ip = ip_match.group(1)
                            if NetworkSecurity.is_private_ip(ip):
                                print(f"🔍 備用私有 IP: {ip}")
                                return ip
        except Exception as e:
            print(f"⚠️ 方法2失敗: {e}")
        
        return None
    
    @staticmethod
    def is_private_ip(ip):
        """檢查是否為私有 IP"""
        try:
            ip_obj = ipaddress.ip_address(ip)
            return ip_obj.is_private
        except ValueError:
            return False
    
    @staticmethod
    def get_default_allowed_networks():
        """根據當前網路環境自動生成預設允許的網路"""
        networks = []
        
        # 根據你的 ifconfig 輸出，自動加入可能的網路範圍
        common_networks = [
            # "147.92.150.0/24",      # 熱點網路
            "172.20.10.0/24",      # iPhone 熱點網路
            "192.168.101.0/24",    # PPP 連接網路
            "10.243.0.0/16",       # feth 虛擬網路
            "192.168.1.0/24",      # 常見路由器網路
            "192.168.1.110", 
            "192.168.0.0/24",      # 常見路由器網路
            "10.0.0.0/24",         # 常見私有網路
            "147.92.150.192/28",
            "147.92.149.0/24",
        ]
        
        # 如果能偵測到當前 IP，加入對應的網路範圍
        try:
            current_ip = NetworkSecurity.get_local_network_ip()
            if current_ip:
                ip_obj = ipaddress.ip_address(current_ip)
                
                # 根據 IP 自動生成網路範圍
                if current_ip.startswith('172.20.10.'):
                    networks.append("172.20.10.0/24")
                elif current_ip.startswith('192.168.101.'):
                    networks.append("192.168.101.0/24")
                elif current_ip.startswith('147.92.150.'):
                    networks.append("147.92.150.192/28")
                elif current_ip.startswith('147.92.149.'):
                    networks.append("147.92.149.0/24")
                elif current_ip.startswith('192.168.1.'):
                    networks.append("192.168.1.0/24")
                elif current_ip.startswith('10.243.'):
                    networks.append("10.243.0.0/16")
                elif current_ip.startswith('192.168.'):
                    # 自動生成 192.168.x.0/24 網路
                    parts = current_ip.split('.')
                    network = f"192.168.{parts[2]}.0/24"
                    networks.append(network)
                elif current_ip.startswith('10.'):
                    # 自動生成 10.x.x.0/24 網路
                    parts = current_ip.split('.')
                    network = f"10.{parts[1]}.{parts[2]}.0/24"
                    networks.append(network)
                    
                print(f"🔧 根據當前 IP {current_ip} 自動生成網路範圍: {networks}")
        except Exception as e:
            print(f"⚠️ 自動生成網路範圍失敗: {e}")
        
        # 移除重複項目
        return list(set(networks + common_networks))
    
    @staticmethod
    def is_allowed_network(ip_address):
        """檢查IP是否在允許的網路範圍內"""
        allowed_networks_str = CompanySettings.get_setting('allowed_networks', '')
        
        # 如果設定為空，自動使用預設網路範圍
        if not allowed_networks_str.strip():
            default_networks = NetworkSecurity.get_default_allowed_networks()
            print(f"📋 使用自動偵測的網路範圍: {default_networks}")
            allowed_networks = default_networks
        else:
            allowed_networks = [net.strip() for net in allowed_networks_str.split(',') if net.strip()]
        
        print(f"🔍 檢查 IP: {ip_address}")
        print(f"📋 允許的網路: {allowed_networks}")
        
        if not allowed_networks:
            # 如果完全沒有設定，允許所有 IP
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
                            print(f"✅ 通過網路驗證: {network_str}")
                            return True, f"通過網路驗證: {network_str}"
                    else:
                        if str(client_ip) == network_str:
                            print(f"✅ 通過IP驗證: {network_str}")
                            return True, f"通過IP驗證: {network_str}"
                except ValueError as e:
                    print(f"⚠️ 網路格式錯誤: {network_str} - {e}")
                    continue
            
            print(f"❌ IP {ip_address} 不在允許的網路範圍內")
            return False, f"IP {ip_address} 不在允許的網路範圍內"
            
        except ValueError:
            print(f"❌ 無效的IP地址: {ip_address}")
            return False, f"無效的IP地址: {ip_address}"
    
    @staticmethod
    def check_punch_network():
        """檢查打卡網路權限"""
        client_ip = NetworkSecurity.get_client_ip()
        print(f"🔍 當前偵測到的客戶端 IP: {client_ip}")
        
        # 加入除錯資訊
        allowed_networks = CompanySettings.get_setting('allowed_networks', '')
        print(f"📋 設定的允許網路: '{allowed_networks}'")
        
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
            client_ip = NetworkSecurity.get_client_ip()
            print(f"ℹ️ 網路檢查已停用，IP: {client_ip}")
            return {
                'success': True,
                'network_info': "網路檢查已停用",
                'ip': client_ip
            }
        
        client_ip = NetworkSecurity.get_client_ip()
        is_allowed, network_message = NetworkSecurity.is_allowed_network(client_ip)
        
        if not is_allowed:
            print(f"🚫 網路驗證失敗: {network_message}")
            return {
                'success': False,
                'message': f'網路驗證失敗：{network_message}\n請確認您在公司網路環境內',
                'network_error': True,
                'ip': client_ip
            }
        
        print(f"✅ 網路驗證成功: {network_message}")
        return {
            'success': True,
            'network_info': network_message,
            'ip': client_ip
        }
    
    @staticmethod
    def setup_network_for_current_environment():
        """為當前環境自動設定網路範圍"""
        try:
            current_ip = NetworkSecurity.get_local_network_ip()
            if current_ip:
                default_networks = NetworkSecurity.get_default_allowed_networks()
                networks_str = ','.join(default_networks)
                
                # 這裡你需要根據你的 CompanySettings 實作來更新設定
                # CompanySettings.set_setting('allowed_networks', networks_str)
                
                print(f"🔧 建議的網路設定: {networks_str}")
                print(f"📝 請將以下設定加入資料庫：")
                print(f"   allowed_networks = '{networks_str}'")
                
                return {
                    'success': True,
                    'current_ip': current_ip,
                    'suggested_networks': networks_str,
                    'networks_list': default_networks
                }
        except Exception as e:
            print(f"⚠️ 自動設定失敗: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def debug_network_info():
        """除錯用：顯示完整的網路資訊"""
        info = {
            'client_ip': NetworkSecurity.get_client_ip(),
            'local_network_ip': NetworkSecurity.get_local_network_ip(),
            'allowed_networks_setting': CompanySettings.get_setting('allowed_networks', ''),
            'network_check_enabled': CompanySettings.get_setting('network_check_enabled', 'true'),
            'suggested_networks': NetworkSecurity.get_default_allowed_networks()
        }
        
        print("🔍 完整網路除錯資訊:")
        for key, value in info.items():
            print(f"   {key}: {value}")
        
        return info




# network_security.py - 網路安全管理模組 (不限定網路版本)
# from flask import request
# import ipaddress
# import socket
# import subprocess
# import re
# from models import CompanySettings

# class NetworkSecurity:
#     """網路安全管理類"""
    
#     @staticmethod
#     def get_client_ip():
#         """獲取客戶端真實IP地址"""
#         # 檢查是否通過代理
#         if request.headers.get('X-Forwarded-For'):
#             return request.headers.get('X-Forwarded-For').split(',')[0].strip()
#         elif request.headers.get('X-Real-IP'):
#             return request.headers.get('X-Real-IP')
#         else:
#             return request.remote_addr
    
#     @staticmethod
#     def is_allowed_network(ip_address):
#         """檢查IP是否在允許的網路範圍內 - 修改為允許所有IP"""
#         print(f"🔍 檢查 IP: {ip_address}")
#         print(f"✅ 網路限制已停用，允許所有IP")
        
#         # 直接返回允許，不進行任何網路限制
#         return True, f"網路限制已停用，允許所有IP訪問"
    
#     @staticmethod
#     def check_punch_network():
#         """檢查打卡網路權限 - 不限定網路版本"""
#         client_ip = NetworkSecurity.get_client_ip()
#         print(f"🔍 當前偵測到的客戶端 IP: {client_ip}")
#         print(f"✅ 網路限制已停用")
        
#         return {
#             'allowed': True,  # 始終允許
#             'ip': client_ip,
#             'message': '網路限制已停用，允許所有IP訪問'
#         }
    
#     @staticmethod
#     def validate_punch_permission():
#         """驗證打卡權限 - 不限定網路版本"""
#         client_ip = NetworkSecurity.get_client_ip()
#         print(f"ℹ️ 網路檢查已停用，允許所有IP，當前IP: {client_ip}")
        
#         return {
#             'success': True,  # 始終成功
#             'network_info': "網路限制已停用，允許所有IP訪問",
#             'ip': client_ip
#         }
    
#     # 保留原有的其他方法以維持相容性
#     @staticmethod
#     def get_local_network_ip():
#         """獲取本地網路 IP 地址"""
#         try:
#             with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
#                 s.connect(("8.8.8.8", 80))
#                 local_ip = s.getsockname()[0]
#                 return local_ip
#         except Exception:
#             return None
    
#     @staticmethod
#     def is_private_ip(ip):
#         """檢查是否為私有 IP"""
#         try:
#             ip_obj = ipaddress.ip_address(ip)
#             return ip_obj.is_private
#         except ValueError:
#             return False
    
#     @staticmethod
#     def debug_network_info():
#         """除錯用：顯示網路資訊"""
#         info = {
#             'client_ip': NetworkSecurity.get_client_ip(),
#             'network_restriction': 'DISABLED - 允許所有IP',
#             'status': '網路限制已停用'
#         }
        
#         print("🔍 網路除錯資訊:")
#         for key, value in info.items():
#             print(f"   {key}: {value}")
        
#         return info