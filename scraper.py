# -*- coding: utf-8 -*-
"""
Created on Sun Dec 28 17:08:57 2025

@author: sasha
"""

import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, FlexSendMessage
from scraper import scrape_web # 引入新的搜尋功能

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.environ.get('CHANNEL_SECRET')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

def create_carousel(spots):
    bubbles = []
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

@app.route("/")
def home(): return "搜尋引擎 Bot 運作中"

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
    
    # 直接去搜尋
    spots = scrape_web(user_msg)
    
    flex = create_carousel(spots)
    line_bot_api.reply_message(
        event.reply_token,
        FlexSendMessage(alt_text=f"{user_msg} 搜尋結果", contents=flex)
    )

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
