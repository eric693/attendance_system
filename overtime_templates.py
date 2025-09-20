# overtime_templates.py - 加班管理模板模組

# 加班管理主頁面模板
OVERTIME_MANAGEMENT_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>加班管理系統 - 企業出勤管理</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f6fa;
            min-height: 100vh;
        }
        .header {
            background: linear-gradient(135deg, #FF9800 0%, #F57C00 100%);
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
            background: linear-gradient(135deg, #FF9800, #F57C00);
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
            min-height: 80px;
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
        .alert-info {
            background: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
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
        .overtime-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .stat-item {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            color: #FF9800;
        }
        .stat-label {
            font-size: 14px;
            color: #666;
            margin-top: 5px;
        }
        .hidden { display: none; }
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
        .time-display {
            font-family: 'Courier New', monospace;
            font-weight: bold;
            color: #FF9800;
        }
        .hours-calculation {
            background: #fff3e0;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
            border-left: 4px solid #FF9800;
        }
        .cost-estimate {
            background: #e8f5e8;
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
            border-left: 4px solid #4CAF50;
        }
        .filter-bar {
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
            flex-wrap: wrap;
            align-items: center;
        }
        .export-section {
            background: #f0f8ff;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            border-left: 4px solid #2196F3;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>⏰ 加班管理系統</h1>
        <p>員工加班申請與審核管理平台</p>
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
                <div class="stat-number" id="totalHours">-</div>
                <div>本月加班時數</div>
            </div>
            <div class="card stat-card" style="background: linear-gradient(135deg, #9C27B0, #7B1FA2);">
                <div class="stat-number" id="estimatedCost">-</div>
                <div>預估加班費</div>
            </div>
        </div>

        <!-- 功能導航 -->
        <div class="card">
            <h3>🛠️ 管理功能</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 20px;">
                <button class="btn" onclick="showPendingRequests()">⏳ 待審核申請</button>
                <button class="btn" onclick="showAllRequests()">📋 所有申請</button>
                <button class="btn" onclick="showOvertimeStatistics()">📈 統計分析</button>
                <button class="btn" onclick="showCostAnalysis()">💰 費用分析</button>
                <button class="btn" onclick="showBatchApproval()">⚡ 批量審核</button>
                <button class="btn" onclick="exportOvertimeData()">📤 匯出數據</button>
                <button class="btn" onclick="showOvertimeSettings()">⚙️ 加班設定</button>
                <button class="btn btn-warning" onclick="location.href='/admin'">🔙 返回管理台</button>
            </div>
        </div>

        <!-- 主要內容區域 -->
        <div id="mainContent" class="card">
            <h3 id="contentTitle">加班管理</h3>
            <div id="contentBody">
                <p style="text-align: center; color: #666; padding: 40px;">
                    請選擇上方功能開始管理加班申請
                </p>
            </div>
        </div>
    </div>

    <!-- 審核模態框 -->
    <div id="approvalModal" class="modal hidden">
        <div class="modal-content">
            <h3>加班申請審核</h3>
            <div id="modalContent"></div>
            <div style="text-align: center; margin-top: 20px;">
                <button class="btn btn-success" onclick="processApproval('approve')">✅ 批准</button>
                <button class="btn btn-danger" onclick="processApproval('reject')">❌ 拒絕</button>
                <button class="btn" onclick="closeModal()" style="background: #666;">取消</button>
            </div>
            <div id="approvalResult"></div>
        </div>
    </div>

    <!-- 批量審核模態框 -->
    <div id="batchModal" class="modal hidden">
        <div class="modal-content">
            <h3>批量審核</h3>
            <div id="batchContent"></div>
            <div style="text-align: center; margin-top: 20px;">
                <button class="btn btn-success" onclick="processBatchApproval('approve')">✅ 批量批准</button>
                <button class="btn btn-danger" onclick="processBatchApproval('reject')">❌ 批量拒絕</button>
                <button class="btn" onclick="closeModal()" style="background: #666;">取消</button>
            </div>
            <div id="batchResult"></div>
        </div>
    </div>

    <script>
        // 確保變數初始化
        let currentRequestId = null;
        let selectedRequests = [];

        // 關閉模態框函數
        function closeModal() {
            const modals = document.querySelectorAll('.modal');
            modals.forEach(modal => modal.classList.add('hidden'));
            currentRequestId = null;
        }

        // 頁面載入完成後執行
        document.addEventListener('DOMContentLoaded', function() {
            // 為所有關閉按鈕添加事件
            document.querySelectorAll('[onclick*="closeModal"]').forEach(btn => {
                btn.addEventListener('click', closeModal);
            });
        });

        // 頁面載入時初始化
        window.onload = function() {
            loadDashboardStats();
        };

        // 載入統計數據
        async function loadDashboardStats() {
            try {
                const response = await fetch('/api/overtime/stats');
                const stats = await response.json();
                
                if (stats.success) {
                    const data = stats.data;
                    document.getElementById('pendingCount').textContent = data.pending_count || 0;
                    
                    const monthlyStats = data.monthly_stats;
                    document.getElementById('approvedCount').textContent = 
                        (monthlyStats.approved?.count || 0);
                    document.getElementById('totalHours').textContent = 
                        (monthlyStats.approved?.hours || 0).toFixed(1) + 'h';
                    document.getElementById('estimatedCost').textContent = 
                        '$' + (data.estimated_monthly_cost || 0).toLocaleString();
                }
            } catch (error) {
                console.error('載入統計數據失敗:', error);
            }
        }

        // 顯示待審核申請
        async function showPendingRequests() {
            document.getElementById('contentTitle').textContent = '⏳ 待審核加班申請';
            document.getElementById('contentBody').innerHTML = '<p style="text-align: center; padding: 20px;">載入中...</p>';
            
            try {
                const response = await fetch('/api/overtime/requests?status=pending&limit=50');
                const result = await response.json();
                
                if (!result.success) {
                    throw new Error(result.message);
                }
                
                const requests = result.data;
                let html = '';
                
                if (requests.length === 0) {
                    html = '<div class="alert alert-success">🎉 目前沒有待審核的加班申請！</div>';
                } else {
                    html = `
                        <div style="margin-bottom: 20px;">
                            <div class="filter-bar">
                                <button class="btn btn-success" onclick="batchApprove('approve')">✅ 批量批准</button>
                                <button class="btn btn-danger" onclick="batchApprove('reject')">❌ 批量拒絕</button>
                                <span>已選擇 <span id="selectedCount">0</span> 個申請</span>
                            </div>
                        </div>
                        <table>
                            <thead>
                                <tr>
                                    <th><input type="checkbox" onchange="toggleAllCheckbox(this)"></th>
                                    <th>申請編號</th>
                                    <th>員工</th>
                                    <th>加班日期</th>
                                    <th>時間</th>
                                    <th>時數</th>
                                    <th>原因</th>
                                    <th>申請時間</th>
                                    <th>預估費用</th>
                                    <th>操作</th>
                                </tr>
                            </thead>
                            <tbody>
                    `;
                    
                    requests.forEach(req => {
                        const estimatedCost = (req.hours * 300).toLocaleString(); // 假設時薪300
                        html += `
                            <tr>
                                <td><input type="checkbox" class="request-checkbox" value="${req.id}" onchange="updateSelectedCount()"></td>
                                <td>#${req.id}</td>
                                <td>${req.employee_name}</td>
                                <td>${req.overtime_date}</td>
                                <td class="time-display">${req.start_time} - ${req.end_time}</td>
                                <td><span class="time-display">${req.hours}h</span></td>
                                <td title="${req.reason}">${truncateText(req.reason, 15)}</td>
                                <td>${formatDateTime(req.created_at)}</td>
                                <td>$${estimatedCost}</td>
                                <td>
                                    <button class="btn" style="padding: 5px 10px; font-size: 12px;" 
                                            onclick="showApprovalModal(${req.id}, '${req.employee_name}', '${req.overtime_date}', '${req.start_time}', '${req.end_time}', '${req.hours}', '${req.reason}')">
                                        審核
                                    </button>
                                </td>
                            </tr>
                        `;
                    });
                    
                    html += '</tbody></table>';
                }
                
                document.getElementById('contentBody').innerHTML = html;
            } catch (error) {
                document.getElementById('contentBody').innerHTML = '<div class="alert alert-error">❌ 載入失敗: ' + error.message + '</div>';
            }
        }

        // 顯示所有申請
        async function showAllRequests() {
            document.getElementById('contentTitle').textContent = '📋 所有加班申請';
            document.getElementById('contentBody').innerHTML = '<p style="text-align: center; padding: 20px;">載入中...</p>';
            
            try {
                const response = await fetch('/api/overtime/requests?status=all&limit=100');
                const result = await response.json();
                
                if (!result.success) {
                    throw new Error(result.message);
                }
                
                const requests = result.data;
                
                let html = `
                    <div class="filter-bar">
                        <select class="form-select" style="width: auto;" id="statusFilter" onchange="filterRequests()">
                            <option value="">所有狀態</option>
                            <option value="pending">待審核</option>
                            <option value="approved">已批准</option>
                            <option value="rejected">已拒絕</option>
                        </select>
                        <input type="date" class="form-input" style="width: auto;" id="dateFilter" onchange="filterRequests()" placeholder="篩選日期">
                        <input type="text" class="form-input" placeholder="搜尋員工姓名..." style="width: 200px;" id="nameFilter" onkeyup="filterRequests()">
                        <button class="btn btn-info" onclick="exportFilteredData()">📊 匯出篩選結果</button>
                    </div>
                    <table id="requestsTable">
                        <thead>
                            <tr>
                                <th>申請編號</th>
                                <th>員工</th>
                                <th>加班日期</th>
                                <th>時間</th>
                                <th>時數</th>
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
                    const statusBadge = getStatusBadge(req.status);
                    
                    html += `
                        <tr class="request-row" data-status="${req.status}" data-date="${req.overtime_date}" data-name="${req.employee_name.toLowerCase()}">
                            <td>#${req.id}</td>
                            <td>${req.employee_name}</td>
                            <td>${req.overtime_date}</td>
                            <td class="time-display">${req.start_time} - ${req.end_time}</td>
                            <td><span class="time-display">${req.hours}h</span></td>
                            <td>${statusBadge}</td>
                            <td title="${req.reason}">${truncateText(req.reason, 20)}</td>
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

        // 顯示統計分析
        async function showOvertimeStatistics() {
            document.getElementById('contentTitle').textContent = '📈 加班統計分析';
            
            let html = `
                <div class="overtime-stats">
                    <div class="stat-item">
                        <div class="stat-value" id="monthlyTotal">-</div>
                        <div class="stat-label">本月總時數</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value" id="avgPerPerson">-</div>
                        <div class="stat-label">人均加班時數</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value" id="peakDay">-</div>
                        <div class="stat-label">加班高峰日</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value" id="approvalRate">-</div>
                        <div class="stat-label">審核通過率</div>
                    </div>
                </div>

                <div class="card">
                    <h4>📊 部門加班統計</h4>
                    <div class="alert alert-info">
                        <h5>統計功能開發中</h5>
                        <p>將包含以下分析功能：</p>
                        <ul style="margin-top: 10px;">
                            <li>按部門統計加班時數和費用</li>
                            <li>按員工排名加班時數</li>
                            <li>加班趨勢分析（週期性模式）</li>
                            <li>加班原因分類統計</li>
                            <li>審核效率分析</li>
                        </ul>
                    </div>
                </div>

                <div class="card">
                    <h4>📈 月度趨勢</h4>
                    <div style="height: 300px; background: #f8f9fa; border-radius: 8px; display: flex; align-items: center; justify-content: center;">
                        <p style="color: #666;">圖表功能開發中 - 將顯示加班時數月度變化趨勢</p>
                    </div>
                </div>
            `;
            
            document.getElementById('contentBody').innerHTML = html;
        }

        // 顯示費用分析
        async function showCostAnalysis() {
            document.getElementById('contentTitle').textContent = '💰 加班費用分析';
            
            try {
                const response = await fetch('/api/overtime/stats');
                const stats = await response.json();
                
                let html = `
                    <div class="cost-estimate">
                        <h4>💰 本月加班費用預估</h4>
                        <div style="font-size: 2em; font-weight: bold; color: #4CAF50; text-align: center; margin: 20px 0;">
                            $${(stats.data?.estimated_monthly_cost || 0).toLocaleString()}
                        </div>
                        <p style="text-align: center; color: #666;">基於已批准的加班時數計算</p>
                    </div>

                    <div class="dashboard-grid">
                        <div class="card">
                            <h5>⏳ 待審核</h5>
                            <div style="font-size: 1.5em; color: #FF9800;">
                                ${stats.data?.monthly_stats?.pending?.count || 0} 申請
                            </div>
                            <div style="color: #666;">
                                ${stats.data?.monthly_stats?.pending?.hours || 0} 小時
                            </div>
                        </div>
                        <div class="card">
                            <h5>✅ 已批准</h5>
                            <div style="font-size: 1.5em; color: #4CAF50;">
                                ${stats.data?.monthly_stats?.approved?.count || 0} 申請
                            </div>
                            <div style="color: #666;">
                                ${stats.data?.monthly_stats?.approved?.hours || 0} 小時
                            </div>
                        </div>
                        <div class="card">
                            <h5>❌ 已拒絕</h5>
                            <div style="font-size: 1.5em; color: #f44336;">
                                ${stats.data?.monthly_stats?.rejected?.count || 0} 申請
                            </div>
                            <div style="color: #666;">
                                ${stats.data?.monthly_stats?.rejected?.hours || 0} 小時
                            </div>
                        </div>
                    </div>

                    <div class="card">
                        <h4>📋 費用明細設定</h4>
                        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
                            <div class="form-row">
                                <div>
                                    <label>標準時薪：</label>
                                    <input type="number" class="form-input" value="200" id="standardRate">
                                </div>
                                <div>
                                    <label>加班時薪：</label>
                                    <input type="number" class="form-input" value="300" id="overtimeRate">
                                </div>
                            </div>
                            <button class="btn" onclick="updateRates()">💾 更新費率設定</button>
                        </div>
                    </div>
                `;
                
                document.getElementById('contentBody').innerHTML = html;
            } catch (error) {
                document.getElementById('contentBody').innerHTML = '<div class="alert alert-error">❌ 載入失敗: ' + error.message + '</div>';
            }
        }

        // 顯示批量審核
        function showBatchApproval() {
            document.getElementById('contentTitle').textContent = '⚡ 批量審核';
            
            let html = `
                <div class="alert alert-info">
                    <h4>批量審核功能</h4>
                    <p>可以一次性審核多個加班申請，提高審核效率</p>
                </div>

                <div class="card">
                    <h4>快速批量操作</h4>
                    <div style="margin: 20px 0;">
                        <button class="btn btn-info" onclick="loadPendingForBatch()">載入待審核申請</button>
                        <button class="btn btn-warning" onclick="selectByDate()">按日期選擇</button>
                        <button class="btn" onclick="selectByDepartment()">按部門選擇</button>
                    </div>
                </div>

                <div id="batchPreview" class="card" style="display: none;">
                    <h4>預覽選中的申請</h4>
                    <div id="batchList"></div>
                    <div style="margin-top: 20px;">
                        <button class="btn btn-success" onclick="processBatchApproval('approve')">✅ 批量批准</button>
                        <button class="btn btn-danger" onclick="processBatchApproval('reject')">❌ 批量拒絕</button>
                    </div>
                </div>
            `;
            
            document.getElementById('contentBody').innerHTML = html;
        }

        // 匯出加班數據
        async function exportOvertimeData() {
            try {
                const response = await fetch('/api/overtime/export/csv');
                
                if (response.ok) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `overtime_records_${new Date().toISOString().split('T')[0]}.csv`;
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                    
                    showAlert('success', '✅ 加班數據匯出成功！');
                } else {
                    throw new Error('匯出失敗');
                }
            } catch (error) {
                showAlert('error', '❌ 匯出失敗: ' + error.message);
            }
        }

        // 顯示加班設定
        function showOvertimeSettings() {
            document.getElementById('contentTitle').textContent = '⚙️ 加班設定';
            
            let html = `
                <div class="card">
                    <h4>⏰ 加班時間設定</h4>
                    <div class="form-row">
                        <div>
                            <label>最早加班開始時間：</label>
                            <input type="time" class="form-input" value="17:00" id="earliestStart">
                        </div>
                        <div>
                            <label>最晚加班結束時間：</label>
                            <input type="time" class="form-input" value="23:00" id="latestEnd">
                        </div>
                    </div>
                    <div class="form-row">
                        <div>
                            <label>單日最大加班時數：</label>
                            <input type="number" class="form-input" value="4" min="1" max="8" id="maxDailyHours">
                        </div>
                        <div>
                            <label>月度最大加班時數：</label>
                            <input type="number" class="form-input" value="46" min="1" max="100" id="maxMonthlyHours">
                        </div>
                    </div>
                    <div class="form-row">
                        <div>
                            <label>需要提前申請時間（小時）：</label>
                            <input type="number" class="form-input" value="24" min="0" id="advanceNoticeHours">
                        </div>
                        <div>
                            <label>自動審核閾值（小時）：</label>
                            <input type="number" class="form-input" value="2" min="0" max="8" id="autoApprovalThreshold">
                        </div>
                    </div>
                    <button class="btn" onclick="saveOvertimeSettings()">💾 儲存時間設定</button>
                </div>

                <div class="card">
                    <h4>💰 費用設定</h4>
                    <div class="form-row">
                        <div>
                            <label>平日加班費率（倍數）：</label>
                            <input type="number" class="form-input" value="1.33" step="0.01" min="1" id="weekdayRate">
                        </div>
                        <div>
                            <label>假日加班費率（倍數）：</label>
                            <input type="number" class="form-input" value="2.0" step="0.01" min="1" id="holidayRate">
                        </div>
                    </div>
                    <div class="form-row">
                        <div>
                            <label>夜間加班費率（倍數）：</label>
                            <input type="number" class="form-input" value="1.67" step="0.01" min="1" id="nightRate">
                        </div>
                        <div>
                            <label>夜間時段開始時間：</label>
                            <input type="time" class="form-input" value="22:00" id="nightStartTime">
                        </div>
                    </div>
                    <button class="btn" onclick="saveRateSettings()">💾 儲存費率設定</button>
                </div>

                <div class="card">
                    <h4>🔧 審核設定</h4>
                    <div class="form-row">
                        <div>
                            <label>預設審核者：</label>
                            <select class="form-select" id="defaultApprover">
                                <option value="">請選擇...</option>
                                <option value="admin">系統管理員</option>
                                <option value="hr">人資部門</option>
                                <option value="manager">直屬主管</option>
                            </select>
                        </div>
                        <div>
                            <label>審核提醒間隔（小時）：</label>
                            <input type="number" class="form-input" value="24" min="1" id="reminderInterval">
                        </div>
                    </div>
                    <div style="margin: 15px 0;">
                        <label>
                            <input type="checkbox" id="autoApprovalEnabled" style="margin-right: 8px;">
                            啟用自動審核（低於閾值的申請）
                        </label>
                    </div>
                    <div style="margin: 15px 0;">
                        <label>
                            <input type="checkbox" id="emailNotificationEnabled" checked style="margin-right: 8px;">
                            啟用郵件通知
                        </label>
                    </div>
                    <button class="btn" onclick="saveApprovalSettings()">💾 儲存審核設定</button>
                </div>

                <div class="export-section">
                    <h4>📤 系統維護</h4>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                        <button class="btn btn-info" onclick="backupOvertimeData()">🗄️ 備份數據</button>
                        <button class="btn btn-warning" onclick="clearOldRecords()">🧹 清理舊記錄</button>
                        <button class="btn" onclick="resetSettings()">🔄 重置設定</button>
                        <button class="btn btn-success" onclick="exportSettings()">📋 匯出設定</button>
                    </div>
                </div>
            `;
            
            document.getElementById('contentBody').innerHTML = html;
        }

        // 顯示審核模態框
        function showApprovalModal(id, employeeName, overtimeDate, startTime, endTime, hours, reason) {
            currentRequestId = id;
            
            const modalContent = `
                <div class="hours-calculation">
                    <h4>申請詳情</h4>
                    <p><strong>員工：</strong> ${employeeName}</p>
                    <p><strong>加班日期：</strong> ${overtimeDate}</p>
                    <p><strong>時間：</strong> <span class="time-display">${startTime} - ${endTime}</span></p>
                    <p><strong>時數：</strong> <span class="time-display">${hours} 小時</span></p>
                    <p><strong>原因：</strong> ${reason}</p>
                </div>
                
                <div class="cost-estimate">
                    <h4>費用預估</h4>
                    <p><strong>基本時薪：</strong> $300</p>
                    <p><strong>加班費率：</strong> 1.33x</p>
                    <p><strong>預估費用：</strong> ${(hours * 300 * 1.33).toFixed(0)}</p>
                </div>
                
                <div style="margin: 20px 0;">
                    <label>審核意見：</label>
                    <textarea class="form-textarea" id="approvalComment" placeholder="請輸入審核意見（選填）"></textarea>
                </div>
            `;
            
            document.getElementById('modalContent').innerHTML = modalContent;
            document.getElementById('approvalModal').classList.remove('hidden');
        }

        // 處理審核
        async function processApproval(action) {
            if (!currentRequestId) return;
            
            const comment = document.getElementById('approvalComment').value;
            
            try {
                const response = await fetch(`/api/overtime/approve/${currentRequestId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        action: action,
                        comment: comment
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    document.getElementById('approvalResult').innerHTML = 
                        `<div class="alert alert-success">✅ ${action === 'approve' ? '批准' : '拒絕'}成功！</div>`;
                    
                    setTimeout(() => {
                        closeModal();
                        showPendingRequests(); // 重新載入待審核列表
                        loadDashboardStats(); // 更新統計
                    }, 1500);
                } else {
                    throw new Error(result.message);
                }
            } catch (error) {
                document.getElementById('approvalResult').innerHTML = 
                    `<div class="alert alert-error">❌ 操作失敗: ${error.message}</div>`;
            }
        }

        // 關閉模態框
        function closeModal() {
            document.getElementById('approvalModal').classList.add('hidden');
            document.getElementById('batchModal').classList.add('hidden');
            currentRequestId = null;
        }

        // 批量審核相關函數
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

        function batchApprove(action) {
            if (selectedRequests.length === 0) {
                showAlert('warning', '請先選擇要審核的申請！');
                return;
            }
            
            const actionText = action === 'approve' ? '批准' : '拒絕';
            if (confirm(`確定要${actionText} ${selectedRequests.length} 個加班申請嗎？`)) {
                processBatchApproval(action);
            }
        }

        async function processBatchApproval(action) {
            if (selectedRequests.length === 0) return;
            
            try {
                const response = await fetch('/api/overtime/batch-approve', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        request_ids: selectedRequests,
                        action: action,
                        comment: '批量審核'
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showAlert('success', `✅ 批量${action === 'approve' ? '批准' : '拒絕'}成功！`);
                    showPendingRequests();
                    loadDashboardStats();
                } else {
                    throw new Error(result.message);
                }
            } catch (error) {
                showAlert('error', '❌ 批量操作失敗: ' + error.message);
            }
        }

        // 篩選相關函數
        function filterRequests() {
            const statusFilter = document.getElementById('statusFilter').value;
            const dateFilter = document.getElementById('dateFilter').value;
            const nameFilter = document.getElementById('nameFilter').value.toLowerCase();
            
            const rows = document.querySelectorAll('.request-row');
            rows.forEach(row => {
                let show = true;
                
                if (statusFilter && row.dataset.status !== statusFilter) {
                    show = false;
                }
                
                if (dateFilter && row.dataset.date !== dateFilter) {
                    show = false;
                }
                
                if (nameFilter && !row.dataset.name.includes(nameFilter)) {
                    show = false;
                }
                
                row.style.display = show ? '' : 'none';
            });
        }

        // 設定相關函數
        async function saveOvertimeSettings() {
            const settings = {
                earliest_start: document.getElementById('earliestStart').value,
                latest_end: document.getElementById('latestEnd').value,
                max_daily_hours: document.getElementById('maxDailyHours').value,
                max_monthly_hours: document.getElementById('maxMonthlyHours').value,
                advance_notice_hours: document.getElementById('advanceNoticeHours').value,
                auto_approval_threshold: document.getElementById('autoApprovalThreshold').value
            };
            
            try {
                const response = await fetch('/api/overtime/settings/time', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(settings)
                });
                
                const result = await response.json();
                if (result.success) {
                    showAlert('success', '✅ 時間設定已儲存！');
                } else {
                    throw new Error(result.message);
                }
            } catch (error) {
                showAlert('error', '❌ 儲存失敗: ' + error.message);
            }
        }

        async function saveRateSettings() {
            const rates = {
                weekday_rate: document.getElementById('weekdayRate').value,
                holiday_rate: document.getElementById('holidayRate').value,
                night_rate: document.getElementById('nightRate').value,
                night_start_time: document.getElementById('nightStartTime').value
            };
            
            try {
                const response = await fetch('/api/overtime/settings/rates', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(rates)
                });
                
                const result = await response.json();
                if (result.success) {
                    showAlert('success', '✅ 費率設定已儲存！');
                } else {
                    throw new Error(result.message);
                }
            } catch (error) {
                showAlert('error', '❌ 儲存失敗: ' + error.message);
            }
        }

        async function saveApprovalSettings() {
            const settings = {
                default_approver: document.getElementById('defaultApprover').value,
                reminder_interval: document.getElementById('reminderInterval').value,
                auto_approval_enabled: document.getElementById('autoApprovalEnabled').checked,
                email_notification_enabled: document.getElementById('emailNotificationEnabled').checked
            };
            
            try {
                const response = await fetch('/api/overtime/settings/approval', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(settings)
                });
                
                const result = await response.json();
                if (result.success) {
                    showAlert('success', '✅ 審核設定已儲存！');
                } else {
                    throw new Error(result.message);
                }
            } catch (error) {
                showAlert('error', '❌ 儲存失敗: ' + error.message);
            }
        }

        // 系統維護函數
        async function backupOvertimeData() {
            try {
                const response = await fetch('/api/overtime/backup');
                if (response.ok) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `overtime_backup_${new Date().toISOString().split('T')[0]}.sql`;
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                    
                    showAlert('success', '✅ 數據備份成功！');
                } else {
                    throw new Error('備份失敗');
                }
            } catch (error) {
                showAlert('error', '❌ 備份失敗: ' + error.message);
            }
        }

        async function clearOldRecords() {
            if (!confirm('確定要清理6個月前的舊記錄嗎？此操作無法復原！')) return;
            
            try {
                const response = await fetch('/api/overtime/cleanup', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ months: 6 })
                });
                
                const result = await response.json();
                if (result.success) {
                    showAlert('success', `✅ 已清理 ${result.deleted_count} 筆舊記錄！`);
                } else {
                    throw new Error(result.message);
                }
            } catch (error) {
                showAlert('error', '❌ 清理失敗: ' + error.message);
            }
        }

        function resetSettings() {
            if (!confirm('確定要重置所有設定為預設值嗎？')) return;
            
            // 重置時間設定
            document.getElementById('earliestStart').value = '17:00';
            document.getElementById('latestEnd').value = '23:00';
            document.getElementById('maxDailyHours').value = '4';
            document.getElementById('maxMonthlyHours').value = '46';
            document.getElementById('advanceNoticeHours').value = '24';
            document.getElementById('autoApprovalThreshold').value = '2';
            
            // 重置費率設定
            document.getElementById('weekdayRate').value = '1.33';
            document.getElementById('holidayRate').value = '2.0';
            document.getElementById('nightRate').value = '1.67';
            document.getElementById('nightStartTime').value = '22:00';
            
            // 重置審核設定
            document.getElementById('defaultApprover').value = '';
            document.getElementById('reminderInterval').value = '24';
            document.getElementById('autoApprovalEnabled').checked = false;
            document.getElementById('emailNotificationEnabled').checked = true;
            
            showAlert('success', '✅ 設定已重置為預設值！');
        }

        async function exportSettings() {
            try {
                const settings = {
                    time_settings: {
                        earliest_start: document.getElementById('earliestStart').value,
                        latest_end: document.getElementById('latestEnd').value,
                        max_daily_hours: document.getElementById('maxDailyHours').value,
                        max_monthly_hours: document.getElementById('maxMonthlyHours').value,
                        advance_notice_hours: document.getElementById('advanceNoticeHours').value,
                        auto_approval_threshold: document.getElementById('autoApprovalThreshold').value
                    },
                    rate_settings: {
                        weekday_rate: document.getElementById('weekdayRate').value,
                        holiday_rate: document.getElementById('holidayRate').value,
                        night_rate: document.getElementById('nightRate').value,
                        night_start_time: document.getElementById('nightStartTime').value
                    },
                    approval_settings: {
                        default_approver: document.getElementById('defaultApprover').value,
                        reminder_interval: document.getElementById('reminderInterval').value,
                        auto_approval_enabled: document.getElementById('autoApprovalEnabled').checked,
                        email_notification_enabled: document.getElementById('emailNotificationEnabled').checked
                    }
                };
                
                const blob = new Blob([JSON.stringify(settings, null, 2)], { type: 'application/json' });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `overtime_settings_${new Date().toISOString().split('T')[0]}.json`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                
                showAlert('success', '✅ 設定匯出成功！');
            } catch (error) {
                showAlert('error', '❌ 匯出失敗: ' + error.message);
            }
        }

        // 工具函數
        function getStatusBadge(status) {
            const statusMap = {
                'pending': '<span class="status-badge status-pending">待審核</span>',
                'approved': '<span class="status-badge status-approved">已批准</span>',
                'rejected': '<span class="status-badge status-rejected">已拒絕</span>'
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

        function showAlert(type, message) {
            const alertDiv = document.createElement('div');
            alertDiv.className = `alert alert-${type}`;
            alertDiv.innerHTML = message;
            alertDiv.style.position = 'fixed';
            alertDiv.style.top = '20px';
            alertDiv.style.right = '20px';
            alertDiv.style.zIndex = '9999';
            alertDiv.style.maxWidth = '300px';
            
            document.body.appendChild(alertDiv);
            
            setTimeout(() => {
                alertDiv.remove();
            }, 3000);
        }

        function viewRequestDetail(requestId) {
            // 查看申請詳情的邏輯
            window.location.href = `/overtime/request/${requestId}`;
        }

        function exportFilteredData() {
            // 匯出篩選結果的邏輯
            showAlert('info', '📊 匯出功能開發中...');
        }

        function loadPendingForBatch() {
            // 載入待審核申請到批量審核的邏輯
            showAlert('info', '🔄 載入中...');
        }

        function selectByDate() {
            // 按日期選擇的邏輯
            showAlert('info', '📅 按日期選擇功能開發中...');
        }

        function selectByDepartment() {
            // 按部門選擇的邏輯
            showAlert('info', '🏢 按部門選擇功能開發中...');
        }

        function updateRates() {
            // 更新費率的邏輯
            const standardRate = document.getElementById('standardRate').value;
            const overtimeRate = document.getElementById('overtimeRate').value;
            
            showAlert('success', `✅ 費率已更新：標準 ${standardRate}/時，加班 ${overtimeRate}/時`);
        }
    </script>
</body>
</html>
'''