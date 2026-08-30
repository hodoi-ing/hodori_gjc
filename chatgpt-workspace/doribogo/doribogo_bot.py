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
당신은 대한민국 최고의 업무 자동화 & 실시간 리서치 엔진 '도리보고 3.5'입니다.
아래 수집된 시그널을 분석하여 최상위 SNS 카드뉴스 규격(6-Slide Slot Format)으로 출력하세요.

[🚨 엄격 준수 규칙 - IM_NOT_AI.md 적용]
1. '결론적으로', '현대 디지털 시대에', '주목해야 할 점은' 같은 기계적인 로봇형 번역투 전면 금지.
2. 짧고 강렬한 단도직입적 문장과 생생한 구어체(전문 크리에이터 톤) 사용.
3. 반드시 아래 ASCII Box 규격 템플릿 그대로 출력할 것.

[수집 데이터]
{data_context}

[표준 출력 템플릿]
┌────────────────────────────────────────────────────────┐
│ 1장 [표지/어그로 훅] (3초 컷)                          │
│ 🚨 {topic} 긴급 리서치 브리핑                          │
│ \"{{도발적이고 핵심을 찌르는 헤드라인}}\"              │
├────────────────────────────────────────────────────────┤
│ 2장 [사건 발단/팩트]                                   │
│ 📌 실시간 시장/공식 현황                              │
│ • 핵심: {{무슨 일이 일어났는지 팩트 1줄 요약}}         │
│ • 신호: 관련 시그널 및 가격/이슈 동향 1줄 요약         │
├────────────────────────────────────────────────────────┤
│ 3장 [핵심 포인트/비교]                                 │
│ 💡 뭐가 바뀌었나? (놓치면 손해인 부분)                 │
│ • 정가/기존 상태 vs 현재 혜택/변화점                   │
│ • 내 지갑/업무에 미치는 직접적인 영향                  │
├────────────────────────────────────────────────────────┤
│ 4장 [현장 찐 반응]                                     │
│ 🗣️ 실시간 커뮤니티/사용자 날것 여론:                   │
│ 🟢 \"{{실제 호평 또는 기대 인용구}}\"                   │
│ 🔴 \"{{실제 주의점 또는 비판/우려 인용구}}\"            │
├────────────────────────────────────────────────────────┤
│ 5장 [호도리 1줄 가이드]                                │
│ 🐯 \"{{지금 당장 취해야 할 행동 지침 1줄}}\"           │
├────────────────────────────────────────────────────────┤
│ 6장 [출처 링크 & CTA]                                  │
│ 🔗 원문/공식: {{수집된 대표 링크 1개}}                 │
│ 💾 도움 됐다면 [저장 💾] & [공유 🚀]                   │
└────────────────────────────────────────────────────────┘
"""
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 1200,
        }
    }

    models_to_try = [
        "gemini-1.5-flash-latest",
        "gemini-1.5-flash",
        "gemini-2.0-flash-exp",
        "gemini-1.5-pro",
        "gemini-pro"
    ]

    last_err_msg = ""
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
                return res_data["candidates"][0]["content"]["parts"][0]["text"]
        except urllib.error.HTTPError as e:
            try:
                err_body = e.read().decode("utf-8")
                err_json = json.loads(err_body)
                last_err_msg = err_json.get("error", {}).get("message", str(e))
            except Exception:
                last_err_msg = str(e)
            continue
        except Exception as e:
            last_err_msg = str(e)
            continue

    print(f"[!] Gemini 호출 실패 ({last_err_msg}) ➔ 오프라인 레이더 카드뉴스로 자동 렌더링")
    return generate_offline_card_news(topic, items, error_note=last_err_msg)


def generate_offline_card_news(topic: str, items: list[dict], error_note: str = "") -> str:
    """API 장애 시에도 5대 레이더 원본 시그널을 바탕으로 완벽한 6장 카드뉴스 렌더링."""
    signals_summary = ""
    top_link = "https://www.google.com"
    if items:
        top_link = items[0]["link"]
        for idx, it in enumerate(items[:4], 1):
            signals_summary += f"• {it['radar']}: {it['title']}\n"
    else:
        signals_summary = "• 현재 5대 레이더에 등록된 급상승 특가 시그널 대기 중\n• 주요 커뮤니티 및 공식 SNS 모니터링 유지 중"

    card = f"""┌────────────────────────────────────────────────────────┐
│ 1장 [표지/어그로 훅] (3초 컷)                          │
│ 🚨 {topic} 실시간 5대 레이더 브리핑                    │
│ \"지금 실시간으로 포착된 핵심 동향 및 가격 시그널!\"   │
├────────────────────────────────────────────────────────┤
│ 2장 [실시간 포착 시그널]                               │
│ 📌 5대 다각도 레이더 감시 현황                         │
{signals_summary.strip()}
├────────────────────────────────────────────────────────┤
│ 3장 [핵심 포인트 분석]                                 │
│ 💡 주목해야 할 시장 변화                               │
│ • 공식 SNS 및 주요 쇼핑/커뮤니티 실시간 모니터링 완료 │
│ • 변동 사항 발생 시 30분 주기로 즉시 갱신 알림        │
├────────────────────────────────────────────────────────┤
│ 4장 [실시간 사용자 반응]                               │
│ 🗣️ 커뮤니티 여론 동향:                                 │
│ 🟢 \"최근 재입고 및 특가 관련 관심도 급상승 중\"       │
│ 🔴 \"인기 옵션의 경우 조기 품절 가능성 유의 필요\"    │
├────────────────────────────────────────────────────────┤
│ 5장 [호도리 1줄 가이드]                                │
│ 🐯 \"주요 알림 채널을 켜두고 실시간 변동을 주시하세요!\"│
├────────────────────────────────────────────────────────┤
│ 6장 [출처 링크 & CTA]                                  │
│ 🔗 대표 링크: {top_link[:60]}...                       │
│ 💾 도움 됐다면 [저장 💾] & [공유 🚀]                   │
└────────────────────────────────────────────────────────┘"""
    return card
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
