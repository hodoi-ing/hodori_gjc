#!/usr/bin/env python3
import sys
import json
import time
import random
import urllib.request
import urllib.parse
from bs4 import BeautifulSoup

# 1. 다양한 최신 브라우저 User-Agent 목록 (랜덤 순환용)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:129.0) Gecko/20100101 Firefox/129.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Whale/3.27.254.15 Safari/537.36"
]

def get_random_headers(referer="https://www.naver.com/"):
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": referer,
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin"
    }

def human_delay(min_sec=1.5, max_sec=3.2):
    """사람이 실제 웹페이지를 읽는 것처럼 랜덤 지연시간 부여"""
    sleep_time = random.uniform(min_sec, max_sec)
    time.sleep(sleep_time)

def safe_request(url, referer="https://www.naver.com/", retries=3):
    """안전한 HTTP 요청 (지수 백오프 및 재시도)"""
    for attempt in range(retries):
        try:
            headers = get_random_headers(referer)
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status == 200:
                    return resp.read().decode('utf-8', errors='ignore')
        except Exception as e:
            if attempt == retries - 1:
                return None
            time.sleep((attempt + 1) * 2.0)
    return None

def search_naver_blog(keyword, max_results=5):
    """네이버 블로그 검색 (제재 방지 규칙 적용)"""
    encoded_keyword = urllib.parse.quote(keyword)
    url = f"https://search.naver.com/search.naver?where=blog&query={encoded_keyword}"
    
    html = safe_request(url)
    if not html:
        return {"error": "네이버 검색 요청 실패 (차단 또는 네트워크 오류)"}
        
    soup = BeautifulSoup(html, 'html.parser')
    items = []
    
    for a in soup.select('a'):
        href = a.get('href', '')
        text = a.get_text(strip=True)
        if ('blog.naver.com' in href or 'post.naver.com' in href) and len(text) > 8:
            if not any(item['link'] == href for item in items):
                items.append({
                    "title": text,
                    "link": href
                })
        if len(items) >= max_results:
            break
            
    return items

def fetch_blog_content(blog_url):
    """블로그 본문 수집 (제재 방지 모바일 우회 규칙 적용)"""
    # 모바일 주소로 우회 (보안 스크립트 차단 우회 및 iframe 제거)
    mobile_url = blog_url.replace("blog.naver.com", "m.blog.naver.com")
    
    # 봇 검출 방지를 위해 사람처럼 딜레이
    human_delay(1.2, 2.5)
    
    html = safe_request(mobile_url, referer="https://search.naver.com/")
    if not html:
        return "본문 수집 실패 (차단됨)"
        
    soup = BeautifulSoup(html, 'html.parser')
    content_div = soup.select_one('div.se-main-container') or soup.select_one('div#postViewArea')
    
    if content_div:
        for s in content_div(['script', 'style', 'iframe']):
            s.decompose()
        return content_div.get_text(separator="\n", strip=True)
    else:
        return soup.get_text(separator="\n", strip=True)[:1000]

if __name__ == "__main__":
    keyword = sys.argv[1] if len(sys.argv) > 1 else "AI 자동화"
    print(f"🔍 네이버 안전 검색 중: '{keyword}'...")
    
    results = search_naver_blog(keyword, max_results=3)
    print(f"✅ {len(results)}개 검색 완료.\n")
    
    for idx, item in enumerate(results):
        print(f"[{idx+1}] {item['title']}")
        print(f"🔗 {item['link']}")
        print("📄 본문 읽는 중 (안전 딜레이 적용)...")
        content = fetch_blog_content(item['link'])
        print(f"--- 본문 미리보기 ({len(content)}자) ---")
        print(content[:300] + "...\n")
        
        # 다중 요청 간 랜덤 휴식
        human_delay(2.0, 4.0)
