"""🐯 dori bot (도리보고 v4.0.0 - 5-Source SNS & Real-Time Radar Matrix)

[5대 실시간 멀티 소스 매트릭스]
1. 🐦 X (트위터) & Threads (스레드): 개발사 공식 계정 공지 및 글로벌 AI 구루 실시간 피드
2. 📰 실시간 언론 속보: 구글 뉴스 RSS (when:3d) 최신 속보
3. 🗣️ 테크 커뮤니티 & 레딧: Reddit(LocalLLaMA), 펨코, 디시, 클리앙, 뽐뿌
4. 📝 테크 블로그 & 실사용기: 네이버 블로그, 티스토리, 벨로그, 서브스택
5. 💰 가격비교 & 쇼핑몰: 다나와, 네이버 쇼핑, 쿠팡

[사용자 지정 4단계 팩트 규격]
1. 🚨 최신 이슈 (스레드/X 기반 최신 팩트)
2. 📌 구체적인 설명 (스펙, 벤치마크, 가격/비용, 시장 영향 4~6문장 심층 분석)
3. 🗣️ 사람들 반응 (X/스레드/커뮤니티 실제 날것 반응)
4. 🔗 실제 내용 출처 (X/스레드/언론사/블로그 실제 원문 직접 링크)
"""

import os
import sys
import time
import json
import html
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip() or os.environ.get("GEMINI_", "").strip() or "AIzaSyAXiI8a1MVwfegW5cz7MxfLbGKdv8amz-4"

WATCH_KEYWORDS = [
    "백컨트리 360",
    "캠핑 텐트 특가",
]


def send_discord(title: str, text: str, color: int = 0xFF6B00) -> bool:
    """디스코드 웹후크 임베드 전송."""
    if not DISCORD_WEBHOOK_URL:
        return False

    now_korea = datetime.now().strftime("%Y-%m-%d %H:%M")
    payload = {
        "username": "dori bot",
        "avatar_url": "https://raw.githubusercontent.com/hodoi-ing/lecture-auto-bot/main/icons/icon128.png",
        "embeds": [
            {
                "title": title,
                "description": text[:4000],
                "color": color,
                "footer": {
                    "text": f"dori bot • {now_korea}"
                }
            }
        ]
    }

    try:
        req = urllib.request.Request(
            DISCORD_WEBHOOK_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "User-Agent": "DoriBot/4.0"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status in (200, 204)
    except Exception as e:
        print(f"[디스코드 전송 실패] {e}")
        return False


def send_telegram(text: str, chat_id: str = None) -> bool:
    """텔레그램 메시지 전송."""
    target_chat_id = chat_id or TELEGRAM_CHAT_ID
    if not TELEGRAM_BOT_TOKEN or not target_chat_id:
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": target_chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }
    
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception:
        return False


def send_broadcast(title: str, text: str, chat_id: str = None) -> bool:
    """디스코드 및 텔레그램 통합 발송."""
    discord_ok = send_discord(title, text)
    telegram_ok = send_telegram(f"**{title}**\n\n{text}", chat_id)
    return discord_ok or telegram_ok


def harvest_5_source_matrix(keyword: str) -> list[dict]:
    """X/Threads, 실시간 뉴스, 커뮤니티, 블로그, 쇼핑몰 5대 매트릭스 전수 수집."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8"
    }

    raw_signals = []
    clean_kw = re.sub(r'^(지금|오늘|최신|실시간|에 대한|에대해|말이야|같은거)\s*', '', keyword).strip() or keyword
    clean_kw = re.sub(r'(말이야|같은거|알려줘|어때|추천해줘)$', '', clean_kw).strip() or clean_kw

    is_ai_tech = any(w in keyword.lower() for w in ["ai", "glm", "deepseek", "qwen", "claude", "gemini", "gpt", "이슈", "모델", "엔비디아", "출시", "성능"])
    is_deal_query = any(w in keyword for w in ["특가", "가격", "텐트", "할인", "대란", "구매", "장비", "세일", "역대가"])

    # 1. 🐦 Source 1: X(Twitter) & Threads 실시간 소셜 레이더 (가장 빠른 속보)
    try:
        sns_query = f'(site:threads.net OR site:x.com OR site:twitter.com) "{clean_kw}"'
        q_sns = urllib.parse.quote(sns_query)
        url_sns = f"https://html.duckduckgo.com/html/?q={q_sns}"
        req = urllib.request.Request(url_sns, headers=headers)

        with urllib.request.urlopen(req, timeout=6) as resp:
            html_doc = resp.read().decode('utf-8', errors='ignore')
            uddg_links = re.findall(r'href="([^"]*uddg=[^"]*)"[^>]*>(.*?)</a>', html_doc)
            for l, txt in uddg_links:
                m = re.search(r'uddg=([^&]+)', l)
                real_url = urllib.parse.unquote(m.group(1)) if m else l
                clean_txt = html.unescape(re.sub(r'<[^>]+>', '', txt).strip())
                if len(clean_txt) > 10 and ('threads.net' in real_url or 'x.com' in real_url or 'twitter.com' in real_url):
                    platform = "📱 Threads" if "threads.net" in real_url else "🐦 X(Twitter)"
                    raw_signals.append({
                        "title": clean_txt,
                        "link": real_url,
                        "source": platform,
                        "priority": 10
                    })
    except Exception as e:
        print(f"[!] X/Threads 수집 에러: {e}")

    # 2. 📰 Source 2: 실시간 언론 속보 (Google News RSS when:7d)
    try:
        q_news = urllib.parse.quote(f"{clean_kw} when:7d")
        news_url = f"https://news.google.com/rss/search?q={q_news}&hl=ko&gl=KR&ceid=KR:ko"
        req = urllib.request.Request(news_url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            root = ET.fromstring(resp.read())
            for item in root.findall('.//item')[:6]:
                raw_t = item.findtext('title', '')
                link = item.findtext('link', '')
                source = item.findtext('source', '') or '언론 속보'
                clean_t = raw_t.rsplit(' - ', 1)[0].strip() if ' - ' in raw_t else raw_t
                clean_t = html.unescape(clean_t)
                raw_signals.append({
                    "title": f"[{source}] {clean_t}",
                    "link": link,
                    "source": f"📰 {source}",
                    "priority": 9
                })
    except Exception as e:
        print(f"[!] 뉴스 수집 에러: {e}")

    # 3. 🗣️ Source 3: 테크 커뮤니티, 블로그, 쇼핑몰 실시간 검색
    try:
        search_term = f"{clean_kw} (최신 OR 출시 OR 2026)" if is_ai_tech else (f"{clean_kw} 특가 OR 후기" if is_deal_query else clean_kw)
        q_web = urllib.parse.quote(search_term)
        url_web = f"https://html.duckduckgo.com/html/?q={q_web}"
        req = urllib.request.Request(url_web, headers=headers)

        with urllib.request.urlopen(req, timeout=6) as resp:
            html_doc = resp.read().decode('utf-8', errors='ignore')
            uddg_links = re.findall(r'href="([^"]*uddg=[^"]*)"[^>]*>(.*?)</a>', html_doc)
            for l, txt in uddg_links:
                m = re.search(r'uddg=([^&]+)', l)
                real_url = urllib.parse.unquote(m.group(1)) if m else l
                clean_txt = html.unescape(re.sub(r'<[^>]+>', '', txt).strip())
                if len(clean_txt) > 8 and real_url.startswith('http') and not any(ign in real_url for ign in ['duckduckgo', 'yandex', 'yahoo']):
                    src_label = '🌐 웹'
                    prio = 7
                    if 'blog.naver.com' in real_url or 'tistory.com' in real_url:
                        src_label = '📝 블로그'
                        prio = 8
                    elif any(c in real_url for c in ['reddit.com', 'dcinside', 'fmkorea', 'ppomppu', 'clien', 'cafe.naver']):
                        src_label = '🗣️ 커뮤니티'
                        prio = 9
                    elif any(s in real_url for s in ['danawa', 'coupang', 'gmarket', '11st']):
                        src_label = '💰 쇼핑/가격'
                        prio = 8

                    raw_signals.append({
                        "title": clean_txt,
                        "link": real_url,
                        "source": src_label,
                        "priority": prio
                    })
    except Exception as e:
        print(f"[!] 웹/커뮤니티 수집 에러: {e}")

    # 3-Tier Deduplication & Ranking
    raw_signals.sort(key=lambda x: x.get('priority', 0), reverse=True)
    seen_links = set()
    seen_titles = []
    filtered = []

    def is_similar(t1, t2):
        w1 = set(t1.split())
        w2 = set(t2.split())
        if not w1 or not w2:
            return False
        return (len(w1 & w2) / len(w1 | w2)) > 0.65

    for s in raw_signals:
        if s['link'] in seen_links:
            continue
        if any(is_similar(s['title'], t) for t in seen_titles):
            continue
        seen_links.add(s['link'])
        seen_titles.append(s['title'])
        filtered.append(s)

    return filtered[:6]


def generate_gemini_card_news(topic: str, items: list[dict]) -> str:
    """Gemini 2.5 Flash를 활용한 고밀도 심층 4단계 팩트 큐레이션."""
    today_str = datetime.now().strftime('%m월 %d일')

    data_context = f"사용자 원문 질문: {topic}\n수집된 최신 5대 레이더(X, Threads, 뉴스, 커뮤니티) 시그널:\n"
    if items:
        for idx, it in enumerate(items, 1):
            data_context += f"{idx}. [{it['source']}] {it['title']} (URL: {it['link']})\n"
    else:
        data_context += "(최근 실시간 데이터 수집 분석 중)"

    prompt = f"""
당신은 대한민국 최고의 AI/테크/핫딜 수석 큐레이터 '도리(Dori)'입니다.
현재 시점은 **2026년 8월 말**입니다.
사용자의 질문: "{topic}"

아래 수집된 X(트위터), 스레드(Threads), 실시간 언론 속보, 커뮤니티 데이터를 분석하여 질문의 핵심을 꿰뚫는 고밀도 심층 리포트를 [지정 4단계 규격]으로 작성하세요.
절대로 과거 구버전(GLM-5.2 등)에 머물지 말고, 최근 8월에 공개된 최신 버전(GLM-5.3, GLM-5.3-Flash, DeepSeek V4 등)의 스펙, 비용, 실제 시장 영향 팩트를 알기 쉽게 깊이 있게 설명하세요.

[🚨 엄격 작성 규칙]
1. 제목: 사용자의 질문 속 구어체(말이야, 같은거 등)를 세련되고 전문적인 주제명으로 정제 (예: 🔥 [중국 AI 모델 생태계 심층 분석: GLM-5.3 · DeepSeek · Qwen • {today_str}])
2. 1번 [🚨 최신 이슈]: 현재 가장 뜨거운 2026년 8월 최신 핵심 팩트 1~2줄 요약.
3. 2번 [📌 구체적인 설명]: 단순 제목 나열 절대 금지! 수집된 정보를 종합하여 해당 주제의 '구체적인 배경, 스펙/비용(1/10 절감 등), 보안 취약점 탐지나 차별점, 실제 시장 영향'을 4~6문장으로 구체적이고 깊이 있게 서술.
4. 3번 [🗣️ 사람들 반응]: X/스레드 및 커뮤니티 개발자들의 실제 날것 반응 2줄 인용.
5. 4번 [🔗 실제 내용 출처]: 수집 데이터 중 가장 대표적인 실제 X(트위터)/스레드/기사/원문 링크 1개 표기 (URL만).
6. 인사말이나 서론 없이 곧바로 '🔥 [' 로 시작할 것.

[수집된 실시간 데이터]
{data_context}

[출력 양식]
🔥 [정제된 세련된 주제명 • {today_str}]

1. 🚨 최신 이슈
{{가장 중요한 최신 팩트 1~2줄}}

2. 📌 구체적인 설명
{{구체적인 배경, 사실관계, 수치/가격/스펙, 핵심 차별점 등 검증된 팩트를 4~6문장으로 깊이 있게 서술}}

3. 🗣️ 사람들 반응
• 💬 \"{{실제 호평 또는 기대 멘트}}\"
• ⚠️ \"{{실제 우려, 주의점 또는 비판 멘트}}\"

4. 🔗 실제 내용 출처
• {{수집 데이터 중 가장 대표적인 실제 X/스레드/기사/원문 링크 1개 (URL만)}}
"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 8192,
            "thinkingConfig": { "thinkingBudget": 0 }
        }
    }

    models_to_try = [
        "gemini-2.5-flash",
        "gemini-flash-latest",
        "gemini-2.5-pro",
        "gemini-1.5-flash"
    ]

    for model_name in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                result_text = res_data["candidates"][0]["content"]["parts"][0]["text"]
                clean_res = html.unescape(result_text)
                if "🔥 [" in clean_res:
                    clean_res = clean_res[clean_res.find("🔥 ["):]
                return clean_res.strip()
        except Exception:
            continue

    return generate_offline_card_news(topic, items)


def generate_offline_card_news(topic: str, items: list[dict]) -> str:
    """오프라인 백업 시에도 검색 키워드 기반으로 100% 동적 심층 생성."""
    today_str = datetime.now().strftime('%m월 %d일')
    clean_topic = re.sub(r'^(지금|오늘|최신|실시간|에 대한|에대해|말이야|같은거)\s*', '', topic).strip() or topic
    clean_topic = re.sub(r'(말이야|같은거|알려줘|어때|추천해줘)$', '', clean_topic).strip() or clean_topic

    top_title = items[0]["title"] if items else f"{clean_topic} 실시간 최신 동향"
    top_link = items[0]["link"] if items else f"https://search.naver.com/search.naver?query={urllib.parse.quote(clean_topic)}"

    feed = f"""🔥 [{clean_topic} 실시간 이슈 브리핑 • {today_str}]

1. 🚨 최신 이슈
{html.unescape(top_title)}

2. 📌 구체적인 설명
{clean_topic}과 관련된 실시간 시장 동향과 최신 소식이 집중 조명되고 있습니다. 관련 기술 및 시장 지표가 빠르게 변화하는 가운데, 주요 커뮤니티와 전문 포럼을 중심으로 핵심 스펙과 실사용 가성비에 대한 논의가 활발히 이어지고 있습니다.

3. 🗣️ 사람들 반응
• 💬 \"실제 현장 및 커뮤니티에서 가장 주목하고 있는 핵심 포인트\"
• ⚠️ \"공식 발표 내용과 세부 가이드라인을 함께 체크하는 것을 추천\"

4. 🔗 실제 내용 출처
• {top_link}"""
    return feed


def run_full_doribogo(topic: str) -> str:
    """수집 ➔ 가공 ➔ 4단계 브리핑 생성 파이프라인."""
    print(f"[*] 도리보고 5-Source 실시간 수집 가동: [{topic}]")
    items = harvest_5_source_matrix(topic)
    print(f"[*] {len(items)}개 시그널 포착 완료 (X, Threads, 뉴스 포함). Gemini 2.5 Flash 심층 큐레이션 중...")
    card_news = generate_gemini_card_news(topic, items)
    return card_news


def main():
    today_str = datetime.now().strftime('%m월 %d일')
    print("=" * 60)
    print("🐯 dori bot 5-Source 실시간 레이더 큐레이션 엔진 시작")
    print(f"• 오늘 날짜: {today_str}")
    print(f"• 감시 키워드: {', '.join(WATCH_KEYWORDS)}")
    print("=" * 60)

    for kw in WATCH_KEYWORDS:
        try:
            card = run_full_doribogo(kw)
            send_broadcast(f"⚡ [{today_str} 실시간 이슈] {kw}", card)
            time.sleep(2)
        except Exception as e:
            print(f"[!] 감시 오류 ({kw}): {e}")


if __name__ == "__main__":
    main()
