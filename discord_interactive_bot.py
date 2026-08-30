"""🐯 dori bot - 실시간 디스코드 통합 비서 봇 (discord.py)

💡 지원 명령어:
• !도리 [키워드] : 5대 레이더 실시간 리서치 ➔ 4단계 팩트 브리핑 출력
• !ai [질문/코드/번역] : Gemini AI 자유 대화, 코딩, 번역, 문서 작성 비서
• !도움말 : 전체 명령어 안내
• 30분 주기 정기 자동 브리핑
"""

import os
import sys
import time
import json
import asyncio
import urllib.request
import html
from datetime import datetime, timezone

try:
    import discord
    from discord.ext import commands, tasks
except ImportError:
    print("[!] discord.py가 설치되지 않았습니다.")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import doribogo_bot

DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "").strip()
DISCORD_CHANNEL_ID = os.environ.get("DISCORD_CHANNEL_ID", "").strip()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip() or os.environ.get("GEMINI_", "").strip() or "AIzaSyAXiI8a1MVwfegW5cz7MxfLbGKdv8amz-4"

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

WATCH_KEYWORDS = ["백컨트리 360", "캠핑 텐트 특가"]


@bot.event
async def on_ready():
    print("=" * 60)
    print(f"🐯 hodori bot 통합 비서 가동 완료: {bot.user.name} ({bot.user.id})")
    print("• 지원 명령어: !도리 [키워드], !ai [질문], !도움말")
    print("=" * 60)
    if not auto_radar_loop.is_running():
        auto_radar_loop.start()


# --- 기능 1: 도리보고 실시간 팩트 큐레이션 (!도리) ---
@bot.command(name="도리", aliases=["dori", "doribogo"])
async def dori_command(ctx, *, keyword: str = ""):
    """실시간 5대 레이더 4단계 팩트 큐레이션."""
    keyword = keyword.strip()
    if not keyword or keyword in ["도움말", "help", "?"]:
        await send_help(ctx)
        return

    loading_msg = await ctx.send(f"🔍 **[{keyword}]** 5대 레이더 실시간 수집 및 팩트 분석 중... ⏳")

    try:
        loop = asyncio.get_event_loop()
        card_news = await loop.run_in_executor(None, doribogo_bot.run_full_doribogo, keyword)
        today_str = datetime.now().strftime("%m월 %d일")

        embed = discord.Embed(
            title=f"⚡ [{today_str} 실시간 이슈] {keyword}",
            description=card_news,
            color=0xFF6B00
        )
        embed.set_footer(text=f"hodori bot • {datetime.now().strftime('%Y-%m-%d %H:%M')}")

        await loading_msg.delete()
        await ctx.send(embed=embed)

    except Exception as e:
        await loading_msg.edit(content=f"❌ **[{keyword}]** 분석 중 오류 발생: {e}")


# --- 기능 2: Gemini AI 자유 대화 & 코딩/번역 비서 (!ai, !질문) ---
@bot.command(name="ai", aliases=["질문", "q", "ask"])
async def ai_chat_command(ctx, *, query: str = ""):
    """Gemini 2.5 Flash 기반 자유 대화, 코딩, 번역, 문서 작성 비서."""
    query = query.strip()
    if not query:
        await ctx.send("🐯 질문이나 요청할 내용을 입력해주세요!\n예) `!ai 파이썬 비동기 처리 코드 예제 짜줘`\n예) `!ai 이 영어 문장 자연스럽게 번역해줘`")
        return

    loading_msg = await ctx.send(f"🧠 **[{query[:30]}...]** Gemini AI 분석 중... ⏳")

    try:
        loop = asyncio.get_event_loop()
        answer = await loop.run_in_executor(None, call_gemini_general, query)

        # 디스코드 2000자 제한 대응 분할 전송
        await loading_msg.delete()
        
        if len(answer) <= 2000:
            embed = discord.Embed(
                title=f"💡 [AI 답변] {query[:40]}",
                description=answer,
                color=0x3B82F6
            )
            embed.set_footer(text="hodori bot • Powered by Gemini 2.5 Flash")
            await ctx.send(embed=embed)
        else:
            # 2000자 초과 시 텍스트로 분할 발송
            chunks = [answer[i:i+1900] for i in range(0, len(answer), 1900)]
            for idx, ch in enumerate(chunks, 1):
                await ctx.send(f"**[답변 {idx}/{len(chunks)}]**\n{ch}")

    except Exception as e:
        await loading_msg.edit(content=f"❌ AI 답변 생성 중 오류 발생: {e}")


def call_gemini_general(prompt: str) -> str:
    """Gemini 2.5 Flash 범용 질의응답."""
    system_instruction = (
        "당신은 친절하고 유능하며 명쾌한 AI 수석 비서 '호도리봇(hodori bot)'입니다. "
        "사용자의 질문에 대해 핵심을 찌르는 친절하고 전문적인 한국어로 답변하세요. "
        "코딩 질문에는 실행 가능한 깔끔한 코드 블록과 핵심 해설을 제공하세요."
    )
    
    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": f"[시스템 지침: {system_instruction}]\n\n사용자 질문: {prompt}"}]}
        ],
        "generationConfig": {
            "temperature": 0.5,
            "maxOutputTokens": 8192,
            "thinkingConfig": {"thinkingBudget": 0}
        }
    }

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        res_data = json.loads(resp.read().decode("utf-8"))
        return res_data["candidates"][0]["content"]["parts"][0]["text"].strip()


@bot.command(name="도움말", aliases=["help", "명령어"])
async def help_command(ctx):
    await send_help(ctx)


async def send_help(ctx):
    embed = discord.Embed(
        title="🐯 hodori bot 명령어 안내",
        description=(
            "**1. 실시간 팩트 큐레이션 (!도리)**\n"
            "• `!도리 [키워드]` : 5대 레이더 실시간 리서치 + 4단계 팩트 리포트 출력\n"
            "• 예시: `!도리 중국 AI 이슈` | `!도리 백컨트리 360`\n\n"
            "**2. AI 자유 질문 & 코딩/번역 비서 (!ai)**\n"
            "• `!ai [질문]` 또는 `!질문 [질문]` : Gemini AI 범용 질의응답\n"
            "• 예시: `!ai 파이썬 디스코드 봇 예제 코드 짜줘`\n"
            "• 예시: `!ai 이 비즈니스 메일 영어로 정중하게 번역해줘`\n\n"
            "**3. 24시간 클라우드 자동 알림**\n"
            "• 30분마다 주요 감시 키워드 브리핑이 자동 전송됩니다."
        ),
        color=0x10B981
    )
    embed.set_footer(text="hodori bot • 만능 개인 비서")
    await ctx.send(embed=embed)


@tasks.loop(minutes=30)
async def auto_radar_loop():
    """30분 주기 정기 자동 브리핑."""
    if not DISCORD_CHANNEL_ID:
        return

    try:
        channel = bot.get_channel(int(DISCORD_CHANNEL_ID))
        if not channel:
            return

        today_str = datetime.now().strftime("%m월 %d일")
        loop = asyncio.get_event_loop()

        for kw in WATCH_KEYWORDS:
            card = await loop.run_in_executor(None, doribogo_bot.run_full_doribogo, kw)
            embed = discord.Embed(
                title=f"⚡ [{today_str} 실시간 이슈] {kw}",
                description=card,
                color=0xFF6B00
            )
            embed.set_footer(text=f"hodori bot • {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            await channel.send(embed=embed)
            await asyncio.sleep(2)

    except Exception as e:
        print(f"[!] 30분 정기 브리핑 에러: {e}")


@auto_radar_loop.before_loop
async def before_loop():
    await bot.wait_until_ready()


def main():
    if not DISCORD_BOT_TOKEN:
        print("❌ DISCORD_BOT_TOKEN이 설정되지 않았습니다.")
        sys.exit(1)

    bot.run(DISCORD_BOT_TOKEN)


if __name__ == "__main__":
    main()
