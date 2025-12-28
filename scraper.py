# -*- coding: utf-8 -*-
"""
Created on Sun Dec 28 17:08:57 2025

@author: sasha
"""

import requests
from bs4 import BeautifulSoup
import random

# ==========================================
# 1. 爬美食 (愛食記 iFoodie)
# ==========================================
def scrape_ifoodie(location, keyword):
    print(f"🕷️ [美食模式] 正在爬取：{location} 的 {keyword} ...")
    url = f"https://ifoodie.tw/explore/{location}/list/{keyword}"
    headers = { "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36" }

    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            items = soup.find_all("div", class_="restaurant-item", limit=5)
            results = []
            for item in items:
                try:
                    title = item.find("a", class_="title-text").text.strip()
                    img_tag = item.find("img", class_="lazy-load")
                    image = img_tag["data-src"] if img_tag and "data-src" in img_tag.attrs else "https://images.unsplash.com/photo-1504674900247-0877df9cc836"
                    rating = item.find("div", class_="text").text.strip() if item.find("div", class_="text") else "4.0"
                    address = item.find("div", class_="address-row").text.strip() if item.find("div", class_="address-row") else "地址詳見連結"
                    link = "https://ifoodie.tw" + item.find("a", class_="title-text")["href"]
                    
                    results.append({ "name": title, "score": rating, "image": image, "address": address, "link": link })
                except: continue
            
            if results: return results
    except Exception as e:
        print(f"❌ 美食爬蟲錯誤: {e}")
    
    return [] # 失敗回傳空陣列

# ==========================================
# 2. 爬景點 (旅遊王 TravelKing)
# ==========================================
def scrape_travelking(keyword):
    print(f"🕷️ [景點模式] 正在爬取：{keyword} ...")
    # 旅遊王的搜尋網址結構
    url = f"https://www.travelking.com.tw/tourguide/search/qw.asp?q={keyword}"
    headers = { "User-Agent": "Mozilla/5.0" }

    try:
        response = requests.get(url, headers=headers, timeout=5)
        response.encoding = 'utf-8' # 強制編碼，避免亂碼
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            # 抓取搜尋結果列表
            box = soup.find("div", class_="box_search")
            if box:
                items = box.find_all("li", limit=5)
                results = []
                for item in items:
                    try:
                        # 抓標題與連結
                        h4 = item.find("h4")
                        if not h4: continue
                        a_tag = h4.find("a")
                        title = a_tag.text.strip()
                        link = a_tag["href"]
                        
                        # 抓簡介 (作為地址或描述顯示)
                        desc = item.find("div", class_="text").text.strip()[:30] + "..." if item.find("div", class_="text") else "熱門景點"
                        
                        # 抓圖片 (旅遊王搜尋頁有時沒圖，我們用隨機風景圖取代，讓卡片好看)
                        image = "https://images.unsplash.com/photo-1469854523086-cc02fe5d8800" 

                        # 嘗試抓取真實圖片 (如果有)
                        img_tag = item.find("img")
                        if img_tag and "src" in img_tag.attrs:
                            image = img_tag["src"]

                        results.append({
                            "name": title,
                            "score": "推薦", # 景點通常沒評分，改顯示文字
                            "image": image,
                            "address": desc, # 這裡改放簡介
                            "link": link
                        })
                    except: continue
                
                if results: return results
    except Exception as e:
        print(f"❌ 景點爬蟲錯誤: {e}")

    # ==========================================
    # 3. 備援資料 (如果兩個都掛掉)
    # ==========================================
    return [
        {
            "name": f"搜尋失敗: {keyword}",
            "score": "N/A",
            "image": "https://images.unsplash.com/photo-1594322436404-5a0526db4d13",
            "address": "系統忙線中或找不到資料，請稍後再試",
            "link": "https://www.google.com/maps"
        }
    ]