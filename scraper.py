import os
import requests
import json
import urllib.parse
import random
import time
from tavily import TavilyClient
from groq import Groq

# 讀取 Keys
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# 定義一張預設的安全圖片 (Unsplash)
DEFAULT_IMAGE = "https://images.unsplash.com/photo-1555939594-58d7cb561ad1"

def get_gmap_link(location_name):
    query = urllib.parse.quote(location_name)
    return f"https://www.google.com/maps/search/?api=1&query={query}"

def analyze_with_ai(text_content, source):
    """
    呼叫 Groq AI 進行閱讀與萃取
    """
    if not GROQ_API_KEY: return []
    
    client = Groq(api_key=GROQ_API_KEY)
    print(f"🧠 [Groq AI] 正在分析 ({source})...")
    
    # 🔥 修改點 1: 更新 Prompt，請 AI 順便抓圖片網址
    prompt = f"""
    你是一個資料萃取機器人。請閱讀以下資料，找出推薦的「店家名稱」。
    
    資料來源 ({source})：
    {text_content}
    
    請嚴格遵守以下規則：
    1. 回傳 JSON 陣列，格式為：
       [{{
           "name": "店名", 
           "address": "地址(沒寫回傳空字串)", 
           "summary": "15字特色短評",
           "image_url": "請從文章中找出代表該店食物的圖片連結(網址)。如果找不到、或者是Plan B摘要模式，請回傳 null"
       }}]
    2. 至少抓 5 間。
    3. 只要 JSON，不要廢話。
    4. 如果找不到，回傳 []。
    """

    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
        )
        ai_response = chat_completion.choices[0].message.content
        
        start_idx = ai_response.find('[')
        end_idx = ai_response.rfind(']') + 1
        
        if start_idx != -1 and end_idx != -1:
            return json.loads(ai_response[start_idx:end_idx])
        return []
    except Exception as e:
        print(f"⚠️ AI 分析錯誤: {e}")
        return []

def scrape_web(keyword):
    print(f"\n🚀 [系統] 收到 LINE 請求，目標：{keyword}")
    
    if not TAVILY_API_KEY or not GROQ_API_KEY:
        print("❌ 錯誤：請確認 Secrets 裡有 Keys")
        return []

    tavily = TavilyClient(api_key=TAVILY_API_KEY)
    
    blacklist_domains = [
        "instagram.com", "facebook.com", "youtube.com", "tiktok.com", 
        "twitter.com", "threads.net", "dcard.tw",
        "trip.com", "klook.com", "kkday.com", "agoda.com", "booking.com"
    ]

    random_terms = ["推薦", "必吃", "懶人包", "食記", "評價", "排行榜"]
    search_term = f"{keyword} {random.choice(random_terms)}"
    print(f"🔍 [Tavily] 正在搜尋：{search_term} ...")

    try:
        search_result = tavily.search(
            query=search_term, 
            search_depth="basic", 
            max_results=10, 
            exclude_domains=blacklist_domains
        )
    except Exception as e:
        print(f"❌ 搜尋失敗: {e}")
        return []

    if not search_result['results']:
        return []

    articles_pool = search_result['results']
    random.shuffle(articles_pool)
    
    max_retries = 3
    final_shops = []

    # ==========================================
    # Plan A: 全文模式 (比較有機會抓到圖)
    # ==========================================
    for attempt in range(1, max_retries + 1):
        if not articles_pool:
            break
            
        current_article = articles_pool.pop()
        print(f"🎬 [第 {attempt} 次嘗試] 讀取：{current_article['title']}")
        
        jina_url = f"https://r.jina.ai/{current_article['url']}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        try:
            page = requests.get(jina_url, headers=headers, timeout=8)
            
            if page.status_code == 200 and len(page.text) > 500:
                found_shops = analyze_with_ai(page.text[:8000], source="全文閱讀")
                
                if found_shops:
                    print(f"🎉 成功抓到 {len(found_shops)} 間店！")
                    final_shops = found_shops
                    break
            else:
                print(f"⚠️ 讀取失敗 Code: {page.status_code}")
        except Exception as e:
            print(f"⚠️ 連線錯誤: {e}")

    # ==========================================
    # Plan B: 摘要模式 (絕對沒圖，AI 會回傳 null)
    # ==========================================
    if not final_shops:
        print("🛡️ [B計畫] 啟動！改用「搜尋摘要」分析...")
        snippets_text = ""
        for item in search_result['results']:
            snippets_text += f"標題：{item['title']}\n摘要：{item['content']}\n\n"
            
        final_shops = analyze_with_ai(snippets_text, source="搜尋摘要")

    # ==========================================
    # 整理結果 (決定要用哪張圖)
    # ==========================================
    if final_shops:
        selected = random.sample(final_shops, min(5, len(final_shops)))
        
        results = []
        for shop in selected:
            raw_address = shop.get('address', '').strip()
            summary = shop.get('summary', '網友推薦美食')
            
            # 🔥 修改點 2: 圖片判斷邏輯
            # 1. 取得 AI 抓到的圖
            ai_image = shop.get('image_url')
            
            # 2. 檢查圖片是否有效 (不是 None，且是 http 開頭)
            if ai_image and ai_image.startswith("http"):
                # 這裡可以再加一個小判斷，如果是 .svg 結尾的通常是 icon，不要用
                if ".svg" in ai_image:
                    display_image = DEFAULT_IMAGE
                else:
                    display_image = ai_image
            else:
                # 3. 如果沒抓到，用預設圖
                display_image = DEFAULT_IMAGE

            # 處理文字
            if len(raw_address) > 2:
                display_text = f"📍 {raw_address} | 📝 {summary}"
            else:
                display_text = f"📝 {summary}"

            if len(display_text) > 60:
                display_text = display_text[:57] + "..."

            results.append({
                "name": shop['name'],
                "address": display_text,     
                "score": "精選",             
                "image": display_image,      # 使用剛剛判斷完的圖片
                "link": get_gmap_link(shop['name'])
            })
        return results
    else:
        return []
