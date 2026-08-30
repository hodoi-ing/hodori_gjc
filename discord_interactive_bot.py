"""🐯 dori bot - 실시간 디스코드 인터랙티브 챗봇 (discord.py)

💡 명령어 안내:
• !도리 [키워드] : 어떤 키워드든 5대 레이더로 실시간 리서치 ➔ 4단계 팩트 브리핑 즉시 출력
  예) !도리 백컨트리 360
  예) !도리 RTX 5090 특가
  예) !도리 제미나이 2.5
• !도리 도움말 : 사용법 안내
• 30분마다 감시 키워드 자동 브리핑도 함께 발송
"""

import os
import sys
import time
import json
import asyncio
from datetime import datetime, timezone

try:
    import discord
    from discord.ext import commands, tasks
except ImportError:
    print("[!] discord.py가 설치되지 않았습니다. 'pip install discord.py'를 실행해주세요.")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import doribogo_bot

DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "").strip()
DISCORD_CHANNEL_ID = os.environ.get("DISCORD_CHANNEL_ID", "").strip()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

WATCH_KEYWORDS = ["백컨트리 360", "캠핑 텐트 특가"]


@bot.event
async def on_ready():
    print("=" * 60)
    print(f"🐯 dori bot 온라인 로그인 완료: {bot.user.name} ({bot.user.id})")
    print(f"• 명령어 접두사: '!' (예: !도리 백컨트리 360)")
    print("=" * 60)
    if not auto_radar_loop.is_running():
        auto_radar_loop.start()


@bot.command(name="도리", aliases=["dori", "doribogo"])
async def dori_command(ctx, *, keyword: str = ""):
    """실시간 키워드 질의응답 명령어."""
    keyword = keyword.strip()
    if not keyword:
        await ctx.send("🐯 검색할 키워드를 입력해주세요!\n예) `!도리 백컨트리 360`\n예) `!도리 아이폰 16 특가`")
        return

    if keyword in ["도움말", "help", "?"]:
        embed = discord.Embed(
            title="🐯 dori bot 사용 안내",
            description=(
                "**실시간 4단계 팩트 큐레이션 챗봇**\n\n"
                "• `!도리 [키워드]` : 5대 레이더 실시간 스캔 & 4단계 팩트 브리핑 생성\n"
                "• 예시: `!도리 백컨트리 360`\n"
                "• 예시: `!도리 RTX 5090 가격`\n"
                "• 예시: `!도리 텐트 대란`\n\n"
                "💡 30분마다 주요 키워드 자동 브리핑도 함께 제공됩니다."
            ),
            color=0x3B82F6
        )
        embed.set_footer(text="dori bot • 실시간 레이더")
        await ctx.send(embed=embed)
        return

    # 대기 메시지 전송
    loading_msg = await ctx.send(f"🔍 **[{keyword}]** 5대 레이더 실시간 수집 및 AI 분석 중... 잠시만 기다려주세요! ⏳")

    try:
        # 비동기 백그라운드 리서치 실행
        loop = asyncio.get_event_loop()
        card_news = await loop.run_in_executor(None, doribogo_bot.run_full_doribogo, keyword)
        today_str = datetime.now().strftime("%m월 %d일")

        embed = discord.Embed(
            title=f"⚡ [{today_str} 실시간 이슈] {keyword}",
            description=card_news,
            color=0xFF6B00
        )
        embed.set_footer(text=f"dori bot • {datetime.now().strftime('%Y-%m-%d %H:%M')}")

        await loading_msg.delete()
        await ctx.send(embed=embed)

    except Exception as e:
        await loading_msg.edit(content=f"❌ **[{keyword}]** 분석 중 오류가 발생했습니다: {e}")


@tasks.loop(minutes=30)
async def auto_radar_loop():
    """30분 주기 정기 자동 브리핑 발송."""
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
            embed.set_footer(text=f"dori bot • {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            await channel.send(embed=embed)
            await asyncio.sleep(2)

    except Exception as e:
        print(f"[!] 30분 정기 브리핑 에러: {e}")


@auto_radar_loop.before_loop
async def before_loop():
    await bot.wait_until_ready()


def main():
    if not DISCORD_BOT_TOKEN:
        print("=" * 60)
        print("❌ DISCORD_BOT_TOKEN이 설정되지 않았습니다!")
        print("👉 디스코드 개발자 포털(discord.com/developers/applications)에서")
        print("   봇 토큰을 발급받아 .env에 입력해주세요.")
        print("=" * 60)
        sys.exit(1)

    bot.run(DISCORD_BOT_TOKEN)


if __name__ == "__main__":
    main()
