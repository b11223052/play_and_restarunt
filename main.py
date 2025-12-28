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

# 引入爬蟲
from scraper import scrape_web

app = Flask(__name__)

# 從 Secrets 讀取 Token
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.environ.get('CHANNEL_SECRET')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 介面 1：一般模式 (Carousel)
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
                        { "type": "text", "text": "⭐ " + str(spot['score']), "size": "sm", "color": "#999999", "flex": 0 },
                        { "type": "text", "text": "  |  " + spot['address'], "size": "sm", "color": "#aaaaaa", "flex": 1, "wrap": True }
                    ] }
                ]
            },
            "footer": {
                "type": "box", "layout": "vertical", "contents": [
                    { "type": "button", "action": { "type": "uri", "label": "🔗 查看詳情", "uri": spot["link"] }, "style": "primary", "color": "#1DB446" }
                ]
            }
        }
        bubbles.append(bubble)
    return { "type": "carousel", "contents": bubbles }

# 介面 2：抽籤模式 (Lucky Card)
def create_lucky_card(spot):
    return {
        "type": "bubble",
        "size": "giga",
        "header": {
            "type": "box", "layout": "vertical",
            "contents": [
                { "type": "text", "text": "🎉 命運的選擇是...", "color": "#ffffff", "weight": "bold", "size": "lg" }
            ],
            "backgroundColor": "#ff5555"
        },
        "hero": { "type": "image", "url": spot["image"], "size": "full", "aspectRatio": "20:13", "aspectMode": "cover" },
        "body": {
            "type": "box", "layout": "vertical", "contents": [
                { "type": "text", "text": spot["name"], "weight": "bold", "size": "xxl", "wrap": True, "color": "#333333" },
                { "type": "separator", "margin": "md" },
                { "type": "text", "text": "就是這裡了！馬上出發！", "weight": "bold", "size": "md", "margin": "md", "color": "#ff5555" },
                { "type": "text", "text": spot["address"], "size": "sm", "color": "#aaaaaa", "wrap": True, "margin": "sm" }
            ]
        },
        "footer": {
            "type": "box", "layout": "vertical", "contents": [
                { "type": "button", "action": { "type": "uri", "label": "🚀 開啟連結", "uri": spot["link"] }, "style": "primary", "color": "#ff5555" }
            ]
        }
    }

@app.route("/")
def home():
    return "LINE Bot is Running on Replit!"

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
    
    # 判斷抽籤
    is_lucky_draw = False
    search_keyword = user_msg

    if "抽" in user_msg or "隨機" in user_msg:
        is_lucky_draw = True
        search_keyword = user_msg.replace("抽", "").replace("隨機", "").strip()

    # 呼叫爬蟲
    spots_data = scrape_web(search_keyword)
    
    if not spots_data:
        line_bot_api.reply_message(event.reply_token, TextMessage(text="抱歉，找不到相關資料，請換個關鍵字試試！"))
        return

    # 決定回傳格式
    if is_lucky_draw:
        lucky_spot = random.choice(spots_data)
        flex_payload = create_lucky_card(lucky_spot)
        alt_text = f"恭喜！抽中了：{lucky_spot['name']}"
    else:
        flex_payload = create_carousel(spots_data)
        alt_text = f"{search_keyword} 的搜尋結果"

    line_bot_api.reply_message(
        event.reply_token,
        FlexSendMessage(alt_text=alt_text, contents=flex_payload)
    )

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
