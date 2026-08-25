#!/usr/bin/env python3
import sys
import json
import urllib.request
import urllib.parse
from bs4 import BeautifulSoup

def fetch_blog_post_body(blog_url):
    """네이버 블로그 URL에서 본문 전체 텍스트 추출 (iframe 처리 포함)"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # 모바일 URL로 변경하면 iframe 없이 바로 본문 수집 가능
    mobile_url = blog_url.replace("blog.naver.com", "m.blog.naver.com")
    
    try:
        req = urllib.request.Request(mobile_url, headers=headers)
        with urllib.request.urlopen(req) as resp:
            html = resp.read().decode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')
            
            # 모바일 네이버 블로그 본문 태그
            content_div = soup.select_one('div.se-main-container') or soup.select_one('div#postViewArea')
            if content_div:
                # 불필요한 스크립트/스타일 제거
                for s in content_div(['script', 'style']):
                    s.decompose()
                return content_div.get_text(separator="\n", strip=True)
            else:
                return soup.get_text(separator="\n", strip=True)[:1000]
    except Exception as e:
        return f"Error: {e}"

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://blog.naver.com/dhsia0618/224368175497"
    print(f"=== 블로그 본문 추출: {url} ===")
    content = fetch_blog_post_body(url)
    print(content[:1500]) # 1500자까지 미리보기
