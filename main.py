# main.py - 主程式啟動檔 (修正版)
from flask import Flask, request, abort
import os
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, FollowEvent

# 導入自定義模組
from models import init_db
from message_processor import MessageProcessor
from admin_routes import setup_admin_routes

# 初始化 Flask 應用
app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# LINE Bot v2 設定
ACCESS_TOKEN = 'E7zP9wng9dQwxKXxGTnMFb7F57fmeLQC55Xmaap77EXfk/BMhu9fGz8VGLx3KjRgtZ4CIyKaiJ/2Ih/iispaeQKRwtRxci4L1uw67T/QUk3HOJaWSoOHh0q329PCOj0wAo1jGWRh40x7g7dTkGOW0gdB04t89/1O/w1cDnyilFU='
WEBHOOK_SECRET = 'b277fba0a28a0278861a69f8de4df0cd'

line_bot_api = LineBotApi(ACCESS_TOKEN)
handler = WebhookHandler(WEBHOOK_SECRET)

# 設定管理後台路由
setup_admin_routes(app)

# LINE Bot Webhook 路由
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    message_text = event.message.text
    
    response_text = MessageProcessor.process_command(user_id, message_text)
    line_bot_api.reply_message(event.reply_token, 
                              MessageProcessor.create_text_message(response_text))

@handler.add(FollowEvent)
def handle_follow(event):
    user_id = event.source.user_id
    welcome_message = MessageProcessor.get_welcome_message()
    line_bot_api.reply_message(event.reply_token, 
                              MessageProcessor.create_text_message(welcome_message))

# 測試路由
@app.route('/test')
def test():
    return "Flask 應用運行正常！"

if __name__ == "__main__":  # ✅ 修正：使用雙底線而非雙星號
    print("🚀 啟動企業級出勤管理系統...")
    print("🔒 權限系統：管理員 / 員工")
    print("🛡️ 安全特色：IP驗證 + 網路範圍控制")
    
    # 初始化資料庫
    init_db()
    print("✅ 企業資料庫初始化完成")
    
    # 自動更新網路設定
    try:
        from models import CompanySettings
        CompanySettings.update_setting('allowed_networks', '172.20.10.0/24,147.92.150.0/24', 'system')
        print("✅ 網路設定已自動更新")
    except Exception as e:
        print(f"⚠️ 網路設定更新失敗: {e}")
    
    print("\n📱 LINE Bot功能已就緒")
    print("🌐 管理後台已整合")
    print("🔒 網路安全控制已啟用")
    print("🔥 自助註冊功能已啟用")
    
    print("\n💡 主要功能：")
    print("  ✅ 上班打卡 / 下班打卡")
    print("  ✅ 今日狀態 / 查看記錄") 
    print("  ✅ 網路安全驗證")
    print("  ✅ 自助註冊流程")
    
    # 顯示已註冊的路由
    print("\n📋 已註冊的路由:")
    for rule in app.url_map.iter_rules():
        print(f"  {rule.endpoint}: {rule.rule}")
    
    # 啟動 Flask 應用
    port = int(os.environ.get('PORT', 5008))
    print(f"\n🌐 系統網址: http://localhost:{port}")
    print(f"🧪 測試網址: http://localhost:{port}/test")
    print(f"👨‍💼 管理後台: http://localhost:{port}/admin (admin/admin123)")
    print("🎉 完整出勤管理系統啟動完成！")
    
    app.run(host='0.0.0.0', port=port, debug=True)