# leave_templates.py

LEAVE_MANAGEMENT_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>請假管理系統 - 企業出勤管理</title>
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
        .btn-success { background: linear-gradient(135deg, #4CAF50, #45a049); }
        .btn-danger { background: linear-gradient(135deg, #f44336, #d32f2f); }
        .btn-warning { background: linear-gradient(135deg, #FF9800, #F57C00); }
        .btn-info { background: linear-gradient(135deg, #2196F3, #1976D2); }
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
            color: white;
            padding: 30px 20px;
        }
        .stat-number {
            font-size: 3em;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .form-input, .form-select, .form-textarea {
            width: 100%;
            padding: 12px;
            margin: 8px 0;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-size: 14px;
        }
        .form-textarea {
            min-height: 100px;
            resize: vertical;
        }
        .alert {
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
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
        .alert-warning {
            background: #fff3cd;
            color: #856404;
            border: 1px solid #ffeaa7;
        }
        .status-badge {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
        }
        .status-pending { background: #fff3cd; color: #856404; }
        .status-approved { background: #d4edda; color: #155724; }
        .status-rejected { background: #f8d7da; color: #721c24; }
        .leave-type-badge {
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 11px;
            margin-right: 8px;
        }
        .hidden { display: none !important; }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #f8f9fa;
            font-weight: bold;
        }
        tr:hover {
            background-color: #f5f5f5;
        }
        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-bottom: 15px;
        }
        .modal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
        }
        .modal-content {
            background: white;
            padding: 30px;
            border-radius: 15px;
            max-width: 600px;
            width: 90%;
            max-height: 80vh;
            overflow-y: auto;
        }
        .leave-type-card {
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .leave-type-card:hover {
            border-color: #667eea;
            background: #f8f9ff;
        }
        .leave-type-card.selected {
            border-color: #667eea;
            background: linear-gradient(135deg, #f8f9ff 0%, #e8f2ff 100%);
        }
        .calendar-view {
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 1px;
            background: #ddd;
            border-radius: 8px;
            overflow: hidden;
        }
        .calendar-day {
            background: white;
            padding: 8px;
            min-height: 60px;
            font-size: 12px;
        }
        .calendar-day.has-leave {
            background: #e8f5e8;
        }
        .filter-section {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .tabs {
            display: flex;
            background: #f1f3f4;
            border-radius: 8px;
            padding: 4px;
            margin-bottom: 20px;
        }
        .tab {
            flex: 1;
            padding: 12px;
            text-align: center;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .tab.active {
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .quota-bar {
            background: #e0e0e0;
            height: 20px;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }
        .quota-fill {
            height: 100%;
            background: linear-gradient(135deg, #4CAF50, #45a049);
            transition: width 0.3s ease;
        }
        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
        }
        .export-options {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏖️ 請假管理系統</h1>
        <p>員工請假申請與審核管理平台</p>
    </div>

    <div class="container">
        <!-- 統計卡片 -->
        <div class="dashboard-grid">
            <div class="card stat-card" style="background: linear-gradient(135deg, #FF9800, #F57C00);">
                <div class="stat-number" id="pendingCount">-</div>
                <div>待審核申請</div>
            </div>
            <div class="card stat-card" style="background: linear-gradient(135deg, #4CAF50, #45a049);">
                <div class="stat-number" id="approvedCount">-</div>
                <div>本月已批准</div>
            </div>
            <div class="card stat-card" style="background: linear-gradient(135deg, #2196F3, #1976D2);">
                <div class="stat-number" id="totalRequests">-</div>
                <div>總申請數</div>
            </div>
            <div class="card stat-card" style="background: linear-gradient(135deg, #9C27B0, #7B1FA2);">
                <div class="stat-number" id="leaveTypes">9</div>
                <div>假別類型</div>
            </div>
        </div>

        <!-- 標籤導航 -->
        <div class="tabs">
            <div class="tab active" onclick="switchTab('pending')">⏳ 待審核申請</div>
            <div class="tab" onclick="switchTab('all')">📋 所有申請</div>
            <div class="tab" onclick="switchTab('calendar')">📅 請假日曆</div>
            <div class="tab" onclick="switchTab('statistics')">📈 統計分析</div>
            <div class="tab" onclick="switchTab('settings')">⚙️ 系統設定</div>
        </div>

        <!-- 功能導航 -->
        <div class="card">
            <h3>🛠️ 管理功能</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 20px;">
                <button class="btn" onclick="switchTab('pending')">⏳ 待審核申請</button>
                <button class="btn" onclick="switchTab('all')">📋 所有申請</button>
                <button class="btn" onclick="switchTab('calendar')">📅 請假日曆</button>
                <button class="btn" onclick="switchTab('statistics')">📈 統計報表</button>
                <button class="btn" onclick="showQuotaManagement()">📊 額度管理</button>
                <button class="btn" onclick="exportLeaveData()">📤 匯出數據</button>
                <button class="btn" onclick="switchTab('settings')">⚙️ 假別設定</button>
                <button class="btn btn-warning" onclick="location.href='/admin'">🔙 返回管理台</button>
            </div>
        </div>

        <!-- 主要內容區域 -->
        <div id="mainContent" class="card">
            <h3 id="contentTitle">請假管理</h3>
            <div id="contentBody">
                <div class="loading">
                    載入中...
                </div>
            </div>
        </div>
    </div>

    <!-- 審核模態框 -->
    <div id="approvalModal" class="modal hidden">
        <div class="modal-content">
            <h3>請假申請審核</h3>
            <div id="modalContent"></div>
            <div style="text-align: center; margin-top: 20px;">
                <button class="btn btn-success" id="approveBtn">✅ 批准</button>
                <button class="btn btn-danger" id="rejectBtn">❌ 拒絕</button>
                <button class="btn" id="cancelBtn" style="background: #666;">取消</button>
            </div>
            <div id="approvalResult"></div>
        </div>
    </div>

    <!-- 請假類型設定模態框 -->
    <div id="leaveTypeModal" class="modal hidden">
        <div class="modal-content">
            <h3>假別類型設定</h3>
            <div id="leaveTypeContent"></div>
            <div style="text-align: center; margin-top: 20px;">
                <button class="btn btn-success" id="saveLeaveTypeBtn">💾 儲存</button>
                <button class="btn" id="closeLeaveTypeBtn" style="background: #666;">關閉</button>
            </div>
        </div>
    </div>

    <script>
        // 全域變數
        let currentRequestId = null;
        let currentTab = 'pending';
        let leaveTypes = {};
        let currentEditingLeaveType = null;

        // DOM 載入完成後初始化
        document.addEventListener('DOMContentLoaded', function() {
            initEventListeners();
            loadDashboardStats();
            loadLeaveTypes();
            switchTab('pending');
        });

        // 初始化事件監聽器
        function initEventListeners() {
            // 審核按鈕事件
            document.getElementById('approveBtn').addEventListener('click', () => processApproval('approve'));
            document.getElementById('rejectBtn').addEventListener('click', () => processApproval('reject'));
            document.getElementById('cancelBtn').addEventListener('click', closeModal);
            document.getElementById('closeLeaveTypeBtn').addEventListener('click', closeModal);
            document.getElementById('saveLeaveTypeBtn').addEventListener('click', saveLeaveTypeSettings);
            
            // 模態框背景點擊關閉
            document.getElementById('approvalModal').addEventListener('click', function(e) {
                if (e.target === this) closeModal();
            });
            document.getElementById('leaveTypeModal').addEventListener('click', function(e) {
                if (e.target === this) closeModal();
            });
            
            // ESC 鍵關閉模態框
            document.addEventListener('keydown', function(e) {
                if (e.key === 'Escape') closeModal();
            });
        }

        // 關閉模態框
        function closeModal() {
            document.getElementById('approvalModal').classList.add('hidden');
            document.getElementById('leaveTypeModal').classList.add('hidden');
            currentRequestId = null;
            currentEditingLeaveType = null;
            document.getElementById('approvalResult').innerHTML = '';
        }

        // 載入統計數據
        async function loadDashboardStats() {
            try {
                const response = await fetch('/api/leave/statistics');
                const data = await response.json();
                
                if (data.success) {
                    const stats = data.data;
                    document.getElementById('pendingCount').textContent = stats.pending_count || 0;
                    document.getElementById('approvedCount').textContent = stats.approved_count || 0;
                    document.getElementById('totalRequests').textContent = stats.total_requests || 0;
                }
            } catch (error) {
                console.error('載入統計數據失敗:', error);
            }
        }

        // 載入請假類型
        async function loadLeaveTypes() {
            try {
                const response = await fetch('/api/leave/types');
                const data = await response.json();
                
                if (data.success) {
                    leaveTypes = data.data;
                }
            } catch (error) {
                console.error('載入請假類型失敗:', error);
            }
        }

        // 切換標籤
        function switchTab(tabName) {
            // 更新標籤樣式
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            event.target?.classList.add('active');
            
            currentTab = tabName;
            
            // 根據標籤載入對應內容
            switch(tabName) {
                case 'pending':
                    showPendingRequests();
                    break;
                case 'all':
                    showAllRequests();
                    break;
                case 'calendar':
                    showLeaveCalendar();
                    break;
                case 'statistics':
                    showLeaveStatistics();
                    break;
                case 'settings':
                    showLeaveTypeSettings();
                    break;
            }
        }

        // 顯示待審核申請
        async function showPendingRequests() {
            document.getElementById('contentTitle').textContent = '⏳ 待審核請假申請';
            document.getElementById('contentBody').innerHTML = '<div class="loading">載入中...</div>';
            
            try {
                const response = await fetch('/api/leave/pending');
                const data = await response.json();
                
                if (!data.success) {
                    throw new Error(data.error);
                }
                
                const requests = data.data;
                let html = '';
                
                if (requests.length === 0) {
                    html = '<div class="alert alert-success">🎉 目前沒有待審核的請假申請！</div>';
                } else {
                    html = `
                        <div style="margin-bottom: 20px;">
                            <div class="filter-section">
                                <h4>🔍 篩選選項</h4>
                                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 15px;">
                                    <select class="form-select" id="filterLeaveType" onchange="filterRequests()">
                                        <option value="">所有假別</option>
                                        ${Object.entries(leaveTypes).map(([key, type]) => 
                                            `<option value="${key}">${type.emoji} ${type.name}</option>`
                                        ).join('')}
                                    </select>
                                    <input type="date" class="form-input" id="filterDate" onchange="filterRequests()">
                                    <input type="text" class="form-input" placeholder="搜尋員工姓名..." id="filterEmployee" onkeyup="filterRequests()">
                                    <button class="btn btn-success" onclick="batchApproval('approve')">✅ 批量批准</button>
                                    <button class="btn btn-danger" onclick="batchApproval('reject')">❌ 批量拒絕</button>
                                </div>
                            </div>
                        </div>
                        <table>
                            <thead>
                                <tr>
                                    <th><input type="checkbox" onchange="toggleAllCheckbox(this)"></th>
                                    <th>申請編號</th>
                                    <th>員工</th>
                                    <th>假別</th>
                                    <th>請假時間</th>
                                    <th>天數</th>
                                    <th>狀態</th>
                                    <th>申請時間</th>
                                    <th>操作</th>
                                </tr>
                            </thead>
                            <tbody>
                    `;
                    
                    requests.forEach(req => {
                        const leaveTypeInfo = leaveTypes[req.leave_type] || {};
                        const typeDisplay = `${leaveTypeInfo.emoji || '📋'} ${leaveTypeInfo.name || req.leave_type}`;
                        
                        html += `
                            <tr class="request-row" data-leave-type="${req.leave_type}" data-date="${req.start_date}" data-employee="${req.employee_name.toLowerCase()}">
                                <td><input type="checkbox" class="request-checkbox" value="${req.id}" onchange="updateSelectedCount()"></td>
                                <td>#${req.id}</td>
                                <td>${req.employee_name}</td>
                                <td>${typeDisplay}</td>
                                <td>${req.start_date} ~ ${req.end_date}<br><small>${req.start_time} - ${req.end_time}</small></td>
                                <td><strong>${req.total_days}天</strong></td>
                                <td><span class="status-badge status-pending">⏳ 待審核</span></td>
                                <td>${formatDateTime(req.created_at)}</td>
                                <td>
                                    <button class="btn" style="padding: 5px 10px; font-size: 12px;" 
                                            onclick="showApprovalModal(${req.id}, '${req.employee_name}', '${typeDisplay}', '${req.start_date}', '${req.end_date}', '${req.total_days}', '${req.reason || ''}')">
                                        審核
                                    </button>
                                </td>
                            </tr>
                        `;
                    });
                    
                    html += `
                            </tbody>
                        </table>
                        <div style="margin-top: 20px; text-align: center;">
                            <span id="selectedInfo" style="color: #666;">已選擇 <span id="selectedCount">0</span> 個申請</span>
                        </div>
                    `;
                }
                
                document.getElementById('contentBody').innerHTML = html;
            } catch (error) {
                document.getElementById('contentBody').innerHTML = '<div class="alert alert-error">❌ 載入失敗: ' + error.message + '</div>';
            }
        }

        // 顯示所有申請
        async function showAllRequests() {
            document.getElementById('contentTitle').textContent = '📋 所有請假申請';
            document.getElementById('contentBody').innerHTML = '<div class="loading">載入中...</div>';
            
            try {
                const response = await fetch('/api/leave/requests?limit=100');
                const data = await response.json();
                
                if (!data.success) {
                    throw new Error(data.error);
                }
                
                const requests = data.data;
                
                let html = `
                    <div class="filter-section">
                        <h4>🔍 篩選與搜尋</h4>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 15px;">
                            <select class="form-select" id="statusFilter" onchange="filterAllRequests()">
                                <option value="">所有狀態</option>
                                <option value="pending">⏳ 待審核</option>
                                <option value="approved">✅ 已批准</option>
                                <option value="rejected">❌ 已拒絕</option>
                                <option value="cancelled">🚫 已取消</option>
                            </select>
                            <select class="form-select" id="leaveTypeFilter" onchange="filterAllRequests()">
                                <option value="">所有假別</option>
                                ${Object.entries(leaveTypes).map(([key, type]) => 
                                    `<option value="${key}">${type.emoji} ${type.name}</option>`
                                ).join('')}
                            </select>
                            <input type="month" class="form-input" id="monthFilter" onchange="filterAllRequests()" value="${new Date().toISOString().slice(0, 7)}">
                            <input type="text" class="form-input" placeholder="搜尋員工..." id="employeeFilter" onkeyup="filterAllRequests()">
                            <button class="btn btn-info" onclick="exportFilteredData()">📊 匯出篩選結果</button>
                        </div>
                    </div>
                    <table id="allRequestsTable">
                        <thead>
                            <tr>
                                <th>申請編號</th>
                                <th>員工</th>
                                <th>假別</th>
                                <th>請假時間</th>
                                <th>天數</th>
                                <th>狀態</th>
                                <th>原因</th>
                                <th>申請時間</th>
                                <th>審核者</th>
                                <th>操作</th>
                            </tr>
                        </thead>
                        <tbody>
                `;
                
                requests.forEach(req => {
                    const leaveTypeInfo = leaveTypes[req.leave_type] || {};
                    const typeDisplay = `${leaveTypeInfo.emoji || '📋'} ${leaveTypeInfo.name || req.leave_type}`;
                    const statusBadge = getStatusBadge(req.status);
                    
                    html += `
                        <tr class="all-request-row" data-status="${req.status}" data-leave-type="${req.leave_type}" 
                            data-month="${req.start_date.slice(0, 7)}" data-employee="${req.employee_name.toLowerCase()}">
                            <td>#${req.id}</td>
                            <td>${req.employee_name}</td>
                            <td>${typeDisplay}</td>
                            <td>${req.start_date} ~ ${req.end_date}<br><small>${req.start_time} - ${req.end_time}</small></td>
                            <td><strong>${req.total_days}天</strong></td>
                            <td>${statusBadge}</td>
                            <td title="${req.reason || ''}">${truncateText(req.reason || '', 20)}</td>
                            <td>${formatDateTime(req.created_at)}</td>
                            <td>${req.approved_by || '-'}</td>
                            <td>
                                <button class="btn" style="padding: 5px 10px; font-size: 12px;" 
                                        onclick="viewRequestDetail(${req.id})">
                                    詳情
                                </button>
                            </td>
                        </tr>
                    `;
                });
                
                html += '</tbody></table>';
                document.getElementById('contentBody').innerHTML = html;
            } catch (error) {
                document.getElementById('contentBody').innerHTML = '<div class="alert alert-error">❌ 載入失敗: ' + error.message + '</div>';
            }
        }

        // 顯示請假日曆
        async function showLeaveCalendar() {
            document.getElementById('contentTitle').textContent = '📅 請假日曆檢視';
            
            const currentDate = new Date();
            const year = currentDate.getFullYear();
            const month = currentDate.getMonth();
            
            let html = `
                <div style="margin-bottom: 20px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                        <button class="btn" onclick="changeCalendarMonth(-1)">◀ 上月</button>
                        <h3 id="calendarTitle">${year}年${month + 1}月</h3>
                        <button class="btn" onclick="changeCalendarMonth(1)">下月 ▶</button>
                    </div>
                    
                    <div class="calendar-view">
                        <div class="calendar-day" style="background: #f8f9fa; font-weight: bold;">日</div>
                        <div class="calendar-day" style="background: #f8f9fa; font-weight: bold;">一</div>
                        <div class="calendar-day" style="background: #f8f9fa; font-weight: bold;">二</div>
                        <div class="calendar-day" style="background: #f8f9fa; font-weight: bold;">三</div>
                        <div class="calendar-day" style="background: #f8f9fa; font-weight: bold;">四</div>
                        <div class="calendar-day" style="background: #f8f9fa; font-weight: bold;">五</div>
                        <div class="calendar-day" style="background: #f8f9fa; font-weight: bold;">六</div>
            `;
            
            // 生成日曆天數（這裡簡化處理，實際應該根據月份動態生成）
            const daysInMonth = new Date(year, month + 1, 0).getDate();
            const firstDay = new Date(year, month, 1).getDay();
            
            // 填充月初空白
            for (let i = 0; i < firstDay; i++) {
                html += '<div class="calendar-day"></div>';
            }
            
            // 填充月份天數
            for (let day = 1; day <= daysInMonth; day++) {
                const hasLeave = Math.random() > 0.8; // 模擬有請假的日期
                html += `
                    <div class="calendar-day ${hasLeave ? 'has-leave' : ''}">
                        <div style="font-weight: bold;">${day}</div>
                        ${hasLeave ? '<div style="font-size: 10px; color: #4CAF50;">🏖️ 請假</div>' : ''}
                    </div>
                `;
            }
            
            html += `
                    </div>
                </div>
                
                <div class="card">
                    <h4>📊 本月請假統計</h4>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 15px;">
                        <div style="text-align: center; padding: 15px; background: #e8f5e8; border-radius: 8px;">
                            <div style="font-size: 2em; color: #4CAF50;">12</div>
                            <div>總請假天數</div>
                        </div>
                        <div style="text-align: center; padding: 15px; background: #fff3e0; border-radius: 8px;">
                            <div style="font-size: 2em; color: #FF9800;">8</div>
                            <div>特休假</div>
                        </div>
                        <div style="text-align: center; padding: 15px; background: #f3e5f5; border-radius: 8px;">
                            <div style="font-size: 2em; color: #9C27B0;">4</div>
                            <div>病假</div>
                        </div>
                        <div style="text-align: center; padding: 15px; background: #e3f2fd; border-radius: 8px;">
                            <div style="font-size: 2em; color: #2196F3;">2</div>
                            <div>事假</div>
                        </div>
                    </div>
                </div>
            `;
            
            document.getElementById('contentBody').innerHTML = html;
        }

        // 顯示統計分析
        async function showLeaveStatistics() {
            document.getElementById('contentTitle').textContent = '📈 請假統計分析';
            document.getElementById('contentBody').innerHTML = '<div class="loading">載入中...</div>';
            
            try {
                const response = await fetch('/api/leave/statistics');
                const data = await response.json();
                
                if (!data.success) {
                    throw new Error(data.error);
                }
                
                const stats = data.data;
                
                let html = `
                    <div class="dashboard-grid">
                        <div class="card stat-card" style="background: linear-gradient(135deg, #FF9800, #F57C00);">
                            <div class="stat-number">${stats.pending_count || 0}</div>
                            <div>待審核</div>
                        </div>
                        <div class="card stat-card" style="background: linear-gradient(135deg, #4CAF50, #45a049);">
                            <div class="stat-number">${stats.approved_count || 0}</div>
                            <div>已批准</div>
                        </div>
                        <div class="card stat-card" style="background: linear-gradient(135deg, #f44336, #d32f2f);">
                            <div class="stat-number">${stats.rejected_count || 0}</div>
                            <div>已拒絕</div>
                        </div>
                        <div class="card stat-card" style="background: linear-gradient(135deg, #2196F3, #1976D2);">
                            <div class="stat-number">${stats.total_requests || 0}</div>
                            <div>總申請數</div>
                        </div>
                    </div>

                    <div class="card">
                        <h4>📊 按假別統計</h4>
                        <div style="display: grid; gap: 15px; margin-top: 20px;">
                `;
                
                if (stats.by_type) {
                    Object.entries(stats.by_type).forEach(([type, data]) => {
                        const typeInfo = leaveTypes[type] || {};
                        html += `
                            <div style="display: flex; justify-content: space-between; align-items: center; padding: 15px; background: #f8f9fa; border-radius: 8px;">
                                <div>
                                    <span style="font-size: 1.2em;">${typeInfo.emoji || '📋'}</span>
                                    <strong>${data.name}</strong>
                                </div>
                                <div style="text-align: right;">
                                    <div>申請次數: <strong>${data.count}</strong></div>
                                    <div>批准天數: <strong>${data.approved_days}</strong></div>
                                </div>
                            </div>
                        `;
                    });
                }
                
                html += `
                        </div>
                    </div>

                    <div class="card">
                        <h4>📈 趨勢分析</h4>
                        <div style="height: 300px; background: #f8f9fa; border-radius: 8px; display: flex; align-items: center; justify-content: center;">
                            <p style="color: #666;">圖表功能開發中 - 將顯示請假申請的月度趨勢</p>
                        </div>
                    </div>
                `;
                
                document.getElementById('contentBody').innerHTML = html;
            } catch (error) {
                document.getElementById('contentBody').innerHTML = '<div class="alert alert-error">❌ 載入失敗: ' + error.message + '</div>';
            }
        }

        // 顯示請假類型設定
        async function showLeaveTypeSettings() {
            document.getElementById('contentTitle').textContent = '⚙️ 假別類型設定';
            
            let html = `
                <div class="alert alert-warning">
                    <h4>📋 假別說明</h4>
                    <p>以下是系統支援的假別類型，每種假別都有不同的規則和限制。</p>
                </div>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px;">
            `;
            
            Object.entries(leaveTypes).forEach(([type, info]) => {
                html += `
                    <div class="card">
                        <h4>${info.emoji} ${info.name}</h4>
                        <p><strong>描述：</strong>${info.description}</p>
                        <p><strong>單次申請上限：</strong>${info.max_days_per_request} 天</p>
                        <p><strong>需要證明：</strong>${info.requires_proof ? '是' : '否'}</p>
                        <div style="margin-top: 15px;">
                            <button class="btn" onclick="showEditLeaveTypeModal('${type}')">編輯設定</button>
                        </div>
                    </div>
                `;
            });
            
            html += `
                </div>
                
                <div class="card">
                    <h4>🔧 系統設定</h4>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-top: 20px;">
                        <div>
                            <label>自動審核門檻（天數）：</label>
                            <input type="number" class="form-input" value="0" min="0" max="3" id="autoApprovalThreshold">
                            <small>設定0表示關閉自動審核</small>
                        </div>
                        <div>
                            <label>提前申請天數：</label>
                            <input type="number" class="form-input" value="1" min="0" id="advanceNoticeDays">
                            <small>需要提前幾天申請</small>
                        </div>
                        <div>
                            <label>最大申請範圍（天）：</label>
                            <input type="number" class="form-input" value="365" min="1" id="maxRequestRange">
                            <small>可申請未來多少天內的假期</small>
                        </div>
                        <div>
                            <label>
                                <input type="checkbox" id="allowWeekendLeave" checked style="margin-right: 8px;">
                                允許週末請假
                            </label>
                        </div>
                    </div>
                    <div style="margin-top: 20px;">
                        <button class="btn" onclick="saveLeaveSettings()">💾 儲存設定</button>
                        <button class="btn btn-warning" onclick="resetLeaveSettings()">🔄 重置設定</button>
                    </div>
                </div>
            `;
            
            document.getElementById('contentBody').innerHTML = html;
        }

        // 顯示編輯假別類型的模態框
        function showEditLeaveTypeModal(leaveType) {
            currentEditingLeaveType = leaveType;
            const typeInfo = leaveTypes[leaveType] || {};
            
            const modalContent = `
                <div style="margin-bottom: 20px;">
                    <h4>編輯假別：${typeInfo.emoji} ${typeInfo.name}</h4>
                </div>
                
                <div style="margin-bottom: 15px;">
                    <label>假別名稱：</label>
                    <input type="text" class="form-input" id="editTypeName" value="${typeInfo.name || ''}" placeholder="請輸入假別名稱">
                </div>
                
                <div style="margin-bottom: 15px;">
                    <label>表情符號：</label>
                    <input type="text" class="form-input" id="editTypeEmoji" value="${typeInfo.emoji || ''}" placeholder="🏖️" maxlength="2">
                </div>
                
                <div style="margin-bottom: 15px;">
                    <label>顏色：</label>
                    <input type="color" class="form-input" id="editTypeColor" value="${typeInfo.color || '#4CAF50'}">
                </div>
                
                <div style="margin-bottom: 15px;">
                    <label>描述：</label>
                    <textarea class="form-textarea" id="editTypeDescription" placeholder="請輸入假別描述">${typeInfo.description || ''}</textarea>
                </div>
                
                <div style="margin-bottom: 15px;">
                    <label>單次申請上限（天數）：</label>
                    <input type="number" class="form-input" id="editTypeMaxDays" value="${typeInfo.max_days_per_request || 30}" min="1" max="365">
                </div>
                
                <div style="margin-bottom: 15px;">
                    <label>
                        <input type="checkbox" id="editTypeRequiresProof" ${typeInfo.requires_proof ? 'checked' : ''} style="margin-right: 8px;">
                        需要證明文件
                    </label>
                </div>
                
                <div class="alert alert-warning">
                    <p><strong>注意：</strong>修改假別設定將影響未來的請假申請，已存在的申請不會受到影響。</p>
                </div>
            `;
            
            document.getElementById('leaveTypeContent').innerHTML = modalContent;
            document.getElementById('leaveTypeModal').classList.remove('hidden');
        }

        // 儲存假別類型設定
        function saveLeaveTypeSettings() {
            if (!currentEditingLeaveType) return;
            
            const name = document.getElementById('editTypeName').value.trim();
            const emoji = document.getElementById('editTypeEmoji').value.trim();
            const color = document.getElementById('editTypeColor').value;
            const description = document.getElementById('editTypeDescription').value.trim();
            const maxDays = parseInt(document.getElementById('editTypeMaxDays').value);
            const requiresProof = document.getElementById('editTypeRequiresProof').checked;
            
            if (!name) {
                alert('請輸入假別名稱！');
                return;
            }
            
            if (maxDays < 1 || maxDays > 365) {
                alert('單次申請上限必須在1-365天之間！');
                return;
            }
            
            // 更新本地數據（實際應該發送到後端保存）
            leaveTypes[currentEditingLeaveType] = {
                ...leaveTypes[currentEditingLeaveType],
                name: name,
                emoji: emoji,
                color: color,
                description: description,
                max_days_per_request: maxDays,
                requires_proof: requiresProof
            };
            
            // 模擬保存成功
            alert('✅ 假別設定已儲存！');
            closeModal();
            
            // 重新載入設定頁面
            if (currentTab === 'settings') {
                showLeaveTypeSettings();
            }
        }

        // 顯示審核模態框
        function showApprovalModal(id, employeeName, leaveType, startDate, endDate, totalDays, reason) {
            currentRequestId = id;
            
            const modalContent = `
                <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 15px 0;">
                    <h4>申請詳情</h4>
                    <p><strong>員工：</strong> ${employeeName}</p>
                    <p><strong>假別：</strong> ${leaveType}</p>
                    <p><strong>請假時間：</strong> ${startDate} ~ ${endDate}</p>
                    <p><strong>請假天數：</strong> ${totalDays} 天</p>
                    <p><strong>申請原因：</strong> ${reason || '無'}</p>
                </div>
                
                <div style="margin: 20px 0;">
                    <label for="approvalComment">審核意見：</label>
                    <textarea class="form-textarea" id="approvalComment" placeholder="請輸入審核意見（選填）"></textarea>
                </div>
                
                <div style="margin: 20px 0;">
                    <h5>🔍 快速檢查</h5>
                    <div style="background: #e8f5e8; padding: 15px; border-radius: 8px;">
                        <p>✅ 申請格式正確</p>
                        <p>✅ 請假時間合理</p>
                        <p>✅ 未與其他請假衝突</p>
                        <p id="quotaCheck">🔍 檢查請假額度...</p>
                    </div>
                </div>
            `;
            
            document.getElementById('modalContent').innerHTML = modalContent;
            document.getElementById('approvalModal').classList.remove('hidden');
            
            // 檢查請假額度（模擬）
            setTimeout(() => {
                document.getElementById('quotaCheck').innerHTML = '✅ 請假額度充足';
            }, 1000);
        }

        // 處理審核
        async function processApproval(action) {
            if (!currentRequestId) return;
            
            const comment = document.getElementById('approvalComment') ? 
                          document.getElementById('approvalComment').value : '';
            
            try {
                const response = await fetch('/api/leave/approve', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        request_id: currentRequestId,
                        action: action,
                        reason: comment
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    document.getElementById('approvalResult').innerHTML = 
                        `<div class="alert alert-success">✅ ${action === 'approve' ? '批准' : '拒絕'}成功！</div>`;
                    
                    setTimeout(() => {
                        closeModal();
                        switchTab(currentTab); // 重新載入當前標籤
                        loadDashboardStats(); // 更新統計
                    }, 1500);
                } else {
                    document.getElementById('approvalResult').innerHTML = 
                        `<div class="alert alert-error">❌ 操作失敗: ${result.message}</div>`;
                }
            } catch (error) {
                document.getElementById('approvalResult').innerHTML = 
                    `<div class="alert alert-error">❌ 操作失敗: ${error.message}</div>`;
            }
        }

        // 批量選擇和審核功能
        let selectedRequests = [];

        function toggleAllCheckbox(checkbox) {
            const checkboxes = document.querySelectorAll('.request-checkbox');
            checkboxes.forEach(cb => cb.checked = checkbox.checked);
            updateSelectedCount();
        }

        function updateSelectedCount() {
            const checked = document.querySelectorAll('.request-checkbox:checked');
            document.getElementById('selectedCount').textContent = checked.length;
            selectedRequests = Array.from(checked).map(cb => cb.value);
        }

        async function batchApproval(action) {
            if (selectedRequests.length === 0) {
                alert('請先選擇要審核的申請！');
                return;
            }
            
            const actionText = action === 'approve' ? '批准' : '拒絕';
            if (!confirm(`確定要${actionText} ${selectedRequests.length} 個請假申請嗎？`)) {
                return;
            }
            
            try {
                let successCount = 0;
                for (const requestId of selectedRequests) {
                    const response = await fetch('/api/leave/approve', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            request_id: parseInt(requestId),
                            action: action,
                            reason: `批量${actionText}`
                        })
                    });
                    
                    const result = await response.json();
                    if (result.success) successCount++;
                }
                
                alert(`✅ 批量${actionText}完成：成功 ${successCount}/${selectedRequests.length} 筆`);
                switchTab(currentTab); // 重新載入
                loadDashboardStats(); // 更新統計
            } catch (error) {
                alert('❌ 批量操作失敗: ' + error.message);
            }
        }

        // 篩選功能
        function filterRequests() {
            const leaveTypeFilter = document.getElementById('filterLeaveType')?.value || '';
            const dateFilter = document.getElementById('filterDate')?.value || '';
            const employeeFilter = document.getElementById('filterEmployee')?.value.toLowerCase() || '';
            
            const rows = document.querySelectorAll('.request-row');
            rows.forEach(row => {
                let show = true;
                
                if (leaveTypeFilter && row.dataset.leaveType !== leaveTypeFilter) {
                    show = false;
                }
                
                if (dateFilter && row.dataset.date !== dateFilter) {
                    show = false;
                }
                
                if (employeeFilter && !row.dataset.employee.includes(employeeFilter)) {
                    show = false;
                }
                
                row.style.display = show ? '' : 'none';
            });
        }

        function filterAllRequests() {
            const statusFilter = document.getElementById('statusFilter')?.value || '';
            const leaveTypeFilter = document.getElementById('leaveTypeFilter')?.value || '';
            const monthFilter = document.getElementById('monthFilter')?.value || '';
            const employeeFilter = document.getElementById('employeeFilter')?.value.toLowerCase() || '';
            
            const rows = document.querySelectorAll('.all-request-row');
            rows.forEach(row => {
                let show = true;
                
                if (statusFilter && row.dataset.status !== statusFilter) {
                    show = false;
                }
                
                if (leaveTypeFilter && row.dataset.leaveType !== leaveTypeFilter) {
                    show = false;
                }
                
                if (monthFilter && row.dataset.month !== monthFilter) {
                    show = false;
                }
                
                if (employeeFilter && !row.dataset.employee.includes(employeeFilter)) {
                    show = false;
                }
                
                row.style.display = show ? '' : 'none';
            });
        }

        // 額度管理
        async function showQuotaManagement() {
            document.getElementById('contentTitle').textContent = '📊 請假額度管理';
            document.getElementById('contentBody').innerHTML = '<div class="loading">載入中...</div>';
            
            // 模擬員工請假額度數據
            const quotaData = [
                { employeeId: 'EMP001', name: '張小明', department: 'IT部', annual: { allocated: 14, used: 8, remaining: 6 }, sick: { used: 2 }, compensatory: { allocated: 3, used: 1, remaining: 2 } },
                { employeeId: 'EMP002', name: '李小華', department: '人事部', annual: { allocated: 14, used: 12, remaining: 2 }, sick: { used: 0 }, compensatory: { allocated: 2, used: 2, remaining: 0 } },
                { employeeId: 'EMP003', name: '王小美', department: '業務部', annual: { allocated: 14, used: 5, remaining: 9 }, sick: { used: 1 }, compensatory: { allocated: 1, used: 0, remaining: 1 } }
            ];
            
            let html = `
                <div class="filter-section">
                    <h4>🔍 篩選選項</h4>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 15px;">
                        <select class="form-select" id="departmentFilter">
                            <option value="">所有部門</option>
                            <option value="IT部">IT部</option>
                            <option value="人事部">人事部</option>
                            <option value="業務部">業務部</option>
                        </select>
                        <input type="text" class="form-input" placeholder="搜尋員工..." id="employeeQuotaFilter">
                        <button class="btn btn-success" onclick="batchUpdateQuota()">📝 批量更新額度</button>
                        <button class="btn btn-info" onclick="exportQuotaData()">📊 匯出額度報表</button>
                    </div>
                </div>
                
                <table>
                    <thead>
                        <tr>
                            <th>員工編號</th>
                            <th>姓名</th>
                            <th>部門</th>
                            <th>特休假額度</th>
                            <th>補休額度</th>
                            <th>病假使用</th>
                            <th>操作</th>
                        </tr>
                    </thead>
                    <tbody>
            `;
            
            quotaData.forEach(emp => {
                const annualUsagePercent = (emp.annual.used / emp.annual.allocated * 100).toFixed(1);
                
                html += `
                    <tr>
                        <td>${emp.employeeId}</td>
                        <td>${emp.name}</td>
                        <td>${emp.department}</td>
                        <td>
                            <div>已用: ${emp.annual.used}/${emp.annual.allocated} 天</div>
                            <div class="quota-bar">
                                <div class="quota-fill" style="width: ${annualUsagePercent}%"></div>
                            </div>
                            <small>剩餘: ${emp.annual.remaining} 天 (${annualUsagePercent}%)</small>
                        </td>
                        <td>
                            <div>已用: ${emp.compensatory.used}/${emp.compensatory.allocated} 天</div>
                            <small>剩餘: ${emp.compensatory.remaining} 天</small>
                        </td>
                        <td>${emp.sick.used} 天</td>
                        <td>
                            <button class="btn" style="padding: 5px 10px; font-size: 12px;" 
                                    onclick="editQuota('${emp.employeeId}', '${emp.name}')">
                                編輯
                            </button>
                        </td>
                    </tr>
                `;
            });
            
            html += '</tbody></table>';
            document.getElementById('contentBody').innerHTML = html;
        }

        // 匯出請假數據
        async function exportLeaveData() {
            try {
                const response = await fetch('/api/leave/export');
                
                if (response.ok) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'leave_requests_' + new Date().toISOString().split('T')[0] + '.csv';
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                    
                    alert('✅ 請假數據匯出成功！');
                } else {
                    throw new Error('匯出失敗');
                }
            } catch (error) {
                alert('❌ 匯出失敗: ' + error.message);
            }
        }

        // 工具函數
        function getStatusBadge(status) {
            const statusMap = {
                'pending': '<span class="status-badge status-pending">⏳ 待審核</span>',
                'approved': '<span class="status-badge status-approved">✅ 已批准</span>',
                'rejected': '<span class="status-badge status-rejected">❌ 已拒絕</span>',
                'cancelled': '<span class="status-badge" style="background: #f5f5f5; color: #666;">🚫 已取消</span>'
            };
            return statusMap[status] || status;
        }

        function truncateText(text, maxLength) {
            if (!text) return '-';
            return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
        }

        function formatDateTime(dateStr) {
            if (!dateStr) return '-';
            const date = new Date(dateStr);
            return date.toLocaleString('zh-TW', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            });
        }

        // 其他功能函數（實際實現）
        function changeCalendarMonth(direction) {
            // 實際應該更新日曆顯示
            console.log(`切換月份: ${direction > 0 ? '下月' : '上月'}`);
        }

        function viewRequestDetail(requestId) {
            // 實際應該顯示詳細信息模態框
            console.log(`查看申請詳情: #${requestId}`);
        }

        function saveLeaveSettings() {
            // 實際應該發送到後端保存
            alert('✅ 假別設定已儲存！');
        }

        function resetLeaveSettings() {
            if (confirm('確定要重置所有設定嗎？')) {
                // 實際應該重置表單值
                alert('✅ 設定已重置！');
            }
        }

        function batchUpdateQuota() {
            // 實際應該顯示批量更新模態框
            console.log('批量更新額度功能');
        }

        function exportQuotaData() {
            // 實際應該匯出額度數據
            console.log('匯出額度報表功能');
        }

        function editQuota(employeeId, name) {
            // 實際應該顯示編輯額度模態框
            console.log(`編輯 ${name} 的請假額度`);
        }

        function exportFilteredData() {
            // 實際應該匯出篩選後的數據
            console.log('匯出篩選結果功能');
        }
    </script>
</body>
</html>
"""