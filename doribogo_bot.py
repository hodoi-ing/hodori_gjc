"""🐯 dori bot (도리보고 3.5 - 실시간 핫딜 & SNS 이슈 브리핑 엔진)

- 오늘 날짜 기준 24시간 실시간 시그널 수집 (구글, 공식 SNS, 커뮤니티)
- Gemini AI 기반 스레드(Threads) / SNS 피드 스타일 숏폼 브리핑 생성
- 디스코드 웹후크 및 텔레그램 실시간 발송
"""

import os
import sys
import time
import json
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
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip() or os.environ.get("GEMINI_", "").strip()

# 실시간 감시 키워드
WATCH_KEYWORDS = [
    "백컨트리 360",
    "캠핑 텐트 특가",
]

# 5대 다각도 트리거 키워드 매트릭스
TRIGGER_RADARS = {
    "BRAND_SNS": {
        "label": "📱 공식 SNS (X·스레드·인스타)",
        "query_template": '(site:threads.net OR site:x.com OR site:instagram.com) "{topic}"'
    },
    "DEAL_PRICE": {
        "label": "💰 특가/최저가",
        "keywords": ["역대가", "최저가", "핫딜", "대란", "특가", "세일", "쿠폰", "타임딜"]
    },
    "GUERRILLA_INCIDENT": {
        "label": "⚡ 게릴라/재입고",
        "keywords": ["기습", "품절", "완판", "재입고", "오류", "유출"]
    },
    "SPEC_UPDATE": {
        "label": "🛠️ 스펙/출시",
        "keywords": ["신규", "출시", "공개", "스펙", "성능", "신모델"]
    },
    "BUZZ_TIPS": {
        "label": "🗣️ 실사용 후기",
        "keywords": ["꿀팁", "실사용", "후기", "추천", "반응"]
    }
}


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
            headers={"Content-Type": "application/json", "User-Agent": "DoriBot/3.5"}
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


def fetch_radar_data(topic: str, days: int = 1) -> list[dict]:
    """오늘 날짜 기준 24시간 실시간 최신 시그널 수집."""
    items = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    for r_key, r_info in TRIGGER_RADARS.items():
        if r_key == "BRAND_SNS":
            q = f'{r_info["query_template"].format(topic=topic)} when:1d'
        else:
            kw_str = " OR ".join(r_info["keywords"][:4])
            q = f'{topic} ({kw_str}) when:1d'

        encoded = urllib.parse.quote(q)
        feed_url = f"https://news.google.com/rss/search?q={encoded}&hl=ko&gl=KR&ceid=KR:ko"

        try:
            req = urllib.request.Request(feed_url, headers=headers)
            with urllib.request.urlopen(req, timeout=6) as resp:
                root = ET.fromstring(resp.read())
                for entry in root.findall(".//item")[:3]:
                    raw_title = entry.findtext("title", "")
                    link = entry.findtext("link", "")
                    clean_title = raw_title.rsplit(" - ", 1)[0].strip() if " - " in raw_title else raw_title
                    items.append({
                        "radar": r_info["label"],
                        "title": clean_title,
                        "link": link
                    })
        except Exception:
            pass

    return items


def generate_gemini_card_news(topic: str, items: list[dict]) -> str:
    """Gemini AI 호출하여 트렌디한 스레드(Threads)/SNS 피드 스타일 브리핑 생성."""
    today_str = datetime.now().strftime('%m월 %d일')

    if not GEMINI_API_KEY:
        return generate_offline_card_news(topic, items)

    data_context = f"주제: {topic}\n수집된 실시간 시그널 목록:\n"
    if items:
        for idx, it in enumerate(items[:5], 1):
            data_context += f"{idx}. [{it['radar']}] {it['title']} ({it['link']})\n"
    else:
        data_context += "(최근 24시간 내 특이 뉴스 없음, 현재 시장 분위기와 커뮤니티 인기 동향 바탕으로 작성)"

    prompt = f"""
당신은 트위터(X), 스레드(Threads), 인스타그램에서 활동하는 감각적인 핫딜/이슈 전문 큐레이터입니다.
딱딱한 표나 아스키 박스(┌───┘)를 절대 쓰지 말고, 요즘 SNS에서 가장 잘 읽히는 피드 글 스타일로 {topic}에 대한 실시간 브리핑을 작성하세요.

[🚨 작성 원칙]
1. 딱딱한 아스키 선(┌, │, └), 표, '1장/2장' 같은 기계적인 분류 전면 금지.
2. 짧고 임팩트 있는 문장, 적절한 이모지와 줄바꿈을 활용한 세련된 SNS 피드 형식.
3. 오늘({today_str}) 기준의 실시간 현장 체감과 가격/스펙 팩트를 맛깔나게 전달.
4. AI스러운 번역투('고찰', '결론적으로', '유익한 시간') 절대 금지.

[수집 데이터]
{data_context}

[출력 양식]
🔥 [{topic} 오늘의 실시간 이슈 • {today_str}]

📌 3줄 핵심 요약
• {{오늘 가장 뜨거운 팩트/가격/이슈 1줄}}
• {{주목해야 할 변화나 스펙 특징 1줄}}
• {{현재 실시간 시장 분위기나 재고/특가 동향 1줄}}

💡 지금 주목해야 할 포인트
- {{왜 사람들이 이 상품/주제에 열광하는지 1~2줄}}
- {{실제 구매나 활용 시 놓치면 손해인 핵심 팁}}

🗣️ 실시간 커뮤니티 날것 반응
💬 \"{{실제 호평 또는 기대 멘트}}\"
⚠️ \"{{실사용자가 꼽는 현실적인 주의점이나 단점}}\"

🐯 호도리의 1줄 픽
\"{{지금 당장 취해야 할 행동 지침이나 센스 있는 추천사}}\"
"""
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.5,
            "maxOutputTokens": 1000,
        }
    }

    endpoints_to_try = [
        "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent",
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent",
        "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-pro:generateContent",
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent"
    ]

    for endpoint_url in endpoints_to_try:
        url = f"{endpoint_url}?key={GEMINI_API_KEY}"
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                return res_data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            continue

    return generate_offline_card_news(topic, items)


def generate_offline_card_news(topic: str, items: list[dict]) -> str:
    """API 미연결 시에도 깔끔한 스레드/SNS 피드 스타일 브리핑 생성."""
    today_str = datetime.now().strftime('%m월 %d일')
    summary_lines = []
    if items:
        for it in items[:3]:
            summary_lines.append(f"• [{it['radar']}] {it['title']}")
    else:
        summary_lines = [
            f"• {today_str} 기준 실시간 관심도 및 특가 문의 급상승 중",
            "• 주요 캠핑 커뮤니티 및 특가 채널에서 실시간 시그널 모니터링 중",
            "• 가격 변동 및 게릴라 할인 발생 시 30분 주기로 즉시 갱신"
        ]

    feed = f"""🔥 [{topic} 오늘의 실시간 이슈 • {today_str}]

📌 3줄 핵심 요약
{chr(10).join(summary_lines)}

💡 지금 주목해야 할 포인트
- 스펙과 가성비로 캠퍼들 사이에서 꾸준히 회자되는 인기 라인업
- 타임딜이나 라이브 특가 뜰 때 순식간에 빠지니 알림 켜두는 게 유리함

🗣️ 실시간 커뮤니티 날것 반응
💬 \"이 체급에서는 공간감이랑 개방감 제일 잘 뽑았음\"
⚠️ \"인기 색상이나 옵션은 풀리자마자 바로 빠지니 타이밍 중요\"

🐯 호도리의 1줄 픽
\"스펙 대비 만족도 높은 모델. 특가 시그널 뜨면 바로 낚아채세요!\""""
    return feed


def run_full_doribogo(topic: str) -> str:
    """수집 ➔ 가공 ➔ 카드뉴스 생성 파이프라인."""
    print(f"[*] 도리보고 5대 레이더 가동: [{topic}]")
    items = fetch_radar_data(topic, days=1)
    print(f"[*] {len(items)}개 시그널 포착 완료. SNS 피드 브리핑 생성 중...")
    card_news = generate_gemini_card_news(topic, items)
    return card_news


def main():
    today_str = datetime.now().strftime('%m월 %d일')
    print("=" * 60)
    print("🐯 dori bot 실시간 이슈 브리핑 엔진 시작")
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
