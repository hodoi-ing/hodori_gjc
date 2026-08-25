#!/usr/bin/env python3
import sys
import json
import urllib.request
import urllib.parse
from bs4 import BeautifulSoup

def fetch_today_hot_social_news():
    # 네이버 뉴스 사회(202) 분야 주요 뉴스 / 랭킹 뉴스 URL
    url = "https://news.naver.com/section/102"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Referer": "https://www.naver.com/"
    }
    
    req = urllib.request.Request(url, headers=headers)
    items = []
    
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            soup = BeautifulSoup(html, 'html.parser')
            
            # 사회 섹션 헤드라인/주요 기사 텍스트 및 링크 추출
            headlines = soup.select('div.sa_text')
            for h in headlines:
                title_elem = h.select_one('a.sa_text_title')
                press_elem = h.select_one('div.sa_text_press')
                
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    link = title_elem.get('href', '')
                    press = press_elem.get_text(strip=True) if press_elem else ""
                    
                    if title and link and not any(item['link'] == link for item in items):
                        items.append({
                            "title": title,
                            "press": press,
                            "link": link
                        })
                        
                if len(items) >= 10:
                    break
    except Exception as e:
        return {"error": str(e)}
        
    return items

if __name__ == "__main__":
    news_list = fetch_today_hot_social_news()
    print(json.dumps(news_list, ensure_ascii=False, indent=2))
