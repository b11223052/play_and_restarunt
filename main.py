# -*- coding: utf-8 -*-
"""
Created on Sun Dec 28 17:12:05 2025

@author: sasha
"""

import os
import random
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, FlexSendMessage

from scraper import scrape_web

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.environ.get('CHANNEL_SECRET')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ==========================================
# 1. 一般模式：多張卡片 (Carousel)
# ==========================================
def create_carousel(spots):
    bubbles = []
    # 只取前 5 個給使用者選
    for spot in spots[:5]:
        bubble = {
            "type": "bubble",
            "hero": { "type": "image", "url": spot["image"], "size": "full", "aspectRatio": "20:13", "aspectMode": "cover" },
            "body": {
                "type": "box", "layout": "vertical", "contents": [
                    { "type": "text", "text": spot["name"], "weight": "bold", "size": "xl", "wrap": True },
                    { "type": "text", "text": spot["address"], "size": "sm", "color": "#aaaaaa", "wrap": True }
                ]
            },
            "footer": {
                "type": "box", "layout": "vertical", "contents": [
                    { "type": "button", "action": { "type": "uri", "label": "🔗 點我查看", "uri": spot["link"] }, "style": "primary", "color": "#1DB446" }
                ]
            }
        }
        bubbles.append(bubble)
    return { "type": "carousel", "contents": bubbles }

# ==========================================
# 2. 抽籤模式：單張大卡片 (Bubble)
# ==========================================
def create_lucky_card(spot):
    return {
        "type": "bubble",
        "size": "giga", # 做大張一點
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                { "type": "text", "text": "🎉 命運的選擇是...", "color": "#ffffff", "weight": "bold", "size": "lg" }
            ],
            "backgroundColor": "#ff5555" # 紅色喜氣
        },
        "hero": { "type": "image", "url": spot["image"], "size": "full", "aspectRatio": "20:13", "aspectMode": "cover" },
        "body": {
            "type": "box", "layout": "vertical", "contents": [
                { "type": "text", "text": spot["name"], "weight": "bold", "size": "xxl", "wrap": True, "color": "#333333" },
                { "type": "separator", "margin": "md" },
                { "type": "text", "text": "這就是你今天的落腳處！", "weight": "bold", "size": "md", "margin": "md", "color": "#ff5555" },
                { "type": "text", "text": spot["address"], "size": "sm", "color": "#aaaaaa", "wrap": True, "margin": "sm" }
            ]
        },
        "footer": {
            "type": "box", "layout": "vertical", "contents": [
                { "type": "button", "action": { "type": "uri", "label": "🚀 馬上出發", "uri": spot["link"] }, "style": "primary", "color": "#ff5555" }
            ]
        }
    }

# ==========================================
# 伺服器與訊息處理
# ==========================================
@app.route("/")
def home(): return "隨機抽籤 Bot 運作中"

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try: handler.handle(body, signature)
    except InvalidSignatureError: abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_msg = event.message.text.strip()
    print(f"收到指令：{user_msg}")
    
    # 判斷是不是要「抽」
    is_lucky_draw = False
    search_keyword = user_msg

    if "抽" in user_msg or "隨機" in user_msg:
        is_lucky_draw = True
        # 把「抽」跟「隨機」這些字去掉，剩下的才是要搜尋的地點
        # 例如：「抽 台北 景點」變成 「台北 景點」
        search_keyword = user_msg.replace("抽", "").replace("隨機", "").strip()

    # 1. 先去搜尋 (抓一堆回來)
    spots_data = scrape_web(search_keyword)
    
    # 2. 決定回傳什麼
    if not spots_data:
        line_bot_api.reply_message(event.reply_token, TextMessage(text="找不到相關地點，請換個關鍵字試試！"))
        return

    if is_lucky_draw:
        # === 抽籤模式 ===
        # 從搜尋結果中隨機挑選 1 個
        lucky_spot = random.choice(spots_data)
        
        # 製作單張大卡片
        flex_payload = create_lucky_card(lucky_spot)
        alt_text = f"恭喜！抽中了：{lucky_spot['name']}"
    
    else:
        # === 一般模式 ===
        # 製作多張卡片
        flex_payload = create_carousel(spots_data)
        alt_text = f"{search_keyword} 的搜尋結果"

    # 3. 發送
    line_bot_api.reply_message(
        event.reply_token,
        FlexSendMessage(alt_text=alt_text, contents=flex_payload)
    )

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
