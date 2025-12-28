# -*- coding: utf-8 -*-
"""
Created on Sun Dec 28 17:12:05 2025

@author: sasha
"""

from tavily import TavilyClient
import random
import os

import os
from tavily import TavilyClient
import random

# 從 Secrets 讀取 API Key
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")

def scrape_web(keyword):
    print(f"🚀 [Tavily API] 正在搜尋：{keyword} ...")
    

    tavily = TavilyClient(api_key=TAVILY_API_KEY)
    
    try:
        # 執行搜尋
        response = tavily.search(
            query=f"{keyword} 評價 推薦", 
            search_depth="basic", 
            include_images=True,
            max_results=5
        )
        
        results = []
        text_results = response.get('results', [])
        image_results = response.get('images', [])
        
        for i, item in enumerate(text_results):
            title = item['title']
            link = item['url']
            content = item['content']
            
            # 配對圖片
            if i < len(image_results):
                img = image_results[i]
            else:
                img = "https://images.unsplash.com/photo-1504674900247-0877df9cc836"

            results.append({
                "name": title,
                "score": "推薦",
                "image": img,
                "address": content[:60] + "...",
                "link": link
            })
            
        if len(results) > 0:
            return results

    except Exception as e:
        print(f"❌ Tavily API 錯誤: {e}")

    # 安全網 (備用資料)
    return [{
        "name": f"Google Maps: {keyword}",
        "score": "G",
        "image": "https://images.unsplash.com/photo-1559339352-11d035aa65de",
        "address": "點擊開啟地圖查看更多結果",
        "link": f"http://googleusercontent.com/maps.google.com/search?q={keyword}"
    }]
