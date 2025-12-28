# -*- coding: utf-8 -*-
"""
Created on Sun Dec 28 17:12:05 2025

@author: sasha
"""

import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, FlexSendMessage

# 引入兩個爬蟲功能
from scraper import scrape_ifoodie, scrape_travelking

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.environ.get('CHANNEL_SECRET')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ==========================================
# 製作漂亮卡片 (Flex Message)
# ==========================================
def create_carousel(spots):
    bubbles = []
    for spot in spots[:5]:
        bubble = {
            "type": "bubble",
            "hero": { "type": "image", "url": spot["image"], "size": "full", "aspectRatio": "20:13", "aspectMode": "cover" },
            "body": {
                "type": "box", "layout": "vertical", "contents": [
                    { "type": "text", "text": spot["name"], "weight": "bold", "size": "xl", "wrap": True },
                    { "type": "box", "layout": "baseline", "margin": "md", "contents": [
                        { "type": "text", "text": f"⭐ {spot['score']}", "size": "sm", "color": "#999999", "flex": 0 },
                        { "type": "text", "text": f"  |  {spot['address']}", "size": "sm", "color": "#aaaaaa", "flex": 1, "wrap": True }
                    ] }
                ]
            },
            "footer": {
                "type": "box", "layout": "vertical", "contents": [
                    { "type": "button", "action": { "type": "uri", "label": "📍 查看詳情", "uri": spot["link"] }, "style": "primary", "color": "#1DB446" }
                ]
            }
        }
        bubbles.append(bubble)
    return { "type": "carousel", "contents": bubbles }

# ==========================================
# 伺服器監聽區
# ==========================================
@app.route("/")
def home():
    return "LINE Bot 雙模式爬蟲運作中！"

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
    user_msg = event.message.text.strip()
    
    # === 智慧判斷邏輯 ===
    # 預設行為
    mode = "food" 
    location = user_msg
    keyword = "美食"

    # 1. 檢查是否有指定關鍵字 (例如：台中 景點)
    if " " in user_msg:
        parts = user_msg.split(" ")
        location = parts[0]
        keyword = parts[1]
    
    # 2. 判斷是要「吃」還是要「玩」
    # 如果關鍵字包含這些字，就切換成景點模式
    play_keywords = ["景點", "玩", "旅遊", "爬山", "逛街", "一日遊", "好玩"]
    
    if any(k in keyword for k in play_keywords) or any(k in user_msg for k in play_keywords):
        mode = "play"
    
    # === 執行爬蟲 ===
    spots_data = []
    
    if mode == "food":
        # 呼叫愛食記
        spots_data = scrape_ifoodie(location, keyword)
        alt_text = f"找到 {location} 的美食情報！"
    else:
        # 呼叫旅遊王 (搜尋時直接把地點+關鍵字丟進去查，例如 "台中 景點")
        search_query = f"{location} {keyword}"
        spots_data = scrape_travelking(search_query)
        alt_text = f"找到 {location} 的好玩景點！"

    # 如果爬回來是空的 (兩個爬蟲都失敗)，使用備援資料
    if not spots_data:
         spots_data = scrape_travelking("台灣旅遊") # 隨便抓個東西墊檔

    # === 回覆 ===
    flex_payload = create_carousel(spots_data)
    line_bot_api.reply_message(
        event.reply_token,
        FlexSendMessage(alt_text=alt_text, contents=flex_payload)
    )

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)