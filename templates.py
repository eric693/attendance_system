# templates.py - HTML模板模組 (修正版)

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
            <p><strong>允許打卡網路：</strong>172.20.10.0/24, 192.168.101.0/24, 192.168.1.0/24, 147.92.150.192/28</p>
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
            const statusElement = document.getElementById('networkStatus');
            statusElement.innerHTML = '檢查中...';
            
            try {
                const response = await fetch('/api/network/status');
                const data = await response.json();
                
                const statusText = data.allowed ? '✅ 允許打卡' : '❌ 無法打卡';
                
                statusElement.innerHTML = `
                    <strong>IP：${data.ip}</strong><br>
                    <span style="color: ${data.allowed ? 'green' : 'red'}">${statusText}</span><br>
                    <small>${data.message}</small>
                `;
            } catch (error) {
                statusElement.innerHTML = '❌ 無法檢查網路狀態';
            }
        }
        
        // 頁面載入時檢查網路
        window.onload = function() {
            checkNetwork();
        };
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
            min-width: 300px;
        }
        .form-input {
            width: 100%;
            padding: 12px;
            margin: 8px 0;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-size: 14px;
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
            font-size: 14px;
        }
        .btn:hover { transform: translateY(-2px); }
        .card {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            text-align: center;
            background: linear-gradient(135deg, #4CAF50, #45a049);
            color: white;
        }
        .stat-number {
            font-size: 3em;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .hidden { display: none; }
        .status-ok { color: #4CAF50; }
        .status-error { color: #f44336; }
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
        .network-settings {
            background: #e8f5e8;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }
        .alert {
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
        }
        .alert-success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .alert-error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
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
            <p>網路安全版 - 系統自動更新允許的網路範圍</p>
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
            </div>

            <!-- 網路安全設定 -->
            <div class="card">
                <h3>🌐 網路安全設定</h3>
                
                <div class="network-settings">
                    <div style="margin-bottom: 15px;">
                        <label><strong>當前管理員IP：</strong></label>
                        <span id="currentIP" class="status-ok">檢查中...</span>
                    </div>
                    
                    <div style="margin-bottom: 15px;">
                        <label for="allowedNetworks"><strong>允許的網路範圍：</strong></label>
                        <textarea id="allowedNetworks" class="form-textarea" 
                                placeholder="例如：172.20.10.0/24, 192.168.101.0/24, 192.168.1.0/24, 147.92.150.192/28"></textarea>
                    </div>
                    
                    <div style="margin-bottom: 15px;">
                        <label>
                            <input type="checkbox" id="networkCheckEnabled"> 
                            啟用網路檢查
                        </label>
                    </div>
                    
                    <button class="btn" onclick="saveNetworkSettings()">💾 儲存設定</button>
                    <button class="btn" onclick="testCurrentNetwork()">🧪 測試當前網路</button>
                    
                    <div id="networkResult"></div>
                </div>
            </div>

            <!-- 功能區域 -->
            <div class="dashboard-grid">
                <div class="card">
                    <h3>👥 員工管理</h3>
                    <p>員工資料、權限設定（管理員/員工）</p>
                    <button class="btn" onclick="showEmployees()">員工列表</button>
                </div>

                <div class="card">
                    <h3>📊 出勤統計</h3>
                    <p>即時出勤狀況、工時統計、網路記錄</p>
                    <button class="btn" onclick="showAttendanceStats()">出勤報表</button>
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
                    alert('登入失敗：' + (result.message || '帳號或密碼錯誤'));
                }
            } catch (error) {
                alert('登入錯誤：' + error.message);
            }
        }

        // 載入儀表板數據
        async function loadDashboard() {
            try {
                const statsRes = await fetch('/api/attendance/stats');
                const stats = await statsRes.json();
                
                document.getElementById('totalEmployees').textContent = stats.total_employees || 0;
                document.getElementById('todayCheckin').textContent = stats.today_checkin || 0;
                document.getElementById('attendanceRate').textContent = (stats.attendance_rate || 0) + '%';
            } catch (error) {
                console.error('載入數據失敗:', error);
            }
        }

        // 載入網路設定
        async function loadNetworkSettings() {
            try {
                const response = await fetch('/api/network/settings');
                const settings = await response.json();
                
                document.getElementById('currentIP').textContent = settings.current_ip || '未知';
                document.getElementById('allowedNetworks').value = settings.allowed_networks || '';
                document.getElementById('networkCheckEnabled').checked = settings.network_check_enabled === 'true';
            } catch (error) {
                console.error('載入網路設定失敗:', error);
                document.getElementById('currentIP').textContent = '載入失敗';
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
                
                const resultDiv = document.getElementById('networkResult');
                if (result.success) {
                    resultDiv.innerHTML = '<div class="alert alert-success">✅ 網路設定儲存成功！</div>';
                    loadNetworkSettings();
                } else {
                    resultDiv.innerHTML = '<div class="alert alert-error">❌ 儲存失敗：' + (result.message || '未知錯誤') + '</div>';
                }
                
                setTimeout(() => {
                    resultDiv.innerHTML = '';
                }, 3000);
            } catch (error) {
                document.getElementById('networkResult').innerHTML = '<div class="alert alert-error">❌ 儲存錯誤：' + error.message + '</div>';
            }
        }

        // 測試當前網路
        async function testCurrentNetwork() {
            try {
                const response = await fetch('/api/network/status');
                const data = await response.json();
                
                const status = data.allowed ? '✅ 允許' : '❌ 拒絕';
                const resultDiv = document.getElementById('networkResult');
                resultDiv.innerHTML = `<div class="alert ${data.allowed ? 'alert-success' : 'alert-error'}">
                    🧪 網路測試結果<br>
                    IP：${data.ip}<br>
                    狀態：${status}<br>
                    說明：${data.message}
                </div>`;
                
                setTimeout(() => {
                    resultDiv.innerHTML = '';
                }, 5000);
            } catch (error) {
                document.getElementById('networkResult').innerHTML = '<div class="alert alert-error">❌ 測試失敗：' + error.message + '</div>';
            }
        }

        // 顯示員工列表
        async function showEmployees() {
            try {
                const response = await fetch('/api/employees');
                const employees = await response.json();
                
                let tableHTML = `
                    <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
                        <thead>
                            <tr style="background: #f8f9fa;">
                                <th style="padding: 12px; border-bottom: 1px solid #ddd;">員工編號</th>
                                <th style="padding: 12px; border-bottom: 1px solid #ddd;">姓名</th>
                                <th style="padding: 12px; border-bottom: 1px solid #ddd;">部門</th>
                                <th style="padding: 12px; border-bottom: 1px solid #ddd;">職位</th>
                                <th style="padding: 12px; border-bottom: 1px solid #ddd;">權限</th>
                                <th style="padding: 12px; border-bottom: 1px solid #ddd;">狀態</th>
                            </tr>
                        </thead>
                        <tbody>
                `;
                
                if (employees.length === 0) {
                    tableHTML += '<tr><td colspan="6" style="padding: 20px; text-align: center;">暫無員工資料</td></tr>';
                } else {
                    employees.forEach(emp => {
                        const roleText = emp.role === 'ADMIN' ? '👨‍💼 管理員' : '👤 員工';
                        const statusColor = emp.status === 'active' ? 'green' : 'red';
                        
                        tableHTML += `
                            <tr>
                                <td style="padding: 12px; border-bottom: 1px solid #ddd;">${emp.employee_id}</td>
                                <td style="padding: 12px; border-bottom: 1px solid #ddd;">${emp.name}</td>
                                <td style="padding: 12px; border-bottom: 1px solid #ddd;">${emp.department || '-'}</td>
                                <td style="padding: 12px; border-bottom: 1px solid #ddd;">${emp.position || '-'}</td>
                                <td style="padding: 12px; border-bottom: 1px solid #ddd;">${roleText}</td>
                                <td style="padding: 12px; border-bottom: 1px solid #ddd;"><span style="color: ${statusColor}">${emp.status}</span></td>
                            </tr>
                        `;
                    });
                }
                
                tableHTML += '</tbody></table>';
                
                document.getElementById('tableTitle').textContent = '👥 員工列表';
                document.getElementById('tableContent').innerHTML = tableHTML;
                document.getElementById('dataTableContainer').classList.remove('hidden');
            } catch (error) {
                alert('載入員工列表失敗：' + error.message);
            }
        }

        // 顯示出勤報表
        async function showAttendanceStats() {
            document.getElementById('tableTitle').textContent = '📊 出勤報表管理';
            
            const reportHTML = `
                <div style="margin-bottom: 20px;">
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px;">
                        <button class="btn" onclick="loadDailyReport()">📅 每日報表</button>
                        <button class="btn" onclick="loadMonthlyReport()">📈 月度報表</button>
                        <button class="btn" onclick="loadDepartmentReport()">🏢 部門報表</button>
                        <button class="btn" onclick="loadLateReport()">⏰ 遲到統計</button>
                        <button class="btn" onclick="loadNetworkViolations()">🚫 網路違規</button>
                        <button class="btn" onclick="exportReport()">📤 導出報表</button>
                    </div>
                    
                    <div style="display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap;">
                        <input type="date" id="reportDate" class="form-input" style="width: auto;" value="${new Date().toISOString().split('T')[0]}">
                        <select id="reportMonth" class="form-input" style="width: auto;">
                            ${generateMonthOptions()}
                        </select>
                        <select id="reportYear" class="form-input" style="width: auto;">
                            ${generateYearOptions()}
                        </select>
                    </div>
                </div>
                
                <div id="reportContent">
                    <p style="text-align: center; color: #666; padding: 40px;">請選擇上方的報表類型</p>
                </div>
            `;
            
            document.getElementById('tableContent').innerHTML = reportHTML;
            document.getElementById('dataTableContainer').classList.remove('hidden');
        }

        // 產生月份選項
        function generateMonthOptions() {
            const months = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12'];
            const currentMonth = new Date().getMonth() + 1;
            return months.map(month => 
                `<option value="${month}" ${month == currentMonth ? 'selected' : ''}>${month}月</option>`
            ).join('');
        }

        // 產生年份選項
        function generateYearOptions() {
            const currentYear = new Date().getFullYear();
            const years = [];
            for (let i = currentYear - 2; i <= currentYear + 1; i++) {
                years.push(`<option value="${i}" ${i === currentYear ? 'selected' : ''}>${i}年</option>`);
            }
            return years.join('');
        }

        // 載入每日報表
        async function loadDailyReport() {
            const date = document.getElementById('reportDate').value;
            try {
                const response = await fetch(`/api/reports/daily?date=${date}`);
                const data = await response.json();
                
                let tableHTML = `
                    <h4>📅 每日出勤報表 - ${date}</h4>
                    <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
                        <thead>
                            <tr style="background: #f8f9fa;">
                                <th style="padding: 12px; border: 1px solid #ddd;">員工編號</th>
                                <th style="padding: 12px; border: 1px solid #ddd;">姓名</th>
                                <th style="padding: 12px; border: 1px solid #ddd;">部門</th>
                                <th style="padding: 12px; border: 1px solid #ddd;">上班時間</th>
                                <th style="padding: 12px; border: 1px solid #ddd;">下班時間</th>
                                <th style="padding: 12px; border: 1px solid #ddd;">工作時數</th>
                                <th style="padding: 12px; border: 1px solid #ddd;">狀態</th>
                                <th style="padding: 12px; border: 1px solid #ddd;">IP地址</th>
                            </tr>
                        </thead>
                        <tbody>
                `;
                
                if (data.length === 0) {
                    tableHTML += '<tr><td colspan="8" style="padding: 20px; text-align: center;">當日無出勤記錄</td></tr>';
                } else {
                    data.forEach(record => {
                        const statusColor = record.status.includes('遲到') ? 'red' : 
                                          record.status === '未打卡' ? 'orange' : 'green';
                        
                        tableHTML += `
                            <tr>
                                <td style="padding: 12px; border: 1px solid #ddd;">${record.employee_id}</td>
                                <td style="padding: 12px; border: 1px solid #ddd;">${record.name}</td>
                                <td style="padding: 12px; border: 1px solid #ddd;">${record.department || '-'}</td>
                                <td style="padding: 12px; border: 1px solid #ddd;">${record.clock_in ? record.clock_in.split(' ')[1] : '-'}</td>
                                <td style="padding: 12px; border: 1px solid #ddd;">${record.clock_out ? record.clock_out.split(' ')[1] : '-'}</td>
                                <td style="padding: 12px; border: 1px solid #ddd;">${record.working_hours}h</td>
                                <td style="padding: 12px; border: 1px solid #ddd; color: ${statusColor};">${record.status}</td>
                                <td style="padding: 12px; border: 1px solid #ddd;">${record.ip_address}</td>
                            </tr>
                        `;
                    });
                }
                
                tableHTML += '</tbody></table>';
                document.getElementById('reportContent').innerHTML = tableHTML;
            } catch (error) {
                document.getElementById('reportContent').innerHTML = '<div class="alert alert-error">載入每日報表失敗：' + error.message + '</div>';
            }
        }

        // 載入月度報表
        async function loadMonthlyReport() {
            const year = document.getElementById('reportYear').value;
            const month = document.getElementById('reportMonth').value;
            
            try {
                const response = await fetch(`/api/reports/monthly?year=${year}&month=${month}`);
                const data = await response.json();
                
                let tableHTML = `
                    <h4>📈 月度出勤報表 - ${year}年${month}月</h4>
                    <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
                        <thead>
                            <tr style="background: #f8f9fa;">
                                <th style="padding: 12px; border: 1px solid #ddd;">員工編號</th>
                                <th style="padding: 12px; border: 1px solid #ddd;">姓名</th>
                                <th style="padding: 12px; border: 1px solid #ddd;">部門</th>
                                <th style="padding: 12px; border: 1px solid #ddd;">出勤天數</th>
                                <th style="padding: 12px; border: 1px solid #ddd;">總工時</th>
                                <th style="padding: 12px; border: 1px solid #ddd;">平均工時</th>
                                <th style="padding: 12px; border: 1px solid #ddd;">遲到次數</th>
                                <th style="padding: 12px; border: 1px solid #ddd;">打卡完整度</th>
                            </tr>
                        </thead>
                        <tbody>
                `;
                
                if (data.length === 0) {
                    tableHTML += '<tr><td colspan="8" style="padding: 20px; text-align: center;">當月無出勤記錄</td></tr>';
                } else {
                    data.forEach(record => {
                        const completeness = record.checkin_count === record.checkout_count ? '完整' : '不完整';
                        const completenessColor = completeness === '完整' ? 'green' : 'orange';
                        
                        tableHTML += `
                            <tr>
                                <td style="padding: 12px; border: 1px solid #ddd;">${record.employee_id}</td>
                                <td style="padding: 12px; border: 1px solid #ddd;">${record.name}</td>
                                <td style="padding: 12px; border: 1px solid #ddd;">${record.department || '-'}</td>
                                <td style="padding: 12px; border: 1px solid #ddd;">${record.work_days}天</td>
                                <td style="padding: 12px; border: 1px solid #ddd;">${record.total_hours}h</td>
                                <td style="padding: 12px; border: 1px solid #ddd;">${record.avg_hours}h</td>
                                <td style="padding: 12px; border: 1px solid #ddd; color: ${record.late_count > 0 ? 'red' : 'green'};">${record.late_count}次</td>
                                <td style="padding: 12px; border: 1px solid #ddd; color: ${completenessColor};">${completeness}</td>
                            </tr>
                        `;
                    });
                }
                
                tableHTML += '</tbody></table>';
                document.getElementById('reportContent').innerHTML = tableHTML;
            } catch (error) {
                document.getElementById('reportContent').innerHTML = '<div class="alert alert-error">載入月度報表失敗：' + error.message + '</div>';
            }
        }

        // 載入部門報表
        async function loadDepartmentReport() {
            const date = document.getElementById('reportDate').value;
            
            try {
                const response = await fetch(`/api/reports/department?date=${date}`);
                const data = await response.json();
                
                let tableHTML = `
                    <h4>🏢 部門出勤摘要 - ${date}</h4>
                    <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
                        <thead>
                            <tr style="background: #f8f9fa;">
                                <th style="padding: 12px; border: 1px solid #ddd;">部門</th>
                                <th style="padding: 12px; border: 1px solid #ddd;">總員工數</th>
                                <th style="padding: 12px; border: 1px solid #ddd;">出勤人數</th>
                                <th style="padding: 12px; border: 1px solid #ddd;">缺勤人數</th>
                                <th style="padding: 12px; border: 1px solid #ddd;">遲到人數</th>
                                <th style="padding: 12px; border: 1px solid #ddd;">出勤率</th>
                            </tr>
                        </thead>
                        <tbody>
                `;
                
                if (data.length === 0) {
                    tableHTML += '<tr><td colspan="6" style="padding: 20px; text-align: center;">暫無部門資料</td></tr>';
                } else {
                    data.forEach(dept => {
                        const rateColor = dept.attendance_rate >= 90 ? 'green' : 
                                        dept.attendance_rate >= 80 ? 'orange' : 'red';
                        
                        tableHTML += `
                            <tr>
                                <td style="padding: 12px; border: 1px solid #ddd;">${dept.department}</td>
                                <td style="padding: 12px; border: 1px solid #ddd;">${dept.total_employees}</td>
                                <td style="padding: 12px; border: 1px solid #ddd;">${dept.present_count}</td>
                                <td style="padding: 12px; border: 1px solid #ddd;">${dept.absent_count}</td>
                                <td style="padding: 12px; border: 1px solid #ddd;">${dept.late_count}</td>
                                <td style="padding: 12px; border: 1px solid #ddd; color: ${rateColor};">${dept.attendance_rate}%</td>
                            </tr>
                        `;
                    });
                }
                
                tableHTML += '</tbody></table>';
                document.getElementById('reportContent').innerHTML = tableHTML;
            } catch (error) {
                document.getElementById('reportContent').innerHTML = '<div class="alert alert-error">載入部門報表失敗：' + error.message + '</div>';
            }
        }

        // 載入遲到統計
        async function loadLateReport() {
            const year = document.getElementById('reportYear').value;
            const month = document.getElementById('reportMonth').value;
            
            try {
                const response = await fetch(`/api/reports/late?year=${year}&month=${month}`);
                const data = await response.json();
                
                let tableHTML = `
                    <h4>⏰ 遲到統計報表 - ${year}年${month}月</h4>
                    <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
                        <thead>
                            <tr style="background: #f8f9fa;">
                                <th style="padding: 12px; border: 1px solid #ddd;">姓名</th>
                                <th style="padding: 12px; border: 1px solid #ddd;">部門</th>
                                <th style="padding: 12px; border: 1px solid #ddd;">遲到次數</th>
                                <th style="padding: 12px; border: 1px solid #ddd;">遲到日期</th>
                            </tr>
                        </thead>
                        <tbody>
                `;
                
                if (data.length === 0) {
                    tableHTML += '<tr><td colspan="4" style="padding: 20px; text-align: center; color: green;">🎉 本月無人遲到！</td></tr>';
                } else {
                    data.forEach(record => {
                        tableHTML += `
                            <tr>
                                <td style="padding: 12px; border: 1px solid #ddd;">${record.name}</td>
                                <td style="padding: 12px; border: 1px solid #ddd;">${record.department}</td>
                                <td style="padding: 12px; border: 1px solid #ddd; color: red;">${record.late_count}次</td>
                                <td style="padding: 12px; border: 1px solid #ddd;">${record.late_dates.join(', ')}</td>
                            </tr>
                        `;
                    });
                }
                
                tableHTML += '</tbody></table>';
                document.getElementById('reportContent').innerHTML = tableHTML;
            } catch (error) {
                document.getElementById('reportContent').innerHTML = '<div class="alert alert-error">載入遲到統計失敗：' + error.message + '</div>';
            }
        }

        // 載入網路違規記錄
        async function loadNetworkViolations() {
            try {
                const response = await fetch('/api/reports/network-violations');
                const data = await response.json();
                
                let tableHTML = `
                    <h4>🚫 網路違規記錄 (最近30天)</h4>
                    <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
                        <thead>
                            <tr style="background: #f8f9fa;">
                                <th style="padding: 12px; border: 1px solid #ddd;">時間</th>
                                <th style="padding: 12px; border: 1px solid #ddd;">姓名</th>
                                <th style="padding: 12px; border: 1px solid #ddd;">部門</th>
                                <th style="padding: 12px; border: 1px solid #ddd;">操作</th>
                                <th style="padding: 12px; border: 1px solid #ddd;">IP地址</th>
                                <th style="padding: 12px; border: 1px solid #ddd;">網路資訊</th>
                            </tr>
                        </thead>
                        <tbody>
                `;
                
                if (data.length === 0) {
                    tableHTML += '<tr><td colspan="6" style="padding: 20px; text-align: center; color: green;">🎉 近期無網路違規記錄！</td></tr>';
                } else {
                    data.forEach(record => {
                        tableHTML += `
                            <tr>
                                <td style="padding: 12px; border: 1px solid #ddd;">${record.time}</td>
                                <td style="padding: 12px; border: 1px solid #ddd;">${record.name}</td>
                                <td style="padding: 12px; border: 1px solid #ddd;">${record.department}</td>
                                <td style="padding: 12px; border: 1px solid #ddd;">${record.action}</td>
                                <td style="padding: 12px; border: 1px solid #ddd; color: red;">${record.ip_address}</td>
                                <td style="padding: 12px; border: 1px solid #ddd;">${record.network_info}</td>
                            </tr>
                        `;
                    });
                }
                
                tableHTML += '</tbody></table>';
                document.getElementById('reportContent').innerHTML = tableHTML;
            } catch (error) {
                document.getElementById('reportContent').innerHTML = '<div class="alert alert-error">載入網路違規記錄失敗：' + error.message + '</div>';
            }
        }

        // 導出報表
        async function exportReport() {
            const date = document.getElementById('reportDate').value;
            const reportType = 'daily'; // 可以根據需要修改
            
            try {
                const response = await fetch(`/api/reports/export/csv?type=${reportType}&date=${date}`);
                
                if (response.ok) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `attendance_report_${date}.csv`;
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                    
                    alert('✅ 報表導出成功！');
                } else {
                    alert('❌ 導出失敗');
                }
            } catch (error) {
                alert('❌ 導出錯誤：' + error.message);
            }
        }

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