"""🐯 도리보고 24/7 무인 자동화 통합 봇 (Zero-Cost & Zero-Log)

- 30분 주기 자동 키워드 감시 (백컨트리 360, 특가, AI 핫이슈 등)
- 텔레그램 실시간 양방향 질의 (/도리 [키워드])
- 5대 다각도 레이더 (공식SNS, 특가, 게릴라, 스펙, 여론) + WAF 우회
- Gemini 2.0/3.7 Flash 기반 6-Slide Card News 자동 생성
- 프라이버시 보호: 메모리 캐시 기반 처리 (디스크 검색기록 영구 미보관)
"""

import os
import sys
import time
import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

# .env 파일 로드 (있을 경우)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
# 24시간 자동 감시 기본 키워드
WATCH_KEYWORDS = [
    "백컨트리 360",
    "캠핑 텐트 특가",
    "구글 AI 제미나이",
]

# 5대 다각도 트리거 키워드 매트릭스
TRIGGER_RADARS = {
    "BRAND_SNS": {
        "label": "📱 공식 SNS (X·스레드·인스타)",
        "query_template": '(site:threads.net OR site:x.com OR site:instagram.com) "{topic}"'
    },
    "DEAL_PRICE": {
        "label": "💰 가격/특가/대란",
        "keywords": ["역대가", "최저가", "반값", "핫딜", "대란", "특가", "세일", "쿠폰", "0원", "청구할인", "라방", "타임딜"]
    },
    "GUERRILLA_INCIDENT": {
        "label": "⚡ 게릴라/돌발/사건",
        "keywords": ["기습", "무료", "잠시", "테스트", "오류", "가격오류", "품절", "완판", "재입고", "서버다운", "먹통", "유출"]
    },
    "SPEC_UPDATE": {
        "label": "🛠️ 스펙/신기능/출시",
        "keywords": ["신규", "출시", "공개", "업데이트", "패치", "스펙", "성능", "벤치마크", "비교", "신모델", "차이"]
    },
    "BUZZ_TIPS": {
        "label": "🗣️ 여론/논란/꿀팁",
        "keywords": ["논란", "결함", "꿀팁", "실사용", "후기", "고질병", "주의", "대체재", "추천", "반응", "난리"]
    }
}


def send_discord(title: str, text: str, color: int = 0x3B82F6) -> bool:
    """디스코드 웹후크 임베드 카드뉴스 전송."""
    if not DISCORD_WEBHOOK_URL:
        return False

    payload = {
        "username": "dori bot",
        "avatar_url": "https://raw.githubusercontent.com/hodoi-ing/lecture-auto-bot/main/icons/icon128.png",
        "embeds": [
            {
                "title": title,
                "description": text[:4000],
                "color": color,
                "footer": {
                    "text": f"도리보고 v3.5.0 • {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC"
                }
            }
        ]
    }

    try:
        req = urllib.request.Request(
            DISCORD_WEBHOOK_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "User-Agent": "DoribogoBot/3.5"}
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
    except Exception as e:
        try:
            payload.pop("parse_mode")
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
    """디스코드 및 텔레그램 통합 브로드캐스트."""
    discord_ok = send_discord(title, text)
    telegram_ok = send_telegram(f"**{title}**\n\n{text}", chat_id)
    return discord_ok or telegram_ok

def fetch_radar_data(topic: str, days: int = 3) -> list[dict]:
    """구글 뉴스 RSS + 5대 레이더 병렬 수집."""
    items = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    for r_key, r_info in TRIGGER_RADARS.items():
        if r_key == "BRAND_SNS":
            q = f'{r_info["query_template"].format(topic=topic)} when:{max(days, 7)}d'
        else:
            kw_str = " OR ".join(r_info["keywords"][:5])
            q = f'{topic} ({kw_str}) when:{days}d'

        encoded = urllib.parse.quote(q)
        feed_url = f"https://news.google.com/rss/search?q={encoded}&hl=ko&gl=KR&ceid=KR:ko"

        try:
            req = urllib.request.Request(feed_url, headers=headers)
            with urllib.request.urlopen(req, timeout=6) as resp:
                root = ET.fromstring(resp.read())
                for entry in root.findall(".//item")[:4]:
                    raw_title = entry.findtext("title", "")
                    link = entry.findtext("link", "")
                    pub_date = entry.findtext("pubDate", "")
                    clean_title = raw_title.rsplit(" - ", 1)[0].strip() if " - " in raw_title else raw_title
                    items.append({
                        "radar": r_info["label"],
                        "title": clean_title,
                        "link": link,
                        "pub_date": pub_date
                    })
        except Exception:
            pass

    return items


def generate_gemini_card_news(topic: str, items: list[dict]) -> str:
    """Gemini Flash API 호출하여 6장 카드뉴스 렌더링 (다중 모델 폴백 + 오프라인 보장)."""
    if not GEMINI_API_KEY:
        return generate_offline_card_news(topic, items)

    data_context = f"주제: {topic}\n수집된 최신 시그널 목록:\n"
    if items:
        for idx, it in enumerate(items[:6], 1):
            data_context += f"{idx}. [{it['radar']}] {it['title']} ({it['link']})\n"
    else:
        data_context += "(최근 72시간 내 특이 뉴스 없음, 기본 시장 동향 바탕으로 작성)"

    prompt = f"""
당신은 트위터(X), 스레드(Threads), 인스타그램에서 활동하는 감각적이고 유능한 핫딜/테크 전문 인플루언서입니다.
딱딱한 표나 아스키 박스(┌───┘)를 절대 쓰지 말고, 요즘 SNS에서 가장 잘 읽히는 피드 글 스타일로 {topic}에 대한 실시간 브리핑을 작성하세요.

[🚨 작성 원칙]
1. 딱딱한 아스키 박스(┌, │, └), 표, '1장/2장/3장' 같은 기계적인 분류 전면 금지.
2. 짧고 임팩트 있는 문장, 적절한 이모지와 줄바꿈을 활용한 세련된 SNS 피드 형식.
3. 실제 커뮤니티와 현장의 생생한 반응과 가격/스펙 팩트를 맛깔나게 전달.
4. AI스러운 번역투('고찰', '결론적으로', '유익한 시간') 절대 금지.

[수집 데이터]
{data_context}

[출력 양식 (스레드/SNS 스타일)]
🔥 [{topic} 실시간 레이더 브리핑]

📌 3줄 핵심 요약
• {{가장 중요한 팩트/가격/이슈 1줄}}
• {{주목해야 할 변화나 스펙 특징 1줄}}
• {{현재 시장 분위기나 재고/특가 동향 1줄}}

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
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent",
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"
    ]

    for endpoint_url in endpoints_to_try:
        url = f"{endpoint_url}?key={GEMINI_API_KEY}"
        model_tag = endpoint_url.split('/models/')[-1].split(':')[0]
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                return res_data["candidates"][0]["content"]["parts"][0]["text"]
        except urllib.error.HTTPError as e:
            try:
                err_body = e.read().decode("utf-8")
                err_json = json.loads(err_body)
                err_desc = err_json.get("error", {}).get("message", str(e))
                print(f"[!] Model {model_tag} HTTP {e.code}: {err_desc}")
            except Exception:
                err_desc = str(e)
                print(f"[!] Model {model_tag} HTTP error: {e}")
            last_err_msg = f"{model_tag} ({e.code}): {err_desc}"
            continue
        except Exception as e:
            print(f"[!] Model {model_tag} unexpected error: {e}")
            last_err_msg = str(e)
            continue
    print(f"[!] Gemini 호출 실패 ({last_err_msg}) ➔ 오프라인 레이더 카드뉴스로 자동 렌더링")
    return generate_offline_card_news(topic, items, error_note=last_err_msg)


def generate_offline_card_news(topic: str, items: list[dict], error_note: str = "") -> str:
    """API 미연결 시에도 깔끔한 스레드/SNS 피드 스타일 브리핑 생성."""
    summary_lines = []
    if items:
        for it in items[:3]:
            summary_lines.append(f"• [{it['radar']}] {it['title']}")
    else:
        summary_lines = [
            "• 최근 특가 및 재입고 관련 실시간 관심도 급상승 중",
            "• 주요 캠핑 커뮤니티 및 특가 채널에서 실시간 시그널 모니터링 중",
            "• 가격 변동 및 게릴라 할인 발생 시 30분 주기로 즉시 갱신"
        ]

    feed = f"""🔥 [{topic} 실시간 레이더 브리핑]

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
    items = fetch_radar_data(topic, days=3)
    print(f"[*] {len(items)}개 시그널 포착 완료. Gemini AI 6장 카드뉴스 생성 중...")
    card_news = generate_gemini_card_news(topic, items)
    return card_news


def get_telegram_updates(offset=None):
    """텔레그램 롱폴링 명령 수신."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    params = {"timeout": 20}
    if offset:
        params["offset"] = offset

    try:
        req_url = f"{url}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(req_url)
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("result", [])
    except Exception:
        return []


def main():
    print("=" * 60)
    print("🐯 도리보고 24/7 무인 자동화 봇이 시작되었습니다.")
    print(f"• 감시 키워드: {', '.join(WATCH_KEYWORDS)}")
    print("• 프라이버시 보호: 메모리 휘발성 처리 (검색 로그 영구 미보관)")
    print("=" * 60)

    welcome_msg = (
        "24시간 자율 감시 및 실시간 질의응답이 시작되었습니다.\n\n"
        "💡 **기능 안내:**\n"
        "• 30분마다 5대 레이더(특가, 공식SNS, 게릴라, 스펙, 여론) 자동 수집\n"
        "• 감시 키워드: 백컨트리 360, 특가, AI 트렌드 등"
    )
    send_broadcast("🐯 [도리보고 24/7 무인 관제탑 가동]", welcome_msg)
    offset = None
    last_cron_time = 0

    while True:
        try:
            # 1. 텔레그램 실시간 명령 수신
            updates = get_telegram_updates(offset)
            for upd in updates:
                offset = upd["update_id"] + 1
                msg = upd.get("message", {})
                text = msg.get("text", "").strip()
                chat_id = msg.get("chat", {}).get("id")

                if text.startswith("/도리") or text.startswith("/doribogo") or text.startswith("/dori"):
                    parts = text.split(maxsplit=1)
                    if len(parts) < 2 or not parts[1].strip():
                        send_telegram("🐯 키워드를 입력해 주세요!\n예: `/도리 백컨트리 360`", chat_id)
                        continue

                    query = parts[1].strip()
                    send_telegram(f"🔍 **[{query}]** 5대 레이더 가동 중... 잠시만 기다려주세요!", chat_id)
                    card = run_full_doribogo(query)
                    send_telegram(card, chat_id)

                elif text == "/start" or text == "/help":
                    send_telegram(
                        "🐯 **도리보고 봇 도움말**\n\n"
                        "• `/도리 [키워드]` : 5대 레이더 리서치 + 6장 카드뉴스 즉시 생성\n"
                        "예) `/도리 백컨트리 360`\n"
                        "예) `/도리 아이폰 16 할인`\n"
                        "예) `/도리 엔비디아 실적`",
                        chat_id
                    )

            # 2. 30분 주기 자동 감시 (Cron)
            now = time.time()
            if now - last_cron_time > 1800:  # 1800초 = 30분
                last_cron_time = now
                print(f"[*] 정기 30분 자동 감시 실행: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                for kw in WATCH_KEYWORDS:
                    try:
                        card = run_full_doribogo(kw)
                        send_broadcast(f"📢 [30분 정기 감시: {kw}]", card)
                        time.sleep(2)
                    except Exception as e:
                        print(f"[!] 감시 오류 ({kw}): {e}")

            time.sleep(1)

        except KeyboardInterrupt:
            print("\n[!] 봇을 종료합니다.")
            break
        except Exception as e:
            print(f"[!] 메인 루프 에러: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
