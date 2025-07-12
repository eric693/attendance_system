# templates.py - HTML模板模組

# 首頁模板
INDEX_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>企業出勤管理系統 - 網路安全版</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            background: rgba(255,255,255,0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 40px;
            text-align: center;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            max-width: 600px;
            width: 90%;
        }
        h1 {
            color: #333;
            margin-bottom: 30px;
            font-size: 2.5em;
        }
        .feature {
            background: #f8f9fa;
            padding: 20px;
            margin: 15px 0;
            border-radius: 10px;
            border-left: 4px solid #667eea;
        }
        .security-feature {
            background: linear-gradient(135deg, #e8f5e8 0%, #f0f8ff 100%);
            border-left: 4px solid #4CAF50;
        }
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            margin: 10px;
            transition: transform 0.3s ease;
        }
        .btn:hover { transform: translateY(-2px); }
        .network-status {
            background: #e3f2fd;
            padding: 15px;
            border-radius: 10px;
            margin: 20px 0;
        }
        .network-info {
            background: linear-gradient(135deg, #fff3e0 0%, #e8f5e8 100%);
            padding: 15px;
            border-radius: 10px;
            margin: 20px 0;
            border-left: 4px solid #FF9800;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏢 企業出勤管理系統</h1>
        <p style="color: #666; margin-bottom: 30px;">網路安全版 - 限制特定網路才能打卡</p>
        
        <div class="feature">
            <h3>👥 智能出勤管理</h3>
            <p>LINE Bot整合，一鍵打卡，自動統計工時</p>
        </div>
        
        <div class="feature security-feature">
            <h3>🔒 網路安全控制</h3>
            <p>限制特定網路環境才能打卡，確保員工在公司內打卡</p>
        </div>
        
        <div class="feature">
            <h3>📊 簡化權限管理</h3>
            <p>管理員與員工兩層權限，簡潔高效</p>
        </div>
        
        <div class="network-info">
            <h4>🌐 網路設定資訊</h4>
            <p><strong>允許打卡網路：</strong>147.92.150.0/24</p>
            <p><small>僅在此網路範圍內可以進行打卡操作</small></p>
        </div>
        
        <div class="network-status">
            <h4>🔍 當前網路狀態</h4>
            <p id="networkStatus">檢查中...</p>
            <button class="btn" onclick="checkNetwork()" style="padding: 8px 16px; font-size: 14px;">
                重新檢查
            </button>
        </div>
        
        <button class="btn" onclick="location.href='/admin'">
            👨‍💼 管理後台
        </button>
        
        <div style="margin-top: 30px; color: #666;">
            <p>📱 員工請加入LINE Bot開始使用</p>
            <p>🔗 LINE Bot ID: @your_bot_id</p>
            <p>⚠️ 注意：需要在允許的網路環境內才能打卡</p>
        </div>
        
        <div style="margin-top: 20px; padding: 15px; background: #f0f8ff; border-radius: 10px;">
            <h4>✨ 主要功能</h4>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 10px;">
                <div>✅ 上班打卡</div>
                <div>✅ 下班打卡</div>
                <div>✅ 今日狀態</div>
                <div>✅ 查看記錄</div>
                <div>✅ 個人統計</div>
                <div>✅ 網路檢查</div>
            </div>
        </div>
    </div>
    
    <script>
        async function checkNetwork() {
            try {
                const response = await fetch('/api/network/status');
                const data = await response.json();
                
                const statusElement = document.getElementById('networkStatus');
                const statusText = data.allowed ? '✅ 允許打卡' : '❌ 無法打卡';
                
                statusElement.innerHTML = `
                    <strong>IP：${data.ip}</strong><br>
                    <span style="color: ${data.allowed ? 'green' : 'red'}">${statusText}</span><br>
                    <small>${data.message}</small>
                `;
            } catch (error) {
                document.getElementById('networkStatus').innerHTML = '❌ 無法檢查網路狀態';
            }
        }
        
        // 頁面載入時檢查網路
        checkNetwork();
    </script>
</body>
</html>
'''

# 管理後台模板
ADMIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>管理後台 - 企業出勤管理系統</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f6fa;
            min-height: 100vh;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px 0;
            text-align: center;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 30px 20px;
        }
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .stat-card {
            text-align: center;
            background: linear-gradient(135deg, #4CAF50, #45a049);
            color: white;
        }
        .security-card {
            background: linear-gradient(135deg, #FF5722, #E64A19);
            color: white;
        }
        .stat-number {
            font-size: 3em;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 25px;
            border-radius: 25px;
            cursor: pointer;
            margin: 5px;
            transition: transform 0.3s ease;
        }
        .btn:hover { transform: translateY(-2px); }
        .btn.danger { background: linear-gradient(135deg, #f44336, #da190b); }
        .form-input {
            width: 100%;
            padding: 12px;
            margin: 8px 0;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-size: 14px;
        }
        .form-textarea {
            width: 100%;
            padding: 12px;
            margin: 8px 0;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-size: 14px;
            min-height: 100px;
            resize: vertical;
        }
        .login-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.8);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
        }
        .login-form {
            background: white;
            padding: 40px;
            border-radius: 15px;
            text-align: center;
        }
        .network-settings {
            background: #e8f5e8;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }
        .status-ok { color: #4CAF50; }
        .status-error { color: #f44336; }
        .hidden { display: none; }
        .network-info-box {
            background: linear-gradient(135deg, #e3f2fd 0%, #fff3e0 100%);
            padding: 15px;
            border-radius: 10px;
            margin: 15px 0;
            border-left: 4px solid #2196F3;
        }
    </style>
</head>
<body>
    <!-- 登入覆蓋層 -->
    <div id="loginOverlay" class="login-overlay">
        <div class="login-form">
            <h2>🔐 管理員登入</h2>
            <input type="text" id="username" class="form-input" placeholder="帳號" value="admin">
            <input type="password" id="password" class="form-input" placeholder="密碼" value="admin123">
            <button class="btn" onclick="login()">登入</button>
            <p style="margin-top: 15px; color: #666; font-size: 14px;">
                預設帳號：admin / admin123
            </p>
        </div>
    </div>

    <!-- 主要內容 -->
    <div id="mainContent" class="hidden">
        <div class="header">
            <h1>📊 企業出勤管理後台</h1>
            <p>網路安全版 - 限制 147.92.150.0/24 網路才能打卡</p>
        </div>

        <div class="container">
            <!-- 統計卡片 -->
            <div class="dashboard-grid">
                <div class="card stat-card">
                    <div class="stat-number" id="totalEmployees">-</div>
                    <div>總員工數</div>
                </div>
                <div class="card stat-card" style="background: linear-gradient(135deg, #2196F3, #1976D2);">
                    <div class="stat-number" id="todayCheckin">-</div>
                    <div>今日出勤</div>
                </div>
                <div class="card stat-card" style="background: linear-gradient(135deg, #FF9800, #F57C00);">
                    <div class="stat-number" id="attendanceRate">-%</div>
                    <div>出勤率</div>
                </div>
                <div class="card security-card">
                    <div class="stat-number" id="networkViolations">-</div>
                    <div>網路違規</div>
                </div>
            </div>

            <!-- 網路安全設定 -->
            <div class="card">
                <h3>🌐 網路安全設定</h3>
                
                <div class="network-info-box">
                    <h4>📋 當前網路設定</h4>
                    <p><strong>允許打卡網路：</strong>147.92.150.0/24</p>
                    <p><small>此網路範圍包含 172.20.10.0 到 172.20.10.15 共16個IP地址</small></p>
                </div>
                
                <div class="network-settings">
                    <div style="margin-bottom: 15px;">
                        <label><strong>當前管理員IP：</strong></label>
                        <span id="currentIP" class="status-ok">檢查中...</span>
                    </div>
                    
                    <div style="margin-bottom: 15px;">
                        <label for="allowedNetworks"><strong>允許的網路範圍：</strong></label>
                        <textarea id="allowedNetworks" class="form-textarea" 
                                placeholder="例如：147.92.150.0/24,192.168.1.0/24&#10;多個網路用逗號分隔"></textarea>
                        <small style="color: #666;">
                            支援格式：<br>
                            • 單一IP：172.20.10.5<br>
                            • 網路段：147.92.150.0/24<br>
                            • 多個網路用逗號分隔
                        </small>
                    </div>
                    
                    <div style="margin-bottom: 15px;">
                        <label>
                            <input type="checkbox" id="networkCheckEnabled"> 
                            啟用網路檢查
                        </label>
                    </div>
                    
                    <button class="btn" onclick="saveNetworkSettings()">💾 儲存設定</button>
                    <button class="btn" onclick="testCurrentNetwork()">🧪 測試當前網路</button>
                    <button class="btn" onclick="addCurrentIP()">➕ 加入當前IP</button>
                </div>
            </div>

            <!-- 功能區域 -->
            <div class="dashboard-grid">
                <div class="card">
                    <h3>👥 員工管理</h3>
                    <p>員工資料、權限設定（管理員/員工）</p>
                    <button class="btn" onclick="showEmployees()">員工列表</button>
                    <button class="btn" onclick="showAddEmployeeForm()">新增員工</button>
                    <button class="btn" onclick="showPendingRegistrations()">待註冊用戶</button>
                </div>

                <div class="card">
                    <h3>📊 出勤統計</h3>
                    <p>即時出勤狀況、工時統計、網路記錄</p>
                    <button class="btn" onclick="showAttendanceStats()">出勤報表</button>
                    <button class="btn" onclick="showNetworkLogs()">網路記錄</button>
                </div>

                <div class="card">
                    <h3>✅ 申請審核</h3>
                    <p>請假申請審核管理</p>
                    <button class="btn" onclick="showPendingRequests()">待審項目</button>
                    <button class="btn" onclick="approvalHistory()">審核記錄</button>
                </div>

                <div class="card">
                    <h3>⚙️ 系統設定</h3>
                    <p>公司設定、工作時間、安全參數</p>
                    <button class="btn" onclick="systemSettings()">基本設定</button>
                    <button class="btn" onclick="securitySettings()">安全設定</button>
                </div>
            </div>

            <!-- 數據表格區域 -->
            <div id="dataTableContainer" class="card hidden">
                <h3 id="tableTitle">數據表格</h3>
                <div id="tableContent"></div>
            </div>
        </div>
    </div>

    <script>
        let networkSettings = {};

        // 登入功能
        async function login() {
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            
            try {
                const response = await fetch('/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    document.getElementById('loginOverlay').style.display = 'none';
                    document.getElementById('mainContent').classList.remove('hidden');
                    loadDashboard();
                    loadNetworkSettings();
                } else {
                    alert('登入失敗：' + result.message);
                }
            } catch (error) {
                alert('登入錯誤：' + error.message);
            }
        }

        // 載入儀表板數據
        async function loadDashboard() {
            try {
                const [employeesRes, statsRes] = await Promise.all([
                    fetch('/api/employees'),
                    fetch('/api/attendance/stats')
                ]);
                
                const employees = await employeesRes.json();
                const stats = await statsRes.json();
                
                document.getElementById('totalEmployees').textContent = employees.length;
                document.getElementById('todayCheckin').textContent = stats.today_checkin;
                document.getElementById('attendanceRate').textContent = stats.attendance_rate + '%';
                document.getElementById('networkViolations').textContent = stats.network_violations;
            } catch (error) {
                console.error('載入數據失敗:', error);
            }
        }

        // 載入網路設定
        async function loadNetworkSettings() {
            try {
                const response = await fetch('/api/network/settings');
                networkSettings = await response.json();
                
                document.getElementById('currentIP').textContent = networkSettings.current_ip;
                document.getElementById('allowedNetworks').value = networkSettings.allowed_networks;
                document.getElementById('networkCheckEnabled').checked = networkSettings.network_check_enabled === 'true';
            } catch (error) {
                console.error('載入網路設定失敗:', error);
            }
        }

        // 儲存網路設定
        async function saveNetworkSettings() {
            try {
                const settings = {
                    allowed_networks: document.getElementById('allowedNetworks').value,
                    network_check_enabled: document.getElementById('networkCheckEnabled').checked ? 'true' : 'false'
                };
                
                const response = await fetch('/api/network/settings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(settings)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    alert('✅ 網路設定儲存成功！');
                    loadNetworkSettings();
                } else {
                    alert('❌ 儲存失敗：' + result.message);
                }
            } catch (error) {
                alert('❌ 儲存錯誤：' + error.message);
            }
        }

        // 測試當前網路
        async function testCurrentNetwork() {
            try {
                const response = await fetch('/api/network/status');
                const data = await response.json();
                
                const status = data.allowed ? '✅ 允許' : '❌ 拒絕';
                alert(`🧪 網路測試結果\\n\\nIP：${data.ip}\\n狀態：${status}\\n說明：${data.message}`);
            } catch (error) {
                alert('❌ 測試失敗：' + error.message);
            }
        }

        // 加入當前IP到允許列表
        function addCurrentIP() {
            const currentIP = document.getElementById('currentIP').textContent;
            const allowedNetworks = document.getElementById('allowedNetworks');
            
            if (allowedNetworks.value.includes(currentIP)) {
                alert('⚠️ 當前IP已經在允許列表中');
                return;
            }
            
            if (allowedNetworks.value.trim()) {
                allowedNetworks.value += ',' + currentIP;
            } else {
                allowedNetworks.value = currentIP;
            }
            
            alert('✅ 已加入當前IP到允許列表\\n請記得點擊「儲存設定」');
        }

        // 顯示員工列表
        async function showEmployees() {
            try {
                const response = await fetch('/api/employees');
                const employees = await response.json();
                
                let tableHTML = '<table style="width: 100%; border-collapse: collapse; margin-top: 20px;"><thead><tr style="background: #f8f9fa;"><th style="padding: 12px; border-bottom: 1px solid #ddd;">員工編號</th><th style="padding: 12px; border-bottom: 1px solid #ddd;">姓名</th><th style="padding: 12px; border-bottom: 1px solid #ddd;">部門</th><th style="padding: 12px; border-bottom: 1px solid #ddd;">職位</th><th style="padding: 12px; border-bottom: 1px solid #ddd;">權限</th><th style="padding: 12px; border-bottom: 1px solid #ddd;">狀態</th></tr></thead><tbody>';
                
                employees.forEach(emp => {
                    const roleText = emp.role === 'ADMIN' ? '👨‍💼 管理員' : '👤 員工';
                    const statusColor = emp.status === 'active' ? 'green' : 'red';
                    
                    tableHTML += `<tr><td style="padding: 12px; border-bottom: 1px solid #ddd;">${emp.employee_id}</td><td style="padding: 12px; border-bottom: 1px solid #ddd;">${emp.name}</td><td style="padding: 12px; border-bottom: 1px solid #ddd;">${emp.department || '-'}</td><td style="padding: 12px; border-bottom: 1px solid #ddd;">${emp.position || '-'}</td><td style="padding: 12px; border-bottom: 1px solid #ddd;">${roleText}</td><td style="padding: 12px; border-bottom: 1px solid #ddd;"><span style="color: ${statusColor}">${emp.status}</span></td></tr>`;
                });
                
                tableHTML += '</tbody></table>';
                
                document.getElementById('tableTitle').textContent = '👥 員工列表';
                document.getElementById('tableContent').innerHTML = tableHTML;
                document.getElementById('dataTableContainer').classList.remove('hidden');
            } catch (error) {
                alert('載入員工列表失敗');
            }
        }

        // 其他功能函數
        function showAddEmployeeForm() { alert('新增員工功能：請在管理後台實現'); }
        function showPendingRegistrations() { alert('待註冊用戶功能：請在管理後台實現'); }
        function showAttendanceStats() { alert('出勤報表功能開發中...'); }
        function showNetworkLogs() { alert('網路記錄功能開發中...'); }
        function showPendingRequests() { alert('待審項目功能開發中...'); }
        function approvalHistory() { alert('審核記錄功能開發中...'); }
        function systemSettings() { alert('基本設定功能開發中...'); }
        function securitySettings() { alert('安全設定功能開發中...'); }

        // Enter鍵登入
        document.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !document.getElementById('loginOverlay').classList.contains('hidden')) {
                login();
            }
        });
    </script>
</body>
</html>
'''