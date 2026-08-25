#!/usr/bin/env python3
import sys
import json
import urllib.request
import urllib.parse
from bs4 import BeautifulSoup

def crawl_naver_news(keyword, display=5):
    encoded_keyword = urllib.parse.quote(keyword)
    url = f"https://search.naver.com/search.naver?where=news&query={encoded_keyword}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    req = urllib.request.Request(url, headers=headers)
    items = []
    
    try:
        with urllib.request.urlopen(req) as resp:
            html = resp.read().decode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')
            
            # 네이버 뉴스 기사 링크 및 제목 추출
            news_links = soup.find_all('a', attrs={'title': True})
            for a in news_links:
                title = a.get('title', '').strip()
                href = a.get('href', '')
                if title and href.startswith('http') and len(title) > 5:
                    if not any(item['link'] == href for item in items):
                        items.append({
                            "title": title,
                            "link": href
                        })
                if len(items) >= display:
                    break
    except Exception as e:
        return {"error": str(e)}
        
    return items

def crawl_naver_blog(keyword, display=5):
    encoded_keyword = urllib.parse.quote(keyword)
    url = f"https://search.naver.com/search.naver?where=blog&query={encoded_keyword}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    req = urllib.request.Request(url, headers=headers)
    items = []
    
    try:
        with urllib.request.urlopen(req) as resp:
            html = resp.read().decode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')
            
            # 블로그 제목과 링크
            for a in soup.select('a'):
                href = a.get('href', '')
                text = a.get_text(strip=True)
                if ('blog.naver.com' in href or 'post.naver.com' in href) and len(text) > 8:
                    if not any(item['link'] == href for item in items):
                        items.append({
                            "title": text,
                            "link": href
                        })
                if len(items) >= display:
                    break
    except Exception as e:
        return {"error": str(e)}
        
    return items

if __name__ == "__main__":
    keyword = sys.argv[1] if len(sys.argv) > 1 else "AI 수익화"
    mode = sys.argv[2] if len(sys.argv) > 2 else "news"
    
    if mode == "news":
        res = crawl_naver_news(keyword)
    else:
        res = crawl_naver_blog(keyword)
        
    print(json.dumps(res, ensure_ascii=False, indent=2))
