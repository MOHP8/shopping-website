# socket_io.py

from flask import Blueprint, render_template ,current_app
from flask_socketio import SocketIO, emit
import google.generativeai as genai
import time

socket_io_bp = Blueprint('socket_io', __name__)
socketio = SocketIO()

# 定義是否處於真人模式的標誌
human_mode = False

@socketio.on('message')
def handle_message(msg):
    print('Received message:', msg)
    
    # 如果處於機器人模式，根據客戶輸入回覆機器人的內容
    bot_response = get_bot_response(msg)
    emit('message', {'message': str(bot_response), 'sender': 'backend'}, broadcast=False)

def get_bot_response(user_input):
    max_retries = 3  # 定義最大重試次數
    retries = 0

    while retries < max_retries:
        try:
            # 目前是使用 google AI API 進行串接(generative-ai-studio)
            # 這裡可以根據實際情況擴展成一個真實的機器人回覆邏輯
            genai.configure(api_key=current_app.config['GOOGLE_AI_API_KEY'])
            model = genai.GenerativeModel(model_name="gemini-pro")
            response = model.generate_content(user_input)
            print(response)

            # 新增處理邏輯，取得文本內容
            try:
                # 嘗試解析 JSON 格式的回應
                text = response.get("text")
                if text:
                    return text
            except AttributeError:
                pass

            try:
                # 嘗試直接取得文本
                text = response.text
                if text:
                    return text
            except AttributeError:
                pass

            # 如果無法從上述方式取得文本，返回一個錯誤提示
            return "無法解析回應中的文本內容"

        except Exception as e:
            print(f"發生錯誤: {e}")
            retries += 1
            time.sleep(2)  # 等待一段時間再進行重試

    # 如果重試次數達到上限，返回一個錯誤提示
    return "API 異常，請稍後再試。"
